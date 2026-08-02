"""Read-only eligibility readiness audit for Golden Pilot (DEC gate — no eligibility impl)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from schemas.order_snapshot_v2 import OrderSnapshotV2


def _audit_task(task: dict[str, Any]) -> dict[str, Any]:
    process_id = str(task.get("process_id") or "").strip()
    wc = task.get("workcenter")
    mr = task.get("machine_requirement")
    wc_status = None
    if isinstance(mr, dict):
        wc_status = mr.get("resolution_status")
        if wc is None:
            wc = mr.get("workcenter")
    minutes = task.get("estimated_time_minutes")
    if minutes is None:
        minutes = task.get("estimated_minutes")
    warnings = list(task.get("warnings") or [])

    needs_wc = "WORKCENTER_NOT_REQUIRED" not in warnings and wc_status != "not_required"
    wc_ok = (not needs_wc) or bool(wc)
    minutes_status = "resolved" if minutes is not None else "source_missing"

    blockers: list[str] = []
    if needs_wc and not wc:
        if "WORKCENTER_MAPPING_AMBIGUOUS" in warnings:
            blockers.append("workcenter_ambiguous")
        else:
            blockers.append("workcenter_missing")

    return {
        "task_id": task.get("task_id") or task.get("source_task_key"),
        "process_id": process_id,
        "workcenter": wc,
        "workcenter_required": needs_wc,
        "workcenter_ok": wc_ok,
        "estimated_minutes": minutes,
        "planning_minutes_status": minutes_status,
        "blockers": blockers,
        "warnings": warnings,
    }


async def build_eligibility_readiness_audit(
    db: AsyncSession,
    order_id: int,
) -> dict[str, Any]:
    """Pure read audit — never writes, never assigns, never materializes."""
    order = await db.get(Orders, order_id)
    if order is None:
        return {"order_id": order_id, "status": "order_not_found", "ready": False}

    plan_row = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan_row is None:
        return {"order_id": order_id, "status": "plan_not_found", "ready": False}

    try:
        envelope = json.loads(plan_row.tasks_json or "{}")
    except json.JSONDecodeError:
        envelope = {}
    ops: list[Any]
    if isinstance(envelope, list):
        ops = envelope
    else:
        ops = envelope.get("operational_tasks") or []

    task_audits = [_audit_task(t) for t in ops if isinstance(t, dict)]
    wc_blockers = sum(1 for t in task_audits if t["blockers"])
    minutes_missing = sum(
        1 for t in task_audits if t["planning_minutes_status"] == "source_missing"
    )

    identity_stable = all(
        bool(t.get("task_id")) and bool(t.get("process_id")) for t in task_audits
    )
    materialized = len(ops) > 0 and (
        bool(isinstance(envelope, dict) and envelope.get("execution_tasks_created"))
        or len(ops) > 0
    )

    ready = materialized and identity_stable and wc_blockers == 0 and len(task_audits) > 0
    status = (
        "ready"
        if ready and minutes_missing == 0
        else ("ready_with_warnings" if ready else "blocked")
    )

    snap_valid = False
    if order.snapshot_v2_json:
        try:
            OrderSnapshotV2.model_validate_json(order.snapshot_v2_json)
            snap_valid = True
        except Exception:
            snap_valid = False

    return {
        "mode": "read_only_eligibility_readiness",
        "order_id": order_id,
        "execution_plan_id": plan_row.id,
        "status": status,
        "ready_for_employee_eligibility": ready,
        "operational_task_count": len(task_audits),
        "workcenter_blocker_count": wc_blockers,
        "planning_minutes_source_missing_count": minutes_missing,
        "identity_stable": identity_stable,
        "materialized": materialized,
        "sessions": 0,
        "actuals": 0,
        "assignments": 0,
        "order_snapshot_valid": snap_valid,
        "tasks": task_audits,
        "notes": [
            "Eligibility itself is NOT implemented — this is a readiness gate only.",
            "Planning minutes source_missing yields ready_with_warnings when WC truth is complete.",
            "Ambiguous or missing required workcenter blocks eligibility readiness for that task.",
        ],
    }
