"""MACHINE_RUN commands — CREATE + lifecycle + execution + RESCHEDULE + participants.

START/COMPLETE mutate MachineRun execution status only (reservation stays RESERVED).
No task state, employee session, assignment, PAUSE/RESUME, or auto-batch.
Participant mutation is HELD-only. RESERVED ≠ shop-floor RUNNING.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from models.execution_plan import ExecutionPlan
from models.execution_task_machine_reservation import (
    ExecutionTaskMachineReservation,
    ExecutionTaskMachineReservationTransition,
)
from models.machine_run import MachineRun, MachineRunParticipant, MachineRunTransition
from schemas.resource_state_machine_run import (
    AddMachineRunParticipantCommand,
    CancelMachineRunCommand,
    CompleteMachineRunCommand,
    ConfirmMachineRunCommand,
    CreateMachineRunCommand,
    CreateMachineRunResult,
    MachineRunParticipantResult,
    ReleaseMachineRunCommand,
    RemoveMachineRunParticipantCommand,
    RescheduleMachineRunCommand,
    StartMachineRunCommand,
)
from services.execution_task_machine_reservation_repository import (
    ExecutionTaskMachineReservationRepository,
)
from services.machine_run_eligibility import (
    demand_stamps as _demand_stamps,
    find_active_membership as _find_active_membership,
    require_reservable_machine as _require_reservable_machine,
    validate_machine_capability_join as _validate_machine_capability_join,
)
from services.resource_state_write_common import (
    ResourceStateNotFoundError,
    ResourceStateValidationError,
    ResourceStateWriteError,
    dt_key,
    get_operational_task_from_plan,
    load_plan_for_update,
    machine_lock,
    plan_order_lock,
    require_active_domain_config,
    utcnow,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

DOMAIN = "MACHINE_RESERVATION"
MIN_PARTICIPANTS = 2
OPERATION = "CREATE_MACHINE_RUN"
OWNER_FORM = "MACHINE_RUN"


def _validate_window(start: datetime, end: datetime) -> None:
    if end <= start:
        raise ResourceStateValidationError(
            "invalid_time_window",
            "reservation_end must be after reservation_start",
        )


def _canonicalize_participants(
    command: CreateMachineRunCommand,
) -> list[tuple[int, str]]:
    raw: list[tuple[int, str]] = []
    for p in command.participants:
        tid = (p.task_key or "").strip()
        if not tid:
            raise ResourceStateValidationError(
                "invalid_task_identity", "task_key is blank"
            )
        raw.append((int(p.execution_plan_id), tid))
    if len(raw) != len(set(raw)):
        raise ResourceStateValidationError(
            "duplicate_participant",
            "request contains duplicate (execution_plan_id, task_key)",
        )
    canonical = sorted(set(raw), key=lambda x: (x[0], x[1]))
    if len(canonical) < MIN_PARTICIPANTS:
        raise ResourceStateValidationError(
            "invalid_participant_set",
            f"CREATE_MACHINE_RUN requires at least {MIN_PARTICIPANTS} participants",
        )
    return canonical


async def _get_run_by_idempotency(
    db: AsyncSession, idempotency_key: str
) -> MachineRun | None:
    result = await db.execute(
        select(MachineRun).where(MachineRun.idempotency_key == idempotency_key)
    )
    return result.scalar_one_or_none()


async def _get_run_transition_by_idempotency(
    db: AsyncSession, idempotency_key: str
) -> MachineRunTransition | None:
    result = await db.execute(
        select(MachineRunTransition).where(
            MachineRunTransition.idempotency_key == idempotency_key
        )
    )
    return result.scalar_one_or_none()


async def _load_participants(
    db: AsyncSession, machine_run_id: int
) -> list[MachineRunParticipant]:
    result = await db.execute(
        select(MachineRunParticipant)
        .where(MachineRunParticipant.machine_run_id == machine_run_id)
        .order_by(
            MachineRunParticipant.execution_plan_id,
            MachineRunParticipant.task_key,
        )
    )
    return list(result.scalars().all())


async def _load_run_reservation(
    db: AsyncSession, machine_run_id: int
) -> ExecutionTaskMachineReservation | None:
    result = await db.execute(
        select(ExecutionTaskMachineReservation).where(
            ExecutionTaskMachineReservation.machine_run_id == machine_run_id
        )
    )
    return result.scalar_one_or_none()


def _fingerprint(
    *,
    command: CreateMachineRunCommand,
    participants: list[tuple[int, str]],
    actor_user_id: str,
) -> dict[str, Any]:
    return {
        "operation": OPERATION,
        "owner_form": OWNER_FORM,
        "machine_id": command.machine_id,
        "reservation_start": dt_key(command.reservation_start),
        "reservation_end": dt_key(command.reservation_end),
        "timezone": command.timezone,
        "expected_version": 0,
        "participants": [[pid, tk] for pid, tk in participants],
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
    }


def _transition_matches(
    tr: MachineRunTransition, fp: dict[str, Any], participants: list[tuple[int, str]]
) -> bool:
    # Participants are not stored on the run transition; match is completed
    # against loaded participant rows in the replay path.
    return (
        tr.operation == OPERATION
        and tr.machine_id == fp["machine_id"]
        and tr.new_status == "HELD"
        and tr.new_version == 1
        and (tr.reason_code or "") == fp["reason_code"]
        and (tr.reason_note or None) == fp["reason_note"]
        and (tr.actor_user_id or "") == fp["actor_user_id"]
    )


def _participant_result(p: MachineRunParticipant) -> MachineRunParticipantResult:
    return MachineRunParticipantResult(
        execution_plan_id=p.execution_plan_id,
        task_key=p.task_key,
        order_id=p.order_id,
        status=p.status,  # type: ignore[arg-type]
    )


async def _result_from_persisted(
    db: AsyncSession,
    *,
    run: MachineRun,
    transition_id: str,
    reservation_transition_id: str,
    already_applied: bool,
    operation: str = OPERATION,
    previous_status: str | None = None,
    previous_version: int | None = None,
    affected_participant: MachineRunParticipant | None = None,
) -> CreateMachineRunResult:
    reservation = await _load_run_reservation(db, run.id)
    if reservation is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "machine_run exists without run-owned reservation",
        )
    parts = await _load_participants(db, run.id)
    return CreateMachineRunResult(
        machine_run_id=run.id,
        status=run.status,  # type: ignore[arg-type]
        version=run.version,
        reservation_id=reservation.id,
        reservation_status=reservation.status,  # type: ignore[arg-type]
        reservation_version=reservation.version,
        machine_id=run.machine_id,
        reservation_start=reservation.reservation_start,
        reservation_end=reservation.reservation_end,
        timezone=run.timezone,
        participants=[_participant_result(p) for p in parts],
        operation=operation,  # type: ignore[arg-type]
        transition_id=transition_id,
        reservation_transition_id=reservation_transition_id,
        already_applied=already_applied,
        previous_status=previous_status,  # type: ignore[arg-type]
        previous_version=previous_version,
        affected_participant=(
            _participant_result(affected_participant)
            if affected_participant is not None
            else None
        ),
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


async def _idempotent_replay(
    db: AsyncSession,
    *,
    command: CreateMachineRunCommand,
    participants: list[tuple[int, str]],
    actor_user_id: str,
) -> CreateMachineRunResult | None:
    fp = _fingerprint(
        command=command, participants=participants, actor_user_id=actor_user_id
    )
    tr = await _get_run_transition_by_idempotency(db, command.idempotency_key)
    if tr is None:
        orphan_run = await _get_run_by_idempotency(db, command.idempotency_key)
        if orphan_run is not None:
            raise ResourceStateWriteError(
                "idempotency_orphaned_transition",
                "machine_run exists without CREATE transition",
            )
        return None

    if not _transition_matches(tr, fp, participants):
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )

    run = await db.get(MachineRun, tr.machine_run_id)
    if run is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "transition exists without machine_run row",
        )
    if (
        run.machine_id != fp["machine_id"]
        or run.timezone != fp["timezone"]
        or run.idempotency_key != command.idempotency_key
    ):
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )

    reservation = await _load_run_reservation(db, run.id)
    if reservation is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "machine_run exists without run-owned reservation",
        )
    if (
        dt_key(reservation.reservation_start) != fp["reservation_start"]
        or dt_key(reservation.reservation_end) != fp["reservation_end"]
        or reservation.machine_id != fp["machine_id"]
    ):
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )

    parts = await _load_participants(db, run.id)
    part_ids = sorted(
        [(p.execution_plan_id, p.task_key) for p in parts],
        key=lambda x: (x[0], x[1]),
    )
    if part_ids != participants:
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )

    res_repo = ExecutionTaskMachineReservationRepository(db)
    res_tr = await res_repo.get_transition_by_idempotency_key(command.idempotency_key)
    if res_tr is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "reservation transition missing for idempotent CREATE_MACHINE_RUN",
        )

    return await _result_from_persisted(
        db,
        run=run,
        transition_id=tr.transition_id,
        reservation_transition_id=res_tr.transition_id,
        already_applied=True,
    )


async def create_machine_run(
    db: AsyncSession,
    *,
    command: CreateMachineRunCommand,
    actor_user_id: str,
) -> CreateMachineRunResult:
    if command.expected_version != 0:
        raise ResourceStateWriteError(
            "cas_stale_or_missing",
            "CREATE_MACHINE_RUN requires expected_version=0",
        )
    _validate_window(command.reservation_start, command.reservation_end)
    participants = _canonicalize_participants(command)

    replay = await _idempotent_replay(
        db,
        command=command,
        participants=participants,
        actor_user_id=actor_user_id,
    )
    if replay is not None:
        return replay

    # Peek plans (existence) before locking.
    plan_ids = sorted({pid for pid, _ in participants})
    peek_orders: dict[int, int] = {}
    for plan_id in plan_ids:
        peek = await db.get(ExecutionPlan, plan_id)
        if peek is None:
            raise ResourceStateNotFoundError(
                "execution_plan_not_found",
                f"plan {plan_id} not found",
            )
        peek_orders[plan_id] = int(peek.order_id)

    order_ids = sorted(set(peek_orders.values()))

    async with machine_lock(command.machine_id):
        # Acquire plan-order locks in ascending order_id to reduce deadlock risk.
        async def _locked_create() -> CreateMachineRunResult:
            # Nested acquisition for each distinct order.
            async def _with_order_locks(idx: int) -> CreateMachineRunResult:
                if idx >= len(order_ids):
                    return await _create_under_locks(
                        db,
                        command=command,
                        participants=participants,
                        actor_user_id=actor_user_id,
                        plan_ids=plan_ids,
                    )
                async with plan_order_lock(order_ids[idx]):
                    return await _with_order_locks(idx + 1)

            return await _with_order_locks(0)

        try:
            return await _locked_create()
        except ResourceStateWriteError:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            raise


async def _create_under_locks(
    db: AsyncSession,
    *,
    command: CreateMachineRunCommand,
    participants: list[tuple[int, str]],
    actor_user_id: str,
    plan_ids: list[int],
) -> CreateMachineRunResult:
    replay = await _idempotent_replay(
        db,
        command=command,
        participants=participants,
        actor_user_id=actor_user_id,
    )
    if replay is not None:
        await db.commit()
        return replay

    await require_active_domain_config(db, domain=DOMAIN)
    machine = await _require_reservable_machine(db, command.machine_id)

    plans: dict[int, ExecutionPlan] = {}
    for plan_id in plan_ids:
        plans[plan_id] = await load_plan_for_update(db, plan_id=plan_id)

    resolved: list[tuple[int, str, int, str]] = []
    shared_capability: str | None = None
    for plan_id, task_key in participants:
        plan = plans[plan_id]
        task = get_operational_task_from_plan(plan, task_key)
        _mode, cap, _eligible = _demand_stamps(task)
        if shared_capability is None:
            shared_capability = cap
        elif cap != shared_capability:
            raise ResourceStateValidationError(
                "participant_capability_mismatch",
                f"participants require {shared_capability!r} and {cap!r}",
            )
        existing = await _find_active_membership(
            db, execution_plan_id=plan_id, task_key=task_key
        )
        if existing is not None:
            raise ResourceStateWriteError(
                "task_already_in_active_machine_run",
                f"task ({plan_id}, {task_key!r}) already ACTIVE in "
                f"machine_run_id={existing.machine_run_id}",
            )
        resolved.append((plan_id, task_key, int(plan.order_id), cap))

    assert shared_capability is not None
    _validate_machine_capability_join(machine, shared_capability)

    res_repo = ExecutionTaskMachineReservationRepository(db)
    overlap = await res_repo.find_overlapping_open(
        machine_id=command.machine_id,
        start=command.reservation_start,
        end=command.reservation_end,
    )
    if overlap is not None:
        raise ResourceStateWriteError(
            "overlap_conflict",
            f"overlaps reservation id={overlap.id}",
        )

    now = utcnow()
    try:
        run = MachineRun(
            machine_id=command.machine_id,
            status="HELD",
            version=1,
            timezone=command.timezone,
            created_by=actor_user_id,
            updated_by=actor_user_id,
            created_at=now,
            updated_at=now,
            idempotency_key=command.idempotency_key,
        )
        db.add(run)
        await db.flush()

        reservation = ExecutionTaskMachineReservation(
            execution_plan_id=None,
            order_id=None,
            task_key=None,
            machine_run_id=run.id,
            machine_id=command.machine_id,
            reservation_start=command.reservation_start,
            reservation_end=command.reservation_end,
            timezone=command.timezone,
            status="HELD",
            version=1,
            created_by=actor_user_id,
            updated_by=actor_user_id,
            created_at=now,
            updated_at=now,
            idempotency_key=command.idempotency_key,
        )
        await res_repo.add_reservation(reservation)

        for plan_id, task_key, order_id, _cap in resolved:
            db.add(
                MachineRunParticipant(
                    machine_run_id=run.id,
                    execution_plan_id=plan_id,
                    order_id=order_id,
                    task_key=task_key,
                    status="ACTIVE",
                    added_at=now,
                    added_by=actor_user_id,
                    idempotency_key=None,
                )
            )
        await db.flush()

        run_tr = MachineRunTransition(
            transition_id=str(uuid.uuid4()),
            machine_run_id=run.id,
            machine_id=command.machine_id,
            operation=OPERATION,
            previous_status=None,
            new_status="HELD",
            previous_version=None,
            new_version=1,
            reason_code=command.reason_code,
            reason_note=command.reason_note,
            actor_user_id=actor_user_id,
            idempotency_key=command.idempotency_key,
            correlation_id=command.correlation_id,
            created_at=now,
        )
        db.add(run_tr)
        await db.flush()

        res_tr = ExecutionTaskMachineReservationTransition(
            transition_id=str(uuid.uuid4()),
            reservation_id=reservation.id,
            owner_form=OWNER_FORM,
            execution_plan_id=None,
            task_key=None,
            machine_run_id=run.id,
            machine_id=command.machine_id,
            operation="CREATE_RESERVATION",
            previous_status=None,
            new_status="HELD",
            previous_start=None,
            previous_end=None,
            new_start=command.reservation_start,
            new_end=command.reservation_end,
            previous_version=None,
            new_version=1,
            reason_code=command.reason_code,
            reason_note=command.reason_note,
            actor_user_id=actor_user_id,
            idempotency_key=command.idempotency_key,
            correlation_id=command.correlation_id,
            created_at=now,
        )
        await res_repo.add_transition(res_tr)
        await db.commit()
    except IntegrityError as ie:
        await db.rollback()
        # Membership uniqueness / idempotency races collapse to typed conflicts.
        msg = str(getattr(ie, "orig", ie)).lower()
        if "idempotency" in msg:
            raise ResourceStateWriteError(
                "idempotency_payload_conflict",
                "idempotency_key uniqueness conflict",
            ) from ie
        if "active" in msg or "participant" in msg:
            raise ResourceStateWriteError(
                "task_already_in_active_machine_run",
                "active participant uniqueness conflict",
            ) from ie
        raise ResourceStateWriteError(
            "open_row_conflict",
            "machine_run create uniqueness conflict",
        ) from ie

    return await _result_from_persisted(
        db,
        run=run,
        transition_id=run_tr.transition_id,
        reservation_transition_id=res_tr.transition_id,
        already_applied=False,
    )


# ---------------------------------------------------------------------------
# CONFIRM / RELEASE / CANCEL — reservation lifecycle
# START / COMPLETE — shop-floor execution (reservation stays RESERVED)
# ---------------------------------------------------------------------------

TERMINAL = frozenset({"CANCELLED", "RELEASED", "SUPERSEDED"})

# Phase-aware run/reservation pairs (status equality is not required after START).
COUPLED_STATUS_PAIRS = frozenset(
    {
        ("HELD", "HELD"),
        ("RESERVED", "RESERVED"),
        ("RUNNING", "RESERVED"),
        ("COMPLETED", "RESERVED"),
        ("RELEASED", "RELEASED"),
        ("CANCELLED", "CANCELLED"),
        ("SUPERSEDED", "SUPERSEDED"),
    }
)

_LifecycleCommand = (
    ConfirmMachineRunCommand | ReleaseMachineRunCommand | CancelMachineRunCommand
)
_ExecutionCommand = StartMachineRunCommand | CompleteMachineRunCommand


async def _load_run_for_update(db: AsyncSession, machine_run_id: int) -> MachineRun:
    result = await db.execute(
        select(MachineRun)
        .where(MachineRun.id == machine_run_id)
        .with_for_update()
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise ResourceStateNotFoundError(
            "machine_run_not_found", f"machine_run {machine_run_id} not found"
        )
    return run


async def _load_run_reservation_for_update(
    db: AsyncSession, machine_run_id: int
) -> ExecutionTaskMachineReservation:
    result = await db.execute(
        select(ExecutionTaskMachineReservation)
        .where(ExecutionTaskMachineReservation.machine_run_id == machine_run_id)
        .with_for_update()
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise ResourceStateNotFoundError(
            "reservation_not_found",
            f"run-owned reservation missing for machine_run {machine_run_id}",
        )
    return row


def _assert_coupled(
    run: MachineRun, reservation: ExecutionTaskMachineReservation
) -> None:
    pair = (run.status, reservation.status)
    if pair not in COUPLED_STATUS_PAIRS or run.version != reservation.version:
        raise ResourceStateWriteError(
            "run_reservation_state_mismatch",
            f"run status={run.status!r} v={run.version} "
            f"reservation status={reservation.status!r} v={reservation.version}",
        )


async def _lifecycle_idempotent_replay(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: _LifecycleCommand,
    actor_user_id: str,
    operation: str,
    target_status: str,
) -> CreateMachineRunResult | None:
    tr = await _get_run_transition_by_idempotency(db, command.idempotency_key)
    if tr is None:
        return None
    match = (
        tr.operation == operation
        and tr.machine_run_id == machine_run_id
        and tr.previous_version == command.expected_version
        and tr.new_status == target_status
        and (tr.reason_code or "") == command.reason_code
        and (tr.reason_note or None) == command.reason_note
        and (tr.actor_user_id or "") == actor_user_id
    )
    if not match:
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )
    run = await db.get(MachineRun, machine_run_id)
    if run is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "transition exists without machine_run row",
        )
    res_repo = ExecutionTaskMachineReservationRepository(db)
    res_tr = await res_repo.get_transition_by_idempotency_key(command.idempotency_key)
    if res_tr is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "reservation transition missing for idempotent lifecycle command",
        )
    return await _result_from_persisted(
        db,
        run=run,
        transition_id=tr.transition_id,
        reservation_transition_id=res_tr.transition_id,
        already_applied=True,
        operation=operation,
        previous_status=tr.previous_status,
        previous_version=tr.previous_version,
    )


async def _mutate_machine_run_lifecycle(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: _LifecycleCommand,
    actor_user_id: str,
    operation: str,
    reservation_operation: str,
    target_status: str,
    allowed_sources: frozenset[str],
    stamp_fn: Callable[[MachineRun, ExecutionTaskMachineReservation, datetime], None],
) -> CreateMachineRunResult:
    replay = await _lifecycle_idempotent_replay(
        db,
        machine_run_id=machine_run_id,
        command=command,
        actor_user_id=actor_user_id,
        operation=operation,
        target_status=target_status,
    )
    if replay is not None:
        return replay

    peek = await db.get(MachineRun, machine_run_id)
    if peek is None:
        raise ResourceStateNotFoundError(
            "machine_run_not_found", f"machine_run {machine_run_id} not found"
        )

    async with machine_lock(int(peek.machine_id)):
        try:
            replay = await _lifecycle_idempotent_replay(
                db,
                machine_run_id=machine_run_id,
                command=command,
                actor_user_id=actor_user_id,
                operation=operation,
                target_status=target_status,
            )
            if replay is not None:
                await db.commit()
                return replay

            await require_active_domain_config(db, domain=DOMAIN)
            run = await _load_run_for_update(db, machine_run_id)
            reservation = await _load_run_reservation_for_update(db, machine_run_id)
            _assert_coupled(run, reservation)

            if run.version != command.expected_version:
                raise ResourceStateWriteError(
                    "cas_stale",
                    f"expected_version={command.expected_version} "
                    f"current={run.version}",
                )
            if run.status in TERMINAL:
                raise ResourceStateWriteError(
                    "invalid_transition",
                    f"terminal machine_run status {run.status}",
                )
            if run.status not in allowed_sources:
                raise ResourceStateWriteError(
                    "invalid_transition",
                    f"{operation} not allowed from {run.status}",
                )

            prev_run_status = run.status
            prev_res_status = reservation.status
            prev_ver = run.version
            now = utcnow()
            window_start = reservation.reservation_start
            window_end = reservation.reservation_end
            machine_id = run.machine_id

            run.status = target_status
            run.version = prev_ver + 1
            run.updated_by = actor_user_id
            run.updated_at = now
            reservation.status = target_status
            reservation.version = prev_ver + 1
            reservation.updated_by = actor_user_id
            reservation.updated_at = now
            stamp_fn(run, reservation, now)

            run_tr = MachineRunTransition(
                transition_id=str(uuid.uuid4()),
                machine_run_id=run.id,
                machine_id=machine_id,
                operation=operation,
                previous_status=prev_run_status,
                new_status=target_status,
                previous_version=prev_ver,
                new_version=run.version,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
                actor_user_id=actor_user_id,
                idempotency_key=command.idempotency_key,
                correlation_id=command.correlation_id,
                created_at=now,
            )
            db.add(run_tr)
            await db.flush()

            res_repo = ExecutionTaskMachineReservationRepository(db)
            res_tr = ExecutionTaskMachineReservationTransition(
                transition_id=str(uuid.uuid4()),
                reservation_id=reservation.id,
                owner_form=OWNER_FORM,
                execution_plan_id=None,
                task_key=None,
                machine_run_id=run.id,
                machine_id=machine_id,
                operation=reservation_operation,
                previous_status=prev_res_status,
                new_status=target_status,
                previous_start=window_start,
                previous_end=window_end,
                new_start=window_start,
                new_end=window_end,
                previous_version=prev_ver,
                new_version=reservation.version,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
                actor_user_id=actor_user_id,
                idempotency_key=command.idempotency_key,
                correlation_id=command.correlation_id,
                created_at=now,
            )
            await res_repo.add_transition(res_tr)
            await db.commit()
        except ResourceStateWriteError:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            raise

    return await _result_from_persisted(
        db,
        run=run,
        transition_id=run_tr.transition_id,
        reservation_transition_id=res_tr.transition_id,
        already_applied=False,
        operation=operation,
        previous_status=prev_run_status,
        previous_version=prev_ver,
    )


async def confirm_machine_run(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: ConfirmMachineRunCommand,
    actor_user_id: str,
) -> CreateMachineRunResult:
    def stamp(
        run: MachineRun, reservation: ExecutionTaskMachineReservation, _now: datetime
    ) -> None:
        return None

    return await _mutate_machine_run_lifecycle(
        db,
        machine_run_id=machine_run_id,
        command=command,
        actor_user_id=actor_user_id,
        operation="CONFIRM_MACHINE_RUN",
        reservation_operation="CONFIRM_RESERVATION",
        target_status="RESERVED",
        allowed_sources=frozenset({"HELD"}),
        stamp_fn=stamp,
    )


async def release_machine_run(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: ReleaseMachineRunCommand,
    actor_user_id: str,
) -> CreateMachineRunResult:
    def stamp(
        run: MachineRun, reservation: ExecutionTaskMachineReservation, now: datetime
    ) -> None:
        run.released_at = now
        run.released_by = actor_user_id
        reservation.released_at = now
        reservation.released_by = actor_user_id

    return await _mutate_machine_run_lifecycle(
        db,
        machine_run_id=machine_run_id,
        command=command,
        actor_user_id=actor_user_id,
        operation="RELEASE_MACHINE_RUN",
        reservation_operation="RELEASE_RESERVATION",
        target_status="RELEASED",
        allowed_sources=frozenset({"RESERVED", "COMPLETED"}),
        stamp_fn=stamp,
    )


async def cancel_machine_run(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: CancelMachineRunCommand,
    actor_user_id: str,
) -> CreateMachineRunResult:
    def stamp(
        run: MachineRun, reservation: ExecutionTaskMachineReservation, now: datetime
    ) -> None:
        run.cancelled_at = now
        run.cancelled_by = actor_user_id
        reservation.cancelled_at = now
        reservation.cancelled_by = actor_user_id

    return await _mutate_machine_run_lifecycle(
        db,
        machine_run_id=machine_run_id,
        command=command,
        actor_user_id=actor_user_id,
        operation="CANCEL_MACHINE_RUN",
        reservation_operation="CANCEL_RESERVATION",
        target_status="CANCELLED",
        allowed_sources=frozenset({"HELD", "RESERVED"}),
        stamp_fn=stamp,
    )


async def _execution_idempotent_replay(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: _ExecutionCommand,
    actor_user_id: str,
    operation: str,
    target_run_status: str,
) -> CreateMachineRunResult | None:
    tr = await _get_run_transition_by_idempotency(db, command.idempotency_key)
    if tr is None:
        return None
    match = (
        tr.operation == operation
        and tr.machine_run_id == machine_run_id
        and tr.previous_version == command.expected_version
        and tr.new_status == target_run_status
        and (tr.reason_code or "") == command.reason_code
        and (tr.reason_note or None) == command.reason_note
        and (tr.actor_user_id or "") == actor_user_id
    )
    if not match:
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )
    run = await db.get(MachineRun, machine_run_id)
    if run is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "transition exists without machine_run row",
        )
    res_repo = ExecutionTaskMachineReservationRepository(db)
    res_tr = await res_repo.get_transition_by_idempotency_key(command.idempotency_key)
    if res_tr is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "reservation transition missing for idempotent execution command",
        )
    return await _result_from_persisted(
        db,
        run=run,
        transition_id=tr.transition_id,
        reservation_transition_id=res_tr.transition_id,
        already_applied=True,
        operation=operation,
        previous_status=tr.previous_status,
        previous_version=tr.previous_version,
    )


async def _mutate_machine_run_execution(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: _ExecutionCommand,
    actor_user_id: str,
    operation: str,
    source_run_status: str,
    target_run_status: str,
    required_reservation_status: str,
    stamp_fn: Callable[[MachineRun, datetime], None],
) -> CreateMachineRunResult:
    """START/COMPLETE: run status changes; reservation status stays RESERVED; dual bump."""
    replay = await _execution_idempotent_replay(
        db,
        machine_run_id=machine_run_id,
        command=command,
        actor_user_id=actor_user_id,
        operation=operation,
        target_run_status=target_run_status,
    )
    if replay is not None:
        return replay

    peek = await db.get(MachineRun, machine_run_id)
    if peek is None:
        raise ResourceStateNotFoundError(
            "machine_run_not_found", f"machine_run {machine_run_id} not found"
        )

    async with machine_lock(int(peek.machine_id)):
        try:
            replay = await _execution_idempotent_replay(
                db,
                machine_run_id=machine_run_id,
                command=command,
                actor_user_id=actor_user_id,
                operation=operation,
                target_run_status=target_run_status,
            )
            if replay is not None:
                await db.commit()
                return replay

            await require_active_domain_config(db, domain=DOMAIN)
            run = await _load_run_for_update(db, machine_run_id)
            reservation = await _load_run_reservation_for_update(db, machine_run_id)
            _assert_coupled(run, reservation)

            if run.version != command.expected_version:
                raise ResourceStateWriteError(
                    "cas_stale",
                    f"expected_version={command.expected_version} "
                    f"current={run.version}",
                )
            if run.status in TERMINAL:
                raise ResourceStateWriteError(
                    "invalid_transition",
                    f"terminal machine_run status {run.status}",
                )
            if (
                run.status != source_run_status
                or reservation.status != required_reservation_status
            ):
                raise ResourceStateWriteError(
                    "invalid_transition",
                    f"{operation} requires run={source_run_status}/"
                    f"reservation={required_reservation_status}; "
                    f"got run={run.status}/reservation={reservation.status}",
                )

            prev_run_status = run.status
            prev_res_status = reservation.status
            prev_ver = run.version
            now = utcnow()
            window_start = reservation.reservation_start
            window_end = reservation.reservation_end
            machine_id = run.machine_id

            run.status = target_run_status
            run.version = prev_ver + 1
            run.updated_by = actor_user_id
            run.updated_at = now
            stamp_fn(run, now)

            # Reservation status unchanged; version bumps for coupling invariant.
            reservation.version = prev_ver + 1
            reservation.updated_by = actor_user_id
            reservation.updated_at = now

            run_tr = MachineRunTransition(
                transition_id=str(uuid.uuid4()),
                machine_run_id=run.id,
                machine_id=machine_id,
                operation=operation,
                previous_status=prev_run_status,
                new_status=target_run_status,
                previous_version=prev_ver,
                new_version=run.version,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
                actor_user_id=actor_user_id,
                idempotency_key=command.idempotency_key,
                correlation_id=command.correlation_id,
                created_at=now,
            )
            db.add(run_tr)
            await db.flush()

            res_repo = ExecutionTaskMachineReservationRepository(db)
            res_tr = ExecutionTaskMachineReservationTransition(
                transition_id=str(uuid.uuid4()),
                reservation_id=reservation.id,
                owner_form=OWNER_FORM,
                execution_plan_id=None,
                task_key=None,
                machine_run_id=run.id,
                machine_id=machine_id,
                operation=operation,
                previous_status=prev_res_status,
                new_status=prev_res_status,
                previous_start=window_start,
                previous_end=window_end,
                new_start=window_start,
                new_end=window_end,
                previous_version=prev_ver,
                new_version=reservation.version,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
                actor_user_id=actor_user_id,
                idempotency_key=command.idempotency_key,
                correlation_id=command.correlation_id,
                created_at=now,
            )
            await res_repo.add_transition(res_tr)
            await db.commit()
        except ResourceStateWriteError:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            raise

    return await _result_from_persisted(
        db,
        run=run,
        transition_id=run_tr.transition_id,
        reservation_transition_id=res_tr.transition_id,
        already_applied=False,
        operation=operation,
        previous_status=prev_run_status,
        previous_version=prev_ver,
    )


async def start_machine_run(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: StartMachineRunCommand,
    actor_user_id: str,
) -> CreateMachineRunResult:
    def stamp(run: MachineRun, now: datetime) -> None:
        run.started_at = now

    return await _mutate_machine_run_execution(
        db,
        machine_run_id=machine_run_id,
        command=command,
        actor_user_id=actor_user_id,
        operation="START_MACHINE_RUN",
        source_run_status="RESERVED",
        target_run_status="RUNNING",
        required_reservation_status="RESERVED",
        stamp_fn=stamp,
    )


async def complete_machine_run(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: CompleteMachineRunCommand,
    actor_user_id: str,
) -> CreateMachineRunResult:
    def stamp(run: MachineRun, now: datetime) -> None:
        run.completed_at = now

    return await _mutate_machine_run_execution(
        db,
        machine_run_id=machine_run_id,
        command=command,
        actor_user_id=actor_user_id,
        operation="COMPLETE_MACHINE_RUN",
        source_run_status="RUNNING",
        target_run_status="COMPLETED",
        required_reservation_status="RESERVED",
        stamp_fn=stamp,
    )


# ---------------------------------------------------------------------------
# RESCHEDULE — same machine / participants / status; new window only
# ---------------------------------------------------------------------------

OPEN_RESCHEDULE = frozenset({"HELD", "RESERVED"})


async def _reschedule_idempotent_replay(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: RescheduleMachineRunCommand,
    actor_user_id: str,
) -> CreateMachineRunResult | None:
    tr = await _get_run_transition_by_idempotency(db, command.idempotency_key)
    if tr is None:
        return None
    match = (
        tr.operation == "RESCHEDULE_MACHINE_RUN"
        and tr.machine_run_id == machine_run_id
        and tr.previous_version == command.expected_version
        and tr.previous_status == tr.new_status
        and tr.new_status in OPEN_RESCHEDULE
        and (tr.reason_code or "") == command.reason_code
        and (tr.reason_note or None) == command.reason_note
        and (tr.actor_user_id or "") == actor_user_id
    )
    if not match:
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )
    res_repo = ExecutionTaskMachineReservationRepository(db)
    res_tr = await res_repo.get_transition_by_idempotency_key(command.idempotency_key)
    if res_tr is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "reservation transition missing for idempotent RESCHEDULE",
        )
    if (
        dt_key(res_tr.new_start) != dt_key(command.reservation_start)
        or dt_key(res_tr.new_end) != dt_key(command.reservation_end)
        or res_tr.operation != "RESCHEDULE_RESERVATION"
    ):
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )
    run = await db.get(MachineRun, machine_run_id)
    if run is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "transition exists without machine_run row",
        )
    return await _result_from_persisted(
        db,
        run=run,
        transition_id=tr.transition_id,
        reservation_transition_id=res_tr.transition_id,
        already_applied=True,
        operation="RESCHEDULE_MACHINE_RUN",
        previous_status=tr.previous_status,
        previous_version=tr.previous_version,
    )


async def reschedule_machine_run(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: RescheduleMachineRunCommand,
    actor_user_id: str,
) -> CreateMachineRunResult:
    _validate_window(command.reservation_start, command.reservation_end)

    replay = await _reschedule_idempotent_replay(
        db,
        machine_run_id=machine_run_id,
        command=command,
        actor_user_id=actor_user_id,
    )
    if replay is not None:
        return replay

    peek = await db.get(MachineRun, machine_run_id)
    if peek is None:
        raise ResourceStateNotFoundError(
            "machine_run_not_found", f"machine_run {machine_run_id} not found"
        )

    async with machine_lock(int(peek.machine_id)):
        try:
            replay = await _reschedule_idempotent_replay(
                db,
                machine_run_id=machine_run_id,
                command=command,
                actor_user_id=actor_user_id,
            )
            if replay is not None:
                await db.commit()
                return replay

            await require_active_domain_config(db, domain=DOMAIN)
            run = await _load_run_for_update(db, machine_run_id)
            reservation = await _load_run_reservation_for_update(db, machine_run_id)
            _assert_coupled(run, reservation)

            if run.version != command.expected_version:
                raise ResourceStateWriteError(
                    "cas_stale",
                    f"expected_version={command.expected_version} "
                    f"current={run.version}",
                )
            if run.status in TERMINAL or run.status not in OPEN_RESCHEDULE:
                raise ResourceStateWriteError(
                    "invalid_transition",
                    f"RESCHEDULE_MACHINE_RUN not allowed from {run.status}",
                )

            res_repo = ExecutionTaskMachineReservationRepository(db)
            overlap = await res_repo.find_overlapping_open(
                machine_id=run.machine_id,
                start=command.reservation_start,
                end=command.reservation_end,
                exclude_id=reservation.id,
            )
            if overlap is not None:
                raise ResourceStateWriteError(
                    "overlap_conflict",
                    f"overlaps reservation id={overlap.id}",
                )

            prev_status = run.status
            prev_ver = run.version
            prev_start = reservation.reservation_start
            prev_end = reservation.reservation_end
            now = utcnow()

            reservation.reservation_start = command.reservation_start
            reservation.reservation_end = command.reservation_end
            reservation.timezone = command.timezone
            reservation.version = prev_ver + 1
            reservation.updated_by = actor_user_id
            reservation.updated_at = now

            run.timezone = command.timezone
            run.version = prev_ver + 1
            run.updated_by = actor_user_id
            run.updated_at = now
            # status unchanged on both

            run_tr = MachineRunTransition(
                transition_id=str(uuid.uuid4()),
                machine_run_id=run.id,
                machine_id=run.machine_id,
                operation="RESCHEDULE_MACHINE_RUN",
                previous_status=prev_status,
                new_status=prev_status,
                previous_version=prev_ver,
                new_version=run.version,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
                actor_user_id=actor_user_id,
                idempotency_key=command.idempotency_key,
                correlation_id=command.correlation_id,
                created_at=now,
            )
            db.add(run_tr)
            await db.flush()

            res_tr = ExecutionTaskMachineReservationTransition(
                transition_id=str(uuid.uuid4()),
                reservation_id=reservation.id,
                owner_form=OWNER_FORM,
                execution_plan_id=None,
                task_key=None,
                machine_run_id=run.id,
                machine_id=run.machine_id,
                operation="RESCHEDULE_RESERVATION",
                previous_status=prev_status,
                new_status=prev_status,
                previous_start=prev_start,
                previous_end=prev_end,
                new_start=command.reservation_start,
                new_end=command.reservation_end,
                previous_version=prev_ver,
                new_version=reservation.version,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
                actor_user_id=actor_user_id,
                idempotency_key=command.idempotency_key,
                correlation_id=command.correlation_id,
                created_at=now,
            )
            await res_repo.add_transition(res_tr)
            await db.commit()
        except ResourceStateWriteError:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            raise

    return await _result_from_persisted(
        db,
        run=run,
        transition_id=run_tr.transition_id,
        reservation_transition_id=res_tr.transition_id,
        already_applied=False,
        operation="RESCHEDULE_MACHINE_RUN",
        previous_status=prev_status,
        previous_version=prev_ver,
    )


# ---------------------------------------------------------------------------
# ADD / REMOVE participant — HELD only; soft REMOVED; version lockstep
# ---------------------------------------------------------------------------

PARTICIPANT_MUTATION_LOCKSTEP_OP = "MACHINE_RUN_PARTICIPANT_MUTATION_LOCKSTEP"
_ParticipantMutationCommand = (
    AddMachineRunParticipantCommand | RemoveMachineRunParticipantCommand
)


def _normalize_task_key(task_key: str) -> str:
    tid = (task_key or "").strip()
    if not tid:
        raise ResourceStateValidationError(
            "invalid_task_identity", "task_key is blank"
        )
    return tid


async def _find_membership_on_run(
    db: AsyncSession,
    *,
    machine_run_id: int,
    execution_plan_id: int,
    task_key: str,
) -> MachineRunParticipant | None:
    result = await db.execute(
        select(MachineRunParticipant).where(
            MachineRunParticipant.machine_run_id == machine_run_id,
            MachineRunParticipant.execution_plan_id == execution_plan_id,
            MachineRunParticipant.task_key == task_key,
        )
    )
    return result.scalar_one_or_none()


async def _count_active_participants(
    db: AsyncSession, machine_run_id: int
) -> int:
    result = await db.execute(
        select(MachineRunParticipant).where(
            MachineRunParticipant.machine_run_id == machine_run_id,
            MachineRunParticipant.status == "ACTIVE",
        )
    )
    return len(list(result.scalars().all()))


async def _active_shared_capability(
    db: AsyncSession, machine_run_id: int
) -> str:
    result = await db.execute(
        select(MachineRunParticipant).where(
            MachineRunParticipant.machine_run_id == machine_run_id,
            MachineRunParticipant.status == "ACTIVE",
        )
    )
    active = list(result.scalars().all())
    if not active:
        raise ResourceStateWriteError(
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
        _mode, cap, _eligible = _demand_stamps(task)
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


async def _find_participant_by_idempotency(
    db: AsyncSession, idempotency_key: str
) -> MachineRunParticipant | None:
    result = await db.execute(
        select(MachineRunParticipant).where(
            MachineRunParticipant.idempotency_key == idempotency_key
        )
    )
    return result.scalar_one_or_none()


async def _participant_mutation_idempotent_replay(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: _ParticipantMutationCommand,
    actor_user_id: str,
    operation: str,
    expected_status: str,
) -> CreateMachineRunResult | None:
    """Replay ADD/REMOVE. Participant identity is matched structurally.

    ADD stamps ``participant.idempotency_key`` (not overwritten by REMOVE) so
    same-key/different-task conflicts are detectable. REMOVE matches membership
    on ``(run, plan, task)`` plus ``REMOVED`` status.
    """
    tr = await _get_run_transition_by_idempotency(db, command.idempotency_key)
    if tr is None:
        return None
    task_key = _normalize_task_key(command.task_key)
    match = (
        tr.operation == operation
        and tr.machine_run_id == machine_run_id
        and tr.previous_version == command.expected_version
        and tr.previous_status == "HELD"
        and tr.new_status == "HELD"
        and (tr.reason_code or "") == command.reason_code
        and (tr.reason_note or None) == command.reason_note
        and (tr.actor_user_id or "") == actor_user_id
    )
    if not match:
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )

    if operation == "ADD_MACHINE_RUN_PARTICIPANT":
        part = await _find_participant_by_idempotency(db, command.idempotency_key)
        if (
            part is None
            or part.machine_run_id != machine_run_id
            or part.execution_plan_id != command.execution_plan_id
            or part.task_key != task_key
        ):
            raise ResourceStateWriteError(
                "idempotency_payload_conflict",
                "idempotency_key already used with a different payload",
            )
        # Status may later be REMOVED; still already_applied for this ADD key.
    else:
        part = await _find_membership_on_run(
            db,
            machine_run_id=machine_run_id,
            execution_plan_id=command.execution_plan_id,
            task_key=task_key,
        )
        if part is None or part.status != expected_status:
            raise ResourceStateWriteError(
                "idempotency_payload_conflict",
                "idempotency_key already used with a different payload",
            )

    res_repo = ExecutionTaskMachineReservationRepository(db)
    res_tr = await res_repo.get_transition_by_idempotency_key(command.idempotency_key)
    if res_tr is None or res_tr.operation != PARTICIPANT_MUTATION_LOCKSTEP_OP:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "reservation lockstep transition missing for participant mutation",
        )
    run = await db.get(MachineRun, machine_run_id)
    if run is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "transition exists without machine_run row",
        )
    return await _result_from_persisted(
        db,
        run=run,
        transition_id=tr.transition_id,
        reservation_transition_id=res_tr.transition_id,
        already_applied=True,
        operation=operation,
        previous_status=tr.previous_status,
        previous_version=tr.previous_version,
        affected_participant=part,
    )


async def _append_participant_mutation_histories(
    db: AsyncSession,
    *,
    run: MachineRun,
    reservation: ExecutionTaskMachineReservation,
    command: _ParticipantMutationCommand,
    actor_user_id: str,
    operation: str,
    prev_ver: int,
    now: datetime,
) -> tuple[MachineRunTransition, ExecutionTaskMachineReservationTransition]:
    run_tr = MachineRunTransition(
        transition_id=str(uuid.uuid4()),
        machine_run_id=run.id,
        machine_id=run.machine_id,
        operation=operation,
        previous_status="HELD",
        new_status="HELD",
        previous_version=prev_ver,
        new_version=run.version,
        reason_code=command.reason_code,
        reason_note=command.reason_note,
        actor_user_id=actor_user_id,
        idempotency_key=command.idempotency_key,
        correlation_id=command.correlation_id,
        created_at=now,
    )
    db.add(run_tr)
    await db.flush()

    res_repo = ExecutionTaskMachineReservationRepository(db)
    res_tr = ExecutionTaskMachineReservationTransition(
        transition_id=str(uuid.uuid4()),
        reservation_id=reservation.id,
        owner_form=OWNER_FORM,
        execution_plan_id=None,
        task_key=None,
        machine_run_id=run.id,
        machine_id=run.machine_id,
        operation=PARTICIPANT_MUTATION_LOCKSTEP_OP,
        previous_status="HELD",
        new_status="HELD",
        previous_start=reservation.reservation_start,
        previous_end=reservation.reservation_end,
        new_start=reservation.reservation_start,
        new_end=reservation.reservation_end,
        previous_version=prev_ver,
        new_version=reservation.version,
        reason_code=command.reason_code,
        reason_note=command.reason_note,
        actor_user_id=actor_user_id,
        idempotency_key=command.idempotency_key,
        correlation_id=command.correlation_id,
        created_at=now,
    )
    await res_repo.add_transition(res_tr)
    return run_tr, res_tr


async def add_machine_run_participant(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: AddMachineRunParticipantCommand,
    actor_user_id: str,
) -> CreateMachineRunResult:
    task_key = _normalize_task_key(command.task_key)
    operation = "ADD_MACHINE_RUN_PARTICIPANT"

    replay = await _participant_mutation_idempotent_replay(
        db,
        machine_run_id=machine_run_id,
        command=command,
        actor_user_id=actor_user_id,
        operation=operation,
        expected_status="ACTIVE",
    )
    if replay is not None:
        return replay

    peek = await db.get(MachineRun, machine_run_id)
    if peek is None:
        raise ResourceStateNotFoundError(
            "machine_run_not_found", f"machine_run {machine_run_id} not found"
        )
    plan_peek = await db.get(ExecutionPlan, command.execution_plan_id)
    if plan_peek is None:
        raise ResourceStateNotFoundError(
            "execution_plan_not_found",
            f"plan {command.execution_plan_id} not found",
        )
    order_id = int(plan_peek.order_id)

    async with machine_lock(int(peek.machine_id)):
        async with plan_order_lock(order_id):
            try:
                replay = await _participant_mutation_idempotent_replay(
                    db,
                    machine_run_id=machine_run_id,
                    command=command,
                    actor_user_id=actor_user_id,
                    operation=operation,
                    expected_status="ACTIVE",
                )
                if replay is not None:
                    await db.commit()
                    return replay

                await require_active_domain_config(db, domain=DOMAIN)
                run = await _load_run_for_update(db, machine_run_id)
                reservation = await _load_run_reservation_for_update(
                    db, machine_run_id
                )
                _assert_coupled(run, reservation)

                if run.version != command.expected_version:
                    raise ResourceStateWriteError(
                        "cas_stale",
                        f"expected_version={command.expected_version} "
                        f"current={run.version}",
                    )
                if run.status != "HELD" or reservation.status != "HELD":
                    raise ResourceStateWriteError(
                        "invalid_transition",
                        f"ADD_MACHINE_RUN_PARTICIPANT not allowed from "
                        f"{run.status}",
                    )

                plan = await load_plan_for_update(
                    db, plan_id=command.execution_plan_id
                )
                task = get_operational_task_from_plan(plan, task_key)
                _mode, new_cap, _eligible = _demand_stamps(task)
                shared_cap = await _active_shared_capability(db, run.id)
                if new_cap != shared_cap:
                    raise ResourceStateValidationError(
                        "participant_capability_mismatch",
                        f"participants require {shared_cap!r} and {new_cap!r}",
                    )
                machine = await _require_reservable_machine(db, run.machine_id)
                _validate_machine_capability_join(machine, new_cap)

                existing_active = await _find_active_membership(
                    db,
                    execution_plan_id=command.execution_plan_id,
                    task_key=task_key,
                )
                membership = await _find_membership_on_run(
                    db,
                    machine_run_id=run.id,
                    execution_plan_id=command.execution_plan_id,
                    task_key=task_key,
                )
                if membership is not None and membership.status == "ACTIVE":
                    raise ResourceStateWriteError(
                        "participant_already_exists",
                        f"task ({command.execution_plan_id}, {task_key!r}) "
                        "already ACTIVE on this MACHINE_RUN",
                    )
                if (
                    existing_active is not None
                    and existing_active.machine_run_id != run.id
                ):
                    raise ResourceStateWriteError(
                        "task_already_in_active_machine_run",
                        f"task ({command.execution_plan_id}, {task_key!r}) "
                        f"already ACTIVE in machine_run_id="
                        f"{existing_active.machine_run_id}",
                    )

                prev_ver = run.version
                now = utcnow()
                if membership is not None and membership.status == "REMOVED":
                    membership.status = "ACTIVE"
                    membership.removed_at = None
                    membership.removed_by = None
                    membership.added_at = now
                    membership.added_by = actor_user_id
                    membership.order_id = int(plan.order_id)
                    membership.idempotency_key = command.idempotency_key
                    affected = membership
                else:
                    affected = MachineRunParticipant(
                        machine_run_id=run.id,
                        execution_plan_id=command.execution_plan_id,
                        order_id=int(plan.order_id),
                        task_key=task_key,
                        status="ACTIVE",
                        added_at=now,
                        added_by=actor_user_id,
                        idempotency_key=command.idempotency_key,
                    )
                    db.add(affected)

                run.version = prev_ver + 1
                run.updated_by = actor_user_id
                run.updated_at = now
                reservation.version = prev_ver + 1
                reservation.updated_by = actor_user_id
                reservation.updated_at = now
                await db.flush()

                run_tr, res_tr = await _append_participant_mutation_histories(
                    db,
                    run=run,
                    reservation=reservation,
                    command=command,
                    actor_user_id=actor_user_id,
                    operation=operation,
                    prev_ver=prev_ver,
                    now=now,
                )
                await db.commit()
            except ResourceStateWriteError:
                await db.rollback()
                raise
            except Exception:
                await db.rollback()
                raise

    return await _result_from_persisted(
        db,
        run=run,
        transition_id=run_tr.transition_id,
        reservation_transition_id=res_tr.transition_id,
        already_applied=False,
        operation=operation,
        previous_status="HELD",
        previous_version=prev_ver,
        affected_participant=affected,
    )


async def remove_machine_run_participant(
    db: AsyncSession,
    *,
    machine_run_id: int,
    command: RemoveMachineRunParticipantCommand,
    actor_user_id: str,
) -> CreateMachineRunResult:
    task_key = _normalize_task_key(command.task_key)
    operation = "REMOVE_MACHINE_RUN_PARTICIPANT"

    replay = await _participant_mutation_idempotent_replay(
        db,
        machine_run_id=machine_run_id,
        command=command,
        actor_user_id=actor_user_id,
        operation=operation,
        expected_status="REMOVED",
    )
    if replay is not None:
        return replay

    peek = await db.get(MachineRun, machine_run_id)
    if peek is None:
        raise ResourceStateNotFoundError(
            "machine_run_not_found", f"machine_run {machine_run_id} not found"
        )

    async with machine_lock(int(peek.machine_id)):
        try:
            replay = await _participant_mutation_idempotent_replay(
                db,
                machine_run_id=machine_run_id,
                command=command,
                actor_user_id=actor_user_id,
                operation=operation,
                expected_status="REMOVED",
            )
            if replay is not None:
                await db.commit()
                return replay

            await require_active_domain_config(db, domain=DOMAIN)
            run = await _load_run_for_update(db, machine_run_id)
            reservation = await _load_run_reservation_for_update(db, machine_run_id)
            _assert_coupled(run, reservation)

            if run.version != command.expected_version:
                raise ResourceStateWriteError(
                    "cas_stale",
                    f"expected_version={command.expected_version} "
                    f"current={run.version}",
                )
            if run.status != "HELD" or reservation.status != "HELD":
                raise ResourceStateWriteError(
                    "invalid_transition",
                    f"REMOVE_MACHINE_RUN_PARTICIPANT not allowed from "
                    f"{run.status}",
                )

            membership = await _find_membership_on_run(
                db,
                machine_run_id=run.id,
                execution_plan_id=command.execution_plan_id,
                task_key=task_key,
            )
            if membership is None or membership.status != "ACTIVE":
                raise ResourceStateWriteError(
                    "participant_not_found",
                    f"no ACTIVE participant "
                    f"({command.execution_plan_id}, {task_key!r}) "
                    f"on machine_run {run.id}",
                )

            active_count = await _count_active_participants(db, run.id)
            if active_count - 1 < MIN_PARTICIPANTS:
                raise ResourceStateWriteError(
                    "minimum_participants_violation",
                    f"REMOVE would leave {active_count - 1} ACTIVE "
                    f"(minimum {MIN_PARTICIPANTS})",
                )

            prev_ver = run.version
            now = utcnow()
            membership.status = "REMOVED"
            membership.removed_at = now
            membership.removed_by = actor_user_id
            # Keep participant.idempotency_key (ADD stamp) for ADD replay identity.

            run.version = prev_ver + 1
            run.updated_by = actor_user_id
            run.updated_at = now
            reservation.version = prev_ver + 1
            reservation.updated_by = actor_user_id
            reservation.updated_at = now
            await db.flush()

            run_tr, res_tr = await _append_participant_mutation_histories(
                db,
                run=run,
                reservation=reservation,
                command=command,
                actor_user_id=actor_user_id,
                operation=operation,
                prev_ver=prev_ver,
                now=now,
            )
            await db.commit()
        except ResourceStateWriteError:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            raise

    return await _result_from_persisted(
        db,
        run=run,
        transition_id=run_tr.transition_id,
        reservation_transition_id=res_tr.transition_id,
        already_applied=False,
        operation=operation,
        previous_status="HELD",
        previous_version=prev_ver,
        affected_participant=membership,
    )
