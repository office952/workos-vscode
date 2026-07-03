"""Intake V3 read-only preview endpoint tests."""

from __future__ import annotations

from data_models.intake_v3_contracts import BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH
from schemas.intake_v3 import PILOT_TEMPLATE_CODE
from services.intake_v3_preview_fixtures import (
    INTAKE_V3_PREVIEW_SCENARIO_HUB_MISSING_FACE_ROLL_WIDTH,
    INTAKE_V3_PREVIEW_SCENARIO_HUB_PAINTED_FACE_VINYL,
    INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL,
    list_intake_v3_preview_scenarios,
)


def _active_seed(seeds: list[dict], code: str) -> dict:
    for seed in seeds:
        if seed["seed_code"] == code:
            return seed
    raise AssertionError(f"seed {code} not found")


class TestIntakeV3PreviewFixtures:
    def test_list_known_scenarios(self):
        scenarios = list_intake_v3_preview_scenarios()
        assert INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL in scenarios
        assert INTAKE_V3_PREVIEW_SCENARIO_HUB_PAINTED_FACE_VINYL in scenarios
        assert INTAKE_V3_PREVIEW_SCENARIO_HUB_MISSING_FACE_ROLL_WIDTH in scenarios


class TestIntakeV3PreviewEndpoint:
    def test_wrapped_scenario_returns_preview(self, auth_client):
        response = auth_client.get(
            "/api/v1/intake-v3/preview",
            params={"scenario": INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL},
        )
        assert response.status_code == 200
        payload = response.json()
        preview = payload["preview"]
        assert preview["boundary_flags"]["preview_only"] is True
        assert preview["template_code"] == PILOT_TEMPLATE_CODE
        assert preview["vector_summary"]["confirmed_letter_count"] == 18
        assert preview["vector_summary"]["confirmed_cut_contour_count"] == 27
        assert preview["vector_summary"]["confirmed_inner_hole_count"] == 9
        assert preview["created_quote_id"] is None
        assert preview["created_order_id"] is None
        assert preview["execution_plan_id"] is None
        assert preview["boundary_flags"]["quote_creation_allowed"] is False
        assert preview["boundary_flags"]["order_creation_allowed"] is False
        assert preview["boundary_flags"]["execution_plan_creation_allowed"] is False
        assert preview["boundary_flags"]["inventory_mutation_allowed"] is False

    def test_painted_scenario_painting_order_semantics(self, auth_client):
        response = auth_client.get(
            "/api/v1/intake-v3/preview",
            params={"scenario": INTAKE_V3_PREVIEW_SCENARIO_HUB_PAINTED_FACE_VINYL},
        )
        assert response.status_code == 200
        seeds = response.json()["preview"]["production_handoff_preview"]["task_seeds"]
        paint = _active_seed(seeds, "return_painting_after_assembly")
        face = _active_seed(seeds, "face_vinyl_application_final")
        assert paint["active"] is True
        assert "letter_assembly_no_shared_support" in paint["depends_on"]
        assert face["active"] is True
        assert "return_painting_after_assembly" in face["depends_on"]
        assert face["non_executable"] is True

    def test_missing_roll_width_scenario_returns_blocker(self, auth_client):
        response = auth_client.get(
            "/api/v1/intake-v3/preview",
            params={"scenario": INTAKE_V3_PREVIEW_SCENARIO_HUB_MISSING_FACE_ROLL_WIDTH},
        )
        assert response.status_code == 200
        preview = response.json()["preview"]
        assert BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH in preview["preview_blockers"]
        assert preview["is_ready_for_quote"] is False
        assert preview["pricing_input_candidate"] is None or preview["is_ready_for_quote"] is False

    def test_unknown_scenario_returns_400(self, auth_client):
        response = auth_client.get(
            "/api/v1/intake-v3/preview",
            params={"scenario": "not_a_real_scenario"},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error"] == "unknown_preview_scenario"
        assert INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL in detail["supported_scenarios"]

    def test_scenarios_list_endpoint(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/scenarios")
        assert response.status_code == 200
        scenarios = response.json()["scenarios"]
        assert len(scenarios) == 3

    def test_endpoint_does_not_create_entities(self, auth_client):
        response = auth_client.get(
            "/api/v1/intake-v3/preview",
            params={"scenario": INTAKE_V3_PREVIEW_SCENARIO_HUB_WRAPPED_FACE_VINYL},
        )
        assert response.status_code == 200
        preview = response.json()["preview"]
        assert preview.get("created_quote_id") is None
        assert preview.get("created_order_id") is None
        assert preview.get("execution_plan_id") is None
        flags = preview["boundary_flags"]
        assert flags["quote_creation_allowed"] is False
        assert flags["order_creation_allowed"] is False
        assert flags["execution_plan_creation_allowed"] is False
        assert flags["inventory_mutation_allowed"] is False
        assert flags["employee_mobile_action_allowed"] is False
