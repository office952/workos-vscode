"""Resource State R9 — scheduling domain command service."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from models.execution_plan import ExecutionPlan
from models.execution_task_schedule import (
    ExecutionTaskSchedule,
    ExecutionTaskScheduleTransition,
)
from schemas.resource_state_schedule import (
    CancelScheduleCommand,
    ConfirmScheduleCommand,
    CreateScheduleCommand,
    RescheduleCommand,
    ScheduleCommandResult,
    SupersedeScheduleCommand,
)
from services.execution_task_schedule_repository import ExecutionTaskScheduleRepository
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

DOMAIN = "SCHEDULING"
OPEN = frozenset({"DRAFT", "PLANNED", "CONFIRMED"})
TERMINAL = frozenset({"CANCELLED", "SUPERSEDED"})


def _validate_window(start: datetime, end: datetime) -> None:
    if end <= start:
        raise ResourceStateValidationError(
            "invalid_time_window", "scheduled_end must be after scheduled_start"
        )


def _result_from_row(
    *,
    row: ExecutionTaskSchedule,
    operation: str,
    transition_id: str,
    previous_status: str | None,
    previous_version: int | None,
    already_applied: bool,
    replacement_schedule_id: int | None = None,
    replacement_transition_id: str | None = None,
) -> ScheduleCommandResult:
    return ScheduleCommandResult(
        schedule_id=row.id,
        execution_plan_id=row.execution_plan_id,
        task_key=row.task_key,
        status=row.status,  # type: ignore[arg-type]
        version=row.version,
        scheduled_start=row.scheduled_start,
        scheduled_end=row.scheduled_end,
        timezone=row.timezone,
        operation=operation,  # type: ignore[arg-type]
        transition_id=transition_id,
        previous_status=previous_status,  # type: ignore[arg-type]
        previous_version=previous_version,
        already_applied=already_applied,
        replacement_schedule_id=replacement_schedule_id,
        replacement_transition_id=replacement_transition_id,
    )


async def _idempotent_or_conflict(
    repo: ExecutionTaskScheduleRepository,
    *,
    idempotency_key: str,
    fingerprint: dict[str, Any],
    match_fn,
) -> ScheduleCommandResult | None:
    existing = await repo.get_transition_by_idempotency_key(idempotency_key)
    if existing is None:
        return None
    if not match_fn(existing, fingerprint):
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )
    row = await repo.get_by_id(existing.schedule_id)
    if row is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "transition exists without schedule row",
        )
    return _result_from_row(
        row=row,
        operation=existing.operation,
        transition_id=existing.transition_id,
        previous_status=existing.previous_status,
        previous_version=existing.previous_version,
        already_applied=True,
    )


def _create_fp(cmd: CreateScheduleCommand, actor: str) -> dict[str, Any]:
    return {
        "operation": "CREATE_SCHEDULE",
        "execution_plan_id": cmd.execution_plan_id,
        "task_key": cmd.task_key,
        "scheduled_start": dt_key(cmd.scheduled_start),
        "scheduled_end": dt_key(cmd.scheduled_end),
        "timezone": cmd.timezone,
        "initial_status": cmd.initial_status,
        "workcenter_code": cmd.workcenter_code,
        "expected_version": cmd.expected_version,
        "reason_code": cmd.reason_code,
        "reason_note": cmd.reason_note,
        "actor_user_id": actor,
    }


def _match_create(tr: ExecutionTaskScheduleTransition, fp: dict[str, Any]) -> bool:
    return (
        tr.operation == fp["operation"]
        and tr.execution_plan_id == fp["execution_plan_id"]
        and tr.task_key == fp["task_key"]
        and tr.new_status == fp["initial_status"]
        and dt_key(tr.new_start) == fp["scheduled_start"]
        and dt_key(tr.new_end) == fp["scheduled_end"]
        and (tr.reason_code or "") == fp["reason_code"]
        and (tr.reason_note or None) == fp["reason_note"]
        and (tr.actor_user_id or "") == fp["actor_user_id"]
        and tr.previous_version is None
        and fp["expected_version"] == 0
    )


async def create_schedule(
    db: AsyncSession,
    *,
    command: CreateScheduleCommand,
    actor_user_id: str,
) -> ScheduleCommandResult:
    if command.expected_version != 0:
        raise ResourceStateWriteError(
            "cas_stale_or_missing",
            "CREATE_SCHEDULE requires expected_version=0",
        )
    _validate_window(command.scheduled_start, command.scheduled_end)
    if command.initial_status not in ("DRAFT", "PLANNED"):
        raise ResourceStateValidationError(
            "invalid_status", "CREATE allows DRAFT or PLANNED only"
        )

    repo = ExecutionTaskScheduleRepository(db)
    fp = _create_fp(command, actor_user_id)
    replay = await _idempotent_or_conflict(
        repo, idempotency_key=command.idempotency_key, fingerprint=fp, match_fn=_match_create
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

            # Re-check idempotency inside lock
            replay = await _idempotent_or_conflict(
                repo,
                idempotency_key=command.idempotency_key,
                fingerprint=fp,
                match_fn=_match_create,
            )
            if replay is not None:
                await db.commit()
                return replay

            open_row = await repo.get_open_for_task(
                execution_plan_id=plan.id, task_key=command.task_key
            )
            if open_row is not None:
                raise ResourceStateWriteError(
                    "open_row_conflict",
                    "open schedule already exists for plan/task",
                )

            now = utcnow()
            row = ExecutionTaskSchedule(
                execution_plan_id=plan.id,
                order_id=int(plan.order_id),
                task_key=command.task_key,
                scheduled_start=command.scheduled_start,
                scheduled_end=command.scheduled_end,
                timezone=command.timezone,
                status=command.initial_status,
                workcenter_code=command.workcenter_code,
                version=1,
                created_by=actor_user_id,
                updated_by=actor_user_id,
                created_at=now,
                updated_at=now,
                idempotency_key=command.idempotency_key,
            )
            try:
                await repo.add_schedule(row)
                tr = ExecutionTaskScheduleTransition(
                    transition_id=str(uuid.uuid4()),
                    schedule_id=row.id,
                    execution_plan_id=plan.id,
                    task_key=command.task_key,
                    operation="CREATE_SCHEDULE",
                    previous_status=None,
                    new_status=command.initial_status,
                    previous_start=None,
                    previous_end=None,
                    new_start=command.scheduled_start,
                    new_end=command.scheduled_end,
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
                    "open schedule uniqueness conflict",
                ) from ie
            return _result_from_row(
                row=row,
                operation="CREATE_SCHEDULE",
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


async def _mutate_schedule(
    db: AsyncSession,
    *,
    schedule_id: int,
    actor_user_id: str,
    expected_version: int,
    idempotency_key: str,
    fingerprint: dict[str, Any],
    match_fn,
    apply_fn,
) -> ScheduleCommandResult:
    repo = ExecutionTaskScheduleRepository(db)
    replay = await _idempotent_or_conflict(
        repo, idempotency_key=idempotency_key, fingerprint=fingerprint, match_fn=match_fn
    )
    if replay is not None:
        return replay

    row_peek = await repo.get_by_id(schedule_id)
    if row_peek is None:
        raise ResourceStateNotFoundError(
            "schedule_not_found", f"schedule {schedule_id} not found"
        )
    order_id = int(row_peek.order_id)

    async with plan_order_lock(order_id):
        try:
            plan = await load_plan_for_update(
                db, plan_id=row_peek.execution_plan_id
            )
            await require_active_domain_config(db, domain=DOMAIN)
            row = await repo.get_by_id(schedule_id)
            if row is None:
                raise ResourceStateNotFoundError(
                    "schedule_not_found", f"schedule {schedule_id} not found"
                )
            require_task_in_plan(plan, row.task_key)

            replay = await _idempotent_or_conflict(
                repo,
                idempotency_key=idempotency_key,
                fingerprint=fingerprint,
                match_fn=match_fn,
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
                    f"terminal schedule status {row.status}",
                )

            result = await apply_fn(repo, plan, row)
            await db.commit()
            return result
        except Exception:
            await db.rollback()
            raise


async def reschedule_schedule(
    db: AsyncSession,
    *,
    schedule_id: int,
    command: RescheduleCommand,
    actor_user_id: str,
) -> ScheduleCommandResult:
    _validate_window(command.scheduled_start, command.scheduled_end)
    fp = {
        "operation": "RESCHEDULE",
        "schedule_id": schedule_id,
        "scheduled_start": dt_key(command.scheduled_start),
        "scheduled_end": dt_key(command.scheduled_end),
        "timezone": command.timezone,
        "workcenter_code": command.workcenter_code,
        "expected_version": command.expected_version,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
    }

    def match(tr: ExecutionTaskScheduleTransition, f: dict[str, Any]) -> bool:
        return (
            tr.operation == "RESCHEDULE"
            and tr.schedule_id == f["schedule_id"]
            and tr.previous_version == f["expected_version"]
            and dt_key(tr.new_start) == f["scheduled_start"]
            and dt_key(tr.new_end) == f["scheduled_end"]
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.reason_note or None) == f["reason_note"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
        )

    async def apply(repo, plan, row):
        if row.status not in OPEN:
            raise ResourceStateWriteError(
                "invalid_transition", f"cannot reschedule from {row.status}"
            )
        if row.status == "CONFIRMED" and not command.reason_code:
            raise ResourceStateValidationError(
                "reason_required", "reason_code required when rescheduling CONFIRMED"
            )
        prev_status = row.status
        prev_ver = row.version
        prev_start = row.scheduled_start
        prev_end = row.scheduled_end
        now = utcnow()
        row.scheduled_start = command.scheduled_start
        row.scheduled_end = command.scheduled_end
        if command.timezone is not None:
            row.timezone = command.timezone
        if command.workcenter_code is not None:
            row.workcenter_code = command.workcenter_code
        row.version = prev_ver + 1
        row.updated_by = actor_user_id
        row.updated_at = now
        tr = ExecutionTaskScheduleTransition(
            transition_id=str(uuid.uuid4()),
            schedule_id=row.id,
            execution_plan_id=row.execution_plan_id,
            task_key=row.task_key,
            operation="RESCHEDULE",
            previous_status=prev_status,
            new_status=prev_status,
            previous_start=prev_start,
            previous_end=prev_end,
            new_start=row.scheduled_start,
            new_end=row.scheduled_end,
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
            operation="RESCHEDULE",
            transition_id=tr.transition_id,
            previous_status=prev_status,
            previous_version=prev_ver,
            already_applied=False,
        )

    return await _mutate_schedule(
        db,
        schedule_id=schedule_id,
        actor_user_id=actor_user_id,
        expected_version=command.expected_version,
        idempotency_key=command.idempotency_key,
        fingerprint=fp,
        match_fn=match,
        apply_fn=apply,
    )


async def confirm_schedule(
    db: AsyncSession,
    *,
    schedule_id: int,
    command: ConfirmScheduleCommand,
    actor_user_id: str,
) -> ScheduleCommandResult:
    fp = {
        "operation": "CONFIRM_SCHEDULE",
        "schedule_id": schedule_id,
        "expected_version": command.expected_version,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
    }

    def match(tr: ExecutionTaskScheduleTransition, f: dict[str, Any]) -> bool:
        return (
            tr.operation == "CONFIRM_SCHEDULE"
            and tr.schedule_id == f["schedule_id"]
            and tr.previous_version == f["expected_version"]
            and tr.new_status == "CONFIRMED"
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.reason_note or None) == f["reason_note"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
        )

    async def apply(repo, plan, row):
        if row.status not in ("DRAFT", "PLANNED"):
            raise ResourceStateWriteError(
                "invalid_transition",
                f"CONFIRM allowed from DRAFT/PLANNED only, got {row.status}",
            )
        prev_status = row.status
        prev_ver = row.version
        now = utcnow()
        row.status = "CONFIRMED"
        row.version = prev_ver + 1
        row.updated_by = actor_user_id
        row.updated_at = now
        tr = ExecutionTaskScheduleTransition(
            transition_id=str(uuid.uuid4()),
            schedule_id=row.id,
            execution_plan_id=row.execution_plan_id,
            task_key=row.task_key,
            operation="CONFIRM_SCHEDULE",
            previous_status=prev_status,
            new_status="CONFIRMED",
            previous_start=row.scheduled_start,
            previous_end=row.scheduled_end,
            new_start=row.scheduled_start,
            new_end=row.scheduled_end,
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
            operation="CONFIRM_SCHEDULE",
            transition_id=tr.transition_id,
            previous_status=prev_status,
            previous_version=prev_ver,
            already_applied=False,
        )

    return await _mutate_schedule(
        db,
        schedule_id=schedule_id,
        actor_user_id=actor_user_id,
        expected_version=command.expected_version,
        idempotency_key=command.idempotency_key,
        fingerprint=fp,
        match_fn=match,
        apply_fn=apply,
    )


async def cancel_schedule(
    db: AsyncSession,
    *,
    schedule_id: int,
    command: CancelScheduleCommand,
    actor_user_id: str,
) -> ScheduleCommandResult:
    fp = {
        "operation": "CANCEL_SCHEDULE",
        "schedule_id": schedule_id,
        "expected_version": command.expected_version,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
    }

    def match(tr: ExecutionTaskScheduleTransition, f: dict[str, Any]) -> bool:
        return (
            tr.operation == "CANCEL_SCHEDULE"
            and tr.schedule_id == f["schedule_id"]
            and tr.previous_version == f["expected_version"]
            and tr.new_status == "CANCELLED"
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.reason_note or None) == f["reason_note"]
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
        tr = ExecutionTaskScheduleTransition(
            transition_id=str(uuid.uuid4()),
            schedule_id=row.id,
            execution_plan_id=row.execution_plan_id,
            task_key=row.task_key,
            operation="CANCEL_SCHEDULE",
            previous_status=prev_status,
            new_status="CANCELLED",
            previous_start=row.scheduled_start,
            previous_end=row.scheduled_end,
            new_start=row.scheduled_start,
            new_end=row.scheduled_end,
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
            operation="CANCEL_SCHEDULE",
            transition_id=tr.transition_id,
            previous_status=prev_status,
            previous_version=prev_ver,
            already_applied=False,
        )

    return await _mutate_schedule(
        db,
        schedule_id=schedule_id,
        actor_user_id=actor_user_id,
        expected_version=command.expected_version,
        idempotency_key=command.idempotency_key,
        fingerprint=fp,
        match_fn=match,
        apply_fn=apply,
    )


async def supersede_schedule(
    db: AsyncSession,
    *,
    schedule_id: int,
    command: SupersedeScheduleCommand,
    actor_user_id: str,
) -> ScheduleCommandResult:
    _validate_window(command.scheduled_start, command.scheduled_end)
    if command.idempotency_key == command.replacement_idempotency_key:
        raise ResourceStateValidationError(
            "invalid_idempotency",
            "supersede and replacement idempotency keys must differ",
        )

    repo = ExecutionTaskScheduleRepository(db)
    fp_super = {
        "operation": "SUPERSEDE_SCHEDULE",
        "schedule_id": schedule_id,
        "expected_version": command.expected_version,
        "replacement_start": dt_key(command.scheduled_start),
        "replacement_end": dt_key(command.scheduled_end),
        "replacement_status": command.initial_status,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
        "replacement_idempotency_key": command.replacement_idempotency_key,
    }

    def match_super(tr: ExecutionTaskScheduleTransition, f: dict[str, Any]) -> bool:
        return (
            tr.operation == "SUPERSEDE_SCHEDULE"
            and tr.schedule_id == f["schedule_id"]
            and tr.previous_version == f["expected_version"]
            and tr.new_status == "SUPERSEDED"
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
        )

    replay = await _idempotent_or_conflict(
        repo,
        idempotency_key=command.idempotency_key,
        fingerprint=fp_super,
        match_fn=match_super,
    )
    if replay is not None:
        # Attach replacement id if present
        if replay.already_applied and replay.previous_version is not None:
            # look up superseded_by
            old = await repo.get_by_id(schedule_id)
            if old and old.superseded_by_id:
                repl = await repo.get_by_id(old.superseded_by_id)
                if repl:
                    return _result_from_row(
                        row=old,
                        operation="SUPERSEDE_SCHEDULE",
                        transition_id=replay.transition_id,
                        previous_status=replay.previous_status,
                        previous_version=replay.previous_version,
                        already_applied=True,
                        replacement_schedule_id=repl.id,
                    )
        return replay

    row_peek = await repo.get_by_id(schedule_id)
    if row_peek is None:
        raise ResourceStateNotFoundError(
            "schedule_not_found", f"schedule {schedule_id} not found"
        )
    order_id = int(row_peek.order_id)

    async with plan_order_lock(order_id):
        try:
            plan = await load_plan_for_update(
                db, plan_id=row_peek.execution_plan_id
            )
            await require_active_domain_config(db, domain=DOMAIN)
            row = await repo.get_by_id(schedule_id)
            if row is None:
                raise ResourceStateNotFoundError(
                    "schedule_not_found", f"schedule {schedule_id} not found"
                )
            require_task_in_plan(plan, row.task_key)

            replay = await _idempotent_or_conflict(
                repo,
                idempotency_key=command.idempotency_key,
                fingerprint=fp_super,
                match_fn=match_super,
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

            # Replacement key must be free
            if await repo.get_transition_by_idempotency_key(
                command.replacement_idempotency_key
            ):
                raise ResourceStateWriteError(
                    "idempotency_payload_conflict",
                    "replacement_idempotency_key already used",
                )

            prev_status = row.status
            prev_ver = row.version
            now = utcnow()
            # Terminalize first so partial unique open index frees the slot.
            row.status = "SUPERSEDED"
            row.version = prev_ver + 1
            row.updated_by = actor_user_id
            row.updated_at = now
            await db.flush()

            new_row = ExecutionTaskSchedule(
                execution_plan_id=plan.id,
                order_id=int(plan.order_id),
                task_key=row.task_key,
                scheduled_start=command.scheduled_start,
                scheduled_end=command.scheduled_end,
                timezone=command.timezone,
                status=command.initial_status,
                workcenter_code=command.workcenter_code,
                version=1,
                created_by=actor_user_id,
                updated_by=actor_user_id,
                created_at=now,
                updated_at=now,
                idempotency_key=command.replacement_idempotency_key,
            )
            await repo.add_schedule(new_row)
            row.superseded_by_id = new_row.id
            await db.flush()

            tr_super = ExecutionTaskScheduleTransition(
                transition_id=str(uuid.uuid4()),
                schedule_id=row.id,
                execution_plan_id=plan.id,
                task_key=row.task_key,
                operation="SUPERSEDE_SCHEDULE",
                previous_status=prev_status,
                new_status="SUPERSEDED",
                previous_start=row.scheduled_start,
                previous_end=row.scheduled_end,
                new_start=row.scheduled_start,
                new_end=row.scheduled_end,
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

            tr_create = ExecutionTaskScheduleTransition(
                transition_id=str(uuid.uuid4()),
                schedule_id=new_row.id,
                execution_plan_id=plan.id,
                task_key=row.task_key,
                operation="CREATE_SCHEDULE",
                previous_status=None,
                new_status=command.initial_status,
                previous_start=None,
                previous_end=None,
                new_start=command.scheduled_start,
                new_end=command.scheduled_end,
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
                operation="SUPERSEDE_SCHEDULE",
                transition_id=tr_super.transition_id,
                previous_status=prev_status,
                previous_version=prev_ver,
                already_applied=False,
                replacement_schedule_id=new_row.id,
                replacement_transition_id=tr_create.transition_id,
            )
        except Exception:
            await db.rollback()
            raise
