"""MACHINE_RUN operator read service — list + detail (no writes).

Source of truth: machine_runs + participants + run-owned reservation + machines
+ ExecutionPlan tasks_json provenance. Not R6.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from models.execution_plan import ExecutionPlan
from models.execution_task_machine_reservation import ExecutionTaskMachineReservation
from models.machine_run import MachineRun, MachineRunParticipant
from models.operational_registry import MachineRegistry
from schemas.resource_state_machine_run_read import (
    MachineRunDetail,
    MachineRunListItem,
    MachineRunListResult,
    MachineRunMachineProjection,
    MachineRunParticipantRead,
    MachineRunReservationProjection,
)
from services.execution_plan_task_parser import load_operational_tasks_from_plan_json
from services.resource_state_write_common import (
    ResourceStateNotFoundError,
    ResourceStateValidationError,
)
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Commitment still open for the machine clock (includes COMPLETED+RESERVED).
OPEN_RESERVATION_STATUSES = frozenset({"HELD", "RESERVED"})


def _workcenter_of(task: dict[str, Any]) -> str | None:
    mr = task.get("machine_requirement")
    if isinstance(mr, dict):
        wc = mr.get("workcenter") or mr.get("workcenter_code")
        if wc is not None and str(wc).strip():
            return str(wc).strip()
    wc = task.get("workcenter") or task.get("workcenter_code")
    if wc is not None and str(wc).strip():
        return str(wc).strip()
    return None


def _operation_code_of(task: dict[str, Any]) -> str | None:
    for key in ("source_operation_code", "process_id", "operation_code"):
        val = task.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def _parse_capabilities(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(v) for v in raw]
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(v) for v in parsed]
        except (TypeError, ValueError):
            return []
    return []


def _derived_runtime_seconds(
    started_at: datetime | None, completed_at: datetime | None
) -> int | None:
    if started_at is None or completed_at is None:
        return None
    start = started_at if started_at.tzinfo else started_at.replace(tzinfo=timezone.utc)
    end = (
        completed_at
        if completed_at.tzinfo
        else completed_at.replace(tzinfo=timezone.utc)
    )
    seconds = int((end - start).total_seconds())
    return max(seconds, 0)


def _task_lookup(plan: ExecutionPlan) -> dict[str, dict[str, Any]]:
    tasks, parsed = load_operational_tasks_from_plan_json(plan.tasks_json or "")
    if parsed.format == "invalid":
        return {}
    out: dict[str, dict[str, Any]] = {}
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        tid = entry.get("task_id")
        if isinstance(tid, str) and tid.strip():
            out[tid.strip()] = entry
    return out


def _machine_projection(machine: MachineRegistry) -> MachineRunMachineProjection:
    return MachineRunMachineProjection(
        machine_id=int(machine.id),
        machine_code=str(machine.machine_code or ""),
        name=str(machine.name or ""),
        is_active=bool(machine.is_active),
        is_available=bool(machine.is_available),
        operational_status=(
            str(machine.operational_status)
            if machine.operational_status is not None
            else None
        ),
        capabilities=_parse_capabilities(machine.capabilities),
    )


def _reservation_projection(
    reservation: ExecutionTaskMachineReservation,
) -> MachineRunReservationProjection:
    return MachineRunReservationProjection(
        reservation_id=int(reservation.id),
        status=reservation.status,  # type: ignore[arg-type]
        version=int(reservation.version),
        machine_id=int(reservation.machine_id),
        reservation_start=reservation.reservation_start,
        reservation_end=reservation.reservation_end,
        timezone=str(reservation.timezone),
    )


def _participant_read(
    p: MachineRunParticipant, task: dict[str, Any] | None
) -> MachineRunParticipantRead:
    capability = None
    batch_eligible = None
    operation_code = None
    workcenter = None
    if task is not None:
        operation_code = _operation_code_of(task)
        workcenter = _workcenter_of(task)
        raw_cap = task.get("machine_capability_code")
        if isinstance(raw_cap, str) and raw_cap.strip():
            capability = raw_cap.strip()
        be = task.get("batch_eligible")
        if isinstance(be, bool):
            batch_eligible = be
    return MachineRunParticipantRead(
        participant_id=int(p.id),
        status=p.status,  # type: ignore[arg-type]
        execution_plan_id=int(p.execution_plan_id),
        task_key=str(p.task_key),
        order_id=int(p.order_id),
        operation_code=operation_code,
        workcenter=workcenter,
        machine_capability_code=capability,
        batch_eligible=batch_eligible,
        added_at=p.added_at,
        added_by=p.added_by,
        removed_at=p.removed_at,
        removed_by=p.removed_by,
    )


async def list_machine_runs(
    db: AsyncSession,
    *,
    status: str | None = None,
    machine_id: int | None = None,
    execution_plan_id: int | None = None,
    order_id: int | None = None,
    open_only: bool = False,
) -> MachineRunListResult:
    """List MachineRuns — compact summary for /execution/machine-runs."""
    if status is not None and status not in {
        "HELD",
        "RESERVED",
        "RUNNING",
        "COMPLETED",
        "CANCELLED",
        "RELEASED",
        "SUPERSEDED",
    }:
        raise ResourceStateValidationError(
            "invalid_filter",
            f"unknown status filter {status!r}",
        )

    open_rank = case(
        (
            ExecutionTaskMachineReservation.status.in_(tuple(OPEN_RESERVATION_STATUSES)),
            0,
        ),
        else_=1,
    )
    stmt = (
        select(MachineRun, ExecutionTaskMachineReservation)
        .join(
            ExecutionTaskMachineReservation,
            ExecutionTaskMachineReservation.machine_run_id == MachineRun.id,
        )
        .order_by(
            open_rank.asc(),
            ExecutionTaskMachineReservation.reservation_start.asc(),
            MachineRun.id.asc(),
        )
    )
    if status is not None:
        stmt = stmt.where(MachineRun.status == status)
    if machine_id is not None:
        if machine_id <= 0:
            raise ResourceStateValidationError(
                "invalid_filter", "machine_id must be > 0"
            )
        stmt = stmt.where(MachineRun.machine_id == machine_id)
    if open_only:
        stmt = stmt.where(
            ExecutionTaskMachineReservation.status.in_(tuple(OPEN_RESERVATION_STATUSES))
        )
    if execution_plan_id is not None:
        if execution_plan_id <= 0:
            raise ResourceStateValidationError(
                "invalid_filter", "execution_plan_id must be > 0"
            )
        stmt = stmt.where(
            MachineRun.id.in_(
                select(MachineRunParticipant.machine_run_id).where(
                    MachineRunParticipant.execution_plan_id == execution_plan_id
                )
            )
        )
    if order_id is not None:
        if order_id <= 0:
            raise ResourceStateValidationError(
                "invalid_filter", "order_id must be > 0"
            )
        stmt = stmt.where(
            MachineRun.id.in_(
                select(MachineRunParticipant.machine_run_id).where(
                    MachineRunParticipant.order_id == order_id
                )
            )
        )

    rows = (await db.execute(stmt)).all()
    if not rows:
        return MachineRunListResult(items=[], count=0)

    run_ids = [int(run.id) for run, _res in rows]
    machine_ids = sorted({int(run.machine_id) for run, _res in rows})

    machines = {
        int(m.id): m
        for m in (
            await db.execute(
                select(MachineRegistry).where(MachineRegistry.id.in_(machine_ids))
            )
        ).scalars().all()
    }

    count_rows = (
        await db.execute(
            select(
                MachineRunParticipant.machine_run_id,
                func.sum(
                    case((MachineRunParticipant.status == "ACTIVE", 1), else_=0)
                ).label("active_count"),
                func.count().label("total_count"),
            )
            .where(MachineRunParticipant.machine_run_id.in_(run_ids))
            .group_by(MachineRunParticipant.machine_run_id)
        )
    ).all()
    counts = {
        int(rid): (int(active or 0), int(total or 0))
        for rid, active, total in count_rows
    }

    prov_rows = (
        await db.execute(
            select(
                MachineRunParticipant.machine_run_id,
                MachineRunParticipant.execution_plan_id,
                MachineRunParticipant.order_id,
            ).where(
                MachineRunParticipant.machine_run_id.in_(run_ids),
                MachineRunParticipant.status == "ACTIVE",
            )
        )
    ).all()
    plan_ids_by_run: dict[int, list[int]] = {rid: [] for rid in run_ids}
    order_ids_by_run: dict[int, list[int]] = {rid: [] for rid in run_ids}
    for rid, pid, oid in prov_rows:
        rid_i, pid_i, oid_i = int(rid), int(pid), int(oid)
        if pid_i not in plan_ids_by_run[rid_i]:
            plan_ids_by_run[rid_i].append(pid_i)
        if oid_i not in order_ids_by_run[rid_i]:
            order_ids_by_run[rid_i].append(oid_i)
    for rid in run_ids:
        plan_ids_by_run[rid].sort()
        order_ids_by_run[rid].sort()

    items: list[MachineRunListItem] = []
    for run, reservation in rows:
        rid = int(run.id)
        machine = machines.get(int(run.machine_id))
        active_count, total_count = counts.get(rid, (0, 0))
        items.append(
            MachineRunListItem(
                machine_run_id=rid,
                status=run.status,  # type: ignore[arg-type]
                version=int(run.version),
                machine_id=int(run.machine_id),
                machine_code=str(machine.machine_code) if machine else None,
                machine_name=str(machine.name) if machine else None,
                reservation_id=int(reservation.id),
                reservation_status=reservation.status,  # type: ignore[arg-type]
                reservation_version=int(reservation.version),
                reservation_start=reservation.reservation_start,
                reservation_end=reservation.reservation_end,
                timezone=str(run.timezone),
                active_participant_count=active_count,
                total_participant_count=total_count,
                execution_plan_ids=plan_ids_by_run.get(rid, []),
                order_ids=order_ids_by_run.get(rid, []),
                started_at=run.started_at,
                completed_at=run.completed_at,
                created_at=run.created_at,
                updated_at=run.updated_at,
            )
        )
    return MachineRunListResult(items=items, count=len(items))


async def get_machine_run(
    db: AsyncSession, *, machine_run_id: int
) -> MachineRunDetail:
    """Detail MachineRun with reservation, machine, and participant provenance."""
    if machine_run_id <= 0:
        raise ResourceStateNotFoundError(
            "machine_run_not_found", f"machine_run {machine_run_id} not found"
        )
    run = await db.get(MachineRun, machine_run_id)
    if run is None:
        raise ResourceStateNotFoundError(
            "machine_run_not_found", f"machine_run {machine_run_id} not found"
        )

    reservation = (
        await db.execute(
            select(ExecutionTaskMachineReservation).where(
                ExecutionTaskMachineReservation.machine_run_id == machine_run_id
            )
        )
    ).scalar_one_or_none()
    if reservation is None:
        raise ResourceStateNotFoundError(
            "reservation_not_found",
            f"run-owned reservation missing for machine_run {machine_run_id}",
        )

    machine = await db.get(MachineRegistry, int(run.machine_id))
    if machine is None:
        raise ResourceStateNotFoundError(
            "machine_not_found", f"machine_id {run.machine_id} not found"
        )

    parts = (
        await db.execute(
            select(MachineRunParticipant)
            .where(MachineRunParticipant.machine_run_id == machine_run_id)
            .order_by(
                case((MachineRunParticipant.status == "ACTIVE", 0), else_=1).asc(),
                MachineRunParticipant.execution_plan_id.asc(),
                MachineRunParticipant.task_key.asc(),
            )
        )
    ).scalars().all()

    plan_ids = sorted({int(p.execution_plan_id) for p in parts})
    plans = {
        int(pl.id): pl
        for pl in (
            await db.execute(
                select(ExecutionPlan).where(ExecutionPlan.id.in_(plan_ids))
            )
        ).scalars().all()
    } if plan_ids else {}
    task_maps = {pid: _task_lookup(pl) for pid, pl in plans.items()}

    participants: list[MachineRunParticipantRead] = []
    active_plan_ids: list[int] = []
    active_order_ids: list[int] = []
    active_count = 0
    for p in parts:
        task = task_maps.get(int(p.execution_plan_id), {}).get(str(p.task_key))
        participants.append(_participant_read(p, task))
        if p.status == "ACTIVE":
            active_count += 1
            if int(p.execution_plan_id) not in active_plan_ids:
                active_plan_ids.append(int(p.execution_plan_id))
            if int(p.order_id) not in active_order_ids:
                active_order_ids.append(int(p.order_id))
    active_plan_ids.sort()
    active_order_ids.sort()

    return MachineRunDetail(
        machine_run_id=int(run.id),
        status=run.status,  # type: ignore[arg-type]
        version=int(run.version),
        timezone=str(run.timezone),
        started_at=run.started_at,
        completed_at=run.completed_at,
        actual_runtime_seconds=_derived_runtime_seconds(
            run.started_at, run.completed_at
        ),
        created_at=run.created_at,
        updated_at=run.updated_at,
        created_by=run.created_by,
        updated_by=run.updated_by,
        machine=_machine_projection(machine),
        reservation=_reservation_projection(reservation),
        participants=participants,
        execution_plan_ids=active_plan_ids,
        order_ids=active_order_ids,
        active_participant_count=active_count,
        total_participant_count=len(parts),
    )
