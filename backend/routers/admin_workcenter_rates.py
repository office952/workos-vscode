"""Admin router for the Workcenter Rates registry (Sprint #20).

Exposes CRUD-lite endpoints for the canonical per-workcenter hourly rate
table introduced by Sprint #20.

Endpoints (prefix `/api/admin/workcenter-rates`):
  - GET    /                 -> list all rows (ordered by `code`).
  - GET    /{code}            -> fetch one row by canonical code.
  - POST   /                 -> create a new row; enforces invariants.
  - PATCH  /{code}            -> update rate / status / label / notes.

All endpoints validate the canonical status invariant:
`status="active"` requires `rate_per_hour` to be a positive number.
Violations return HTTP 400.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from services.workcenter_rates_service import (
    WorkcenterRateValidationError,
    create_workcenter_rate,
    get_workcenter_rate_by_code,
    list_workcenter_rates,
    update_workcenter_rate,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/workcenter-rates",
    tags=["admin_workcenter_rates"],
    dependencies=[Depends(get_current_user)],
)


class WorkcenterRateCreateBody(BaseModel):
    code: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    rate_per_hour: Optional[float] = None
    rate_per_linear_meter: Optional[float] = None
    rate_basis: str = "per_hour"
    status: str = "missing_price"
    is_active: Optional[bool] = None
    approval_reference: Optional[str] = None
    notes: Optional[str] = None
    currency: str = "RON"


class WorkcenterRatePatchBody(BaseModel):
    rate_per_hour: Optional[float] = None
    rate_per_linear_meter: Optional[float] = None
    rate_basis: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    approval_reference: Optional[str] = None
    label: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
async def list_rates(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """Return every workcenter rate row (including archived) sorted by code."""
    return await list_workcenter_rates(db)


@router.get("/{code}")
async def get_rate(code: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    row = await get_workcenter_rate_by_code(db, code)
    if row is None:
        raise HTTPException(status_code=404, detail=f"workcenter_rate '{code}' not found")
    return row


@router.post("", status_code=201)
async def create_rate(
    body: WorkcenterRateCreateBody,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_permission("workcenter_rates.manage")),
) -> Dict[str, Any]:
    try:
        return await create_workcenter_rate(
            db,
            code=body.code,
            label=body.label,
            rate_per_hour=body.rate_per_hour,
            rate_per_linear_meter=body.rate_per_linear_meter,
            rate_basis=body.rate_basis,
            status=body.status,
            is_active=body.is_active,
            approval_reference=body.approval_reference,
            notes=body.notes,
            currency=body.currency,
        )
    except WorkcenterRateValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{code}")
async def patch_rate(
    code: str,
    body: WorkcenterRatePatchBody,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_permission("workcenter_rates.manage")),
) -> Dict[str, Any]:
    try:
        payload = (
            body.model_dump(exclude_unset=True)
            if hasattr(body, "model_dump")
            else body.dict(exclude_unset=True)
        )
        row = await update_workcenter_rate(
            db,
            code,
            **payload,
        )
    except WorkcenterRateValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if row is None:
        raise HTTPException(status_code=404, detail=f"workcenter_rate '{code}' not found")
    return row