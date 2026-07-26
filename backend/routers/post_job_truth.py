"""Read-only post-job truth endpoint for Execution detail."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.post_job_truth import PostJobTruthResponse
from services.post_job_truth_service import OrderNotFoundError, PostJobTruthService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/execution",
    tags=["post-job-truth"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/{order_id}/post-job-truth",
    response_model=PostJobTruthResponse,
)
async def get_post_job_truth_for_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> PostJobTruthResponse:
    """
    Cohesive read model: baseline + actuals + reconciliation + profitability coverage.

    No persist, no CostEngine, no quote/order write-back, no labor money.
    """
    if order_id <= 0:
        raise HTTPException(
            status_code=422,
            detail={"error": "order_id_invalid", "order_id": order_id},
        )

    service = PostJobTruthService(db)
    try:
        return await service.build_for_order(order_id)
    except OrderNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={"error": "order_not_found", "order_id": order_id},
        ) from None
