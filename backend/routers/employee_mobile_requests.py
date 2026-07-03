"""Employee-mobile self-only request endpoints."""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import List, Optional

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.employee_mobile import EmployeeMobileContext, require_employee_self_user
from dependencies.employee_manager_team import ManagerTeamReaderContext, require_manager_team_reader
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from schemas.auth import UserResponse
from services.employee_attendance_service import list_attendance_events, validate_event_type
from services.employee_manager_team_service import (
    list_team_attendance_events,
    list_team_requests_overview,
)
from services.employee_request_service import (
    cancel_employee_request,
    create_employee_request,
    get_employee_request,
    list_employee_requests,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/api/v1/employee-mobile",
    tags=["employee-mobile"],
    dependencies=[Depends(get_current_user)],
)


class EmployeeRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    reason: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = Field(default="RON")


class EmployeeRequestResponse(BaseModel):
    id: int
    employee_id: int
    request_type: str
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    reason: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewed_by_user_id: Optional[str] = None
    review_note: Optional[str] = None


class SelfAttendanceEventResponse(BaseModel):
    id: int
    employee_id: int
    start_date: date
    end_date: date
    event_type: str
    event_status: str
    hours_override: Optional[float] = None
    hours_delta: Optional[float] = None
    notes: Optional[str] = None
    source: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    employee_name: Optional[str] = None


class ManagerTeamAttendanceEventResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    start_date: str
    end_date: str
    event_type: str
    event_status: str
    hours_override: Optional[float] = None
    hours_delta: Optional[float] = None
    notes: Optional[str] = None
    source: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ManagerTeamRequestResponse(BaseModel):
    id: int
    employee_id: int
    request_type: str
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    reason: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewed_by_user_id: Optional[str] = None
    review_note: Optional[str] = None
    employee_name: str
    employee_department: Optional[str] = None
    employee_operational_role: Optional[str] = None
    employee_status: str


def _default_month_bounds(today: date | None = None) -> tuple[date, date]:
    ref = today or date.today()
    last_day = calendar.monthrange(ref.year, ref.month)[1]
    return date(ref.year, ref.month, 1), date(ref.year, ref.month, last_day)


def _http_validation_error(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/requests", response_model=List[EmployeeRequestResponse])
async def list_requests(
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_employee_requests(db, ctx.employee.id)
    return [EmployeeRequestResponse(**row) for row in rows]


@router.post("/requests", response_model=EmployeeRequestResponse, status_code=201)
async def post_request(
    body: EmployeeRequestCreate,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        row = await create_employee_request(db, ctx.employee.id, body.model_dump())
    except ValueError as exc:
        raise _http_validation_error(exc) from exc
    return EmployeeRequestResponse(**row)


@router.get("/requests/{request_id}", response_model=EmployeeRequestResponse)
async def get_request_detail(
    request_id: int,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    row = await get_employee_request(db, ctx.employee.id, request_id)
    return EmployeeRequestResponse(**row)


@router.patch("/requests/{request_id}/cancel", response_model=EmployeeRequestResponse)
async def patch_cancel_request(
    request_id: int,
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    row = await cancel_employee_request(db, ctx.employee.id, request_id)
    return EmployeeRequestResponse(**row)


@router.get("/attendance", response_model=List[SelfAttendanceEventResponse])
async def list_self_attendance(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    event_type: Optional[str] = Query(None),
    employee_id: Optional[int] = Query(None),
    ctx: EmployeeMobileContext = Depends(require_employee_self_user),
    db: AsyncSession = Depends(get_db),
):
    if employee_id is not None:
        raise HTTPException(
            status_code=422,
            detail="employee_id is not accepted on self attendance endpoint",
        )

    range_start, range_end = _default_month_bounds()
    if start_date is not None:
        range_start = start_date
    if end_date is not None:
        range_end = end_date

    normalized_type: Optional[str] = None
    if event_type is not None and event_type.strip():
        try:
            normalized_type = validate_event_type(event_type)
        except ValueError as exc:
            raise _http_validation_error(exc) from exc

    rows = await list_attendance_events(db, range_start, range_end, ctx.employee.id)
    if normalized_type is not None:
        rows = [row for row in rows if row["event_type"] == normalized_type]

    return [SelfAttendanceEventResponse(**row) for row in rows]


@router.get("/manager/team-attendance", response_model=List[ManagerTeamAttendanceEventResponse])
async def list_manager_team_attendance(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee_id: Optional[int] = Query(None),
    event_type: Optional[str] = Query(None),
    ctx: ManagerTeamReaderContext = Depends(require_manager_team_reader),
    db: AsyncSession = Depends(get_db),
):
    range_start, range_end = _default_month_bounds()
    if start_date is not None:
        range_start = start_date
    if end_date is not None:
        range_end = end_date

    try:
        rows = await list_team_attendance_events(
            db,
            ctx.scope,
            range_start,
            range_end,
            employee_id=employee_id,
            event_type=event_type,
        )
    except ValueError as exc:
        raise _http_validation_error(exc) from exc

    return [ManagerTeamAttendanceEventResponse(**row) for row in rows]


@router.get("/manager/team-requests", response_model=List[ManagerTeamRequestResponse])
async def list_manager_team_requests(
    status: Optional[str] = Query(None),
    request_type: Optional[str] = Query(None),
    employee_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    ctx: ManagerTeamReaderContext = Depends(require_manager_team_reader),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_team_requests_overview(
        db,
        ctx.scope,
        status=status,
        request_type=request_type,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
    )
    return [ManagerTeamRequestResponse(**row) for row in rows]
