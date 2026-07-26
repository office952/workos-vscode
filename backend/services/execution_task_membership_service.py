"""HELPER collaboration membership — join/leave (Phase 1).

Membership is authorization intent only. Does not start sessions, claim tasks,
change assignment, mark progress, or complete operations.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_task_participant import ExecutionTaskParticipant
from models.orders import Orders
from schemas.execution_task_membership import (
    MEMBERSHIP_ROLE_HELPER,
    MEMBERSHIP_STATUS_ACTIVE,
    MEMBERSHIP_STATUS_INACTIVE,
    HelperMembershipRead,
    MembershipActionResponse,
    TaskMembershipListResponse,
)
from services.execution_plan_operational_readiness_service import (
    STATUS_V2_OPERATIONAL_READY,
    evaluate_execution_plan_operational_readiness,
)
from services.execution_plan_task_parser import operational_tasks_only
from services.flex_membership_flags import is_membership_api_enabled
from services.operational_registry_service import OperationalRegistryService

_TERMINAL_ORDER_STATUSES = frozenset({"completed", "cancelled"})

# Per-(order_id, task_id) asyncio locks — mirrors assignment service pattern.
_membership_locks: dict[tuple[int, str], asyncio.Lock] = {}
_membership_locks_guard = asyncio.Lock()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


async def _lock_for(order_id: int, task_id: str) -> asyncio.Lock:
    key = (order_id, task_id)
    async with _membership_locks_guard:
        lock = _membership_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            _membership_locks[key] = lock
        return lock


def _assert_writes_enabled() -> None:
    if not is_membership_api_enabled():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "membership_api_disabled",
                "message": "Collaboration membership writes are disabled.",
            },
        )


def _serialize_membership(
    row: ExecutionTaskParticipant,
    *,
    employee_name: str | None = None,
) -> HelperMembershipRead:
    return HelperMembershipRead(
        membership_id=row.id,
        employee_id=int(row.employee_id),
        employee_name=employee_name,
        status=MEMBERSHIP_STATUS_ACTIVE
        if row.status == MEMBERSHIP_STATUS_ACTIVE
        else MEMBERSHIP_STATUS_INACTIVE,
        role=MEMBERSHIP_ROLE_HELPER,
        joined_at=_iso(row.joined_at) or "",
        left_at=_iso(row.left_at),
        join_source=row.join_source,
    )


async def _employee_name(db: AsyncSession, employee_id: int) -> str | None:
    row = (
        await db.execute(select(Employees.name).where(Employees.id == employee_id))
    ).scalar_one_or_none()
    if row is None:
        return None
    return str(row).strip() or None


async def _load_order(db: AsyncSession, order_id: int) -> Orders:
    order = (
        await db.execute(select(Orders).where(Orders.id == order_id))
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})
    return order


async def _load_latest_plan(db: AsyncSession, order_id: int) -> ExecutionPlan:
    plan = (
        await db.execute(
            select(ExecutionPlan)
            .where(ExecutionPlan.order_id == order_id)
            .order_by(ExecutionPlan.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "execution_plan_not_found"})
    return plan


def _require_v2_materialized(plan: ExecutionPlan) -> None:
    readiness = evaluate_execution_plan_operational_readiness(plan)
    if readiness.status != STATUS_V2_OPERATIONAL_READY:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "v2_materialization_required",
                "message": "Collaboration membership requires a materialized V2 operational task.",
                "readiness_status": readiness.status,
            },
        )


def _find_operational_task(plan: ExecutionPlan, task_id: str) -> dict[str, Any]:
    tasks = operational_tasks_only(plan.tasks_json)
    match = next(
        (t for t in tasks if isinstance(t, dict) and str(t.get("task_id") or "") == task_id),
        None,
    )
    if match is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "task_not_found",
                "message": "Task not found on materialized V2 operational plan.",
            },
        )
    return match


async def _assert_eligible(
    db: AsyncSession,
    *,
    employee_id: int,
    plan_task: dict[str, Any],
) -> None:
    process_type = str(
        plan_task.get("process_type")
        or plan_task.get("process_id")
        or plan_task.get("source_operation_code")
        or ""
    ).strip()
    machine_type = str(plan_task.get("machine_type") or "").strip() or None
    if not process_type:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "task_operation_unresolved",
                "message": "Operational task has no process_type for eligibility.",
            },
        )
    registry = OperationalRegistryService(db)
    eligibility = await registry.check_employee_operation_eligibility(
        employee_id,
        process_type,
        machine_type=machine_type,
    )
    if not eligibility.get("eligible"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "employee_not_eligible",
                "message": "Employee is not eligible to collaborate on this operation.",
                "eligibility": eligibility,
            },
        )


async def _get_membership_for_update(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
) -> ExecutionTaskParticipant | None:
    stmt = (
        select(ExecutionTaskParticipant)
        .where(
            ExecutionTaskParticipant.order_id == order_id,
            ExecutionTaskParticipant.task_id == task_id,
            ExecutionTaskParticipant.employee_id == employee_id,
        )
        .with_for_update()
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def join_helper_membership(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
    joined_by_employee_id: int | None = None,
    join_source: str = "self_join",
    source_help_request_id: int | None = None,
    skip_eligibility: bool = False,
) -> MembershipActionResponse:
    """Create or reactivate HELPER membership. No session/assignment/claim side effects."""
    _assert_writes_enabled()

    if not isinstance(order_id, int) or order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    if not isinstance(employee_id, int) or employee_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "employee_id_invalid"})
    task_id = str(task_id or "").strip()
    if not task_id:
        raise HTTPException(status_code=422, detail={"error": "task_id_invalid"})

    employee = (
        await db.execute(select(Employees).where(Employees.id == employee_id))
    ).scalar_one_or_none()
    if employee is None:
        raise HTTPException(status_code=404, detail={"error": "employee_not_found"})
    emp_status = str(getattr(employee, "status", "") or "").strip().lower()
    if emp_status != "active":
        raise HTTPException(
            status_code=409,
            detail={"error": "employee_not_active"},
        )

    order = await _load_order(db, order_id)
    if str(order.status or "").strip().lower() in _TERMINAL_ORDER_STATUSES:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "order_not_active",
                "message": "Cannot join collaboration on a terminal order.",
            },
        )

    plan = await _load_latest_plan(db, order_id)
    _require_v2_materialized(plan)
    plan_task = _find_operational_task(plan, task_id)
    if not skip_eligibility:
        await _assert_eligible(db, employee_id=employee_id, plan_task=plan_task)

    lock = await _lock_for(order_id, task_id)
    async with lock:
        existing = await _get_membership_for_update(
            db,
            order_id=order_id,
            task_id=task_id,
            employee_id=employee_id,
        )
        now = _utcnow()
        actor = joined_by_employee_id if joined_by_employee_id is not None else employee_id

        if existing is not None and existing.status == MEMBERSHIP_STATUS_ACTIVE:
            if source_help_request_id is not None and getattr(
                existing, "source_help_request_id", None
            ) is None:
                existing.source_help_request_id = source_help_request_id
                existing.updated_at = now
                await db.commit()
                await db.refresh(existing)
            name = await _employee_name(db, employee_id)
            return MembershipActionResponse(
                action="join",
                order_id=order_id,
                task_id=task_id,
                employee_id=employee_id,
                membership=_serialize_membership(existing, employee_name=name),
                already_joined=True,
            )

        if existing is not None:
            # Reactivate same row — history model from Phase 1 plan.
            existing.status = MEMBERSHIP_STATUS_ACTIVE
            existing.role = MEMBERSHIP_ROLE_HELPER
            existing.left_at = None
            existing.joined_at = now
            existing.joined_by_employee_id = actor
            existing.join_source = join_source
            existing.execution_plan_id = plan.id
            existing.updated_at = now
            if source_help_request_id is not None:
                existing.source_help_request_id = source_help_request_id
            await db.commit()
            await db.refresh(existing)
            name = await _employee_name(db, employee_id)
            return MembershipActionResponse(
                action="join",
                order_id=order_id,
                task_id=task_id,
                employee_id=employee_id,
                membership=_serialize_membership(existing, employee_name=name),
                reactivated=True,
            )

        row = ExecutionTaskParticipant(
            order_id=order_id,
            task_id=task_id,
            employee_id=employee_id,
            role=MEMBERSHIP_ROLE_HELPER,
            status=MEMBERSHIP_STATUS_ACTIVE,
            joined_at=now,
            left_at=None,
            joined_by_employee_id=actor,
            join_source=join_source,
            source_help_request_id=source_help_request_id,
            execution_plan_id=plan.id,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raced = await _get_membership_for_update(
                db,
                order_id=order_id,
                task_id=task_id,
                employee_id=employee_id,
            )
            if raced is None:
                raise
            if raced.status != MEMBERSHIP_STATUS_ACTIVE:
                raced.status = MEMBERSHIP_STATUS_ACTIVE
                raced.role = MEMBERSHIP_ROLE_HELPER
                raced.left_at = None
                raced.joined_at = _utcnow()
                raced.joined_by_employee_id = actor
                raced.join_source = join_source
                raced.execution_plan_id = plan.id
                raced.updated_at = _utcnow()
                if source_help_request_id is not None:
                    raced.source_help_request_id = source_help_request_id
                await db.commit()
                await db.refresh(raced)
                name = await _employee_name(db, employee_id)
                return MembershipActionResponse(
                    action="join",
                    order_id=order_id,
                    task_id=task_id,
                    employee_id=employee_id,
                    membership=_serialize_membership(raced, employee_name=name),
                    reactivated=True,
                )
            name = await _employee_name(db, employee_id)
            return MembershipActionResponse(
                action="join",
                order_id=order_id,
                task_id=task_id,
                employee_id=employee_id,
                membership=_serialize_membership(raced, employee_name=name),
                already_joined=True,
            )

        await db.refresh(row)
        name = await _employee_name(db, employee_id)
        return MembershipActionResponse(
            action="join",
            order_id=order_id,
            task_id=task_id,
            employee_id=employee_id,
            membership=_serialize_membership(row, employee_name=name),
        )


async def leave_helper_membership(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
) -> MembershipActionResponse:
    """Close actor's own HELPER membership. Does not stop sessions or change assignment."""
    _assert_writes_enabled()

    if not isinstance(order_id, int) or order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    if not isinstance(employee_id, int) or employee_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "employee_id_invalid"})
    task_id = str(task_id or "").strip()
    if not task_id:
        raise HTTPException(status_code=422, detail={"error": "task_id_invalid"})

    lock = await _lock_for(order_id, task_id)
    async with lock:
        existing = await _get_membership_for_update(
            db,
            order_id=order_id,
            task_id=task_id,
            employee_id=employee_id,
        )
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "membership_not_found",
                    "message": "No collaboration membership found for this employee on the task.",
                },
            )

        name = await _employee_name(db, employee_id)
        if existing.status != MEMBERSHIP_STATUS_ACTIVE:
            return MembershipActionResponse(
                action="leave",
                order_id=order_id,
                task_id=task_id,
                employee_id=employee_id,
                membership=_serialize_membership(existing, employee_name=name),
                already_left=True,
            )

        now = _utcnow()
        existing.status = MEMBERSHIP_STATUS_INACTIVE
        existing.left_at = now
        existing.updated_at = now
        await db.commit()
        await db.refresh(existing)
        return MembershipActionResponse(
            action="leave",
            order_id=order_id,
            task_id=task_id,
            employee_id=employee_id,
            membership=_serialize_membership(existing, employee_name=name),
        )


async def list_task_memberships(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
) -> TaskMembershipListResponse:
    task_id = str(task_id or "").strip()
    rows = (
        await db.execute(
            select(ExecutionTaskParticipant)
            .where(
                ExecutionTaskParticipant.order_id == order_id,
                ExecutionTaskParticipant.task_id == task_id,
            )
            .order_by(
                ExecutionTaskParticipant.status.asc(),
                ExecutionTaskParticipant.joined_at.desc(),
            )
        )
    ).scalars().all()

    names_sql = text("SELECT id, name FROM employees")
    name_map = {
        int(r["id"]): str(r["name"] or "").strip() or None
        for r in (await db.execute(names_sql)).mappings()
    }

    memberships = [
        _serialize_membership(row, employee_name=name_map.get(int(row.employee_id)))
        for row in rows
    ]
    active_count = sum(1 for m in memberships if m.status == MEMBERSHIP_STATUS_ACTIVE)
    return TaskMembershipListResponse(
        order_id=order_id,
        task_id=task_id,
        memberships=memberships,
        active_count=active_count,
    )


async def list_order_memberships_by_task(
    db: AsyncSession,
    order_id: int,
) -> dict[str, list[HelperMembershipRead]]:
    """Load all memberships for an order, keyed by task_id (for collaboration read)."""
    rows = (
        await db.execute(
            select(ExecutionTaskParticipant).where(
                ExecutionTaskParticipant.order_id == order_id
            )
        )
    ).scalars().all()
    if not rows:
        return {}

    names_sql = text("SELECT id, name FROM employees")
    name_map = {
        int(r["id"]): str(r["name"] or "").strip() or None
        for r in (await db.execute(names_sql)).mappings()
    }

    by_task: dict[str, list[HelperMembershipRead]] = {}
    for row in rows:
        tid = str(row.task_id)
        by_task.setdefault(tid, []).append(
            _serialize_membership(row, employee_name=name_map.get(int(row.employee_id)))
        )
    for tid in by_task:
        by_task[tid].sort(
            key=lambda m: (0 if m.status == MEMBERSHIP_STATUS_ACTIVE else 1, m.joined_at),
        )
    return by_task


async def list_active_helper_memberships_for_employee(
    db: AsyncSession,
    *,
    employee_id: int,
) -> list[ExecutionTaskParticipant]:
    """Active HELPER memberships for pool/visibility (Phase 2)."""
    return list(
        (
            await db.execute(
                select(ExecutionTaskParticipant).where(
                    ExecutionTaskParticipant.employee_id == employee_id,
                    ExecutionTaskParticipant.status == MEMBERSHIP_STATUS_ACTIVE,
                )
            )
        )
        .scalars()
        .all()
    )


async def employee_has_active_helper_membership(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
) -> bool:
    row = (
        await db.execute(
            select(ExecutionTaskParticipant.id).where(
                ExecutionTaskParticipant.order_id == order_id,
                ExecutionTaskParticipant.task_id == task_id,
                ExecutionTaskParticipant.employee_id == employee_id,
                ExecutionTaskParticipant.status == MEMBERSHIP_STATUS_ACTIVE,
            )
        )
    ).scalar_one_or_none()
    return row is not None
