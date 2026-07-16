"""Help request lifecycle — Phase 2 broadcast OPEN / targeted (membership-as-acceptance)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_task_help_request import ExecutionTaskHelpRequest
from models.orders import Orders
from schemas.execution_task_help import (
    HELP_STATUS_CANCELLED,
    HELP_STATUS_CLOSED,
    HELP_STATUS_DECLINED,
    HELP_STATUS_OPEN,
    HelpActionResponse,
    HelpRequestCreateBody,
    HelpRequestListResponse,
    HelpRequestRead,
)
from services.execution_plan_operational_readiness_service import (
    STATUS_V2_OPERATIONAL_READY,
    evaluate_execution_plan_operational_readiness,
)
from services.execution_plan_task_parser import operational_tasks_only
from services.execution_task_membership_service import join_helper_membership
from services.flex_membership_flags import is_collab_phase2_enabled
from services.operational_registry_service import OperationalRegistryService

_TERMINAL_ORDER_STATUSES = frozenset({"completed", "cancelled"})
_help_locks: dict[tuple[int, str], asyncio.Lock] = {}
_help_locks_guard = asyncio.Lock()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _assert_phase2() -> None:
    if not is_collab_phase2_enabled():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "collab_phase2_disabled",
                "message": "Collaboration Phase 2 help/work APIs are disabled.",
            },
        )


async def _lock_for(order_id: int, task_id: str) -> asyncio.Lock:
    key = (order_id, task_id)
    async with _help_locks_guard:
        lock = _help_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            _help_locks[key] = lock
        return lock


def _serialize(row: ExecutionTaskHelpRequest) -> HelpRequestRead:
    targeted = row.targeted_employee_id
    return HelpRequestRead(
        help_request_id=int(row.id),
        order_id=int(row.order_id),
        task_id=str(row.task_id),
        requested_by_employee_id=int(row.requested_by_employee_id),
        targeted_employee_id=int(targeted) if targeted is not None else None,
        status=row.status,  # type: ignore[arg-type]
        reason=row.reason,
        competence_hint=row.competence_hint,
        created_at=_iso(row.created_at) or "",
        updated_at=_iso(row.updated_at) or "",
        closed_at=_iso(row.closed_at),
        is_broadcast=targeted is None,
    )


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


def _require_v2(plan: ExecutionPlan) -> None:
    readiness = evaluate_execution_plan_operational_readiness(plan)
    if readiness.status != STATUS_V2_OPERATIONAL_READY:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "v2_materialization_required",
                "message": "Help requests require a materialized V2 operational task.",
                "readiness_status": readiness.status,
            },
        )


def _find_task(plan: ExecutionPlan, task_id: str) -> dict[str, Any]:
    tasks = operational_tasks_only(plan.tasks_json)
    match = next(
        (t for t in tasks if isinstance(t, dict) and str(t.get("task_id") or "") == task_id),
        None,
    )
    if match is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "task_not_found", "message": "Task not on V2 operational plan."},
        )
    return match


async def _assert_eligible(
    db: AsyncSession, *, employee_id: int, plan_task: dict[str, Any]
) -> None:
    process_type = str(
        plan_task.get("process_type")
        or plan_task.get("process_id")
        or plan_task.get("source_operation_code")
        or ""
    ).strip()
    machine_type = str(plan_task.get("machine_type") or "").strip() or None
    if not process_type:
        raise HTTPException(status_code=409, detail={"error": "task_operation_unresolved"})
    registry = OperationalRegistryService(db)
    eligibility = await registry.check_employee_operation_eligibility(
        employee_id, process_type, machine_type=machine_type
    )
    if not eligibility.get("eligible"):
        raise HTTPException(
            status_code=403,
            detail={"error": "employee_not_eligible", "eligibility": eligibility},
        )


async def create_help_request(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    requested_by_employee_id: int,
    body: HelpRequestCreateBody,
) -> HelpActionResponse:
    _assert_phase2()
    task_id = str(task_id or "").strip()
    if not task_id:
        raise HTTPException(status_code=422, detail={"error": "task_id_invalid"})

    order = await _load_order(db, order_id)
    if str(order.status or "").strip().lower() in _TERMINAL_ORDER_STATUSES:
        raise HTTPException(status_code=409, detail={"error": "order_not_active"})

    plan = await _load_latest_plan(db, order_id)
    _require_v2(plan)
    _find_task(plan, task_id)

    target = body.targeted_employee_id
    if target is not None:
        if target <= 0:
            raise HTTPException(status_code=422, detail={"error": "targeted_employee_id_invalid"})
        emp = (
            await db.execute(select(Employees).where(Employees.id == target))
        ).scalar_one_or_none()
        if emp is None:
            raise HTTPException(status_code=404, detail={"error": "targeted_employee_not_found"})

    lock = await _lock_for(order_id, task_id)
    async with lock:
        existing_open = (
            await db.execute(
                select(ExecutionTaskHelpRequest)
                .where(
                    ExecutionTaskHelpRequest.order_id == order_id,
                    ExecutionTaskHelpRequest.task_id == task_id,
                    ExecutionTaskHelpRequest.status == HELP_STATUS_OPEN,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if existing_open is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "help_already_open",
                    "message": "An OPEN help request already exists for this task.",
                    "help_request_id": existing_open.id,
                },
            )

        now = _utcnow()
        row = ExecutionTaskHelpRequest(
            order_id=order_id,
            task_id=task_id,
            requested_by_employee_id=requested_by_employee_id,
            targeted_employee_id=target,
            status=HELP_STATUS_OPEN,
            reason=(body.reason or None),
            competence_hint=(body.competence_hint or None),
            execution_plan_id=plan.id,
            closed_at=None,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=409,
                detail={"error": "help_already_open", "message": "Concurrent OPEN help exists."},
            )
        await db.refresh(row)
        return HelpActionResponse(action="create", help_request=_serialize(row))


async def accept_help_request(
    db: AsyncSession,
    *,
    order_id: int,
    help_request_id: int,
    employee_id: int,
) -> HelpActionResponse:
    _assert_phase2()
    lock_key_task = ""
    # Load then lock by task
    row = (
        await db.execute(
            select(ExecutionTaskHelpRequest).where(
                ExecutionTaskHelpRequest.id == help_request_id,
                ExecutionTaskHelpRequest.order_id == order_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "help_request_not_found"})
    lock_key_task = str(row.task_id)

    lock = await _lock_for(order_id, lock_key_task)
    async with lock:
        row = (
            await db.execute(
                select(ExecutionTaskHelpRequest)
                .where(
                    ExecutionTaskHelpRequest.id == help_request_id,
                    ExecutionTaskHelpRequest.order_id == order_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail={"error": "help_request_not_found"})
        if row.status != HELP_STATUS_OPEN:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "help_not_open",
                    "message": "Only OPEN help requests can be accepted.",
                    "status": row.status,
                },
            )

        targeted = row.targeted_employee_id
        if targeted is not None and int(targeted) != int(employee_id):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "help_targeted_other",
                    "message": "Only the targeted employee may accept this help request.",
                },
            )

        plan = await _load_latest_plan(db, order_id)
        plan_task = _find_task(plan, str(row.task_id))
        await _assert_eligible(db, employee_id=employee_id, plan_task=plan_task)

        membership = await join_helper_membership(
            db,
            order_id=order_id,
            task_id=str(row.task_id),
            employee_id=employee_id,
            joined_by_employee_id=employee_id,
            join_source="help_accept",
            source_help_request_id=int(row.id),
        )

        # Re-load help row after membership commit (separate transaction)
        row = (
            await db.execute(
                select(ExecutionTaskHelpRequest)
                .where(ExecutionTaskHelpRequest.id == help_request_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail={"error": "help_request_not_found"})

        if targeted is not None and row.status == HELP_STATUS_OPEN:
            now = _utcnow()
            row.status = HELP_STATUS_CLOSED
            row.closed_at = now
            row.updated_at = now
            await db.commit()
            await db.refresh(row)

        return HelpActionResponse(
            action="accept",
            help_request=_serialize(row),
            membership_already_active=bool(membership.already_joined),
            membership_reactivated=bool(membership.reactivated),
            membership_id=membership.membership.membership_id,
        )


async def decline_help_request(
    db: AsyncSession,
    *,
    order_id: int,
    help_request_id: int,
    employee_id: int,
) -> HelpActionResponse:
    _assert_phase2()
    row = (
        await db.execute(
            select(ExecutionTaskHelpRequest).where(
                ExecutionTaskHelpRequest.id == help_request_id,
                ExecutionTaskHelpRequest.order_id == order_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "help_request_not_found"})

    lock = await _lock_for(order_id, str(row.task_id))
    async with lock:
        row = (
            await db.execute(
                select(ExecutionTaskHelpRequest)
                .where(ExecutionTaskHelpRequest.id == help_request_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail={"error": "help_request_not_found"})
        if row.status != HELP_STATUS_OPEN:
            raise HTTPException(status_code=409, detail={"error": "help_not_open"})
        if row.targeted_employee_id is None:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "decline_requires_targeted",
                    "message": "Only targeted help requests can be declined.",
                },
            )
        if int(row.targeted_employee_id) != int(employee_id):
            raise HTTPException(status_code=403, detail={"error": "help_targeted_other"})

        now = _utcnow()
        row.status = HELP_STATUS_DECLINED
        row.closed_at = now
        row.updated_at = now
        await db.commit()
        await db.refresh(row)
        return HelpActionResponse(action="decline", help_request=_serialize(row))


async def cancel_help_request(
    db: AsyncSession,
    *,
    order_id: int,
    help_request_id: int,
    actor_employee_id: int,
) -> HelpActionResponse:
    """Cancel OPEN help — does not revoke memberships."""
    _assert_phase2()
    return await _close_like(
        db,
        order_id=order_id,
        help_request_id=help_request_id,
        actor_employee_id=actor_employee_id,
        new_status=HELP_STATUS_CANCELLED,
        action="cancel",
    )


async def close_help_request(
    db: AsyncSession,
    *,
    order_id: int,
    help_request_id: int,
    actor_employee_id: int,
) -> HelpActionResponse:
    _assert_phase2()
    return await _close_like(
        db,
        order_id=order_id,
        help_request_id=help_request_id,
        actor_employee_id=actor_employee_id,
        new_status=HELP_STATUS_CLOSED,
        action="close",
    )


async def _close_like(
    db: AsyncSession,
    *,
    order_id: int,
    help_request_id: int,
    actor_employee_id: int,
    new_status: str,
    action: str,
) -> HelpActionResponse:
    row = (
        await db.execute(
            select(ExecutionTaskHelpRequest).where(
                ExecutionTaskHelpRequest.id == help_request_id,
                ExecutionTaskHelpRequest.order_id == order_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "help_request_not_found"})

    lock = await _lock_for(order_id, str(row.task_id))
    async with lock:
        row = (
            await db.execute(
                select(ExecutionTaskHelpRequest)
                .where(ExecutionTaskHelpRequest.id == help_request_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail={"error": "help_request_not_found"})
        if row.status != HELP_STATUS_OPEN:
            # Idempotent: already terminal
            return HelpActionResponse(action=action, help_request=_serialize(row))  # type: ignore[arg-type]

        now = _utcnow()
        row.status = new_status
        row.closed_at = now
        row.updated_at = now
        await db.commit()
        await db.refresh(row)
        return HelpActionResponse(action=action, help_request=_serialize(row))  # type: ignore[arg-type]


async def close_open_help_for_task(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
) -> int:
    """Auto-close remaining OPEN help when operation is explicitly completed. Returns count closed."""
    if not is_collab_phase2_enabled():
        return 0
    task_id = str(task_id or "").strip()
    rows = list(
        (
            await db.execute(
                select(ExecutionTaskHelpRequest).where(
                    ExecutionTaskHelpRequest.order_id == order_id,
                    ExecutionTaskHelpRequest.task_id == task_id,
                    ExecutionTaskHelpRequest.status == HELP_STATUS_OPEN,
                )
            )
        ).scalars().all()
    )
    if not rows:
        return 0
    now = _utcnow()
    for row in rows:
        row.status = HELP_STATUS_CLOSED
        row.closed_at = now
        row.updated_at = now
    await db.commit()
    return len(rows)


async def list_help_requests_for_task(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
) -> HelpRequestListResponse:
    rows = list(
        (
            await db.execute(
                select(ExecutionTaskHelpRequest)
                .where(
                    ExecutionTaskHelpRequest.order_id == order_id,
                    ExecutionTaskHelpRequest.task_id == task_id,
                )
                .order_by(ExecutionTaskHelpRequest.id.desc())
            )
        ).scalars().all()
    )
    return HelpRequestListResponse(
        order_id=order_id,
        task_id=task_id,
        help_requests=[_serialize(r) for r in rows],
    )


async def list_open_help_for_order(
    db: AsyncSession, *, order_id: int
) -> list[ExecutionTaskHelpRequest]:
    return list(
        (
            await db.execute(
                select(ExecutionTaskHelpRequest).where(
                    ExecutionTaskHelpRequest.order_id == order_id,
                    ExecutionTaskHelpRequest.status == HELP_STATUS_OPEN,
                )
            )
        ).scalars().all()
    )
