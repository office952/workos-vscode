"""Intake V3 quote creation dry-run contract — simulation only, no quote/order/plan/CostEngine."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from schemas.intake_v3 import (
    IntakeV3FinishVariationSummary,
    IntakeV3PreQuoteReview,
    IntakeV3QuoteCreationDryRun,
    IntakeV3QuoteCreationDryRunPayloadPreview,
    IntakeV3QuoteCreationDryRunSafetyFlags,
    IntakeV3QuoteCreationDryRunSnapshotPreview,
    IntakeV3QuoteReadinessItem,
    IntakeV3QuoteReadinessResult,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
    PricingInputCandidate,
)
from services.intake_v3_pricing_input_adapter import build_pricing_input_candidate
from services.intake_v3_quote_creation_guard_policy_service import (
    POLICY_DISABLED_REASON,
    evaluate_quote_creation_guard_policy,
)
from services.intake_v3_quote_readiness_service import (
    build_prequote_review,
    evaluate_intake_v3_quote_readiness,
)

DryRunStatus = Literal["blocked", "ready_for_future_quote_step", "dry_run_only"]

QUOTE_CREATION_DISABLED_REASON = POLICY_DISABLED_REASON


def _payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _dry_run_id(workspace_id: str, payload_marker: str) -> str:
    return f"DRY-{workspace_id[:8]}-{payload_marker}"


def _item_code(item: IntakeV3QuoteReadinessItem) -> str:
    return item.code


def build_quote_creation_blockers(
    workspace: IntakeV3Workspace,
    *,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    quote_readiness: IntakeV3QuoteReadinessResult | None = None,
    workspace_archived: bool = False,
) -> list[str]:
    """Derive dry-run blockers from quote readiness and workspace safety checks."""
    quote_readiness = quote_readiness or evaluate_intake_v3_quote_readiness(
        workspace,
        workspace_preview,
        workspace_archived=workspace_archived,
    )
    blockers = [_item_code(item) for item in quote_readiness.blockers]

    if workspace_archived:
        if "WORKSPACE_ARCHIVED" not in blockers:
            blockers.insert(0, "WORKSPACE_ARCHIVED")

    preview = workspace_preview
    if preview and preview.created_quote_id is not None:
        blockers.append("QUOTE_ID_ALREADY_PRESENT")

    payload = workspace.model_dump(mode="json")
    if payload.get("created_quote_id"):
        blockers.append("PAYLOAD_QUOTE_ID_PRESENT")

    if quote_readiness.status == "blocked" and not blockers:
        blockers.append("QUOTE_READINESS_BLOCKED")

    if not quote_readiness.checklist and quote_readiness.status == "blocked":
        blockers.append("QUOTE_READINESS_MISSING")

    pricing = preview.pricing_input_candidate if preview else build_pricing_input_candidate(workspace).candidate
    if pricing is None:
        blockers.append("PRICING_INPUT_CANDIDATE_MISSING")
    elif preview and preview.pricing_input_candidate is None:
        blockers.append("PRICING_INPUT_PREVIEW_MISSING")

    if workspace.confirmed_production_model is None:
        blockers.append("UNCONFIRMED_PRODUCTION_MODEL")

    return list(dict.fromkeys(blockers))


def build_quote_creation_warnings(
    workspace: IntakeV3Workspace,
    *,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    quote_readiness: IntakeV3QuoteReadinessResult | None = None,
    workspace_archived: bool = False,
) -> list[str]:
    quote_readiness = quote_readiness or evaluate_intake_v3_quote_readiness(
        workspace,
        workspace_preview,
        workspace_archived=workspace_archived,
    )
    return list(dict.fromkeys(_item_code(item) for item in quote_readiness.warnings))


def validate_intake_v3_quote_creation_preconditions(
    workspace: IntakeV3Workspace,
    *,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    workspace_archived: bool = False,
) -> tuple[list[str], list[str], IntakeV3QuoteReadinessResult]:
    quote_readiness = (
        workspace_preview.quote_readiness
        if workspace_preview and workspace_preview.quote_readiness
        else evaluate_intake_v3_quote_readiness(
            workspace,
            workspace_preview,
            workspace_archived=workspace_archived,
        )
    )
    blockers = build_quote_creation_blockers(
        workspace,
        workspace_preview=workspace_preview,
        quote_readiness=quote_readiness,
        workspace_archived=workspace_archived,
    )
    warnings = build_quote_creation_warnings(
        workspace,
        workspace_preview=workspace_preview,
        quote_readiness=quote_readiness,
        workspace_archived=workspace_archived,
    )
    return blockers, warnings, quote_readiness


def build_quote_creation_payload_preview(
    workspace: IntakeV3Workspace,
    *,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    workspace_id: str | None = None,
    workspace_title: str | None = None,
) -> IntakeV3QuoteCreationDryRunPayloadPreview:
    preview = workspace_preview
    pricing_candidate: PricingInputCandidate | None = None
    if preview and preview.pricing_input_candidate:
        pricing_candidate = preview.pricing_input_candidate
    else:
        pricing_candidate = build_pricing_input_candidate(workspace).candidate

    finish_variation: IntakeV3FinishVariationSummary | None = (
        preview.finish_variation_summary if preview else None
    )
    confirmed = workspace.confirmed_production_model
    finish = workspace.finish_assignment

    dimensions = {
        "width_mm": workspace.client_request.width_mm,
        "height_mm": workspace.client_request.height_mm,
        "depth_mm": workspace.client_request.depth_mm,
    }
    if pricing_candidate:
        dimensions = {
            "width_mm": pricing_candidate.dimensions.width_mm,
            "height_mm": pricing_candidate.dimensions.height_mm,
            "depth_mm": pricing_candidate.dimensions.depth_mm,
        }

    pricing_notes: list[str] = ["Pricing input preview only — no final commercial price."]
    if finish_variation and finish_variation.pricing_preview_notes:
        pricing_notes.extend(finish_variation.pricing_preview_notes[:5])
    elif pricing_candidate and pricing_candidate.finish_variation_notes:
        pricing_notes.extend(pricing_candidate.finish_variation_notes[:5])

    handoff_notes: list[str] = ["Production handoff preview only — no execution tasks created."]
    if finish_variation and finish_variation.handoff_preview_notes:
        handoff_notes.extend(finish_variation.handoff_preview_notes[:5])

    operator_notes: list[str] = []
    if preview and preview.prequote_review:
        operator_notes.append(preview.prequote_review.next_recommended_action or "")
    operator_notes = [note for note in operator_notes if note]

    return IntakeV3QuoteCreationDryRunPayloadPreview(
        workspace_id=workspace_id or (preview.workspace_id if preview else ""),
        template_code=workspace.product_selection.template_code,
        product_label=pricing_candidate.product_label if pricing_candidate else "Litere volumetrice luminoase",
        job_title=workspace_title or workspace.client_request.job_title or workspace.client_request.request_code,
        client_name=workspace.client_request.client_name,
        request_code=workspace.client_request.request_code,
        dimensions=dimensions,
        confirmed_letter_count=confirmed.letter_count if confirmed else 0,
        confirmed_cut_contour_count=confirmed.cut_contour_count if confirmed else 0,
        confirmed_inner_hole_count=confirmed.inner_hole_count if confirmed else 0,
        face_finish_type=finish.face_finish.finish_type if finish else "none",
        return_finish_type=finish.return_finish.finish_type if finish else "none",
        backing_material=finish.backing_finish.material if finish else None,
        finish_variation_count=len(finish_variation.variations) if finish_variation else 0,
        requires_grouped_finish_review=bool(
            finish_variation and finish_variation.has_variations
        ),
        pricing_input_candidate_reference={
            "template_code": pricing_candidate.template_code,
            "support_mode": pricing_candidate.support_mode,
            "adapter_status": "preview_only",
        },
        pricing_notes=pricing_notes,
        handoff_notes=handoff_notes,
        operator_review_notes=operator_notes,
        preview_only=True,
    )


def build_quote_creation_snapshot_preview(
    workspace: IntakeV3Workspace,
    *,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    prequote_review: IntakeV3PreQuoteReview | None = None,
) -> IntakeV3QuoteCreationDryRunSnapshotPreview:
    payload = workspace.model_dump(mode="json")
    marker = _payload_hash(payload)
    raw = workspace.raw_svg_analysis
    confirmed = workspace.confirmed_production_model

    prequote = prequote_review
    if prequote is None and workspace_preview and workspace_preview.prequote_review:
        prequote = workspace_preview.prequote_review
    if prequote is None:
        prequote = build_prequote_review(workspace, workspace_preview)

    pricing_snapshot: dict[str, Any] = {}
    if workspace_preview and workspace_preview.pricing_input_candidate:
        candidate = workspace_preview.pricing_input_candidate
        pricing_snapshot = {
            "template_code": candidate.template_code,
            "support_mode": candidate.support_mode,
            "production_counts": candidate.production_counts.model_dump(mode="json"),
            "finish_summary": candidate.finish_summary.model_dump(mode="json"),
            "finish_variation_count": candidate.finish_variation_count,
            "requires_grouped_finish_review": candidate.requires_grouped_finish_review,
            "preview_only": True,
        }

    finish_assignments_snapshot = {
        "finish_assignment": payload.get("finish_assignment"),
        "letter_group_finish_assignments": payload.get("letter_group_finish_assignments") or [],
        "letter_finish_assignments": payload.get("letter_finish_assignments") or [],
        "finish_assignment_status": payload.get("finish_assignment_status"),
    }

    variation_snapshot: dict[str, Any] = {}
    if workspace_preview and workspace_preview.finish_variation_summary:
        variation_snapshot = workspace_preview.finish_variation_summary.model_dump(mode="json")

    return IntakeV3QuoteCreationDryRunSnapshotPreview(
        workspace_payload_marker=marker,
        raw_svg_analysis_reference={
            "file_name": raw.file_name if raw else "",
            "closed_contour_count": raw.closed_contour_count if raw else 0,
            "warnings_count": len(raw.warnings) if raw else 0,
            "is_production_truth": False,
        },
        confirmed_production_model_snapshot=(
            confirmed.model_dump(mode="json") if confirmed else {}
        ),
        raw_vs_confirmed_boundary_note=(
            "Raw SVG analysis remains separate from confirmed production model snapshot."
        ),
        finish_assignments_snapshot=finish_assignments_snapshot,
        finish_variation_summary_snapshot=variation_snapshot,
        pricing_input_preview_snapshot=pricing_snapshot,
        prequote_review_snapshot={
            "status": prequote.status,
            "blocker_count": len(prequote.blockers),
            "warning_count": len(prequote.warnings),
            "next_recommended_action": prequote.next_recommended_action,
        },
        created_quote_id=None,
        created_order_id=None,
        execution_plan_id=None,
        preview_only=True,
    )


def _derive_dry_run_status(
    blockers: list[str],
    quote_readiness: IntakeV3QuoteReadinessResult,
) -> DryRunStatus:
    if blockers or quote_readiness.status == "blocked":
        return "blocked"
    if quote_readiness.status in {"ready_preview_only", "warning"}:
        return "ready_for_future_quote_step"
    return "dry_run_only"


def _next_action(
    blockers: list[str],
    quote_readiness: IntakeV3QuoteReadinessResult,
) -> str:
    if blockers:
        return quote_readiness.next_recommended_action or "Resolve dry-run blockers before a future quote step."
    return (
        "Dry-run contract complete — real quote creation remains disabled until a dedicated build is implemented."
    )


def build_intake_v3_quote_creation_dry_run(
    payload: dict[str, Any] | IntakeV3Workspace,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    *,
    workspace_id: str | None = None,
    workspace_code: str | None = None,
    workspace_title: str | None = None,
    workspace_archived: bool = False,
) -> IntakeV3QuoteCreationDryRun:
    """Build quote creation dry-run contract — never creates quote or calls quote endpoints."""
    if isinstance(payload, dict):
        workspace = IntakeV3Workspace.model_validate(payload)
    else:
        workspace = payload

    blockers, warnings, quote_readiness = validate_intake_v3_quote_creation_preconditions(
        workspace,
        workspace_preview=workspace_preview,
        workspace_archived=workspace_archived,
    )
    prequote = (
        workspace_preview.prequote_review
        if workspace_preview and workspace_preview.prequote_review
        else build_prequote_review(
            workspace,
            workspace_preview,
            workspace_title=workspace_title,
            workspace_archived=workspace_archived,
        )
    )

    payload_marker = _payload_hash(workspace.model_dump(mode="json"))
    resolved_workspace_id = workspace_id or (workspace_preview.workspace_id if workspace_preview else "")

    payload_preview = build_quote_creation_payload_preview(
        workspace,
        workspace_preview=workspace_preview,
        workspace_id=resolved_workspace_id,
        workspace_title=workspace_title,
    )
    snapshot_preview = build_quote_creation_snapshot_preview(
        workspace,
        workspace_preview=workspace_preview,
        prequote_review=prequote,
    )

    status = _derive_dry_run_status(blockers, quote_readiness)
    would_block = bool(blockers) or quote_readiness.status == "blocked"

    pricing_summary = quote_readiness.pricing_input_summary
    handoff_summary = quote_readiness.handoff_summary
    variation_summary = (
        workspace_preview.finish_variation_summary if workspace_preview else None
    )

    dry_run = IntakeV3QuoteCreationDryRun(
        dry_run_id=_dry_run_id(resolved_workspace_id or "draft", payload_marker),
        dry_run_only=True,
        can_create_quote_now=False,
        quote_creation_disabled_reason=QUOTE_CREATION_DISABLED_REASON,
        readiness_status=quote_readiness.status,
        dry_run_status=status,
        would_block_real_quote_creation=would_block,
        would_use_workspace_id=resolved_workspace_id,
        would_use_workspace_code=workspace_code,
        would_use_template_code=workspace.product_selection.template_code,
        would_use_pricing_input_candidate=workspace_preview.pricing_input_candidate is not None
        if workspace_preview
        else build_pricing_input_candidate(workspace).candidate is not None,
        would_use_finish_variation_notes=bool(
            variation_summary and variation_summary.pricing_preview_notes
        ),
        would_use_production_handoff_preview=bool(
            workspace_preview and workspace_preview.production_handoff_preview
        ),
        would_create_snapshot_preview=True,
        would_require_owner_confirmation=quote_readiness.status != "ready_preview_only",
        blockers=blockers,
        warnings=warnings,
        payload_preview=payload_preview,
        snapshot_preview=snapshot_preview,
        pricing_input_preview_summary=pricing_summary,
        finish_variation_summary=variation_summary,
        handoff_preview_summary=handoff_summary,
        safety_flags=IntakeV3QuoteCreationDryRunSafetyFlags(),
        next_action=_next_action(blockers, quote_readiness),
    )
    dry_run.guard_policy = evaluate_quote_creation_guard_policy(
        workspace,
        workspace_preview,
        dry_run,
        workspace_archived=workspace_archived,
    )
    return dry_run


def is_quote_creation_dry_run_available(
    workspace: IntakeV3Workspace,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    *,
    workspace_archived: bool = False,
) -> bool:
    """True when workspace has enough structure to attempt a dry-run (may still be blocked)."""
    if workspace_archived:
        return False
    preview = workspace_preview
    if preview and preview.quote_readiness:
        return True
    return workspace.client_request.request_code.strip() != "" or (
        workspace.confirmed_production_model is not None
    )
