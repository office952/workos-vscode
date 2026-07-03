"""Intake V3 commercial quote bridge — mapping preview only, no quote/CostEngine calls."""

from __future__ import annotations

from typing import Any, Literal

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE
from schemas.intake_v3 import (
    IntakeV3CommercialQuoteBridgePreview,
    IntakeV3CommercialQuoteBridgeSafetyFlags,
    IntakeV3CommercialQuoteCandidatePayload,
    IntakeV3CommercialQuoteMappingItem,
    IntakeV3CommercialQuoteMissingField,
    IntakeV3CommercialQuoteSnapshotPlan,
    IntakeV3PreQuoteReview,
    IntakeV3QuoteCreationDryRun,
    IntakeV3QuoteCreationGuardPolicy,
    IntakeV3Workspace,
    IntakeV3WorkspacePreview,
)
from services.intake_v3_pricing_input_adapter import build_pricing_input_candidate
from services.intake_v3_quote_creation_dry_run_service import build_intake_v3_quote_creation_dry_run
from services.intake_v3_quote_creation_guard_policy_service import (
    POLICY_CODE,
    evaluate_quote_creation_guard_policy,
)
from services.intake_v3_quote_readiness_service import (
    build_prequote_review,
    evaluate_intake_v3_quote_readiness,
)
from services.intake_v3_workspace_field_editor_service import resolve_workspace_support_context

BridgeStatus = Literal["disabled_by_policy", "blocked_by_missing_policy"]
MappingStatus = Literal[
    "mapped",
    "missing",
    "blocked_by_policy",
    "preview_only",
    "needs_owner_decision",
]

NEXT_ACTION = (
    "Review bridge mapping. Real quote creation requires owner-approved enablement build."
)

PREVIEW_ONLY_FIELD_CODES = frozenset(
    {
        "pricing_input_candidate",
        "pricing_input_preview",
        "finish_variation_summary",
        "production_handoff_preview",
        "prequote_review",
        "guard_policy",
        "dry_run_contract",
    }
)

BLOCKED_FIELD_CODES = frozenset(
    {
        "commercial_quote_id",
        "quote_id",
        "cost_engine_result",
        "final_total_price",
        "final_commercial_price",
    }
)


def _resolve_workspace(
    payload: dict[str, Any] | IntakeV3Workspace,
) -> IntakeV3Workspace:
    if isinstance(payload, dict):
        return IntakeV3Workspace.model_validate(payload)
    return payload


def build_commercial_quote_bridge_policy_lock(
    guard_policy: IntakeV3QuoteCreationGuardPolicy | None = None,
) -> dict[str, Any]:
    if guard_policy is None:
        return {
            "can_create_commercial_quote": False,
            "disabled_by_policy": False,
            "owner_confirmation_required": True,
            "policy_code": "",
            "policy_missing": True,
        }
    return {
        "can_create_commercial_quote": False,
        "disabled_by_policy": guard_policy.disabled_by_policy,
        "owner_confirmation_required": guard_policy.owner_confirmation_required,
        "policy_code": guard_policy.policy_code,
        "policy_missing": False,
    }


def build_commercial_quote_candidate_payload(
    payload: dict[str, Any] | IntakeV3Workspace,
    *,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    workspace_id: str | None = None,
    workspace_code: str | None = None,
    workspace_title: str | None = None,
    guard_policy: IntakeV3QuoteCreationGuardPolicy | None = None,
) -> IntakeV3CommercialQuoteCandidatePayload:
    workspace = _resolve_workspace(payload)
    preview = workspace_preview
    req = workspace.client_request
    confirmed = workspace.confirmed_production_model
    raw = workspace.raw_svg_analysis
    finish = workspace.finish_assignment
    support = workspace.support_context or resolve_workspace_support_context(workspace)

    pricing_candidate = (
        preview.pricing_input_candidate
        if preview and preview.pricing_input_candidate
        else build_pricing_input_candidate(workspace).candidate
    )
    variation = preview.finish_variation_summary if preview else None
    handoff = preview.production_handoff_preview if preview else None

    dimensions = {
        "width_mm": req.width_mm,
        "height_mm": req.height_mm,
        "depth_mm": req.depth_mm,
    }
    if pricing_candidate:
        dimensions = {
            "width_mm": pricing_candidate.dimensions.width_mm,
            "height_mm": pricing_candidate.dimensions.height_mm,
            "depth_mm": pricing_candidate.dimensions.depth_mm,
        }

    pricing_notes = ["Pricing input preview only — no final commercial price."]
    if variation and variation.pricing_preview_notes:
        pricing_notes.extend(variation.pricing_preview_notes[:5])
    elif pricing_candidate and pricing_candidate.finish_variation_notes:
        pricing_notes.extend(pricing_candidate.finish_variation_notes[:5])

    material_notes: list[str] = []
    operation_notes: list[str] = []
    if variation and variation.material_notes:
        material_notes.extend(note.note for note in variation.material_notes[:5] if note.note)
    if variation and variation.operation_notes:
        operation_notes.extend(note.note for note in variation.operation_notes[:5] if note.note)
    if handoff:
        operation_notes.append("Production handoff preview only — non_executable=true.")
    if variation and variation.handoff_preview_notes:
        operation_notes.extend(variation.handoff_preview_notes[:5])

    dry_run_payload = dry_run.payload_preview if dry_run else None
    product_label = (
        dry_run_payload.product_label
        if dry_run_payload and dry_run_payload.product_label
        else (pricing_candidate.product_label if pricing_candidate else "Litere volumetrice luminoase")
    )

    policy_lock = build_commercial_quote_bridge_policy_lock(guard_policy)

    return IntakeV3CommercialQuoteCandidatePayload(
        workspace_id=workspace_id or (preview.workspace_id if preview else ""),
        workspace_code=workspace_code or (dry_run.would_use_workspace_code if dry_run else None),
        workspace_title=workspace_title or req.job_title or req.request_code,
        source_module="intake_v3",
        source_status=preview.quote_readiness.status if preview and preview.quote_readiness else "unknown",
        template_code=workspace.product_selection.template_code,
        client_id=req.client_id,
        client_name=req.client_name,
        request_code=req.request_code,
        job_title=req.job_title,
        product_label=product_label,
        dimensions=dimensions,
        illuminated=support.illuminated if support else None,
        support_mode=getattr(support, "shared_support", None),
        confirmed_letter_count=confirmed.letter_count if confirmed else 0,
        confirmed_cut_contour_count=confirmed.cut_contour_count if confirmed else 0,
        confirmed_inner_hole_count=confirmed.inner_hole_count if confirmed else 0,
        raw_svg_analysis_reference={
            "file_name": raw.file_name if raw else "",
            "closed_contour_count": raw.closed_contour_count if raw else 0,
            "is_production_truth": False,
        },
        confirmed_production_model_reference={
            "confirmation_status": confirmed.confirmation_status if confirmed else "missing",
            "letter_count": confirmed.letter_count if confirmed else 0,
        },
        finish_assignment_summary={
            "face_finish_type": finish.face_finish.finish_type if finish else "none",
            "return_finish_type": finish.return_finish.finish_type if finish else "none",
            "backing_material": finish.backing_finish.material if finish and finish.backing_finish else None,
            "finish_assignment_status": workspace.finish_assignment_status,
            "letter_group_count": len(workspace.letter_group_finish_assignments or []),
            "letter_override_count": len(workspace.letter_finish_assignments or []),
        },
        finish_variation_summary_reference=(
            variation.model_dump(mode="json") if variation else {}
        ),
        material_notes=material_notes,
        operation_notes=operation_notes,
        pricing_input_candidate_reference={
            "template_code": pricing_candidate.template_code if pricing_candidate else PILOT_TEMPLATE_CODE,
            "support_mode": pricing_candidate.support_mode if pricing_candidate else None,
            "adapter_status": "preview_only",
        },
        pricing_notes=pricing_notes,
        requires_grouped_finish_review=bool(
            variation and variation.has_variations
        ),
        production_handoff_preview_reference={
            "preview_only": True,
            "non_executable": handoff.non_executable if handoff else True,
            "task_seed_count": len(handoff.task_seeds) if handoff else 0,
        },
        handoff_non_executable=True,
        guard_policy_status=policy_lock.get("policy_code") or "disabled_by_default",
        owner_confirmation_required=True,
        dry_run_only=True,
        real_quote_disabled=True,
        preview_only=True,
    )


def _mapping_item(
    *,
    source_field: str,
    target_quote_field: str,
    status: MappingStatus,
    message: str,
) -> IntakeV3CommercialQuoteMappingItem:
    return IntakeV3CommercialQuoteMappingItem(
        source_field=source_field,
        target_quote_field=target_quote_field,
        status=status,
        message=message,
    )


def validate_commercial_quote_bridge_mapping(
    payload: dict[str, Any] | IntakeV3Workspace,
    *,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    candidate: IntakeV3CommercialQuoteCandidatePayload | None = None,
    guard_policy: IntakeV3QuoteCreationGuardPolicy | None = None,
) -> list[IntakeV3CommercialQuoteMappingItem]:
    workspace = _resolve_workspace(payload)
    preview = workspace_preview
    candidate = candidate or build_commercial_quote_candidate_payload(
        workspace,
        workspace_preview=preview,
        dry_run=dry_run,
        guard_policy=guard_policy,
    )
    items: list[IntakeV3CommercialQuoteMappingItem] = []

    ws_id = candidate.workspace_id
    items.append(
        _mapping_item(
            source_field="workspace.id",
            target_quote_field="quote.source_workspace_id",
            status="mapped" if ws_id else "missing",
            message="Intake V3 workspace id maps to quote source linkage." if ws_id else "Workspace id missing.",
        )
    )
    items.append(
        _mapping_item(
            source_field="template_code",
            target_quote_field="quote.product_template_code",
            status="mapped" if candidate.template_code else "missing",
            message=f"Template {candidate.template_code} maps to product template code.",
        )
    )
    dims_ok = bool(candidate.dimensions.get("width_mm")) and bool(candidate.dimensions.get("height_mm"))
    items.append(
        _mapping_item(
            source_field="dimensions.width/height",
            target_quote_field="quote.dimensions",
            status="mapped" if dims_ok else "missing",
            message="Dimensions map to quote sizing fields." if dims_ok else "Dimensions missing or incomplete.",
        )
    )
    items.append(
        _mapping_item(
            source_field="client_request.client_id",
            target_quote_field="quote.customer_id",
            status="mapped" if candidate.client_id else "missing",
            message="Client id present." if candidate.client_id else "Client/customer id not present in workspace.",
        )
    )
    items.append(
        _mapping_item(
            source_field="confirmed_production_model",
            target_quote_field="quote.production_model_snapshot",
            status="mapped" if candidate.confirmed_letter_count > 0 else "missing",
            message="Confirmed production model counts available for snapshot handoff.",
        )
    )
    items.append(
        _mapping_item(
            source_field="pricing_input_candidate",
            target_quote_field="quote.quote_input / quote.pricing_input",
            status="preview_only" if candidate.pricing_input_candidate_reference else "missing",
            message="Pricing input candidate is preview-only — CostEngine not invoked here.",
        )
    )
    items.append(
        _mapping_item(
            source_field="finish_variation_summary",
            target_quote_field="quote.finish_snapshot",
            status="preview_only" if candidate.finish_variation_summary_reference else "missing",
            message="Finish variation summary maps as preview snapshot reference.",
        )
    )
    items.append(
        _mapping_item(
            source_field="production_handoff_preview",
            target_quote_field="quote.handoff_preview",
            status="preview_only" if candidate.production_handoff_preview_reference else "missing",
            message="Production handoff preview is non-executable reference only.",
        )
    )
    items.append(
        _mapping_item(
            source_field="final_total_price",
            target_quote_field="quote.total_price",
            status="missing",
            message="Final commercial price is not calculated in Intake V3 bridge preview.",
        )
    )
    items.append(
        _mapping_item(
            source_field="commercial_quote_id",
            target_quote_field="quote.id",
            status="blocked_by_policy",
            message="Commercial quote id is blocked — quote creation disabled by policy.",
        )
    )
    items.append(
        _mapping_item(
            source_field="cost_engine_result",
            target_quote_field="quote.cost_breakdown",
            status="blocked_by_policy",
            message="CostEngine is not called — result blocked by policy and build boundary.",
        )
    )
    if guard_policy is None:
        items.append(
            _mapping_item(
                source_field="guard_policy",
                target_quote_field="quote.creation_policy",
                status="needs_owner_decision",
                message="Guard policy missing — bridge remains conservative.",
            )
        )
    else:
        items.append(
            _mapping_item(
                source_field="guard_policy.policy_code",
                target_quote_field="quote.creation_policy",
                status="blocked_by_policy",
                message=f"Policy {guard_policy.policy_code} blocks real quote creation.",
            )
        )
    if dry_run:
        items.append(
            _mapping_item(
                source_field="dry_run.payload_preview",
                target_quote_field="quote.dry_run_candidate",
                status="preview_only",
                message="Dry-run payload preview informs future quote bridge only.",
            )
        )
    return items


def build_commercial_quote_bridge_missing_fields(
    payload: dict[str, Any] | IntakeV3Workspace,
    *,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    candidate: IntakeV3CommercialQuoteCandidatePayload | None = None,
) -> list[IntakeV3CommercialQuoteMissingField]:
    workspace = _resolve_workspace(payload)
    candidate = candidate or build_commercial_quote_candidate_payload(
        workspace,
        workspace_preview=workspace_preview,
    )
    missing: list[IntakeV3CommercialQuoteMissingField] = []

    if not candidate.client_id:
        missing.append(
            IntakeV3CommercialQuoteMissingField(
                field_code="client_customer_id",
                label="Client / customer id",
                message="Workspace has no persisted client_id for commercial quote linkage.",
                severity="info",
            )
        )
    if not candidate.dimensions.get("width_mm") or not candidate.dimensions.get("height_mm"):
        missing.append(
            IntakeV3CommercialQuoteMissingField(
                field_code="dimensions",
                label="Dimensions",
                message="Width/height not fully present for quote dimensions mapping.",
                severity="blocker",
            )
        )
    missing.append(
        IntakeV3CommercialQuoteMissingField(
            field_code="final_commercial_price",
            label="Final commercial price",
            message="Not calculated — bridge preview does not invoke CostEngine or pricing formulas.",
            severity="info",
        )
    )
    missing.append(
        IntakeV3CommercialQuoteMissingField(
            field_code="owner_quote_approval",
            label="Owner quote approval",
            message="Owner approval required before enabling commercial quote creation.",
            severity="info",
        )
    )
    missing.append(
        IntakeV3CommercialQuoteMissingField(
            field_code="snapshot_persistence_decision",
            label="Snapshot persistence decision",
            message="Real quote snapshot persistence target not defined in this foundation build.",
            severity="info",
        )
    )
    req = workspace.client_request
    if not req.delivery_type:
        missing.append(
            IntakeV3CommercialQuoteMissingField(
                field_code="commercial_terms_delivery",
                label="Delivery type",
                message="Delivery type not present on workspace client request.",
                severity="info",
            )
        )
    missing.append(
        IntakeV3CommercialQuoteMissingField(
            field_code="payment_terms",
            label="Payment terms",
            message="Payment terms not present on Intake V3 workspace payload.",
            severity="info",
        )
    )
    missing.append(
        IntakeV3CommercialQuoteMissingField(
            field_code="quote_validity_days",
            label="Quote validity days",
            message="Validity days not present — not invented by bridge preview.",
            severity="info",
        )
    )
    return missing


def build_commercial_quote_bridge_snapshot_plan(
    payload: dict[str, Any] | IntakeV3Workspace,
    *,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    prequote_review: IntakeV3PreQuoteReview | None = None,
) -> IntakeV3CommercialQuoteSnapshotPlan:
    workspace = _resolve_workspace(payload)
    preview = workspace_preview
    has_confirmed = workspace.confirmed_production_model is not None
    has_raw = workspace.raw_svg_analysis is not None
    has_finish = workspace.finish_assignment is not None
    has_variation = bool(preview and preview.finish_variation_summary)
    has_pricing = bool(preview and preview.pricing_input_candidate)
    has_prequote = bool(
        prequote_review
        or (preview and preview.prequote_review)
        or dry_run
    )
    return IntakeV3CommercialQuoteSnapshotPlan(
        workspace_payload_snapshot=True,
        confirmed_production_model_snapshot=has_confirmed,
        raw_svg_analysis_reference=has_raw,
        finish_assignment_snapshot=has_finish,
        finish_variation_summary_snapshot=has_variation,
        pricing_input_candidate_snapshot=has_pricing,
        prequote_review_snapshot=has_prequote,
        guard_policy_snapshot=True,
        operator_confirmation_snapshot=has_confirmed,
        persistence_note="Snapshot plan preview only — no DB snapshot rows created in this build.",
    )


def build_commercial_quote_bridge_preview(
    payload: dict[str, Any] | IntakeV3Workspace,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    *,
    dry_run: IntakeV3QuoteCreationDryRun | None = None,
    guard_policy: IntakeV3QuoteCreationGuardPolicy | None = None,
    workspace_id: str | None = None,
    workspace_code: str | None = None,
    workspace_title: str | None = None,
    workspace_archived: bool = False,
) -> IntakeV3CommercialQuoteBridgePreview:
    """Build commercial quote bridge mapping preview — never creates quote or calls quote endpoints."""
    workspace = _resolve_workspace(payload)
    preview = workspace_preview

    if dry_run is None:
        dry_run = build_intake_v3_quote_creation_dry_run(
            workspace,
            preview,
            workspace_id=workspace_id,
            workspace_code=workspace_code,
            workspace_title=workspace_title,
            workspace_archived=workspace_archived,
        )
    if guard_policy is None:
        guard_policy = evaluate_quote_creation_guard_policy(
            workspace,
            preview,
            dry_run,
            workspace_archived=workspace_archived,
        )

    bridge_status: BridgeStatus = (
        "blocked_by_missing_policy" if guard_policy is None else "disabled_by_policy"
    )
    policy_code = guard_policy.policy_code if guard_policy else POLICY_CODE

    candidate = build_commercial_quote_candidate_payload(
        workspace,
        workspace_preview=preview,
        dry_run=dry_run,
        workspace_id=workspace_id,
        workspace_code=workspace_code,
        workspace_title=workspace_title,
        guard_policy=guard_policy,
    )
    mapping = validate_commercial_quote_bridge_mapping(
        workspace,
        workspace_preview=preview,
        dry_run=dry_run,
        candidate=candidate,
        guard_policy=guard_policy,
    )
    missing = build_commercial_quote_bridge_missing_fields(
        workspace,
        workspace_preview=preview,
        candidate=candidate,
    )
    prequote = (
        preview.prequote_review
        if preview and preview.prequote_review
        else build_prequote_review(
            workspace,
            preview,
            workspace_title=workspace_title,
            workspace_archived=workspace_archived,
        )
    )
    snapshot_plan = build_commercial_quote_bridge_snapshot_plan(
        workspace,
        workspace_preview=preview,
        dry_run=dry_run,
        prequote_review=prequote,
    )

    preview_only_fields = sorted(
        {
            item.source_field
            for item in mapping
            if item.status == "preview_only"
        }
        | PREVIEW_ONLY_FIELD_CODES
    )
    blocked_fields = sorted(
        {
            item.source_field
            for item in mapping
            if item.status == "blocked_by_policy"
        }
        | BLOCKED_FIELD_CODES
    )

    if workspace_archived:
        bridge_status = "disabled_by_policy"

    return IntakeV3CommercialQuoteBridgePreview(
        bridge_status=bridge_status,
        can_create_commercial_quote=False,
        would_create_quote=False,
        quote_creation_endpoint_called=False,
        policy_code=policy_code,
        candidate_payload=candidate,
        mapping_status=mapping,
        missing_fields=missing,
        blocked_fields=blocked_fields,
        preview_only_fields=preview_only_fields,
        snapshot_plan=snapshot_plan,
        owner_confirmation_required=True,
        safety_flags=IntakeV3CommercialQuoteBridgeSafetyFlags(),
        next_action=NEXT_ACTION,
        enablement_policy_status="owner_approval_required",
        final_blockers_present=True,
        real_creation_status="blocked",
        owner_decision_record_status="required_not_present",
        snapshot_policy_status="defined_not_executed",
        anti_duplicate_policy_status="defined",
        rollback_policy_status="defined",
        real_quote_creation_enablement_readiness_status="blocked_owner_decision_missing",
    )


def is_commercial_quote_bridge_available(
    workspace: IntakeV3Workspace,
    workspace_preview: IntakeV3WorkspacePreview | None = None,
    *,
    workspace_archived: bool = False,
) -> bool:
    """True when workspace has enough structure to build bridge preview (may still be policy-disabled)."""
    if workspace_archived:
        return True
    preview = workspace_preview
    if preview and preview.quote_readiness:
        return True
    return workspace.client_request.request_code.strip() != "" or (
        workspace.confirmed_production_model is not None
    )


def commercial_quote_bridge_status_label(
    workspace: IntakeV3Workspace,
    *,
    workspace_archived: bool = False,
) -> str:
    if workspace_archived:
        return "disabled_by_policy"
    return "disabled_by_policy"
