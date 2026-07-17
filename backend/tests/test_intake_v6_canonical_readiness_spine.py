"""W1-L-SPINE — canonical readiness truth spine regression tests."""

from __future__ import annotations

from services.intake_v4_internal_draft_quote_policy_service import evaluate_internal_draft_quote_policy
from services.intake_v6_canonical_readiness_service import (
    apply_readiness_spine_to_pricing_preview,
    list_runtime_capture_fatal_blocker_codes,
    merge_policy_findings,
)
from services.intake_v6_workspace_service import _derive_readiness_status
from services.mounting_solution_service import ACM_BOXED_MOUNTING_TEMPLATE_CODE, METAL_PREMOUNT_TEMPLATE_CODE
from schemas.intake_v6 import IntakeV6WorkspacePayload


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"


def _base_payload() -> dict:
    return {
        "product_binding": {"template_code": ROOT},
        "svg_source": {
            "upload_status": "analyzed",
            "file_name": "fixture.svg",
            "file_size_bytes": 1024,
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "face-1",
                    "layer_id": "face-1",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
        },
        "svg": {
            "selected_layer_refs": [
                {
                    "layer_id": "face-1",
                    "role": "vector_litere",
                    "confirmed": True,
                }
            ]
        },
        "finish_setup": {
            "finish_target": "face",
            "confirmed": True,
            "artwork_finishes": [
                {"layer_key": "logo-left", "print_required": True, "lamination_required": False},
            ],
            "mounting_scope": "mounting_included",
        },
    }


def _payload_with_mounting_solution(template_code: str = ACM_BOXED_MOUNTING_TEMPLATE_CODE) -> IntakeV6WorkspacePayload:
    raw = _base_payload()
    raw["finish_setup"]["mounting_solution"] = {
        "template_code": template_code,
        "configuration": {
            "panel_width_mm": 1000,
            "panel_height_mm": 600,
            "acm_thickness_mm": 3,
            "return_depth_mm": 60,
            "rear_lip_mm": 25,
            "fold_sides": "all",
            "v_groove_angle_deg": 135,
            "frame_clearance_mm": 0,
        }
        if template_code == ACM_BOXED_MOUNTING_TEMPLATE_CODE
        else {
            "bar_count": 2,
            "mounting_bar_profile": "30x30x1.5",
            "bar_material": "steel",
        },
    }
    return IntakeV6WorkspacePayload.model_validate(raw)


def test_canonical_mounting_solution_satisfies_runtime_capture_requirement() -> None:
    payload = _payload_with_mounting_solution()
    blockers = list_runtime_capture_fatal_blocker_codes(payload.model_dump(mode="json"), template_code=ROOT)
    assert blockers == []


def test_missing_canonical_mounting_truth_still_blocks_when_prep_active() -> None:
    raw = _base_payload()
    raw["finish_setup"]["mounting_system"] = "steel_bars"
    raw["finish_setup"]["support_type"] = "steel_frame"
    blockers = list_runtime_capture_fatal_blocker_codes(raw, template_code=ROOT)
    assert "MOUNTING_SOLUTION_MISSING" in blockers


def test_cant_only_subset_does_not_surface_mounting_capture_blocker() -> None:
    raw = _base_payload()
    raw["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": "component_subset",
        "sold_modules": ["RETURN-CANT"],
    }
    raw["finish_setup"]["mounting_scope"] = "preparation_only"
    blockers = list_runtime_capture_fatal_blocker_codes(raw, template_code=ROOT)
    assert "MOUNTING_SOLUTION_MISSING" not in blockers


def test_face_only_subset_does_not_surface_mounting_capture_blocker() -> None:
    raw = _base_payload()
    raw["offer_scope"] = {
        "contract_version": "offer_scope_contract/v1",
        "mode": "component_subset",
        "sold_modules": ["FACE"],
    }
    blockers = list_runtime_capture_fatal_blocker_codes(raw, template_code=ROOT)
    assert "MOUNTING_SOLUTION_MISSING" not in blockers


def test_legacy_only_support_type_does_not_clear_mounting_blocker() -> None:
    raw = _base_payload()
    raw["finish_setup"]["support_type"] = "steel_frame"
    raw["finish_setup"]["mounting_system"] = "steel_bars"
    blockers = list_runtime_capture_fatal_blocker_codes(raw, template_code=ROOT)
    assert "SUPPORT_TYPE_MISSING" not in blockers
    assert "MOUNTING_SOLUTION_MISSING" in blockers


def test_workspace_readiness_blocked_when_capture_blockers_active() -> None:
    raw = _base_payload()
    payload = IntakeV6WorkspacePayload.model_validate(raw)
    assert _derive_readiness_status(payload) == "runtime_capture_blocked"


def test_workspace_readiness_ready_when_canonical_mounting_and_capture_clear() -> None:
    payload = _payload_with_mounting_solution()
    assert _derive_readiness_status(payload) == "ready_for_quote_preview"


def test_pricing_preview_merges_capture_blockers_into_adapter_blockers() -> None:
    from schemas.intake_v4 import IntakeV4PricingInputPreviewResponse

    preview = IntakeV4PricingInputPreviewResponse(
        workspace_id="ws-spine",
        template_code=ROOT,
        is_ready_for_quote=True,
        adapter_status="ready",
        adapter_blockers=[],
        adapter_warnings=[],
        quote_input_payload={"letter_count": 3},
    )
    raw = _base_payload()
    enriched = apply_readiness_spine_to_pricing_preview(preview, payload=raw, template_code=ROOT)
    assert enriched.is_ready_for_quote is False
    assert "runtime_capture:MOUNTING_SOLUTION_MISSING" in enriched.adapter_blockers


def test_handoff_policy_consumes_pricing_preview_adapter_blockers() -> None:
    from schemas.intake_v4 import IntakeV4PricingInputPreviewResponse
    from types import SimpleNamespace

    record = SimpleNamespace(
        archived_at=None,
        readiness_status="ready_for_quote_preview",
    )
    payload = _payload_with_mounting_solution()
    preview = IntakeV4PricingInputPreviewResponse(
        workspace_id="ws-spine",
        template_code=ROOT,
        is_ready_for_quote=False,
        adapter_status="blocked",
        adapter_blockers=["runtime_capture:MOUNTING_SOLUTION_MISSING"],
        adapter_warnings=[],
        quote_input_payload={"letter_count": 3},
    )
    policy = evaluate_internal_draft_quote_policy(record, payload, pricing_preview=preview, include_hash_sync=False)
    assert policy.can_create_internal_draft_quote is False
    assert any("runtime_capture:MOUNTING_SOLUTION_MISSING" in code for code in policy.fatal_blockers)


def test_merge_policy_findings_combines_policy_and_canonical_findings() -> None:
    from services.intake_v6_canonical_readiness_service import IntakeV6CanonicalReadinessFindings
    from types import SimpleNamespace

    policy = SimpleNamespace(
        fatal_blockers=["operator_confirmation_missing"],
        review_warnings=["artwork_execution_undecided:logo-left"],
    )
    findings = IntakeV6CanonicalReadinessFindings(
        fatal_blockers=["canonical_missing_required_field:mounting_solution"],
        review_warnings=[],
    )
    merged = merge_policy_findings(policy=policy, findings=findings)
    assert "operator_confirmation_missing" in merged["fatal_blockers"]
    assert "canonical_missing_required_field:mounting_solution" in merged["fatal_blockers"]
    assert merged["can_create_internal_draft_quote"] is False


def test_acm_template_code_satisfies_mounting_requirement() -> None:
    payload = _payload_with_mounting_solution(ACM_BOXED_MOUNTING_TEMPLATE_CODE)
    blockers = list_runtime_capture_fatal_blocker_codes(payload.model_dump(mode="json"), template_code=ROOT)
    assert blockers == []
    assert _derive_readiness_status(payload) == "ready_for_quote_preview"


def test_metal_template_code_satisfies_mounting_requirement() -> None:
    payload = _payload_with_mounting_solution(METAL_PREMOUNT_TEMPLATE_CODE)
    blockers = list_runtime_capture_fatal_blocker_codes(payload.model_dump(mode="json"), template_code=ROOT)
    assert blockers == []
    assert _derive_readiness_status(payload) == "ready_for_quote_preview"
