from __future__ import annotations

import asyncio
import inspect
import unittest
from datetime import datetime, timezone

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from tests._db_fixture import IsolatedDBFixture

from dependencies.auth import get_current_user
from routers.admin_productsystem_pricing_preview import router as pricing_preview_router
from routers.admin_commercial_markup_policies import router as admin_markup_router
from schemas.auth import UserResponse


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestProductSystemPricingPreview(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture()
        cls.db_fixture.setup()
        _run(cls._seed())

        async def _override_get_current_user():
            return UserResponse(
                id="test-user-id",
                email="test@example.com",
                name="Test Admin",
                role="admin",
                last_login=None,
            )

        cls.app = FastAPI()
        cls.app.include_router(pricing_preview_router)
        cls.app.include_router(admin_markup_router)
        cls.app.dependency_overrides[get_current_user] = _override_get_current_user

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
        from core.database import db_manager
        from models.commercial_markup_policies import Commercial_markup_policies
        from models.inventory_material_price_history import Inventory_material_price_history
        from models.inventory_materials import Inventory_materials

        async with db_manager.async_session_maker() as session:
            led = Inventory_materials(
                code="DEV-SMOKE-LED-MODULE",
                name="DEV Smoke LED Module",
                unit="buc",
                category="Parti electrice",
                subcategory="LED modules",
                status="active",
                unit_cost=10.0,
                currency="RON",
                vat_percent=19.0,
                valid_from=datetime(2026, 6, 1, tzinfo=timezone.utc),
                source_review_status="reviewed",
                source_checked_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            )
            no_policy = Inventory_materials(
                code="DEV-SMOKE-NOPOLICY",
                name="No policy material",
                unit="buc",
                category="Consumabile",
                subcategory="adezivi",
                status="active",
                unit_cost=8.0,
                currency="RON",
                vat_percent=19.0,
                valid_from=datetime(2026, 6, 1, tzinfo=timezone.utc),
                source_review_status="needs_review",
                source_checked_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            )
            incomplete = Inventory_materials(
                code="DEV-SMOKE-NO-COST",
                name="Incomplete material",
                unit="buc",
                category="Folii",
                subcategory=None,
                status="active",
                unit_cost=None,
                currency=None,
                vat_percent=None,
                valid_from=None,
                source_review_status="missing",
                source_checked_at=None,
            )
            archived = Inventory_materials(
                code="DEV-SMOKE-ARCHIVED",
                name="Archived material",
                unit="buc",
                category="Folii",
                subcategory="Printabil",
                status="archived",
                unit_cost=5.0,
                currency="RON",
                vat_percent=19.0,
                valid_from=datetime(2026, 6, 1, tzinfo=timezone.utc),
                source_review_status="stale",
                source_checked_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            )
            session.add_all([led, no_policy, incomplete, archived])
            session.add_all(
                [
                    Commercial_markup_policies(
                        scope_type="global",
                        scope_value="global",
                        markup_type="percent",
                        markup_percent=5.0,
                        currency="RON",
                        rounding_mode="none",
                        applies_to="material_cost",
                        status="draft",
                        priority=100,
                        notes="global",
                    ),
                    Commercial_markup_policies(
                        scope_type="category",
                        scope_value="Parti electrice",
                        markup_type="percent",
                        markup_percent=10.0,
                        currency="RON",
                        rounding_mode="none",
                        applies_to="material_cost",
                        status="active",
                        priority=50,
                        notes="category",
                    ),
                    Commercial_markup_policies(
                        scope_type="material",
                        scope_value="DEV-SMOKE-LED-MODULE",
                        markup_type="hybrid",
                        markup_percent=15.0,
                        markup_fixed=1.0,
                        currency="RON",
                        rounding_mode="nearest_0_10",
                        applies_to="material_cost",
                        status="active",
                        priority=10,
                        notes="material",
                    ),
                ]
            )
            session.add(
                Inventory_material_price_history(
                    material_id=1,
                    unit_cost=10.0,
                    currency="RON",
                    vat_percent=19.0,
                    valid_from=datetime(2026, 6, 1, tzinfo=timezone.utc),
                    changed_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
                    changed_by="seed",
                    change_reason="seed",
                    snapshot_source="seed",
                )
            )
            await session.commit()

    def _client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://test")

    def test_preview_with_policy_returns_complete_price(self) -> None:
        async def _go():
            async with self._client() as c:
                res = await c.post(
                    "/api/admin/productsystem/pricing-preview",
                    json={"material_code": "DEV-SMOKE-LED-MODULE", "quantity": 2, "include_vat": True},
                )
                return res.status_code, res.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        self.assertTrue(body["no_write_guarantee"])
        self.assertEqual(body["material_code"], "DEV-SMOKE-LED-MODULE")
        self.assertEqual(body["unit_cost"], 10.0)
        self.assertEqual(body["base_cost_total"], 20.0)
        self.assertIsNotNone(body["applied_markup_policy"])
        self.assertGreater(body["commercial_unit_price_ex_vat"], body["unit_cost"])
        self.assertGreater(body["commercial_total_inc_vat"], body["commercial_total_ex_vat"])

    def test_preview_keeps_material_and_history_unchanged(self) -> None:
        from core.database import db_manager
        from models.inventory_material_price_history import Inventory_material_price_history
        from models.inventory_materials import Inventory_materials

        async def _go():
            async with db_manager.async_session_maker() as session:
                before = (
                    await session.execute(
                        select(Inventory_materials).where(Inventory_materials.code == "DEV-SMOKE-LED-MODULE")
                    )
                ).scalar_one()
                history_before = (
                    await session.execute(
                        select(Inventory_material_price_history).where(
                            Inventory_material_price_history.material_id == before.id
                        )
                    )
                ).scalars().all()

            async with self._client() as c:
                res = await c.post(
                    "/api/admin/productsystem/pricing-preview",
                    json={"material_code": "DEV-SMOKE-LED-MODULE", "quantity": 1, "vat_percent": 21},
                )
                payload = res.json()

            async with db_manager.async_session_maker() as session:
                after = (
                    await session.execute(
                        select(Inventory_materials).where(Inventory_materials.code == "DEV-SMOKE-LED-MODULE")
                    )
                ).scalar_one()
                history_after = (
                    await session.execute(
                        select(Inventory_material_price_history).where(
                            Inventory_material_price_history.material_id == after.id
                        )
                    )
                ).scalars().all()

            return payload, after.unit_cost, len(history_after) - len(history_before)

        payload, unit_cost_after, history_delta = _run(_go())
        self.assertEqual(payload["vat_percent"], 21.0)
        self.assertEqual(unit_cost_after, 10.0)
        self.assertEqual(history_delta, 0)

    def test_no_policy_returns_warning_and_no_write(self) -> None:
        async def _go():
            async with self._client() as c:
                res = await c.post(
                    "/api/admin/productsystem/pricing-preview",
                    json={"material_code": "DEV-SMOKE-NOPOLICY", "quantity": 1},
                )
                return res.status_code, res.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        warning_codes = {w["code"] for w in body["warnings"]}
        self.assertIn("no_markup_policy", warning_codes)
        self.assertTrue(body["no_write_guarantee"])

    def test_incomplete_material_returns_warnings_and_blockers(self) -> None:
        async def _go():
            async with self._client() as c:
                res = await c.post(
                    "/api/admin/productsystem/pricing-preview",
                    json={"material_code": "DEV-SMOKE-NO-COST", "quantity": 1},
                )
                return res.status_code, res.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        blocker_codes = {b["code"] for b in body["blockers"]}
        warning_codes = {w["code"] for w in body["warnings"]}
        self.assertIn("material_missing_unit_cost", blocker_codes)
        self.assertIn("subcategory_missing", warning_codes)
        self.assertIn("vat_missing", warning_codes)

    def test_quantity_invalid_blocks_preview(self) -> None:
        async def _go():
            async with self._client() as c:
                res = await c.post(
                    "/api/admin/productsystem/pricing-preview",
                    json={"material_code": "DEV-SMOKE-LED-MODULE", "quantity": 0},
                )
                return res.status_code, res.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        blocker_codes = {b["code"] for b in body["blockers"]}
        self.assertIn("quantity_invalid", blocker_codes)

    def test_costengine_not_referenced(self) -> None:
        import services.productsystem_pricing_preview_service as preview_service

        source = inspect.getsource(preview_service)
        self.assertNotIn("CostEngine", source)
        self.assertNotIn("product_system_cost_simulation_service", source)


if __name__ == "__main__":
    unittest.main()