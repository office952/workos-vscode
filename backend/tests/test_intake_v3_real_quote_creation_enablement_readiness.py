"""Intake V3 real quote creation enablement readiness — policy contracts, no quote creation."""

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
from services.intake_v3_commercial_quote_bridge_service import build_commercial_quote_bridge_preview
from services.intake_v3_owner_decision_record_policy_service import (
    build_owner_decision_record_policy,
)
from services.intake_v3_quote_creation_anti_duplicate_policy_service import (
    build_quote_creation_anti_duplicate_policy,
)
from services.intake_v3_quote_creation_dry_run_service import build_intake_v3_quote_creation_dry_run
from services.intake_v3_quote_creation_enablement_policy_service import (
    evaluate_quote_creation_enablement_policy,
)
from services.intake_v3_quote_creation_final_blocker_service import evaluate_quote_creation_final_blockers
from services.intake_v3_quote_creation_guard_policy_service import evaluate_quote_creation_guard_policy
from services.intake_v3_quote_creation_recovery_policy_service import (
    build_quote_creation_recovery_policy,
)
from services.intake_v3_quote_snapshot_policy_service import build_quote_snapshot_policy
from services.intake_v3_real_quote_creation_enablement_readiness_service import (
    evaluate_real_quote_creation_enablement_readiness,
)
from services.intake_v3_workspace_preview_service import build_intake_v3_workspace_preview

MINIMAL_WORKSPACE_PAYLOAD = {
    "client_request": {
        "client_name": "Readiness test",
        "request_code": "RDY-TEST-001",
        "job_title": "Readiness test",
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
    return ConfirmedProductionModel(
        confirmed_by_user_id="op-1",
        confirmed_at=datetime.now(timezone.utc),
        letter_count=18,
        cut_contour_count=18,
        inner_hole_count=0,
        letter_model=LetterModel(letters=letters, count_confirmed=True),
        cut_contour_model=CutContourModel(
            contours=contours,
            outer_contour_count=18,
            inner_hole_count=0,
            cut_contour_count=18,
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


def _full_chain(workspace: IntakeV3Workspace, *, archived: bool = False):
    preview = build_intake_v3_workspace_preview(workspace).preview
    dry_run = build_intake_v3_quote_creation_dry_run(
        workspace,
        preview,
        workspace_id="ws-readiness-test",
        workspace_code="IV3-RDY01",
        workspace_archived=archived,
    )
    guard = evaluate_quote_creation_guard_policy(
        workspace,
        preview,
        dry_run,
        workspace_archived=archived,
    )
    bridge = build_commercial_quote_bridge_preview(
        workspace,
        preview,
        workspace_id="ws-readiness-test",
        workspace_code="IV3-RDY01",
        workspace_archived=archived,
    )
    final_check = evaluate_quote_creation_final_blockers(
        workspace,
        preview,
        dry_run,
        guard,
        bridge,
        workspace_archived=archived,
    )
    enablement = evaluate_quote_creation_enablement_policy(
        workspace,
        preview,
        dry_run=dry_run,
        guard_policy=guard,
        bridge=bridge,
        final_blocker_check=final_check,
        workspace_archived=archived,
    )
    bundle = evaluate_real_quote_creation_enablement_readiness(
        workspace,
        preview,
        bridge,
        enablement,
        final_check,
        workspace_archived=archived,
    )
    return preview, dry_run, guard, bridge, enablement, bundle


class TestOwnerDecisionRecordPolicy:
    def test_owner_decision_required_but_absent(self):
        workspace = _ready_workspace()
        preview, _, _, bridge, enablement, _ = _full_chain(workspace)
        policy = build_owner_decision_record_policy(workspace, preview, enablement, bridge)
        assert policy.owner_decision_record_required is True
        assert policy.owner_decision_record_present is False
        assert policy.owner_decision_status == "required_not_present"
        assert policy.can_enable_real_quote_creation is False


class TestQuoteSnapshotPolicy:
    def test_snapshot_policy_defined_not_executed(self):
        workspace = _ready_workspace()
        preview, _, _, bridge, _, _ = _full_chain(workspace)
        policy = build_quote_snapshot_policy(workspace, preview, bridge)
        assert policy.snapshot_policy_defined is True
        assert policy.snapshot_persistence_executed is False
        section_codes = {section.section_code for section in policy.required_sections}
        assert "confirmed_production_model_snapshot" in section_codes
        assert "finish_assignment_snapshot" in section_codes
        assert "commercial_quote_bridge_snapshot" in section_codes
        assert "owner_decision_record_snapshot" in section_codes

    def test_snapshot_integrity_rules_include_raw_vs_confirmed_boundary(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        rules = {rule.code for rule in build_quote_snapshot_policy(workspace, preview).integrity_rules}
        assert "RAW_NOT_PRODUCTION_TRUTH" in rules
        assert "CONFIRMED_MODEL_PRODUCTION_TRUTH" in rules
        assert "HOLES_NOT_LETTERS" in rules


class TestAntiDuplicatePolicy:
    def test_anti_duplicate_policy_defined(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        policy = build_quote_creation_anti_duplicate_policy(workspace, preview)
        assert policy.anti_duplicate_policy_defined is True
        assert policy.quote_creation_idempotency_required is True
        assert policy.duplicate_check_executed is False
        key_codes = {key.key_code for key in policy.duplicate_key_strategy}
        assert "source_workspace_id" in key_codes
        assert policy.would_block_if_existing_quote_found is True


class TestRecoveryPolicy:
    def test_recovery_policy_defined(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        policy = build_quote_creation_recovery_policy(workspace, preview)
        assert policy.rollback_policy_defined is True
        assert policy.recovery_policy_defined is True
        assert policy.manual_review_required_on_partial_failure is True
        codes = {mode.code for mode in policy.failure_modes}
        assert "QUOTE_CREATED_SNAPSHOT_FAILED" in codes


class TestRealQuoteCreationEnablementReadiness:
    def test_final_enablement_readiness_remains_blocked(self):
        workspace = _ready_workspace()
        _, _, guard, bridge, _, bundle = _full_chain(workspace)
        readiness = bundle["readiness"]
        assert readiness.can_create_quote_now is False
        assert readiness.can_enable_real_quote_creation is False
        assert readiness.real_quote_creation_enablement_readiness_status == (
            "blocked_owner_decision_missing"
        )
        assert "OWNER_DECISION_RECORD_MISSING" in readiness.blockers
        assert guard.policy_status == "disabled_by_default"
        assert bridge.bridge_status == "disabled_by_policy"

    def test_safety_flags_not_indicating_calls(self):
        workspace = _ready_workspace()
        _, dry_run, _, bridge, _, bundle = _full_chain(workspace)
        assert dry_run.safety_flags.cost_engine_called is False
        assert dry_run.safety_flags.quote_creation_endpoint_called is False
        assert bridge.safety_flags.cost_engine_called is False
        assert bundle["readiness"].snapshot_persistence_executed is False


class TestRealQuoteCreationEnablementReadinessEndpoint:
    def test_get_readiness_read_only(self, auth_client):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "Readiness endpoint", "payload": MINIMAL_WORKSPACE_PAYLOAD},
        )
        assert create.status_code == 201
        workspace_id = create.json()["id"]
        before_updated = create.json()["updated_at"]

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/real-quote-creation-enablement-readiness"
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["readiness"]["can_create_quote_now"] is False
        assert payload["owner_decision_record_policy"]["owner_decision_record_present"] is False
        assert payload["snapshot_policy"]["snapshot_persistence_executed"] is False
        assert payload["anti_duplicate_policy"]["anti_duplicate_policy_defined"] is True
        assert payload["recovery_policy"]["rollback_policy_defined"] is True

        repeat = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/real-quote-creation-enablement-readiness"
        )
        assert repeat.status_code == 200
        assert (
            repeat.json()["readiness"]["real_quote_creation_enablement_readiness_status"]
            == payload["readiness"]["real_quote_creation_enablement_readiness_status"]
        )

        after = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert after.json()["updated_at"] == before_updated

    def test_preview_sets_readiness_availability_flag(self):
        build_result = build_intake_v3_workspace_preview(_ready_workspace())
        assert build_result.preview.real_quote_creation_enablement_readiness_available is True
        assert (
            build_result.preview.real_quote_creation_enablement_readiness_status
            == "blocked_owner_decision_missing"
        )
        assert build_result.preview.owner_decision_record_status == "required_not_present"
        assert build_result.preview.snapshot_policy_status == "defined_not_executed"
