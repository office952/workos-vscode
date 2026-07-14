"""Execution owner-decision production release guard routes (Wave 5 / W5-T01)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from schemas.execution_owner_decision_release import (
    OwnerDecisionResolutionRequest,
    OwnerDecisionResolutionResult,
    ProductionReleaseEvaluation,
)
from services.execution_owner_decision_production_release_service import (
    get_production_release_status,
    resolve_owner_decision_for_order,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/execution",
    tags=["execution-owner-decision-release"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/orders/{order_id}/production-release-status",
    response_model=ProductionReleaseEvaluation,
)
async def production_release_status(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("execution.task_start")),
) -> ProductionReleaseEvaluation:
    """Read-only production release evaluation from frozen snapshot + runtime resolutions."""
    logger.info("GET /api/v1/execution/orders/%s/production-release-status", order_id)
    return await get_production_release_status(db, order_id)


@router.post(
    "/orders/{order_id}/owner-decisions/{code}/resolve",
    response_model=OwnerDecisionResolutionResult,
)
async def resolve_owner_decision(
    order_id: int,
    code: str,
    body: OwnerDecisionResolutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    _user=Depends(require_permission("execution.owner_decision_resolve")),
) -> OwnerDecisionResolutionResult:
    """Persist operational resolution for a frozen production-blocking owner decision."""
    logger.info(
        "POST /api/v1/execution/orders/%s/owner-decisions/%s/resolve",
        order_id,
        code,
    )
    return await resolve_owner_decision_for_order(
        db,
        order_id=order_id,
        code=code,
        status=body.status,
        note=body.note,
        current_user=current_user,
    )
