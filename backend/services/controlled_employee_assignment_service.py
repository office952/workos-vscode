"""Controlled Employee Assignment V1 — eligibility-gated, operational_tasks only.

Wraps ``assign_plan_task`` with DEC-015 eligibility revalidation.
Never creates sessions/actuals. Does not invent PREPRESS/CNC authorizations.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_reality import ExecutionReality
from services.employee_eligibility_read_model_service import (
    build_employee_eligibility_read_model,
)
from services.execution_task_assignment_service import assign_plan_task

CONTROLLED_ASSIGNMENT_SOURCE = "controlled_ops_graph_assign_v1"


def _reality_has_active_session(raw: str | None, task_id: str) -> bool:
    import json

    if not raw:
        return False
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return False
    if not isinstance(parsed, list):
        return False
    for item in parsed:
        if not isinstance(item, dict):
            continue
        if str(item.get("task_id")) != task_id:
            continue
        if item.get("started_at") and not item.get("ended_at"):
            return True
    return False


async def assign_operational_task_controlled(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    assigned_employee_id: int,
    allow_reassign: bool = False,
    actor_user_id: str | None = None,
) -> dict[str, Any]:
    """Assign only if current eligibility read model lists the employee.

    Fail-closed for blocked eligibility statuses and non-eligible employees.
    """
    tid = (task_id or "").strip()
    if not tid:
        raise HTTPException(status_code=422, detail={"error": "invalid_task_identity"})

    eligibility = await build_employee_eligibility_read_model(db, order_id)
    if eligibility.get("status") == "blocked_not_materialized":
        raise HTTPException(
            status_code=422,
            detail={"error": "task_not_materialized"},
        )
    if eligibility.get("status") == "plan_not_found":
        raise HTTPException(status_code=404, detail={"error": "plan_not_found"})

    task_row = None
    for row in eligibility.get("tasks") or []:
        if str(row.get("task_key") or "") == tid:
            task_row = row
            break
    if task_row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "task_not_found", "message": "Task absent from operational_tasks[]."},
        )

    status = str(task_row.get("eligibility_status") or "")
    blockers = list(task_row.get("blockers") or [])

    status_to_error = {
        "blocked_missing_workcenter": "blocked_missing_workcenter",
        "blocked_ambiguous_workcenter": "blocked_ambiguous_workcenter",
        "blocked_missing_requirements": "blocked_missing_requirements",
        "blocked_no_matching_employee": "blocked_no_matching_employee",
        "not_required": "blocked_missing_requirements",
    }
    if status in status_to_error:
        raise HTTPException(
            status_code=422,
            detail={
                "error": status_to_error[status],
                "eligibility_status": status,
                "blockers": blockers,
            },
        )
    if status not in {"ready", "ready_with_warnings"}:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "employee_not_eligible",
                "eligibility_status": status,
                "blockers": blockers,
            },
        )

    eligible_ids = {
        int(e["employee_id"])
        for e in (task_row.get("eligible_employees") or [])
        if e.get("employee_id") is not None
    }
    if int(assigned_employee_id) not in eligible_ids:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "employee_not_eligible",
                "message": "Employee is not in current eligibility candidates for this task.",
                "eligible_employee_ids": sorted(eligible_ids),
            },
        )

    reality = (
        await db.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one_or_none()
    if reality and _reality_has_active_session(reality.tasks_json, tid):
        raise HTTPException(
            status_code=409,
            detail={"error": "task_session_already_active"},
        )

    result = await assign_plan_task(
        db,
        order_id=order_id,
        task_id=tid,
        assigned_employee_id=int(assigned_employee_id),
        allow_reassign=allow_reassign,
        assignment_source=CONTROLLED_ASSIGNMENT_SOURCE,
    )

    # Enrich response — never invent sessions.
    result["controlled"] = True
    result["eligibility_status"] = status
    result["eligible_employee_count"] = int(task_row.get("eligible_employee_count") or 0)
    result["requirement_version"] = task_row.get("requirement_version")
    result["actor_user_id"] = actor_user_id
    result["sessions_created"] = 0
    result["actuals_created"] = 0
    return result
