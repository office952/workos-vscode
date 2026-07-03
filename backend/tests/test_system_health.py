"""Tests for GET /api/v1/system/health (Sprint #40).

Covers:
  - 200 status + full check schema (all 5 check keys present)
  - happy path aggregate = "ok"
  - missing observation config -> warning/fail (not ok)
  - missing anchor order 14 -> warning (not ok)
  - version contract reuses /system/version resolver
  - seed_sync_all importable check
  - generated_at is a valid ISO-8601 UTC timestamp
  - service-level aggregate rules
  - DB failure surfaced as check.status="fail"
"""

from __future__ import annotations

import asyncio
import os
import sys
import unittest
from datetime import datetime
from unittest import mock

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core.database import get_db  # noqa: E402
from dependencies.auth import get_current_user  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402

# Ensure every model is registered before create_all.
from models.execution_observation_config import ExecutionObservationConfig  # noqa: E402,F401
from models.execution_plan import ExecutionPlan  # noqa: E402,F401
from models.execution_reality import ExecutionReality  # noqa: E402,F401
from models.orders import Orders  # noqa: E402,F401

from routers.system import router as system_router  # noqa: E402
from services.system_health_service import (  # noqa: E402
    STATUS_FAIL,
    STATUS_OK,
    STATUS_UNKNOWN,
    STATUS_WARNING,
    SystemHealthService,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


REQUIRED_CHECK_KEYS = {
    "database",
    "version",
    "seed_pipeline",
    "observation_thresholds",
    "execution_anchor_order_14",
}

_FAKE_ADMIN = UserResponse(
    id="test-admin-id",
    email="admin@test.local",
    name="Test Admin",
    role="admin",
)


def _build_app(fixture: IsolatedDBFixture) -> FastAPI:
    app = FastAPI()
    app.include_router(system_router)

    async def _override_get_db():
        async with fixture.session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: _FAKE_ADMIN
    return app


async def _seed_config(fixture: IsolatedDBFixture) -> None:
    async with fixture.session_maker() as s:
        s.add(
            ExecutionObservationConfig(
                id=1,
                warning_time_delta_pct=10.0,
                critical_time_delta_pct=20.0,
                warning_time_delta_minutes=15.0,
                critical_time_delta_minutes=30.0,
                is_active=True,
            )
        )
        await s.commit()


async def _seed_anchor_order_with_plan_and_reality(fixture: IsolatedDBFixture) -> None:
    async with fixture.session_maker() as s:
        s.add(
            Orders(
                id=14,
                code="ORD-ANCHOR-14",
                client_name="Anchor Client",
                status="locked",
            )
        )
        s.add(
            ExecutionPlan(
                order_id=14,
                order_code="ORD-ANCHOR-14",
                snapshot_version=1,
                tasks_json="[]",
                total_estimated_time_minutes=60.0,
            )
        )
        s.add(
            ExecutionReality(
                order_id=14,
                order_code="ORD-ANCHOR-14",
                tasks_json="[]",
                total_actual_time_minutes=60.0,
            )
        )
        await s.commit()


class SystemHealthHappyPathTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture()
        cls.db.setup()
        cls.db.run(_seed_config(cls.db))
        cls.db.run(_seed_anchor_order_with_plan_and_reality(cls.db))
        cls.app = _build_app(cls.db)
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def test_endpoint_returns_200_with_full_schema(self):
        resp = self.client.get("/api/v1/system/diagnostics")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("status", data)
        self.assertIn("checks", data)
        self.assertIn("generated_at", data)
        self.assertEqual(set(data["checks"].keys()), REQUIRED_CHECK_KEYS)
        for name, check in data["checks"].items():
            self.assertIn("status", check, f"{name} missing status")
            self.assertIn("details", check, f"{name} missing details")

    def test_generated_at_is_valid_iso_timestamp(self):
        resp = self.client.get("/api/v1/system/diagnostics")
        ts = resp.json()["generated_at"]
        # datetime.fromisoformat accepts "+00:00" offset produced by timezone.utc.
        parsed = datetime.fromisoformat(ts)
        self.assertIsNotNone(parsed.tzinfo, "generated_at must be timezone-aware")

    def test_happy_path_aggregate_is_ok(self):
        resp = self.client.get("/api/v1/system/diagnostics")
        data = resp.json()
        self.assertEqual(data["checks"]["database"]["status"], STATUS_OK)
        self.assertEqual(data["checks"]["seed_pipeline"]["status"], STATUS_OK)
        self.assertTrue(
            data["checks"]["seed_pipeline"]["details"]["seed_sync_all_importable"]
        )
        self.assertEqual(
            data["checks"]["observation_thresholds"]["status"], STATUS_OK
        )
        obs_details = data["checks"]["observation_thresholds"]["details"]
        self.assertEqual(obs_details["warning_threshold_pct"], 10.0)
        self.assertEqual(obs_details["critical_threshold_pct"], 20.0)
        self.assertEqual(obs_details["warning_threshold_minutes"], 15.0)
        self.assertEqual(obs_details["critical_threshold_minutes"], 30.0)
        self.assertTrue(obs_details["is_active"])

        anchor = data["checks"]["execution_anchor_order_14"]
        self.assertEqual(anchor["status"], STATUS_OK)
        self.assertTrue(anchor["details"]["order_exists"])
        self.assertTrue(anchor["details"]["has_plan"])
        self.assertTrue(anchor["details"]["has_reality"])
        self.assertEqual(anchor["details"]["observability_status"], "OK")

        # Version check must exist with the documented fields.
        ver = data["checks"]["version"]
        self.assertIn(ver["status"], (STATUS_OK, STATUS_WARNING))
        for field in (
            "app_name",
            "release_version",
            "environment",
            "release_scope",
            "source",
        ):
            self.assertIn(field, ver["details"])

        # When all five checks are ok, aggregate must be ok.
        if all(
            data["checks"][k]["status"] == STATUS_OK for k in REQUIRED_CHECK_KEYS
        ):
            self.assertEqual(data["status"], STATUS_OK)

    def test_version_contract_reused(self):
        """health.version.details mirrors /system/version output."""
        health = self.client.get("/api/v1/system/diagnostics").json()
        version = self.client.get("/api/v1/system/version").json()
        vd = health["checks"]["version"]["details"]
        self.assertEqual(vd["app_name"], version["app_name"])
        self.assertEqual(vd["release_version"], version["release_version"])
        self.assertEqual(vd["environment"], version["environment"])
        self.assertEqual(vd["release_scope"], version["release_scope"])
        self.assertEqual(vd["source"], version["source"])


class SystemHealthMissingConfigTest(unittest.TestCase):
    """No ExecutionObservationConfig row at all -> fail + aggregate fail."""

    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture()
        cls.db.setup()
        # NOTE: no config, no anchor order.
        cls.app = _build_app(cls.db)
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def test_missing_thresholds_surface_as_fail_not_ok(self):
        data = self.client.get("/api/v1/system/diagnostics").json()
        obs = data["checks"]["observation_thresholds"]
        self.assertEqual(obs["status"], STATUS_FAIL)
        self.assertEqual(obs["details"].get("reason"), "no_observation_config_rows")
        # Aggregate must reflect failure, not a fake ok.
        self.assertEqual(data["status"], STATUS_FAIL)

    def test_missing_anchor_order_surfaces_as_warning_not_ok(self):
        data = self.client.get("/api/v1/system/diagnostics").json()
        anchor = data["checks"]["execution_anchor_order_14"]
        self.assertIn(anchor["status"], (STATUS_WARNING, STATUS_FAIL, STATUS_UNKNOWN))
        self.assertNotEqual(anchor["status"], STATUS_OK)
        self.assertFalse(anchor["details"]["order_exists"])


class SystemHealthInactiveConfigTest(unittest.TestCase):
    """is_active=False -> observation_thresholds.status=warning."""

    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture()
        cls.db.setup()

        async def _seed_inactive():
            async with cls.db.session_maker() as s:
                s.add(
                    ExecutionObservationConfig(
                        id=1,
                        warning_time_delta_pct=10.0,
                        critical_time_delta_pct=20.0,
                        warning_time_delta_minutes=15.0,
                        critical_time_delta_minutes=30.0,
                        is_active=False,
                    )
                )
                await s.commit()

        cls.db.run(_seed_inactive())
        cls.app = _build_app(cls.db)
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def test_inactive_config_is_warning_not_ok(self):
        data = self.client.get("/api/v1/system/diagnostics").json()
        obs = data["checks"]["observation_thresholds"]
        self.assertEqual(obs["status"], STATUS_WARNING)
        self.assertEqual(obs["details"]["is_active"], False)
        self.assertEqual(obs["details"].get("reason"), "observation_config_inactive")


class SystemHealthUnitTest(unittest.TestCase):
    """Pure unit tests for the aggregator rules and seed import check."""

    def test_seed_pipeline_check_imports_and_validates_callable(self):
        check = SystemHealthService._check_seed_pipeline()
        self.assertEqual(check["status"], STATUS_OK)
        self.assertTrue(check["details"]["seed_sync_all_importable"])
        self.assertTrue(check["details"]["has_run_all_seeds_callable"])

    def test_aggregate_any_fail_is_fail(self):
        checks = {
            "a": {"status": STATUS_OK, "details": {}},
            "b": {"status": STATUS_FAIL, "details": {}},
            "c": {"status": STATUS_WARNING, "details": {}},
        }
        self.assertEqual(SystemHealthService._aggregate(checks), STATUS_FAIL)

    def test_aggregate_warning_when_unknown_or_warning_and_no_fail(self):
        checks_w = {
            "a": {"status": STATUS_OK, "details": {}},
            "b": {"status": STATUS_WARNING, "details": {}},
        }
        self.assertEqual(SystemHealthService._aggregate(checks_w), STATUS_WARNING)

        checks_u = {
            "a": {"status": STATUS_OK, "details": {}},
            "b": {"status": STATUS_UNKNOWN, "details": {}},
        }
        self.assertEqual(SystemHealthService._aggregate(checks_u), STATUS_WARNING)

    def test_aggregate_ok_only_when_everything_ok(self):
        checks = {
            "a": {"status": STATUS_OK, "details": {}},
            "b": {"status": STATUS_OK, "details": {}},
        }
        self.assertEqual(SystemHealthService._aggregate(checks), STATUS_OK)


class SystemHealthDatabaseFailTest(unittest.TestCase):
    """Simulate a DB failure at the service level."""

    def test_database_check_fails_when_execute_raises(self):
        class _BoomSession:
            async def execute(self, *_a, **_kw):
                raise RuntimeError("db_down")

        svc = SystemHealthService(_BoomSession())  # type: ignore[arg-type]

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(svc._check_database())
        finally:
            loop.close()

        self.assertEqual(result["status"], STATUS_FAIL)
        self.assertEqual(result["details"]["reason"], "db_ping_exception")
        self.assertEqual(result["details"]["exception_type"], "RuntimeError")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()