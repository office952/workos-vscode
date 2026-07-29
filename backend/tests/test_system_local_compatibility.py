"""GET /api/v1/system/local-compatibility — local DEV identity (no DB)."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from main import app
from routers import system as system_router
from services.dec009_materialize_gate import (
    BATCH_EXECUTE_MATERIALIZE_AUTHORIZED,
    LIVE_DEC009_STATUS,
    OD3_MIN_MERGE_COMMIT,
    OD3_RUNTIME_IDENTITY_VERSION,
    SCOPED_B_STAMP_STATUS,
    build_od3_runtime_identity,
)


class SystemLocalCompatibilityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_endpoint_returns_workos_contract_and_capabilities(self) -> None:
        resp = self.client.get("/api/v1/system/local-compatibility")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["service"], "workos-backend")
        self.assertEqual(data["contract"], system_router.LOCAL_COMPAT_CONTRACT)
        self.assertIsInstance(data["capabilities"], list)
        for required in system_router.LOCAL_COMPAT_CAPABILITIES:
            self.assertIn(required, data["capabilities"])
        self.assertIn("observed_at", data)
        # No secrets / path leakage
        joined = str(data)
        self.assertNotIn("JWT", joined)
        self.assertNotIn("secret", joined.lower())
        self.assertNotIn("DATABASE_URL", joined)

    def test_endpoint_exposes_od3_runtime_identity(self) -> None:
        """14D: stale/pre-OD3 runtimes omit capability + od3_dec009_gate."""
        resp = self.client.get("/api/v1/system/local-compatibility")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("execution.dec009_od3_gate", data["capabilities"])
        gate = data["od3_dec009_gate"]
        expected = build_od3_runtime_identity()
        self.assertEqual(gate, expected)
        self.assertTrue(gate["gate_landed"])
        self.assertEqual(gate["identity_version"], OD3_RUNTIME_IDENTITY_VERSION)
        self.assertEqual(gate["min_merge_commit"], OD3_MIN_MERGE_COMMIT)
        self.assertEqual(gate["live_dec009"], LIVE_DEC009_STATUS)
        self.assertEqual(gate["scoped_b_stamp"], SCOPED_B_STAMP_STATUS)
        self.assertIs(gate["batch_execute_materialize_authorized"], False)
        self.assertIs(BATCH_EXECUTE_MATERIALIZE_AUTHORIZED, False)

    def test_openapi_lists_local_compatibility_route(self) -> None:
        resp = self.client.get("/openapi.json")
        self.assertEqual(resp.status_code, 200)
        paths = resp.json().get("paths") or {}
        self.assertIn("/api/v1/system/local-compatibility", paths)


if __name__ == "__main__":
    unittest.main()
