"""Intake V3 quote creation guard policy — disabled-by-default, no quote/CostEngine side effects."""

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
    QUOTE_CREATION_DISABLED_REASON,
    build_intake_v3_quote_creation_dry_run,
)
from services.intake_v3_quote_creation_guard_policy_service import (
    POLICY_CODE,
    POLICY_DISABLED_REASON,
    REQUIRED_BEFORE_ENABLE,
    evaluate_quote_creation_guard_policy,
    is_real_quote_creation_enabled,
)
from services.intake_v3_quote_readiness_service import evaluate_intake_v3_quote_readiness
from services.intake_v3_workspace_preview_service import build_intake_v3_workspace_preview

MINIMAL_WORKSPACE_PAYLOAD = {
    "client_request": {
        "client_name": "Policy test",
        "request_code": "POL-TEST-001",
        "job_title": "Policy test",
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


class TestQuoteCreationGuardPolicy:
    def test_policy_disabled_by_default(self):
        policy = evaluate_quote_creation_guard_policy(MINIMAL_WORKSPACE_PAYLOAD)
        assert policy.policy_status == "disabled_by_default"
        assert policy.policy_code == POLICY_CODE
        assert policy.can_create_quote is False
        assert policy.real_quote_creation_enabled is False
        assert policy.disabled_by_policy is True
        assert policy.owner_confirmation_required is True
        assert is_real_quote_creation_enabled() is False

    def test_complete_workspace_still_cannot_create_quote(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        quote_readiness = evaluate_intake_v3_quote_readiness(workspace, preview)
        assert quote_readiness.status == "ready_preview_only"
        policy = evaluate_quote_creation_guard_policy(workspace, preview)
        assert policy.can_create_quote is False
        assert policy.real_quote_creation_enabled is False
        assert policy.disabled_by_policy is True

    def test_blocked_workspace_still_policy_disabled(self):
        workspace = IntakeV3Workspace.model_validate(MINIMAL_WORKSPACE_PAYLOAD)
        preview = build_intake_v3_workspace_preview(workspace).preview
        quote_readiness = evaluate_intake_v3_quote_readiness(workspace, preview)
        assert quote_readiness.status == "blocked"
        policy = evaluate_quote_creation_guard_policy(workspace, preview)
        assert policy.disabled_by_policy is True
        assert policy.can_create_quote is False
        assert any("quote_readiness_status: blocked" in item for item in policy.observed_preconditions)

    def test_required_before_enable_list_present(self):
        policy = evaluate_quote_creation_guard_policy(MINIMAL_WORKSPACE_PAYLOAD)
        required = policy.required_before_enable
        assert "Owner approval" in required
        assert any("bridge" in item.lower() for item in required)
        assert any("snapshot" in item.lower() for item in required)
        assert any("endpoint" in item.lower() for item in required)
        assert any("CostEngine" in item for item in required)
        assert any("Rollback" in item or "backup" in item.lower() for item in required)
        assert list(REQUIRED_BEFORE_ENABLE) == required

    def test_dry_run_includes_guard_policy(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        dry_run = build_intake_v3_quote_creation_dry_run(workspace, preview, workspace_id="ws-policy")
        assert dry_run.guard_policy is not None
        assert dry_run.guard_policy.disabled_by_policy is True
        assert dry_run.quote_creation_disabled_reason == POLICY_DISABLED_REASON
        assert dry_run.quote_creation_disabled_reason == QUOTE_CREATION_DISABLED_REASON

    def test_quote_readiness_includes_info_policy_item(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        result = evaluate_intake_v3_quote_readiness(workspace, preview)
        policy_items = [item for item in result.checklist if item.code == "QUOTE_CREATION_POLICY_DISABLED"]
        assert len(policy_items) == 1
        assert policy_items[0].severity == "info"
        assert policy_items[0].status == "info"
        assert policy_items[0] not in result.blockers

    def test_archived_workspace_policy_still_disabled(self):
        workspace = _ready_workspace()
        preview = build_intake_v3_workspace_preview(workspace).preview
        policy = evaluate_quote_creation_guard_policy(
            workspace,
            preview,
            workspace_archived=True,
        )
        assert policy.can_create_quote is False
        assert policy.safe_to_dry_run is False
        assert any("workspace_archived: true" in item for item in policy.observed_preconditions)


class TestQuoteCreationGuardPolicyEndpoint:
    def test_get_guard_policy_read_only(self, auth_client):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "Guard policy endpoint", "payload": MINIMAL_WORKSPACE_PAYLOAD},
        )
        assert create.status_code == 201
        workspace_id = create.json()["id"]
        before_updated = create.json()["updated_at"]

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/quote-creation-guard-policy"
        )
        assert response.status_code == 200
        payload = response.json()
        policy = payload["guard_policy"]
        assert policy["policy_status"] == "disabled_by_default"
        assert policy["can_create_quote"] is False
        assert policy["real_quote_creation_enabled"] is False
        assert policy["disabled_by_policy"] is True

        repeat = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/quote-creation-guard-policy"
        )
        assert repeat.status_code == 200
        assert repeat.json()["guard_policy"]["policy_code"] == policy["policy_code"]

        after = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}")
        assert after.json()["updated_at"] == before_updated

    def test_safety_boundary_no_side_effects(self, auth_client):
        create = auth_client.post(
            "/api/v1/intake-v3/workspaces",
            json={"title": "Guard safety", "payload": MINIMAL_WORKSPACE_PAYLOAD},
        )
        workspace_id = create.json()["id"]
        dry_run = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/quote-creation-dry-run"
        ).json()["dry_run"]
        assert dry_run["safety_flags"]["quote_created"] is False
        assert dry_run["safety_flags"]["cost_engine_called"] is False
        assert dry_run["guard_policy"]["can_create_quote"] is False
