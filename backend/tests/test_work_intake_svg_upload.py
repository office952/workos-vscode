"""Tests for server-backed Work Intake V2 SVG upload endpoint."""

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

_FIXTURE_SVG = (BACKEND_DIR.parent / "frontend" / "e2e" / "fixtures" / "lleexxaa.svg").read_text(encoding="utf-8")

_SIMPLE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100mm" height="50mm">
  <g id="layer-1" inkscape:label="TPL-VOLUMETRIC-LETTERS"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     inkscape:groupmode="layer">
    <rect x="0" y="0" width="100" height="50"/>
  </g>
</svg>
""".strip()


class WorkIntakeSvgUploadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_intake_svg_upload_")
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

    def _create_intake(self, code: str = "IR-SVG-UPLOAD-TEST", **spec_extra):
        payload = {
            "code": code,
            "client_name": "SVG Upload Client",
            "product_family": "litere_volumetrice",
            "status": "new",
            "product_spec_json": {
                "vector_file_name": "browser-proof.svg",
                "vector_parse_status": "parsed",
                "vector_detected_layer_count": 1,
                **spec_extra,
            },
        }
        response = self.client.post("/api/v1/entities/intake_requests", json=payload)
        self.assertEqual(response.status_code, 201, msg=response.text)
        return response.json()

    def test_valid_svg_upload_updates_vector_file_name(self) -> None:
        created = self._create_intake()
        files = {
            "file": ("owner-manual-svg-test.svg", _FIXTURE_SVG.encode("utf-8"), "image/svg+xml"),
        }
        response = self.client.post(
            f"/api/v1/entities/intake_requests/by-code/{created['code']}/svg-upload-and-analyze",
            files=files,
        )
        self.assertEqual(response.status_code, 200, msg=response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["filename"], "owner-manual-svg-test.svg")
        self.assertEqual(body["product_spec_json"]["vector_file_name"], "owner-manual-svg-test.svg")
        self.assertEqual(body["product_spec_json"]["vector_file_source"], "server_upload")

        get_r = self.client.get(f"/api/v1/entities/intake_requests/{created['id']}")
        self.assertEqual(get_r.status_code, 200)
        persisted = get_r.json()["product_spec_json"]
        self.assertEqual(persisted["vector_file_name"], "owner-manual-svg-test.svg")
        self.assertIn(persisted["vector_parse_status"], {"parsed", "parsed_sanitized"})

    def test_valid_svg_upload_returns_parsed_metadata(self) -> None:
        created = self._create_intake(code="IR-SVG-META")
        files = {"file": ("owner-manual-svg-test.svg", _SIMPLE_SVG.encode("utf-8"), "image/svg+xml")}
        response = self.client.post(
            f"/api/v1/entities/intake_requests/by-code/{created['code']}/svg-upload-and-analyze",
            files=files,
        )
        self.assertEqual(response.status_code, 200, msg=response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["vector_parse_status"], "parsed")
        self.assertEqual(body["vector_svg_viewbox"], "0 0 100 50")
        self.assertGreaterEqual(body["vector_detected_layer_count"], 1)
        self.assertTrue(body["vector_detected_layers"])

    def test_invalid_file_rejected(self) -> None:
        created = self._create_intake(code="IR-SVG-INVALID")
        files = {"file": ("notes.txt", b"hello", "text/plain")}
        response = self.client.post(
            f"/api/v1/entities/intake_requests/by-code/{created['code']}/svg-upload-and-analyze",
            files=files,
        )
        self.assertEqual(response.status_code, 400, msg=response.text)
        detail = response.json()["detail"]
        self.assertFalse(detail["ok"])
        self.assertEqual(detail["code"], "invalid_svg")

    def test_missing_intake_returns_404(self) -> None:
        files = {"file": ("owner-manual-svg-test.svg", _SIMPLE_SVG.encode("utf-8"), "image/svg+xml")}
        response = self.client.post(
            "/api/v1/entities/intake_requests/by-code/IR-DOES-NOT-EXIST/svg-upload-and-analyze",
            files=files,
        )
        self.assertEqual(response.status_code, 404, msg=response.text)
        detail = response.json()["detail"]
        self.assertFalse(detail["ok"])
        self.assertEqual(detail["code"], "intake_not_found")

    def test_product_spec_json_contains_vector_parse_status_parsed(self) -> None:
        created = self._create_intake(code="IR-SVG-PARSE-STATUS")
        files = {"file": ("owner-manual-svg-test.svg", _SIMPLE_SVG.encode("utf-8"), "image/svg+xml")}
        response = self.client.post(
            f"/api/v1/entities/intake_requests/by-code/{created['code']}/svg-upload-and-analyze",
            files=files,
        )
        self.assertEqual(response.status_code, 200, msg=response.text)
        spec = response.json()["product_spec_json"]
        self.assertEqual(spec["vector_parse_status"], "parsed")
        self.assertTrue(spec["vector_svg_analyzed"])
        self.assertEqual(spec["vector_metrics_source"], "svg_analysis")

    def test_lleexxaa_upload_persists_geometry_suggestions(self) -> None:
        created = self._create_intake(code="IR-SVG-LLEEXXAA")
        files = {"file": ("lleexxaa.svg", _FIXTURE_SVG.encode("utf-8"), "image/svg+xml")}
        response = self.client.post(
            f"/api/v1/entities/intake_requests/by-code/{created['code']}/svg-upload-and-analyze",
            files=files,
        )
        self.assertEqual(response.status_code, 200, msg=response.text)
        spec = response.json()["product_spec_json"]
        self.assertIn(spec["vector_parse_status"], {"parsed", "parsed_sanitized"})
        self.assertGreater(float(spec.get("vector_suggested_letter_perimeter_m") or 0), 1.0)
        self.assertGreater(float(spec.get("vector_suggested_letter_face_area_m2") or 0), 0.1)
        self.assertGreater(float(spec.get("vector_suggested_letter_layer_width_mm") or 0), 3000.0)
        self.assertGreater(int(spec.get("vector_suggested_letter_count") or 0), 0)
        self.assertFalse(spec.get("vector_geometry_analyzed"))
        support_w = float(spec.get("vector_suggested_support_width_mm") or 0)
        letter_w = float(spec.get("vector_suggested_letter_layer_width_mm") or 0)
        self.assertGreater(support_w, 0)
        self.assertNotEqual(support_w, letter_w)

    def test_uploaded_file_stored_outside_gitignored_path(self) -> None:
        created = self._create_intake(code="IR-SVG-STORAGE")
        files = {"file": ("owner-manual-svg-test.svg", _SIMPLE_SVG.encode("utf-8"), "image/svg+xml")}
        response = self.client.post(
            f"/api/v1/entities/intake_requests/by-code/{created['code']}/svg-upload-and-analyze",
            files=files,
        )
        self.assertEqual(response.status_code, 200, msg=response.text)
        storage_path = (
            BACKEND_DIR / "storage" / "intake_svg_uploads" / created["code"] / "owner-manual-svg-test.svg"
        )
        self.assertTrue(storage_path.exists())
        self.assertIn(b"<svg", storage_path.read_bytes())
