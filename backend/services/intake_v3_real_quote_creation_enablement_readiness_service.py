"""Intake V3 real quote creation enablement readiness — composes policy contracts, no quote creation."""

from __future__ import annotations

from typing import Any, Literal

from schemas.intake_v3 import (
    IntakeV3CommercialQuoteBridgePreview,
    IntakeV3OwnerDecisionRecordPolicy,
    IntakeV3QuoteCreationAntiDuplicatePolicy,
    IntakeV3QuoteCreationEnablementPolicy,
    IntakeV3QuoteCreationFinalBlockerCheck,
    IntakeV3QuoteCreationRecoveryPolicy,
    IntakeV3QuoteSnapshotPolicy,
    IntakeV3RealQuoteCreationEnablementReadiness,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
)
from services.intake_v3_owner_decision_record_policy_service import (
    build_owner_decision_record_policy,
)
from services.intake_v3_quote_creation_anti_duplicate_policy_service import (
    build_quote_creation_anti_duplicate_policy,
)
from services.intake_v3_quote_creation_recovery_policy_service import (
    build_quote_creation_recovery_policy,
)
from services.intake_v3_quote_snapshot_policy_service import build_quote_snapshot_policy

ReadinessStatus = Literal[
    "blocked_owner_decision_missing",
    "blocked_workspace_archived",
    "blocked",
]

NEXT_ACTION = (
    "Implement owner decision capture and snapshot persistence before enabling quote creation."
)


def _resolve_workspace(
    payload: dict[str, Any] | IntakeV3Workspace | None,
) -> IntakeV3Workspace | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return IntakeV3Workspace.model_validate(payload)
    return payload


def build_real_quote_creation_enablement_blockers(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
    enablement_policy: IntakeV3QuoteCreationEnablementPolicy | None = None,
    *,
    owner_decision: IntakeV3OwnerDecisionRecordPolicy | None = None,
    final_blocker_check: IntakeV3QuoteCreationFinalBlockerCheck | None = None,
    workspace_archived: bool = False,
) -> list[str]:
    blockers: list[str] = []
    if owner_decision and not owner_decision.owner_decision_record_present:
        blockers.extend(owner_decision.blockers)
    if enablement_policy:
        blockers.extend(item.code for item in enablement_policy.blockers[:5])
    if final_blocker_check:
        for code in final_blocker_check.blockers:
            if code not in blockers:
                blockers.append(code)
    if bridge and bridge.bridge_status == "disabled_by_policy":
        if "BRIDGE_DISABLED_BY_POLICY" not in blockers:
            blockers.append("BRIDGE_DISABLED_BY_POLICY")
    if workspace_archived and "WORKSPACE_ARCHIVED" not in blockers:
        blockers.append("WORKSPACE_ARCHIVED")
    blockers.append("REAL_QUOTE_CREATION_NOT_ENABLED")
    blockers.append("SNAPSHOT_PERSISTENCE_NOT_EXECUTED")
    return list(dict.fromkeys(blockers))


def build_real_quote_creation_enablement_readiness(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
    enablement_policy: IntakeV3QuoteCreationEnablementPolicy | None = None,
    final_blocker_check: IntakeV3QuoteCreationFinalBlockerCheck | None = None,
    *,
    owner_decision: IntakeV3OwnerDecisionRecordPolicy | None = None,
    snapshot_policy: IntakeV3QuoteSnapshotPolicy | None = None,
    anti_duplicate_policy: IntakeV3QuoteCreationAntiDuplicatePolicy | None = None,
    recovery_policy: IntakeV3QuoteCreationRecoveryPolicy | None = None,
    workspace_archived: bool = False,
) -> IntakeV3RealQuoteCreationEnablementReadiness:
    owner_decision = owner_decision or build_owner_decision_record_policy(
        payload,
        workspace_preview,
        enablement_policy,
        bridge,
        workspace_archived=workspace_archived,
    )
    snapshot_policy = snapshot_policy or build_quote_snapshot_policy(
        payload,
        workspace_preview,
        bridge,
    )
    anti_duplicate_policy = anti_duplicate_policy or build_quote_creation_anti_duplicate_policy(
        payload,
        workspace_preview,
        bridge,
    )
    recovery_policy = recovery_policy or build_quote_creation_recovery_policy(
        payload,
        workspace_preview,
        bridge,
    )
    status: ReadinessStatus = "blocked_owner_decision_missing"
    if workspace_archived:
        status = "blocked_workspace_archived"
    blockers = build_real_quote_creation_enablement_blockers(
        payload,
        workspace_preview,
        bridge,
        enablement_policy,
        owner_decision=owner_decision,
        final_blocker_check=final_blocker_check,
        workspace_archived=workspace_archived,
    )
    warnings: list[str] = []
    if enablement_policy:
        warnings.extend(item.code for item in enablement_policy.warnings[:3])
    return IntakeV3RealQuoteCreationEnablementReadiness(
        real_quote_creation_enablement_readiness_status=status,
        can_create_quote_now=False,
        can_enable_real_quote_creation=False,
        owner_decision_record_required=True,
        owner_decision_record_present=False,
        snapshot_policy_defined=snapshot_policy.snapshot_policy_defined,
        snapshot_persistence_executed=False,
        anti_duplicate_policy_defined=anti_duplicate_policy.anti_duplicate_policy_defined,
        rollback_policy_defined=recovery_policy.rollback_policy_defined,
        owner_decision_record_status=owner_decision.owner_decision_status,
        snapshot_policy_status="defined_not_executed",
        anti_duplicate_policy_status="defined",
        rollback_policy_status="defined",
        blockers=blockers,
        warnings=warnings,
        next_action=NEXT_ACTION,
    )


def evaluate_real_quote_creation_enablement_readiness(
    payload: dict[str, Any] | IntakeV3Workspace,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
    enablement_policy: IntakeV3QuoteCreationEnablementPolicy | None = None,
    final_blocker_check: IntakeV3QuoteCreationFinalBlockerCheck | None = None,
    *,
    workspace_archived: bool = False,
) -> dict[str, Any]:
    """Evaluate full readiness bundle — policies + readiness contract."""
    owner_decision = build_owner_decision_record_policy(
        payload,
        workspace_preview,
        enablement_policy,
        bridge,
        workspace_archived=workspace_archived,
    )
    snapshot_policy = build_quote_snapshot_policy(payload, workspace_preview, bridge)
    anti_duplicate_policy = build_quote_creation_anti_duplicate_policy(
        payload,
        workspace_preview,
        bridge,
    )
    recovery_policy = build_quote_creation_recovery_policy(
        payload,
        workspace_preview,
        bridge,
    )
    readiness = build_real_quote_creation_enablement_readiness(
        payload,
        workspace_preview,
        bridge,
        enablement_policy,
        final_blocker_check,
        owner_decision=owner_decision,
        snapshot_policy=snapshot_policy,
        anti_duplicate_policy=anti_duplicate_policy,
        recovery_policy=recovery_policy,
        workspace_archived=workspace_archived,
    )
    return {
        "owner_decision_record_policy": owner_decision,
        "snapshot_policy": snapshot_policy,
        "anti_duplicate_policy": anti_duplicate_policy,
        "recovery_policy": recovery_policy,
        "readiness": readiness,
    }


def is_real_quote_creation_enablement_readiness_available(
    workspace: IntakeV3Workspace,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    *,
    workspace_archived: bool = False,
) -> bool:
    from services.intake_v3_quote_creation_final_blocker_service import (
        is_quote_creation_enablement_available,
    )

    return is_quote_creation_enablement_available(
        workspace,
        workspace_preview,
        workspace_archived=workspace_archived,
    )


def real_quote_creation_enablement_readiness_status_label(
    *,
    workspace_archived: bool = False,
) -> str:
    if workspace_archived:
        return "blocked_workspace_archived"
    return "blocked_owner_decision_missing"
