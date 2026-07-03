"""Intake V3 SVG upload + raw analysis — draft workspace only, no side effects."""

from __future__ import annotations

from services.intake_v3_svg_analysis_service import (
    WARNING_MISSING_VIEW_BOX,
    WARNING_TEXT_NOT_CONVERTED_TO_PATHS,
)

VALID_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100mm" height="50mm">
  <g id="letters">
    <path id="letter-a" d="M10 40 L20 10 L30 40 Z" fill="#ff0000" stroke="#000000"/>
    <path id="letter-b" d="M40 40 L40 10 L55 10 Q60 10 60 20 Q60 30 55 30 L40 30" fill="#00ff00"/>
  </g>
</svg>"""

SVG_WITH_TEXT = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50" width="50" height="50">
  <text x="5" y="20">HELLO</text>
  <path d="M0 0 L10 10 Z" fill="#abc"/>
</svg>"""

SVG_MISSING_VIEWBOX = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <path d="M0 0 L10 10 Z" fill="blue"/>
</svg>"""

SVG_WITH_SCRIPT = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
  <script>alert(1)</script>
  <path d="M0 0 L1 1 Z"/>
</svg>"""

MINIMAL_WORKSPACE_PAYLOAD = {
    "client_request": {
        "client_name": "SVG Test Client",
        "request_code": "SVG-TEST-001",
        "job_title": "SVG upload test",
        "width_mm": 1000,
        "height_mm": 500,
    },
    "product_selection": {"template_code": "TPL-VOLUMETRIC-LETTERS", "pilot_scope": True},
    "material_intent": {"inventory_mutation_allowed": False, "estimate_status": "not_started"},
    "production_handoff": {"preview_only": True},
    "employee_preview_seed": {"non_executable": True, "preview_tasks": []},
}


def _create_workspace(auth_client, payload: dict | None = None) -> str:
    response = auth_client.post(
        "/api/v1/intake-v3/workspaces",
        json={"title": "SVG upload test", "payload": payload or MINIMAL_WORKSPACE_PAYLOAD},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _upload_svg(auth_client, workspace_id: str, filename: str, content: str, content_type: str = "image/svg+xml"):
    return auth_client.post(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/svg",
        files={"file": (filename, content, content_type)},
    )


class TestIntakeV3SvgUploadAnalysis:
    def test_upload_valid_svg_on_draft_workspace(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        response = _upload_svg(auth_client, workspace_id, "letters.svg", VALID_SVG)
        assert response.status_code == 200
        body = response.json()

        analysis = body["raw_svg_analysis"]
        assert analysis["path_count"] == 2
        assert analysis["closed_contour_count"] >= 1
        assert body["workspace"]["payload"]["raw_svg_analysis"]["path_count"] == 2
        assert body["workspace"]["payload"]["vector_asset"]["file_name"] == "letters.svg"
        assert body["workspace"]["payload"]["raw_analysis_status"] == "analyzed"
        assert body["preview"]["preview"] is not None
        assert body["workspace"].get("created_quote_id") is None
        assert body["workspace"].get("order_id") is None
        assert body["workspace"].get("execution_plan_id") is None

    def test_reject_non_svg_file(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        response = _upload_svg(auth_client, workspace_id, "notes.txt", "plain text", "text/plain")
        assert response.status_code == 422

    def test_reject_archived_workspace(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        archive = auth_client.post(f"/api/v1/intake-v3/workspaces/{workspace_id}/archive")
        assert archive.status_code == 200

        response = _upload_svg(auth_client, workspace_id, "letters.svg", VALID_SVG)
        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "workspace_archived"

    def test_reject_svg_with_script(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        response = _upload_svg(auth_client, workspace_id, "bad.svg", SVG_WITH_SCRIPT)
        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "svg_scripts_forbidden"

    def test_svg_with_text_creates_warning(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        response = _upload_svg(auth_client, workspace_id, "text.svg", SVG_WITH_TEXT)
        assert response.status_code == 200
        warnings = response.json()["raw_svg_analysis"]["warnings"]
        assert WARNING_TEXT_NOT_CONVERTED_TO_PATHS in warnings

    def test_svg_missing_viewbox_creates_warning(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        response = _upload_svg(auth_client, workspace_id, "novb.svg", SVG_MISSING_VIEWBOX)
        assert response.status_code == 200
        warnings = response.json()["raw_svg_analysis"]["warnings"]
        assert WARNING_MISSING_VIEW_BOX in warnings

    def test_svg_paths_and_colors_detected(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        response = _upload_svg(auth_client, workspace_id, "colors.svg", VALID_SVG)
        assert response.status_code == 200
        analysis = response.json()["raw_svg_analysis"]
        assert analysis["detected_color_count"] >= 2
        assert analysis["path_count"] == 2

    def test_raw_analysis_does_not_set_confirmed_production_model(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        response = _upload_svg(auth_client, workspace_id, "letters.svg", VALID_SVG)
        assert response.status_code == 200
        payload = response.json()["workspace"]["payload"]
        confirmed = payload.get("confirmed_production_model")
        assert confirmed is None or confirmed.get("confirmation_status") != "confirmed"

    def test_no_side_effects(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        response = _upload_svg(auth_client, workspace_id, "letters.svg", VALID_SVG)
        assert response.status_code == 200
        workspace = response.json()["workspace"]
        payload = workspace["payload"]

        assert workspace.get("quote_id") is None
        assert workspace.get("order_id") is None
        assert workspace.get("execution_plan_id") is None
        assert payload.get("material_intent", {}).get("inventory_mutation_allowed") is False
        assert payload.get("production_handoff", {}).get("preview_only") is True
