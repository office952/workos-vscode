"""Intake V3 owner decision record policy — contract preview only, no capture or DB writes."""

from __future__ import annotations

from typing import Any, Literal

from schemas.intake_v3 import (
    IntakeV3CommercialQuoteBridgePreview,
    IntakeV3OwnerDecisionAuditRequirement,
    IntakeV3OwnerDecisionRecordPolicy,
    IntakeV3OwnerDecisionRequiredField,
    IntakeV3QuoteCreationEnablementPolicy,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
)

OwnerDecisionStatus = Literal["required_not_present"]

DECISION_SCOPE = "intake_v3_real_quote_creation"
NEXT_ACTION = (
    "Capture explicit owner approval in a dedicated enablement build before quote creation can be activated."
)

REQUIRED_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("owner_user_id", "string", "Owner user identifier — required for audit trail"),
    ("owner_display_name", "string", "Human-readable owner name at decision time"),
    (
        "decision_status",
        "enum:approved|rejected|revoked",
        "Explicit owner decision outcome",
    ),
    ("decision_timestamp", "datetime", "UTC timestamp of owner decision"),
    ("decision_reason", "string", "Owner rationale for approval or rejection"),
    ("approved_workspace_id", "string", "Intake V3 workspace id covered by decision"),
    (
        "approved_bridge_preview_hash_or_marker",
        "string",
        "Hash/marker of commercial bridge preview at approval time",
    ),
    (
        "approved_snapshot_policy_version",
        "string",
        "Snapshot policy version approved by owner",
    ),
    (
        "approval_source",
        "enum:UI|admin_action|migration|test_fixture",
        "How the decision was captured",
    ),
)

AUDIT_REQUIREMENTS: tuple[tuple[str, str], ...] = (
    ("IMMUTABLE_AUDIT_LOG", "Owner decision must be append-only with audit log entry"),
    ("DECISION_SCOPE_MATCH", "Decision scope must match intake_v3_real_quote_creation"),
    ("WORKSPACE_BINDING", "Decision must bind to a specific workspace id"),
    ("BRIDGE_MARKER_BINDING", "Decision must reference bridge preview marker at approval time"),
    ("NO_SILENT_OVERRIDE", "Later quote creation must not proceed without valid decision record"),
)


def _resolve_workspace(
    payload: dict[str, Any] | IntakeV3Workspace | None,
) -> IntakeV3Workspace | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return IntakeV3Workspace.model_validate(payload)
    return payload


def build_owner_decision_required_fields(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
) -> list[IntakeV3OwnerDecisionRequiredField]:
    del payload, workspace_preview
    return [
        IntakeV3OwnerDecisionRequiredField(
            field_code=code,
            field_type=field_type,
            description=description,
            required=True,
            present_in_build=False,
        )
        for code, field_type, description in REQUIRED_FIELD_SPECS
    ]


def build_owner_decision_audit_requirements(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
) -> list[IntakeV3OwnerDecisionAuditRequirement]:
    del payload, workspace_preview
    return [
        IntakeV3OwnerDecisionAuditRequirement(code=code, requirement=text)
        for code, text in AUDIT_REQUIREMENTS
    ]


def build_owner_decision_absence_blockers(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
) -> list[str]:
    del payload, workspace_preview
    return [
        "OWNER_DECISION_RECORD_MISSING",
        "OWNER_DECISION_NOT_CAPTURED",
    ]


def build_owner_decision_record_policy(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    enablement_policy: IntakeV3QuoteCreationEnablementPolicy | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
    *,
    workspace_archived: bool = False,
) -> IntakeV3OwnerDecisionRecordPolicy:
    del enablement_policy, bridge
    required_fields = build_owner_decision_required_fields(payload, workspace_preview)
    missing_fields = [field.field_code for field in required_fields]
    blockers = build_owner_decision_absence_blockers(payload, workspace_preview)
    if workspace_archived:
        blockers.append("WORKSPACE_ARCHIVED")
    return IntakeV3OwnerDecisionRecordPolicy(
        owner_decision_record_required=True,
        owner_decision_record_present=False,
        owner_decision_status="required_not_present",
        can_enable_real_quote_creation=False,
        decision_scope=DECISION_SCOPE,
        required_fields=required_fields,
        audit_requirements=build_owner_decision_audit_requirements(payload, workspace_preview),
        missing_fields=missing_fields,
        blockers=blockers,
        next_action=NEXT_ACTION,
    )
