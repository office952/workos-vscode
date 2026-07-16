"""Helper work session start/stop — Phase 2 (membership-gated, not claim)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.execution_task_participant import ExecutionTaskParticipant
from models.orders import Orders
from schemas.execution_task_membership import MEMBERSHIP_STATUS_ACTIVE
from services.execution_reality_service import ExecutionRealityService, RealityInputError
from services.execution_task_membership_service import (
    _assert_eligible,
    _find_operational_task,
    _load_latest_plan,
    _require_v2_materialized,
)
from services.flex_membership_flags import is_collab_phase2_enabled
from services.task_work_session_service import (
    ROLE_HELPER,
    SESSION_TYPE_ASSIST,
    is_session_active,
)

_TERMINAL_ORDER_STATUSES = frozenset({"completed", "cancelled"})


def _assert_phase2() -> None:
    if not is_collab_phase2_enabled():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "collab_phase2_disabled",
                "message": "Collaboration Phase 2 helper work APIs are disabled.",
            },
        )


async def _require_active_membership(
    db: AsyncSession, *, order_id: int, task_id: str, employee_id: int
) -> ExecutionTaskParticipant:
    row = (
        await db.execute(
            select(ExecutionTaskParticipant).where(
                ExecutionTaskParticipant.order_id == order_id,
                ExecutionTaskParticipant.task_id == task_id,
                ExecutionTaskParticipant.employee_id == employee_id,
                ExecutionTaskParticipant.status == MEMBERSHIP_STATUS_ACTIVE,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "helper_membership_required",
                "message": "Active HELPER membership is required to start helper work.",
            },
        )
    return row


def _sessions_for_task(tasks_json: str | None, task_id: str) -> list[dict]:
    import json

    raw = json.loads(tasks_json or "[]")
    if not isinstance(raw, list):
        return []
    return [
        e
        for e in raw
        if isinstance(e, dict) and str(e.get("task_id") or "") == task_id
    ]


def _own_active_session(sessions: list[dict], employee_id: int) -> dict | None:
    for entry in sessions:
        if not is_session_active(entry):
            continue
        try:
            owner = int(entry.get("employee_id") or 0)
        except (TypeError, ValueError):
            owner = 0
        # Legacy no-employee rows do not count as this helper's session.
        if owner == employee_id:
            return entry
    return None


async def start_helper_session(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
    employee_name: str | None = None,
) -> dict[str, Any]:
    """Start helper/assist session — requires membership; no claim/assign/complete."""
    _assert_phase2()
    if not isinstance(employee_id, int) or employee_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "employee_id_required"})

    order = (
        await db.execute(select(Orders).where(Orders.id == order_id))
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})
    if str(order.status or "").strip().lower() in _TERMINAL_ORDER_STATUSES:
        raise HTTPException(status_code=409, detail={"error": "order_not_active"})

    plan = await _load_latest_plan(db, order_id)
    _require_v2_materialized(plan)
    plan_task = _find_operational_task(plan, task_id)
    await _assert_eligible(db, employee_id=employee_id, plan_task=plan_task)
    await _require_active_membership(
        db, order_id=order_id, task_id=task_id, employee_id=employee_id
    )

    order_code = str(getattr(plan, "order_code", None) or f"ORD-{order_id}")

    reality = (
        await db.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one_or_none()
    sessions = _sessions_for_task(
        reality.tasks_json if reality else None, task_id
    )
    if _own_active_session(sessions, employee_id) is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "helper_session_already_active",
                "message": "Employee already has an active session on this task.",
            },
        )

    svc = ExecutionRealityService(db)
    now = datetime.now(timezone.utc).isoformat()
    try:
        row = await svc.start_task(
            order_id,
            order_code,
            task_id,
            now,
            initial_fields={
                "employee_id": employee_id,
                "employee_name": employee_name or "",
                "role": ROLE_HELPER,
                "session_type": SESSION_TYPE_ASSIST,
                "source": "helper_collaboration",
            },
        )
    except RealityInputError as exc:
        raise HTTPException(
            status_code=409,
            detail={"error": exc.code, "detail": exc.detail},
        ) from exc

    sessions = _sessions_for_task(row.tasks_json, task_id)
    mine = _own_active_session(sessions, employee_id)
    return {
        "status": "ok",
        "action": "helper_session_start",
        "order_id": order_id,
        "task_id": task_id,
        "employee_id": employee_id,
        "session": mine,
        "role": ROLE_HELPER,
        "session_type": SESSION_TYPE_ASSIST,
    }


async def stop_helper_session(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
) -> dict[str, Any]:
    """Stop only the actor's own session — no completed_by, no membership leave."""
    _assert_phase2()
    if not isinstance(employee_id, int) or employee_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "employee_id_required"})

    reality = (
        await db.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one_or_none()
    sessions = _sessions_for_task(
        reality.tasks_json if reality else None, task_id
    )
    if _own_active_session(sessions, employee_id) is None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "helper_session_not_active",
                "message": "No active helper session for this employee on the task.",
            },
        )

    svc = ExecutionRealityService(db)
    now = datetime.now(timezone.utc).isoformat()
    try:
        row = await svc.end_task(
            order_id,
            task_id,
            now,
            employee_id=employee_id,
            completion_fields=None,
        )
    except RealityInputError as exc:
        raise HTTPException(
            status_code=409,
            detail={"error": exc.code, "detail": exc.detail},
        ) from exc

    sessions = _sessions_for_task(row.tasks_json, task_id)
    return {
        "status": "ok",
        "action": "helper_session_stop",
        "order_id": order_id,
        "task_id": task_id,
        "employee_id": employee_id,
        "operation_completed": False,
        "membership_unchanged": True,
        "sessions_for_task": sessions,
    }
