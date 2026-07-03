"""Tests for artwork print file upload endpoint."""

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


class WorkIntakeArtworkPrintUploadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_intake_artwork_print_")
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

    def _create_intake(self, code: str = "IR-ARTWORK-PRINT", **spec_extra):
        payload = {
            "code": code,
            "client_name": "Artwork Print Client",
            "status": "new",
            "product_family": "litere_volumetrice",
            "product_spec_json": {
                "svgArtworkLayersPending": [
                    {
                        "layerId": "Emblema",
                        "layerName": "Emblema",
                        "elementCount": 510,
                        "distinctFillCount": 242,
                    }
                ],
                **spec_extra,
            },
        }
        response = self.client.post("/api/v1/entities/intake_requests", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_upload_print_file_persists_assignment(self):
        created = self._create_intake()
        response = self.client.post(
            f"/api/v1/entities/intake_requests/by-code/{created['code']}/artwork-print-upload",
            params={"layer_id": "Emblema"},
            files={"file": ("emblema-print.pdf", b"%PDF-1.4 test", "application/pdf")},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["layer_id"], "Emblema")
        self.assertEqual(body["print_file"]["fileName"], "emblema-print.pdf")

        get_r = self.client.get(f"/api/v1/entities/intake_requests/{created['id']}")
        self.assertEqual(get_r.status_code, 200)
        raw_spec = get_r.json()["product_spec_json"]
        spec = raw_spec if isinstance(raw_spec, dict) else json.loads(raw_spec)
        assignment = spec["svgArtworkFinishAssignments"][0]
        self.assertEqual(assignment["layerId"], "Emblema")
        self.assertEqual(assignment["printFile"]["fileName"], "emblema-print.pdf")
        self.assertEqual(assignment["printFile"]["storedFileName"], "emblema-print.pdf")

    def test_upload_rejects_unsupported_extension(self):
        created = self._create_intake(code="IR-ARTWORK-PRINT-BAD")
        response = self.client.post(
            f"/api/v1/entities/intake_requests/by-code/{created['code']}/artwork-print-upload",
            params={"layer_id": "Emblema"},
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertFalse(detail["ok"])
        self.assertEqual(detail["code"], "invalid_file")


if __name__ == "__main__":
    unittest.main()
