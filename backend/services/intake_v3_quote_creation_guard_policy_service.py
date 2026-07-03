"""Intake V3 quote creation guard policy — disabled-by-default, no real quote creation."""

from __future__ import annotations

from typing import Any, Literal

from schemas.intake_v3 import (
    IntakeV3QuoteCreationDryRun,
    IntakeV3QuoteCreationGuardPolicy,
    IntakeV3QuoteCreationGuardReason,
    IntakeV3QuoteReadinessItem,
    IntakeV3QuoteReadinessResult,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
)

PolicyStatus = Literal["disabled_by_default"]

POLICY_CODE = "INTAKE_V3_QUOTE_CREATION_DISABLED_BY_DEFAULT"
POLICY_DISABLED_REASON = (
    "Real quote creation is disabled by policy until an owner-approved build enables it."
)

REQUIRED_BEFORE_ENABLE: tuple[str, ...] = (
    "Owner approval",
    "Commercial quote bridge mapping reviewed",
    "Real quote snapshot persistence defined",
    "Real quote endpoint integration guarded",
    "CostEngine boundary confirmed",
    "Rollback/backup point confirmed before enabling",
)


def is_real_quote_creation_enabled() -> bool:
    """Real quote creation remains disabled until a dedicated owner-approved build."""
    return False


def build_disabled_by_default_policy(
    *,
    safe_to_dry_run: bool = True,
    observed_preconditions: list[str] | None = None,
    extra_reasons: list[IntakeV3QuoteCreationGuardReason] | None = None,
) -> IntakeV3QuoteCreationGuardPolicy:
    reasons = [
        IntakeV3QuoteCreationGuardReason(
            code="REAL_QUOTE_CREATION_DISABLED_BY_POLICY",
            severity="info",
            message=POLICY_DISABLED_REASON,
        ),
        IntakeV3QuoteCreationGuardReason(
            code="QUOTE_CREATION_NOT_IMPLEMENTED",
            severity="info",
            message="Commercial quote creation from Intake V3 is not implemented or enabled in this build.",
        ),
        IntakeV3QuoteCreationGuardReason(
            code="DRY_RUN_ALLOWED",
            severity="info",
            message="Quote creation dry-run preview is allowed — no quote endpoint is called.",
        ),
    ]
    if extra_reasons:
        reasons.extend(extra_reasons)

    return IntakeV3QuoteCreationGuardPolicy(
        policy_status="disabled_by_default",
        policy_code=POLICY_CODE,
        can_create_quote=False,
        real_quote_creation_enabled=False,
        disabled_by_policy=True,
        owner_confirmation_required=True,
        safe_to_dry_run=safe_to_dry_run,
        reasons=reasons,
        required_before_enable=list(REQUIRED_BEFORE_ENABLE),
        observed_preconditions=observed_preconditions or [],
    )


def build_required_before_enable(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
) -> list[str]:
    del payload, workspace_preview, dry_run
    return list(REQUIRED_BEFORE_ENABLE)


def _resolve_workspace(
    payload: dict[str, Any] | IntakeV3Workspace | None,
) -> IntakeV3Workspace | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return IntakeV3Workspace.model_validate(payload)
    return payload


def _resolve_quote_readiness(
    workspace: IntakeV3Workspace | None,
    workspace_preview: IntakeV3WorkspacePreview | None,
) -> IntakeV3QuoteReadinessResult | None:
    if workspace_preview and workspace_preview.quote_readiness:
        return workspace_preview.quote_readiness
    return None


def build_observed_preconditions(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    *,
    workspace_archived: bool = False,
) -> list[str]:
    """Inspect readiness/dry-run fragments — preconditions never enable quote creation."""
    observed: list[str] = []
    workspace = _resolve_workspace(payload)
    quote_readiness = _resolve_quote_readiness(workspace, workspace_preview)

    if workspace_archived:
        observed.append("workspace_archived: true")
    else:
        observed.append("workspace_archived: false")

    if quote_readiness:
        observed.append(f"quote_readiness_status: {quote_readiness.status}")
        observed.append(f"quote_readiness_blockers: {len(quote_readiness.blockers)}")
    elif workspace_preview and workspace_preview.quote_readiness:
        observed.append(f"quote_readiness_status: {workspace_preview.quote_readiness.status}")
    else:
        observed.append("quote_readiness_status: not_evaluated")

    if dry_run is not None:
        observed.append(f"dry_run_status: {dry_run.dry_run_status}")
        observed.append(f"dry_run_blockers: {len(dry_run.blockers)}")
        flags = dry_run.safety_flags
        observed.append(
            "dry_run_safety_flags_clear: "
            f"{not any([flags.quote_created, flags.cost_engine_called, flags.inventory_mutated])}"
        )
    elif workspace_preview and workspace_preview.quote_creation_dry_run_available:
        observed.append("dry_run_available: true")
    else:
        observed.append("dry_run_available: false")

    if workspace and workspace.confirmed_production_model is not None:
        observed.append("confirmed_production_model: present")
    else:
        observed.append("confirmed_production_model: missing")

    if workspace_preview and workspace_preview.pricing_input_candidate is not None:
        observed.append("pricing_input_preview: present")
    elif workspace_preview:
        observed.append("pricing_input_preview: missing")
    else:
        observed.append("pricing_input_preview: unknown")

    if workspace_preview and workspace_preview.finish_variation_summary is not None:
        observed.append("finish_variation_summary: present")
    else:
        observed.append("finish_variation_summary: missing")

    return observed


def build_quote_creation_guard_reasons(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    *,
    workspace_archived: bool = False,
) -> list[IntakeV3QuoteCreationGuardReason]:
    reasons = [
        IntakeV3QuoteCreationGuardReason(
            code="REAL_QUOTE_CREATION_DISABLED_BY_POLICY",
            severity="info",
            message=POLICY_DISABLED_REASON,
        ),
        IntakeV3QuoteCreationGuardReason(
            code="OWNER_CONFIRMATION_REQUIRED",
            severity="info",
            message="Owner approval is required before enabling commercial quote creation from Intake V3.",
        ),
        IntakeV3QuoteCreationGuardReason(
            code="DRY_RUN_ALLOWED_REAL_QUOTE_DISABLED",
            severity="info",
            message="Dry-run is allowed. Real quote creation is not.",
        ),
    ]
    if workspace_archived:
        reasons.append(
            IntakeV3QuoteCreationGuardReason(
                code="WORKSPACE_ARCHIVED",
                severity="info",
                message="Workspace is archived — policy remains disabled and dry-run may be blocked.",
            )
        )
    if dry_run and dry_run.blockers:
        reasons.append(
            IntakeV3QuoteCreationGuardReason(
                code="DRY_RUN_OPERATIONAL_BLOCKERS",
                severity="info",
                message=(
                    "Operational dry-run blockers exist — they do not override the disabled-by-default policy."
                ),
            )
        )
    del payload, workspace_preview
    return reasons


def evaluate_quote_creation_guard_policy(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    *,
    workspace_archived: bool = False,
) -> IntakeV3QuoteCreationGuardPolicy:
    """Central guard policy — always disabled-by-default regardless of readiness or dry-run quality."""
    safe_to_dry_run = not workspace_archived
    observed = build_observed_preconditions(
        payload,
        workspace_preview,
        dry_run,
        workspace_archived=workspace_archived,
    )
    reasons = build_quote_creation_guard_reasons(
        payload,
        workspace_preview,
        dry_run,
        workspace_archived=workspace_archived,
    )
    return IntakeV3QuoteCreationGuardPolicy(
        policy_status="disabled_by_default",
        policy_code=POLICY_CODE,
        can_create_quote=False,
        real_quote_creation_enabled=False,
        disabled_by_policy=True,
        owner_confirmation_required=True,
        safe_to_dry_run=safe_to_dry_run,
        reasons=reasons,
        required_before_enable=build_required_before_enable(payload, workspace_preview, dry_run),
        observed_preconditions=observed,
        enablement_policy_status="owner_approval_required",
        final_blocker_check_available=True,
    )


def build_quote_creation_policy_readiness_item() -> IntakeV3QuoteReadinessItem:
    """Info-only checklist item — separate from operational blockers."""
    return IntakeV3QuoteReadinessItem(
        code="QUOTE_CREATION_POLICY_DISABLED",
        label="Quote creation policy",
        severity="info",
        status="info",
        message=POLICY_DISABLED_REASON,
        recommended_action="Complete owner-approved commercial quote bridge build before enabling quote creation.",
        source="quote_creation_guard_policy",
        editable_here=False,
        related_section="safety",
    )
