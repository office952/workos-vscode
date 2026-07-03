"""Assign execution plan tasks to employees via tasks_json (no ORM ExecutionTask)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.execution_plan_operational_readiness_service import (
    assert_operational_mutation_allowed,
)
from services.execution_plan_task_parser import (
    ParsedExecutionPlanTasks,
    load_operational_tasks_from_plan_json,
    serialize_operational_tasks_to_plan_json,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ExecutionTaskAssignmentError(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(code)


def _reality_task_lookup(raw: Optional[str]) -> Dict[str, dict]:
    import json

    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    if not isinstance(parsed, list):
        return {}
    return {
        str(item.get("task_id")): item
        for item in parsed
        if isinstance(item, dict) and item.get("task_id")
    }


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
) -> dict:
    if not isinstance(order_id, int) or order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    if not isinstance(task_id, str) or not task_id.strip():
        raise HTTPException(status_code=422, detail={"error": "task_id_invalid"})
    if not isinstance(assigned_employee_id, int) or assigned_employee_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "assigned_employee_id_invalid"})

    emp = (
        await db.execute(select(Employees).where(Employees.id == assigned_employee_id))
    ).scalar_one_or_none()
    if emp is None:
        raise HTTPException(status_code=404, detail={"error": "employee_not_found"})
    if emp.status != "active":
        raise HTTPException(status_code=422, detail={"error": "employee_not_active"})

    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "plan_not_found"})

    assert_operational_mutation_allowed(plan)

    reality = (
        await db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
    ).scalar_one_or_none()
    reality_lookup = _reality_task_lookup(reality.tasks_json if reality else None)

    tasks, parsed = _load_plan_operational_tasks(plan.tasks_json)
    updated_task: Optional[dict] = None
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("task_id")) != task_id:
            continue
        rt = reality_lookup.get(task_id, {})
        if rt.get("ended_at"):
            raise HTTPException(
                status_code=409,
                detail={"error": "task_already_completed", "detail": "Task finalizat — reassign interzis."},
            )
        entry["assigned_employee_id"] = assigned_employee_id
        updated_task = dict(entry)
        break

    if updated_task is None:
        raise HTTPException(status_code=404, detail={"error": "task_not_found_in_plan"})

    plan.tasks_json = serialize_operational_tasks_to_plan_json(parsed, tasks)
    await db.commit()
    await db.refresh(plan)

    return {
        "plan_id": plan.id,
        "order_id": plan.order_id,
        "order_code": plan.order_code,
        "task_id": task_id,
        "assigned_employee_id": assigned_employee_id,
        "assigned_employee_name": emp.name,
        "task": updated_task,
    }


async def clear_plan_task_assignment(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
) -> None:
    """Remove plan assignee — used to rollback failed start-from-available."""
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
