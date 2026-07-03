"""Operational Reality Review API — read-only gaps dashboard."""
from __future__ import annotations

import logging

from core.database import get_db
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends
from services.operational_reality_review_service import OperationalRealityReviewService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/operational-reality",
    tags=["operational-reality"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/review")
async def get_operational_reality_review(db: AsyncSession = Depends(get_db)):
    """Read-only review of operational reality completeness and quality gaps.

    Does NOT mutate execution_reality, inventory, quotes, or costs.
    """
    svc = OperationalRealityReviewService(db)
    return await svc.build_review()
