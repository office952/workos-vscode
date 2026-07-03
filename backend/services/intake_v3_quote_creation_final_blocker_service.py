"""Intake V3 quote creation final blocker check — preview vs real creation separation."""

from __future__ import annotations

from typing import Any, Literal

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE
from schemas.intake_v3 import (
    IntakeV3CommercialQuoteBridgePreview,
    IntakeV3QuoteCreationDryRun,
    IntakeV3QuoteCreationEnablementPolicy,
    IntakeV3QuoteCreationFinalBlockerCheck,
    IntakeV3QuoteCreationFinalBlockerItem,
    IntakeV3QuoteCreationGuardPolicy,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
)

FinalBlockerSeverity = Literal["blocker", "warning", "info", "pass"]
FinalCreationStatus = Literal["blocked", "pass", "ready"]


def _resolve_workspace(
    payload: dict[str, Any] | IntakeV3Workspace | None,
) -> IntakeV3Workspace | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return IntakeV3Workspace.model_validate(payload)
    return payload


def _item(
    *,
    code: str,
    label: str,
    severity: FinalBlockerSeverity,
    category: str,
    message: str,
    affects_preview: bool = False,
    affects_real_creation: bool = True,
) -> IntakeV3QuoteCreationFinalBlockerItem:
    return IntakeV3QuoteCreationFinalBlockerItem(
        code=code,
        label=label,
        severity=severity,
        category=category,
        message=message,
        affects_preview=affects_preview,
        affects_real_creation=affects_real_creation,
    )


def build_final_blocker_items(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    guard_policy: IntakeV3QuoteCreationGuardPolicy | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
    enablement_policy: IntakeV3QuoteCreationEnablementPolicy | None = None,
    *,
    workspace_archived: bool = False,
) -> list[IntakeV3QuoteCreationFinalBlockerItem]:
    """Build categorized final blocker items — no side effects."""
    items: list[IntakeV3QuoteCreationFinalBlockerItem] = []
    workspace = _resolve_workspace(payload)

    # 5.1 Workspace / data blockers
    if workspace is None:
        items.append(
            _item(
                code="WORKSPACE_MISSING",
                label="Workspace missing",
                severity="blocker",
                category="workspace",
                message="Workspace payload is missing.",
                affects_preview=True,
            )
        )
    if workspace_archived:
        items.append(
            _item(
                code="WORKSPACE_ARCHIVED",
                label="Workspace archived",
                severity="blocker",
                category="workspace",
                message="Workspace is archived — real quote creation is blocked.",
                affects_preview=True,
            )
        )
    if workspace:
        template = workspace.product_selection.template_code
        if not template:
            items.append(
                _item(
                    code="TEMPLATE_MISSING",
                    label="Template missing",
                    severity="blocker",
                    category="workspace",
                    message="Product template is missing.",
                    affects_preview=True,
                )
            )
        elif template != PILOT_TEMPLATE_CODE:
            items.append(
                _item(
                    code="TEMPLATE_UNSUPPORTED",
                    label="Template unsupported",
                    severity="blocker",
                    category="workspace",
                    message=f"Template {template} is not supported for Intake V3 quote enablement.",
                    affects_preview=True,
                )
            )
        cr = workspace.client_request
        if cr.width_mm is None or cr.height_mm is None:
            items.append(
                _item(
                    code="DIMENSIONS_MISSING",
                    label="Dimensions missing",
                    severity="blocker",
                    category="workspace",
                    message="Job width/height dimensions are missing.",
                    affects_preview=True,
                )
            )

    # 5.2 Production model blockers
    if workspace:
        if workspace.raw_svg_analysis is None and workspace.vector_asset is None:
            items.append(
                _item(
                    code="SVG_RAW_ANALYSIS_MISSING",
                    label="SVG / raw analysis missing",
                    severity="blocker",
                    category="production_model",
                    message="No SVG upload or raw analysis present.",
                    affects_preview=True,
                )
            )
        if workspace.confirmed_production_model is None:
            items.append(
                _item(
                    code="PRODUCTION_MODEL_UNCONFIRMED",
                    label="Production model unconfirmed",
                    severity="blocker",
                    category="production_model",
                    message="Confirmed production model is missing.",
                    affects_preview=True,
                )
            )
        elif workspace.confirmed_production_model.letter_count <= 0:
            items.append(
                _item(
                    code="LETTER_COUNT_MISSING",
                    label="Letter count missing",
                    severity="blocker",
                    category="production_model",
                    message="Confirmed letter count is zero or missing.",
                    affects_preview=True,
                )
            )

    # 5.3 Finish blockers
    if workspace:
        fa = workspace.finish_assignment
        if fa is None or not fa.confirmed_by_operator:
            items.append(
                _item(
                    code="GLOBAL_FINISH_MISSING",
                    label="Global finish missing",
                    severity="blocker",
                    category="finish",
                    message="Global finish assignment is missing or unconfirmed.",
                    affects_preview=True,
                )
            )
        else:
            if fa.face_finish and fa.face_finish.finish_type == "oracal_8500":
                if not fa.face_finish.face_vinyl_roll_width_mm:
                    items.append(
                        _item(
                            code="FACE_VINYL_ROLL_WIDTH_MISSING",
                            label="Face vinyl roll width missing",
                            severity="blocker",
                            category="finish",
                            message="Face vinyl requires roll width before real quote creation.",
                            affects_preview=True,
                        )
                    )
            if fa.return_finish and fa.return_finish.finish_type in {
                "oracal_wrapped",
                "wrapped_return",
            }:
                if not fa.return_finish.return_depth_mm:
                    items.append(
                        _item(
                            code="RETURN_DEPTH_MISSING",
                            label="Return depth missing",
                            severity="blocker",
                            category="finish",
                            message="Wrapped return requires return depth.",
                            affects_preview=True,
                        )
                    )
    if workspace_preview and workspace_preview.finish_variation_summary is None:
        fvs_needed = (
            workspace_preview.finish_summary.finish_variations_present
            if workspace_preview.finish_summary
            else False
        )
        if fvs_needed:
            items.append(
                _item(
                    code="FINISH_VARIATION_SUMMARY_MISSING",
                    label="Finish variation summary missing",
                    severity="blocker",
                    category="finish",
                    message="Finish variations exist but variation summary is missing.",
                    affects_preview=True,
                )
            )

    # 5.4 Pricing / quote blockers
    pricing = workspace_preview.pricing_input_candidate if workspace_preview else None
    if pricing is None:
        items.append(
            _item(
                code="PRICING_INPUT_CANDIDATE_MISSING",
                label="Pricing input candidate missing",
                severity="blocker",
                category="pricing",
                message="Pricing input candidate is missing.",
                affects_preview=True,
            )
        )
    items.append(
        _item(
            code="FINAL_PRICE_NOT_CALCULATED",
            label="Final price not calculated",
            severity="blocker",
            category="pricing",
            message="Final commercial price is not calculated — expected at this stage.",
            affects_preview=False,
        )
    )
    items.append(
        _item(
            code="QUOTE_INPUT_MAPPING_NOT_FINAL",
            label="Quote input mapping not final",
            severity="warning",
            category="pricing",
            message="quote_input mapping is preview-only until enablement build.",
            affects_preview=False,
        )
    )

    # CostEngine — expected not called at this stage
    cost_engine_called = False
    if dry_run and dry_run.safety_flags.cost_engine_called:
        cost_engine_called = True
    if bridge and bridge.safety_flags.cost_engine_called:
        cost_engine_called = True
    if cost_engine_called:
        items.append(
            _item(
                code="COST_ENGINE_CALLED_UNEXPECTEDLY",
                label="CostEngine called unexpectedly",
                severity="blocker",
                category="safety",
                message="CostEngine was called — this is a safety violation at this stage.",
                affects_preview=True,
            )
        )
    else:
        items.append(
            _item(
                code="COST_ENGINE_NOT_CALLED",
                label="CostEngine not called",
                severity="info",
                category="pricing",
                message="CostEngine not called — expected at this preview stage.",
                affects_preview=False,
                affects_real_creation=False,
            )
        )

    # 5.5 Bridge / policy blockers
    if dry_run is None:
        items.append(
            _item(
                code="DRY_RUN_MISSING",
                label="Dry-run missing",
                severity="blocker",
                category="bridge_policy",
                message="Quote creation dry-run contract is missing.",
            )
        )
    if guard_policy is None:
        items.append(
            _item(
                code="GUARD_POLICY_MISSING",
                label="Guard policy missing",
                severity="blocker",
                category="bridge_policy",
                message="Quote creation guard policy is missing.",
            )
        )
    elif guard_policy.disabled_by_policy:
        items.append(
            _item(
                code="REAL_QUOTE_CREATION_DISABLED_BY_POLICY",
                label="Real quote creation disabled by policy",
                severity="blocker",
                category="bridge_policy",
                message="Guard policy keeps real quote creation disabled.",
                affects_preview=False,
            )
        )
    if bridge is None:
        items.append(
            _item(
                code="COMMERCIAL_BRIDGE_MISSING",
                label="Commercial bridge missing",
                severity="blocker",
                category="bridge_policy",
                message="Commercial quote bridge preview is missing.",
            )
        )
    elif bridge.bridge_status == "disabled_by_policy":
        items.append(
            _item(
                code="BRIDGE_DISABLED_BY_POLICY",
                label="Bridge disabled by policy",
                severity="blocker",
                category="bridge_policy",
                message="Commercial quote bridge is disabled by policy.",
                affects_preview=False,
            )
        )
    items.append(
        _item(
            code="OWNER_APPROVAL_MISSING",
            label="Owner approval missing",
            severity="blocker",
            category="bridge_policy",
            message="Owner approval is required before real quote creation can be enabled.",
            affects_preview=False,
        )
    )
    items.append(
        _item(
            code="OWNER_DECISION_RECORD_MISSING",
            label="Owner decision record missing",
            severity="blocker",
            category="bridge_policy",
            message="Owner decision record is required and not captured in this build.",
            affects_preview=False,
        )
    )
    items.append(
        _item(
            code="SNAPSHOT_PERSISTENCE_NOT_EXECUTED",
            label="Snapshot persistence not executed",
            severity="blocker",
            category="bridge_policy",
            message="Snapshot policy is defined but persistence is not executed.",
            affects_preview=False,
        )
    )
    items.append(
        _item(
            code="REAL_QUOTE_CREATION_NOT_ENABLED",
            label="Real quote creation not enabled",
            severity="blocker",
            category="bridge_policy",
            message="Real quote creation is not enabled — requires owner-approved enablement build.",
            affects_preview=False,
        )
    )
    if enablement_policy and not enablement_policy.owner_approval_present:
        pass  # covered by OWNER_APPROVAL_MISSING

    # 5.6 Safety blockers
    safety_violation = False
    if dry_run:
        flags = dry_run.safety_flags
        if any(
            [
                flags.quote_creation_endpoint_called,
                flags.quote_created,
                flags.order_created,
                flags.execution_plan_created,
                flags.inventory_mutated,
                flags.pricing_formula_modified,
            ]
        ):
            safety_violation = True
    if bridge:
        bflags = bridge.safety_flags
        if any(
            [
                bflags.quote_creation_endpoint_called,
                bflags.quote_created,
                bflags.order_created,
                bflags.execution_plan_created,
                bflags.inventory_mutated,
                bflags.cost_engine_called,
            ]
        ):
            safety_violation = True
    if workspace_preview and workspace_preview.created_quote_id is not None:
        safety_violation = True
        items.append(
            _item(
                code="QUOTE_ID_ALREADY_PRESENT",
                label="Quote ID already present",
                severity="blocker",
                category="safety",
                message="Preview reports a created quote ID — safety violation.",
                affects_preview=True,
            )
        )
    if safety_violation:
        items.append(
            _item(
                code="SAFETY_MUTATION_FLAG_DETECTED",
                label="Safety mutation flag detected",
                severity="blocker",
                category="safety",
                message="A safety mutation flag is set — real quote creation blocked immediately.",
                affects_preview=True,
            )
        )
    else:
        items.append(
            _item(
                code="SAFETY_FLAGS_CLEAR",
                label="Safety flags clear",
                severity="pass",
                category="safety",
                message="No quote/order/execution/inventory mutation detected.",
                affects_preview=False,
                affects_real_creation=False,
            )
        )

    return items


def classify_final_blockers(
    items: list[IntakeV3QuoteCreationFinalBlockerItem],
) -> list[str]:
    return [
        item.code
        for item in items
        if item.severity == "blocker" and item.affects_real_creation
    ]


def classify_final_warnings(
    items: list[IntakeV3QuoteCreationFinalBlockerItem],
) -> list[str]:
    return [item.code for item in items if item.severity == "warning"]


def _preview_status(
    items: list[IntakeV3QuoteCreationFinalBlockerItem],
) -> FinalCreationStatus:
    preview_blockers = [
        item for item in items if item.severity == "blocker" and item.affects_preview
    ]
    if preview_blockers:
        return "blocked"
    return "pass"


def evaluate_quote_creation_final_blockers(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    guard_policy: IntakeV3QuoteCreationGuardPolicy | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
    enablement_policy: IntakeV3QuoteCreationEnablementPolicy | None = None,
    *,
    workspace_archived: bool = False,
) -> IntakeV3QuoteCreationFinalBlockerCheck:
    """Evaluate final blockers — always blocks real creation in this build."""
    items = build_final_blocker_items(
        payload,
        workspace_preview,
        dry_run,
        guard_policy,
        bridge,
        enablement_policy,
        workspace_archived=workspace_archived,
    )
    blockers = classify_final_blockers(items)
    warnings = classify_final_warnings(items)
    preview_status = _preview_status(items)
    real_creation_status: FinalCreationStatus = "blocked"

    cost_engine_called = False

    return IntakeV3QuoteCreationFinalBlockerCheck(
        final_blockers_checked=True,
        preview_status=preview_status,
        real_creation_status=real_creation_status,
        can_create_quote_now=False,
        items=items,
        blockers=blockers,
        warnings=warnings,
        cost_engine_called=cost_engine_called,
        quote_creation_endpoint_called=False,
        quote_created=False,
        next_action=(
            "Resolve final blockers and obtain owner approval before a future enablement build."
        ),
    )


def is_quote_creation_enablement_available(
    workspace: IntakeV3Workspace,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    *,
    workspace_archived: bool = False,
) -> bool:
    """True when workspace can build enablement policy + final blocker check preview."""
    from services.intake_v3_commercial_quote_bridge_service import (
        is_commercial_quote_bridge_available,
    )

    return is_commercial_quote_bridge_available(
        workspace,
        workspace_preview,
        workspace_archived=workspace_archived,
    )


def quote_creation_enablement_status_label() -> str:
    return "owner_approval_required"
