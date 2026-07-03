"""Intake V6 order-bound task readiness namespace."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.orders import Orders
from schemas.intake_v6 import IntakeV6OrderBoundTaskReadinessResponse, IntakeV6WorkspacePayload
from schemas.intake_v4 import TEMPLATE_OPTION_CONTRACT_VERSION
from services.intake_v3_guarded_convert_to_order_service import check_existing_order_for_iv3_quote
from services.intake_v4_order_bound_task_readiness_service import (
    _build_future_contract,
    _build_owner_approval_summary,
    _build_pricing_review_summary,
    _build_v4_order_conversion_summary,
    _collect_analysis_blockers,
    _collect_commercial_blockers,
    _collect_dry_run_blockers,
    _collect_intake_setup_blockers,
    _collect_order_blockers,
    _order_has_execution_plan,
    _primary_blocker_reason,
    _snapshot_analysis_hash,
    _workspace_analysis_hash,
)
from services.intake_v4_order_bound_task_readiness_service import (
    _issue,
)
from services.intake_v4_template_option_contract_service import evaluate_v4_template_option_contract
from services.intake_v6_commercial_quote_service import (
    check_existing_quote_for_intake_v6_workspace,
    parse_intake_v6_linkage_from_notes,
)
from services.intake_v6_task_generation_dry_run_service import build_intake_v6_task_generation_dry_run


def _v6_issue_text(message: str) -> str:
    return message.replace("Intake V4", "Intake V6").replace("V4 task generation", "V6 task generation")


async def build_intake_v6_order_bound_task_readiness(
    db: AsyncSession,
    workspace_id: str,
    payload_raw: dict[str, Any],
    payload: IntakeV6WorkspacePayload,
) -> IntakeV6OrderBoundTaskReadinessResponse:
    """Read-only order-bound readiness — no ExecutionTask, no execution_plan writes, no stock."""
    template_code = payload.product_binding.template_code
    workspace_hash = _workspace_analysis_hash(payload)

    dry_run = await build_intake_v6_task_generation_dry_run(
        db,
        workspace_id,
        payload_raw,
        payload,
    )
    template_contract = evaluate_v4_template_option_contract(payload)

    quote = await check_existing_quote_for_intake_v6_workspace(db, workspace_id)
    linkage = parse_intake_v6_linkage_from_notes(quote.notes if quote is not None else None)

    order: Orders | None = None
    has_execution_plan = False
    if quote is not None:
        order = await check_existing_order_for_iv3_quote(db, quote.id)
        if order is not None:
            has_execution_plan = await _order_has_execution_plan(db, order.id)

    blockers = []
    warnings = []

    blockers.extend(_collect_analysis_blockers(payload))
    blockers.extend(_collect_intake_setup_blockers(payload))

    for contract_blocker in template_contract.blockers:
        if contract_blocker.severity == "blocking":
            blockers.append(
                _issue(
                    contract_blocker.code,
                    contract_blocker.message,
                    source="template_contract",
                )
            )
    warnings.extend(
        [
            _issue(w.code, w.message, severity="warning", source="template_contract")
            for w in template_contract.warnings
        ]
    )

    commercial_blockers, commercial_warnings, linked_quote = _collect_commercial_blockers(
        quote=quote,
        linkage=linkage,
        workspace_id=workspace_id,
        workspace_hash=workspace_hash,
    )
    blockers.extend(commercial_blockers)
    warnings.extend(commercial_warnings)

    order_blockers, order_warnings, linked_order = _collect_order_blockers(
        quote=quote,
        order=order,
        has_execution_plan=has_execution_plan,
    )
    blockers.extend(order_blockers)
    warnings.extend(order_warnings)

    dry_run_summary = dict(dry_run.summary or {})
    dry_run_summary["can_generate_tasks"] = dry_run.can_generate_tasks
    dry_run_summary["dry_run_blockers_count"] = len(
        [b for b in dry_run.blockers if b.severity == "blocking"]
    )
    template_operation_alignment = dict(
        dry_run_summary.get("template_operation_alignment") or {}
    )
    if dry_run.audit_preview is not None:
        dry_run_summary["source_fingerprint"] = (
            dry_run.idempotency_plan[0].source_fingerprint if dry_run.idempotency_plan else None
        )
        dry_run_summary["analysis_hash"] = dry_run.audit_preview.analysis_hash

    active_count = int(dry_run_summary.get("active_candidates_count") or 0)
    provisional_count = int(dry_run_summary.get("provisional_count") or 0)
    idempotency_count = len(dry_run.idempotency_plan)

    idempotency_summary = {
        "entries_count": idempotency_count,
        "duplicate_policy": (
            dry_run.idempotency_plan[0].duplicate_policy if dry_run.idempotency_plan else None
        ),
        "source_fingerprint_present": bool(dry_run.idempotency_plan),
    }

    dry_blockers, dry_warnings = _collect_dry_run_blockers(
        dry_run_summary,
        dry_run_blockers=dry_run.blockers,
        idempotency_count=idempotency_count,
        task_candidates_count=len(dry_run.task_candidates),
        provisional_count=provisional_count,
        active_candidates_count=active_count,
    )
    blockers.extend(dry_blockers)
    warnings.extend(dry_warnings)

    if template_operation_alignment.get("blocks_real_task_generation"):
        warnings.append(
            _issue(
                "template_operation_alignment_incomplete",
                "Template operation alignment has critical partial/missing operations — real task generation blocked.",
                severity="warning",
                source="template_operation_alignment",
            )
        )

    pricing_review_summary = _build_pricing_review_summary(linkage)
    owner_approval_summary = _build_owner_approval_summary(linkage, workspace_hash)
    v6_order_conversion_summary = _build_v4_order_conversion_summary(
        quote=quote,
        linkage=linkage,
        order=order,
        workspace_hash=workspace_hash,
    )

    owner_confirmation_required = not (
        owner_approval_summary.get("exists")
        and owner_approval_summary.get("valid")
        and not owner_approval_summary.get("stale")
    )
    if owner_confirmation_required:
        blockers.append(
            _issue(
                "owner_confirmation_required",
                "Owner/operator explicit confirmation is required before real task generation.",
                source="confirmation",
            )
        )

    for issue in [*blockers, *warnings]:
        issue.message = _v6_issue_text(issue.message)

    hash_synced = linked_quote.analysis_hash_synced
    future_contract = _build_future_contract(order=order)
    future_contract.contract_version = "intake_v6_task_generation_v1"

    pricing_status = {
        "requires_pricing_review": linked_quote.requires_pricing_review,
        "pricing_review_completed": pricing_review_summary["completed"],
    }
    template_contract_status = {
        "blocking_count": len([b for b in template_contract.blockers if b.severity == "blocking"]),
        "warning_count": len(template_contract.warnings),
        "contract_version": TEMPLATE_OPTION_CONTRACT_VERSION,
    }
    analysis_hash_status = {
        "workspace_hash": workspace_hash,
        "quote_snapshot_hash": _snapshot_analysis_hash(linkage) if linkage else None,
        "synced": hash_synced,
    }

    return IntakeV6OrderBoundTaskReadinessResponse(
        workspace_id=workspace_id,
        template_code=template_code,
        linked_quote=linked_quote,
        linked_order=linked_order,
        can_generate_real_tasks=False,
        can_generate_reason=_primary_blocker_reason(blockers) or "real_task_generation_deferred",
        owner_confirmation_required=owner_confirmation_required,
        pricing_review=pricing_review_summary,
        owner_approval=owner_approval_summary,
        v6_order_conversion=v6_order_conversion_summary,
        blockers=blockers,
        warnings=warnings,
        dry_run_summary=dry_run_summary,
        idempotency_summary=idempotency_summary,
        pricing_status=pricing_status,
        template_contract_status=template_contract_status,
        template_operation_alignment=template_operation_alignment,
        analysis_hash_status=analysis_hash_status,
        future_generation_contract=future_contract,
    )
