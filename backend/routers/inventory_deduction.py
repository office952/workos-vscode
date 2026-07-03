"""
Inventory Deduction Router — BUILD 16: Inventory Operational Loop.

Exposes controlled stock deduction from ExecutionReality.

Endpoints:
    GET  /api/v1/inventory/deduction/status/{order_id}  — eligibility check (read-only)
    POST /api/v1/inventory/deduction/deduct/{order_id}  — explicit deduction action
    GET  /api/v1/inventory/deduction/movements/{order_id} — movements for order
    GET  /api/v1/inventory/deduction/movements/recent    — recent movements

STRICT BOUNDARIES:
  - Does NOT modify Quote, Order, Snapshot, CostEngine, or commercial documents.
  - Does NOT auto-deduct on task completion.
  - Deduction requires explicit operator action via POST.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.inventory_deduction_service import (
    DeductionError,
    InventoryDeductionService,
)
from services.inventory_stock_adjustment_service import (
    InventoryStockAdjustmentService,
    StockAdjustmentError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/inventory/deduction",
    tags=["inventory_deduction"],
    dependencies=[Depends(get_current_user)],
)


class DeductMaterialsRequest(BaseModel):
    """Request to deduct materials from inventory."""
    reason: Optional[str] = None
    material_indices: Optional[List[int]] = None  # None = all eligible


class ReverseMovementRequest(BaseModel):
    reason: str = Field(..., min_length=1)


@router.get("/status/{order_id}")
async def get_deduction_status(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.view")),
):
    """Get deduction eligibility status for all material rows in an ExecutionReality.

    Read-only — does not mutate anything.
    """
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})

    svc = InventoryDeductionService(db)
    try:
        status = await svc.get_deduction_status(order_id)
        return status
    except DeductionError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": e.code, "detail": e.detail},
        )


@router.post("/deduct/{order_id}")
async def deduct_materials(
    order_id: int,
    req: DeductMaterialsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("inventory.deduct_stock")),
):
    """Explicitly deduct linked materials from inventory based on ExecutionReality.

    This is the ONLY way stock is reduced in BUILD 16.
    Requires explicit operator action — never automatic.

    Rules:
    - Only material rows with valid material_id are deducted.
    - Free-text rows are skipped (observational only).
    - Duplicate deductions are idempotent (blocked).
    - Insufficient stock blocks the specific row.
    """
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})

    performed_by = current_user.email or current_user.name or "unknown"

    svc = InventoryDeductionService(db)
    try:
        result = await svc.deduct_materials(
            order_id=order_id,
            performed_by=performed_by,
            reason=req.reason,
            material_indices=req.material_indices,
        )
        return result.to_dict()
    except DeductionError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": e.code, "detail": e.detail},
        )


@router.post("/reverse/{movement_id}")
async def reverse_movement(
    movement_id: int,
    req: ReverseMovementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("inventory.adjust_stock")),
):
    """Reverse a previously committed stock consumption movement via compensating movement."""
    performed_by = current_user.email or current_user.name or "unknown"
    svc = InventoryStockAdjustmentService(db)
    try:
        result = await svc.reverse_movement(
            movement_id=movement_id,
            performed_by=performed_by,
            reason=req.reason,
        )
        return result.to_dict()
    except StockAdjustmentError as e:
        if e.code == "movement_not_found":
            raise HTTPException(status_code=404, detail={"error": e.code, "detail": e.detail})
        if e.code == "stock_movement_already_reversed":
            existing_reversal_movement_id = None
            if isinstance(e.detail, str):
                match = re.search(r"(\d+)$", e.detail)
                if match:
                    existing_reversal_movement_id = int(match.group(1))
            raise HTTPException(
                status_code=409,
                detail={
                    "error": e.code,
                    "detail": e.detail,
                    "original_movement_id": movement_id,
                    "existing_reversal_movement_id": existing_reversal_movement_id,
                },
            )
        if e.code in {"movement_not_reversible", "material_not_found", "material_inactive", "invalid_original_quantity"}:
            raise HTTPException(status_code=422, detail={"error": e.code, "detail": e.detail})
        raise HTTPException(status_code=422, detail={"error": e.code, "detail": e.detail})


@router.get("/movements/recent")
async def get_recent_movements(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.view_movements")),
):
    """Get recent stock movements across all orders (read-only)."""
    svc = InventoryDeductionService(db)
    movements = await svc.get_recent_movements(limit=min(limit, 200))
    return {"movements": movements, "total": len(movements)}


@router.get("/movements/{order_id}")
async def get_movements_for_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.view_movements")),
):
    """Get all stock movements for a specific order (read-only)."""
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})

    svc = InventoryDeductionService(db)
    movements = await svc.get_movements_for_order(order_id)
    return {"order_id": order_id, "movements": movements, "total": len(movements)}