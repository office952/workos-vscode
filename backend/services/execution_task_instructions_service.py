"""Manual execution instructions on planned tasks — stored in tasks_json only."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from models.execution_plan import ExecutionPlan
from services.execution_plan_operational_readiness_service import (
    assert_operational_mutation_allowed,
)
from services.execution_plan_task_parser import (
    load_operational_tasks_from_plan_json,
    serialize_operational_tasks_to_plan_json,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def update_plan_task_instructions(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    instructions: str,
) -> dict:
    if not isinstance(order_id, int) or order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    if not isinstance(task_id, str) or not task_id.strip():
        raise HTTPException(status_code=422, detail={"error": "task_id_invalid"})
    if not isinstance(instructions, str):
        raise HTTPException(status_code=422, detail={"error": "instructions_invalid"})

    normalized = instructions.strip()

    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "plan_not_found"})

    assert_operational_mutation_allowed(plan)

    tasks, parsed = load_operational_tasks_from_plan_json(plan.tasks_json)
    if parsed.format == "invalid":
        raise HTTPException(
            status_code=422,
            detail={"error": "tasks_json_invalid", "blockers": parsed.parse_errors},
        )

    updated_task: Optional[dict] = None
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("task_id")) != task_id:
            continue
        if normalized:
            entry["instructions"] = normalized
        elif "instructions" in entry:
            del entry["instructions"]
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
        "instructions": normalized,
        "task": updated_task,
    }
