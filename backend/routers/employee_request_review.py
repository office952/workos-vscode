"""Manager/admin employee request review — no attendance/payment side effects."""

from __future__ import annotations

from typing import List, Optional

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.employee_request_review import (
    EmployeeRequestReviewerContext,
    require_employee_request_reviewer,
)
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from services.employee_request_service import (
    approve_employee_request,
    get_employee_request_for_review,
    list_employee_requests_for_review,
    reject_employee_request,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/api/v1/employee-requests",
    tags=["employee-request-review"],
    dependencies=[Depends(get_current_user)],
)


class EmployeeRequestReviewAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_note: Optional[str] = None


class EmployeeRequestReviewResponse(BaseModel):
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


@router.get("/review", response_model=List[EmployeeRequestReviewResponse])
async def list_review_requests(
    ctx: EmployeeRequestReviewerContext = Depends(require_employee_request_reviewer),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_employee_requests_for_review(db, ctx.user, ctx.role)
    return [EmployeeRequestReviewResponse(**row) for row in rows]


@router.get("/review/{request_id}", response_model=EmployeeRequestReviewResponse)
async def get_review_request_detail(
    request_id: int,
    ctx: EmployeeRequestReviewerContext = Depends(require_employee_request_reviewer),
    db: AsyncSession = Depends(get_db),
):
    row = await get_employee_request_for_review(db, request_id, ctx.user, ctx.role)
    return EmployeeRequestReviewResponse(**row)


@router.patch("/review/{request_id}/approve", response_model=EmployeeRequestReviewResponse)
async def patch_approve_request(
    request_id: int,
    body: EmployeeRequestReviewAction,
    ctx: EmployeeRequestReviewerContext = Depends(require_employee_request_reviewer),
    db: AsyncSession = Depends(get_db),
):
    row = await approve_employee_request(
        db,
        request_id,
        ctx.user,
        ctx.role,
        review_note=body.review_note,
    )
    return EmployeeRequestReviewResponse(**row)


@router.patch("/review/{request_id}/reject", response_model=EmployeeRequestReviewResponse)
async def patch_reject_request(
    request_id: int,
    body: EmployeeRequestReviewAction,
    ctx: EmployeeRequestReviewerContext = Depends(require_employee_request_reviewer),
    db: AsyncSession = Depends(get_db),
):
    row = await reject_employee_request(
        db,
        request_id,
        ctx.user,
        ctx.role,
        review_note=body.review_note,
    )
    return EmployeeRequestReviewResponse(**row)
