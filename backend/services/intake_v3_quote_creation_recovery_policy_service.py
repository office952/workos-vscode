"""Intake V3 quote creation rollback/recovery policy — failure modes preview only."""

from __future__ import annotations

from typing import Any

from schemas.intake_v3 import (
    IntakeV3CommercialQuoteBridgePreview,
    IntakeV3QuoteCreationFailureMode,
    IntakeV3QuoteCreationRecoveryAction,
    IntakeV3QuoteCreationRecoveryPolicy,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
)

NEXT_ACTION = (
    "Real quote creation build must define rollback or manual recovery behavior before enabling writes."
)

FAILURE_MODE_SPECS: tuple[tuple[str, str, str], ...] = (
    (
        "QUOTE_CREATED_SNAPSHOT_FAILED",
        "blocker",
        "Quote entity created but snapshot persistence failed.",
    ),
    (
        "COSTENGINE_PRICING_FAILED",
        "blocker",
        "CostEngine pricing failed during quote creation attempt.",
    ),
    (
        "QUOTE_WITHOUT_OWNER_DECISION",
        "blocker",
        "Quote persisted without owner decision record.",
    ),
    (
        "DUPLICATE_QUOTE_ATTEMPT",
        "blocker",
        "Duplicate quote creation attempt for same workspace.",
    ),
    (
        "UI_TIMEOUT_AFTER_WRITE",
        "warning",
        "UI timeout after backend write — state may be ambiguous.",
    ),
    (
        "PARTIAL_UPDATE_AFTER_CREATION",
        "blocker",
        "Partial update applied after quote creation.",
    ),
    (
        "MISSING_AUDIT_TRAIL",
        "blocker",
        "Audit trail missing for quote creation step.",
    ),
)

RECOVERY_ACTION_SPECS: tuple[tuple[str, str], ...] = (
    ("MARK_QUOTE_DRAFT_REVIEW", "Mark quote as draft/requires review on partial failure"),
    ("REQUIRE_MANUAL_OWNER_REVIEW", "Require manual owner review before retry"),
    ("NO_AUTO_DELETE_FINANCIAL", "Do not auto-delete financial records without explicit policy"),
    ("IMMUTABLE_FAILURE_LOG", "Keep immutable failure/audit log entry"),
    (
        "IDEMPOTENCY_RETRY_GUARD",
        "Block duplicate retry unless idempotency key matches prior attempt",
    ),
)


def build_quote_creation_failure_modes(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
) -> list[IntakeV3QuoteCreationFailureMode]:
    del payload, workspace_preview
    return [
        IntakeV3QuoteCreationFailureMode(
            code=code,
            severity=severity,
            description=description,
        )
        for code, severity, description in FAILURE_MODE_SPECS
    ]


def build_quote_creation_recovery_actions(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
) -> list[IntakeV3QuoteCreationRecoveryAction]:
    del payload, workspace_preview
    return [
        IntakeV3QuoteCreationRecoveryAction(code=code, action=action)
        for code, action in RECOVERY_ACTION_SPECS
    ]


def build_quote_creation_recovery_policy(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
) -> IntakeV3QuoteCreationRecoveryPolicy:
    del bridge
    return IntakeV3QuoteCreationRecoveryPolicy(
        rollback_policy_defined=True,
        recovery_policy_defined=True,
        failure_modes=build_quote_creation_failure_modes(payload, workspace_preview),
        recovery_actions=build_quote_creation_recovery_actions(payload, workspace_preview),
        manual_review_required_on_partial_failure=True,
        next_action=NEXT_ACTION,
    )
