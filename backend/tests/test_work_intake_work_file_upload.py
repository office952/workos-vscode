"""Tests for production work file upload/download endpoints."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("ENVIRONMENT", "dev")

from fastapi.testclient import TestClient  # noqa: E402

import models  # noqa: F401,E402
from dependencies.auth import get_current_user  # noqa: E402
from models.intake_requests import Intake_requests  # noqa: E402
from models.product_families import Product_families  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402

_FAKE_ADMIN = UserResponse(id="test-admin-id", email="admin@test.local", name="Test Admin", role="admin")


class WorkIntakeWorkFileUploadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_intake_work_file_")
        cls.db.setup()
        from main import app  # noqa: E402

        app.dependency_overrides[get_current_user] = lambda: _FAKE_ADMIN
        cls.app = app
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.client.close()
        except Exception:
            pass
        cls.app.dependency_overrides.pop(get_current_user, None)
        cls.db.teardown()

    def setUp(self) -> None:
        self.db.reset_tables([Intake_requests, Product_families])
        self.db.run(self._seed_litere_family())

    async def _seed_litere_family(self):
        async with self.db.session_maker() as s:
            s.add(
                Product_families(
                    family_id="litere_volumetrice",
                    label="Litere volumetrice",
                    category="semnalistica",
                    active=True,
                )
            )
            await s.commit()

    def _create_intake(self, code: str = "IR-WORK-FILE-TEST", **spec_extra):
        payload = {
            "code": code,
            "client_name": "Work File Client",
            "status": "new",
            "product_family": "litere_volumetrice",
            "product_spec_json": {**spec_extra},
        }
        response = self.client.post("/api/v1/entities/intake_requests", json=payload)
        self.assertEqual(response.status_code, 201, msg=response.text)
        return response.json()

    def test_upload_cdr_work_file_persists_and_downloads(self):
        created = self._create_intake()
        response = self.client.post(
            f"/api/v1/entities/intake_requests/by-code/{created['code']}/work-file-upload",
            files={"file": ("master.cdr", b"CorelDRAW dummy", "application/octet-stream")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["work_file"]["fileName"], "master.cdr")
        self.assertEqual(body["work_file"]["extension"], ".cdr")
        self.assertEqual(body["work_file"]["role"], "master_work_file")
        self.assertIn("cnc", body["work_file"]["usableFor"])

        get_r = self.client.get(f"/api/v1/entities/intake_requests/{created['id']}")
        raw_spec = get_r.json()["product_spec_json"]
        spec = raw_spec if isinstance(raw_spec, dict) else json.loads(raw_spec)
        self.assertEqual(spec["workFileAttachments"][0]["fileName"], "master.cdr")

        file_id = body["work_file"]["id"]
        download = self.client.get(
            f"/api/v1/entities/intake_requests/by-code/{created['code']}/work-files/{file_id}/download"
        )
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.content, b"CorelDRAW dummy")

    def test_upload_rejects_unsupported_extension(self):
        created = self._create_intake(code="IR-WORK-FILE-BAD")
        response = self.client.post(
            f"/api/v1/entities/intake_requests/by-code/{created['code']}/work-file-upload",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertFalse(detail["ok"])
        self.assertEqual(detail["code"], "invalid_file")


if __name__ == "__main__":
    unittest.main()
