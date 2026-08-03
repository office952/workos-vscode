"""Materialize V2 operational_tasks[] inside execution_plan.tasks_json envelope (Step 9.3.4.a).

No ExecutionReality writes, no sessions, no Employee Mobile wiring.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from schemas.execution_plan_v2 import EXECUTION_PLAN_V2_PLAN_SOURCE
from schemas.execution_plan_v2_materialize import (
    OPERATIONAL_TASKS_VERSION,
    ExecutionPlanV2MaterializeResult,
)
from services.dec009_materialize_gate import (
    LIVE_DEC009_LABEL,
    LIVE_DEC009_STATUS,
    OD3_RUNTIME_IDENTITY_VERSION,
    enforce_dec009_materialize_gate,
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
    order = await db.get(Orders, order_id)
    if order is None:
        raise ExecutionPlanV2MaterializeOrderNotFound()

    plan_stmt = select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
    plan_result = await db.execute(plan_stmt)
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        raise ExecutionPlanV2MaterializePlanNotFound()

    # OD3: DEC-009 hard reject before any envelope mutation (Capacity Batch 14B).
    enforce_dec009_materialize_gate(order_id=order.id, plan_id=plan.id)

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
    # Optimistic concurrency token — reject lost updates / double-submit races.
    tasks_json_token = plan.tasks_json
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
    planned_count = len(envelope.get("planned_tasks") or [])
    envelope["operational_tasks"] = operational_tasks
    envelope["execution_tasks_created"] = True
    envelope["operational_tasks_version"] = OPERATIONAL_TASKS_VERSION
    envelope["activation_hash"] = activation_hash
    envelope["activation_status"] = "materialized"
    envelope["materialization_warnings"] = warnings
    envelope["materialization_blockers"] = []
    # Durable audit trail inside the existing V2 envelope (no schema / migration).
    envelope["materialization_audit"] = {
        "dec009": LIVE_DEC009_STATUS,
        "dec009_label": LIVE_DEC009_LABEL,
        "authorized_by": f"DEC-009={LIVE_DEC009_STATUS}",
        "wave": "FINALIZATION_WAVE_3",
        "order_id": order.id,
        "execution_plan_id": plan.id,
        "source_quote_snapshot_v2_id": plan.source_quote_snapshot_v2_id,
        "source_snapshot_code": plan.source_snapshot_code,
        "source_planned_task_count": planned_count,
        "operational_task_count": len(operational_tasks),
        "before_execution_tasks_created": False,
        "after_execution_tasks_created": True,
        "materialized_at_utc": datetime.now(timezone.utc).isoformat(),
        "idempotency": "first_materialization",
        "gate_identity_version": OD3_RUNTIME_IDENTITY_VERSION,
        "prepared_by_user_id": prepared_by_user_id,
        "no_assignments": True,
        "no_machine_assignments": True,
        "no_sessions": True,
        "no_scheduling": True,
        "no_capacity_allocation": True,
        "source_contract": "planned_tasks_only",
    }

    planned_tasks_after = json.dumps(envelope.get("planned_tasks") or [], sort_keys=True)
    if planned_tasks_after != planned_tasks_before:
        _raise_blocked(
            "PLANNED_TASKS_MUTATION_DETECTED",
            "planned_tasks[] must remain unchanged during materialization.",
            ["planned_tasks_mutated"],
        )

    snapshot_v2_json_before = getattr(order, "snapshot_v2_json", None)
    _ = snapshot_v2_json_before  # order snapshot must not be mutated; tests verify
    new_tasks_json = json.dumps(envelope, ensure_ascii=False)

    # Atomic compare-and-swap on tasks_json — second concurrent writer gets rowcount 0.
    cas = await db.execute(
        update(ExecutionPlan)
        .where(
            ExecutionPlan.id == plan.id,
            ExecutionPlan.tasks_json == tasks_json_token,
        )
        .values(tasks_json=new_tasks_json)
    )
    if cas.rowcount != 1:
        await db.rollback()
        refreshed = await db.get(ExecutionPlan, plan.id)
        if refreshed is not None:
            again = parse_tasks_json_raw(refreshed.tasks_json)
            if again.envelope is not None and _already_materialized(again.envelope):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "operational_tasks_already_materialized",
                        "execution_plan_id": plan.id,
                    },
                )
        _raise_blocked(
            "MATERIALIZATION_CONCURRENT_UPDATE",
            "Execution plan changed during materialization; no partial write persisted.",
            ["concurrent_update"],
        )

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
