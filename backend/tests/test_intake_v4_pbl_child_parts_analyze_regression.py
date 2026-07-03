"""Regression: PBL-like SVG analysis must preserve child parts, not layer-level collapse."""

from __future__ import annotations

import json
from pathlib import Path

import asyncio

import pytest
from fastapi import HTTPException

from schemas.intake_v4 import PILOT_V4_TEMPLATE_CODE
from services.intake_v4_analysis_bundle_guard_service import (
    analysis_bundle_has_degraded_child_parts,
    assert_analysis_bundle_child_parts_or_raise,
)
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "intake_v4"
PBL_LAYERE_SVG = (
    Path(__file__).parent.parent.parent
    / "frontend"
    / "src"
    / "lib"
    / "svgAnalyzer"
    / "fixtures"
    / "pbl-layere.svg"
)
GOLDEN_ANALYSIS = FIXTURE_DIR / "pbl_layere_golden_analysis.json"
DEGRADED_ANALYSIS = FIXTURE_DIR / "pbl_layere_degraded_analysis.json"


@pytest.fixture(scope="module")
def seeded_db(db_fixture):
    from seeds.seed_build4_templates import seed_build4_templates

    asyncio.get_event_loop().run_until_complete(seed_build4_templates())
    return db_fixture


@pytest.fixture
def v4_client(seeded_db):
    from main import app
    from core.database import get_db
    from dependencies.auth import get_current_user
    from schemas.auth import UserResponse
    from fastapi.testclient import TestClient

    async def _override_get_db():
        async with seeded_db.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test Admin",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pbl_layer_role_setup() -> dict:
    return {
        "confirmation_status": "complete",
        "layers": [
            {
                "layer_key": "Layer_x0020_1",
                "layer_name": "Layer_x0020_1",
                "auto_role": "printed_artwork",
                "auto_confidence": "high",
                "confirmed_role": "printed_artwork",
                "confirmation_state": "confirmed",
                "artwork_execution": "needs_decision",
            },
            {
                "layer_key": "Layer_x0020_2",
                "layer_name": "Layer_x0020_2",
                "auto_role": "face",
                "auto_confidence": "high",
                "confirmed_role": "face",
                "confirmation_state": "confirmed",
            },
            {
                "layer_key": "Layer_x0020_3",
                "layer_name": "Layer_x0020_3",
                "auto_role": "face",
                "auto_confidence": "high",
                "confirmed_role": "face",
                "confirmation_state": "confirmed",
            },
        ],
        "warnings": [],
    }


def _payload_with_analysis(analysis: dict) -> dict:
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
        "svg_analysis_json": analysis,
        "layer_role_setup": _pbl_layer_role_setup(),
        "finish_setup": {
            "face_finish_type": "none",
            "return_finish_type": "standard_aluminum",
            "return_depth_mm": 60,
            "illuminated": True,
            "confirmed": True,
            "letter_group_finishes": [
                {
                    "group_key": "Layer_x0020_2",
                    "layer_name": "Layer_x0020_2",
                    "face_finish_type": "none",
                },
                {
                    "group_key": "Layer_x0020_3",
                    "layer_name": "Layer_x0020_3",
                    "face_finish_type": "none",
                },
            ],
        },
        "quote_geometry": {
            "letter_count": 10,
            "real_letters_count": 10,
            "artwork_piece_count": 1,
            "face_area_m2": 0.5834,
            "return_material_perimeter_ml": 14.5711,
        },
        "path_geometry_summary": {"parse_status": "parsed", "face_area_m2": 0.5834},
        "svg_source": {
            "file_name": "pbl-layere.svg",
            "file_size_bytes": 5631,
            "file_hash": "c674e8a3",
            "upload_status": "analyzed",
        },
    }


class TestPblChildPartsGuard:
    def test_detects_degraded_three_part_bundle(self):
        degraded = _load_json(DEGRADED_ANALYSIS)
        assert analysis_bundle_has_degraded_child_parts(degraded) is True

    def test_accepts_golden_eleven_part_bundle(self):
        golden = _load_json(GOLDEN_ANALYSIS)
        assert analysis_bundle_has_degraded_child_parts(golden) is False

    def test_assert_raises_for_degraded_bundle(self):
        degraded = _load_json(DEGRADED_ANALYSIS)
        with pytest.raises(HTTPException) as exc:
            assert_analysis_bundle_child_parts_or_raise(degraded)
        assert exc.value.detail["error"] == "degraded_child_parts_analysis"


class TestPblChildPartsAnalysisBundleApi:
    def test_analysis_bundle_rejects_degraded_client_parts(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "PBL degraded guard", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        svg_text = PBL_LAYERE_SVG.read_text(encoding="utf-8")
        degraded = _load_json(DEGRADED_ANALYSIS)

        response = v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
            json={
                "file_name": "pbl-layere.svg",
                "file_size_bytes": len(svg_text.encode("utf-8")),
                "svg_text": svg_text,
                "svg_analysis_json": degraded,
                "layer_role_setup": _pbl_layer_role_setup(),
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "degraded_child_parts_analysis"

    def test_analysis_bundle_accepts_golden_child_parts(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "PBL golden child parts", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        svg_text = PBL_LAYERE_SVG.read_text(encoding="utf-8")
        golden = _load_json(GOLDEN_ANALYSIS)

        response = v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
            json={
                "file_name": "pbl-layere.svg",
                "file_size_bytes": len(svg_text.encode("utf-8")),
                "svg_text": svg_text,
                "svg_analysis_json": golden,
                "layer_role_setup": _pbl_layer_role_setup(),
            },
        )
        assert response.status_code == 200, response.text
        parts = response.json()["payload"]["svg_analysis_json"]["parts"]
        assert parts["count"] == 11
        assert parts["splitDiagnostics"]["groupsCreated"] == 10


class TestPblChildPartsDownstreamMetrics:
    def test_material_breakdown_uses_child_footprint_not_full_sheet(self):
        golden = _load_json(GOLDEN_ANALYSIS)
        payload = _payload_with_analysis(golden)
        breakdown = build_intake_v4_material_breakdown("ws-pbl-golden", payload)
        plexi_rows = [
            row
            for row in breakdown.material_rows
            if row.material_key == "plexiglas_face" and row.quantity_basis != "absent"
        ]
        assert plexi_rows, "expected plexiglas face row"
        assert all(row.quantity is not None and row.quantity < 1.0 for row in plexi_rows)
        assert all(row.quantity != 6.0 for row in plexi_rows)

        preview = breakdown.nesting_preview
        assert preview is not None
        active = [sheet for sheet in preview.sheets if sheet.is_active_for_breakdown]
        assert active, "expected active nesting sheet layout"
        assert preview.summary.nestable_parts >= 8
        assert preview.summary.artwork_parts == 1
