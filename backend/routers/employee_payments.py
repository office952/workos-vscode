"""Employee internal payments API — situation read + payment recording (not fiscal payroll)."""

import logging
from datetime import date, datetime
from typing import List, Optional

from core.database import get_db
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from schemas.auth import UserResponse
from services.employee_payment_record_service import (
    cancel_employee_payment_record,
    create_employee_payment_record,
)
from services.employee_payment_situation_service import get_employee_payment_situation
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/employee-payments",
    tags=["employee-payments"],
    dependencies=[Depends(get_current_user)],
)


class PaymentBreakdown(BaseModel):
    base_amount: float
    attendance_adjustment: float
    overtime_amount: float
    advances_debts_deduction: float
    existing_payments: float
    suggested_deduction: float = 0.0


class PaymentHistoryItem(BaseModel):
    id: int
    amount_paid: float
    payment_date: str
    status: str
    notes: Optional[str] = None
    created_at: Optional[str] = None
    cancelled: bool = False


class PaymentSlotSituation(BaseModel):
    slot: str
    period_start: str
    period_end: str
    expected_amount: float
    paid_amount: float
    remaining_amount: float
    status: str
    breakdown: PaymentBreakdown
    warnings: List[str] = []
    history: List[PaymentHistoryItem] = []


class EmployeePaymentSlots(BaseModel):
    slot_15: PaymentSlotSituation = Field(alias="15")
    slot_30: PaymentSlotSituation = Field(alias="30")

    class Config:
        populate_by_name = True


class EmployeePaymentEmployee(BaseModel):
    employee_id: int
    employee_name: str
    salary_monthly: Optional[float] = None
    salary_amount: Optional[float] = None
    monthly_internal_pay_amount: Optional[float] = None
    currency: str
    base_source: str
    warnings: List[str] = []
    attendance_label: str
    advances_debts_label: str
    monthly_expected_amount: float
    monthly_paid_amount: float
    monthly_remaining_amount: float
    missing_pay_base: bool
    slots: dict


class PaymentSituationSummary(BaseModel):
    expected_total: float
    paid_total: float
    remaining_total: float
    unpaid_count: int
    partial_count: int
    paid_count: int


class PaymentSituationResponse(BaseModel):
    year: int
    month: int
    currency: str
    summary: PaymentSituationSummary
    employees: List[EmployeePaymentEmployee]


class PaymentRecordCreate(BaseModel):
    employee_id: int
    year: int
    month: int = Field(ge=1, le=12)
    slot: str
    amount_paid: float
    payment_date: date
    notes: Optional[str] = None


class PaymentRecordResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    year: int
    month: int
    slot: str
    amount_paid: float
    payment_date: date
    status: str
    notes: Optional[str] = None
    source: str
    cancelled_at: Optional[datetime] = None
    cancelled_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentCancelBody(BaseModel):
    reason: Optional[str] = None


def _http_error(exc: ValueError) -> HTTPException:
    detail = str(exc)
    if "not found" in detail:
        return HTTPException(status_code=404, detail=detail)
    return HTTPException(status_code=422, detail=detail)


@router.get("/situation", response_model=PaymentSituationResponse)
async def get_payment_situation(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(get_current_user),
):
    try:
        data = await get_employee_payment_situation(db, year, month)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PaymentSituationResponse(**data)


@router.post("", response_model=PaymentRecordResponse, status_code=201)
async def post_payment_record(
    body: PaymentRecordCreate,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(get_current_user),
):
    try:
        row = await create_employee_payment_record(db, body.model_dump())
    except ValueError as exc:
        raise _http_error(exc) from exc
    return PaymentRecordResponse(**row)


@router.post("/{record_id}/cancel", response_model=PaymentRecordResponse)
async def cancel_payment_record(
    record_id: int,
    body: PaymentCancelBody = PaymentCancelBody(),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(get_current_user),
):
    try:
        row = await cancel_employee_payment_record(db, record_id, body.reason)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return PaymentRecordResponse(**row)
