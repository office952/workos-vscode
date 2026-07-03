"""Intake V3 anti-duplicate quote creation policy — idempotency contract preview only."""

from __future__ import annotations

from typing import Any

from schemas.intake_v3 import (
    IntakeV3CommercialQuoteBridgePreview,
    IntakeV3QuoteCreationAntiDuplicatePolicy,
    IntakeV3QuoteCreationDuplicateKey,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
)
from services.intake_v3_quote_snapshot_policy_service import build_quote_snapshot_hash_marker

NEXT_ACTION = (
    "Real quote creation must check for existing quote linked to this Intake V3 workspace before creating another."
)

DUPLICATE_KEY_SPECS: tuple[tuple[str, str], ...] = (
    ("source_module", "intake_v3"),
    ("source_workspace_id", "Intake V3 workspace primary key"),
    ("workspace_payload_hash_or_marker", "Payload hash/marker at creation attempt"),
    ("owner_decision_record_id_or_marker", "Owner decision record id or marker"),
    ("snapshot_policy_version", "Snapshot policy version at creation attempt"),
)


def _resolve_workspace(
    payload: dict[str, Any] | IntakeV3Workspace | None,
) -> IntakeV3Workspace | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return IntakeV3Workspace.model_validate(payload)
    return payload


def build_quote_creation_duplicate_keys(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
) -> list[IntakeV3QuoteCreationDuplicateKey]:
    workspace = _resolve_workspace(payload)
    workspace_id = workspace_preview.workspace_id if workspace_preview else ""
    marker = build_quote_snapshot_hash_marker(payload, workspace_preview)
    return [
        IntakeV3QuoteCreationDuplicateKey(
            key_code=code,
            description=description,
            preview_value=(
                "intake_v3"
                if code == "source_module"
                else workspace_id
                if code == "source_workspace_id"
                else marker
                if code == "workspace_payload_hash_or_marker"
                else "not_captured"
                if code == "owner_decision_record_id_or_marker"
                else "intake_v3_quote_snapshot_v1"
            ),
        )
        for code, description in DUPLICATE_KEY_SPECS
    ]


def build_quote_creation_duplicate_blockers(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
) -> list[str]:
    del payload, workspace_preview
    return [
        "DUPLICATE_QUOTE_CHECK_NOT_EXECUTED",
        "EXISTING_QUOTE_LINK_UNKNOWN",
    ]


def build_quote_creation_anti_duplicate_policy(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
) -> IntakeV3QuoteCreationAntiDuplicatePolicy:
    del bridge
    return IntakeV3QuoteCreationAntiDuplicatePolicy(
        anti_duplicate_policy_defined=True,
        duplicate_check_executed=False,
        quote_creation_idempotency_required=True,
        duplicate_key_strategy=build_quote_creation_duplicate_keys(payload, workspace_preview),
        would_block_if_existing_quote_found=True,
        blockers=build_quote_creation_duplicate_blockers(payload, workspace_preview),
        next_action=NEXT_ACTION,
    )
