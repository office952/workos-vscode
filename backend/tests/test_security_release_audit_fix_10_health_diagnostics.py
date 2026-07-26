"""SECURITY_RELEASE_AUDIT_FIX_10 focused coverage.

Validates:
- public /api/v1/system/health is minimal and redacted
- detailed diagnostics are permission-gated
- diagnostics payload avoids raw stack/error leaks
- system version endpoint behavior remains available
"""

from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core.database import get_db  # noqa: E402
from dependencies.auth import get_current_user  # noqa: E402
from dependencies import permissions as permissions_module  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402

from models.execution_observation_config import ExecutionObservationConfig  # noqa: E402,F401
from models.execution_plan import ExecutionPlan  # noqa: E402,F401
from models.execution_reality import ExecutionReality  # noqa: E402,F401
from models.orders import Orders  # noqa: E402,F401
from routers.system import router as system_router  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


_FAKE_ADMIN = UserResponse(
    id="admin-user-id",
    email="admin@test.local",
    name="Admin",
    role="admin",
)

_FAKE_VIEWER = UserResponse(
    id="viewer-user-id",
    email="viewer@test.local",
    name="Viewer",
    role="viewer",
)

_FAKE_MANAGER = UserResponse(
    id="manager-user-id",
    email="manager@test.local",
    name="Manager",
    role="manager",
)


def _build_app(fixture: IsolatedDBFixture, current_user: UserResponse | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(system_router)

    async def _override_get_db():
        async with fixture.session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    if current_user is not None:
        app.dependency_overrides[get_current_user] = lambda: current_user
    return app


async def _seed_config_and_anchor(fixture: IsolatedDBFixture) -> None:
    async with fixture.session_maker() as session:
        session.add(
            ExecutionObservationConfig(
                id=1,
                warning_time_delta_pct=10.0,
                critical_time_delta_pct=20.0,
                warning_time_delta_minutes=15.0,
                critical_time_delta_minutes=30.0,
                is_active=True,
            )
        )
        session.add(
            Orders(
                id=14,
                code="ORD-ANCHOR-14",
                client_name="Anchor Client",
                status="locked",
            )
        )
        session.add(
            ExecutionPlan(
                order_id=14,
                order_code="ORD-ANCHOR-14",
                snapshot_version=1,
                tasks_json="[]",
                total_estimated_time_minutes=60.0,
            )
        )
        session.add(
            ExecutionReality(
                order_id=14,
                order_code="ORD-ANCHOR-14",
                tasks_json="[]",
                total_actual_time_minutes=60.0,
            )
        )
        await session.commit()


class PublicHealthContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture()
        cls.db.setup()
        cls.db.run(_seed_config_and_anchor(cls.db))
        cls.client = TestClient(_build_app(cls.db, current_user=None))

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def test_public_health_unauthenticated_returns_minimal_shape(self):
        resp = self.client.get("/api/v1/system/health")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(set(payload.keys()), {"status", "service", "generated_at", "checks"})
        self.assertEqual(payload["service"], "workos")
        self.assertIsInstance(payload["checks"], dict)

    def test_public_health_redacts_sensitive_diagnostics_fields(self):
        resp = self.client.get("/api/v1/system/health")
        self.assertEqual(resp.status_code, 200)
        raw = resp.text.lower()
        forbidden_tokens = (
            "environment",
            "release",
            "database",
            "db_status",
            "exception",
            "traceback",
            "migration",
            "current_head",
            "alembic",
        )
        for token in forbidden_tokens:
            self.assertNotIn(token, raw, f"public health leaked sensitive token: {token}")

    def test_public_health_ok_when_database_ok_even_if_optional_anchor_warns(self):
        """Missing execution_anchor must not alarm public chrome while DB is live."""
        # This fixture seeds config + anchor; force-missing anchor via patch on service.
        from services.system_health_service import SystemHealthService, STATUS_OK, STATUS_WARNING

        async def _fake_diagnostics(self):
            return {
                "status": STATUS_WARNING,
                "generated_at": "2026-07-26T00:00:00+00:00",
                "checks": {
                    "database": {"status": STATUS_OK, "details": {"ping": "SELECT 1"}},
                    "version": {"status": STATUS_OK, "details": {}},
                    "seed_pipeline": {"status": STATUS_OK, "details": {}},
                    "observation_thresholds": {"status": STATUS_OK, "details": {}},
                    "execution_anchor_order_14": {
                        "status": STATUS_WARNING,
                        "details": {"reason": "anchor_order_missing"},
                    },
                },
            }

        with mock.patch.object(SystemHealthService, "run_diagnostics", _fake_diagnostics):
            resp = self.client.get("/api/v1/system/health")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["status"], STATUS_OK)
        self.assertEqual(payload["checks"], {})


class DiagnosticsAuthorizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture()
        cls.db.setup()
        cls.db.run(_seed_config_and_anchor(cls.db))

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def test_unauthenticated_diagnostics_rejected(self):
        client = TestClient(_build_app(self.db, current_user=None))
        resp = client.get("/api/v1/system/diagnostics")
        self.assertIn(resp.status_code, (401, 403))

    def test_authenticated_without_permission_rejected(self):
        client = TestClient(_build_app(self.db, current_user=_FAKE_VIEWER))
        resp = client.get("/api/v1/system/diagnostics")
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_access_diagnostics(self):
        client = TestClient(_build_app(self.db, current_user=_FAKE_ADMIN))
        resp = client.get("/api/v1/system/diagnostics")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn("checks", payload)
        self.assertIn("database", payload["checks"])
        self.assertIn("version", payload["checks"])

    def test_explicit_permission_key_can_grant_non_admin_access(self):
        with mock.patch.dict(
            permissions_module.PERMISSION_MATRIX,
            {"system.diagnostics.read": ["admin", "manager"]},
            clear=False,
        ):
            client = TestClient(_build_app(self.db, current_user=_FAKE_MANAGER))
            resp = client.get("/api/v1/system/diagnostics")
            self.assertEqual(resp.status_code, 200)

    def test_diagnostics_do_not_expose_raw_stack_traces_or_secrets(self):
        client = TestClient(_build_app(self.db, current_user=_FAKE_ADMIN))
        resp = client.get("/api/v1/system/diagnostics")
        self.assertEqual(resp.status_code, 200)
        raw = resp.text.lower()
        forbidden_tokens = (
            "traceback",
            "stack",
            "database_url",
            "password",
            "jwt_secret",
            "exception_message",
        )
        for token in forbidden_tokens:
            self.assertNotIn(token, raw, f"diagnostics leaked forbidden token: {token}")


class VersionRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture()
        cls.db.setup()
        cls.client = TestClient(_build_app(cls.db, current_user=None))

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def test_system_version_endpoint_still_available(self):
        resp = self.client.get("/api/v1/system/version")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn("release_version", payload)
        self.assertIn("environment", payload)
        self.assertIn("source", payload)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
