"""Intake V3 workspace draft persistence tests."""

from __future__ import annotations

from data_models.intake_v3_contracts import BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH
from schemas.intake_v3 import PILOT_TEMPLATE_CODE
from services.intake_v3_preview_fixtures import (
    INTAKE_V3_PREVIEW_SCENARIO_HUB_MISSING_FACE_ROLL_WIDTH,
    INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL,
)
from services.intake_v3_workspace_service import sanitize_intake_v3_workspace_payload


def _wrapped_payload() -> dict:
    from services.intake_v3_preview_fixtures import build_hub_wrapped_face_vinyl_workspace

    return build_hub_wrapped_face_vinyl_workspace().model_dump(mode="json")


class TestSanitizeWorkspacePayload:
    def test_unsafe_boundary_flags_are_reset(self):
        payload = _wrapped_payload()
        payload["material_intent"]["inventory_mutation_allowed"] = True
        payload["production_handoff"]["preview_only"] = False
        payload["employee_preview_seed"]["non_executable"] = False
        workspace = sanitize_intake_v3_workspace_payload(payload)
        assert workspace.material_intent.inventory_mutation_allowed is False
        assert workspace.production_handoff.preview_only is True
        assert workspace.employee_preview_seed.non_executable is True


class TestWorkspacePersistenceEndpoints:
    def test_create_workspace_draft(self, auth_client):
        response = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={
                "title": "HUB draft test",
                "template_code": PILOT_TEMPLATE_CODE,
                "payload": _wrapped_payload(),
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["id"]
        assert body["status"] in {"draft", "collecting_data", "ready_for_quote_preview", "blocked"}
        assert body["template_code"] == PILOT_TEMPLATE_CODE
        assert body["payload"]
        assert body.get("created_quote_id") is None

    def test_list_workspaces_includes_created(self, auth_client):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "List me", "payload": _wrapped_payload()},
        )
        assert create.status_code == 201
        workspace_id = create.json()["id"]

        listed = auth_client.get("/api/v1/intake-v3/workspaces")
        assert listed.status_code == 200
        items = listed.json()["items"]
        assert any(item["id"] == workspace_id for item in items)

    def test_get_workspace_roundtrip(self, auth_client):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "Roundtrip", "payload": _wrapped_payload()},
        )
        workspace_id = create.json()["id"]
        fetched = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert fetched.status_code == 200
        body = fetched.json()
        assert body["title"] == "Roundtrip"
        assert body["payload"]["client_request"]["client_name"] == "HUB MEDIA PRODUCTION"
        assert body.get("created_quote_id") is None
        assert body.get("order_id") is None
        assert body.get("execution_plan_id") is None

    def test_update_workspace_title_and_payload(self, auth_client):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "Before", "payload": _wrapped_payload()},
        )
        workspace_id = create.json()["id"]
        updated = auth_client.patch(
            f"/api/v1/intake-v3/workspaces/{workspace_id}",
            json={"title": "After"},
        )
        assert updated.status_code == 200
        assert updated.json()["title"] == "After"

        unsafe = auth_client.patch(
            f"/api/v1/intake-v3/workspaces/{workspace_id}",
            json={
                "payload": {
                    **_wrapped_payload(),
                    "material_intent": {"inventory_mutation_allowed": True, "estimate_status": "complete"},
                }
            },
        )
        assert unsafe.status_code == 200
        assert unsafe.json()["payload"]["material_intent"]["inventory_mutation_allowed"] is False

    def test_archive_workspace_hides_from_default_list(self, auth_client):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "Archive me", "payload": _wrapped_payload()},
        )
        workspace_id = create.json()["id"]
        archived = auth_client.post(f"/api/v1/intake-v3/workspaces/{workspace_id}/archive")
        assert archived.status_code == 200
        assert archived.json()["status"] == "archived"
        assert archived.json()["archived_at"] is not None

        listed = auth_client.get("/api/v1/intake-v3/workspaces")
        assert all(item["id"] != workspace_id for item in listed.json()["items"])

    def test_seed_from_scenario_creates_hub_workspace(self, auth_client):
        response = auth_client.post(
            "/api/v1/intake-v3/workspaces/seed-from-scenario",
            json={"scenario": INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["metadata"]["source_scenario"] == INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL
        model = body["payload"]["confirmed_production_model"]
        assert model["letter_count"] == 18
        assert model["cut_contour_count"] == 27
        assert model["inner_hole_count"] == 9

    def test_workspace_preview_from_saved_payload(self, auth_client):
        seeded = auth_client.post(
            "/api/v1/intake-v3/workspaces/seed-from-scenario",
            json={"scenario": INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL},
        )
        workspace_id = seeded.json()["id"]
        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview")
        assert preview.status_code == 200
        body = preview.json()
        assert body["workspace_id"] == workspace_id
        assert body["preview"]["vector_summary"]["confirmed_letter_count"] == 18
        assert body["preview"]["boundary_flags"]["preview_only"] is True
        assert body["preview"]["boundary_flags"]["quote_creation_allowed"] is False
        assert body["preview"]["created_quote_id"] is None

    def test_missing_roll_width_workspace_preview_blocker(self, auth_client):
        seeded = auth_client.post(
            "/api/v1/intake-v3/workspaces/seed-from-scenario",
            json={"scenario": INTAKE_V3_PREVIEW_SCENARIO_HUB_MISSING_FACE_ROLL_WIDTH},
        )
        workspace_id = seeded.json()["id"]
        preview = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview")
        assert preview.status_code == 200
        assert BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH in preview.json()["preview"]["preview_blockers"]

    def test_unknown_workspace_returns_404(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/workspaces/does-not-exist/preview")
        assert response.status_code == 404

    def test_no_side_effect_ids_in_responses(self, auth_client):
        seeded = auth_client.post(
            "/api/v1/intake-v3/workspaces/seed-from-scenario",
            json={"scenario": INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL},
        )
        preview = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{seeded.json()['id']}/preview"
        )
        flags = preview.json()["preview"]["boundary_flags"]
        assert flags["order_creation_allowed"] is False
        assert flags["execution_plan_creation_allowed"] is False
        assert flags["inventory_mutation_allowed"] is False
        assert flags["employee_mobile_action_allowed"] is False
