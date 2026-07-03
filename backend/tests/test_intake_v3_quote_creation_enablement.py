"""Intake V3 quote creation enablement policy + final blocker check — no real quote creation."""

from __future__ import annotations

from datetime import datetime, timezone

from schemas.intake_v3 import (
    ConfirmedProductionModel,
    CutContourItem,
    CutContourModel,
    FaceFinishSpec,
    FinishAssignment,
    IntakeV3QuoteCreationDryRunSafetyFlags,
    IntakeV3Workspace,
    LetterItem,
    LetterModel,
    RawSvgAnalysis,
    ReturnFinishSpec,
    VectorAsset,
)
from services.intake_v3_commercial_quote_bridge_service import build_commercial_quote_bridge_preview
from services.intake_v3_quote_creation_dry_run_service import build_intake_v3_quote_creation_dry_run
from services.intake_v3_quote_creation_enablement_policy_service import (
    POLICY_CODE,
    can_enable_real_quote_creation,
    evaluate_quote_creation_enablement_policy,
)
from services.intake_v3_quote_creation_final_blocker_service import (
    evaluate_quote_creation_final_blockers,
)
from services.intake_v3_quote_creation_guard_policy_service import evaluate_quote_creation_guard_policy
from services.intake_v3_workspace_preview_service import build_intake_v3_workspace_preview

MINIMAL_WORKSPACE_PAYLOAD = {
    "client_request": {
        "client_name": "Enablement test",
        "request_code": "ENB-TEST-001",
        "job_title": "Enablement test",
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


def _build_chain(workspace: IntakeV3Workspace, *, archived: bool = False):
    build_result = build_intake_v3_workspace_preview(workspace)
    preview = build_result.preview
    dry_run = build_intake_v3_quote_creation_dry_run(
        workspace,
        preview,
        workspace_id="ws-enablement-test",
        workspace_code="IV3-ENB01",
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
        workspace_id="ws-enablement-test",
        workspace_code="IV3-ENB01",
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
    return preview, dry_run, guard, bridge, final_check, enablement


class TestQuoteCreationEnablementPolicy:
    def test_enablement_requires_owner_approval(self):
        assert can_enable_real_quote_creation() is False
        workspace = IntakeV3Workspace.model_validate(MINIMAL_WORKSPACE_PAYLOAD)
        _, _, _, _, _, enablement = _build_chain(workspace)
        assert enablement.enablement_status == "owner_approval_required"
        assert enablement.owner_approval_required is True
        assert enablement.owner_approval_present is False
        assert enablement.can_enable_real_quote_creation is False
        assert enablement.can_create_quote_now is False
        assert enablement.policy_code == POLICY_CODE

    def test_complete_workspace_still_blocked_for_real_creation(self):
        workspace = _ready_workspace()
        preview, _, _, _, final_check, enablement = _build_chain(workspace)
        assert preview.quote_readiness is not None
        assert final_check.preview_status == "pass"
        assert final_check.real_creation_status == "blocked"
        assert enablement.real_creation_status == "blocked"
        assert "OWNER_APPROVAL_MISSING" in final_check.blockers
        assert "REAL_QUOTE_CREATION_DISABLED_BY_POLICY" in final_check.blockers

    def test_incomplete_workspace_reports_data_blockers(self):
        workspace = IntakeV3Workspace.model_validate(MINIMAL_WORKSPACE_PAYLOAD)
        _, _, _, _, final_check, _ = _build_chain(workspace)
        assert final_check.preview_status == "blocked"
        codes = {item.code for item in final_check.items if item.affects_preview}
        assert "DIMENSIONS_MISSING" in codes or "SVG_RAW_ANALYSIS_MISSING" in codes
        assert "PRODUCTION_MODEL_UNCONFIRMED" in codes

    def test_final_price_missing_is_real_creation_blocker_only(self):
        workspace = _ready_workspace()
        _, _, _, _, final_check, _ = _build_chain(workspace)
        price_items = [i for i in final_check.items if i.code == "FINAL_PRICE_NOT_CALCULATED"]
        assert len(price_items) == 1
        assert price_items[0].affects_preview is False
        assert price_items[0].affects_real_creation is True
        assert "FINAL_PRICE_NOT_CALCULATED" in final_check.blockers
        assert final_check.preview_status == "pass"

    def test_cost_engine_not_called_is_expected(self):
        workspace = _ready_workspace()
        _, dry_run, _, _, final_check, _ = _build_chain(workspace)
        assert dry_run.safety_flags.cost_engine_called is False
        assert final_check.cost_engine_called is False
        ce_items = [i for i in final_check.items if i.code == "COST_ENGINE_NOT_CALLED"]
        assert len(ce_items) == 1
        assert ce_items[0].severity == "info"

    def test_bridge_disabled_by_policy_is_real_blocker(self):
        workspace = _ready_workspace()
        _, _, _, bridge, final_check, enablement = _build_chain(workspace)
        assert bridge.bridge_status == "disabled_by_policy"
        assert enablement.can_create_quote_now is False
        assert "BRIDGE_DISABLED_BY_POLICY" in final_check.blockers

    def test_safety_mutation_flags_block_immediately(self):
        workspace = _ready_workspace()
        preview, dry_run, guard, bridge, _, _ = _build_chain(workspace)
        unsafe_flags = IntakeV3QuoteCreationDryRunSafetyFlags.model_construct(
            quote_creation_endpoint_called=True,
        )
        unsafe_dry_run = dry_run.model_copy(update={"safety_flags": unsafe_flags})
        final_check = evaluate_quote_creation_final_blockers(
            workspace,
            preview,
            unsafe_dry_run,
            guard,
            bridge,
        )
        assert "SAFETY_MUTATION_FLAG_DETECTED" in {i.code for i in final_check.items}

    def test_archived_workspace_safe_blocked(self):
        workspace = _ready_workspace()
        _, dry_run, _, bridge, final_check, enablement = _build_chain(workspace, archived=True)
        assert final_check.real_creation_status == "blocked"
        assert enablement.can_create_quote_now is False
        assert dry_run.dry_run_status == "blocked"
        assert bridge.bridge_status == "disabled_by_policy"


class TestQuoteCreationEnablementEndpoint:
    def test_get_enablement_read_only(self, auth_client):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "Enablement endpoint", "payload": MINIMAL_WORKSPACE_PAYLOAD},
        )
        assert create.status_code == 201
        workspace_id = create.json()["id"]
        before_updated = create.json()["updated_at"]

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/quote-creation-enablement"
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["enablement_policy"]["enablement_status"] == "owner_approval_required"
        assert payload["enablement_policy"]["can_create_quote_now"] is False
        assert payload["final_blocker_check"]["final_blockers_checked"] is True
        assert payload["final_blocker_check"]["real_creation_status"] == "blocked"
        assert payload["final_blocker_check"]["quote_created"] is False

        repeat = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/quote-creation-enablement"
        )
        assert repeat.status_code == 200
        assert repeat.json()["enablement_policy"]["policy_code"] == payload["enablement_policy"]["policy_code"]

        after = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert after.json()["updated_at"] == before_updated

    def test_preview_sets_enablement_availability_flag(self):
        build_result = build_intake_v3_workspace_preview(_ready_workspace())
        assert build_result.preview.quote_creation_enablement_available is True
        assert build_result.preview.quote_creation_enablement_status == "owner_approval_required"
        assert build_result.preview.quote_creation_real_status == "blocked"
