"""Intake V3 quote snapshot policy — defines frozen sections, no persistence in this build."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from schemas.intake_v3 import (
    IntakeV3CommercialQuoteBridgePreview,
    IntakeV3QuoteSnapshotIntegrityRule,
    IntakeV3QuoteSnapshotPersistencePlanItem,
    IntakeV3QuoteSnapshotPolicy,
    IntakeV3QuoteSnapshotRequiredSection,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
)

SNAPSHOT_POLICY_VERSION = "intake_v3_quote_snapshot_v1"
NEXT_ACTION = "Persist immutable quote snapshot only in the real quote creation build."

REQUIRED_SECTION_SPECS: tuple[tuple[str, str], ...] = (
    ("workspace_identity_snapshot", "Workspace id, code, title, template"),
    ("workspace_payload_snapshot", "Full Intake V3 workspace payload at quote creation time"),
    ("controlled_fields_snapshot", "Controlled field editor state at quote creation time"),
    ("raw_svg_analysis_reference", "Reference to raw SVG analysis — not production truth"),
    ("confirmed_production_model_snapshot", "Operator-confirmed production model — production truth"),
    ("finish_assignment_snapshot", "Global and per-letter finish assignments"),
    ("finish_variation_summary_snapshot", "Finish variation summary when variations exist"),
    ("pricing_input_candidate_snapshot", "Pricing input candidate reference — preview only until CostEngine"),
    ("prequote_review_snapshot", "Pre-quote review summary at creation time"),
    ("quote_readiness_snapshot", "Quote readiness gate result at creation time"),
    ("dry_run_snapshot", "Quote creation dry-run contract marker"),
    ("guard_policy_snapshot", "Quote creation guard policy at creation time"),
    ("commercial_quote_bridge_snapshot", "Commercial quote bridge mapping at creation time"),
    ("owner_decision_record_snapshot", "Owner decision record binding at creation time"),
    ("final_blocker_check_snapshot", "Final blocker check result at creation time"),
)

INTEGRITY_RULE_SPECS: tuple[tuple[str, str], ...] = (
    (
        "RAW_NOT_PRODUCTION_TRUTH",
        "Raw SVG analysis is diagnostic only — not production truth for quote creation.",
    ),
    (
        "CONFIRMED_MODEL_PRODUCTION_TRUTH",
        "Confirmed production model is production truth for letter counts and contours.",
    ),
    (
        "HOLES_NOT_LETTERS",
        "Inner holes must not be counted as letters in snapshot or quote input.",
    ),
    (
        "FREEZE_OWNER_APPROVED_STATE",
        "Quote snapshot must freeze owner-approved payload state at creation time.",
    ),
    (
        "NO_SILENT_RECALCULATION",
        "Quote snapshot must not be recalculated silently after quote creation.",
    ),
    (
        "EXPLICIT_REPRICE_AUDIT",
        "Any later quote reprice must be explicit and audited.",
    ),
    (
        "IDEMPOTENT_CREATION",
        "Quote creation must be idempotent and anti-duplicate guarded.",
    ),
)


def _resolve_workspace(
    payload: dict[str, Any] | IntakeV3Workspace | None,
) -> IntakeV3Workspace | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return IntakeV3Workspace.model_validate(payload)
    return payload


def build_quote_snapshot_required_sections(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
) -> list[IntakeV3QuoteSnapshotRequiredSection]:
    del payload, bridge
    sections: list[IntakeV3QuoteSnapshotRequiredSection] = []
    for code, description in REQUIRED_SECTION_SPECS:
        available = True
        if code == "finish_variation_summary_snapshot" and workspace_preview:
            available = workspace_preview.finish_variation_summary is not None or (
                workspace_preview.finish_summary.finish_variations_present
                if workspace_preview.finish_summary
                else False
            )
        sections.append(
            IntakeV3QuoteSnapshotRequiredSection(
                section_code=code,
                description=description,
                required=True,
                available_in_preview=available,
            )
        )
    return sections


def build_quote_snapshot_integrity_rules(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
) -> list[IntakeV3QuoteSnapshotIntegrityRule]:
    del payload, workspace_preview
    return [
        IntakeV3QuoteSnapshotIntegrityRule(code=code, rule=rule)
        for code, rule in INTEGRITY_RULE_SPECS
    ]


def build_quote_snapshot_persistence_plan(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
) -> list[IntakeV3QuoteSnapshotPersistencePlanItem]:
    del payload, workspace_preview
    return [
        IntakeV3QuoteSnapshotPersistencePlanItem(
            target="quote_snapshot_store",
            action="persist_immutable_bundle",
            executed=False,
            note="No snapshot rows persisted in this foundation build.",
        ),
        IntakeV3QuoteSnapshotPersistencePlanItem(
            target="audit_log",
            action="append_snapshot_creation_event",
            executed=False,
            note="Audit event deferred to real quote creation build.",
        ),
    ]


def build_quote_snapshot_hash_marker(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
) -> str:
    workspace = _resolve_workspace(payload)
    workspace_id = workspace_preview.workspace_id if workspace_preview else ""
    if not workspace_id and workspace:
        workspace_id = workspace.client_request.request_code
    marker_payload = {
        "policy_version": SNAPSHOT_POLICY_VERSION,
        "workspace_id": workspace_id,
        "preview_only": True,
    }
    if workspace:
        marker_payload["template_code"] = workspace.product_selection.template_code
    encoded = json.dumps(marker_payload, sort_keys=True, default=str)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"preview-only:{digest}"


def build_quote_snapshot_policy(
    payload: dict[str, Any] | IntakeV3Workspace | None = None,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    bridge: IntakeV3CommercialQuoteBridgePreview | None = None,
) -> IntakeV3QuoteSnapshotPolicy:
    return IntakeV3QuoteSnapshotPolicy(
        snapshot_policy_defined=True,
        snapshot_persistence_executed=False,
        snapshot_policy_version=SNAPSHOT_POLICY_VERSION,
        required_sections=build_quote_snapshot_required_sections(
            payload,
            workspace_preview,
            bridge,
        ),
        integrity_rules=build_quote_snapshot_integrity_rules(payload, workspace_preview),
        persistence_plan=build_quote_snapshot_persistence_plan(payload, workspace_preview),
        hash_marker_preview=build_quote_snapshot_hash_marker(payload, workspace_preview),
        next_action=NEXT_ACTION,
    )
