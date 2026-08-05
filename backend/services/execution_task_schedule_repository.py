"""Scheduling write boundary (R9) — bounded methods + append-only transitions."""

from __future__ import annotations

from models.execution_task_schedule import (
    SCHEDULE_OPEN_STATUSES,
    ExecutionTaskSchedule,
    ExecutionTaskScheduleTransition,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

FORBIDDEN_MUTATORS = frozenset(
    {
        "delete_schedule",
        "delete_transition",
        "update_transition",
        "clear_history",
        "save_any",
        "upsert",
    }
)


class ExecutionTaskScheduleRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, schedule_id: int) -> ExecutionTaskSchedule | None:
        result = await self._db.execute(
            select(ExecutionTaskSchedule).where(
                ExecutionTaskSchedule.id == schedule_id
            )
        )
        return result.scalar_one_or_none()

    async def get_open_for_task(
        self, *, execution_plan_id: int, task_key: str
    ) -> ExecutionTaskSchedule | None:
        result = await self._db.execute(
            select(ExecutionTaskSchedule).where(
                ExecutionTaskSchedule.execution_plan_id == execution_plan_id,
                ExecutionTaskSchedule.task_key == task_key,
                ExecutionTaskSchedule.status.in_(SCHEDULE_OPEN_STATUSES),
            )
        )
        return result.scalar_one_or_none()

    async def get_transition_by_idempotency_key(
        self, idempotency_key: str
    ) -> ExecutionTaskScheduleTransition | None:
        result = await self._db.execute(
            select(ExecutionTaskScheduleTransition).where(
                ExecutionTaskScheduleTransition.idempotency_key == idempotency_key
            )
        )
        return result.scalar_one_or_none()

    async def add_schedule(
        self, row: ExecutionTaskSchedule
    ) -> ExecutionTaskSchedule:
        self._db.add(row)
        await self._db.flush()
        return row

    async def add_transition(
        self, row: ExecutionTaskScheduleTransition
    ) -> ExecutionTaskScheduleTransition:
        self._db.add(row)
        await self._db.flush()
        return row
