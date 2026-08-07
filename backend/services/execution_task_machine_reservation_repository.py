"""Machine reservation write boundary (R9)."""

from __future__ import annotations

from datetime import datetime

from models.execution_task_machine_reservation import (
    RESERVATION_OPEN_STATUSES,
    ExecutionTaskMachineReservation,
    ExecutionTaskMachineReservationTransition,
)
from services.resource_state_write_common import windows_overlap
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

FORBIDDEN_MUTATORS = frozenset(
    {
        "delete_reservation",
        "delete_transition",
        "update_transition",
        "clear_history",
        "save_any",
        "upsert",
    }
)


class ExecutionTaskMachineReservationRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(
        self, reservation_id: int
    ) -> ExecutionTaskMachineReservation | None:
        result = await self._db.execute(
            select(ExecutionTaskMachineReservation).where(
                ExecutionTaskMachineReservation.id == reservation_id
            )
        )
        return result.scalar_one_or_none()

    async def get_open_for_task_machine(
        self, *, execution_plan_id: int, task_key: str, machine_id: int
    ) -> ExecutionTaskMachineReservation | None:
        result = await self._db.execute(
            select(ExecutionTaskMachineReservation).where(
                ExecutionTaskMachineReservation.execution_plan_id
                == execution_plan_id,
                ExecutionTaskMachineReservation.task_key == task_key,
                ExecutionTaskMachineReservation.machine_id == machine_id,
                ExecutionTaskMachineReservation.machine_run_id.is_(None),
                ExecutionTaskMachineReservation.status.in_(
                    RESERVATION_OPEN_STATUSES
                ),
            )
        )
        return result.scalar_one_or_none()

    async def list_open_for_machine(
        self, *, machine_id: int
    ) -> list[ExecutionTaskMachineReservation]:
        result = await self._db.execute(
            select(ExecutionTaskMachineReservation).where(
                ExecutionTaskMachineReservation.machine_id == machine_id,
                ExecutionTaskMachineReservation.status.in_(
                    RESERVATION_OPEN_STATUSES
                ),
            )
        )
        return list(result.scalars().all())

    async def find_overlapping_open(
        self,
        *,
        machine_id: int,
        start: datetime,
        end: datetime,
        exclude_id: int | None = None,
    ) -> ExecutionTaskMachineReservation | None:
        rows = await self.list_open_for_machine(machine_id=machine_id)
        for row in rows:
            if exclude_id is not None and row.id == exclude_id:
                continue
            if windows_overlap(
                row.reservation_start, row.reservation_end, start, end
            ):
                return row
        return None

    async def get_transition_by_idempotency_key(
        self, idempotency_key: str
    ) -> ExecutionTaskMachineReservationTransition | None:
        result = await self._db.execute(
            select(ExecutionTaskMachineReservationTransition).where(
                ExecutionTaskMachineReservationTransition.idempotency_key
                == idempotency_key
            )
        )
        return result.scalar_one_or_none()

    async def add_reservation(
        self, row: ExecutionTaskMachineReservation
    ) -> ExecutionTaskMachineReservation:
        self._db.add(row)
        await self._db.flush()
        return row

    async def add_transition(
        self, row: ExecutionTaskMachineReservationTransition
    ) -> ExecutionTaskMachineReservationTransition:
        self._db.add(row)
        await self._db.flush()
        return row
