"""Tests for admin_inventory_materials router + service (Sprint #20.5).

Mirrors the Sprint #20 workcenter_rates test pattern: uses the isolated
DB fixture, unittest-class lifecycle, and tests both service invariants
and HTTP surface.
"""

from __future__ import annotations

import asyncio
import unittest
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from tests._db_fixture import IsolatedDBFixture

from dependencies.auth import get_current_user
from routers.admin_inventory_materials import router as admin_materials_router
from schemas.auth import UserResponse
from services.inventory_materials_admin_service import (
    InventoryMaterialValidationError,
    get_inventory_material_by_code,
    list_inventory_materials_admin,
    patch_inventory_material_by_code,
    validate_status_and_cost,
)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestInventoryMaterialsAdminBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture()
        cls.db_fixture.setup()
        _run(cls._seed())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
        from core.database import db_manager
        from models.inventory_materials import Inventory_materials

        async with db_manager.async_session_maker() as session:
            session.add_all(
                [
                    Inventory_materials(
                        code="MAT-ACP-3MM",
                        name="ACP / Dibond 3mm",
                        unit="mp",
                        category="panou_compozit",
                        unit_cost=None,
                        status="missing_price",
                    ),
                    Inventory_materials(
                        code="MAT-LED-MODULE",
                        name="Modul LED",
                        unit="buc",
                        category="iluminat_led",
                        unit_cost=None,
                        status="missing_price",
                    ),
                    Inventory_materials(
                        code="MAT-ARCHIVED",
                        name="Old material",
                        unit="buc",
                        category="misc",
                        unit_cost=None,
                        status="archived",
                    ),
                ]
            )
            await session.commit()


class TestValidation(TestInventoryMaterialsAdminBase):
    def test_invalid_status_rejected(self) -> None:
        with self.assertRaises(InventoryMaterialValidationError):
            validate_status_and_cost("NOT_A_STATUS", 10.0)

    def test_negative_cost_rejected(self) -> None:
        with self.assertRaises(InventoryMaterialValidationError):
            validate_status_and_cost("missing_price", -0.01)

    def test_active_requires_positive_cost(self) -> None:
        with self.assertRaises(InventoryMaterialValidationError):
            validate_status_and_cost("active", None)
        with self.assertRaises(InventoryMaterialValidationError):
            validate_status_and_cost("active", 0.0)

    def test_active_requires_currency_vat_valid_from(self) -> None:
        with self.assertRaises(InventoryMaterialValidationError):
            validate_status_and_cost("active", 1.0, None, 19.0, datetime.now(timezone.utc))
        with self.assertRaises(InventoryMaterialValidationError):
            validate_status_and_cost("active", 1.0, "RON", None, datetime.now(timezone.utc))
        with self.assertRaises(InventoryMaterialValidationError):
            validate_status_and_cost("active", 1.0, "RON", 19.0, None)

    def test_missing_price_allows_null_cost(self) -> None:
        # Should NOT raise.
        validate_status_and_cost("missing_price", None)
        validate_status_and_cost("missing_price", 10.0)


class TestServicePatch(TestInventoryMaterialsAdminBase):
    def test_patch_transitions_to_active(self) -> None:
        from core.database import db_manager

        async def _go() -> Dict[str, Any]:
            async with db_manager.async_session_maker() as session:
                return await patch_inventory_material_by_code(
                    session,
                    "MAT-ACP-3MM",
                    unit_cost=75.0,
                    currency="RON",
                    vat_percent=19.0,
                    valid_from=datetime.now(timezone.utc),
                    status="active",
                    change_reason="activate material",
                )

        row = _run(_go())
        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "active")
        self.assertEqual(row["unit_cost"], 75.0)

    def test_patch_missing_code_returns_none(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                return await patch_inventory_material_by_code(
                    session,
                    "MAT-DOES-NOT-EXIST",
                    unit_cost=1.0,
                    currency="RON",
                    vat_percent=19.0,
                    valid_from=datetime.now(timezone.utc),
                    status="active",
                )

        self.assertIsNone(_run(_go()))

    def test_patch_active_without_cost_raises(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                return await patch_inventory_material_by_code(
                    session, "MAT-LED-MODULE", status="active"
                )

        with self.assertRaises(InventoryMaterialValidationError):
            _run(_go())

    def test_list_and_get_by_code(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                all_rows = await list_inventory_materials_admin(session)
                one = await get_inventory_material_by_code(session, "MAT-LED-MODULE")
                return all_rows, one

        rows, one = _run(_go())
        codes = [r["code"] for r in rows]
        self.assertIn("MAT-ACP-3MM", codes)
        self.assertIn("MAT-LED-MODULE", codes)
        self.assertIn("MAT-ARCHIVED", codes)
        self.assertIsNotNone(one)
        self.assertEqual(one["code"], "MAT-LED-MODULE")

    def test_list_status_filter(self) -> None:
        from core.database import db_manager

        async def _go():
            async with db_manager.async_session_maker() as session:
                return await list_inventory_materials_admin(
                    session, status_filter="archived"
                )

        rows = _run(_go())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["code"], "MAT-ARCHIVED")


class TestHTTPRouter(TestInventoryMaterialsAdminBase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        async def _override_get_current_user():
            return UserResponse(
                id="test-user-id",
                email="test@example.com",
                name="Test Admin",
                role="admin",
                last_login=None,
            )

        cls.app = FastAPI()
        cls.app.include_router(admin_materials_router)
        cls.app.dependency_overrides[get_current_user] = _override_get_current_user

    def _client(self) -> AsyncClient:
        return AsyncClient(
            transport=ASGITransport(app=self.app), base_url="http://test"
        )

    def test_get_list(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get("/api/admin/inventory-materials")
                return r.status_code, r.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        codes = [row["code"] for row in body]
        self.assertIn("MAT-ACP-3MM", codes)
        self.assertIn("MAT-LED-MODULE", codes)

    def test_get_policy(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get("/api/admin/inventory-materials/policy")
                return r.status_code, r.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        self.assertIn("canonical_categories", body)
        self.assertIn("recommended_subcategories", body)
        self.assertIn("source_review_policy", body)
        self.assertIn("product_system_gate_rules", body)
        self.assertIn("price_governed_fields", body)
        self.assertEqual(body["stale_source_days"], 90)

    def test_get_source_review_audit_endpoint(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get("/api/admin/inventory-materials/MAT-ACP-3MM/source-review-audit")
                return r.status_code, r.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        self.assertTrue(isinstance(body, list))

    def test_get_category_cleanup_preview_endpoint(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get("/api/admin/inventory-materials/category-cleanup/preview")
                return r.status_code, r.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        self.assertTrue(isinstance(body, list))

    def test_patch_to_active(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.patch(
                    "/api/admin/inventory-materials/MAT-LED-MODULE",
                    json={
                        "unit_cost": 1.4,
                        "currency": "RON",
                        "vat_percent": 19.0,
                        "valid_from": "2026-06-02T00:00:00+00:00",
                        "status": "active",
                        "change_reason": "activate material",
                    },
                )
                return r.status_code, r.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "active")
        self.assertEqual(body["unit_cost"], 1.4)

    def test_patch_404(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.patch(
                    "/api/admin/inventory-materials/MAT-NOPE",
                    json={"unit_cost": 1.0, "status": "active"},
                )
                return r.status_code

        self.assertEqual(_run(_go()), 404)

    def test_patch_invariant_violation_returns_400(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.patch(
                    "/api/admin/inventory-materials/MAT-ACP-3MM",
                    json={"status": "active"},  # no unit_cost
                )
                return r.status_code, r.json()

        status, body = _run(_go())
        self.assertEqual(status, 400)
        self.assertIn("active", str(body["detail"]).lower())

    def test_patch_source_metadata(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.patch(
                    "/api/admin/inventory-materials/MAT-ACP-3MM",
                    json={
                        "source_name": "Catalog intern",
                        "source_url": "https://example.invalid/registry",
                        "source_checked_at": "2026-06-02T00:00:00+00:00",
                        "source_notes": "verificat",
                    },
                )
                return r.status_code, r.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        self.assertEqual(body["source_name"], "Catalog intern")
        self.assertEqual(body["source_url"], "https://example.invalid/registry")
        self.assertIsNotNone(body["source_checked_at"])
        self.assertEqual(body["source_notes"], "verificat")
        self.assertEqual(body["status"], "missing_price")

    def test_patch_source_review_status_without_reason_keeps_history(self) -> None:
        async def _go():
            async with self._client() as c:
                before_history = await c.get(
                    "/api/admin/inventory-materials/MAT-ACP-3MM/price-history"
                )
                patch_response = await c.patch(
                    "/api/admin/inventory-materials/MAT-ACP-3MM",
                    json={
                        "source_name": "Catalog intern",
                        "source_url": "https://example.invalid/source",
                        "source_checked_at": "2026-06-02T00:00:00+00:00",
                        "source_notes": "reviewed for governance",
                        "source_review_status": "reviewed",
                    },
                )
                after_history = await c.get(
                    "/api/admin/inventory-materials/MAT-ACP-3MM/price-history"
                )
                return (
                    before_history.status_code,
                    before_history.json(),
                    patch_response.status_code,
                    patch_response.json(),
                    after_history.status_code,
                    after_history.json(),
                )

        (
            before_history_status,
            before_history,
            patch_status,
            patched,
            after_history_status,
            after_history,
        ) = _run(_go())
        self.assertEqual(before_history_status, 200)
        self.assertEqual(patch_status, 200)
        self.assertEqual(after_history_status, 200)
        self.assertEqual(patched["source_review_status"], "reviewed")
        self.assertIsNotNone(patched["source_reviewed_at"])
        self.assertIsNotNone(patched["source_reviewed_by"])
        self.assertEqual(len(after_history), len(before_history))

    def test_patch_source_review_status_writes_audit_without_price_history(self) -> None:
        from core.database import db_manager
        from models.inventory_materials import Inventory_materials

        async def _go():
            async with db_manager.async_session_maker() as session:
                session.add(
                    Inventory_materials(
                        code="MAT-SRC-AUDIT-001",
                        name="Source audit material",
                        unit="mp",
                        category="test",
                        source_review_status="needs_review",
                        status="missing_price",
                    )
                )
                await session.commit()

            async with self._client() as c:
                before_history = await c.get(
                    "/api/admin/inventory-materials/MAT-SRC-AUDIT-001/price-history"
                )
                before_audit = await c.get(
                    "/api/admin/inventory-materials/MAT-SRC-AUDIT-001/source-review-audit"
                )
                patch_response = await c.patch(
                    "/api/admin/inventory-materials/MAT-SRC-AUDIT-001",
                    json={
                        "source_name": "Catalog intern",
                        "source_url": "https://example.invalid/source",
                        "source_checked_at": "2026-06-02T00:00:00+00:00",
                        "source_notes": "reviewed for governance",
                        "source_review_status": "reviewed",
                    },
                )
                after_history = await c.get(
                    "/api/admin/inventory-materials/MAT-SRC-AUDIT-001/price-history"
                )
                after_audit = await c.get(
                    "/api/admin/inventory-materials/MAT-SRC-AUDIT-001/source-review-audit"
                )
                return (
                    before_history.status_code,
                    before_history.json(),
                    before_audit.status_code,
                    before_audit.json(),
                    patch_response.status_code,
                    patch_response.json(),
                    after_history.status_code,
                    after_history.json(),
                    after_audit.status_code,
                    after_audit.json(),
                )

        (
            before_history_status,
            before_history,
            before_audit_status,
            before_audit,
            patch_status,
            patched,
            after_history_status,
            after_history,
            after_audit_status,
            after_audit,
        ) = _run(_go())
        self.assertEqual(before_history_status, 200)
        self.assertEqual(before_audit_status, 200)
        self.assertEqual(patch_status, 200)
        self.assertEqual(after_history_status, 200)
        self.assertEqual(after_audit_status, 200)
        self.assertEqual(patched["source_review_status"], "reviewed")
        self.assertIsNotNone(patched["source_reviewed_at"])
        self.assertIsNotNone(patched["source_reviewed_by"])
        self.assertEqual(len(after_history), len(before_history))
        self.assertEqual(len(after_audit), len(before_audit) + 1)
        latest = after_audit[0]
        self.assertEqual(latest["material_code"], "MAT-SRC-AUDIT-001")
        self.assertEqual(latest["old_status"], "needs_review")
        self.assertEqual(latest["new_status"], "reviewed")
        self.assertEqual(latest["actor"], "test-user-id")

    def test_patch_price_and_source_review_without_reason_rejected_without_partial_write(self) -> None:
        from core.database import db_manager
        from models.inventory_materials import Inventory_materials

        async def _go():
            async with db_manager.async_session_maker() as session:
                session.add(
                    Inventory_materials(
                        code="MAT-MIXED-NO-REASON-001",
                        name="Mixed no reason material",
                        unit="buc",
                        category="test",
                        unit_cost=10.0,
                        currency="RON",
                        vat_percent=19.0,
                        valid_from=datetime.now(timezone.utc),
                        status="active",
                    )
                )
                await session.commit()

            async with self._client() as c:
                before_material = await c.get(
                    "/api/admin/inventory-materials/MAT-MIXED-NO-REASON-001"
                )
                before_history = await c.get(
                    "/api/admin/inventory-materials/MAT-MIXED-NO-REASON-001/price-history"
                )
                before_audit = await c.get(
                    "/api/admin/inventory-materials/MAT-MIXED-NO-REASON-001/source-review-audit"
                )
                reject = await c.patch(
                    "/api/admin/inventory-materials/MAT-MIXED-NO-REASON-001",
                    json={"unit_cost": 11.0, "source_review_status": "reviewed"},
                )
                after_material = await c.get(
                    "/api/admin/inventory-materials/MAT-MIXED-NO-REASON-001"
                )
                after_history = await c.get(
                    "/api/admin/inventory-materials/MAT-MIXED-NO-REASON-001/price-history"
                )
                after_audit = await c.get(
                    "/api/admin/inventory-materials/MAT-MIXED-NO-REASON-001/source-review-audit"
                )
                return (
                    before_material.status_code,
                    before_material.json(),
                    before_history.status_code,
                    before_history.json(),
                    before_audit.status_code,
                    before_audit.json(),
                    reject.status_code,
                    reject.json(),
                    after_material.status_code,
                    after_material.json(),
                    after_history.status_code,
                    after_history.json(),
                    after_audit.status_code,
                    after_audit.json(),
                )

        (
            before_material_status,
            before_material,
            before_history_status,
            before_history,
            before_audit_status,
            before_audit,
            reject_status,
            reject_body,
            after_material_status,
            after_material,
            after_history_status,
            after_history,
            after_audit_status,
            after_audit,
        ) = _run(_go())
        self.assertEqual(before_material_status, 200)
        self.assertEqual(before_history_status, 200)
        self.assertEqual(before_audit_status, 200)
        self.assertEqual(reject_status, 400)
        self.assertIn("change_reason", str(reject_body.get("detail", "")))
        self.assertEqual(after_material_status, 200)
        self.assertEqual(after_history_status, 200)
        self.assertEqual(after_audit_status, 200)
        self.assertEqual(after_material["unit_cost"], before_material["unit_cost"])
        self.assertEqual(len(after_history), len(before_history))
        self.assertEqual(len(after_audit), len(before_audit))

    def test_category_cleanup_preview_returns_issues_without_writes(self) -> None:
        from core.database import db_manager
        from models.inventory_materials import Inventory_materials

        async def _go():
            async with db_manager.async_session_maker() as session:
                session.add(
                    Inventory_materials(
                        code="MAT-LEGACY-CLEANUP-001",
                        name="Legacy cleanup material",
                        unit="mp",
                        category="legacy_misc_material",
                        subcategory=None,
                        status="missing_price",
                    )
                )
                await session.commit()

            async with self._client() as c:
                before_material = await c.get(
                    "/api/admin/inventory-materials/MAT-LEGACY-CLEANUP-001"
                )
                before_history = await c.get(
                    "/api/admin/inventory-materials/MAT-LEGACY-CLEANUP-001/price-history"
                )
                preview = await c.get("/api/admin/inventory-materials/category-cleanup/preview")
                after_material = await c.get(
                    "/api/admin/inventory-materials/MAT-LEGACY-CLEANUP-001"
                )
                after_history = await c.get(
                    "/api/admin/inventory-materials/MAT-LEGACY-CLEANUP-001/price-history"
                )
                return (
                    before_material.status_code,
                    before_material.json(),
                    before_history.status_code,
                    before_history.json(),
                    preview.status_code,
                    preview.json(),
                    after_material.status_code,
                    after_material.json(),
                    after_history.status_code,
                    after_history.json(),
                )

        (
            before_material_status,
            before_material,
            before_history_status,
            before_history,
            preview_status,
            preview_body,
            after_material_status,
            after_material,
            after_history_status,
            after_history,
        ) = _run(_go())
        self.assertEqual(before_material_status, 200)
        self.assertEqual(before_history_status, 200)
        self.assertEqual(preview_status, 200)
        self.assertEqual(after_material_status, 200)
        self.assertEqual(after_history_status, 200)
        self.assertEqual(before_material["category"], after_material["category"])
        self.assertEqual(len(before_history), len(after_history))
        self.assertTrue(any(item["code"] == "MAT-LEGACY-CLEANUP-001" for item in preview_body))
        preview_item = next(item for item in preview_body if item["code"] == "MAT-LEGACY-CLEANUP-001")
        self.assertFalse(preview_item["safe_to_apply"])
        self.assertIn("category", preview_item["reason"])

    def test_patch_subcategory_without_reason_keeps_history(self) -> None:
        async def _go():
            async with self._client() as c:
                before_history = await c.get(
                    "/api/admin/inventory-materials/MAT-LED-MODULE/price-history"
                )
                patch_response = await c.patch(
                    "/api/admin/inventory-materials/MAT-LED-MODULE",
                    json={"subcategory": "LED modules"},
                )
                after_history = await c.get(
                    "/api/admin/inventory-materials/MAT-LED-MODULE/price-history"
                )
                return (
                    before_history.status_code,
                    before_history.json(),
                    patch_response.status_code,
                    patch_response.json(),
                    after_history.status_code,
                    after_history.json(),
                )

        (
            before_history_status,
            before_history,
            patch_status,
            patched,
            after_history_status,
            after_history,
        ) = _run(_go())
        self.assertEqual(before_history_status, 200)
        self.assertEqual(patch_status, 200)
        self.assertEqual(after_history_status, 200)
        self.assertEqual(patched["subcategory"], "LED modules")
        self.assertEqual(len(after_history), len(before_history))

    def test_get_price_history_endpoint_read_only(self) -> None:
        async def _go():
            async with self._client() as c:
                patch_response = await c.patch(
                    "/api/admin/inventory-materials/MAT-LED-MODULE",
                    json={
                        "unit_cost": 2.1,
                        "currency": "RON",
                        "vat_percent": 19.0,
                        "valid_from": "2026-06-02T00:00:00+00:00",
                        "status": "active",
                        "change_reason": "history-check",
                    },
                )
                history_response = await c.get(
                    "/api/admin/inventory-materials/MAT-LED-MODULE/price-history"
                )
                return (
                    patch_response.status_code,
                    history_response.status_code,
                    history_response.json(),
                )

        patch_status, status, payload = _run(_go())
        self.assertEqual(patch_status, 200)
        self.assertEqual(status, 200)
        self.assertTrue(isinstance(payload, list))
        self.assertGreaterEqual(len(payload), 1)
        self.assertEqual(payload[0]["change_reason"], "history-check")

    def test_patch_price_change_without_reason_returns_400_and_no_history_write(self) -> None:
        from core.database import db_manager
        from models.inventory_materials import Inventory_materials

        async def _go():
            async with db_manager.async_session_maker() as session:
                session.add(
                    Inventory_materials(
                        code="MAT-REASON-HTTP-NEG-001",
                        name="Reason Negative",
                        unit="buc",
                        category="test",
                        unit_cost=10.0,
                        currency="RON",
                        vat_percent=19.0,
                        valid_from=datetime.now(timezone.utc),
                        status="active",
                    )
                )
                await session.commit()

            async with self._client() as c:
                before_material = await c.get(
                    "/api/admin/inventory-materials/MAT-REASON-HTTP-NEG-001"
                )
                before_history = await c.get(
                    "/api/admin/inventory-materials/MAT-REASON-HTTP-NEG-001/price-history"
                )
                reject = await c.patch(
                    "/api/admin/inventory-materials/MAT-REASON-HTTP-NEG-001",
                    json={"unit_cost": 11.0},
                )
                after_material = await c.get(
                    "/api/admin/inventory-materials/MAT-REASON-HTTP-NEG-001"
                )
                after_history = await c.get(
                    "/api/admin/inventory-materials/MAT-REASON-HTTP-NEG-001/price-history"
                )
                return (
                    before_material.status_code,
                    before_material.json(),
                    before_history.status_code,
                    before_history.json(),
                    reject.status_code,
                    reject.json(),
                    after_material.status_code,
                    after_material.json(),
                    after_history.status_code,
                    after_history.json(),
                )

        (
            before_material_status,
            before_material,
            before_history_status,
            before_history,
            reject_status,
            reject_body,
            after_material_status,
            after_material,
            after_history_status,
            after_history,
        ) = _run(_go())

        self.assertEqual(before_material_status, 200)
        self.assertEqual(before_history_status, 200)
        self.assertEqual(reject_status, 400)
        self.assertIn("change_reason", str(reject_body.get("detail", "")))
        self.assertEqual(after_material_status, 200)
        self.assertEqual(after_history_status, 200)
        self.assertEqual(after_material["unit_cost"], before_material["unit_cost"])
        self.assertEqual(len(after_history), len(before_history))

    def test_patch_price_and_metadata_without_reason_rejected_without_partial_write(self) -> None:
        from core.database import db_manager
        from models.inventory_materials import Inventory_materials

        async def _go():
            async with db_manager.async_session_maker() as session:
                session.add(
                    Inventory_materials(
                        code="MAT-META-PRICE-NO-REASON-001",
                        name="Meta Price No Reason",
                        unit="buc",
                        category="test",
                        unit_cost=5.0,
                        currency="RON",
                        vat_percent=19.0,
                        valid_from=datetime.now(timezone.utc),
                        status="active",
                        source_notes="before",
                    )
                )
                await session.commit()

            async with self._client() as c:
                before_material = await c.get(
                    "/api/admin/inventory-materials/MAT-META-PRICE-NO-REASON-001"
                )
                before_history = await c.get(
                    "/api/admin/inventory-materials/MAT-META-PRICE-NO-REASON-001/price-history"
                )
                reject = await c.patch(
                    "/api/admin/inventory-materials/MAT-META-PRICE-NO-REASON-001",
                    json={"unit_cost": 6.0, "source_notes": "after"},
                )
                after_material = await c.get(
                    "/api/admin/inventory-materials/MAT-META-PRICE-NO-REASON-001"
                )
                after_history = await c.get(
                    "/api/admin/inventory-materials/MAT-META-PRICE-NO-REASON-001/price-history"
                )
                return (
                    before_material.status_code,
                    before_material.json(),
                    before_history.status_code,
                    before_history.json(),
                    reject.status_code,
                    reject.json(),
                    after_material.status_code,
                    after_material.json(),
                    after_history.status_code,
                    after_history.json(),
                )

        (
            before_material_status,
            before_material,
            before_history_status,
            before_history,
            reject_status,
            reject_body,
            after_material_status,
            after_material,
            after_history_status,
            after_history,
        ) = _run(_go())

        self.assertEqual(before_material_status, 200)
        self.assertEqual(before_history_status, 200)
        self.assertEqual(reject_status, 400)
        self.assertIn("change_reason", str(reject_body.get("detail", "")))
        self.assertEqual(after_material_status, 200)
        self.assertEqual(after_history_status, 200)
        self.assertEqual(after_material["unit_cost"], before_material["unit_cost"])
        self.assertEqual(after_material["source_notes"], before_material["source_notes"])
        self.assertEqual(len(after_history), len(before_history))

    def test_patch_price_change_with_reason_writes_history(self) -> None:
        from core.database import db_manager
        from models.inventory_materials import Inventory_materials

        async def _go():
            async with db_manager.async_session_maker() as session:
                session.add(
                    Inventory_materials(
                        code="MAT-REASON-HTTP-POS-001",
                        name="Reason Positive",
                        unit="buc",
                        category="test",
                        unit_cost=10.0,
                        currency="RON",
                        vat_percent=19.0,
                        valid_from=datetime.now(timezone.utc),
                        status="active",
                    )
                )
                await session.commit()

            async with self._client() as c:
                patch_response = await c.patch(
                    "/api/admin/inventory-materials/MAT-REASON-HTTP-POS-001",
                    json={"unit_cost": 12.0, "change_reason": "pricing update"},
                )
                history_response = await c.get(
                    "/api/admin/inventory-materials/MAT-REASON-HTTP-POS-001/price-history"
                )
                return (
                    patch_response.status_code,
                    patch_response.json(),
                    history_response.status_code,
                    history_response.json(),
                )

        patch_status, patched, history_status, history = _run(_go())
        self.assertEqual(patch_status, 200)
        self.assertEqual(patched["unit_cost"], 12.0)
        self.assertEqual(history_status, 200)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["change_reason"], "pricing update")


if __name__ == "__main__":
    unittest.main()