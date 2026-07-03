"""Manager team read-only workspace — formal direct-report scope via manager_employee_id."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException, status
from models.employee_attendance_event import EmployeeAttendanceEvent
from models.employee_request import EmployeeRequest
from models.employees import Employees
from schemas.auth import UserResponse
from services.employee_attendance_service import validate_event_type
from services.employee_request_service import _serialize_for_review
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

MANAGER_TEAM_READER_ROLES = frozenset({"admin", "manager"})
ACTIVE_EMPLOYEE_STATUSES = frozenset({"active"})


@dataclass(frozen=True)
class ManagerTeamScope:
    """Resolved server-side team visibility — never from client employee_id alone."""

    role: str
    scope_mode: str  # all | direct_reports | empty
    manager_employee_id: Optional[int]
    team_employee_ids: frozenset[int]


def validate_manager_employee_id_assignment(
    employee_id: int,
    manager_employee_id: Optional[int],
) -> None:
    if manager_employee_id is not None and manager_employee_id == employee_id:
        raise ValueError("employee cannot be their own manager")


async def _active_linked_employee(
    db: AsyncSession,
    user_id: str,
) -> Optional[Employees]:
    if not (user_id or "").strip():
        return None
    result = await db.execute(
        select(Employees).where(
            Employees.user_id == user_id,
            Employees.status.in_(ACTIVE_EMPLOYEE_STATUSES),
        ).order_by(Employees.id.asc())
    )
    rows = list(result.scalars().all())
    if len(rows) != 1:
        return None
    return rows[0]


async def get_direct_report_employee_ids(
    db: AsyncSession,
    manager_employee_id: int,
) -> frozenset[int]:
    result = await db.execute(
        select(Employees.id).where(
            Employees.manager_employee_id == manager_employee_id,
            Employees.status.in_(ACTIVE_EMPLOYEE_STATUSES),
            Employees.id != manager_employee_id,
        )
    )
    return frozenset(int(row) for row in result.scalars().all())


async def resolve_manager_team_scope(
    db: AsyncSession,
    user: UserResponse,
    role: str,
) -> ManagerTeamScope:
    """
    Team scope source of truth:

    - admin → all active employees (optional filters validated separately)
    - manager → direct reports where manager_employee_id = manager's employee id
    """
    if role == "admin":
        return ManagerTeamScope(
            role=role,
            scope_mode="all",
            manager_employee_id=None,
            team_employee_ids=frozenset(),
        )

    manager_emp = await _active_linked_employee(db, user.id or "")
    if manager_emp is None:
        return ManagerTeamScope(
            role=role,
            scope_mode="empty",
            manager_employee_id=None,
            team_employee_ids=frozenset(),
        )

    team_ids = await get_direct_report_employee_ids(db, manager_emp.id)
    return ManagerTeamScope(
        role=role,
        scope_mode="direct_reports" if team_ids else "empty",
        manager_employee_id=manager_emp.id,
        team_employee_ids=team_ids,
    )


async def get_manager_team_employee_ids(
    db: AsyncSession,
    user: UserResponse,
    role: str,
) -> ManagerTeamScope:
    """Public helper — returns resolved scope for manager team endpoints."""
    return await resolve_manager_team_scope(db, user, role)


def assert_employee_id_in_team_scope(
    scope: ManagerTeamScope,
    employee_id: int,
) -> None:
    if scope.scope_mode == "all":
        return
    if employee_id not in scope.team_employee_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "team_scope_violation",
                "message": "employee_id is outside manager direct-report scope.",
            },
        )


def team_employee_ids_for_query(scope: ManagerTeamScope) -> Optional[Set[int]]:
    """None = no employee filter (admin all-scope); empty set = no rows."""
    if scope.scope_mode == "all":
        return None
    return set(scope.team_employee_ids)


async def list_team_attendance_events(
    db: AsyncSession,
    scope: ManagerTeamScope,
    start_date: date,
    end_date: date,
    *,
    employee_id: Optional[int] = None,
    event_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    if employee_id is not None:
        assert_employee_id_in_team_scope(scope, employee_id)

    team_ids = team_employee_ids_for_query(scope)
    if team_ids is not None and len(team_ids) == 0:
        return []
    if employee_id is not None:
        team_ids = {employee_id}

    normalized_type: Optional[str] = None
    if event_type is not None and event_type.strip():
        normalized_type = validate_event_type(event_type)

    stmt = (
        select(EmployeeAttendanceEvent, Employees.name)
        .join(Employees, Employees.id == EmployeeAttendanceEvent.employee_id)
        .where(
            EmployeeAttendanceEvent.start_date <= end_date,
            EmployeeAttendanceEvent.end_date >= start_date,
        )
        .order_by(EmployeeAttendanceEvent.start_date.asc(), EmployeeAttendanceEvent.id.asc())
    )
    if team_ids is not None:
        stmt = stmt.where(EmployeeAttendanceEvent.employee_id.in_(team_ids))

    result = await db.execute(stmt)
    rows: List[Dict[str, Any]] = []
    for event, name in result.all():
        if normalized_type is not None and event.event_type != normalized_type:
            continue
        rows.append(
            {
                "id": event.id,
                "employee_id": event.employee_id,
                "employee_name": name,
                "start_date": event.start_date.isoformat(),
                "end_date": event.end_date.isoformat(),
                "event_type": event.event_type,
                "event_status": event.event_status,
                "hours_override": float(event.hours_override)
                if event.hours_override is not None
                else None,
                "hours_delta": float(event.hours_delta) if event.hours_delta is not None else None,
                "notes": event.notes,
                "source": event.source,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "updated_at": event.updated_at.isoformat() if event.updated_at else None,
            }
        )
    return rows


async def list_team_requests_overview(
    db: AsyncSession,
    scope: ManagerTeamScope,
    *,
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    if employee_id is not None:
        assert_employee_id_in_team_scope(scope, employee_id)

    team_ids = team_employee_ids_for_query(scope)
    if team_ids is not None and len(team_ids) == 0:
        return []
    if employee_id is not None:
        team_ids = {employee_id}

    stmt = (
        select(EmployeeRequest, Employees)
        .join(Employees, Employees.id == EmployeeRequest.employee_id)
        .order_by(EmployeeRequest.submitted_at.desc(), EmployeeRequest.id.desc())
    )
    if team_ids is not None:
        stmt = stmt.where(EmployeeRequest.employee_id.in_(team_ids))
    if status is not None and status.strip():
        stmt = stmt.where(EmployeeRequest.status == status.strip().lower())
    if request_type is not None and request_type.strip():
        stmt = stmt.where(EmployeeRequest.request_type == request_type.strip().lower())
    if start_date is not None:
        stmt = stmt.where(EmployeeRequest.start_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(EmployeeRequest.start_date <= end_date)

    result = await db.execute(stmt)
    return [_serialize_for_review(req, emp) for req, emp in result.all()]
