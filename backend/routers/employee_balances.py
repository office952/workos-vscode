"""Employee internal balance ledger API — not fiscal payroll."""

import logging
from datetime import date, datetime
from typing import List, Optional

from core.database import get_db
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from schemas.auth import UserResponse
from services.employee_balance_service import (
    cancel_employee_balance_transaction,
    create_employee_balance_transaction,
    get_employee_balance_summary,
    list_employee_balance_transactions,
    update_employee_balance_transaction,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/employee-balances",
    tags=["employee-balances"],
    dependencies=[Depends(get_current_user)],
)


class BalanceTransactionCreate(BaseModel):
    employee_id: int
    transaction_date: date
    transaction_type: str
    amount: float
    currency: str = Field(default="RON")
    status: str = Field(default="active")
    notes: Optional[str] = None
    source: Optional[str] = "manual"


class BalanceTransactionUpdate(BaseModel):
    transaction_date: Optional[date] = None
    transaction_type: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class BalanceTransactionResponse(BaseModel):
    id: int
    employee_id: int
    transaction_date: date
    transaction_type: str
    amount: float
    currency: str
    status: str
    notes: Optional[str] = None
    source: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    employee_name: Optional[str] = None
    signed_amount: float


class BalanceEmployeeSummary(BaseModel):
    employee_id: int
    employee_name: str
    active_balance: float
    advance_total: float
    loan_total: float
    retention_total: float
    repayment_total: float
    compensation_total: float
    transaction_count: int


class BalanceTotals(BaseModel):
    active_balance: float
    advance_total: float
    loan_total: float
    retention_total: float
    repayment_total: float
    compensation_total: float
    transaction_count: int


class BalanceSummaryResponse(BaseModel):
    currency: str
    totals: BalanceTotals
    employees: List[BalanceEmployeeSummary]


def _http_error(exc: ValueError) -> HTTPException:
    detail = str(exc)
    if "not found" in detail:
        return HTTPException(status_code=404, detail=detail)
    return HTTPException(status_code=422, detail=detail)


@router.get("/summary", response_model=BalanceSummaryResponse)
async def get_balance_summary(
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(get_current_user),
):
    data = await get_employee_balance_summary(db)
    return BalanceSummaryResponse(**data)


@router.get("/transactions", response_model=List[BalanceTransactionResponse])
async def get_balance_transactions(
    employee_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(get_current_user),
):
    try:
        rows = await list_employee_balance_transactions(
            db,
            employee_id=employee_id,
            status=status,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return [BalanceTransactionResponse(**row) for row in rows]


@router.post("/transactions", response_model=BalanceTransactionResponse)
async def post_balance_transaction(
    body: BalanceTransactionCreate,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(get_current_user),
):
    try:
        row = await create_employee_balance_transaction(db, body.model_dump())
    except ValueError as exc:
        raise _http_error(exc) from exc
    return BalanceTransactionResponse(**row)


@router.put("/transactions/{transaction_id}", response_model=BalanceTransactionResponse)
async def put_balance_transaction(
    transaction_id: int,
    body: BalanceTransactionUpdate,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(get_current_user),
):
    try:
        row = await update_employee_balance_transaction(
            db, transaction_id, body.model_dump(exclude_unset=True)
        )
    except ValueError as exc:
        raise _http_error(exc) from exc
    return BalanceTransactionResponse(**row)


@router.post("/transactions/{transaction_id}/cancel", response_model=BalanceTransactionResponse)
async def cancel_balance_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(get_current_user),
):
    try:
        row = await cancel_employee_balance_transaction(db, transaction_id)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return BalanceTransactionResponse(**row)
