"""Materialize V2 operational_tasks[] inside execution_plan.tasks_json envelope (Step 9.3.4.a).

No ExecutionReality writes, no sessions, no Employee Mobile wiring.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from schemas.execution_plan_v2 import EXECUTION_PLAN_V2_PLAN_SOURCE
from schemas.execution_plan_v2_materialize import (
    OPERATIONAL_TASKS_VERSION,
    ExecutionPlanV2MaterializeResult,
)
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


class ExecutionPlanV2MaterializeOrderNotFound(Exception):
    """Raised when the target order row does not exist."""


class ExecutionPlanV2MaterializePlanNotFound(Exception):
    """Raised when no execution plan exists for the order."""


def _raise_blocked(error: str, message: str, blockers: list[str] | None = None) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "error": error,
            "message": message,
            "blockers": blockers or [error],
        },
    )


def _already_materialized(envelope: dict[str, Any]) -> bool:
    if envelope.get("execution_tasks_created") is True and envelope.get("operational_tasks"):
        return isinstance(envelope.get("operational_tasks"), list) and len(
            envelope["operational_tasks"]
        ) > 0
    return False


async def materialize_execution_plan_v2_operational_tasks(
    db: AsyncSession,
    order_id: int,
    *,
    prepared_by_user_id: str | None = None,
) -> ExecutionPlanV2MaterializeResult:
    """Materialize operational_tasks[] into V2 plan envelope — planned tasks only."""
    _ = prepared_by_user_id  # reserved for audit metadata; not persisted in 9.3.4.a

    order = await db.get(Orders, order_id)
    if order is None:
        raise ExecutionPlanV2MaterializeOrderNotFound()

    plan_stmt = select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
    plan_result = await db.execute(plan_stmt)
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        raise ExecutionPlanV2MaterializePlanNotFound()

    if plan.plan_source != EXECUTION_PLAN_V2_PLAN_SOURCE:
        _raise_blocked(
            "WRONG_PLAN_SOURCE",
            f"Execution plan source {plan.plan_source!r} is not order_snapshot_v2.",
            ["wrong_plan_source"],
        )

    parsed = parse_tasks_json_raw(plan.tasks_json)
    if parsed.format != "v2_envelope" or parsed.envelope is None:
        _raise_blocked(
            "INVALID_PLAN_ENVELOPE",
            "Execution plan tasks_json is not a V2 envelope.",
            parsed.parse_errors or ["invalid_plan_envelope"],
        )

    envelope: dict[str, Any] = dict(parsed.envelope)
    preview_status = str(envelope.get("preview_status") or "").strip()
    if preview_status.startswith("blocked_"):
        _raise_blocked(
            "PREVIEW_STATUS_BLOCKED",
            f"Execution plan preview_status {preview_status!r} is not materializable.",
            [preview_status],
        )

    if _already_materialized(envelope):
        raise HTTPException(
            status_code=409,
            detail={
                "error": "operational_tasks_already_materialized",
                "execution_plan_id": plan.id,
            },
        )

    planned_tasks_before = json.dumps(envelope.get("planned_tasks") or [], sort_keys=True)
    operational_tasks, warnings, blockers = materialize_operational_tasks_from_v2_envelope(
        envelope,
        execution_plan_id=plan.id,
        order_id=order.id,
    )
    if blockers:
        _raise_blocked(
            "MATERIALIZATION_BLOCKED",
            "Operational task materialization blocked.",
            blockers,
        )

    if len(operational_tasks) != len(envelope.get("planned_tasks") or []):
        _raise_blocked(
            "PLANNED_OPERATIONAL_COUNT_MISMATCH",
            "Operational tasks must mirror filtered planned_tasks exactly.",
            ["planned_operational_count_mismatch"],
        )

    activation_hash = compute_activation_hash(envelope)
    envelope["operational_tasks"] = operational_tasks
    envelope["execution_tasks_created"] = True
    envelope["operational_tasks_version"] = OPERATIONAL_TASKS_VERSION
    envelope["activation_hash"] = activation_hash
    envelope["activation_status"] = "materialized"
    envelope["materialization_warnings"] = warnings
    envelope["materialization_blockers"] = []

    planned_tasks_after = json.dumps(envelope.get("planned_tasks") or [], sort_keys=True)
    if planned_tasks_after != planned_tasks_before:
        _raise_blocked(
            "PLANNED_TASKS_MUTATION_DETECTED",
            "planned_tasks[] must remain unchanged during materialization.",
            ["planned_tasks_mutated"],
        )

    snapshot_v2_json_before = getattr(order, "snapshot_v2_json", None)
    _ = snapshot_v2_json_before  # order snapshot must not be mutated; tests verify
    plan.tasks_json = json.dumps(envelope, ensure_ascii=False)

    readiness_snapshot = getattr(order, "readiness_snapshot", None)
    if isinstance(readiness_snapshot, dict):
        patched_readiness = dict(readiness_snapshot)
        patched_readiness["execution_tasks_created"] = True
        order.readiness_snapshot = patched_readiness

    await db.commit()
    await db.refresh(plan)
    await db.refresh(order)

    preview = [
        {
            "task_id": task["task_id"],
            "source_task_key": task.get("source_task_key"),
            "process_type": task.get("process_type"),
            "operational_status": task.get("operational_status"),
        }
        for task in operational_tasks
    ]

    return ExecutionPlanV2MaterializeResult(
        status="materialized",
        order_id=order.id,
        execution_plan_id=plan.id,
        execution_tasks_created=True,
        operational_tasks_count=len(operational_tasks),
        operational_tasks_version=OPERATIONAL_TASKS_VERSION,
        activation_hash=activation_hash,
        activation_status="materialized",
        warnings=warnings,
        blockers=[],
        operational_tasks_preview=preview,
        no_sessions_created=True,
        message="Operational tasks materialized into V2 plan envelope.",
    )
