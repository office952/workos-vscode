"""Controlled Task Sessions V1 — assignment-gated start/end on ExecutionReality.

Canonical store: execution_reality.tasks_json (Owner Decision 07).
No commercial / inventory / HR-cost writes. No migration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from services.execution_plan_task_parser import (
    operational_tasks_only,
    parse_tasks_json_raw,
)
from services.execution_reality_service import ExecutionRealityService, RealityInputError
from services.task_work_session_service import (
    compute_duration_minutes,
    has_active_session_for_employee,
    is_session_active,
    sessions_for_task,
)

CONTROLLED_SESSION_SOURCE = "controlled_task_session_v1"
Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_employee_id(raw: Any) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _find_operational_task(plan: ExecutionPlan, task_id: str) -> dict[str, Any] | None:
    tid = (task_id or "").strip()
    if not tid:
        return None
    for entry in operational_tasks_only(plan.tasks_json):
        if isinstance(entry, dict) and str(entry.get("task_id") or "") == tid:
            return entry
    return None


async def _load_plan(db: AsyncSession, order_id: int) -> ExecutionPlan:
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "plan_not_found"})
    return plan


async def _load_order(db: AsyncSession, order_id: int) -> Orders:
    order = (
        await db.execute(select(Orders).where(Orders.id == order_id))
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})
    return order


async def _load_active_employee(db: AsyncSession, employee_id: int) -> Employees:
    emp = (
        await db.execute(select(Employees).where(Employees.id == employee_id))
    ).scalar_one_or_none()
    if emp is None:
        raise HTTPException(status_code=422, detail={"error": "inactive_employee"})
    if str(emp.status or "").lower() != "active":
        raise HTTPException(status_code=422, detail={"error": "inactive_employee"})
    return emp


def _assert_v2_materialized(plan: ExecutionPlan) -> None:
    parsed = parse_tasks_json_raw(plan.tasks_json)
    if parsed.format != "v2_envelope" or not parsed.operational_tasks:
        raise HTTPException(
            status_code=422,
            detail={"error": "v2_not_materialized"},
        )


def _employee_has_any_active_session(tasks: list[dict[str, Any]], employee_id: int) -> bool:
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        if not is_session_active(entry):
            continue
        if _normalize_employee_id(entry.get("employee_id")) == employee_id:
            return True
    return False


def _parse_reality_tasks(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    import json

    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


async def start_controlled_task_session(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
    actor_user_id: str | None = None,
    actor_mode: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Start one work session for the assigned employee on an operational task.

    actor_mode:
      - ``self``: employee_id must be the actor's linked employee (caller enforces)
      - ``supervisor``: actor has operator/execution start permission; employee must
        still equal assigned_employee_id (never arbitrary labor identity)
    """
    tid = (task_id or "").strip()
    if not tid:
        raise HTTPException(status_code=422, detail={"error": "invalid_task_identity"})

    plan = await _load_plan(db, order_id)
    _assert_v2_materialized(plan)
    order = await _load_order(db, order_id)
    task = _find_operational_task(plan, tid)
    if task is None:
        # Distinguish planned-only / missing
        parsed = parse_tasks_json_raw(plan.tasks_json)
        planned_ids = {
            str(t.get("task_id") or "")
            for t in (parsed.planned_tasks or [])
            if isinstance(t, dict)
        }
        if tid in planned_ids:
            raise HTTPException(
                status_code=422,
                detail={"error": "v2_not_materialized", "message": "Planned task is not operational."},
            )
        raise HTTPException(status_code=404, detail={"error": "operational_task_not_found"})

    assigned = _normalize_employee_id(task.get("assigned_employee_id"))
    if assigned is None:
        raise HTTPException(status_code=422, detail={"error": "task_unassigned"})
    if int(employee_id) != assigned:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "employee_not_assigned",
                "message": "Session employee must match current assigned_employee_id.",
                "assigned_employee_id": assigned,
            },
        )

    emp = await _load_active_employee(db, int(employee_id))

    reality = (
        await db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
    ).scalar_one_or_none()
    existing = _parse_reality_tasks(reality.tasks_json if reality else None)

    if has_active_session_for_employee(existing, task_id=tid, employee_id=int(employee_id)):
        active = next(
            (
                e
                for e in sessions_for_task(existing, tid)
                if is_session_active(e)
                and _normalize_employee_id(e.get("employee_id")) == int(employee_id)
            ),
            None,
        )
        return {
            "status": "ok",
            "already_active": True,
            "order_id": order_id,
            "execution_plan_id": plan.id,
            "task_id": tid,
            "employee_id": int(employee_id),
            "employee_name": emp.name,
            "session_id": (active or {}).get("session_id"),
            "started_at": (active or {}).get("started_at"),
            "controlled": True,
            "actor_mode": actor_mode,
            "actor_user_id": actor_user_id,
            "source": CONTROLLED_SESSION_SOURCE,
        }

    if _employee_has_any_active_session(existing, int(employee_id)):
        raise HTTPException(
            status_code=409,
            detail={"error": "employee_active_elsewhere"},
        )

    # Any other active primary session on this task blocks controlled start.
    for entry in sessions_for_task(existing, tid):
        if is_session_active(entry):
            raise HTTPException(
                status_code=409,
                detail={"error": "active_session_exists"},
            )

    now = (clock or _utc_now)()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    ts = now.isoformat()

    svc = ExecutionRealityService(db)
    try:
        row = await svc.start_task(
            order_id=order_id,
            order_code=str(order.code or f"ORD-{order_id}"),
            task_id=tid,
            timestamp=ts,
            initial_fields={
                "employee_id": int(employee_id),
                "employee_name": emp.name,
                "operator_name": emp.name,
                "source": CONTROLLED_SESSION_SOURCE,
                "controlled": True,
                "actor_mode": actor_mode,
                "actor_user_id": actor_user_id,
                "execution_plan_id": plan.id,
                # V1 policy eligibility is explicit. Historical sessions remain unvalued.
                "actual_cost_policy_runtime_v1": True,
            },
        )
    except RealityInputError as exc:
        if exc.code == "task_already_started":
            raise HTTPException(
                status_code=409,
                detail={"error": "active_session_exists"},
            ) from exc
        raise HTTPException(
            status_code=422,
            detail={"error": exc.code, "detail": exc.detail},
        ) from exc

    sessions = _parse_reality_tasks(row.tasks_json)
    active = next(
        (
            e
            for e in sessions_for_task(sessions, tid)
            if is_session_active(e)
            and _normalize_employee_id(e.get("employee_id")) == int(employee_id)
        ),
        None,
    )
    return {
        "status": "ok",
        "already_active": False,
        "order_id": order_id,
        "execution_plan_id": plan.id,
        "task_id": tid,
        "employee_id": int(employee_id),
        "employee_name": emp.name,
        "session_id": (active or {}).get("session_id"),
        "started_at": (active or {}).get("started_at") or ts,
        "controlled": True,
        "actor_mode": actor_mode,
        "actor_user_id": actor_user_id,
        "source": CONTROLLED_SESSION_SOURCE,
        "planned_minutes": task.get("estimated_time_minutes"),
        "sessions_created": 1,
        "commercial_mutated": False,
        "inventory_mutated": False,
        "hr_cost_calculated": False,
    }


async def end_controlled_task_session(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
    actor_user_id: str | None = None,
    actor_mode: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """End the active controlled session; duration is server-derived from timestamps."""
    tid = (task_id or "").strip()
    if not tid:
        raise HTTPException(status_code=422, detail={"error": "invalid_task_identity"})

    plan = await _load_plan(db, order_id)
    _assert_v2_materialized(plan)
    task = _find_operational_task(plan, tid)
    if task is None:
        raise HTTPException(status_code=404, detail={"error": "operational_task_not_found"})

    assigned = _normalize_employee_id(task.get("assigned_employee_id"))
    if assigned is None or int(employee_id) != assigned:
        raise HTTPException(status_code=422, detail={"error": "employee_not_assigned"})

    await _load_active_employee(db, int(employee_id))

    reality = (
        await db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
    ).scalar_one_or_none()
    if reality is None:
        raise HTTPException(
            status_code=422,
            detail={"error": "no_active_session", "message": "No reality row / no active session."},
        )

    sessions = _parse_reality_tasks(reality.tasks_json)
    active = next(
        (
            e
            for e in sessions_for_task(sessions, tid)
            if is_session_active(e)
            and _normalize_employee_id(e.get("employee_id")) == int(employee_id)
        ),
        None,
    )
    if active is None:
        # Idempotent end: already closed for this employee+task
        closed = next(
            (
                e
                for e in sessions_for_task(sessions, tid)
                if e.get("ended_at")
                and _normalize_employee_id(e.get("employee_id")) == int(employee_id)
            ),
            None,
        )
        if closed is not None:
            started = str(closed.get("started_at") or "")
            ended = str(closed.get("ended_at") or "")
            return {
                "status": "ok",
                "already_ended": True,
                "order_id": order_id,
                "execution_plan_id": plan.id,
                "task_id": tid,
                "employee_id": int(employee_id),
                "session_id": closed.get("session_id"),
                "started_at": started,
                "ended_at": ended,
                "duration_minutes": closed.get("duration_minutes")
                or compute_duration_minutes(started, ended),
                "controlled": True,
                "actor_mode": actor_mode,
                "task_auto_completed": False,
                "planned_minutes": task.get("estimated_time_minutes"),
            }
        raise HTTPException(
            status_code=422,
            detail={"error": "no_active_session", "message": "No active session to end."},
        )

    now = (clock or _utc_now)()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    ts = now.isoformat()

    svc = ExecutionRealityService(db)
    try:
        row = await svc.end_task(
            order_id=order_id,
            task_id=tid,
            timestamp=ts,
            employee_id=int(employee_id),
            completion_fields=None,  # V1: end session ≠ task completion decision
        )
    except RealityInputError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": exc.code, "detail": exc.detail},
        ) from exc

    sessions = _parse_reality_tasks(row.tasks_json)
    closed = next(
        (
            e
            for e in sessions_for_task(sessions, tid)
            if e.get("ended_at")
            and _normalize_employee_id(e.get("employee_id")) == int(employee_id)
            and str(e.get("session_id") or "") == str(active.get("session_id") or "")
        ),
        None,
    ) or next(
        (
            e
            for e in sessions_for_task(sessions, tid)
            if e.get("ended_at")
            and _normalize_employee_id(e.get("employee_id")) == int(employee_id)
        ),
        None,
    )
    started = str((closed or active).get("started_at") or "")
    ended = str((closed or {}).get("ended_at") or ts)
    duration = (closed or {}).get("duration_minutes")
    if duration is None:
        duration = compute_duration_minutes(started, ended)

    return {
        "status": "ok",
        "already_ended": False,
        "order_id": order_id,
        "execution_plan_id": plan.id,
        "task_id": tid,
        "employee_id": int(employee_id),
        "session_id": (closed or active).get("session_id"),
        "started_at": started,
        "ended_at": ended,
        "duration_minutes": duration,
        "duration_seconds": int(round(float(duration) * 60)) if duration is not None else None,
        "controlled": True,
        "actor_mode": actor_mode,
        "actor_user_id": actor_user_id,
        "source": CONTROLLED_SESSION_SOURCE,
        "task_auto_completed": False,
        "planned_minutes": task.get("estimated_time_minutes"),
        "variance_available": task.get("estimated_time_minutes") is not None,
        "variance_reason": None
        if task.get("estimated_time_minutes") is not None
        else "planning_minutes_source_missing",
        "commercial_mutated": False,
        "inventory_mutated": False,
        "hr_cost_calculated": False,
    }


async def build_execution_actuals_read_model(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str | None = None,
) -> dict[str, Any]:
    """Read-only ExecutionActuals projection from plan + reality sessions."""
    plan = await _load_plan(db, order_id)
    _assert_v2_materialized(plan)
    reality = (
        await db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
    ).scalar_one_or_none()
    sessions_all = _parse_reality_tasks(reality.tasks_json if reality else None)

    rows: list[dict[str, Any]] = []
    for task in operational_tasks_only(plan.tasks_json):
        if not isinstance(task, dict):
            continue
        tid = str(task.get("task_id") or "")
        if task_id and tid != task_id:
            continue
        task_sessions = sessions_for_task(sessions_all, tid)
        active = [s for s in task_sessions if is_session_active(s)]
        closed = [s for s in task_sessions if s.get("ended_at")]
        total = 0
        first_start = None
        last_end = None
        for s in closed:
            started = str(s.get("started_at") or "")
            ended = str(s.get("ended_at") or "")
            dur = s.get("duration_minutes")
            if dur is None:
                dur = compute_duration_minutes(started, ended)
            total += int(dur or 0)
            if started and (first_start is None or started < first_start):
                first_start = started
            if ended and (last_end is None or ended > last_end):
                last_end = ended
        planned = task.get("estimated_time_minutes")
        variance = None
        variance_reason = None
        if planned is None:
            variance_reason = "planning_minutes_source_missing"
        else:
            try:
                variance = float(total) - float(planned)
            except (TypeError, ValueError):
                variance_reason = "planning_minutes_source_missing"
        rows.append(
            {
                "task_id": tid,
                "assigned_employee_id": _normalize_employee_id(task.get("assigned_employee_id")),
                "session_count": len(task_sessions),
                "active_session": bool(active),
                "total_actual_duration_minutes": total,
                "first_started_at": first_start,
                "last_ended_at": last_end,
                "planned_minutes": planned,
                "variance_minutes": variance,
                "variance_reason": variance_reason,
                "provenance": CONTROLLED_SESSION_SOURCE,
            }
        )

    return {
        "status": "ok",
        "order_id": order_id,
        "execution_plan_id": plan.id,
        "tasks": rows,
        "reality_total_actual_time_minutes": (
            float(reality.total_actual_time_minutes)
            if reality and reality.total_actual_time_minutes is not None
            else 0.0
        ),
    }
