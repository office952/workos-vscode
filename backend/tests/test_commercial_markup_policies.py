from __future__ import annotations

import asyncio
import unittest
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from tests._db_fixture import IsolatedDBFixture

from dependencies.auth import get_current_user
from routers.admin_commercial_markup_policies import router as admin_markup_router
from routers.admin_inventory_materials import router as admin_inventory_router
from schemas.auth import UserResponse


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestCommercialMarkupPolicies(unittest.TestCase):
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
        cls.app.include_router(admin_markup_router)
        cls.app.include_router(admin_inventory_router)
        cls.app.dependency_overrides[get_current_user] = _override_get_current_user

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
        from core.database import db_manager
        from models.inventory_materials import Inventory_materials
        from models.commercial_markup_policies import Commercial_markup_policies

        async with db_manager.async_session_maker() as session:
            session.add_all(
                [
                    Inventory_materials(
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
                    ),
                    Inventory_materials(
                        code="DEV-SMOKE-NOPOLICY",
                        name="No policy material",
                        unit="buc",
                        category="Consumabile",
                        status="active",
                        unit_cost=8.0,
                        currency="RON",
                        vat_percent=19.0,
                        valid_from=datetime(2026, 6, 1, tzinfo=timezone.utc),
                        source_review_status="needs_review",
                    ),
                    Inventory_materials(
                        code="DEV-SMOKE-ARCHIVED",
                        name="Archived material",
                        unit="buc",
                        category="Folii",
                        status="archived",
                        unit_cost=5.0,
                        currency="RON",
                        vat_percent=19.0,
                        valid_from=datetime(2026, 6, 1, tzinfo=timezone.utc),
                        source_review_status="stale",
                    ),
                ]
            )
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
                        scope_type="subcategory",
                        scope_value="LED modules",
                        markup_type="percent",
                        markup_percent=12.0,
                        currency="RON",
                        rounding_mode="none",
                        applies_to="material_cost",
                        status="active",
                        priority=30,
                        notes="subcategory",
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
                    Commercial_markup_policies(
                        scope_type="material",
                        scope_value="DEV-SMOKE-LED-MODULE",
                        markup_type="fixed",
                        markup_fixed=99.0,
                        currency="RON",
                        rounding_mode="none",
                        applies_to="material_cost",
                        status="archived",
                        priority=1,
                        notes="archived should be ignored",
                    ),
                ]
            )
            await session.commit()

    def _client(self) -> AsyncClient:
        return AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url="http://test",
        )

    def test_config_endpoint(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get("/api/admin/commercial-markup-policies/config")
                return r.status_code, r.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        self.assertIn("scope_types", body)
        self.assertIn("markup_types", body)
        self.assertIn("rounding_modes", body)
        self.assertIn("conflict_resolution", body)

    def test_list_endpoint(self) -> None:
        async def _go():
            async with self._client() as c:
                r = await c.get("/api/admin/commercial-markup-policies")
                return r.status_code, r.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(body), 5)

    def test_dry_run_with_policy_keeps_material_unchanged(self) -> None:
        from core.database import db_manager
        from models.inventory_materials import Inventory_materials
        from models.inventory_material_price_history import Inventory_material_price_history

        async def _go() -> tuple[int, Dict[str, Any], float | None, int]:
            async with db_manager.async_session_maker() as session:
                material_before = (
                    await session.execute(
                        select(Inventory_materials).where(
                            Inventory_materials.code == "DEV-SMOKE-LED-MODULE"
                        )
                    )
                ).scalar_one()
                history_before = (
                    await session.execute(
                        select(Inventory_material_price_history).where(
                            Inventory_material_price_history.material_id == material_before.id
                        )
                    )
                ).scalars().all()

            async with self._client() as c:
                response = await c.post(
                    "/api/admin/commercial-markup-policies/dry-run",
                    json={"material_code": "DEV-SMOKE-LED-MODULE", "quantity": 3},
                )

            async with db_manager.async_session_maker() as session:
                material_after = (
                    await session.execute(
                        select(Inventory_materials).where(
                            Inventory_materials.code == "DEV-SMOKE-LED-MODULE"
                        )
                    )
                ).scalar_one()
                history_after = (
                    await session.execute(
                        select(Inventory_material_price_history).where(
                            Inventory_material_price_history.material_id == material_after.id
                        )
                    )
                ).scalars().all()

            return (
                response.status_code,
                response.json(),
                material_after.unit_cost,
                len(history_after) - len(history_before),
            )

        status, body, unit_cost_after, history_delta = _run(_go())
        self.assertEqual(status, 200)
        self.assertEqual(body["material_code"], "DEV-SMOKE-LED-MODULE")
        self.assertIsNotNone(body["applied_policy"])
        self.assertGreater(body["commercial_unit_price"], body["unit_cost"])
        self.assertEqual(unit_cost_after, 10.0)
        self.assertEqual(history_delta, 0)

    def test_resolution_priority_material_scope_wins(self) -> None:
        async def _go():
            async with self._client() as c:
                response = await c.post(
                    "/api/admin/commercial-markup-policies/dry-run",
                    json={"material_code": "DEV-SMOKE-LED-MODULE", "quantity": 1},
                )
                return response.status_code, response.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        self.assertEqual(body["applied_policy"]["scope_type"], "material")
        self.assertEqual(body["applied_policy"]["scope_value"], "DEV-SMOKE-LED-MODULE")

    def test_dry_run_without_policy_returns_warning(self) -> None:
        async def _go():
            async with self._client() as c:
                response = await c.post(
                    "/api/admin/commercial-markup-policies/dry-run",
                    json={"material_code": "DEV-SMOKE-NOPOLICY", "quantity": 2},
                )
                return response.status_code, response.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        warning_codes = {w["code"] for w in body["warnings"]}
        self.assertIn("no_markup_policy", warning_codes)

    def test_dry_run_archived_material_returns_warning(self) -> None:
        async def _go():
            async with self._client() as c:
                response = await c.post(
                    "/api/admin/commercial-markup-policies/dry-run",
                    json={"material_code": "DEV-SMOKE-ARCHIVED", "quantity": 1},
                )
                return response.status_code, response.json()

        status, body = _run(_go())
        self.assertEqual(status, 200)
        warning_codes = {w["code"] for w in body["warnings"]}
        self.assertIn("material_archived", warning_codes)
        self.assertIn("source_review_not_ready", warning_codes)


if __name__ == "__main__":
    unittest.main()