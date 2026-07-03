"""
Execution Reality Quality Router — BUILD 18: Data Quality & Invalid Reality Marker.

Endpoints:
    POST /api/v1/execution-reality/{reality_id}/invalidate
    POST /api/v1/execution-reality/{reality_id}/restore-valid
    GET  /api/v1/execution-reality/{reality_id}/quality-status

STRICT BOUNDARIES:
  - Does NOT delete records.
  - Does NOT mutate Quote, Order, Snapshot, CostEngine.
  - Does NOT silently reverse stock.
  - Permission-protected via Build 17 system.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.execution_reality_invalidation_service import (
    ExecutionRealityInvalidationService,
    InvalidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/execution-reality",
    tags=["execution-reality-quality"],
    dependencies=[Depends(get_current_user)],
)


class InvalidateRequest(BaseModel):
    reason: str


class RestoreRequest(BaseModel):
    reason: str


@router.post("/{reality_id}/invalidate")
async def invalidate_reality(
    reality_id: int,
    req: InvalidateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("reality.invalidate")),
):
    """Invalidate an ExecutionReality record.

    Requires permission: reality.invalidate (admin, manager).
    Reason is required.
    If stock was already deducted, invalidation proceeds but marks
    stock_reconciliation_required.
    """
    if reality_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "reality_id_invalid"})

    if not req.reason or not req.reason.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "reason_required", "message": "Invalid reason is required"},
        )

    performed_by = current_user.email or current_user.name or "unknown"
    svc = ExecutionRealityInvalidationService(db)

    try:
        result = await svc.invalidate(
            reality_id=reality_id,
            reason=req.reason,
            performed_by=performed_by,
        )
        return result
    except InvalidationError as e:
        if e.code == "reality_not_found":
            raise HTTPException(status_code=404, detail={"error": e.code, "detail": e.detail})
        raise HTTPException(status_code=422, detail={"error": e.code, "detail": e.detail})


@router.post("/{reality_id}/restore-valid")
async def restore_reality(
    reality_id: int,
    req: RestoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("reality.restore_valid")),
):
    """Restore an invalid ExecutionReality record to valid state.

    Requires permission: reality.restore_valid (admin, manager).
    Blocked if stock_reconciliation_required is True.
    """
    if reality_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "reality_id_invalid"})

    if not req.reason or not req.reason.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "reason_required", "message": "Restore reason is required"},
        )

    performed_by = current_user.email or current_user.name or "unknown"
    svc = ExecutionRealityInvalidationService(db)

    try:
        result = await svc.restore_valid(
            reality_id=reality_id,
            reason=req.reason,
            performed_by=performed_by,
        )
        return result
    except InvalidationError as e:
        if e.code == "reality_not_found":
            raise HTTPException(status_code=404, detail={"error": e.code, "detail": e.detail})
        if e.code == "reality_not_invalid":
            raise HTTPException(status_code=409, detail={"error": e.code, "detail": e.detail})
        if e.code == "restoration_blocked_stock_reconciliation":
            raise HTTPException(status_code=409, detail={"error": e.code, "detail": e.detail})
        raise HTTPException(status_code=422, detail={"error": e.code, "detail": e.detail})


@router.get("/{reality_id}/quality-status")
async def get_quality_status(
    reality_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get data quality status for an ExecutionReality record.

    Read-only. Available to any authenticated user.
    """
    if reality_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "reality_id_invalid"})

    svc = ExecutionRealityInvalidationService(db)
    try:
        result = await svc.get_quality_status(reality_id)
        return result
    except InvalidationError as e:
        if e.code == "reality_not_found":
            raise HTTPException(status_code=404, detail={"error": e.code, "detail": e.detail})
        raise HTTPException(status_code=422, detail={"error": e.code, "detail": e.detail})