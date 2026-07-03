"""Intake V3 production model review — operator confirmation from raw SVG analysis."""

from __future__ import annotations

from data_models.intake_v3_contracts import BLOCKER_UNCONFIRMED_LETTER_MODEL
from services.intake_v3_svg_analysis_service import WARNING_MISSING_VIEW_BOX

VALID_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100mm" height="50mm">
  <g id="letters">
    <path id="letter-a" d="M10 40 L20 10 L30 40 Z" fill="#ff0000" stroke="#000000"/>
    <path id="letter-b" d="M40 40 L40 10 L55 10 Q60 10 60 20 Q60 30 55 30 L40 30" fill="#00ff00"/>
  </g>
</svg>"""

MINIMAL_WORKSPACE_PAYLOAD = {
    "client_request": {
        "client_name": "Production model test",
        "request_code": "PM-TEST-001",
        "job_title": "Model review test",
        "width_mm": 1000,
        "height_mm": 500,
    },
    "product_selection": {"template_code": "TPL-VOLUMETRIC-LETTERS", "pilot_scope": True},
    "material_intent": {"inventory_mutation_allowed": False, "estimate_status": "not_started"},
    "production_handoff": {"preview_only": True},
    "employee_preview_seed": {"non_executable": True, "preview_tasks": []},
}

HUB_CONFIRM_PAYLOAD = {
    "letter_count": 18,
    "cut_contour_count": 27,
    "inner_hole_count": 9,
    "ignored_object_ids": [],
    "operator_notes": "HUB reference — holes are not separate letters.",
    "confirmed": True,
}


def _create_workspace(auth_client, payload: dict | None = None) -> str:
    response = auth_client.post(
        "/api/v1/intake-v3/workspaces",
        json={"title": "Production model review test", "payload": payload or MINIMAL_WORKSPACE_PAYLOAD},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _upload_svg(auth_client, workspace_id: str) -> dict:
    response = auth_client.post(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/svg",
        files={"file": ("letters.svg", VALID_SVG, "image/svg+xml")},
    )
    assert response.status_code == 200
    return response.json()


def _blocker_codes(preview_body: dict) -> set[str]:
    report = preview_body.get("preview", {}).get("readiness_report")
    if not report:
        return set()
    return {item["code"] for item in report.get("blockers", [])}


class TestIntakeV3ProductionModelReview:
    def test_review_candidate_from_raw_svg_analysis(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id)

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/review-candidate",
        )
        assert response.status_code == 200
        body = response.json()
        candidate = body["review_candidate"]
        assert candidate["confirmed"] is False
        assert candidate["suggested_cut_contour_count"] >= 1
        assert candidate["raw_path_count"] == 2
        assert candidate["source"] == "raw_svg_analysis"

    def test_cannot_get_candidate_without_raw_analysis(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/review-candidate",
        )
        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "missing_raw_svg_analysis"

    def test_confirm_hub_18_27_9_works(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id)

        response = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/confirm",
            json=HUB_CONFIRM_PAYLOAD,
        )
        assert response.status_code == 200
        body = response.json()
        confirmed = body["confirmed_production_model"]
        assert confirmed["letter_count"] == 18
        assert confirmed["cut_contour_count"] == 27
        assert confirmed["inner_hole_count"] == 9
        assert confirmed["confirmation_status"] == "confirmed"
        payload = body["workspace"]["payload"]
        assert payload["raw_svg_analysis"]["path_count"] == 2
        assert payload["production_model_status"] == "confirmed"

    def test_confirmed_model_removes_unconfirmed_blocker(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        upload_body = _upload_svg(auth_client, workspace_id)
        before_codes = _blocker_codes(upload_body["preview"])
        assert BLOCKER_UNCONFIRMED_LETTER_MODEL in before_codes

        confirm = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/confirm",
            json=HUB_CONFIRM_PAYLOAD,
        )
        assert confirm.status_code == 200
        after_codes = _blocker_codes(confirm.json()["preview"])
        assert BLOCKER_UNCONFIRMED_LETTER_MODEL not in after_codes

    def test_invalid_counts_rejected(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id)

        for payload in (
            {"letter_count": 0, "cut_contour_count": 1, "inner_hole_count": 0, "confirmed": True},
            {"letter_count": 5, "cut_contour_count": 3, "inner_hole_count": 0, "confirmed": True},
            {"letter_count": 5, "cut_contour_count": 5, "inner_hole_count": -1, "confirmed": True},
        ):
            response = auth_client.post(
                f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/confirm",
                json=payload,
            )
            assert response.status_code == 422

        unchanged = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert unchanged.json()["payload"].get("confirmed_production_model") is None

    def test_confirmed_false_rejected(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id)

        response = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/confirm",
            json={
                "letter_count": 18,
                "cut_contour_count": 27,
                "inner_hole_count": 9,
                "confirmed": False,
            },
        )
        assert response.status_code == 422

    def test_archived_workspace_rejected(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id)
        archive = auth_client.post(f"/api/v1/intake-v3/workspaces/{workspace_id}/archive")
        assert archive.status_code == 200

        response = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/confirm",
            json=HUB_CONFIRM_PAYLOAD,
        )
        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "workspace_archived"

    def test_raw_analysis_remains_separate(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id)
        confirm = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/confirm",
            json=HUB_CONFIRM_PAYLOAD,
        )
        assert confirm.status_code == 200
        payload = confirm.json()["workspace"]["payload"]
        assert payload.get("raw_svg_analysis") is not None
        assert payload.get("confirmed_production_model") is not None
        assert payload["raw_svg_analysis"]["path_count"] == 2
        assert payload["confirmed_production_model"]["letter_count"] == 18

    def test_no_side_effects(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id)
        confirm = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/confirm",
            json=HUB_CONFIRM_PAYLOAD,
        )
        assert confirm.status_code == 200
        workspace = confirm.json()["workspace"]
        payload = workspace["payload"]
        assert workspace.get("quote_id") is None
        assert workspace.get("order_id") is None
        assert workspace.get("execution_plan_id") is None
        assert payload.get("material_intent", {}).get("inventory_mutation_allowed") is False
        assert payload.get("production_handoff", {}).get("preview_only") is True
