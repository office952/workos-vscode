"""Sprint #20 — tests for the Workcenter Rates registry.

Covers:
  - Service-level invariants: status enum, active-requires-rate, code uniqueness.
  - Service CRUD happy paths.
  - `load_workcenter_rate_dict()` filters to active rows only.
  - HTTP admin router: list, get, create (validation errors), patch (invariant).
  - Seed is idempotent and produces 6 rows with `missing_price`.

Uses `IsolatedDBFixture` to bind an ephemeral SQLite DB to the global
`db_manager` so these tests are hermetic (no Neon Postgres, no global
state leakage).
"""

from __future__ import annotations

import os
import sys
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Ensure ORM metadata is populated before the fixture creates tables.
import models  # noqa: E402,F401
from dependencies.auth import get_current_user  # noqa: E402
from models.workcenter_rates import Workcenter_rates  # noqa: E402
from routers.admin_workcenter_rates import router as wc_rates_router  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402
from seeds.seed_workcenter_rates import (  # noqa: E402
    CANONICAL_WORKCENTERS,
    seed_workcenter_rates,
)
from services.workcenter_rates_service import (  # noqa: E402
    WorkcenterRateValidationError,
    create_workcenter_rate,
    get_workcenter_rate_by_code,
    list_workcenter_rates,
    load_workcenter_rate_pricing_dict,
    load_workcenter_rate_dict,
    update_workcenter_rate,
    validate_rate_contract,
    validate_status_and_rate,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


class WorkcenterRatesValidationTest(unittest.TestCase):
    """Pure synchronous validation unit tests (no DB needed)."""

    def test_validate_status_rejects_unknown_status(self) -> None:
        with self.assertRaises(WorkcenterRateValidationError):
            validate_status_and_rate("bogus", 50.0)

    def test_validate_active_requires_positive_rate(self) -> None:
        with self.assertRaises(WorkcenterRateValidationError):
            validate_status_and_rate("active", None)
        with self.assertRaises(WorkcenterRateValidationError):
            validate_status_and_rate("active", 0)
        with self.assertRaises(WorkcenterRateValidationError):
            validate_status_and_rate("active", -10)
        # valid:
        validate_status_and_rate("active", 120.5)

    def test_validate_non_active_allows_null_rate(self) -> None:
        validate_status_and_rate("missing_price", None)
        validate_status_and_rate("needs_owner_input", None)
        validate_status_and_rate("archived", None)

    def test_validate_rejects_negative_rate_even_when_non_active(self) -> None:
        with self.assertRaises(WorkcenterRateValidationError):
            validate_status_and_rate("missing_price", -5)

    def test_validate_active_cnc_requires_linear_basis(self) -> None:
        with self.assertRaises(WorkcenterRateValidationError):
            validate_rate_contract(
                code="CNC_ROUTER",
                status="active",
                is_active=True,
                rate_basis="per_hour",
                rate_per_hour=120.0,
                rate_per_linear_meter=None,
            )

        validate_rate_contract(
            code="CNC_ROUTER",
            status="active",
            is_active=True,
            rate_basis="per_linear_meter",
            rate_per_hour=None,
            rate_per_linear_meter=12.5,
        )


class WorkcenterRatesDBTest(unittest.TestCase):
    """Service + seed + router tests using an isolated SQLite DB."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_wc_rates_")
        cls.db.setup()

        async def _override_get_current_user():
            return UserResponse(
                id="test-user-id",
                email="test@example.com",
                name="Test Admin",
                role="admin",
                last_login=None,
            )

        cls.app = FastAPI()
        cls.app.include_router(wc_rates_router)
        cls.app.dependency_overrides[get_current_user] = _override_get_current_user
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.client.close()
        except Exception:
            pass
        cls.db.teardown()

    def setUp(self) -> None:
        # Each test starts with an empty table.
        self.db.reset_tables([Workcenter_rates])

    # ------------------------------------------------------------------
    # Service CRUD
    # ------------------------------------------------------------------

    def test_create_and_get_workcenter_rate(self) -> None:
        async def _run():
            async with self.db.session_maker() as session:
                created = await create_workcenter_rate(
                    session,
                    code="TEST_WC_CREATE_GET",
                    label="Test WC",
                    rate_per_hour=None,
                    status="missing_price",
                    notes="unit-test",
                )
                fetched = await get_workcenter_rate_by_code(
                    session, "TEST_WC_CREATE_GET"
                )
                return created, fetched

        created, fetched = self.db.run(_run())
        self.assertEqual(created["code"], "TEST_WC_CREATE_GET")
        self.assertIsNone(created["rate_per_hour"])
        self.assertEqual(created["status"], "missing_price")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["code"], "TEST_WC_CREATE_GET")

    def test_create_rejects_duplicate_code(self) -> None:
        async def _run():
            async with self.db.session_maker() as session:
                await create_workcenter_rate(
                    session, code="TEST_WC_DUP", label="A", status="missing_price"
                )
                with self.assertRaises(WorkcenterRateValidationError):
                    await create_workcenter_rate(
                        session, code="TEST_WC_DUP", label="B", status="missing_price"
                    )

        self.db.run(_run())

    def test_create_rejects_active_without_rate(self) -> None:
        async def _run():
            async with self.db.session_maker() as session:
                with self.assertRaises(WorkcenterRateValidationError):
                    await create_workcenter_rate(
                        session,
                        code="TEST_WC_ACTIVE_NO_RATE",
                        label="X",
                        status="active",
                    )

        self.db.run(_run())

    def test_patch_flips_to_active_when_rate_provided(self) -> None:
        async def _run():
            async with self.db.session_maker() as session:
                await create_workcenter_rate(
                    session,
                    code="TEST_WC_PATCH_ACTIVE",
                    label="X",
                    status="missing_price",
                )
                updated = await update_workcenter_rate(
                    session,
                    "TEST_WC_PATCH_ACTIVE",
                    rate_per_hour=120.0,
                    status="active",
                )
                return updated

        updated = self.db.run(_run())
        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], "active")
        self.assertEqual(updated["rate_per_hour"], 120.0)

    def test_patch_rejects_active_without_rate(self) -> None:
        async def _run():
            async with self.db.session_maker() as session:
                await create_workcenter_rate(
                    session,
                    code="TEST_WC_PATCH_BAD",
                    label="X",
                    status="missing_price",
                )
                with self.assertRaises(WorkcenterRateValidationError):
                    await update_workcenter_rate(
                        session, "TEST_WC_PATCH_BAD", status="active"
                    )

        self.db.run(_run())

    def test_load_workcenter_rate_dict_filters_to_active(self) -> None:
        async def _run():
            async with self.db.session_maker() as session:
                await create_workcenter_rate(
                    session,
                    code="TEST_WC_LOAD_ACTIVE",
                    label="A",
                    rate_per_hour=99.0,
                    status="active",
                )
                await create_workcenter_rate(
                    session,
                    code="TEST_WC_LOAD_MISSING",
                    label="M",
                    status="missing_price",
                )
            return await load_workcenter_rate_dict()

        d = self.db.run(_run())
        self.assertEqual(d.get("TEST_WC_LOAD_ACTIVE"), 99.0)
        self.assertNotIn("TEST_WC_LOAD_MISSING", d)

    def test_load_workcenter_rate_pricing_dict_supports_linear_basis(self) -> None:
        async def _run():
            async with self.db.session_maker() as session:
                await create_workcenter_rate(
                    session,
                    code="LASER_CUTTING",
                    label="Laser",
                    rate_basis="per_linear_meter",
                    rate_per_linear_meter=14.0,
                    status="active",
                    is_active=True,
                )
            return await load_workcenter_rate_pricing_dict()

        d = self.db.run(_run())
        self.assertIn("LASER_CUTTING", d)
        self.assertEqual(d["LASER_CUTTING"]["rate_basis"], "per_linear_meter")
        self.assertEqual(d["LASER_CUTTING"]["rate_per_linear_meter"], 14.0)

    # ------------------------------------------------------------------
    # Seed
    # ------------------------------------------------------------------

    def test_seed_workcenter_rates_is_idempotent_and_missing_price(self) -> None:
        async def _run():
            stats1 = await seed_workcenter_rates()
            stats2 = await seed_workcenter_rates()
            async with self.db.session_maker() as session:
                rows = await list_workcenter_rates(session)
            return stats1, stats2, rows

        stats1, stats2, rows = self.db.run(_run())
        self.assertEqual(
            stats1["inserted"] + stats1["skipped"], len(CANONICAL_WORKCENTERS)
        )
        self.assertEqual(stats2["inserted"], 0)
        self.assertEqual(stats2["skipped"], len(CANONICAL_WORKCENTERS))

        by_code = {r["code"]: r for r in rows}
        for wc in CANONICAL_WORKCENTERS:
            self.assertIn(wc["code"], by_code, msg=f"missing {wc['code']}")
            self.assertEqual(by_code[wc["code"]]["status"], "missing_price")
            self.assertIsNone(by_code[wc["code"]]["rate_per_hour"])

    # ------------------------------------------------------------------
    # HTTP admin router
    # ------------------------------------------------------------------

    def test_admin_router_list_and_get(self) -> None:
        self.db.run(seed_workcenter_rates())

        resp = self.client.get("/api/admin/workcenter-rates")
        self.assertEqual(resp.status_code, 200, msg=resp.text)
        body = resp.json()
        codes = {r["code"] for r in body}
        for wc in CANONICAL_WORKCENTERS:
            self.assertIn(wc["code"], codes)

        resp2 = self.client.get("/api/admin/workcenter-rates/CNC_ROUTER")
        self.assertEqual(resp2.status_code, 200, msg=resp2.text)
        self.assertEqual(resp2.json()["code"], "CNC_ROUTER")

        resp3 = self.client.get("/api/admin/workcenter-rates/DOES_NOT_EXIST")
        self.assertEqual(resp3.status_code, 404)

    def test_admin_router_create_rejects_active_without_rate(self) -> None:
        resp = self.client.post(
            "/api/admin/workcenter-rates",
            json={
                "code": "TEST_ROUTER_ACTIVE_NO_RATE",
                "label": "Bad",
                "status": "active",
            },
        )
        self.assertEqual(resp.status_code, 400, msg=resp.text)

    def test_admin_router_patch_enforces_invariant(self) -> None:
        test_code = "TEST_ROUTER_PATCH"

        c = self.client.post(
            "/api/admin/workcenter-rates",
            json={"code": test_code, "label": "P", "status": "missing_price"},
        )
        self.assertEqual(c.status_code, 201, msg=c.text)

        bad = self.client.patch(
            f"/api/admin/workcenter-rates/{test_code}",
            json={"status": "active"},
        )
        self.assertEqual(bad.status_code, 400, msg=bad.text)

        ok = self.client.patch(
            f"/api/admin/workcenter-rates/{test_code}",
            json={"status": "active", "rate_per_hour": 150.0},
        )
        self.assertEqual(ok.status_code, 200, msg=ok.text)
        self.assertEqual(ok.json()["status"], "active")
        self.assertEqual(ok.json()["rate_per_hour"], 150.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)