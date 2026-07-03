"""Intake V3 controlled field editor — allowlist patches, preview regeneration."""

from __future__ import annotations

from data_models.intake_v3_contracts import (
    BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
    BLOCKER_MISSING_RETURN_DEPTH,
    BLOCKER_MISSING_RETURN_PAINT_COLOR,
)
from schemas.intake_v3 import ReturnFinishSpec
from services.intake_v3_preview_fixtures import (
    INTAKE_V3_PREVIEW_SCENARIO_HUB_MISSING_FACE_ROLL_WIDTH,
    INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL,
    build_hub_wrapped_face_vinyl_workspace,
)
from services.intake_v3_workspace_field_editor_service import get_allowed_intake_v3_field_paths


def _seed_from_scenario(auth_client, scenario: str) -> str:
    response = auth_client.post(
        "/api/v1/intake-v3/workspaces/seed-from-scenario",
        json={"scenario": scenario},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _seed_from_payload(auth_client, payload: dict, title: str = "Field editor test") -> str:
    response = auth_client.post(
        "/api/v1/intake-v3/workspaces",
        json={"title": title, "payload": payload},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _patch_fields(auth_client, workspace_id: str, patches: list[dict], *, regenerate_preview: bool = True):
    return auth_client.patch(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/fields",
        json={"patches": patches, "regenerate_preview": regenerate_preview},
    )


def _blocker_codes(preview_body: dict) -> set[str]:
    report = preview_body["preview"]["readiness_report"]
    if not report:
        return set()
    return {item["code"] for item in report.get("blockers", [])}


def _active_seed_codes(preview_body: dict) -> list[str]:
    seeds = preview_body["preview"]["production_handoff_preview"]["task_seeds"]
    return [seed["seed_code"] for seed in seeds if seed.get("active")]


class TestIntakeV3WorkspaceFieldEditor:
    def test_patch_dimensions_updates_preview(self, auth_client):
        workspace_id = _seed_from_scenario(auth_client, INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL)
        before = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()
        assert before["payload"]["client_request"]["width_mm"] == 9250

        response = _patch_fields(
            auth_client,
            workspace_id,
            [
                {"field_path": "dimensions.width_mm", "value": 8000},
                {"field_path": "dimensions.height_mm", "value": 600},
            ],
        )
        assert response.status_code == 200
        body = response.json()
        assert body["workspace"]["payload"]["client_request"]["width_mm"] == 8000
        assert body["workspace"]["payload"]["client_request"]["height_mm"] == 600
        assert body["preview"]["preview"]["finish_summary"]["face_vinyl_roll_width_mm"] == 1260
        assert body["workspace"].get("created_quote_id") is None
        assert body["workspace"].get("order_id") is None
        assert body["workspace"].get("execution_plan_id") is None

    def test_patch_face_roll_width_removes_blocker(self, auth_client):
        workspace_id = _seed_from_scenario(
            auth_client,
            INTAKE_V3_PREVIEW_SCENARIO_HUB_MISSING_FACE_ROLL_WIDTH,
        )
        preview_before = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        assert BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH in _blocker_codes(preview_before)

        response = _patch_fields(
            auth_client,
            workspace_id,
            [{"field_path": "finish_assignment.face_finish.roll_width_mm", "value": 1260}],
        )
        assert response.status_code == 200
        body = response.json()
        assert BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH not in _blocker_codes(body["preview"])
        assert body["preview"]["preview"]["finish_summary"]["face_vinyl_roll_width_mm"] == 1260

    def test_patch_return_depth_removes_blocker(self, auth_client):
        payload = build_hub_wrapped_face_vinyl_workspace().model_dump(mode="json")
        payload["finish_assignment"]["return_finish"]["return_depth_mm"] = None
        workspace_id = _seed_from_payload(auth_client, payload, title="Missing return depth")

        preview_before = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview").json()
        assert BLOCKER_MISSING_RETURN_DEPTH in _blocker_codes(preview_before)

        response = _patch_fields(
            auth_client,
            workspace_id,
            [{"field_path": "finish_assignment.return_finish.depth_mm", "value": 60}],
        )
        assert response.status_code == 200
        body = response.json()
        assert BLOCKER_MISSING_RETURN_DEPTH not in _blocker_codes(body["preview"])
        assert body["preview"]["preview"]["finish_summary"]["return_depth_mm"] == 60

    def test_patch_return_finish_painted_task_order(self, auth_client):
        workspace_id = _seed_from_scenario(auth_client, INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL)
        response = _patch_fields(
            auth_client,
            workspace_id,
            [
                {"field_path": "finish_assignment.return_finish.finish_type", "value": "painted"},
                {"field_path": "finish_assignment.return_finish.color_code", "value": "9005"},
                {"field_path": "finish_assignment.return_finish.color_name", "value": "Jet black"},
                {"field_path": "finish_assignment.face_finish.enabled", "value": True},
            ],
        )
        assert response.status_code == 200
        active = _active_seed_codes(response.json()["preview"])
        assert "return_painting_after_assembly" in active
        assert "face_vinyl_application_final" in active
        assert "return_vinyl_application_workbench" not in active
        paint_idx = active.index("return_painting_after_assembly")
        face_idx = active.index("face_vinyl_application_final")
        assert paint_idx < face_idx

    def test_painted_missing_color_keeps_blocker(self, auth_client):
        workspace_id = _seed_from_scenario(auth_client, INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL)
        response = _patch_fields(
            auth_client,
            workspace_id,
            [
                {"field_path": "finish_assignment.return_finish.finish_type", "value": "painted"},
                {"field_path": "finish_assignment.return_finish.color_code", "value": ""},
                {"field_path": "finish_assignment.return_finish.color_name", "value": ""},
            ],
        )
        assert response.status_code == 200
        assert BLOCKER_MISSING_RETURN_PAINT_COLOR in _blocker_codes(response.json()["preview"])

    def test_forbidden_field_rejected(self, auth_client):
        workspace_id = _seed_from_scenario(auth_client, INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL)
        before = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()

        for forbidden in (
            "created_quote_id",
            "execution_plan_id",
            "inventory_mutation_allowed",
        ):
            response = _patch_fields(
                auth_client,
                workspace_id,
                [{"field_path": forbidden, "value": "unsafe"}],
            )
            assert response.status_code == 422

        after = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()
        assert after["payload"] == before["payload"]

    def test_invalid_dimension_rejected(self, auth_client):
        workspace_id = _seed_from_scenario(auth_client, INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL)
        before = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()

        response = _patch_fields(
            auth_client,
            workspace_id,
            [{"field_path": "dimensions.width_mm", "value": 0}],
        )
        assert response.status_code == 422

        after = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()
        assert after["payload"]["client_request"]["width_mm"] == before["payload"]["client_request"]["width_mm"]

    def test_unsupported_finish_type_rejected(self, auth_client):
        workspace_id = _seed_from_scenario(auth_client, INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL)
        response = _patch_fields(
            auth_client,
            workspace_id,
            [{"field_path": "finish_assignment.return_finish.finish_type", "value": "invalid_finish"}],
        )
        assert response.status_code == 422

    def test_archived_workspace_cannot_be_patched(self, auth_client):
        workspace_id = _seed_from_scenario(auth_client, INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL)
        archived = auth_client.post(f"/api/v1/intake-v3/workspaces/{workspace_id}/archive")
        assert archived.status_code == 200

        response = _patch_fields(
            auth_client,
            workspace_id,
            [{"field_path": "dimensions.width_mm", "value": 5000}],
        )
        assert response.status_code == 400

    def test_editable_fields_endpoint_returns_allowlist(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/workspaces/editable-fields")
        assert response.status_code == 200
        paths = {item["field_path"] for item in response.json()["fields"]}
        assert "dimensions.width_mm" in paths
        assert "finish_assignment.face_finish.roll_width_mm" in paths
        assert "created_quote_id" not in paths
        assert "execution_plan_id" not in paths
        allowed = set(get_allowed_intake_v3_field_paths())
        assert "dimensions.width_mm" in allowed
        assert "title" in allowed

    def test_no_side_effects_after_patch(self, auth_client):
        workspace_id = _seed_from_scenario(auth_client, INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL)
        response = _patch_fields(
            auth_client,
            workspace_id,
            [{"field_path": "title", "value": "Patched title"}],
        )
        assert response.status_code == 200
        workspace = response.json()["workspace"]
        assert workspace["title"] == "Patched title"
        assert workspace.get("created_quote_id") is None
        assert workspace.get("order_id") is None
        assert workspace.get("execution_plan_id") is None
        assert workspace["payload"]["material_intent"]["inventory_mutation_allowed"] is False
