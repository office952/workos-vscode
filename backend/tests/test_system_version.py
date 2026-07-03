"""Tests for GET /api/v1/system/version (Sprint #38).

Covers:
  - 200 status + required fields in payload
  - env vars override release.json
  - fallback to release.json when env vars are absent
  - `source: "unknown"` when neither env nor file provide data
"""

import json
import os
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from main import app
from routers import system as system_router


_ENV_KEYS = list(system_router._ENV_KEYS.values())


def _clear_env(env: dict) -> dict:
    env = dict(env)
    for key in _ENV_KEYS:
        env.pop(key, None)
    return env


class SystemVersionEndpointTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    # ------------------------------------------------------------------
    # 1. Endpoint returns 200 + required fields
    # ------------------------------------------------------------------
    def test_endpoint_returns_200_with_required_fields(self) -> None:
        resp = self.client.get("/api/v1/system/version")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for key in (
            "app_name",
            "release_version",
            "release_label",
            "environment",
            "release_scope",
            "build_time",
            "source",
            "observed_at",
        ):
            self.assertIn(key, data, f"missing field: {key}")

    # ------------------------------------------------------------------
    # 2. Env vars override release.json
    # ------------------------------------------------------------------
    def test_env_vars_override_release_json(self) -> None:
        overrides = {
            "WORKOS_RELEASE_VERSION": "v999",
            "WORKOS_RELEASE_LABEL": "Test Override",
            "WORKOS_ENV": "live",
            "WORKOS_BUILD_TIME": "2026-05-02T00:00:00Z",
            "WORKOS_RELEASE_SCOPE": "/workspace/app",
            "WORKOS_APP_NAME": "WorkOS",
        }
        with mock.patch.dict(os.environ, overrides, clear=False):
            resp = self.client.get("/api/v1/system/version")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["release_version"], "v999")
        self.assertEqual(data["release_label"], "Test Override")
        self.assertEqual(data["environment"], "live")
        self.assertEqual(data["build_time"], "2026-05-02T00:00:00Z")
        self.assertIn(data["source"], ("env", "env+file"))

    # ------------------------------------------------------------------
    # 3. Fallback to release.json when env vars absent.
    #    Resolver walks _RELEASE_JSON_PATHS in strict order:
    #    canonical (/workspace/app/release.json) first,
    #    mirror    (/workspace/app/backend/release.json) second.
    # ------------------------------------------------------------------
    def test_fallback_to_release_json(self) -> None:
        candidate_paths = [Path(p) for p in system_router._RELEASE_JSON_PATHS]
        self.assertTrue(
            any(p.is_file() for p in candidate_paths),
            "At least one of canonical/mirror release.json must exist: "
            f"{candidate_paths}",
        )
        # The resolver returns the first readable file; match its preference.
        resolved_path = next(p for p in candidate_paths if p.is_file())
        file_data = json.loads(resolved_path.read_text(encoding="utf-8"))

        clean_env = _clear_env(os.environ)
        with mock.patch.dict(os.environ, clean_env, clear=True):
            resp = self.client.get("/api/v1/system/version")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["release_version"], file_data.get("release_version"))
        self.assertEqual(data["environment"], file_data.get("environment"))
        self.assertEqual(data["release_scope"], file_data.get("release_scope"))
        self.assertEqual(data["source"], "file")

    # ------------------------------------------------------------------
    # 4. Unknown when neither env nor file provide data.
    #    _read_release_json now returns a (payload, origin_path) tuple;
    #    simulate "no file found" by returning (None, None).
    # ------------------------------------------------------------------
    def test_source_unknown_when_nothing_available(self) -> None:
        clean_env = _clear_env(os.environ)
        with mock.patch.dict(os.environ, clean_env, clear=True), mock.patch.object(
            system_router, "_read_release_json", return_value=(None, None)
        ):
            resp = self.client.get("/api/v1/system/version")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["source"], "unknown")
        self.assertIsNone(data["release_version"])
        self.assertIsNone(data["environment"])

    # ------------------------------------------------------------------
    # 5. release_name hygiene in live/prod payloads.
    # ------------------------------------------------------------------
    def test_live_environment_sanitizes_staging_token_from_release_name(self) -> None:
        clean_env = _clear_env(os.environ)
        mocked_file = {
            "app_name": "WorkOS",
            "release_version": "v92.1",
            "environment": "live",
            "release_scope": "/workspace/app",
            "release_name": "workos-staging-release-BUILD_2626",
        }
        with mock.patch.dict(os.environ, clean_env, clear=True), mock.patch.object(
            system_router, "_read_release_json", return_value=(mocked_file, Path("/tmp/release.json"))
        ), mock.patch.object(system_router, "_read_release_manifest", return_value=(None, None)):
            resp = self.client.get("/api/v1/system/version")

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["environment"], "live")
        self.assertEqual(data["release_name"], "workos-release-BUILD_2626")
        self.assertNotIn("staging", data["release_name"].lower())


if __name__ == "__main__":
    unittest.main()