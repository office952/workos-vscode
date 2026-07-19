"""GET /api/v1/system/local-compatibility — local DEV identity (no DB)."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from main import app
from routers import system as system_router


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

    def test_openapi_lists_local_compatibility_route(self) -> None:
        resp = self.client.get("/openapi.json")
        self.assertEqual(resp.status_code, 200)
        paths = resp.json().get("paths") or {}
        self.assertIn("/api/v1/system/local-compatibility", paths)


if __name__ == "__main__":
    unittest.main()
