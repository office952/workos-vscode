"""Capacity Stage 1 — workcenter capacity source repository (no generic mutators)."""

from __future__ import annotations

from datetime import date

from models.workcenter_capacity_source import (
    WorkcenterCapacitySource,
    WorkcenterCapacitySourceTransition,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

FORBIDDEN_MUTATORS = {
    "delete",
    "delete_all",
    "upsert",
    "update_status",
    "hard_delete",
}


class WorkcenterCapacitySourceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, source_id: int) -> WorkcenterCapacitySource | None:
        return await self.db.get(WorkcenterCapacitySource, source_id)

    async def get_active_for_day(
        self, *, workcenter_code: str, bucket_date: date
    ) -> WorkcenterCapacitySource | None:
        result = await self.db.execute(
            select(WorkcenterCapacitySource).where(
                WorkcenterCapacitySource.workcenter_code == workcenter_code,
                WorkcenterCapacitySource.bucket_date == bucket_date,
                WorkcenterCapacitySource.status == "ACTIVE",
            )
        )
        return result.scalar_one_or_none()

    async def get_transition_by_idempotency_key(
        self, idempotency_key: str
    ) -> WorkcenterCapacitySourceTransition | None:
        result = await self.db.execute(
            select(WorkcenterCapacitySourceTransition).where(
                WorkcenterCapacitySourceTransition.idempotency_key
                == idempotency_key
            )
        )
        return result.scalar_one_or_none()

    async def add_source(self, row: WorkcenterCapacitySource) -> WorkcenterCapacitySource:
        self.db.add(row)
        await self.db.flush()
        return row

    async def add_transition(
        self, row: WorkcenterCapacitySourceTransition
    ) -> WorkcenterCapacitySourceTransition:
        self.db.add(row)
        await self.db.flush()
        return row
