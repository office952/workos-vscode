"""Tests for intake_requests.product_spec_json persistence."""

from __future__ import annotations

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


class IntakeProductSpecJsonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = IsolatedDBFixture(prefix="mgx_intake_spec_")
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

    def _create_intake_payload(self, **extra):
        base = {
            "code": "IR-SPEC-TEST",
            "client_name": "Spec Client",
            "product_family": "litere_volumetrice",
            "status": "new",
        }
        base.update(extra)
        return base

    def test_create_with_product_spec_json_round_trip(self) -> None:
        spec = {
            "text": "DEDEMAN",
            "font": "Helvetica Bold",
            "letter_height_mm": 600,
            "return_depth_mm": 80,
            "illumination_type": "halo",
            "face_finish": "plexi",
            "ral_color": "RAL 9005",
            "indoor_outdoor": "outdoor",
            "mounting_type": "premounted",
            "premounting_type": "acm_casetted_panel",
            "backing_chamfer": True,
            "notes": "Premontaj ACM separat de spate Forex",
        }
        r = self.client.post(
            "/api/v1/entities/intake_requests",
            json=self._create_intake_payload(product_spec_json=spec),
        )
        self.assertEqual(r.status_code, 201, msg=r.text)
        body = r.json()
        self.assertEqual(body["product_spec_json"]["text"], "DEDEMAN")
        self.assertEqual(body["product_spec_json"]["illumination_type"], "halo")
        self.assertTrue(body["product_spec_json"]["backing_chamfer"])

        get_r = self.client.get(f"/api/v1/entities/intake_requests/{body['id']}")
        self.assertEqual(get_r.status_code, 200)
        self.assertEqual(get_r.json()["product_spec_json"]["letter_height_mm"], 600)

    def test_create_without_product_spec_json_backward_compatible(self) -> None:
        r = self.client.post(
            "/api/v1/entities/intake_requests",
            json=self._create_intake_payload(code="IR-SPEC-LEGACY"),
        )
        self.assertEqual(r.status_code, 201, msg=r.text)
        self.assertIsNone(r.json().get("product_spec_json"))

    def test_update_preserves_and_clears_product_spec_json(self) -> None:
        create_r = self.client.post(
            "/api/v1/entities/intake_requests",
            json=self._create_intake_payload(
                code="IR-SPEC-UPD",
                product_spec_json={"text": "BT", "illumination_type": "backlit"},
            ),
        )
        self.assertEqual(create_r.status_code, 201)
        iid = create_r.json()["id"]

        upd_r = self.client.put(
            f"/api/v1/entities/intake_requests/{iid}",
            json={"product_spec_json": {"text": "BT BANK", "letter_height_mm": 450}},
        )
        self.assertEqual(upd_r.status_code, 200, msg=upd_r.text)
        self.assertEqual(upd_r.json()["product_spec_json"]["text"], "BT BANK")
        self.assertEqual(upd_r.json()["product_spec_json"]["letter_height_mm"], 450)

        clear_r = self.client.put(
            f"/api/v1/entities/intake_requests/{iid}",
            json={"product_spec_json": None},
        )
        self.assertEqual(clear_r.status_code, 200, msg=clear_r.text)
        self.assertIsNone(clear_r.json().get("product_spec_json"))

    def test_invalid_product_spec_json_rejected(self) -> None:
        r = self.client.post(
            "/api/v1/entities/intake_requests",
            json=self._create_intake_payload(
                code="IR-SPEC-BAD",
                product_spec_json={"illumination_type": "neon_party"},
            ),
        )
        self.assertEqual(r.status_code, 422, msg=r.text)

    def test_strips_unknown_keys(self) -> None:
        r = self.client.post(
            "/api/v1/entities/intake_requests",
            json=self._create_intake_payload(
                code="IR-SPEC-STRIP",
                product_spec_json={"text": "X", "future_field": "ignored"},
            ),
        )
        self.assertEqual(r.status_code, 201, msg=r.text)
        spec = r.json()["product_spec_json"]
        self.assertEqual(spec["text"], "X")
        self.assertNotIn("future_field", spec)

    def test_update_preserves_svg_letter_group_assignment_round_trip(self) -> None:
        create_r = self.client.post(
            "/api/v1/entities/intake_requests",
            json=self._create_intake_payload(
                code="IR-SPEC-LETTER-GROUPS",
                product_spec_json={"vector_file_name": "publi-cadru-fx.svg"},
            ),
        )
        self.assertEqual(create_r.status_code, 201, msg=create_r.text)
        iid = create_r.json()["id"]

        spec = {
            "vector_file_name": "publi-cadru-fx.svg",
            "svgLetterGroups": [
                {
                    "groupId": "fill-e31e24",
                    "sourceLayerName": "Litere_x0020_volumetrice",
                    "sourceFillColor": "#E31E24",
                    "visualLabel": "Grup #E31E24",
                    "elementCount": 1,
                    "status": "suggested",
                },
                {
                    "groupId": "fill-393185",
                    "sourceLayerName": "Litere_x0020_volumetrice",
                    "sourceFillColor": "#393185",
                    "visualLabel": "Grup #393185",
                    "elementCount": 1,
                    "status": "suggested",
                },
            ],
            "letterGroupFinishAssignments": [
                {
                    "groupId": "fill-e31e24",
                    "face": {"finishType": "oracal", "colorCode": "test red"},
                    "returnCant": {"finishType": "same_as_face", "depthMm": 60},
                    "confirmedByOperator": True,
                },
                {
                    "groupId": "fill-393185",
                    "face": {"finishType": "oracal", "colorCode": "test blue"},
                    "returnCant": {"finishType": "oracal_wrapped", "depthMm": 60},
                    "confirmedByOperator": True,
                },
            ],
            "svgArtworkLayersPending": [
                {
                    "layerId": "Emblema",
                    "layerName": "Emblema",
                    "elementCount": 510,
                    "distinctFillCount": 242,
                    "note": "Artwork multicolor",
                }
            ],
        }
        upd_r = self.client.put(
            f"/api/v1/entities/intake_requests/{iid}",
            json={"product_spec_json": spec},
        )
        self.assertEqual(upd_r.status_code, 200, msg=upd_r.text)
        body = upd_r.json()["product_spec_json"]
        self.assertEqual(len(body["svgLetterGroups"]), 2)
        self.assertEqual(body["svgLetterGroups"][0]["groupId"], "fill-e31e24")
        self.assertEqual(body["letterGroupFinishAssignments"][0]["returnCant"]["depthMm"], 60.0)
        self.assertEqual(body["svgArtworkLayersPending"][0]["layerName"], "Emblema")

        get_r = self.client.get(f"/api/v1/entities/intake_requests/{iid}")
        self.assertEqual(get_r.status_code, 200)
        persisted = get_r.json()["product_spec_json"]
        self.assertEqual(len(persisted["svgLetterGroups"]), 2)
        self.assertEqual(
            persisted["letterGroupFinishAssignments"][1]["face"]["colorCode"],
            "test blue",
        )
        self.assertEqual(persisted["svgArtworkLayersPending"][0]["distinctFillCount"], 242)


if __name__ == "__main__":
    unittest.main(verbosity=2)
