"""Tests for GET /api/v1/system/db-identity (diagnostic-only).

Covers:
  - 404 when feature flag is OFF
  - 200 + full schema when flag is ON
  - zero credentials in payload (no DATABASE_URL, no password)
  - host omitted when DEBUG_DB_IDENTITY_EXPOSE_HOST is not set
  - fingerprint is a 12-char lowercase hex
  - read-only: repeated calls never mutate counts
  - service-level unit test of the fingerprint function
"""

from __future__ import annotations

import os
import re
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core.database import get_db  # noqa: E402
from dependencies.auth import get_admin_user, get_current_user  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402

# Import models so metadata.create_all builds the five tables we count.
from models.execution_observation_config import ExecutionObservationConfig  # noqa: E402,F401
from models.execution_plan import ExecutionPlan  # noqa: E402,F401
from models.execution_reality import ExecutionReality  # noqa: E402,F401
from models.orders import Orders  # noqa: E402,F401

from routers.system import router as system_router  # noqa: E402

_FAKE_ADMIN = UserResponse(id="test-admin-id", email="admin@test.local", name="Test Admin", role="admin")
from services.db_identity_service import (  # noqa: E402
    DBIdentityService,
    _FEATURE_FLAG_ENABLE,
    _FEATURE_FLAG_EXPOSE_HOST,
    _fingerprint,
    expose_host,
    is_enabled,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


REQUIRED_FIELDS = {
    "release_version",
    "generated_at",
    "current_database",
    "current_schema",
    "current_user",
    "search_path",
    "counts",
    "probe_host_fingerprint_sha256_12",
    "notes",
}

FORBIDDEN_SUBSTRINGS = (
    "DATABASE_URL",
    "password",
    "PASSWORD",
    "postgres://",
    "postgresql://",
    "sqlite+aiosqlite://",
)


def _build_app(fixture: IsolatedDBFixture) -> FastAPI:
    app = FastAPI()
    app.include_router(system_router)

    async def _override_get_db():
        async with fixture.session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: _FAKE_ADMIN
    app.dependency_overrides[get_admin_user] = lambda: _FAKE_ADMIN
    return app


class _EnvPatch:
    """Tiny context manager for patching env vars inside a test."""

    def __init__(self, **overrides: str | None):
        self._overrides = overrides
        self._saved: dict[str, str | None] = {}

    def __enter__(self):
        for k, v in self._overrides.items():
            self._saved[k] = os.environ.get(k)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *exc):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class DBIdentityEndpointGatingTest(unittest.TestCase):
    """Endpoint is 404 by default and 200 only when flag is on."""

    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture()
        cls.db.setup()
        cls.app = _build_app(cls.db)
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def test_disabled_by_default_returns_404(self):
        with _EnvPatch(**{_FEATURE_FLAG_ENABLE: None}):
            self.assertFalse(is_enabled())
            resp = self.client.get("/api/v1/system/db-identity")
            self.assertEqual(resp.status_code, 404)
            body = resp.json()
            self.assertEqual(body.get("detail"), "db-identity endpoint is disabled")

    def test_enabled_returns_200_with_full_schema(self):
        with _EnvPatch(**{_FEATURE_FLAG_ENABLE: "true"}):
            self.assertTrue(is_enabled())
            resp = self.client.get("/api/v1/system/db-identity")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(REQUIRED_FIELDS.issubset(set(data.keys())))

    def test_host_omitted_unless_explicit_expose_flag(self):
        with _EnvPatch(
            **{
                _FEATURE_FLAG_ENABLE: "1",
                _FEATURE_FLAG_EXPOSE_HOST: None,
            }
        ):
            self.assertFalse(expose_host())
            resp = self.client.get("/api/v1/system/db-identity")
            data = resp.json()
            self.assertNotIn("server_addr", data)
            self.assertNotIn("server_port", data)
            self.assertFalse(data["notes"]["host_raw_exposed"])
            # Fingerprint is always present and always 12 hex chars.
            self.assertIn("probe_host_fingerprint_sha256_12", data)
            self.assertRegex(
                data["probe_host_fingerprint_sha256_12"], r"^[0-9a-f]{12}$"
            )

    def test_host_present_when_expose_flag_set(self):
        with _EnvPatch(
            **{
                _FEATURE_FLAG_ENABLE: "1",
                _FEATURE_FLAG_EXPOSE_HOST: "1",
            }
        ):
            self.assertTrue(expose_host())
            resp = self.client.get("/api/v1/system/db-identity")
            data = resp.json()
            # server_addr / server_port ARE present as keys, even if their
            # values are None under SQLite (no inet_server_addr() there).
            self.assertIn("server_addr", data)
            self.assertIn("server_port", data)
            self.assertTrue(data["notes"]["host_raw_exposed"])


class DBIdentityPayloadTest(unittest.TestCase):
    """Content rules: no credentials leak, counts are integers or markers."""

    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture()
        cls.db.setup()
        cls.app = _build_app(cls.db)
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def test_no_credentials_appear_anywhere_in_payload(self):
        with _EnvPatch(
            **{_FEATURE_FLAG_ENABLE: "1", _FEATURE_FLAG_EXPOSE_HOST: "1"}
        ):
            resp = self.client.get("/api/v1/system/db-identity")
            raw = resp.text
            for needle in FORBIDDEN_SUBSTRINGS:
                self.assertNotIn(
                    needle,
                    raw,
                    f"credential-like token {needle!r} leaked into payload",
                )

    def test_counts_are_integers_or_structural_markers(self):
        with _EnvPatch(**{_FEATURE_FLAG_ENABLE: "1"}):
            data = self.client.get("/api/v1/system/db-identity").json()
            self.assertIsInstance(data["counts"], dict)
            expected_tables = {
                "execution_observation_config",
                "orders",
                "quotes",
                "execution_plan",
                "execution_reality",
            }
            self.assertEqual(set(data["counts"].keys()), expected_tables)
            for name, val in data["counts"].items():
                if isinstance(val, int):
                    self.assertGreaterEqual(val, 0, f"{name} count is negative")
                else:
                    self.assertIsInstance(val, str)
                    self.assertTrue(
                        val == "table_not_present"
                        or val.startswith("error: "),
                        f"unexpected count marker for {name}: {val!r}",
                    )

    def test_notes_declare_readonly_contract(self):
        with _EnvPatch(**{_FEATURE_FLAG_ENABLE: "1"}):
            data = self.client.get("/api/v1/system/db-identity").json()
            notes = data["notes"]
            self.assertTrue(notes["read_only_endpoint"])
            self.assertTrue(notes["no_write_operations_performed"])
            self.assertTrue(notes["no_credentials_exposed"])
            self.assertTrue(notes["diagnostic_only"])
            self.assertIn("dialect", notes)

    def test_repeated_calls_do_not_mutate_counts(self):
        """Structural read-only guarantee: counts must be stable between
        two consecutive calls with no writes in between."""
        with _EnvPatch(**{_FEATURE_FLAG_ENABLE: "1"}):
            d1 = self.client.get("/api/v1/system/db-identity").json()
            d2 = self.client.get("/api/v1/system/db-identity").json()
            self.assertEqual(d1["counts"], d2["counts"])


class DBIdentityFingerprintUnitTest(unittest.TestCase):
    """Pure unit tests for the fingerprint function."""

    def test_fingerprint_is_12_hex_lowercase(self):
        fp = _fingerprint("neondb", "1.2.3.4", 5432, "neon", "public")
        self.assertRegex(fp, r"^[0-9a-f]{12}$")

    def test_fingerprint_changes_when_any_component_changes(self):
        a = _fingerprint("neondb", "1.2.3.4", 5432, "neon", "public")
        b = _fingerprint("neondb", "1.2.3.4", 5432, "neon", "other")
        c = _fingerprint("otherdb", "1.2.3.4", 5432, "neon", "public")
        d = _fingerprint("neondb", None, None, "neon", "public")
        self.assertEqual(len({a, b, c, d}), 4)

    def test_fingerprint_is_stable_for_same_inputs(self):
        a = _fingerprint("db", "h", 1, "u", "s")
        b = _fingerprint("db", "h", 1, "u", "s")
        self.assertEqual(a, b)


class DBIdentityServiceDialectTest(unittest.TestCase):
    """Verify the service degrades gracefully on SQLite (test dialect)."""

    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture()
        cls.db.setup()

    @classmethod
    def tearDownClass(cls):
        cls.db.teardown()

    def test_sqlite_dialect_returns_payload_without_raw_host(self):
        async def _run():
            async with self.db.session_maker() as session:
                svc = DBIdentityService(session)
                return await svc.run(release_version="v0.0-test")

        data = self.db.run(_run())
        # Required fields present.
        self.assertTrue(REQUIRED_FIELDS.issubset(set(data.keys())))
        # SQLite dialect → ro-transaction not applied (Postgres-only).
        self.assertFalse(data["notes"]["read_only_transaction_applied"])
        self.assertEqual(data["notes"]["dialect"], "sqlite")
        # Fingerprint always present.
        self.assertRegex(
            data["probe_host_fingerprint_sha256_12"], r"^[0-9a-f]{12}$"
        )
        # Host keys should NOT appear since expose flag is not set.
        with _EnvPatch(**{_FEATURE_FLAG_EXPOSE_HOST: None}):
            # re-run to confirm flag-gated omission
            data2 = self.db.run(_run())
            self.assertNotIn("server_addr", data2)
            self.assertNotIn("server_port", data2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()