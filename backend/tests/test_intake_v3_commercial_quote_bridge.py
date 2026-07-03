"""Intake V3 commercial quote bridge — mapping preview only, no quote/CostEngine side effects."""

from __future__ import annotations

from datetime import datetime, timezone

from schemas.intake_v3 import (
    ConfirmedProductionModel,
    CutContourItem,
    CutContourModel,
    FaceFinishSpec,
    FinishAssignment,
    IntakeV3Workspace,
    LetterItem,
    LetterModel,
    RawSvgAnalysis,
    ReturnFinishSpec,
    VectorAsset,
)
from services.intake_v3_commercial_quote_bridge_service import (
    build_commercial_quote_bridge_preview,
)
from services.intake_v3_workspace_preview_service import build_intake_v3_workspace_preview

MINIMAL_WORKSPACE_PAYLOAD = {
    "client_request": {
        "client_name": "Bridge test",
        "request_code": "BRG-TEST-001",
        "job_title": "Bridge test",
    },
    "product_selection": {"template_code": "TPL-VOLUMETRIC-LETTERS", "pilot_scope": True},
    "material_intent": {"inventory_mutation_allowed": False, "estimate_status": "not_started"},
    "production_handoff": {"preview_only": True},
    "employee_preview_seed": {"non_executable": True, "preview_tasks": []},
}


def _hub_confirmed_model() -> ConfirmedProductionModel:
    letters = [
        LetterItem(letter_id=f"L-{i:02d}", label=str(i), outer_contour_ids=[f"C-{i:02d}"])
        for i in range(1, 19)
    ]
    contours = [
        CutContourItem(contour_id=f"C-{i:02d}", role="outer", parent_letter_id=f"L-{i:02d}")
        for i in range(1, 19)
    ]
    contours.extend(
        CutContourItem(
            contour_id=f"C-HOLE-{i:02d}",
            role="inner_hole",
            parent_letter_id=f"L-{i:02d}",
        )
        for i in range(1, 10)
    )
    return ConfirmedProductionModel(
        confirmed_by_user_id="op-1",
        confirmed_at=datetime.now(timezone.utc),
        letter_count=18,
        cut_contour_count=27,
        inner_hole_count=9,
        letter_model=LetterModel(letters=letters, count_confirmed=True),
        cut_contour_model=CutContourModel(
            contours=contours,
            outer_contour_count=18,
            inner_hole_count=9,
            cut_contour_count=27,
        ),
        confirmation_status="confirmed",
    )


def _complete_finish() -> FinishAssignment:
    return FinishAssignment(
        assignment_mode="all",
        confirmed_by_operator=True,
        face_finish=FaceFinishSpec(
            finish_type="oracal_8500",
            material_code="Oracal 8500",
            color_code="527",
            color_name="Pastel blue",
            face_vinyl_roll_width_mm=1260,
            confirmed=True,
        ),
        return_finish=ReturnFinishSpec(
            finish_type="oracal_651",
            material_code="Oracal 651",
            color_code="055m",
            return_depth_mm=60,
            confirmed=True,
        ),
        backing_finish={"material": "Forex", "thickness_mm": 10, "confirmed": True},
    )


def _ready_workspace(**overrides) -> IntakeV3Workspace:
    payload = {
        "client_request": {
            "client_name": "Hub Media",
            "request_code": "INK-2026-0847",
            "job_title": "Litere volumetrice",
            "width_mm": 9250,
            "height_mm": 550,
        },
        "vector_asset": VectorAsset(file_name="hub.svg", upload_status="parsed"),
        "raw_svg_analysis": RawSvgAnalysis(
            file_name="hub.svg",
            closed_contour_count=18,
            path_count=18,
        ),
        "confirmed_production_model": _hub_confirmed_model().model_dump(mode="json"),
        "finish_assignment": _complete_finish().model_dump(mode="json"),
        "material_intent": {"estimate_status": "complete"},
        "support_context": {"shared_support": False, "illuminated": True},
    }
    payload.update(overrides)
    return IntakeV3Workspace.model_validate(payload)


class TestCommercialQuoteBridge:
    def test_bridge_disabled_by_policy(self):
        bridge = build_commercial_quote_bridge_preview(MINIMAL_WORKSPACE_PAYLOAD)
        assert bridge.bridge_status in {"disabled_by_policy", "blocked_by_missing_policy"}
        assert bridge.can_create_commercial_quote is False
        assert bridge.would_create_quote is False
        assert bridge.quote_creation_endpoint_called is False

    def test_candidate_payload_includes_workspace_template_dimensions(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        bridge = build_commercial_quote_bridge_preview(
            workspace,
            preview,
            workspace_id="ws-bridge",
            workspace_code="IV3-BRG",
        )
        candidate = bridge.candidate_payload
        assert candidate.workspace_id == "ws-bridge"
        assert candidate.template_code == "TPL-VOLUMETRIC-LETTERS"
        assert candidate.dimensions.get("width_mm") == 9250
        assert candidate.dimensions.get("height_mm") == 550

    def test_candidate_payload_includes_confirmed_counts(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        bridge = build_commercial_quote_bridge_preview(workspace, preview)
        candidate = bridge.candidate_payload
        assert candidate.confirmed_letter_count == 18
        assert candidate.confirmed_cut_contour_count == 27
        assert candidate.confirmed_inner_hole_count == 9

    def test_candidate_payload_includes_finish_variation_summary(self):
        workspace = _ready_workspace(
            letter_group_finish_assignments=[
                {
                    "assignment_id": "grp-hub",
                    "label": "HUB",
                    "target_letter_ids": ["L-01", "L-02"],
                    "enabled": True,
                    "face_finish": _complete_finish().face_finish.model_dump(mode="json"),
                    "return_finish": _complete_finish().return_finish.model_dump(mode="json"),
                    "backing_finish": {"material": "Forex", "thickness_mm": 10, "confirmed": True},
                }
            ],
            finish_assignment_status="group_overrides",
        )
        preview = build_intake_v3_workspace_preview(workspace).preview
        bridge = build_commercial_quote_bridge_preview(workspace, preview)
        candidate = bridge.candidate_payload
        assert candidate.finish_variation_summary_reference
        assert candidate.requires_grouped_finish_review is True
        assert candidate.material_notes or candidate.operation_notes or candidate.pricing_notes

    def test_mapping_status_includes_preview_only_pricing(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        bridge = build_commercial_quote_bridge_preview(workspace, preview)
        pricing_items = [
            item
            for item in bridge.mapping_status
            if item.source_field == "pricing_input_candidate"
        ]
        final_price_items = [
            item for item in bridge.mapping_status if item.source_field == "final_total_price"
        ]
        assert pricing_items and pricing_items[0].status == "preview_only"
        assert final_price_items and final_price_items[0].status == "missing"

    def test_missing_fields_not_invented(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        bridge = build_commercial_quote_bridge_preview(workspace, preview)
        codes = {item.field_code for item in bridge.missing_fields}
        assert "final_commercial_price" in codes
        assert "payment_terms" in codes
        assert "quote_validity_days" in codes
        assert "client_customer_id" in codes
        assert not any(item.field_code == "invented_price" for item in bridge.missing_fields)

    def test_snapshot_plan_exists(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        bridge = build_commercial_quote_bridge_preview(workspace, preview)
        plan = bridge.snapshot_plan
        assert plan.workspace_payload_snapshot is True
        assert plan.confirmed_production_model_snapshot is True
        assert plan.guard_policy_snapshot is True
        assert "db snapshot rows" in plan.persistence_note.lower()

    def test_safety_flags_false(self):
        bridge = build_commercial_quote_bridge_preview(_ready_workspace())
        flags = bridge.safety_flags
        assert flags.quote_created is False
        assert flags.commercial_quote_created is False
        assert flags.cost_engine_called is False
        assert flags.inventory_mutated is False

    def test_archived_workspace_blocked_safe(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        bridge = build_commercial_quote_bridge_preview(
            workspace,
            preview,
            workspace_archived=True,
        )
        assert bridge.can_create_commercial_quote is False
        assert bridge.would_create_quote is False
        assert bridge.safety_flags.quote_created is False


class TestCommercialQuoteBridgeEndpoint:
    def test_get_bridge_read_only(self, auth_client):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "Bridge endpoint", "payload": MINIMAL_WORKSPACE_PAYLOAD},
        )
        assert create.status_code == 201
        workspace_id = create.json()["id"]
        before_updated = create.json()["updated_at"]

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/commercial-quote-bridge"
        )
        assert response.status_code == 200
        payload = response.json()
        bridge = payload["bridge"]
        assert bridge["can_create_commercial_quote"] is False
        assert bridge["would_create_quote"] is False
        assert bridge["safety_flags"]["quote_created"] is False

        repeat = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/commercial-quote-bridge"
        )
        assert repeat.status_code == 200
        assert repeat.json()["bridge"]["policy_code"] == bridge["policy_code"]

        after = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert after.json()["updated_at"] == before_updated

    def test_preview_sets_bridge_availability_flag(self):
        build_result = build_intake_v3_workspace_preview(_ready_workspace())
        assert build_result.preview.commercial_quote_bridge_available is True
        assert build_result.preview.commercial_quote_bridge_status == "disabled_by_policy"
