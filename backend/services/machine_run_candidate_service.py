"""MACHINE_RUN candidate discovery + task→active-run lookup (read-only).

Eligibility predicates are shared with CREATE/ADD writers via
``machine_run_eligibility``. Query strategy: load ExecutionPlan rows filtered
by optional execution_plan_id / order_id (full scan of plans only when those
filters are absent — acceptable at current laboratory scale; no new indexes).
"""

from __future__ import annotations

from typing import Any

from models.execution_plan import ExecutionPlan
from models.execution_task_machine_reservation import ExecutionTaskMachineReservation
from models.machine_run import MachineRun, MachineRunParticipant
from models.operational_registry import MachineRegistry
from schemas.resource_state_machine_run_candidate import (
    ActiveMachineRunByTask,
    ActiveMachineRunByTaskResult,
    MachineRunCandidateListResult,
    MachineRunCandidateTask,
)
from services.execution_plan_task_parser import load_operational_tasks_from_plan_json
from services.machine_run_eligibility import (
    BLOCKING_MACHINE_RUN_STATUSES,
    TERMINAL_MACHINE_RUN_STATUSES,
    blocking_membership_keys,
    evaluate_demand_stamps,
    find_all_active_memberships,
    machine_capability_compatible,
    require_reservable_machine,
)
from services.resource_state_write_common import (
    ResourceStateNotFoundError,
    ResourceStateValidationError,
    ResourceStateWriteError,
    get_operational_task_from_plan,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Chip / lookup: same non-terminal set as CREATE/ADD blockers.
_ACTIVE_LOOKUP_RUN_STATUSES = BLOCKING_MACHINE_RUN_STATUSES
_TERMINAL_RUN_STATUSES = TERMINAL_MACHINE_RUN_STATUSES
_OPEN_RESERVATION_STATUSES = frozenset({"HELD", "RESERVED"})


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


def _task_label(task: dict[str, Any], task_key: str) -> str | None:
    for key in ("display_name", "label", "task_label", "name"):
        val = task.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    op = _operation_code_of(task)
    return op


async def _load_plans(
    db: AsyncSession,
    *,
    execution_plan_id: int | None,
    order_id: int | None,
) -> list[ExecutionPlan]:
    stmt = select(ExecutionPlan).order_by(ExecutionPlan.id.asc())
    if execution_plan_id is not None:
        if execution_plan_id <= 0:
            raise ResourceStateValidationError(
                "invalid_filter", "execution_plan_id must be > 0"
            )
        stmt = stmt.where(ExecutionPlan.id == execution_plan_id)
    if order_id is not None:
        if order_id <= 0:
            raise ResourceStateValidationError(
                "invalid_filter", "order_id must be > 0"
            )
        stmt = stmt.where(ExecutionPlan.order_id == order_id)
    return list((await db.execute(stmt)).scalars().all())


async def _active_membership_keys(
    db: AsyncSession,
) -> set[tuple[int, str]]:
    """Blocking keys only — terminal MachineRuns do not exclude candidates."""
    return await blocking_membership_keys(db)


async def _active_shared_capability_for_run(
    db: AsyncSession, machine_run_id: int
) -> str:
    """Same capability agreement rule as ADD writer (soft for empty ACTIVE)."""
    result = await db.execute(
        select(MachineRunParticipant).where(
            MachineRunParticipant.machine_run_id == machine_run_id,
            MachineRunParticipant.status == "ACTIVE",
        )
    )
    active = list(result.scalars().all())
    if not active:
        raise ResourceStateValidationError(
            "invalid_participant_set",
            "MACHINE_RUN has no ACTIVE participants",
        )
    shared: str | None = None
    for part in active:
        plan = await db.get(ExecutionPlan, part.execution_plan_id)
        if plan is None:
            raise ResourceStateNotFoundError(
                "execution_plan_not_found",
                f"plan {part.execution_plan_id} not found",
            )
        task = get_operational_task_from_plan(plan, part.task_key)
        ok, cap, reason = evaluate_demand_stamps(task)
        if not ok or cap is None:
            raise ResourceStateWriteError(
                reason or "run_reservation_state_mismatch",
                "ACTIVE participant demand stamps invalid",
            )
        if shared is None:
            shared = cap
        elif cap != shared:
            raise ResourceStateWriteError(
                "run_reservation_state_mismatch",
                f"ACTIVE participants disagree on capability "
                f"{shared!r} vs {cap!r}",
            )
    assert shared is not None
    return shared


def _candidate_from_task(
    *,
    plan: ExecutionPlan,
    task_key: str,
    task: dict[str, Any],
    capability: str,
) -> MachineRunCandidateTask:
    return MachineRunCandidateTask(
        execution_plan_id=int(plan.id),
        task_key=task_key,
        order_id=int(plan.order_id),
        operation_code=_operation_code_of(task),
        workcenter=_workcenter_of(task),
        resource_mode="MACHINE_BOUND",
        machine_capability_code=capability,
        batch_eligible=True,
        task_label=_task_label(task, task_key),
    )


async def list_create_candidates(
    db: AsyncSession,
    *,
    machine_id: int,
    execution_plan_id: int | None = None,
    order_id: int | None = None,
    operation_code: str | None = None,
) -> MachineRunCandidateListResult:
    """CREATE context — eligible tasks for a selected machine."""
    if machine_id <= 0:
        raise ResourceStateValidationError(
            "invalid_filter", "machine_id must be > 0"
        )
    machine = await require_reservable_machine(db, machine_id)
    plans = await _load_plans(
        db, execution_plan_id=execution_plan_id, order_id=order_id
    )
    active_keys = await _active_membership_keys(db)
    op_filter = operation_code.strip() if operation_code else None

    items: list[MachineRunCandidateTask] = []
    for plan in plans:
        tasks, parsed = load_operational_tasks_from_plan_json(plan.tasks_json or "")
        if parsed.format == "invalid":
            continue
        for entry in tasks:
            if not isinstance(entry, dict):
                continue
            tid = entry.get("task_id")
            if not isinstance(tid, str) or not tid.strip():
                continue
            task_key = tid.strip()
            if (int(plan.id), task_key) in active_keys:
                continue
            ok, cap, _reason = evaluate_demand_stamps(entry)
            if not ok or cap is None:
                continue
            if not machine_capability_compatible(machine, cap):
                continue
            if op_filter:
                op = _operation_code_of(entry)
                if op != op_filter:
                    continue
            items.append(
                _candidate_from_task(
                    plan=plan, task_key=task_key, task=entry, capability=cap
                )
            )

    items.sort(key=lambda c: (c.order_id, c.execution_plan_id, c.task_key))
    return MachineRunCandidateListResult(
        context="create",
        machine_id=int(machine.id),
        machine_code=str(machine.machine_code or "") or None,
        machine_name=str(machine.name or "") or None,
        mutation_allowed=True,
        items=items,
        count=len(items),
    )


async def list_add_candidates(
    db: AsyncSession,
    *,
    machine_run_id: int,
    execution_plan_id: int | None = None,
    order_id: int | None = None,
    operation_code: str | None = None,
) -> MachineRunCandidateListResult:
    """ADD context — candidates compatible with an existing HELD run."""
    if machine_run_id <= 0:
        raise ResourceStateValidationError(
            "invalid_filter", "machine_run_id must be > 0"
        )
    run = await db.get(MachineRun, machine_run_id)
    if run is None:
        raise ResourceStateNotFoundError(
            "machine_run_not_found", f"machine_run_id {machine_run_id} not found"
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
            f"no reservation for machine_run_id {machine_run_id}",
        )

    machine = await db.get(MachineRegistry, int(run.machine_id))
    machine_code = str(machine.machine_code) if machine else None
    machine_name = str(machine.name) if machine else None

    if run.status != "HELD" or reservation.status != "HELD":
        return MachineRunCandidateListResult(
            context="add",
            machine_id=int(run.machine_id),
            machine_run_id=int(run.id),
            machine_code=machine_code,
            machine_name=machine_name,
            mutation_allowed=False,
            reason_code="invalid_transition",
            message=(
                f"ADD candidates only when run/reservation are HELD "
                f"(run={run.status}, reservation={reservation.status})"
            ),
            items=[],
            count=0,
        )

    # Same reservable gate as ADD writer when mutating.
    machine = await require_reservable_machine(db, int(run.machine_id))
    required_capability = await _active_shared_capability_for_run(db, int(run.id))

    plans = await _load_plans(
        db, execution_plan_id=execution_plan_id, order_id=order_id
    )
    active_keys = await _active_membership_keys(db)
    # Already ACTIVE on this run are in active_keys → excluded (writer: already exists).
    op_filter = operation_code.strip() if operation_code else None

    items: list[MachineRunCandidateTask] = []
    for plan in plans:
        tasks, parsed = load_operational_tasks_from_plan_json(plan.tasks_json or "")
        if parsed.format == "invalid":
            continue
        for entry in tasks:
            if not isinstance(entry, dict):
                continue
            tid = entry.get("task_id")
            if not isinstance(tid, str) or not tid.strip():
                continue
            task_key = tid.strip()
            if (int(plan.id), task_key) in active_keys:
                continue
            ok, cap, _reason = evaluate_demand_stamps(entry)
            if not ok or cap is None:
                continue
            if cap != required_capability:
                continue
            if not machine_capability_compatible(machine, cap):
                continue
            if op_filter:
                op = _operation_code_of(entry)
                if op != op_filter:
                    continue
            items.append(
                _candidate_from_task(
                    plan=plan, task_key=task_key, task=entry, capability=cap
                )
            )

    items.sort(key=lambda c: (c.order_id, c.execution_plan_id, c.task_key))
    return MachineRunCandidateListResult(
        context="add",
        machine_id=int(machine.id),
        machine_run_id=int(run.id),
        machine_code=str(machine.machine_code or "") or None,
        machine_name=str(machine.name or "") or None,
        required_capability=required_capability,
        mutation_allowed=True,
        items=items,
        count=len(items),
    )


async def lookup_active_machine_run_by_task(
    db: AsyncSession,
    *,
    execution_plan_id: int,
    task_key: str,
) -> ActiveMachineRunByTaskResult:
    """Resolve ACTIVE participant → open MachineRun for secondary chips."""
    if execution_plan_id <= 0:
        raise ResourceStateValidationError(
            "invalid_filter", "execution_plan_id must be > 0"
        )
    key = (task_key or "").strip()
    if not key:
        raise ResourceStateValidationError(
            "invalid_filter", "task_key must be non-empty"
        )

    memberships = await find_all_active_memberships(
        db, execution_plan_id=execution_plan_id, task_key=key
    )
    if len(memberships) > 1:
        raise ResourceStateWriteError(
            "integrity_conflict",
            f"task ({execution_plan_id}, {key!r}) has "
            f"{len(memberships)} ACTIVE MachineRun memberships",
        )
    if not memberships:
        return ActiveMachineRunByTaskResult(membership=None)

    part = memberships[0]
    run = await db.get(MachineRun, int(part.machine_run_id))
    if run is None:
        raise ResourceStateWriteError(
            "integrity_conflict",
            f"ACTIVE participant references missing run {part.machine_run_id}",
        )
    if run.status in _TERMINAL_RUN_STATUSES:
        return ActiveMachineRunByTaskResult(membership=None)
    if run.status not in _ACTIVE_LOOKUP_RUN_STATUSES:
        return ActiveMachineRunByTaskResult(membership=None)

    reservation = (
        await db.execute(
            select(ExecutionTaskMachineReservation).where(
                ExecutionTaskMachineReservation.machine_run_id == run.id
            )
        )
    ).scalar_one_or_none()
    if reservation is None:
        raise ResourceStateWriteError(
            "integrity_conflict",
            f"run {run.id} has ACTIVE participant but no reservation",
        )
    # COMPLETED must still hold open reservation; HELD/RESERVED/RUNNING too.
    if reservation.status not in _OPEN_RESERVATION_STATUSES:
        return ActiveMachineRunByTaskResult(membership=None)

    machine = await db.get(MachineRegistry, int(run.machine_id))
    return ActiveMachineRunByTaskResult(
        membership=ActiveMachineRunByTask(
            machine_run_id=int(run.id),
            status=run.status,  # type: ignore[arg-type]
            machine_id=int(run.machine_id),
            machine_code=str(machine.machine_code) if machine else None,
            machine_name=str(machine.name) if machine else None,
            reservation_status=reservation.status,  # type: ignore[arg-type]
            execution_plan_id=int(part.execution_plan_id),
            task_key=str(part.task_key),
            order_id=int(part.order_id),
        )
    )
