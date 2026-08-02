"""Read-only Profitability Actual Read Model V1."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.profitability_actual_read_model_service import (
    OrderNotFoundError,
    ProfitabilityActualReadModelService,
)

router = APIRouter(
    prefix="/api/v1/profitability-actual",
    tags=["profitability-actual-read-model"],
)


@router.get("/order/{order_id}")
async def get_profitability_actual_read_model(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    _perm=Depends(require_permission("execution.plan_generate")),
):
    """Honest profitability composition — missing costs stay unavailable (not zero).

    Audience: management/supervisor (admin/manager). Never invents labor money.
    """
    if order_id <= 0:
        raise HTTPException(
            status_code=422,
            detail={"error": "order_id_invalid", "order_id": order_id},
        )
    _ = current_user  # authenticated; permission enforces admin/manager

    service = ProfitabilityActualReadModelService(db)
    try:
        return await service.build(order_id)
    except OrderNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={"error": "order_not_found", "order_id": order_id},
        ) from None
