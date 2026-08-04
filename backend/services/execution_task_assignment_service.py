"""Execution plan task assignment persistence boundary (Wave 6).

Direct ``assign_plan_task`` mutation is **closed**. All employee assignment
mutations must use ``assign_operational_task_controlled`` (canonical command).

``clear_plan_task_assignment`` remains for frozen Mobile rollback compatibility
but Mobile claim/start paths are blocked at the service entry (DEC-ASSIGN-08).
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from models.execution_plan import ExecutionPlan
from services.execution_plan_task_parser import (
    ParsedExecutionPlanTasks,
    load_operational_tasks_from_plan_json,
    serialize_operational_tasks_to_plan_json,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

DIRECT_ASSIGN_BLOCKED = {
    "error": "direct_assign_blocked",
    "message": (
        "Direct assign_plan_task is closed. Use the canonical controlled "
        "assignment command (DEC-ASSIGN-01/08)."
    ),
    "classification": "BLOCKED_LEGACY",
}


class ExecutionTaskAssignmentError(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(code)


def _load_plan_operational_tasks(raw: str) -> tuple[list[dict[str, Any]], ParsedExecutionPlanTasks]:
    tasks, parsed = load_operational_tasks_from_plan_json(raw)
    if parsed.format == "invalid":
        raise ExecutionTaskAssignmentError("tasks_json_invalid", ";".join(parsed.parse_errors))
    return tasks, parsed


async def assign_plan_task(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    assigned_employee_id: int,
    allow_reassign: bool = False,
    assignment_source: str | None = None,
) -> dict:
    """Legacy direct persistence entry — permanently blocked (Wave 6)."""
    del db, order_id, task_id, assigned_employee_id, allow_reassign, assignment_source
    raise HTTPException(status_code=403, detail=dict(DIRECT_ASSIGN_BLOCKED))


async def clear_plan_task_assignment(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
) -> None:
    """Remove plan assignee — retained for frozen Mobile rollback helpers only."""
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        return
    tasks, parsed = _load_plan_operational_tasks(plan.tasks_json)
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("task_id")) != task_id:
            continue
        entry.pop("assigned_employee_id", None)
        break
    plan.tasks_json = serialize_operational_tasks_to_plan_json(parsed, tasks)
    await db.commit()
    await db.refresh(plan)
