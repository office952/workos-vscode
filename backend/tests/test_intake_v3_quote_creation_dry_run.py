"""Intake V3 quote creation dry-run contract — no quote/order/CostEngine side effects."""

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
from services.intake_v3_quote_creation_dry_run_service import (
    build_intake_v3_quote_creation_dry_run,
)
from services.intake_v3_workspace_preview_service import build_intake_v3_workspace_preview

MINIMAL_WORKSPACE_PAYLOAD = {
    "client_request": {
        "client_name": "Dry-run test",
        "request_code": "DRY-TEST-001",
        "job_title": "Dry-run test",
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


class TestQuoteCreationDryRun:
    def test_incomplete_workspace_dry_run_is_blocked(self):
        result = build_intake_v3_quote_creation_dry_run(MINIMAL_WORKSPACE_PAYLOAD)
        assert result.dry_run_only is True
        assert result.can_create_quote_now is False
        assert result.blockers
        assert result.dry_run_status == "blocked"
        assert result.safety_flags.quote_created is False

    def test_complete_workspace_ready_for_future_step_but_disabled(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        result = build_intake_v3_quote_creation_dry_run(
            workspace,
            preview,
            workspace_id="ws-hub",
            workspace_code="IV3-HUB",
        )
        assert result.dry_run_only is True
        assert result.can_create_quote_now is False
        assert result.dry_run_status == "ready_for_future_quote_step"
        assert result.quote_creation_disabled_reason
        assert "disabled by policy" in result.quote_creation_disabled_reason.lower()
        assert result.guard_policy.disabled_by_policy is True
        assert result.payload_preview.confirmed_letter_count == 18
        assert result.snapshot_preview.confirmed_production_model_snapshot

    def test_dry_run_does_not_call_quote_creation(self):
        result = build_intake_v3_quote_creation_dry_run(_ready_workspace())
        flags = result.safety_flags
        assert flags.quote_creation_endpoint_called is False
        assert flags.quote_created is False
        assert result.snapshot_preview.created_quote_id is None

    def test_payload_preview_includes_confirmed_counts(self):
        preview = build_intake_v3_workspace_preview(_ready_workspace()).preview
        result = build_intake_v3_quote_creation_dry_run(_ready_workspace(), preview)
        assert result.payload_preview.confirmed_letter_count == 18
        assert result.payload_preview.confirmed_cut_contour_count == 27
        assert result.payload_preview.confirmed_inner_hole_count == 9

    def test_payload_preview_includes_finish_variation_summary(self):
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
        result = build_intake_v3_quote_creation_dry_run(workspace, preview)
        assert result.payload_preview.finish_variation_count >= 1
        assert result.payload_preview.requires_grouped_finish_review is True
        assert any("grouped" in note.lower() for note in result.payload_preview.pricing_notes)

    def test_snapshot_preserves_raw_vs_confirmed_boundary(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        result = build_intake_v3_quote_creation_dry_run(workspace, preview)
        snap = result.snapshot_preview
        assert snap.raw_svg_analysis_reference.get("is_production_truth") is False
        assert snap.confirmed_production_model_snapshot.get("confirmation_status") == "confirmed"
        assert "separate" in snap.raw_vs_confirmed_boundary_note.lower()

    def test_archived_workspace_is_blocked(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        result = build_intake_v3_quote_creation_dry_run(
            workspace,
            preview,
            workspace_archived=True,
        )
        assert result.dry_run_status == "blocked"
        assert "WORKSPACE_ARCHIVED" in result.blockers

    def test_safety_flags_always_false(self):
        result = build_intake_v3_quote_creation_dry_run(_ready_workspace())
        flags = result.safety_flags
        assert flags.order_created is False
        assert flags.execution_plan_created is False
        assert flags.inventory_mutated is False
        assert flags.cost_engine_called is False
        assert flags.pricing_formula_modified is False

    def test_workspace_preview_sets_dry_run_available_flag(self):
        build_result = build_intake_v3_workspace_preview(_ready_workspace())
        assert build_result.preview.quote_creation_dry_run_available is True


class TestQuoteCreationDryRunEndpoint:
    def test_get_dry_run_read_only(self, auth_client):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "Dry-run endpoint", "payload": MINIMAL_WORKSPACE_PAYLOAD},
        )
        assert create.status_code == 201
        workspace_id = create.json()["id"]
        before_updated = create.json()["updated_at"]

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/quote-creation-dry-run"
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["dry_run"]["dry_run_only"] is True
        assert payload["dry_run"]["can_create_quote_now"] is False
        assert payload["dry_run"]["safety_flags"]["quote_created"] is False
        assert payload["dry_run"]["guard_policy"]["disabled_by_policy"] is True

        repeat = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/quote-creation-dry-run"
        )
        assert repeat.status_code == 200
        assert repeat.json()["dry_run"]["dry_run_id"] == payload["dry_run"]["dry_run_id"]

        get_ws = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert get_ws.status_code == 200
        assert get_ws.json()["updated_at"] == before_updated
