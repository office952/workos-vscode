"""Build 4C — Execution preview from frozen modular graph (strictly read-only)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.execution_preview_from_frozen import ExecutionPreviewFromFrozen
from services.execution_preview_from_frozen_graph_service import (
    build_execution_preview_from_frozen_order,
    build_execution_preview_from_frozen_snapshot,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/execution",
    tags=["execution-preview-from-frozen"],
    dependencies=[Depends(get_current_user)],
)


class FrozenSnapshotPreviewRequest(BaseModel):
    """In-memory QuoteSnapshotV2 / OrderSnapshotV2 JSON — no DB write."""

    snapshot: dict[str, Any]
    source_kind: str | None = None
    order_id: int | None = Field(default=None)


@router.post(
    "/plan-v2/preview-from-frozen-snapshot",
    response_model=ExecutionPreviewFromFrozen,
)
async def post_preview_from_frozen_snapshot(
    body: FrozenSnapshotPreviewRequest,
) -> ExecutionPreviewFromFrozen:
    """
    Project execution candidates from a caller-supplied V2 snapshot.

    Zero DB access. Never persists ExecutionPlan. Never materializes tasks.
    Never recompiles Product System / Aggregate / CPP.
    """
    logger.info("POST /api/v1/execution/plan-v2/preview-from-frozen-snapshot")
    return build_execution_preview_from_frozen_snapshot(
        body.snapshot,
        order_id=body.order_id,
        source_kind=body.source_kind,
    )


@router.get(
    "/plan-v2/preview-from-frozen/{order_id}",
    response_model=ExecutionPreviewFromFrozen,
)
async def get_preview_from_frozen_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> ExecutionPreviewFromFrozen:
    """
    Read orders.snapshot_v2_json only and project execution preview.

    Distinct from POST /plan-v2/from-order (persist) and materialize-tasks.
    """
    logger.info("GET /api/v1/execution/plan-v2/preview-from-frozen/%s", order_id)
    if order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    preview = await build_execution_preview_from_frozen_order(db, order_id)
    if "order_not_found" in preview.blockers:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})
    return preview
