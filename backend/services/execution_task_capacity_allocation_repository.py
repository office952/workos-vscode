"""Capacity Stage 1 — capacity allocation repository (no generic mutators)."""

from __future__ import annotations

from datetime import datetime

from models.execution_task_capacity_allocation import (
    ExecutionTaskCapacityAllocation,
    ExecutionTaskCapacityAllocationTransition,
)
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

FORBIDDEN_MUTATORS = {
    "delete",
    "delete_all",
    "upsert",
    "update_status",
    "hard_delete",
}

OPEN_STATUSES = ("HELD", "ALLOCATED")


class ExecutionTaskCapacityAllocationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self, allocation_id: int
    ) -> ExecutionTaskCapacityAllocation | None:
        return await self.db.get(ExecutionTaskCapacityAllocation, allocation_id)

    async def get_transition_by_idempotency_key(
        self, idempotency_key: str
    ) -> ExecutionTaskCapacityAllocationTransition | None:
        result = await self.db.execute(
            select(ExecutionTaskCapacityAllocationTransition).where(
                ExecutionTaskCapacityAllocationTransition.idempotency_key
                == idempotency_key
            )
        )
        return result.scalar_one_or_none()

    async def sum_open_minutes_for_workcenter_bucket(
        self,
        *,
        workcenter_code: str,
        bucket_start: datetime,
        bucket_end: datetime,
        exclude_allocation_id: int | None = None,
    ) -> int:
        """Aggregate SQL — Stage 1 DAY buckets match exact window bounds.

        Avoids half-open overlap edge cases with SQLite datetime affinity.
        """
        sql = (
            "SELECT COALESCE(SUM(quantity), 0) FROM execution_task_capacity_allocations "
            "WHERE workcenter_code = :wc "
            "AND status IN ('HELD', 'ALLOCATED') "
            "AND bucket_start = :start AND bucket_end = :end"
        )
        params: dict = {
            "wc": workcenter_code,
            "start": bucket_start,
            "end": bucket_end,
        }
        if exclude_allocation_id is not None:
            sql += " AND id != :exclude_id"
            params["exclude_id"] = exclude_allocation_id
        result = await self.db.execute(text(sql), params)
        return int(result.scalar_one())

    async def list_open_for_task(
        self, *, execution_plan_id: int, task_key: str
    ) -> list[ExecutionTaskCapacityAllocation]:
        result = await self.db.execute(
            select(ExecutionTaskCapacityAllocation)
            .where(
                ExecutionTaskCapacityAllocation.execution_plan_id
                == execution_plan_id,
                ExecutionTaskCapacityAllocation.task_key == task_key,
                ExecutionTaskCapacityAllocation.status.in_(OPEN_STATUSES),
            )
            .order_by(ExecutionTaskCapacityAllocation.id.asc())
        )
        return list(result.scalars().all())

    async def add_allocation(
        self, row: ExecutionTaskCapacityAllocation
    ) -> ExecutionTaskCapacityAllocation:
        self.db.add(row)
        await self.db.flush()
        return row

    async def add_transition(
        self, row: ExecutionTaskCapacityAllocationTransition
    ) -> ExecutionTaskCapacityAllocationTransition:
        self.db.add(row)
        await self.db.flush()
        return row

    async def count_open(self) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(ExecutionTaskCapacityAllocation).where(
                ExecutionTaskCapacityAllocation.status.in_(OPEN_STATUSES)
            )
        )
        return int(result.scalar_one())
