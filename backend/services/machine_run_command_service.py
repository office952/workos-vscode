"""CREATE_MACHINE_RUN — atomic create of run + participants + run-owned reservation.

Create-only. No CONFIRM/RELEASE/CANCEL/ADD/REMOVE/auto-batch.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from models.execution_plan import ExecutionPlan
from models.execution_task_machine_reservation import (
    ExecutionTaskMachineReservation,
    ExecutionTaskMachineReservationTransition,
)
from models.machine_run import MachineRun, MachineRunParticipant, MachineRunTransition
from models.operational_registry import MachineRegistry
from schemas.resource_state_machine_run import (
    CreateMachineRunCommand,
    CreateMachineRunResult,
    MachineRunParticipantResult,
)
from services.execution_task_machine_reservation_repository import (
    ExecutionTaskMachineReservationRepository,
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


async def _require_reservable_machine(
    db: AsyncSession, machine_id: int
) -> MachineRegistry:
    machine = await db.get(MachineRegistry, machine_id)
    if machine is None:
        raise ResourceStateNotFoundError(
            "machine_not_found", f"machine_id {machine_id} not found"
        )
    if not bool(machine.is_active):
        raise ResourceStateValidationError(
            "machine_not_reservable", "machine is_active=false"
        )
    if not bool(machine.is_available):
        raise ResourceStateValidationError(
            "machine_not_reservable", "machine is_available=false"
        )
    if machine.operational_status != "active":
        raise ResourceStateValidationError(
            "machine_not_reservable",
            f"operational_status={machine.operational_status!r}",
        )
    return machine


def _parse_machine_capabilities(raw: Any) -> list[str]:
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


def _validate_machine_capability_join(
    machine: MachineRegistry, required_capability: str
) -> None:
    """Hard-join only when inventory capabilities are non-empty (readiness MVP)."""
    caps = _parse_machine_capabilities(machine.capabilities)
    if not caps:
        return
    if required_capability not in caps:
        raise ResourceStateValidationError(
            "machine_capability_mismatch",
            f"machine {machine.id} capabilities={caps!r} "
            f"missing {required_capability!r}",
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


def _demand_stamps(task: dict[str, Any]) -> tuple[str, str, bool]:
    mode = task.get("resource_mode")
    if mode is None or (isinstance(mode, str) and not mode.strip()):
        raise ResourceStateValidationError(
            "task_not_machine_bound",
            "resource_mode missing (hint-only fields are not accepted)",
        )
    mode_s = str(mode).strip()
    if mode_s != "MACHINE_BOUND":
        raise ResourceStateValidationError(
            "task_not_machine_bound",
            f"resource_mode={mode_s!r} (required MACHINE_BOUND)",
        )
    cap = task.get("machine_capability_code")
    if cap is None or (isinstance(cap, str) and not str(cap).strip()):
        raise ResourceStateValidationError(
            "task_capability_unknown",
            "machine_capability_code missing",
        )
    cap_s = str(cap).strip()
    eligible = task.get("batch_eligible")
    if eligible is not True:
        raise ResourceStateValidationError(
            "task_not_batch_eligible",
            f"batch_eligible={eligible!r} (required true)",
        )
    return mode_s, cap_s, True


async def _find_active_membership(
    db: AsyncSession, *, execution_plan_id: int, task_key: str
) -> MachineRunParticipant | None:
    result = await db.execute(
        select(MachineRunParticipant).where(
            MachineRunParticipant.execution_plan_id == execution_plan_id,
            MachineRunParticipant.task_key == task_key,
            MachineRunParticipant.status == "ACTIVE",
        )
    )
    return result.scalar_one_or_none()


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


async def _result_from_persisted(
    db: AsyncSession,
    *,
    run: MachineRun,
    transition_id: str,
    reservation_transition_id: str,
    already_applied: bool,
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
        participants=[
            MachineRunParticipantResult(
                execution_plan_id=p.execution_plan_id,
                task_key=p.task_key,
                order_id=p.order_id,
                status=p.status,  # type: ignore[arg-type]
            )
            for p in parts
        ],
        operation=OPERATION,  # type: ignore[arg-type]
        transition_id=transition_id,
        reservation_transition_id=reservation_transition_id,
        already_applied=already_applied,
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
