"""Employee attendance API — default present + exception events (not fiscal payroll)."""

import logging
from datetime import date, datetime
from typing import List, Optional

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import resolve_effective_role
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from models.employee_request import EmployeeRequest
from schemas.auth import UserResponse
from services.attendance_request_effect_service import (
    apply_attendance_request_effect,
    generate_attendance_effect_for_request,
    get_attendance_effect_for_request,
    get_attendance_request_effect_detail,
    list_attendance_effect_generation_candidates,
    list_attendance_request_effects,
)
from services.employee_attendance_service import (
    create_attendance_event,
    delete_attendance_event,
    get_attendance_month_summary,
    list_attendance_events,
    update_attendance_event,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/employee-attendance",
    tags=["employee-attendance"],
    dependencies=[Depends(get_current_user)],
)

ATTENDANCE_OPERATOR_ROLES = frozenset({"admin", "operator"})


async def require_attendance_operator(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Restrict attendance CRUD/summary/apply to admin or operator."""
    effective_role = resolve_effective_role(current_user.role)
    if effective_role not in ATTENDANCE_OPERATOR_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "attendance_operator_required",
                "role": effective_role,
                "message": "Employee attendance access requires role 'admin' or 'operator'.",
            },
        )
    return current_user


require_attendance_effect_applier = require_attendance_operator


class AttendanceEventCreate(BaseModel):
    employee_id: int
    start_date: date
    end_date: Optional[date] = None
    event_type: str
    event_status: str = Field(default="confirmed")
    hours_override: Optional[float] = None
    hours_delta: Optional[float] = None
    notes: Optional[str] = None
    source: Optional[str] = "manual"


class AttendanceEventUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    event_type: Optional[str] = None
    event_status: Optional[str] = None
    hours_override: Optional[float] = None
    hours_delta: Optional[float] = None
    notes: Optional[str] = None


class AttendanceEventResponse(BaseModel):
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


class AttendanceEmployeeSummary(BaseModel):
    employee_id: int
    employee_name: str
    standard_work_days: int
    standard_hours: float
    present_days: int
    absent_days: int
    leave_days: int
    sick_days: int
    partial_days: int
    overtime_hours: float
    total_hours: float
    event_count: int
    planned_event_count: int = 0
    approved_event_count: int = 0
    confirmed_event_count: int = 0
    cancelled_event_count: int = 0


class AttendanceMonthSummaryResponse(BaseModel):
    year: int
    month: int
    standard_work_hours_per_day: float
    employees: List[AttendanceEmployeeSummary]


class AttendanceEffectApplyResponse(BaseModel):
    effect_id: int
    employee_request_id: int
    employee_id: int
    effect_status: str
    attendance_event_id: int
    already_applied: bool = False


class AttendanceEffectResponse(BaseModel):
    id: int
    employee_request_id: int
    employee_id: int
    request_type: str
    effect_type: str
    status: str
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    hours: Optional[float] = None
    generated_by_user_id: str
    generated_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    applied_by_user_id: Optional[str] = None
    source: str
    notes: Optional[str] = None
    conflict_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AttendanceEffectGenerateRequest(BaseModel):
    employee_request_id: int


class AttendanceEffectGenerateResponse(AttendanceEffectResponse):
    already_exists: bool = False


class AttendanceEffectGenerationCandidate(BaseModel):
    employee_request_id: int
    employee_id: int
    employee_name: str
    request_type: str
    status: str
    title: Optional[str] = None
    reason: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    has_effect: bool
    effect_id: Optional[int] = None
    effect_status: Optional[str] = None


def _http_error(exc: ValueError) -> HTTPException:
    detail = str(exc)
    if "not found" in detail:
        return HTTPException(status_code=404, detail=detail)
    if "conflict" in detail or "cannot add" in detail or "already exists" in detail:
        return HTTPException(status_code=409, detail=detail)
    return HTTPException(status_code=422, detail=detail)


def _apply_effect_http_error(exc: ValueError) -> HTTPException:
    detail = str(exc)
    if "not found" in detail:
        return HTTPException(status_code=404, detail=detail)
    if detail.startswith("apply_unsupported:"):
        return HTTPException(status_code=422, detail=detail)
    if detail.startswith("apply_conflict:") or "conflict" in detail:
        return HTTPException(status_code=409, detail=detail)
    return HTTPException(status_code=422, detail=detail)


@router.get("/summary", response_model=AttendanceMonthSummaryResponse)
async def get_attendance_summary(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_attendance_operator),
):
    try:
        data = await get_attendance_month_summary(db, year, month)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AttendanceMonthSummaryResponse(**data)


@router.get("/events", response_model=List[AttendanceEventResponse])
async def get_attendance_events(
    start_date: date = Query(...),
    end_date: date = Query(...),
    employee_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_attendance_operator),
):
    try:
        rows = await list_attendance_events(db, start_date, end_date, employee_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return [AttendanceEventResponse(**row) for row in rows]


@router.post("/events", response_model=AttendanceEventResponse)
async def post_attendance_event(
    body: AttendanceEventCreate,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_attendance_operator),
):
    try:
        row = await create_attendance_event(db, body.model_dump())
    except ValueError as exc:
        raise _http_error(exc) from exc
    return AttendanceEventResponse(**row)


@router.put("/events/{event_id}", response_model=AttendanceEventResponse)
async def put_attendance_event(
    event_id: int,
    body: AttendanceEventUpdate,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_attendance_operator),
):
    try:
        row = await update_attendance_event(db, event_id, body.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise _http_error(exc) from exc
    return AttendanceEventResponse(**row)


@router.delete("/events/{event_id}", status_code=204)
async def remove_attendance_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_attendance_operator),
):
    try:
        await delete_attendance_event(db, event_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/effects", response_model=List[AttendanceEffectResponse])
async def get_attendance_effects(
    status: Optional[str] = Query(None),
    employee_id: Optional[int] = Query(None),
    request_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_attendance_operator),
):
    try:
        rows = await list_attendance_request_effects(
            db,
            status=status,
            employee_id=employee_id,
            employee_request_id=request_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return [AttendanceEffectResponse(**row) for row in rows]


@router.get(
    "/effects/generation-candidates",
    response_model=List[AttendanceEffectGenerationCandidate],
)
async def get_attendance_effect_generation_candidates(
    employee_id: Optional[int] = Query(None),
    request_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    include_existing: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_attendance_operator),
):
    try:
        rows = await list_attendance_effect_generation_candidates(
            db,
            employee_id=employee_id,
            request_type=request_type,
            start_date=start_date,
            end_date=end_date,
            include_existing=include_existing,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return [AttendanceEffectGenerationCandidate(**row) for row in rows]


@router.post("/effects/generate", response_model=AttendanceEffectGenerateResponse)
async def post_generate_attendance_effect(
    body: AttendanceEffectGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(require_attendance_operator),
):
    req = await db.get(EmployeeRequest, body.employee_request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Employee request not found")

    existing_before = await get_attendance_effect_for_request(db, body.employee_request_id)
    request_status_before = req.status

    try:
        effect = await generate_attendance_effect_for_request(db, req, user.id or "")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if effect is None:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "request_type_skipped",
                "message": "This request type does not generate attendance effects.",
            },
        )

    await db.refresh(req)
    if req.status != request_status_before:
        raise HTTPException(
            status_code=500,
            detail="Request status must not change during effect generation.",
        )

    already_exists = existing_before is not None
    row = await get_attendance_request_effect_detail(db, effect.id)
    payload = AttendanceEffectGenerateResponse(**row, already_exists=already_exists)

    logger.info(
        "attendance_effect_generate request_id=%s effect_id=%s actor=%s already_exists=%s status=%s",
        body.employee_request_id,
        effect.id,
        user.id,
        already_exists,
        effect.status,
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK if already_exists else status.HTTP_201_CREATED,
        content=payload.model_dump(mode="json"),
    )


@router.get("/effects/{effect_id}", response_model=AttendanceEffectResponse)
async def get_attendance_effect(
    effect_id: int,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_attendance_operator),
):
    try:
        row = await get_attendance_request_effect_detail(db, effect_id)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return AttendanceEffectResponse(**row)


@router.post("/effects/{effect_id}/apply", response_model=AttendanceEffectApplyResponse)
async def post_apply_attendance_effect(
    effect_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(require_attendance_effect_applier),
):
    try:
        result = await apply_attendance_request_effect(db, effect_id, user.id)
    except ValueError as exc:
        raise _apply_effect_http_error(exc) from exc

    effect = result["effect"]
    logger.info(
        "attendance_effect_apply effect_id=%s request_id=%s employee_id=%s event_id=%s actor=%s already_applied=%s",
        effect["id"],
        effect["employee_request_id"],
        effect["employee_id"],
        result["attendance_event_id"],
        user.id,
        result.get("already_applied", False),
    )
    return AttendanceEffectApplyResponse(
        effect_id=effect["id"],
        employee_request_id=effect["employee_request_id"],
        employee_id=effect["employee_id"],
        effect_status=effect["status"],
        attendance_event_id=result["attendance_event_id"],
        already_applied=bool(result.get("already_applied")),
    )
