"""Task clarification requests — employee asks for production details without blocking."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import HTTPException
from models.auth import User
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.task_clarification_request import TaskClarificationRequest
from services.employee_mobile_tasks_service import task_belongs_to_employee
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

OPEN_STATUS = "open"
RESOLVED_STATUS = "resolved"
CANCELLED_STATUS = "cancelled"
VALID_STATUSES = frozenset({OPEN_STATUS, RESOLVED_STATUS, CANCELLED_STATUS})


def _iso(dt: datetime | None) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


async def _resolve_target_user_name(db: AsyncSession, user_id: Optional[str]) -> str:
    uid = (user_id or "").strip()
    if not uid:
        return ""
    user = await db.get(User, uid)
    return str(user.name).strip() if user and user.name else ""


async def resolve_plan_prepared_by_user_id(db: AsyncSession, order_id: int) -> Optional[str]:
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        return None
    prepared = getattr(plan, "prepared_by_user_id", None)
    uid = str(prepared or "").strip()
    return uid or None


def _serialize_row(
    row: TaskClarificationRequest,
    *,
    employee_name: str = "",
    target_user_name: str = "",
) -> dict[str, Any]:
    target_user_id = str(getattr(row, "target_user_id", None) or "").strip() or None
    return {
        "id": row.id,
        "order_id": row.order_id,
        "task_id": row.task_id,
        "employee_id": row.employee_id,
        "employee_name": employee_name,
        "message": row.message or "",
        "status": row.status,
        "created_at": _iso(row.created_at),
        "resolved_at": _iso(row.resolved_at),
        "resolved_by_user_id": row.resolved_by_user_id,
        "target_user_id": target_user_id,
        "target_user_name": target_user_name,
        "routed_to_responsible": bool(target_user_id),
    }


async def _assert_task_owned_by_employee(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
) -> None:
    from services.employee_mobile_tasks_service import _load_enriched_tasks

    enriched, _ = await _load_enriched_tasks(db)
    match = next(
        (t for t in enriched if t["order_id"] == order_id and t["task_id"] == task_id),
        None,
    )
    if match is None:
        raise HTTPException(status_code=404, detail={"error": "task_not_found"})

    plan_task = {"assigned_employee_id": match.get("assigned_employee_id")}
    reality_task = {
        "employee_id": match.get("employee_id"),
        "completed_by_employee_id": match.get("completed_by_employee_id"),
    }
    if not task_belongs_to_employee(plan_task, reality_task, employee_id):
        raise HTTPException(status_code=403, detail={"error": "task_not_assigned_to_employee"})


async def get_open_clarification_map(
    db: AsyncSession,
    *,
    employee_id: int,
    task_keys: Sequence[Tuple[int, str]],
) -> Dict[Tuple[int, str], dict]:
    if not task_keys:
        return {}

    rows = (
        await db.execute(
            select(TaskClarificationRequest).where(
                TaskClarificationRequest.employee_id == employee_id,
                TaskClarificationRequest.status == OPEN_STATUS,
            )
        )
    ).scalars().all()

    wanted = set(task_keys)
    result: Dict[Tuple[int, str], dict] = {}
    for row in rows:
        key = (row.order_id, row.task_id)
        if key in wanted:
            target_name = await _resolve_target_user_name(db, row.target_user_id)
            result[key] = _serialize_row(row, target_user_name=target_name)
    return result


async def create_clarification_request(
    db: AsyncSession,
    *,
    employee_id: int,
    order_id: int,
    task_id: str,
    message: Optional[str],
) -> dict[str, Any]:
    tid = (task_id or "").strip()
    if not tid:
        raise HTTPException(status_code=422, detail={"error": "task_id_required"})

    cleaned = (message or "").strip()
    if not cleaned:
        raise HTTPException(
            status_code=422,
            detail={"error": "message_required", "message": "Scrie pe scurt ce informații ai nevoie."},
        )

    await _assert_task_owned_by_employee(
        db, order_id=order_id, task_id=tid, employee_id=employee_id
    )

    existing = (
        await db.execute(
            select(TaskClarificationRequest).where(
                TaskClarificationRequest.order_id == order_id,
                TaskClarificationRequest.task_id == tid,
                TaskClarificationRequest.employee_id == employee_id,
                TaskClarificationRequest.status == OPEN_STATUS,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        target_name = await _resolve_target_user_name(db, existing.target_user_id)
        raise HTTPException(
            status_code=409,
            detail={
                "error": "open_clarification_exists",
                "clarification_request": _serialize_row(existing, target_user_name=target_name),
            },
        )

    target_user_id = await resolve_plan_prepared_by_user_id(db, order_id)

    row = TaskClarificationRequest(
        order_id=order_id,
        task_id=tid,
        employee_id=employee_id,
        message=cleaned,
        status=OPEN_STATUS,
        target_user_id=target_user_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    target_name = await _resolve_target_user_name(db, row.target_user_id)
    return _serialize_row(row, target_user_name=target_name)


async def list_clarification_requests(
    db: AsyncSession,
    *,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[dict[str, Any]]:
    query = select(TaskClarificationRequest).order_by(TaskClarificationRequest.created_at.desc())
    if status:
        normalized = status.strip().lower()
        if normalized not in VALID_STATUSES:
            raise HTTPException(status_code=422, detail={"error": "invalid_status"})
        query = query.where(TaskClarificationRequest.status == normalized)
    query = query.limit(max(1, min(limit, 500)))

    rows = (await db.execute(query)).scalars().all()
    if not rows:
        return []

    employee_ids = {row.employee_id for row in rows}
    employees = (
        await db.execute(select(Employees).where(Employees.id.in_(employee_ids)))
    ).scalars().all()
    names = {emp.id: emp.name for emp in employees}

    target_ids = {
        str(row.target_user_id).strip()
        for row in rows
        if getattr(row, "target_user_id", None)
    }
    target_names: Dict[str, str] = {}
    if target_ids:
        users = (
            await db.execute(select(User).where(User.id.in_(target_ids)))
        ).scalars().all()
        target_names = {user.id: user.name for user in users}

    return [
        _serialize_row(
            row,
            employee_name=names.get(row.employee_id, ""),
            target_user_name=target_names.get(str(row.target_user_id or "").strip(), ""),
        )
        for row in rows
    ]


async def resolve_clarification_request(
    db: AsyncSession,
    *,
    request_id: int,
    resolved_by_user_id: str,
) -> dict[str, Any]:
    row = await db.get(TaskClarificationRequest, request_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "clarification_not_found"})
    if row.status != OPEN_STATUS:
        raise HTTPException(status_code=409, detail={"error": "clarification_not_open"})

    row.status = RESOLVED_STATUS
    row.resolved_at = datetime.now(timezone.utc)
    row.resolved_by_user_id = resolved_by_user_id
    await db.commit()
    await db.refresh(row)

    emp = await db.get(Employees, row.employee_id)
    target_name = await _resolve_target_user_name(db, row.target_user_id)
    return _serialize_row(row, employee_name=emp.name if emp else "", target_user_name=target_name)
