"""Read-only ExecutionPlan V2 materialization audit (Step 9 audit-only).

Dry-runs operational task mapping from execution_plan.tasks_json envelope.
Does NOT write DB, does NOT call POST materialize, does NOT create sessions.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from schemas.execution_plan_v2 import EXECUTION_PLAN_V2_PLAN_SOURCE, READINESS_GATE_TASK_TYPE
from schemas.execution_plan_v2_materialization_audit import (
    ExecutionPlanV2MaterializationAudit,
    MaterializableTaskCandidatePreview,
    MaterializationAuditGuards,
    NonOperationalItemPreview,
)
from schemas.order_snapshot_v2 import OrderSnapshotV2
from services.execution_plan_task_parser import (
    compute_activation_hash,
    materialize_operational_tasks_from_v2_envelope,
    parse_tasks_json_raw,
)

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "quote_orchestrator",
    "cost_engine_service",
    "aggregate_cost_bom_price_bridge",
    "product_system_execution_output",
    "execution_reality_service",
    "employee_mobile_tasks_service",
)

CONTRACT_NOTES = [
    "Primary source for materialization is execution_plan.tasks_json planned_tasks[] (frozen at persist).",
    "orders.snapshot_v2_json is upstream provenance only — not re-read for task generation at materialize.",
    "READINESS_GATE dossier rules are non-operational and excluded from planned_tasks[].",
    "WorkOS V2 materialization writes operational_tasks[] inside tasks_json — no execution_tasks table in dev.",
    "POST /plan-v2/materialize-tasks/{order_id} requires separate owner GO — audit endpoint is GET-only.",
    "Execution sessions / ExecutionActuals are Step 11+ — out of scope.",
]


class ExecutionPlanV2MaterializationAuditPlanNotFound(Exception):
    """Raised when execution_plan row does not exist."""


class ExecutionPlanV2MaterializationAuditOrderNotFound(Exception):
    """Raised when order row does not exist."""


def _guards() -> MaterializationAuditGuards:
    return MaterializationAuditGuards(
        mode="audit_only",
        creates_execution_tasks=False,
        creates_sessions=False,
        writes_database=False,
        uses_cost_engine=False,
        uses_price_endpoint=False,
        uses_quote_orchestrator=False,
        employee_mobile_scope=False,
        post_materialize_allowed=False,
    )


def _non_operational_from_order_snapshot(
    order: Orders,
    *,
    planned_task_keys: set[str],
) -> list[NonOperationalItemPreview]:
    raw = getattr(order, "snapshot_v2_json", None)
    if raw is None or not str(raw).strip():
        return []
    try:
        snapshot = OrderSnapshotV2.model_validate_json(str(raw))
    except Exception:
        return []

    aggregate = snapshot.product_aggregate_snapshot
    if aggregate is None or not aggregate.task_contract.task_rules:
        return []

    items: list[NonOperationalItemPreview] = []
    for rule in aggregate.task_contract.task_rules:
        task_name = (rule.task_name or "").strip()
        task_type = (rule.task_type or "").strip().upper()
        if task_type == READINESS_GATE_TASK_TYPE or task_type == "READINESS_GATE":
            items.append(
                NonOperationalItemPreview(
                    task_name=task_name or rule.task_name,
                    task_type=rule.task_type or READINESS_GATE_TASK_TYPE,
                    reason="READINESS_GATE dossier rule — readiness only, not operational execution task",
                )
            )
        elif task_name and task_name not in planned_task_keys:
            items.append(
                NonOperationalItemPreview(
                    task_name=task_name,
                    task_type=rule.task_type or "unknown",
                    reason="Present in aggregate task_rules but excluded from planned_tasks (trigger/owner filter)",
                )
            )
    return items


def _candidate_previews(
    operational_tasks: list[dict[str, Any]],
) -> list[MaterializableTaskCandidatePreview]:
    previews: list[MaterializableTaskCandidatePreview] = []
    for task in operational_tasks:
        previews.append(
            MaterializableTaskCandidatePreview(
                task_key=str(task.get("source_task_key") or task.get("task_id") or ""),
                label=task.get("display_name") or task.get("name"),
                canonical_task_type=task.get("process_type"),
                source_operation_code=task.get("process_id"),
                sequence_index=task.get("sequence_index"),
                operational_status_preview=str(task.get("operational_status") or "pending"),
                estimated_minutes=task.get("estimated_time_minutes"),
                warnings=list(task.get("warnings") or []),
            )
        )
    return previews


async def build_execution_plan_v2_materialization_audit_by_plan_id(
    db: AsyncSession,
    execution_plan_id: int,
) -> ExecutionPlanV2MaterializationAudit:
    plan = await db.get(ExecutionPlan, execution_plan_id)
    if plan is None:
        raise ExecutionPlanV2MaterializationAuditPlanNotFound()
    return await _build_audit_from_plan(db, plan)


async def build_execution_plan_v2_materialization_audit_by_order_id(
    db: AsyncSession,
    order_id: int,
) -> ExecutionPlanV2MaterializationAudit:
    order = await db.get(Orders, order_id)
    if order is None:
        raise ExecutionPlanV2MaterializationAuditOrderNotFound()

    plan_stmt = select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
    plan_result = await db.execute(plan_stmt)
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        raise ExecutionPlanV2MaterializationAuditPlanNotFound()
    return await _build_audit_from_plan(db, plan)


async def _build_audit_from_plan(
    db: AsyncSession,
    plan: ExecutionPlan,
) -> ExecutionPlanV2MaterializationAudit:
    order = await db.get(Orders, plan.order_id)
    if order is None:
        raise ExecutionPlanV2MaterializationAuditOrderNotFound()

    parsed = parse_tasks_json_raw(plan.tasks_json)
    envelope = parsed.envelope or {}
    planned_tasks = parsed.planned_tasks or []
    planned_keys = {
        str(item.get("task_key")).strip()
        for item in planned_tasks
        if isinstance(item, dict) and item.get("task_key")
    }
    operations = [
        item for item in (envelope.get("planned_operations") or []) if isinstance(item, dict)
    ]
    operational_in_envelope = parsed.operational_tasks or []
    template_code = envelope.get("template_code")

    non_operational = _non_operational_from_order_snapshot(order, planned_task_keys=planned_keys)

    materialization_status: str = "blocked_needs_owner_go"
    dry_run_status: str = "blocked"
    blockers: list[str] = []
    warnings: list[str] = list(envelope.get("warnings") or [])
    candidates: list[MaterializableTaskCandidatePreview] = []
    activation_hash_preview: str | None = None

    if plan.plan_source != EXECUTION_PLAN_V2_PLAN_SOURCE:
        blockers.append(f"wrong_plan_source:{plan.plan_source}")
    if parsed.format != "v2_envelope":
        blockers.append("invalid_plan_envelope")

    if operational_in_envelope and envelope.get("execution_tasks_created") is True:
        materialization_status = "already_materialized_in_envelope"
        dry_run_status = "already_materialized"
        candidates = _candidate_previews(operational_in_envelope)
        activation_hash_preview = envelope.get("activation_hash")
    elif envelope and not blockers:
        activation_hash_preview = compute_activation_hash(envelope)
        operational, mat_warnings, mat_blockers = materialize_operational_tasks_from_v2_envelope(
            envelope,
            execution_plan_id=plan.id,
            order_id=order.id,
        )
        warnings = sorted(set(warnings + mat_warnings))
        if mat_blockers:
            dry_run_status = "blocked"
            blockers.extend(mat_blockers)
        elif mat_warnings:
            dry_run_status = "ready_with_warnings"
            candidates = _candidate_previews(operational)
        else:
            dry_run_status = "ready"
            candidates = _candidate_previews(operational)

    return ExecutionPlanV2MaterializationAudit(
        order_id=order.id,
        order_code=order.code,
        execution_plan_id=plan.id,
        source_quote_snapshot_v2_id=plan.source_quote_snapshot_v2_id,
        source_snapshot_code=plan.source_snapshot_code,
        plan_source=plan.plan_source,
        template_code=template_code if isinstance(template_code, str) else None,
        materialization_status=materialization_status,  # type: ignore[arg-type]
        dry_run_status=dry_run_status,  # type: ignore[arg-type]
        planned_task_count=len(planned_tasks),
        operation_count=len(operations),
        operational_tasks_in_envelope_count=len(operational_in_envelope),
        materializable_task_candidates=candidates,
        non_operational_items=non_operational,
        blockers=blockers,
        warnings=warnings,
        activation_hash_preview=activation_hash_preview,
        guards=_guards(),
        contract_notes=CONTRACT_NOTES,
        message=(
            "Materialization audit-only — POST materialize remains blocked until owner GO. "
            "Dry-run shows mappable operational task candidates from planned_tasks[]."
        ),
        input_summary={
            "envelope_source": envelope.get("source"),
            "preview_status": envelope.get("preview_status"),
            "dry_run_candidate_count": len(candidates),
            "non_operational_count": len(non_operational),
        },
    )
