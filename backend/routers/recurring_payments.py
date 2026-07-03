"""Recurring payments router — CRUD for fixed monthly/annual payments."""
import json
import logging
from datetime import datetime
from typing import List, Optional

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from services.recurring_payments import RecurringPaymentsService, monthly_equivalent
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/recurring-payments",
    tags=["recurring-payments"],
    dependencies=[Depends(get_current_user)],
)


class PaymentData(BaseModel):
    name: str
    category: str = "alte_costuri"
    amount: Optional[float] = None
    currency: str = "RON"
    periodicity: str = "lunar"
    supplier: Optional[str] = None
    due_day: Optional[int] = None
    status: str = "active"
    include_in_overhead: bool = False
    include_in_machine_cost: bool = False
    linked_machine_id: Optional[str] = None
    observatii: Optional[str] = None


class PaymentUpdateData(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    periodicity: Optional[str] = None
    supplier: Optional[str] = None
    due_day: Optional[int] = None
    status: Optional[str] = None
    include_in_overhead: Optional[bool] = None
    include_in_machine_cost: Optional[bool] = None
    linked_machine_id: Optional[str] = None
    observatii: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    name: str
    category: str
    amount: Optional[float] = None
    currency: str
    periodicity: str
    supplier: Optional[str] = None
    due_day: Optional[int] = None
    status: str
    include_in_overhead: bool
    include_in_machine_cost: bool
    linked_machine_id: Optional[str] = None
    monthly_equivalent: float
    valid: bool
    observatii: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    items: List[PaymentResponse]
    total: int
    skip: int
    limit: int


def _serialize(row) -> PaymentResponse:
    amt = row.amount
    has_amount = amt is not None
    try:
        has_amount = has_amount and float(amt) > 0
    except (TypeError, ValueError):
        has_amount = False
    valid = has_amount and bool(row.category)
    return PaymentResponse(
        id=row.id,
        name=row.name,
        category=row.category,
        amount=row.amount,
        currency=row.currency,
        periodicity=row.periodicity,
        supplier=row.supplier,
        due_day=row.due_day,
        status=row.status,
        include_in_overhead=bool(row.include_in_overhead),
        include_in_machine_cost=bool(row.include_in_machine_cost),
        linked_machine_id=row.linked_machine_id,
        monthly_equivalent=round(monthly_equivalent(row), 2),
        valid=valid,
        observatii=row.observatii,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=PaymentListResponse)
async def list_payments(
    query: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
):
    svc = RecurringPaymentsService(db)
    query_dict = None
    if query:
        try:
            query_dict = json.loads(query)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid query JSON format")
    result = await svc.get_list(skip=skip, limit=limit, query_dict=query_dict, sort=sort)
    return PaymentListResponse(
        items=[_serialize(r) for r in result["items"]],
        total=result["total"],
        skip=result["skip"],
        limit=result["limit"],
    )


@router.get("/{id}", response_model=PaymentResponse)
async def get_payment(id: int, db: AsyncSession = Depends(get_db)):
    svc = RecurringPaymentsService(db)
    row = await svc.get_by_id(id)
    if not row:
        raise HTTPException(status_code=404, detail="Payment not found")
    return _serialize(row)


@router.post("", response_model=PaymentResponse, status_code=201)
async def create_payment(data: PaymentData, db: AsyncSession = Depends(get_db), _user: UserResponse = Depends(require_permission("recurring_payment.create"))):
    svc = RecurringPaymentsService(db)
    try:
        row = await svc.create(data.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _serialize(row)


@router.put("/{id}", response_model=PaymentResponse)
async def update_payment(id: int, data: PaymentUpdateData, db: AsyncSession = Depends(get_db), _user: UserResponse = Depends(require_permission("recurring_payment.update"))):
    svc = RecurringPaymentsService(db)
    try:
        row = await svc.update(id, data.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not row:
        raise HTTPException(status_code=404, detail="Payment not found")
    return _serialize(row)


@router.delete("/{id}")
async def delete_payment(id: int, db: AsyncSession = Depends(get_db), _user: UserResponse = Depends(require_permission("recurring_payment.delete"))):
    svc = RecurringPaymentsService(db)
    ok = await svc.delete(id)
    if not ok:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"message": "Payment deleted successfully", "id": id}