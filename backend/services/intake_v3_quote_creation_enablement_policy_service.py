"""Intake V3 quote creation enablement policy — owner approval required, no real quote creation."""

from __future__ import annotations

from typing import Any, Literal

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE
from schemas.intake_v3 import (
    IntakeV3CommercialQuoteBridgePreview,
    IntakeV3OwnerApprovalContractPreview,
    IntakeV3QuoteCreationDryRun,
    IntakeV3QuoteCreationEnablementBlocker,
    IntakeV3QuoteCreationEnablementPolicy,
    IntakeV3QuoteCreationEnablementRequirement,
    IntakeV3QuoteCreationFinalBlockerCheck,
    IntakeV3QuoteCreationGuardPolicy,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
)

EnablementStatus = Literal["owner_approval_required"]

POLICY_CODE = "INTAKE_V3_REAL_QUOTE_CREATION_REQUIRES_OWNER_APPROVAL"
NEXT_ACTION = (
    "Owner must approve a dedicated real quote creation build before enabling quote creation."
)

ENABLEMENT_REQUIREMENTS: tuple[tuple[str, str], ...] = (
    ("OWNER_APPROVAL", "Owner approval for real quote creation enablement build"),
    ("GUARD_POLICY_REVIEW", "Quote creation guard policy reviewed and accepted"),
    ("COMMERCIAL_BRIDGE_REVIEW", "Commercial quote bridge mapping reviewed"),
    ("FINAL_BLOCKER_CHECK", "Final blocker check reviewed with no safety violations"),
    ("SNAPSHOT_PERSISTENCE_DECISION", "Real quote snapshot persistence target defined"),
    ("QUOTE_ENDPOINT_GUARD", "Real quote endpoint integration guarded"),
    ("COSTENGINE_BOUNDARY", "CostEngine boundary confirmed for enablement build"),
    ("ROLLBACK_POINT", "Rollback/backup point confirmed before enabling"),
)


def can_enable_real_quote_creation() -> bool:
    """Real quote enablement remains false until a future owner-approved build."""
    return False


def _resolve_workspace(
    payload: dict[str, Any] | IntakeV3Workspace | None,
) -> IntakeV3Workspace | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return IntakeV3Workspace.model_validate(payload)
    return payload


def build_owner_approval_contract(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    *,
    workspace_title: str | None = None,
) -> IntakeV3OwnerApprovalContractPreview:
    workspace = _resolve_workspace(payload)
    return IntakeV3OwnerApprovalContractPreview(
        owner_approval_required=True,
        owner_approval_present=False,
        approval_scope="real_quote_creation_enablement",
        workspace_id=workspace_preview.workspace_id if workspace_preview else "",
        workspace_title=workspace_title
        or (workspace.client_request.job_title if workspace else ""),
        template_code=workspace.product_selection.template_code if workspace else PILOT_TEMPLATE_CODE,
        contract_note=(
            "Owner approval is required before Intake V3 real quote creation can be enabled. "
            "This foundation build does not record or accept approval."
        ),
    )


def build_quote_creation_enablement_requirements(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    guard_policy: IntakeV3QuoteCreationGuardPolicy | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
) -> list[IntakeV3QuoteCreationEnablementRequirement]:
    del payload, workspace_preview, dry_run, guard_policy, bridge
    return [
        IntakeV3QuoteCreationEnablementRequirement(code=code, requirement=text)
        for code, text in ENABLEMENT_REQUIREMENTS
    ]


def build_quote_creation_enablement_blockers(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    guard_policy: IntakeV3QuoteCreationGuardPolicy | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
    *,
    workspace_archived: bool = False,
    final_blocker_check: IntakeV3QuoteCreationFinalBlockerCheck | None = None,
) -> list[IntakeV3QuoteCreationEnablementBlocker]:
    blockers: list[IntakeV3QuoteCreationEnablementBlocker] = [
        IntakeV3QuoteCreationEnablementBlocker(
            code="OWNER_APPROVAL_MISSING",
            severity="blocker",
            message="Owner approval is not present — real quote creation cannot be enabled.",
        ),
        IntakeV3QuoteCreationEnablementBlocker(
            code="REAL_QUOTE_CREATION_DISABLED_BY_POLICY",
            severity="blocker",
            message="Real quote creation is disabled by policy until owner-approved enablement.",
        ),
    ]
    if guard_policy is None:
        blockers.append(
            IntakeV3QuoteCreationEnablementBlocker(
                code="GUARD_POLICY_MISSING",
                severity="blocker",
                message="Quote creation guard policy is missing.",
            )
        )
    if bridge is None:
        blockers.append(
            IntakeV3QuoteCreationEnablementBlocker(
                code="COMMERCIAL_BRIDGE_MISSING",
                severity="blocker",
                message="Commercial quote bridge preview is missing.",
            )
        )
    elif bridge.bridge_status == "disabled_by_policy":
        blockers.append(
            IntakeV3QuoteCreationEnablementBlocker(
                code="BRIDGE_DISABLED_BY_POLICY",
                severity="blocker",
                message="Commercial quote bridge is disabled by policy.",
            )
        )
    if dry_run is None:
        blockers.append(
            IntakeV3QuoteCreationEnablementBlocker(
                code="DRY_RUN_MISSING",
                severity="blocker",
                message="Quote creation dry-run contract is missing.",
            )
        )
    if workspace_archived:
        blockers.append(
            IntakeV3QuoteCreationEnablementBlocker(
                code="WORKSPACE_ARCHIVED",
                severity="blocker",
                message="Workspace is archived — real quote creation cannot be enabled.",
            )
        )
    if final_blocker_check and final_blocker_check.real_creation_status == "blocked":
        for code in final_blocker_check.blockers[:5]:
            if code not in {b.code for b in blockers}:
                blockers.append(
                    IntakeV3QuoteCreationEnablementBlocker(
                        code=code,
                        severity="blocker",
                        message=f"Final blocker check: {code}.",
                    )
                )
    return blockers


def build_quote_creation_enablement_warnings(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    guard_policy: IntakeV3QuoteCreationGuardPolicy | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
) -> list[IntakeV3QuoteCreationEnablementBlocker]:
    del payload, dry_run
    warnings: list[IntakeV3QuoteCreationEnablementBlocker] = []
    if workspace_preview and workspace_preview.quote_readiness:
        if workspace_preview.quote_readiness.warnings:
            warnings.append(
                IntakeV3QuoteCreationEnablementBlocker(
                    code="QUOTE_READINESS_WARNINGS",
                    severity="warning",
                    message="Quote readiness warnings should be reviewed before enablement.",
                )
            )
    if bridge and bridge.missing_fields:
        warnings.append(
            IntakeV3QuoteCreationEnablementBlocker(
                code="BRIDGE_MISSING_FIELDS",
                severity="warning",
                message="Commercial bridge reports missing fields for real quote handoff.",
            )
        )
    if guard_policy and guard_policy.observed_preconditions:
        warnings.append(
            IntakeV3QuoteCreationEnablementBlocker(
                code="GUARD_PRECONDITIONS_REVIEW",
                severity="warning",
                message="Review guard policy observed preconditions before enablement.",
            )
        )
    return warnings


def _observed_gates(
    workspace_preview: IntakeV3WorkspacePreview | None,
    dry_run: IntakeV3QuoteCreationDryRun | None,
    guard_policy: IntakeV3QuoteCreationGuardPolicy | None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None,
) -> list[str]:
    gates: list[str] = []
    if workspace_preview and workspace_preview.quote_readiness:
        gates.append(f"quote_readiness:{workspace_preview.quote_readiness.status}")
    if workspace_preview and workspace_preview.prequote_review:
        gates.append(f"prequote_review:{workspace_preview.prequote_review.status}")
    if dry_run:
        gates.append(f"dry_run:{dry_run.dry_run_status}")
    if guard_policy:
        gates.append(f"guard_policy:{guard_policy.policy_status}")
    if bridge:
        gates.append(f"commercial_bridge:{bridge.bridge_status}")
    return gates


def evaluate_quote_creation_enablement_policy(
    payload: dict[str, Any] | IntakeV3Workspace,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    *,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    guard_policy: IntakeV3QuoteCreationGuardPolicy | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
    final_blocker_check: IntakeV3QuoteCreationFinalBlockerCheck | None = None,
    workspace_title: str | None = None,
    workspace_archived: bool = False,
) -> IntakeV3QuoteCreationEnablementPolicy:
    """Evaluate enablement policy — never enables real quote creation in this build."""
    requirements = build_quote_creation_enablement_requirements(
        payload,
        workspace_preview,
        dry_run,
        guard_policy,
        bridge,
    )
    blockers = build_quote_creation_enablement_blockers(
        payload,
        workspace_preview,
        dry_run,
        guard_policy,
        bridge,
        workspace_archived=workspace_archived,
        final_blocker_check=final_blocker_check,
    )
    warnings = build_quote_creation_enablement_warnings(
        payload,
        workspace_preview,
        dry_run,
        guard_policy,
        bridge,
    )
    owner_contract = build_owner_approval_contract(
        payload,
        workspace_preview,
        workspace_title=workspace_title,
    )
    preview_status = (
        final_blocker_check.preview_status
        if final_blocker_check
        else "blocked"
    )
    real_creation_status = (
        final_blocker_check.real_creation_status
        if final_blocker_check
        else "blocked"
    )
    return IntakeV3QuoteCreationEnablementPolicy(
        enablement_status="owner_approval_required",
        can_enable_real_quote_creation=False,
        can_create_quote_now=False,
        owner_approval_required=True,
        owner_approval_present=False,
        policy_code=POLICY_CODE,
        requirements=requirements,
        blockers=blockers,
        warnings=warnings,
        observed_gates=_observed_gates(workspace_preview, dry_run, guard_policy, bridge),
        owner_approval_contract=owner_contract,
        preview_status=preview_status,
        real_creation_status=real_creation_status,
        final_blockers_checked=final_blocker_check.final_blockers_checked
        if final_blocker_check
        else True,
        next_action=NEXT_ACTION,
        owner_decision_record_status="required_not_present",
        snapshot_policy_status="defined_not_executed",
        anti_duplicate_policy_status="defined",
        rollback_policy_status="defined",
        real_quote_creation_enablement_readiness_status="blocked_owner_decision_missing",
    )
