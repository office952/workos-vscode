"""Authorized canonical material actual movement APIs (F4)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from models.stock_movements import StockMovement
from schemas.auth import UserResponse
from services.material_actuals_service import MaterialActualsService

router = APIRouter(prefix="/api/v1/material-actuals", tags=["material-actuals"])


class IssueInput(BaseModel):
    material_id: int
    quantity: float = Field(gt=0)
    unit: str
    idempotency_key: str = Field(min_length=1)
    task_id: str | None = None
    source_type: str = "manual_material_actual"
    reason: str | None = None


class ReturnInput(BaseModel):
    reverses_movement_id: int
    quantity: float = Field(gt=0)
    idempotency_key: str = Field(min_length=1)
    reason: str | None = None


class ScrapInput(BaseModel):
    material_id: int
    quantity: float = Field(gt=0)
    unit: str
    scrap_reason: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    task_id: str | None = None


class PlannedBomRejectInput(BaseModel):
    source_type: str = "planned_bom"
    material_id: int = 1
    quantity: float = 1
    unit: str = "buc"
    idempotency_key: str = "reject-bom"


@router.post("/orders/{order_id}/issue")
async def issue_material(
    order_id: int,
    payload: IssueInput,
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
    _permission: UserResponse = Depends(require_permission("inventory.material_actual.write")),
):
    result = await MaterialActualsService(db).record_issue(
        order_id=order_id,
        material_id=payload.material_id,
        quantity=payload.quantity,
        unit=payload.unit,
        actor_id=str(user.id),
        idempotency_key=payload.idempotency_key,
        task_id=payload.task_id,
        source_type=payload.source_type,
        reason=payload.reason,
    )
    await db.commit()
    return result


@router.post("/orders/{order_id}/return")
async def return_material(
    order_id: int,
    payload: ReturnInput,
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
    _permission: UserResponse = Depends(require_permission("inventory.material_actual.write")),
):
    result = await MaterialActualsService(db).record_return(
        order_id=order_id,
        reverses_movement_id=payload.reverses_movement_id,
        quantity=payload.quantity,
        actor_id=str(user.id),
        idempotency_key=payload.idempotency_key,
        reason=payload.reason,
    )
    await db.commit()
    return result


@router.post("/orders/{order_id}/scrap")
async def scrap_material(
    order_id: int,
    payload: ScrapInput,
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
    _permission: UserResponse = Depends(require_permission("inventory.material_actual.write")),
):
    result = await MaterialActualsService(db).record_scrap(
        order_id=order_id,
        material_id=payload.material_id,
        quantity=payload.quantity,
        unit=payload.unit,
        actor_id=str(user.id),
        idempotency_key=payload.idempotency_key,
        scrap_reason=payload.scrap_reason,
        task_id=payload.task_id,
    )
    await db.commit()
    return result


@router.post("/orders/{order_id}/reject-non-actual")
async def reject_non_actual(
    order_id: int,
    payload: PlannedBomRejectInput,
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
    _permission: UserResponse = Depends(require_permission("inventory.material_actual.write")),
):
    # Explicit probe endpoint for planned/reservation rejection contract.
    _ = order_id
    return await MaterialActualsService(db).record_issue(
        order_id=order_id,
        material_id=payload.material_id,
        quantity=payload.quantity,
        unit=payload.unit,
        actor_id=str(user.id),
        idempotency_key=payload.idempotency_key,
        source_type=payload.source_type,
    )


@router.get("/orders/{order_id}/basis")
async def material_basis(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _permission: UserResponse = Depends(require_permission("inventory.view_movements")),
):
    return await MaterialActualsService(db).material_actual_basis(order_id)


@router.get("/orders/{order_id}/movements")
async def list_movements(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
    _permission: UserResponse = Depends(require_permission("inventory.view_movements")),
):
    include_valuation = str(user.role or "").lower() in {"admin", "manager"}
    rows = (
        await db.execute(
            select(StockMovement)
            .where(StockMovement.order_id == order_id)
            .order_by(StockMovement.performed_at.desc())
        )
    ).scalars().all()
    svc = MaterialActualsService(db)
    return {
        "order_id": order_id,
        "include_valuation": include_valuation,
        "movements": [
            svc.serialize_movement(m, include_valuation=include_valuation) for m in rows
        ],
    }
