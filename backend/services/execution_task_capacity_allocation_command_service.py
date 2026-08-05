"""Capacity Stage 1 — WORKCENTER capacity allocation writer."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from models.execution_plan import ExecutionPlan
from models.execution_task_capacity_allocation import (
    CAPACITY_UNIT,
    ExecutionTaskCapacityAllocation,
    ExecutionTaskCapacityAllocationTransition,
)
from models.workcenter_capacity_source import WorkcenterCapacitySource
from schemas.resource_state_capacity_allocation import (
    AdjustAllocationCommand,
    AllocationCommandResult,
    CancelAllocationCommand,
    CreateAllocationCommand,
    OverAllocationDetail,
    ReleaseAllocationCommand,
    SupersedeAllocationCommand,
)
from services.capacity_day_bucket import validate_day_bucket
from services.execution_task_capacity_allocation_repository import (
    ExecutionTaskCapacityAllocationRepository,
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
from services.workcenter_capacity_source_repository import (
    WorkcenterCapacitySourceRepository,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

DOMAIN = "CAPACITY_ALLOCATION"
OPEN = frozenset({"HELD", "ALLOCATED"})
WORKLOAD_SOURCES = frozenset(
    {
        "OWNER_CONFIGURED",
        "PRODUCT_AGGREGATE_DERIVED",
        "OPERATION_CONTRACT",
        "AI_DECISION",
        "MANUAL_MANAGER_ESTIMATE",
    }
)


def _result(
    *,
    row: ExecutionTaskCapacityAllocation,
    operation: str,
    transition_id: str,
    previous_status: str | None,
    previous_version: int | None,
    already_applied: bool,
    over_allocation: OverAllocationDetail | None = None,
    replacement_allocation_id: int | None = None,
    replacement_transition_id: str | None = None,
) -> AllocationCommandResult:
    return AllocationCommandResult(
        allocation_id=row.id,
        execution_plan_id=row.execution_plan_id,
        task_key=row.task_key,
        workcenter_code=row.workcenter_code or "",
        status=row.status,  # type: ignore[arg-type]
        version=row.version,
        quantity_minutes=row.quantity,
        unit="minutes",
        bucket_start=row.bucket_start,
        bucket_end=row.bucket_end,
        timezone=row.timezone,
        workload_source=row.workload_source,  # type: ignore[arg-type]
        operation=operation,  # type: ignore[arg-type]
        transition_id=transition_id,
        previous_status=previous_status,  # type: ignore[arg-type]
        previous_version=previous_version,
        already_applied=already_applied,
        over_allocation=over_allocation,
        replacement_allocation_id=replacement_allocation_id,
        replacement_transition_id=replacement_transition_id,
    )


async def _idempotent_or_conflict(
    repo: ExecutionTaskCapacityAllocationRepository,
    *,
    idempotency_key: str,
    fingerprint: dict[str, Any],
    match_fn,
) -> AllocationCommandResult | None:
    existing = await repo.get_transition_by_idempotency_key(idempotency_key)
    if existing is None:
        return None
    if not match_fn(existing, fingerprint):
        raise ResourceStateWriteError(
            "idempotency_payload_conflict",
            "idempotency_key already used with a different payload",
        )
    row = await repo.get_by_id(existing.allocation_id)
    if row is None:
        raise ResourceStateWriteError(
            "idempotency_orphaned_transition",
            "transition exists without allocation row",
        )
    return _result(
        row=row,
        operation=existing.operation,
        transition_id=existing.transition_id,
        previous_status=existing.previous_status,
        previous_version=existing.previous_version,
        already_applied=True,
    )


def _require_workload(source: str | None, quantity: int | None) -> None:
    if quantity is None:
        raise ResourceStateValidationError(
            "workload_minutes_required",
            "requested_minutes/quantity_minutes must not be null",
        )
    if quantity <= 0:
        raise ResourceStateValidationError(
            "invalid_quantity", "quantity_minutes must be > 0"
        )
    if not source or source not in WORKLOAD_SOURCES:
        raise ResourceStateValidationError(
            "invalid_workload_source",
            f"unsupported or missing workload_source: {source}",
        )


async def _load_active_source(
    source_repo: WorkcenterCapacitySourceRepository,
    *,
    workcenter_code: str,
    bucket_date,
    expected_source_version: int | None,
) -> WorkcenterCapacitySource:
    src = await source_repo.get_active_for_day(
        workcenter_code=workcenter_code, bucket_date=bucket_date
    )
    if src is None:
        raise ResourceStateWriteError(
            "capacity_source_missing",
            f"no ACTIVE workcenter capacity for {workcenter_code} on {bucket_date}",
        )
    if (
        expected_source_version is not None
        and src.version != expected_source_version
    ):
        raise ResourceStateWriteError(
            "cas_stale_source",
            "workcenter capacity source version mismatch",
        )
    return src


def _apply_over_allocation_policy(
    *,
    policy: str,
    available: int,
    allocated_before: int,
    requested: int,
    workcenter_code: str,
    bucket_start: datetime,
    bucket_end: datetime,
    reason_code: str | None,
    reason_note: str | None,
) -> OverAllocationDetail:
    allocated_after = allocated_before + requested
    excess = max(0, allocated_after - available)
    over = excess > 0
    detail = OverAllocationDetail(
        over_allocated=over,
        available_minutes=available,
        allocated_before=allocated_before,
        requested_minutes=requested,
        allocated_after=allocated_after,
        excess_minutes=excess,
        workcenter_code=workcenter_code,
        bucket_start=bucket_start,
        bucket_end=bucket_end,
        policy=policy,  # type: ignore[arg-type]
        reason_code=reason_code if over else None,
    )
    if not over:
        return detail
    if policy == "HARD_BLOCK":
        raise ResourceStateWriteError(
            "over_allocation",
            f"over-allocation blocked: excess={excess}",
        )
    if policy == "ALLOW_WITH_REASON":
        if not reason_code:
            raise ResourceStateValidationError(
                "over_allocation_reason_required",
                "ALLOW_WITH_REASON requires reason_code when over-allocated",
            )
        if not reason_note:
            raise ResourceStateValidationError(
                "over_allocation_reason_required",
                "ALLOW_WITH_REASON requires reason_note when over-allocated",
            )
    # WARN_ONLY: succeed with detail.over_allocated=True
    return detail


async def create_allocation(
    db: AsyncSession,
    *,
    command: CreateAllocationCommand,
    actor_user_id: str,
) -> AllocationCommandResult:
    if command.expected_version != 0:
        raise ResourceStateWriteError(
            "cas_stale_or_missing",
            "CREATE_ALLOCATION requires expected_version=0",
        )
    _require_workload(command.workload_source, command.quantity_minutes)
    if command.initial_status not in OPEN:
        raise ResourceStateValidationError(
            "invalid_status", "CREATE allows HELD or ALLOCATED only"
        )
    bucket_date = validate_day_bucket(
        command.bucket_start, command.bucket_end, command.timezone
    )
    wc = command.workcenter_code.strip()

    repo = ExecutionTaskCapacityAllocationRepository(db)
    source_repo = WorkcenterCapacitySourceRepository(db)
    fp = {
        "operation": "CREATE_ALLOCATION",
        "execution_plan_id": command.execution_plan_id,
        "task_key": command.task_key,
        "workcenter_code": wc,
        "quantity": command.quantity_minutes,
        "bucket_start": dt_key(command.bucket_start),
        "bucket_end": dt_key(command.bucket_end),
        "workload_source": command.workload_source,
        "expected_version": 0,
        "reason_code": command.reason_code,
        "actor_user_id": actor_user_id,
    }

    def _match(tr, f):
        return (
            tr.operation == f["operation"]
            and tr.execution_plan_id == f["execution_plan_id"]
            and tr.task_key == f["task_key"]
            and tr.new_quantity == f["quantity"]
            and dt_key(tr.new_bucket_start) == f["bucket_start"]
            and (tr.workload_source or "") == f["workload_source"]
            and (tr.reason_code or "") == f["reason_code"]
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
            src = await _load_active_source(
                source_repo,
                workcenter_code=wc,
                bucket_date=bucket_date,
                expected_source_version=command.expected_source_version,
            )
            allocated_before = await repo.sum_open_minutes_for_workcenter_bucket(
                workcenter_code=wc,
                bucket_start=command.bucket_start,
                bucket_end=command.bucket_end,
            )
            over = _apply_over_allocation_policy(
                policy=src.over_allocation_policy,
                available=src.available_minutes,
                allocated_before=allocated_before,
                requested=command.quantity_minutes,
                workcenter_code=wc,
                bucket_start=command.bucket_start,
                bucket_end=command.bucket_end,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
            )
            now = utcnow()
            tid = str(uuid.uuid4())
            row = ExecutionTaskCapacityAllocation(
                execution_plan_id=command.execution_plan_id,
                order_id=order_id,
                task_key=command.task_key,
                resource_scope_type="WORKCENTER",
                resource_scope_id=wc,
                workcenter_code=wc,
                machine_id=None,
                bucket_start=command.bucket_start,
                bucket_end=command.bucket_end,
                timezone=command.timezone,
                quantity=command.quantity_minutes,
                unit=CAPACITY_UNIT,
                workload_source=command.workload_source,
                workload_source_reference=command.workload_source_reference,
                workload_explanation=command.workload_explanation,
                status=command.initial_status,
                version=1,
                created_by=actor_user_id,
                updated_by=actor_user_id,
                created_at=now,
                updated_at=now,
                idempotency_key=command.idempotency_key,
            )
            await repo.add_allocation(row)
            await repo.add_transition(
                ExecutionTaskCapacityAllocationTransition(
                    transition_id=tid,
                    allocation_id=row.id,
                    execution_plan_id=row.execution_plan_id,
                    task_key=row.task_key,
                    resource_scope_type="WORKCENTER",
                    resource_scope_id=wc,
                    operation="CREATE_ALLOCATION",
                    previous_status=None,
                    new_status=command.initial_status,
                    previous_quantity=None,
                    new_quantity=command.quantity_minutes,
                    unit=CAPACITY_UNIT,
                    workload_source=command.workload_source,
                    workload_source_reference=command.workload_source_reference,
                    workload_explanation=command.workload_explanation,
                    previous_bucket_start=None,
                    previous_bucket_end=None,
                    new_bucket_start=command.bucket_start,
                    new_bucket_end=command.bucket_end,
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
        except ResourceStateWriteError:
            await db.rollback()
            raise
        except IntegrityError as exc:
            await db.rollback()
            raise ResourceStateWriteError(
                "conflict", "allocation integrity conflict"
            ) from exc

    return _result(
        row=row,
        operation="CREATE_ALLOCATION",
        transition_id=tid,
        previous_status=None,
        previous_version=None,
        already_applied=False,
        over_allocation=over,
    )


async def adjust_allocation(
    db: AsyncSession,
    *,
    allocation_id: int,
    command: AdjustAllocationCommand,
    actor_user_id: str,
) -> AllocationCommandResult:
    repo = ExecutionTaskCapacityAllocationRepository(db)
    source_repo = WorkcenterCapacitySourceRepository(db)
    fp = {
        "operation": "ADJUST_ALLOCATION",
        "allocation_id": allocation_id,
        "quantity": command.quantity_minutes,
        "expected_version": command.expected_version,
        "reason_code": command.reason_code,
        "actor_user_id": actor_user_id,
    }

    def _match(tr, f):
        return (
            tr.operation == f["operation"]
            and tr.allocation_id == f["allocation_id"]
            and tr.previous_version == f["expected_version"]
            and (tr.new_quantity == f["quantity"] or f["quantity"] is None)
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

    peek_row = await repo.get_by_id(allocation_id)
    if peek_row is None:
        raise ResourceStateNotFoundError(
            "allocation_not_found", f"allocation {allocation_id} not found"
        )
    order_id = int(peek_row.order_id)

    async with plan_order_lock(order_id):
        try:
            await require_active_domain_config(db, domain=DOMAIN)
            row = await repo.get_by_id(allocation_id)
            if row is None:
                raise ResourceStateNotFoundError(
                    "allocation_not_found", f"allocation {allocation_id} not found"
                )
            if row.status not in OPEN:
                raise ResourceStateWriteError(
                    "invalid_transition", "ADJUST requires open allocation"
                )
            if row.version != command.expected_version:
                raise ResourceStateWriteError("cas_stale", "expected_version mismatch")
            if row.resource_scope_type != "WORKCENTER" or not row.workcenter_code:
                raise ResourceStateWriteError(
                    "machine_scope_not_enabled",
                    "Stage 1 supports WORKCENTER allocations only",
                )

            new_qty = (
                command.quantity_minutes
                if command.quantity_minutes is not None
                else row.quantity
            )
            new_start = command.bucket_start or row.bucket_start
            new_end = command.bucket_end or row.bucket_end
            new_tz = command.timezone or row.timezone
            new_ws = command.workload_source or row.workload_source
            _require_workload(new_ws, new_qty)
            bucket_date = validate_day_bucket(new_start, new_end, new_tz)
            src = await _load_active_source(
                source_repo,
                workcenter_code=row.workcenter_code,
                bucket_date=bucket_date,
                expected_source_version=command.expected_source_version,
            )
            allocated_before = await repo.sum_open_minutes_for_workcenter_bucket(
                workcenter_code=row.workcenter_code,
                bucket_start=new_start,
                bucket_end=new_end,
                exclude_allocation_id=row.id,
            )
            over = _apply_over_allocation_policy(
                policy=src.over_allocation_policy,
                available=src.available_minutes,
                allocated_before=allocated_before,
                requested=new_qty,
                workcenter_code=row.workcenter_code,
                bucket_start=new_start,
                bucket_end=new_end,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
            )

            prev_status = row.status
            prev_ver = row.version
            prev_qty = row.quantity
            prev_start = row.bucket_start
            prev_end = row.bucket_end
            now = utcnow()
            tid = str(uuid.uuid4())
            row.quantity = new_qty
            row.bucket_start = new_start
            row.bucket_end = new_end
            row.timezone = new_tz
            row.workload_source = new_ws
            if command.workload_source_reference is not None:
                row.workload_source_reference = command.workload_source_reference
            if command.workload_explanation is not None:
                row.workload_explanation = command.workload_explanation
            row.version = prev_ver + 1
            row.updated_by = actor_user_id
            row.updated_at = now
            await repo.add_transition(
                ExecutionTaskCapacityAllocationTransition(
                    transition_id=tid,
                    allocation_id=row.id,
                    execution_plan_id=row.execution_plan_id,
                    task_key=row.task_key,
                    resource_scope_type="WORKCENTER",
                    resource_scope_id=row.workcenter_code,
                    operation="ADJUST_ALLOCATION",
                    previous_status=prev_status,
                    new_status=row.status,
                    previous_quantity=prev_qty,
                    new_quantity=new_qty,
                    unit=CAPACITY_UNIT,
                    workload_source=new_ws,
                    workload_source_reference=row.workload_source_reference,
                    workload_explanation=row.workload_explanation,
                    previous_bucket_start=prev_start,
                    previous_bucket_end=prev_end,
                    new_bucket_start=new_start,
                    new_bucket_end=new_end,
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
        except ResourceStateWriteError:
            await db.rollback()
            raise

    return _result(
        row=row,
        operation="ADJUST_ALLOCATION",
        transition_id=tid,
        previous_status=prev_status,
        previous_version=prev_ver,
        already_applied=False,
        over_allocation=over,
    )


async def _terminal_allocation(
    db: AsyncSession,
    *,
    allocation_id: int,
    expected_version: int,
    idempotency_key: str,
    reason_code: str,
    reason_note: str | None,
    correlation_id: str | None,
    actor_user_id: str,
    operation: str,
    new_status: str,
) -> AllocationCommandResult:
    repo = ExecutionTaskCapacityAllocationRepository(db)
    fp = {
        "operation": operation,
        "allocation_id": allocation_id,
        "expected_version": expected_version,
        "reason_code": reason_code,
        "actor_user_id": actor_user_id,
    }

    def _match(tr, f):
        return (
            tr.operation == f["operation"]
            and tr.allocation_id == f["allocation_id"]
            and tr.previous_version == f["expected_version"]
            and (tr.reason_code or "") == f["reason_code"]
            and (tr.actor_user_id or "") == f["actor_user_id"]
        )

    replay = await _idempotent_or_conflict(
        repo, idempotency_key=idempotency_key, fingerprint=fp, match_fn=_match
    )
    if replay is not None:
        return replay

    peek = await repo.get_by_id(allocation_id)
    if peek is None:
        raise ResourceStateNotFoundError(
            "allocation_not_found", f"allocation {allocation_id} not found"
        )
    order_id = int(peek.order_id)

    async with plan_order_lock(order_id):
        try:
            await require_active_domain_config(db, domain=DOMAIN)
            row = await repo.get_by_id(allocation_id)
            if row is None:
                raise ResourceStateNotFoundError(
                    "allocation_not_found", f"allocation {allocation_id} not found"
                )
            if row.status not in OPEN:
                raise ResourceStateWriteError(
                    "invalid_transition", f"{operation} requires open allocation"
                )
            if row.version != expected_version:
                raise ResourceStateWriteError("cas_stale", "expected_version mismatch")
            prev_status = row.status
            prev_ver = row.version
            now = utcnow()
            tid = str(uuid.uuid4())
            row.status = new_status
            row.version = prev_ver + 1
            row.updated_by = actor_user_id
            row.updated_at = now
            if new_status == "RELEASED":
                row.released_at = now
            if new_status == "CANCELLED":
                row.cancelled_at = now
            await repo.add_transition(
                ExecutionTaskCapacityAllocationTransition(
                    transition_id=tid,
                    allocation_id=row.id,
                    execution_plan_id=row.execution_plan_id,
                    task_key=row.task_key,
                    resource_scope_type=row.resource_scope_type,
                    resource_scope_id=row.resource_scope_id,
                    operation=operation,
                    previous_status=prev_status,
                    new_status=new_status,
                    previous_quantity=row.quantity,
                    new_quantity=row.quantity,
                    unit=CAPACITY_UNIT,
                    workload_source=row.workload_source,
                    workload_source_reference=row.workload_source_reference,
                    workload_explanation=row.workload_explanation,
                    previous_bucket_start=row.bucket_start,
                    previous_bucket_end=row.bucket_end,
                    new_bucket_start=row.bucket_start,
                    new_bucket_end=row.bucket_end,
                    previous_version=prev_ver,
                    new_version=row.version,
                    reason_code=reason_code,
                    reason_note=reason_note,
                    actor_user_id=actor_user_id,
                    idempotency_key=idempotency_key,
                    correlation_id=correlation_id,
                    created_at=now,
                )
            )
            await db.commit()
        except ResourceStateWriteError:
            await db.rollback()
            raise

    return _result(
        row=row,
        operation=operation,
        transition_id=tid,
        previous_status=prev_status,
        previous_version=prev_ver,
        already_applied=False,
    )


async def release_allocation(
    db: AsyncSession,
    *,
    allocation_id: int,
    command: ReleaseAllocationCommand,
    actor_user_id: str,
) -> AllocationCommandResult:
    return await _terminal_allocation(
        db,
        allocation_id=allocation_id,
        expected_version=command.expected_version,
        idempotency_key=command.idempotency_key,
        reason_code=command.reason_code,
        reason_note=command.reason_note,
        correlation_id=command.correlation_id,
        actor_user_id=actor_user_id,
        operation="RELEASE_ALLOCATION",
        new_status="RELEASED",
    )


async def cancel_allocation(
    db: AsyncSession,
    *,
    allocation_id: int,
    command: CancelAllocationCommand,
    actor_user_id: str,
) -> AllocationCommandResult:
    return await _terminal_allocation(
        db,
        allocation_id=allocation_id,
        expected_version=command.expected_version,
        idempotency_key=command.idempotency_key,
        reason_code=command.reason_code,
        reason_note=command.reason_note,
        correlation_id=command.correlation_id,
        actor_user_id=actor_user_id,
        operation="CANCEL_ALLOCATION",
        new_status="CANCELLED",
    )


async def supersede_allocation(
    db: AsyncSession,
    *,
    allocation_id: int,
    command: SupersedeAllocationCommand,
    actor_user_id: str,
) -> AllocationCommandResult:
    _require_workload(command.workload_source, command.quantity_minutes)
    bucket_date = validate_day_bucket(
        command.bucket_start, command.bucket_end, command.timezone
    )
    wc = command.workcenter_code.strip()
    repo = ExecutionTaskCapacityAllocationRepository(db)
    source_repo = WorkcenterCapacitySourceRepository(db)

    existing = await repo.get_transition_by_idempotency_key(command.idempotency_key)
    if existing is not None:
        if existing.operation != "SUPERSEDE_ALLOCATION":
            raise ResourceStateWriteError(
                "idempotency_payload_conflict",
                "idempotency_key already used with a different payload",
            )
        old = await repo.get_by_id(allocation_id)
        if old is None or old.superseded_by_id is None:
            raise ResourceStateWriteError(
                "idempotency_orphaned_transition", "supersede without replacement"
            )
        return _result(
            row=old,
            operation="SUPERSEDE_ALLOCATION",
            transition_id=existing.transition_id,
            previous_status=existing.previous_status,
            previous_version=existing.previous_version,
            already_applied=True,
            replacement_allocation_id=old.superseded_by_id,
        )

    peek = await repo.get_by_id(allocation_id)
    if peek is None:
        raise ResourceStateNotFoundError(
            "allocation_not_found", f"allocation {allocation_id} not found"
        )
    order_id = int(peek.order_id)

    async with plan_order_lock(order_id):
        try:
            plan = await load_plan_for_update(db, plan_id=peek.execution_plan_id)
            await require_active_domain_config(db, domain=DOMAIN)
            require_task_in_plan(plan, peek.task_key)
            row = await repo.get_by_id(allocation_id)
            if row is None or row.status not in OPEN:
                raise ResourceStateWriteError(
                    "invalid_transition", "SUPERSEDE requires open allocation"
                )
            if row.version != command.expected_version:
                raise ResourceStateWriteError("cas_stale", "expected_version mismatch")
            src = await _load_active_source(
                source_repo,
                workcenter_code=wc,
                bucket_date=bucket_date,
                expected_source_version=command.expected_source_version,
            )
            allocated_before = await repo.sum_open_minutes_for_workcenter_bucket(
                workcenter_code=wc,
                bucket_start=command.bucket_start,
                bucket_end=command.bucket_end,
                exclude_allocation_id=row.id,
            )
            over = _apply_over_allocation_policy(
                policy=src.over_allocation_policy,
                available=src.available_minutes,
                allocated_before=allocated_before,
                requested=command.quantity_minutes,
                workcenter_code=wc,
                bucket_start=command.bucket_start,
                bucket_end=command.bucket_end,
                reason_code=command.reason_code,
                reason_note=command.reason_note,
            )
            prev_status = row.status
            prev_ver = row.version
            now = utcnow()
            tid = str(uuid.uuid4())
            repl_tid = str(uuid.uuid4())
            row.status = "SUPERSEDED"
            row.version = prev_ver + 1
            row.updated_by = actor_user_id
            row.updated_at = now
            await db.flush()
            replacement = ExecutionTaskCapacityAllocation(
                execution_plan_id=row.execution_plan_id,
                order_id=row.order_id,
                task_key=row.task_key,
                resource_scope_type="WORKCENTER",
                resource_scope_id=wc,
                workcenter_code=wc,
                machine_id=None,
                bucket_start=command.bucket_start,
                bucket_end=command.bucket_end,
                timezone=command.timezone,
                quantity=command.quantity_minutes,
                unit=CAPACITY_UNIT,
                workload_source=command.workload_source,
                workload_source_reference=command.workload_source_reference,
                workload_explanation=command.workload_explanation,
                status=command.initial_status,
                version=1,
                created_by=actor_user_id,
                updated_by=actor_user_id,
                created_at=now,
                updated_at=now,
                idempotency_key=command.replacement_idempotency_key,
            )
            await repo.add_allocation(replacement)
            row.superseded_by_id = replacement.id
            await repo.add_transition(
                ExecutionTaskCapacityAllocationTransition(
                    transition_id=tid,
                    allocation_id=row.id,
                    execution_plan_id=row.execution_plan_id,
                    task_key=row.task_key,
                    resource_scope_type="WORKCENTER",
                    resource_scope_id=wc,
                    operation="SUPERSEDE_ALLOCATION",
                    previous_status=prev_status,
                    new_status="SUPERSEDED",
                    previous_quantity=row.quantity,
                    new_quantity=command.quantity_minutes,
                    unit=CAPACITY_UNIT,
                    workload_source=command.workload_source,
                    previous_bucket_start=row.bucket_start,
                    previous_bucket_end=row.bucket_end,
                    new_bucket_start=command.bucket_start,
                    new_bucket_end=command.bucket_end,
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
                ExecutionTaskCapacityAllocationTransition(
                    transition_id=repl_tid,
                    allocation_id=replacement.id,
                    execution_plan_id=replacement.execution_plan_id,
                    task_key=replacement.task_key,
                    resource_scope_type="WORKCENTER",
                    resource_scope_id=wc,
                    operation="CREATE_ALLOCATION",
                    previous_status=None,
                    new_status=command.initial_status,
                    previous_quantity=None,
                    new_quantity=command.quantity_minutes,
                    unit=CAPACITY_UNIT,
                    workload_source=command.workload_source,
                    new_bucket_start=command.bucket_start,
                    new_bucket_end=command.bucket_end,
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
        except ResourceStateWriteError:
            await db.rollback()
            raise
        except IntegrityError as exc:
            await db.rollback()
            raise ResourceStateWriteError(
                "conflict", "supersede integrity conflict"
            ) from exc

    return _result(
        row=row,
        operation="SUPERSEDE_ALLOCATION",
        transition_id=tid,
        previous_status=prev_status,
        previous_version=prev_ver,
        already_applied=False,
        over_allocation=over,
        replacement_allocation_id=replacement.id,
        replacement_transition_id=repl_tid,
    )
