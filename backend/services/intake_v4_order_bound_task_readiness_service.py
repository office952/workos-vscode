"""Intake V4 order-bound task generation readiness — read-only guard before real ExecutionTask creation."""

from __future__ import annotations

from typing import Any, Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from schemas.intake_v4 import (
    FUTURE_GENERATION_CONTRACT_VERSION,
    PILOT_V4_TEMPLATE_CODE,
    TEMPLATE_OPTION_CONTRACT_VERSION,
    IntakeV4FutureGenerationContract,
    IntakeV4LinkedOrderSummary,
    IntakeV4LinkedQuoteSummary,
    IntakeV4OrderBoundTaskReadinessResponse,
    IntakeV4TaskGenerationDryRunIssue,
    IntakeV4WorkspacePayload,
)
from services.intake_v3_guarded_convert_to_order_service import check_existing_order_for_iv3_quote
from services.intake_v3_quote_linkage_utils import (
    IV3_ACCEPTED_STATUS,
    PRICING_REVIEW_JSON_KEY,
    is_iv3_accept_completed,
    is_pricing_review_completed,
)
from services.intake_v4_quote_linkage_utils import (
    OWNER_APPROVAL_JSON_KEY,
    is_iv4_quote,
    is_v4_accept_completed,
    is_v4_convert_completed,
    is_v4_owner_approval_valid,
)
from services.intake_v4_analysis_boundary_service import (
    list_v4_analysis_boundary_blockers,
    list_v4_analysis_hash_sync_blockers,
)
from services.intake_v4_commercial_quote_service import (
    check_existing_quote_for_intake_v4_workspace,
    parse_intake_v4_linkage_from_notes,
)
from services.intake_v4_task_generation_dry_run_service import build_intake_v4_task_generation_dry_run
from services.intake_v4_template_option_contract_service import evaluate_v4_template_option_contract

ORDER_TERMINAL_STATUSES = frozenset({"cancelled", "completed", "delivered"})
ORDER_READY_FOR_TASK_GENERATION = frozenset({"locked", "in_production", "confirmed"})
QUOTE_COMMERCIAL_PENDING_STATUSES = frozenset({"draft", "sent", "trimisa", "in_negociere", "pending"})


def _issue(
    code: str,
    message: str,
    *,
    severity: Literal["blocking", "warning", "info"] = "blocking",
    source: str = "order_bound_readiness",
) -> IntakeV4TaskGenerationDryRunIssue:
    return IntakeV4TaskGenerationDryRunIssue(
        code=code,
        severity=severity,
        message=message,
        source=source,
    )


def _workspace_analysis_hash(payload: IntakeV4WorkspacePayload) -> str | None:
    svg_source = payload.svg_source
    if svg_source is not None and svg_source.file_hash:
        return svg_source.file_hash
    return None


def _snapshot_analysis_hash(linkage: dict[str, Any]) -> str | None:
    snapshot = linkage.get("snapshot")
    if not isinstance(snapshot, dict):
        return None
    ws_snap = snapshot.get("workspace_payload_snapshot")
    if not isinstance(ws_snap, dict):
        return None
    svg_source = ws_snap.get("svg_source")
    if not isinstance(svg_source, dict):
        return None
    file_hash = svg_source.get("file_hash")
    return file_hash if isinstance(file_hash, str) and file_hash else None


def _snapshot_workspace_id(linkage: dict[str, Any]) -> str | None:
    snapshot = linkage.get("snapshot")
    if isinstance(snapshot, dict):
        ws_id = snapshot.get("source_workspace_id")
        if isinstance(ws_id, str) and ws_id:
            return ws_id
    ws_id = linkage.get("source_workspace_id")
    return ws_id if isinstance(ws_id, str) and ws_id else None


def _snapshot_is_valid(linkage: dict[str, Any]) -> bool:
    snapshot = linkage.get("snapshot")
    if not isinstance(snapshot, dict):
        return False
    if not snapshot.get("source_workspace_id"):
        return False
    if not isinstance(snapshot.get("quote_input_payload"), dict):
        return False
    if not isinstance(snapshot.get("workspace_payload_snapshot"), dict):
        return False
    return True


def _quote_is_accepted(
    linkage: dict[str, Any],
    quote_status: str | None,
    *,
    quote: Quotes | None = None,
) -> bool:
    if quote is not None and is_iv4_quote(quote):
        return is_v4_accept_completed(linkage, quote_status)
    if quote_status == IV3_ACCEPTED_STATUS:
        return True
    return is_iv3_accept_completed(linkage, quote_status)


async def _order_has_execution_plan(db: AsyncSession, order_id: int) -> bool:
    count = await db.scalar(
        select(func.count()).select_from(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
    )
    return bool(count and count > 0)


def _collect_analysis_blockers(
    payload: IntakeV4WorkspacePayload,
    *,
    client_analysis_hash: str | None = None,
) -> list[IntakeV4TaskGenerationDryRunIssue]:
    issues: list[IntakeV4TaskGenerationDryRunIssue] = []
    for code in list_v4_analysis_boundary_blockers(payload):
        issues.append(
            _issue(code, f"Analysis boundary blocker: {code}.", source="analysis_boundary")
        )
    for code in list_v4_analysis_hash_sync_blockers(payload, client_analysis_hash):
        issues.append(
            _issue(code, f"Analysis hash sync blocker: {code}.", source="analysis_hash")
        )
    return issues


def _collect_intake_setup_blockers(payload: IntakeV4WorkspacePayload) -> list[IntakeV4TaskGenerationDryRunIssue]:
    issues: list[IntakeV4TaskGenerationDryRunIssue] = []
    setup = payload.finish_setup
    if setup is None or not setup.confirmed:
        issues.append(
            _issue(
                "finish_setup_not_confirmed",
                "Finish setup must be confirmed before real task generation.",
                source="finish_setup",
            )
        )
    layer_setup = payload.layer_role_setup
    if layer_setup is None or layer_setup.confirmation_status != "complete":
        issues.append(
            _issue(
                "layer_roles_incomplete",
                "Layer role confirmation must be complete before real task generation.",
                source="layer_roles",
            )
        )
    template_code = payload.product_binding.template_code
    if template_code != PILOT_V4_TEMPLATE_CODE:
        issues.append(
            _issue(
                "template_out_of_scope",
                f"Template {template_code!r} is not supported for V4 task generation.",
                source="template",
            )
        )
    return issues


def _collect_commercial_blockers(
    *,
    quote: Quotes | None,
    linkage: dict[str, Any] | None,
    workspace_id: str,
    workspace_hash: str | None,
) -> tuple[list[IntakeV4TaskGenerationDryRunIssue], list[IntakeV4TaskGenerationDryRunIssue], IntakeV4LinkedQuoteSummary]:
    blockers: list[IntakeV4TaskGenerationDryRunIssue] = []
    warnings: list[IntakeV4TaskGenerationDryRunIssue] = []
    summary = IntakeV4LinkedQuoteSummary(exists=False)

    if quote is None or linkage is None:
        blockers.append(
            _issue(
                "quote_missing",
                "No draft quote linked to this Intake V4 workspace.",
                source="linked_quote",
            )
        )
        return blockers, warnings, summary

    snapshot_valid = _snapshot_is_valid(linkage)
    requires_pricing_review = linkage.get("requires_pricing_review")
    if requires_pricing_review is None:
        requires_pricing_review = True

    snap_hash = _snapshot_analysis_hash(linkage)
    hash_synced: bool | None = None
    if workspace_hash and snap_hash:
        hash_synced = workspace_hash == snap_hash
    elif workspace_hash or snap_hash:
        hash_synced = False

    summary = IntakeV4LinkedQuoteSummary(
        exists=True,
        quote_id=quote.id,
        quote_code=quote.code,
        status=quote.status,
        requires_pricing_review=bool(requires_pricing_review),
        snapshot_valid=snapshot_valid,
        analysis_hash_synced=hash_synced,
    )

    if not snapshot_valid:
        blockers.append(
            _issue(
                "quote_snapshot_invalid",
                "Linked quote is missing a valid Intake V4 snapshot payload.",
                source="linked_quote",
            )
        )

    snap_ws_id = _snapshot_workspace_id(linkage)
    if snap_ws_id and snap_ws_id != workspace_id:
        blockers.append(
            _issue(
                "quote_snapshot_workspace_id_mismatch",
                f"Quote snapshot workspace_id {snap_ws_id!r} does not match workspace {workspace_id!r}.",
                source="linked_quote",
            )
        )

    if workspace_hash and snap_hash and workspace_hash != snap_hash:
        blockers.append(
            _issue(
                "quote_snapshot_hash_mismatch",
                "Quote snapshot analysis hash differs from current workspace analysis hash.",
                source="linked_quote",
            )
        )

    if requires_pricing_review and not is_pricing_review_completed(linkage):
        blockers.append(
            _issue(
                "requires_pricing_review",
                "Quote requires completed pricing review before production task generation.",
                source="pricing",
            )
        )

    quote_status = (quote.status or "").strip().lower()
    if quote_status in QUOTE_COMMERCIAL_PENDING_STATUSES:
        blockers.append(
            _issue(
                "quote_status_not_ready",
                f"Quote status {quote.status!r} is not ready for production task generation.",
                source="linked_quote",
            )
        )

    if not _quote_is_accepted(linkage, quote.status, quote=quote):
        blockers.append(
            _issue(
                "quote_not_accepted",
                "Quote must be accepted before real production tasks can be generated.",
                source="linked_quote",
            )
        )

    return blockers, warnings, summary


def _build_pricing_review_summary(linkage: dict[str, Any] | None) -> dict[str, Any]:
    pricing_record = linkage.get(PRICING_REVIEW_JSON_KEY) if isinstance(linkage, dict) else None
    completed = is_pricing_review_completed(linkage) if linkage else False
    return {
        "completed": completed,
        "completed_at": pricing_record.get("completed_at") if isinstance(pricing_record, dict) else None,
        "completed_by_user_id": (
            pricing_record.get("reviewed_by_user_id") if isinstance(pricing_record, dict) else None
        ),
    }


def _build_owner_approval_summary(
    linkage: dict[str, Any] | None,
    workspace_hash: str | None,
) -> dict[str, Any]:
    exists, valid, stale = is_v4_owner_approval_valid(linkage, workspace_hash)
    record = linkage.get(OWNER_APPROVAL_JSON_KEY) if isinstance(linkage, dict) else None
    return {
        "exists": exists,
        "valid": valid,
        "stale": stale,
        "approved_at": record.get("approved_at") if isinstance(record, dict) else None,
        "approved_by_user_id": record.get("approved_by_user_id") if isinstance(record, dict) else None,
    }


def _build_v4_order_conversion_summary(
    *,
    quote: Quotes | None,
    linkage: dict[str, Any] | None,
    order: Orders | None,
    workspace_hash: str | None,
) -> dict[str, Any]:
    if quote is None or linkage is None or not is_iv4_quote(quote):
        return {
            "available": False,
            "converted": False,
            "order_id": None,
            "blocked_reasons": ["quote_missing"],
        }
    blocked: list[str] = []
    if not is_pricing_review_completed(linkage):
        blocked.append("PRICING_REVIEW_REQUIRED")
    owner_exists, owner_valid, owner_stale = is_v4_owner_approval_valid(linkage, workspace_hash)
    if not owner_exists or not owner_valid or owner_stale:
        blocked.append("OWNER_APPROVAL_REQUIRED")
    if not is_v4_accept_completed(linkage, quote.status):
        blocked.append("QUOTE_NOT_ACCEPTED")
    if order is not None or is_v4_convert_completed(linkage):
        return {
            "available": False,
            "converted": True,
            "order_id": order.id if order is not None else None,
            "blocked_reasons": [],
        }
    return {
        "available": len(blocked) == 0,
        "converted": False,
        "order_id": None,
        "blocked_reasons": blocked,
    }


def _collect_order_blockers(
    *,
    quote: Quotes | None,
    order: Orders | None,
    has_execution_plan: bool,
) -> tuple[list[IntakeV4TaskGenerationDryRunIssue], list[IntakeV4TaskGenerationDryRunIssue], IntakeV4LinkedOrderSummary]:
    blockers: list[IntakeV4TaskGenerationDryRunIssue] = []
    warnings: list[IntakeV4TaskGenerationDryRunIssue] = []
    summary = IntakeV4LinkedOrderSummary(exists=False)

    if order is None:
        blockers.append(
            _issue(
                "order_missing",
                "No order exists for the linked quote — real task generation requires an order.",
                source="linked_order",
            )
        )
        return blockers, warnings, summary

    summary = IntakeV4LinkedOrderSummary(
        exists=True,
        order_id=order.id,
        order_code=order.code,
        status=order.status,
        has_execution_plan=has_execution_plan,
        source_quote_id=order.quote_id,
    )

    if quote is not None and order.quote_id is not None and order.quote_id != quote.id:
        blockers.append(
            _issue(
                "order_not_linked_to_quote",
                f"Order quote_id={order.quote_id} does not match linked quote id={quote.id}.",
                source="linked_order",
            )
        )

    if not (order.client_name or "").strip():
        blockers.append(
            _issue(
                "order_client_missing",
                "Order must have an identifiable client before production task generation.",
                source="linked_order",
            )
        )

    order_status = (order.status or "").strip().lower()
    if order_status in ORDER_TERMINAL_STATUSES:
        blockers.append(
            _issue(
                "order_terminal_status",
                f"Order status {order.status!r} cannot receive new production tasks.",
                source="linked_order",
            )
        )
    elif order_status not in ORDER_READY_FOR_TASK_GENERATION:
        blockers.append(
            _issue(
                "order_status_not_ready_for_production",
                f"Order status {order.status!r} is not ready for production task generation.",
                source="linked_order",
            )
        )

    if has_execution_plan:
        blockers.append(
            _issue(
                "order_already_has_execution_plan",
                "Order already has an execution plan — duplicate task generation is blocked.",
                source="linked_order",
            )
        )

    return blockers, warnings, summary


def _collect_dry_run_blockers(
    dry_run_summary: dict[str, Any],
    *,
    dry_run_blockers: list[IntakeV4TaskGenerationDryRunIssue],
    idempotency_count: int,
    task_candidates_count: int,
    provisional_count: int,
    active_candidates_count: int,
) -> tuple[list[IntakeV4TaskGenerationDryRunIssue], list[IntakeV4TaskGenerationDryRunIssue]]:
    blockers: list[IntakeV4TaskGenerationDryRunIssue] = []
    warnings: list[IntakeV4TaskGenerationDryRunIssue] = []

    critical_preview = [
        b
        for b in dry_run_blockers
        if b.severity == "blocking" and b.code not in {"dry_run_only_no_order"}
    ]
    if critical_preview:
        blockers.append(
            _issue(
                "dry_run_critical_blockers",
                "Production handoff / dry-run preview has critical blockers.",
                source="dry_run",
            )
        )

    if task_candidates_count == 0 or active_candidates_count == 0:
        blockers.append(
            _issue(
                "dry_run_no_task_candidates",
                "Task generation dry-run produced no active task candidates.",
                source="dry_run",
            )
        )

    if active_candidates_count > 0 and provisional_count >= active_candidates_count:
        blockers.append(
            _issue(
                "dry_run_all_provisional",
                "All dry-run task candidates are provisional — real generation is blocked.",
                source="dry_run",
            )
        )

    if idempotency_count == 0 and active_candidates_count > 0:
        blockers.append(
            _issue(
                "dry_run_idempotency_plan_missing",
                "Idempotency plan is missing for dry-run task candidates.",
                source="idempotency",
            )
        )

    if dry_run_summary.get("source_fingerprint") is None:
        warnings.append(
            _issue(
                "source_fingerprint_unavailable",
                "Dry-run source fingerprint could not be resolved.",
                severity="warning",
                source="idempotency",
            )
        )

    return blockers, warnings


def _primary_blocker_reason(blockers: list[IntakeV4TaskGenerationDryRunIssue]) -> str | None:
    for item in blockers:
        if item.severity == "blocking":
            return item.code
    return None


def _build_future_contract(
    *,
    order: Orders | None,
) -> IntakeV4FutureGenerationContract:
    return IntakeV4FutureGenerationContract(
        contract_version=FUTURE_GENERATION_CONTRACT_VERSION,
        target_entity="Order",
        target_order_id=order.id if order is not None else None,
        requires_owner_confirmation=True,
        requires_idempotency_check=True,
        requires_analysis_hash_sync=True,
        requires_quote_accepted=True,
        requires_order_ready=True,
        would_create_execution_tasks=False,
        would_write_execution_plan=False,
        next_action_label="Create production tasks",
        next_action_enabled=False,
    )


async def build_intake_v4_order_bound_task_readiness(
    db: AsyncSession,
    workspace_id: str,
    payload_raw: dict[str, Any],
    payload: IntakeV4WorkspacePayload,
) -> IntakeV4OrderBoundTaskReadinessResponse:
    """Read-only order-bound readiness — no ExecutionTask, no execution_plan writes, no stock."""
    template_code = payload.product_binding.template_code
    workspace_hash = _workspace_analysis_hash(payload)

    dry_run = await build_intake_v4_task_generation_dry_run(
        db,
        workspace_id,
        payload_raw,
        payload,
    )
    template_contract = evaluate_v4_template_option_contract(payload)

    quote = await check_existing_quote_for_intake_v4_workspace(db, workspace_id)
    linkage = parse_intake_v4_linkage_from_notes(quote.notes if quote is not None else None)

    order: Orders | None = None
    has_execution_plan = False
    if quote is not None:
        order = await check_existing_order_for_iv3_quote(db, quote.id)
        if order is not None:
            has_execution_plan = await _order_has_execution_plan(db, order.id)

    blockers: list[IntakeV4TaskGenerationDryRunIssue] = []
    warnings: list[IntakeV4TaskGenerationDryRunIssue] = []

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
    v4_order_conversion_summary = _build_v4_order_conversion_summary(
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

    hash_synced = linked_quote.analysis_hash_synced
    can_generate = False  # this build never enables real generation

    future_contract = _build_future_contract(order=order)

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

    return IntakeV4OrderBoundTaskReadinessResponse(
        workspace_id=workspace_id,
        template_code=template_code,
        linked_quote=linked_quote,
        linked_order=linked_order,
        can_generate_real_tasks=can_generate,
        can_generate_reason=_primary_blocker_reason(blockers) or "real_task_generation_deferred",
        owner_confirmation_required=owner_confirmation_required,
        pricing_review=pricing_review_summary,
        owner_approval=owner_approval_summary,
        v4_order_conversion=v4_order_conversion_summary,
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
