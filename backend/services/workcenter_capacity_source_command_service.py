"""Capacity Stage 1 — workcenter capacity source command service."""

from __future__ import annotations

import uuid
from typing import Any

from models.workcenter_capacity_source import (
    CAPACITY_SOURCE_LABELS,
    OVER_ALLOCATION_POLICIES,
    WorkcenterCapacitySource,
    WorkcenterCapacitySourceTransition,
)
from schemas.resource_state_capacity_source import (
    AdjustWorkcenterCapacityCommand,
    CreateWorkcenterCapacityCommand,
    DisableWorkcenterCapacityCommand,
    SupersedeWorkcenterCapacityCommand,
    WorkcenterCapacitySourceResult,
)
from services.capacity_day_bucket import day_bounds_for_date
from services.resource_state_write_common import (
    ResourceStateValidationError,
    ResourceStateWriteError,
    utcnow,
)
from services.workcenter_capacity_source_repository import (
    WorkcenterCapacitySourceRepository,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


def _result(
    *,
    row: WorkcenterCapacitySource,
    operation: str,
    transition_id: str,
    previous_status: str | None,
    previous_version: int | None,
    already_applied: bool,
    replacement_source_id: int | None = None,
    replacement_transition_id: str | None = None,
) -> WorkcenterCapacitySourceResult:
    return WorkcenterCapacitySourceResult(
        source_id=row.id,
        workcenter_code=row.workcenter_code,
        bucket_date=row.bucket_date,
        bucket_start=row.bucket_start,
        bucket_end=row.bucket_end,
        timezone=row.timezone,
        available_minutes=row.available_minutes,
        over_allocation_policy=row.over_allocation_policy,  # type: ignore[arg-type]
        source_label=row.source_label,  # type: ignore[arg-type]
        source_execution_truth=bool(row.source_execution_truth),
        status=row.status,  # type: ignore[arg-type]
        version=row.version,
        operation=operation,  # type: ignore[arg-type]
        transition_id=transition_id,
        previous_status=previous_status,  # type: ignore[arg-type]
        previous_version=previous_version,
        already_applied=already_applied,
        replacement_source_id=replacement_source_id,
        replacement_transition_id=replacement_transition_id,
    )


async def _idempotent_or_conflict(
    repo: WorkcenterCapacitySourceRepository,
    *,
    idempotency_key: str,
    fingerprint: dict[str, Any],
    match_fn,
) -> WorkcenterCapacitySourceResult | None:
    existing = await repo.get_transition_by_idempotency_key(idempotency_key)
    if existing is None:
        return None
    if not match_fn(existing, fingerprint):
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )
    row = await repo.get_by_id(existing.source_id)
    if row is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "transition exists without source row",
        )
    return _result(
        row=row,
        operation=existing.operation,
        transition_id=existing.transition_id,
        previous_status=existing.previous_status,
        previous_version=existing.previous_version,
        already_applied=True,
    )


def _validate_label_policy(
    *,
    source_label: str,
    source_explanation: str | None,
    source_execution_truth: bool,
) -> None:
    if source_label not in CAPACITY_SOURCE_LABELS:
        raise ResourceStateValidationError(
            "invalid_source_label", f"unsupported source_label: {source_label}"
        )
    if source_label == "AI_DECISION":
        if not source_explanation:
            raise ResourceStateValidationError(
                "ai_explanation_required",
                "AI_DECISION requires source_explanation",
            )
        if source_execution_truth:
            raise ResourceStateValidationError(
                "ai_not_execution_truth",
                "AI_DECISION must set source_execution_truth=false",
            )


async def create_workcenter_capacity(
    db: AsyncSession,
    *,
    command: CreateWorkcenterCapacityCommand,
    actor_user_id: str,
) -> WorkcenterCapacitySourceResult:
    if command.expected_version != 0:
        raise ResourceStateWriteError(
            "cas_stale_or_missing",
            "CREATE_WORKCENTER_CAPACITY requires expected_version=0",
        )
    if command.over_allocation_policy not in OVER_ALLOCATION_POLICIES:
        raise ResourceStateValidationError(
            "invalid_policy",
            f"unsupported policy: {command.over_allocation_policy}",
        )
    _validate_label_policy(
        source_label=command.source_label,
        source_explanation=command.source_explanation,
        source_execution_truth=command.source_execution_truth,
    )
    wc = command.workcenter_code.strip()
    if not wc:
        raise ResourceStateValidationError(
            "invalid_workcenter", "workcenter_code required"
        )

    bucket_start, bucket_end = day_bounds_for_date(
        command.bucket_date, command.timezone
    )
    repo = WorkcenterCapacitySourceRepository(db)
    fp = {
        "operation": "CREATE_WORKCENTER_CAPACITY",
        "workcenter_code": wc,
        "bucket_date": str(command.bucket_date),
        "available_minutes": command.available_minutes,
        "over_allocation_policy": command.over_allocation_policy,
        "source_label": command.source_label,
        "expected_version": 0,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
    }

    def _match(tr, f):
        return (
            tr.operation == f["operation"]
            and tr.workcenter_code == f["workcenter_code"]
            and str(tr.bucket_date) == f["bucket_date"]
            and tr.new_available_minutes == f["available_minutes"]
            and tr.new_policy == f["over_allocation_policy"]
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.reason_note or None) == f["reason_note"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
            and tr.previous_version is None
        )

    replay = await _idempotent_or_conflict(
        repo,
        idempotency_key=command.idempotency_key,
        fingerprint=fp,
        match_fn=_match,
    )
    if replay is not None:
        return replay

    existing = await repo.get_active_for_day(
        workcenter_code=wc, bucket_date=command.bucket_date
    )
    if existing is not None:
        raise ResourceStateWriteError(
            "open_row_conflict",
            "ACTIVE capacity source already exists for workcenter/day",
        )

    now = utcnow()
    tid = str(uuid.uuid4())
    row = WorkcenterCapacitySource(
        workcenter_code=wc,
        bucket_date=command.bucket_date,
        bucket_start=bucket_start,
        bucket_end=bucket_end,
        timezone=command.timezone,
        available_minutes=command.available_minutes,
        over_allocation_policy=command.over_allocation_policy,
        source_label=command.source_label,
        source_explanation=command.source_explanation,
        source_execution_truth=1 if command.source_execution_truth else 0,
        status="ACTIVE",
        version=1,
        created_by=actor_user_id,
        updated_by=actor_user_id,
        created_at=now,
        updated_at=now,
        idempotency_key=command.idempotency_key,
    )
    try:
        await repo.add_source(row)
        await repo.add_transition(
            WorkcenterCapacitySourceTransition(
                transition_id=tid,
                source_id=row.id,
                workcenter_code=wc,
                bucket_date=command.bucket_date,
                operation="CREATE_WORKCENTER_CAPACITY",
                previous_status=None,
                new_status="ACTIVE",
                previous_available_minutes=None,
                new_available_minutes=command.available_minutes,
                previous_policy=None,
                new_policy=command.over_allocation_policy,
                previous_version=None,
                new_version=1,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
                actor_user_id=actor_user_id,
                idempotency_key=command.idempotency_key,
                correlation_id=command.correlation_id,
                created_at=now,
            )
        )
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ResourceStateWriteError(
            "open_row_conflict",
            "capacity source unique constraint conflict",
        ) from exc

    return _result(
        row=row,
        operation="CREATE_WORKCENTER_CAPACITY",
        transition_id=tid,
        previous_status=None,
        previous_version=None,
        already_applied=False,
    )


async def adjust_workcenter_capacity(
    db: AsyncSession,
    *,
    source_id: int,
    command: AdjustWorkcenterCapacityCommand,
    actor_user_id: str,
) -> WorkcenterCapacitySourceResult:
    repo = WorkcenterCapacitySourceRepository(db)
    fp = {
        "operation": "ADJUST_WORKCENTER_CAPACITY",
        "source_id": source_id,
        "available_minutes": command.available_minutes,
        "expected_version": command.expected_version,
        "reason_code": command.reason_code,
        "reason_note": command.reason_note,
        "actor_user_id": actor_user_id,
    }

    def _match(tr, f):
        return (
            tr.operation == f["operation"]
            and tr.source_id == f["source_id"]
            and tr.new_available_minutes == f["available_minutes"]
            and tr.previous_version == f["expected_version"]
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
        )

    replay = await _idempotent_or_conflict(
        repo,
        idempotency_key=command.idempotency_key,
        fingerprint=fp,
        match_fn=_match,
    )
    if replay is not None:
        return replay

    row = await repo.get_by_id(source_id)
    if row is None:
        raise ResourceStateWriteError(
            "capacity_source_not_found", f"source {source_id} not found"
        )
    if row.status != "ACTIVE":
        raise ResourceStateWriteError(
            "invalid_transition", "ADJUST requires ACTIVE source"
        )
    if row.version != command.expected_version:
        raise ResourceStateWriteError("cas_stale", "expected_version mismatch")

    policy = command.over_allocation_policy or row.over_allocation_policy
    label = command.source_label or row.source_label
    explanation = (
        command.source_explanation
        if command.source_explanation is not None
        else row.source_explanation
    )
    exec_truth = (
        command.source_execution_truth
        if command.source_execution_truth is not None
        else bool(row.source_execution_truth)
    )
    if policy not in OVER_ALLOCATION_POLICIES:
        raise ResourceStateValidationError("invalid_policy", f"bad policy: {policy}")
    _validate_label_policy(
        source_label=label,
        source_explanation=explanation,
        source_execution_truth=exec_truth,
    )

    prev_status = row.status
    prev_ver = row.version
    prev_minutes = row.available_minutes
    prev_policy = row.over_allocation_policy
    now = utcnow()
    tid = str(uuid.uuid4())
    row.available_minutes = command.available_minutes
    row.over_allocation_policy = policy
    row.source_label = label
    row.source_explanation = explanation
    row.source_execution_truth = 1 if exec_truth else 0
    row.version = prev_ver + 1
    row.updated_by = actor_user_id
    row.updated_at = now
    await repo.add_transition(
        WorkcenterCapacitySourceTransition(
            transition_id=tid,
            source_id=row.id,
            workcenter_code=row.workcenter_code,
            bucket_date=row.bucket_date,
            operation="ADJUST_WORKCENTER_CAPACITY",
            previous_status=prev_status,
            new_status="ACTIVE",
            previous_available_minutes=prev_minutes,
            new_available_minutes=command.available_minutes,
            previous_policy=prev_policy,
            new_policy=policy,
            previous_version=prev_ver,
            new_version=row.version,
            reason_code=command.reason_code,
            reason_note=command.reason_note,
            actor_user_id=actor_user_id,
            idempotency_key=command.idempotency_key,
            correlation_id=command.correlation_id,
            created_at=now,
        )
    )
    await db.commit()
    return _result(
        row=row,
        operation="ADJUST_WORKCENTER_CAPACITY",
        transition_id=tid,
        previous_status=prev_status,
        previous_version=prev_ver,
        already_applied=False,
    )


async def disable_workcenter_capacity(
    db: AsyncSession,
    *,
    source_id: int,
    command: DisableWorkcenterCapacityCommand,
    actor_user_id: str,
) -> WorkcenterCapacitySourceResult:
    repo = WorkcenterCapacitySourceRepository(db)
    fp = {
        "operation": "DISABLE_WORKCENTER_CAPACITY",
        "source_id": source_id,
        "expected_version": command.expected_version,
        "reason_code": command.reason_code,
        "actor_user_id": actor_user_id,
    }

    def _match(tr, f):
        return (
            tr.operation == f["operation"]
            and tr.source_id == f["source_id"]
            and tr.previous_version == f["expected_version"]
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
        )

    replay = await _idempotent_or_conflict(
        repo,
        idempotency_key=command.idempotency_key,
        fingerprint=fp,
        match_fn=_match,
    )
    if replay is not None:
        return replay

    row = await repo.get_by_id(source_id)
    if row is None:
        raise ResourceStateWriteError(
            "capacity_source_not_found", f"source {source_id} not found"
        )
    if row.status != "ACTIVE":
        raise ResourceStateWriteError(
            "invalid_transition", "DISABLE requires ACTIVE source"
        )
    if row.version != command.expected_version:
        raise ResourceStateWriteError("cas_stale", "expected_version mismatch")

    prev_status = row.status
    prev_ver = row.version
    now = utcnow()
    tid = str(uuid.uuid4())
    row.status = "DISABLED"
    row.version = prev_ver + 1
    row.disabled_at = now
    row.disabled_by = actor_user_id
    row.updated_by = actor_user_id
    row.updated_at = now
    await repo.add_transition(
        WorkcenterCapacitySourceTransition(
            transition_id=tid,
            source_id=row.id,
            workcenter_code=row.workcenter_code,
            bucket_date=row.bucket_date,
            operation="DISABLE_WORKCENTER_CAPACITY",
            previous_status=prev_status,
            new_status="DISABLED",
            previous_available_minutes=row.available_minutes,
            new_available_minutes=row.available_minutes,
            previous_policy=row.over_allocation_policy,
            new_policy=row.over_allocation_policy,
            previous_version=prev_ver,
            new_version=row.version,
            reason_code=command.reason_code,
            reason_note=command.reason_note,
            actor_user_id=actor_user_id,
            idempotency_key=command.idempotency_key,
            correlation_id=command.correlation_id,
            created_at=now,
        )
    )
    await db.commit()
    return _result(
        row=row,
        operation="DISABLE_WORKCENTER_CAPACITY",
        transition_id=tid,
        previous_status=prev_status,
        previous_version=prev_ver,
        already_applied=False,
    )


async def supersede_workcenter_capacity(
    db: AsyncSession,
    *,
    source_id: int,
    command: SupersedeWorkcenterCapacityCommand,
    actor_user_id: str,
) -> WorkcenterCapacitySourceResult:
    """Terminalize ACTIVE source and create replacement in one transaction."""
    repo = WorkcenterCapacitySourceRepository(db)
    existing_tr = await repo.get_transition_by_idempotency_key(command.idempotency_key)
    if existing_tr is not None:
        if existing_tr.operation != "SUPERSEDE_WORKCENTER_CAPACITY":
            raise ResourceStateWriteError(
                "idempotency_payload_conflict",
                "idempotency_key already used with a different payload",
            )
        old = await repo.get_by_id(source_id)
        if old is None or old.superseded_by_id is None:
            raise ResourceStateWriteError(
                "idempotency_orphaned_transition",
                "supersede transition without replacement",
            )
        replacement = await repo.get_by_id(old.superseded_by_id)
        if replacement is None:
            raise ResourceStateWriteError(
                "idempotency_orphaned_transition",
                "replacement missing",
            )
        return _result(
            row=old,
            operation="SUPERSEDE_WORKCENTER_CAPACITY",
            transition_id=existing_tr.transition_id,
            previous_status=existing_tr.previous_status,
            previous_version=existing_tr.previous_version,
            already_applied=True,
            replacement_source_id=replacement.id,
            replacement_transition_id=None,
        )

    _validate_label_policy(
        source_label=command.source_label,
        source_explanation=command.source_explanation,
        source_execution_truth=command.source_execution_truth,
    )
    row = await repo.get_by_id(source_id)
    if row is None:
        raise ResourceStateWriteError(
            "capacity_source_not_found", f"source {source_id} not found"
        )
    if row.status != "ACTIVE":
        raise ResourceStateWriteError(
            "invalid_transition", "SUPERSEDE requires ACTIVE source"
        )
    if row.version != command.expected_version:
        raise ResourceStateWriteError("cas_stale", "expected_version mismatch")

    tz = command.timezone or row.timezone
    bucket_start, bucket_end = day_bounds_for_date(row.bucket_date, tz)
    now = utcnow()
    tid = str(uuid.uuid4())
    repl_tid = str(uuid.uuid4())
    prev_status = row.status
    prev_ver = row.version

    replacement = WorkcenterCapacitySource(
        workcenter_code=row.workcenter_code,
        bucket_date=row.bucket_date,
        bucket_start=bucket_start,
        bucket_end=bucket_end,
        timezone=tz,
        available_minutes=command.available_minutes,
        over_allocation_policy=command.over_allocation_policy,
        source_label=command.source_label,
        source_explanation=command.source_explanation,
        source_execution_truth=1 if command.source_execution_truth else 0,
        status="ACTIVE",
        version=1,
        created_by=actor_user_id,
        updated_by=actor_user_id,
        created_at=now,
        updated_at=now,
        idempotency_key=command.replacement_idempotency_key,
    )
    try:
        # Terminalize first so partial unique allows replacement.
        row.status = "SUPERSEDED"
        row.version = prev_ver + 1
        row.updated_by = actor_user_id
        row.updated_at = now
        await db.flush()
        await repo.add_source(replacement)
        row.superseded_by_id = replacement.id
        await repo.add_transition(
            WorkcenterCapacitySourceTransition(
                transition_id=tid,
                source_id=row.id,
                workcenter_code=row.workcenter_code,
                bucket_date=row.bucket_date,
                operation="SUPERSEDE_WORKCENTER_CAPACITY",
                previous_status=prev_status,
                new_status="SUPERSEDED",
                previous_available_minutes=row.available_minutes,
                new_available_minutes=command.available_minutes,
                previous_policy=row.over_allocation_policy,
                new_policy=command.over_allocation_policy,
                previous_version=prev_ver,
                new_version=row.version,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
                actor_user_id=actor_user_id,
                idempotency_key=command.idempotency_key,
                correlation_id=command.correlation_id,
                created_at=now,
            )
        )
        await repo.add_transition(
            WorkcenterCapacitySourceTransition(
                transition_id=repl_tid,
                source_id=replacement.id,
                workcenter_code=replacement.workcenter_code,
                bucket_date=replacement.bucket_date,
                operation="CREATE_WORKCENTER_CAPACITY",
                previous_status=None,
                new_status="ACTIVE",
                previous_available_minutes=None,
                new_available_minutes=command.available_minutes,
                previous_policy=None,
                new_policy=command.over_allocation_policy,
                previous_version=None,
                new_version=1,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
                actor_user_id=actor_user_id,
                idempotency_key=command.replacement_idempotency_key,
                correlation_id=command.correlation_id,
                created_at=now,
            )
        )
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ResourceStateWriteError(
            "open_row_conflict", "supersede unique conflict"
        ) from exc

    return _result(
        row=row,
        operation="SUPERSEDE_WORKCENTER_CAPACITY",
        transition_id=tid,
        previous_status=prev_status,
        previous_version=prev_ver,
        already_applied=False,
        replacement_source_id=replacement.id,
        replacement_transition_id=repl_tid,
    )
