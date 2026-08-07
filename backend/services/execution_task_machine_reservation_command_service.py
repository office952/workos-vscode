"""Resource State R9 — machine reservation domain command service."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from models.execution_plan import ExecutionPlan
from models.execution_task_machine_reservation import (
    ExecutionTaskMachineReservation,
    ExecutionTaskMachineReservationTransition,
)
from models.operational_registry import MachineRegistry
from schemas.resource_state_reservation import (
    CancelReservationCommand,
    ConfirmReservationCommand,
    CreateReservationCommand,
    ReleaseReservationCommand,
    ReservationCommandResult,
    SupersedeReservationCommand,
)
from services.execution_task_machine_reservation_repository import (
    ExecutionTaskMachineReservationRepository,
)
from services.resource_state_write_common import (
    ResourceStateNotFoundError,
    ResourceStateValidationError,
    ResourceStateWriteError,
    dt_key,
    load_plan_for_update,
    plan_order_lock,
    require_active_domain_config,
    require_task_in_plan,
    utcnow,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

DOMAIN = "MACHINE_RESERVATION"
OPEN = frozenset({"HELD", "RESERVED"})
TERMINAL = frozenset({"CANCELLED", "RELEASED", "SUPERSEDED"})


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


def _result_from_row(
    *,
    row: ExecutionTaskMachineReservation,
    operation: str,
    transition_id: str,
    previous_status: str | None,
    previous_version: int | None,
    already_applied: bool,
    replacement_reservation_id: int | None = None,
    replacement_transition_id: str | None = None,
) -> ReservationCommandResult:
    return ReservationCommandResult(
        reservation_id=row.id,
        execution_plan_id=row.execution_plan_id,
        task_key=row.task_key,
        machine_id=row.machine_id,
        status=row.status,  # type: ignore[arg-type]
        version=row.version,
        reservation_start=row.reservation_start,
        reservation_end=row.reservation_end,
        timezone=row.timezone,
        operation=operation,  # type: ignore[arg-type]
        transition_id=transition_id,
        previous_status=previous_status,  # type: ignore[arg-type]
        previous_version=previous_version,
        already_applied=already_applied,
        replacement_reservation_id=replacement_reservation_id,
        replacement_transition_id=replacement_transition_id,
    )


async def _idempotent_or_conflict(
    repo: ExecutionTaskMachineReservationRepository,
    *,
    idempotency_key: str,
    match_fn,
    fingerprint: dict[str, Any],
) -> ReservationCommandResult | None:
    existing = await repo.get_transition_by_idempotency_key(idempotency_key)
    if existing is None:
        return None
    if not match_fn(existing, fingerprint):
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )
    row = await repo.get_by_id(existing.reservation_id)
    if row is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "transition exists without reservation row",
        )
    return _result_from_row(
        row=row,
        operation=existing.operation,
        transition_id=existing.transition_id,
        previous_status=existing.previous_status,
        previous_version=existing.previous_version,
        already_applied=True,
    )


async def create_reservation(
    db: AsyncSession,
    *,
    command: CreateReservationCommand,
    actor_user_id: str,
) -> ReservationCommandResult:
    if command.expected_version != 0:
        raise ResourceStateWriteError(
            "cas_stale_or_missing",
            "CREATE_RESERVATION requires expected_version=0",
        )
    _validate_window(command.reservation_start, command.reservation_end)

    repo = ExecutionTaskMachineReservationRepository(db)
    fp = {
        "operation": "CREATE_RESERVATION",
        "owner_form": "TASK",
        "execution_plan_id": command.execution_plan_id,
        "task_key": command.task_key,
        "machine_id": command.machine_id,
        "reservation_start": dt_key(command.reservation_start),
        "reservation_end": dt_key(command.reservation_end),
        "timezone": command.timezone,
        "expected_version": 0,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
    }

    def match(tr: ExecutionTaskMachineReservationTransition, f: dict[str, Any]) -> bool:
        return (
            tr.operation == "CREATE_RESERVATION"
            and (getattr(tr, "owner_form", None) or "TASK") == f["owner_form"]
            and tr.machine_run_id is None
            and tr.execution_plan_id == f["execution_plan_id"]
            and tr.task_key == f["task_key"]
            and tr.machine_id == f["machine_id"]
            and tr.new_status == "HELD"
            and dt_key(tr.new_start) == f["reservation_start"]
            and dt_key(tr.new_end) == f["reservation_end"]
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.reason_note or None) == f["reason_note"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
        )

    replay = await _idempotent_or_conflict(
        repo, idempotency_key=command.idempotency_key, match_fn=match, fingerprint=fp
    )
    if replay is not None:
        return replay

    peek = await db.get(ExecutionPlan, command.execution_plan_id)
    if peek is None:
        raise ResourceStateNotFoundError(
            "execution_plan_not_found",
            f"plan {command.execution_plan_id} not found",
        )
    order_id = int(peek.order_id)

    async with plan_order_lock(order_id):
        try:
            plan = await load_plan_for_update(db, plan_id=command.execution_plan_id)
            await require_active_domain_config(db, domain=DOMAIN)
            require_task_in_plan(plan, command.task_key)
            await _require_reservable_machine(db, command.machine_id)

            replay = await _idempotent_or_conflict(
                repo,
                idempotency_key=command.idempotency_key,
                match_fn=match,
                fingerprint=fp,
            )
            if replay is not None:
                await db.commit()
                return replay

            open_same = await repo.get_open_for_task_machine(
                execution_plan_id=plan.id,
                task_key=command.task_key,
                machine_id=command.machine_id,
            )
            if open_same is not None:
                raise ResourceStateWriteError(
                    "open_row_conflict",
                    "open reservation already exists for plan/task/machine",
                )

            overlap = await repo.find_overlapping_open(
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
            row = ExecutionTaskMachineReservation(
                execution_plan_id=plan.id,
                order_id=int(plan.order_id),
                task_key=command.task_key,
                machine_run_id=None,
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
            try:
                await repo.add_reservation(row)
                tr = ExecutionTaskMachineReservationTransition(
                    transition_id=str(uuid.uuid4()),
                    reservation_id=row.id,
                    owner_form="TASK",
                    execution_plan_id=plan.id,
                    task_key=command.task_key,
                    machine_run_id=None,
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
                await repo.add_transition(tr)
                await db.commit()
            except IntegrityError as ie:
                await db.rollback()
                raise ResourceStateWriteError(
                    "open_row_conflict",
                    "open reservation uniqueness conflict",
                ) from ie
            return _result_from_row(
                row=row,
                operation="CREATE_RESERVATION",
                transition_id=tr.transition_id,
                previous_status=None,
                previous_version=None,
                already_applied=False,
            )
        except ResourceStateWriteError:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            raise


async def _mutate_reservation(
    db: AsyncSession,
    *,
    reservation_id: int,
    actor_user_id: str,
    expected_version: int,
    idempotency_key: str,
    fingerprint: dict[str, Any],
    match_fn,
    apply_fn,
) -> ReservationCommandResult:
    repo = ExecutionTaskMachineReservationRepository(db)
    replay = await _idempotent_or_conflict(
        repo, idempotency_key=idempotency_key, match_fn=match_fn, fingerprint=fingerprint
    )
    if replay is not None:
        return replay

    peek = await repo.get_by_id(reservation_id)
    if peek is None:
        raise ResourceStateNotFoundError(
            "reservation_not_found", f"reservation {reservation_id} not found"
        )
    order_id = int(peek.order_id)

    async with plan_order_lock(order_id):
        try:
            plan = await load_plan_for_update(db, plan_id=peek.execution_plan_id)
            await require_active_domain_config(db, domain=DOMAIN)
            row = await repo.get_by_id(reservation_id)
            if row is None:
                raise ResourceStateNotFoundError(
                    "reservation_not_found",
                    f"reservation {reservation_id} not found",
                )
            require_task_in_plan(plan, row.task_key)

            replay = await _idempotent_or_conflict(
                repo,
                idempotency_key=idempotency_key,
                match_fn=match_fn,
                fingerprint=fingerprint,
            )
            if replay is not None:
                await db.commit()
                return replay

            if row.version != expected_version:
                raise ResourceStateWriteError(
                    "cas_stale",
                    f"expected_version={expected_version} current={row.version}",
                )
            if row.status in TERMINAL:
                raise ResourceStateWriteError(
                    "invalid_transition",
                    f"terminal reservation status {row.status}",
                )

            result = await apply_fn(repo, plan, row)
            await db.commit()
            return result
        except Exception:
            await db.rollback()
            raise


async def confirm_reservation(
    db: AsyncSession,
    *,
    reservation_id: int,
    command: ConfirmReservationCommand,
    actor_user_id: str,
) -> ReservationCommandResult:
    fp = {
        "operation": "CONFIRM_RESERVATION",
        "reservation_id": reservation_id,
        "expected_version": command.expected_version,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
    }

    def match(tr, f):
        return (
            tr.operation == "CONFIRM_RESERVATION"
            and tr.reservation_id == f["reservation_id"]
            and tr.previous_version == f["expected_version"]
            and tr.new_status == "RESERVED"
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
        )

    async def apply(repo, plan, row):
        if row.status != "HELD":
            raise ResourceStateWriteError(
                "invalid_transition",
                f"CONFIRM allowed from HELD only, got {row.status}",
            )
        prev_status = row.status
        prev_ver = row.version
        now = utcnow()
        row.status = "RESERVED"
        row.version = prev_ver + 1
        row.updated_by = actor_user_id
        row.updated_at = now
        tr = ExecutionTaskMachineReservationTransition(
            transition_id=str(uuid.uuid4()),
            reservation_id=row.id,
            owner_form="TASK",
            execution_plan_id=row.execution_plan_id,
            task_key=row.task_key,
            machine_run_id=None,
            machine_id=row.machine_id,
            operation="CONFIRM_RESERVATION",
            previous_status=prev_status,
            new_status="RESERVED",
            previous_start=row.reservation_start,
            previous_end=row.reservation_end,
            new_start=row.reservation_start,
            new_end=row.reservation_end,
            previous_version=prev_ver,
            new_version=row.version,
            reason_code=command.reason_code,
            reason_note=command.reason_note,
            actor_user_id=actor_user_id,
            idempotency_key=command.idempotency_key,
            correlation_id=command.correlation_id,
            created_at=now,
        )
        await repo.add_transition(tr)
        return _result_from_row(
            row=row,
            operation="CONFIRM_RESERVATION",
            transition_id=tr.transition_id,
            previous_status=prev_status,
            previous_version=prev_ver,
            already_applied=False,
        )

    return await _mutate_reservation(
        db,
        reservation_id=reservation_id,
        actor_user_id=actor_user_id,
        expected_version=command.expected_version,
        idempotency_key=command.idempotency_key,
        fingerprint=fp,
        match_fn=match,
        apply_fn=apply,
    )


async def release_reservation(
    db: AsyncSession,
    *,
    reservation_id: int,
    command: ReleaseReservationCommand,
    actor_user_id: str,
) -> ReservationCommandResult:
    fp = {
        "operation": "RELEASE_RESERVATION",
        "reservation_id": reservation_id,
        "expected_version": command.expected_version,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
    }

    def match(tr, f):
        return (
            tr.operation == "RELEASE_RESERVATION"
            and tr.reservation_id == f["reservation_id"]
            and tr.previous_version == f["expected_version"]
            and tr.new_status == "RELEASED"
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
        )

    async def apply(repo, plan, row):
        if row.status not in OPEN:
            raise ResourceStateWriteError(
                "invalid_transition", f"cannot release from {row.status}"
            )
        prev_status = row.status
        prev_ver = row.version
        now = utcnow()
        row.status = "RELEASED"
        row.released_at = now
        row.released_by = actor_user_id
        row.version = prev_ver + 1
        row.updated_by = actor_user_id
        row.updated_at = now
        tr = ExecutionTaskMachineReservationTransition(
            transition_id=str(uuid.uuid4()),
            reservation_id=row.id,
            owner_form="TASK",
            execution_plan_id=row.execution_plan_id,
            task_key=row.task_key,
            machine_run_id=None,
            machine_id=row.machine_id,
            operation="RELEASE_RESERVATION",
            previous_status=prev_status,
            new_status="RELEASED",
            previous_start=row.reservation_start,
            previous_end=row.reservation_end,
            new_start=row.reservation_start,
            new_end=row.reservation_end,
            previous_version=prev_ver,
            new_version=row.version,
            reason_code=command.reason_code,
            reason_note=command.reason_note,
            actor_user_id=actor_user_id,
            idempotency_key=command.idempotency_key,
            correlation_id=command.correlation_id,
            created_at=now,
        )
        await repo.add_transition(tr)
        return _result_from_row(
            row=row,
            operation="RELEASE_RESERVATION",
            transition_id=tr.transition_id,
            previous_status=prev_status,
            previous_version=prev_ver,
            already_applied=False,
        )

    return await _mutate_reservation(
        db,
        reservation_id=reservation_id,
        actor_user_id=actor_user_id,
        expected_version=command.expected_version,
        idempotency_key=command.idempotency_key,
        fingerprint=fp,
        match_fn=match,
        apply_fn=apply,
    )


async def cancel_reservation(
    db: AsyncSession,
    *,
    reservation_id: int,
    command: CancelReservationCommand,
    actor_user_id: str,
) -> ReservationCommandResult:
    fp = {
        "operation": "CANCEL_RESERVATION",
        "reservation_id": reservation_id,
        "expected_version": command.expected_version,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
    }

    def match(tr, f):
        return (
            tr.operation == "CANCEL_RESERVATION"
            and tr.reservation_id == f["reservation_id"]
            and tr.previous_version == f["expected_version"]
            and tr.new_status == "CANCELLED"
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
        )

    async def apply(repo, plan, row):
        if row.status not in OPEN:
            raise ResourceStateWriteError(
                "invalid_transition", f"cannot cancel from {row.status}"
            )
        prev_status = row.status
        prev_ver = row.version
        now = utcnow()
        row.status = "CANCELLED"
        row.cancelled_at = now
        row.cancelled_by = actor_user_id
        row.version = prev_ver + 1
        row.updated_by = actor_user_id
        row.updated_at = now
        tr = ExecutionTaskMachineReservationTransition(
            transition_id=str(uuid.uuid4()),
            reservation_id=row.id,
            owner_form="TASK",
            execution_plan_id=row.execution_plan_id,
            task_key=row.task_key,
            machine_run_id=None,
            machine_id=row.machine_id,
            operation="CANCEL_RESERVATION",
            previous_status=prev_status,
            new_status="CANCELLED",
            previous_start=row.reservation_start,
            previous_end=row.reservation_end,
            new_start=row.reservation_start,
            new_end=row.reservation_end,
            previous_version=prev_ver,
            new_version=row.version,
            reason_code=command.reason_code,
            reason_note=command.reason_note,
            actor_user_id=actor_user_id,
            idempotency_key=command.idempotency_key,
            correlation_id=command.correlation_id,
            created_at=now,
        )
        await repo.add_transition(tr)
        return _result_from_row(
            row=row,
            operation="CANCEL_RESERVATION",
            transition_id=tr.transition_id,
            previous_status=prev_status,
            previous_version=prev_ver,
            already_applied=False,
        )

    return await _mutate_reservation(
        db,
        reservation_id=reservation_id,
        actor_user_id=actor_user_id,
        expected_version=command.expected_version,
        idempotency_key=command.idempotency_key,
        fingerprint=fp,
        match_fn=match,
        apply_fn=apply,
    )


async def supersede_reservation(
    db: AsyncSession,
    *,
    reservation_id: int,
    command: SupersedeReservationCommand,
    actor_user_id: str,
) -> ReservationCommandResult:
    _validate_window(command.reservation_start, command.reservation_end)
    if command.idempotency_key == command.replacement_idempotency_key:
        raise ResourceStateValidationError(
            "invalid_idempotency",
            "supersede and replacement idempotency keys must differ",
        )

    repo = ExecutionTaskMachineReservationRepository(db)
    fp = {
        "operation": "SUPERSEDE_RESERVATION",
        "reservation_id": reservation_id,
        "expected_version": command.expected_version,
        "replacement_start": dt_key(command.reservation_start),
        "replacement_end": dt_key(command.reservation_end),
        "machine_id": command.machine_id,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
        "replacement_idempotency_key": command.replacement_idempotency_key,
    }

    def match(tr, f):
        return (
            tr.operation == "SUPERSEDE_RESERVATION"
            and tr.reservation_id == f["reservation_id"]
            and tr.previous_version == f["expected_version"]
            and tr.new_status == "SUPERSEDED"
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
        )

    replay = await _idempotent_or_conflict(
        repo, idempotency_key=command.idempotency_key, match_fn=match, fingerprint=fp
    )
    if replay is not None:
        old = await repo.get_by_id(reservation_id)
        if old and old.superseded_by_id:
            return _result_from_row(
                row=old,
                operation="SUPERSEDE_RESERVATION",
                transition_id=replay.transition_id,
                previous_status=replay.previous_status,
                previous_version=replay.previous_version,
                already_applied=True,
                replacement_reservation_id=old.superseded_by_id,
            )
        return replay

    peek = await repo.get_by_id(reservation_id)
    if peek is None:
        raise ResourceStateNotFoundError(
            "reservation_not_found", f"reservation {reservation_id} not found"
        )
    order_id = int(peek.order_id)

    async with plan_order_lock(order_id):
        try:
            plan = await load_plan_for_update(db, plan_id=peek.execution_plan_id)
            await require_active_domain_config(db, domain=DOMAIN)
            row = await repo.get_by_id(reservation_id)
            if row is None:
                raise ResourceStateNotFoundError(
                    "reservation_not_found",
                    f"reservation {reservation_id} not found",
                )
            require_task_in_plan(plan, row.task_key)

            replay = await _idempotent_or_conflict(
                repo,
                idempotency_key=command.idempotency_key,
                match_fn=match,
                fingerprint=fp,
            )
            if replay is not None:
                await db.commit()
                return replay

            if row.version != command.expected_version:
                raise ResourceStateWriteError(
                    "cas_stale",
                    f"expected_version={command.expected_version} "
                    f"current={row.version}",
                )
            if row.status not in OPEN:
                raise ResourceStateWriteError(
                    "invalid_transition",
                    f"cannot supersede from {row.status}",
                )

            new_machine_id = command.machine_id or row.machine_id
            await _require_reservable_machine(db, new_machine_id)

            if await repo.get_transition_by_idempotency_key(
                command.replacement_idempotency_key
            ):
                raise ResourceStateWriteError(
                    "idempotency_payload_conflict",
                    "replacement_idempotency_key already used",
                )

            overlap = await repo.find_overlapping_open(
                machine_id=new_machine_id,
                start=command.reservation_start,
                end=command.reservation_end,
                exclude_id=row.id,
            )
            if overlap is not None:
                raise ResourceStateWriteError(
                    "overlap_conflict",
                    f"overlaps reservation id={overlap.id}",
                )

            prev_status = row.status
            prev_ver = row.version
            now = utcnow()
            row.status = "SUPERSEDED"
            row.version = prev_ver + 1
            row.updated_by = actor_user_id
            row.updated_at = now
            await db.flush()

            new_row = ExecutionTaskMachineReservation(
                execution_plan_id=plan.id,
                order_id=int(plan.order_id),
                task_key=row.task_key,
                machine_run_id=None,
                machine_id=new_machine_id,
                reservation_start=command.reservation_start,
                reservation_end=command.reservation_end,
                timezone=command.timezone,
                status="HELD",
                version=1,
                created_by=actor_user_id,
                updated_by=actor_user_id,
                created_at=now,
                updated_at=now,
                idempotency_key=command.replacement_idempotency_key,
            )
            await repo.add_reservation(new_row)
            row.superseded_by_id = new_row.id
            await db.flush()

            tr_super = ExecutionTaskMachineReservationTransition(
                transition_id=str(uuid.uuid4()),
                reservation_id=row.id,
                owner_form="TASK",
                execution_plan_id=plan.id,
                task_key=row.task_key,
                machine_run_id=None,
                machine_id=row.machine_id,
                operation="SUPERSEDE_RESERVATION",
                previous_status=prev_status,
                new_status="SUPERSEDED",
                previous_start=row.reservation_start,
                previous_end=row.reservation_end,
                new_start=row.reservation_start,
                new_end=row.reservation_end,
                previous_version=prev_ver,
                new_version=row.version,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
                actor_user_id=actor_user_id,
                idempotency_key=command.idempotency_key,
                correlation_id=command.correlation_id,
                created_at=now,
            )
            await repo.add_transition(tr_super)

            tr_create = ExecutionTaskMachineReservationTransition(
                transition_id=str(uuid.uuid4()),
                reservation_id=new_row.id,
                owner_form="TASK",
                execution_plan_id=plan.id,
                task_key=row.task_key,
                machine_run_id=None,
                machine_id=new_machine_id,
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
                idempotency_key=command.replacement_idempotency_key,
                correlation_id=command.correlation_id,
                created_at=now,
            )
            await repo.add_transition(tr_create)
            await db.commit()
            return _result_from_row(
                row=row,
                operation="SUPERSEDE_RESERVATION",
                transition_id=tr_super.transition_id,
                previous_status=prev_status,
                previous_version=prev_ver,
                already_applied=False,
                replacement_reservation_id=new_row.id,
                replacement_transition_id=tr_create.transition_id,
            )
        except Exception:
            await db.rollback()
            raise
