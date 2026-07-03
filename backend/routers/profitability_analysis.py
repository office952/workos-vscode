"""Read-only ProfitabilityAnalysis endpoint (Step 10.3)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.profitability_analysis import ProfitabilityAnalysisResponse
from services.profitability_analysis_service import (
    OrderNotFoundError,
    ProfitabilityAnalysisService,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/profitability-analysis",
    tags=["profitability-analysis"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/order/{order_id}",
    response_model=ProfitabilityAnalysisResponse,
)
async def get_profitability_analysis_for_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProfitabilityAnalysisResponse:
    """
    Read-only profitability analysis for a single order.

    No persist, no /price, no CostEngine, no QuoteOrchestrator, no write-back.
    """
    if order_id <= 0:
        raise HTTPException(
            status_code=422,
            detail={"error": "order_id_invalid", "order_id": order_id},
        )

    service = ProfitabilityAnalysisService(db)
    try:
        return await service.analyze_order(order_id)
    except OrderNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={"error": "order_not_found", "order_id": order_id},
        ) from None
