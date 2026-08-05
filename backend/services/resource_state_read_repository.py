"""Read-only Resource State repositories (R6).

No insert/update/delete methods by design.
"""

from __future__ import annotations

from typing import Sequence

from core.schema_ownership import RESOURCE_STATE_TABLES
from models.execution_task_capacity_allocation import (
    ExecutionTaskCapacityAllocation,
)
from models.execution_task_machine_reservation import (
    ExecutionTaskMachineReservation,
)
from models.execution_task_schedule import ExecutionTaskSchedule
from models.resource_domain_configuration import ResourceDomainConfiguration
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_APPLICATION_SCOPE = "application"


class ResourceStateReadRepository:
    """Explicit read-only contract for Resource State tables."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_active_configuration(
        self,
        *,
        domain: str,
        application_scope_key: str = DEFAULT_APPLICATION_SCOPE,
    ) -> ResourceDomainConfiguration | None:
        result = await self._db.execute(
            select(ResourceDomainConfiguration).where(
                ResourceDomainConfiguration.domain == domain,
                ResourceDomainConfiguration.application_scope_key
                == application_scope_key,
                ResourceDomainConfiguration.status == "ACTIVE",
            )
        )
        return result.scalar_one_or_none()

    async def list_schedules_for_task(
        self, *, execution_plan_id: int, task_key: str
    ) -> Sequence[ExecutionTaskSchedule]:
        result = await self._db.execute(
            select(ExecutionTaskSchedule)
            .where(
                ExecutionTaskSchedule.execution_plan_id == execution_plan_id,
                ExecutionTaskSchedule.task_key == task_key,
            )
            .order_by(ExecutionTaskSchedule.id.asc())
        )
        return list(result.scalars().all())

    async def list_reservations_for_task(
        self, *, execution_plan_id: int, task_key: str
    ) -> Sequence[ExecutionTaskMachineReservation]:
        result = await self._db.execute(
            select(ExecutionTaskMachineReservation)
            .where(
                ExecutionTaskMachineReservation.execution_plan_id
                == execution_plan_id,
                ExecutionTaskMachineReservation.task_key == task_key,
            )
            .order_by(ExecutionTaskMachineReservation.id.asc())
        )
        return list(result.scalars().all())

    async def list_capacity_allocations_for_task(
        self, *, execution_plan_id: int, task_key: str
    ) -> Sequence[ExecutionTaskCapacityAllocation]:
        result = await self._db.execute(
            select(ExecutionTaskCapacityAllocation)
            .where(
                ExecutionTaskCapacityAllocation.execution_plan_id
                == execution_plan_id,
                ExecutionTaskCapacityAllocation.task_key == task_key,
            )
            .order_by(ExecutionTaskCapacityAllocation.id.asc())
        )
        return list(result.scalars().all())

    async def count_all_resource_state_rows(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for name in sorted(RESOURCE_STATE_TABLES):
            out[name] = int(
                (
                    await self._db.execute(text(f"SELECT COUNT(*) FROM {name}"))
                ).scalar_one()
            )
        return out


# Intentionally absent write surface (testable).
FORBIDDEN_WRITE_METHOD_NAMES = frozenset(
    {
        "insert",
        "update",
        "delete",
        "configure",
        "activate",
        "cancel",
        "release",
        "supersede",
        "create",
        "save",
        "upsert",
    }
)


def repository_public_method_names() -> set[str]:
    return {
        name
        for name in dir(ResourceStateReadRepository)
        if not name.startswith("_") and callable(getattr(ResourceStateReadRepository, name))
    }
