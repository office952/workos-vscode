"""Dual Quote Snapshot V2 preview/freeze endpoints (Step 8 MVP)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.quote_snapshot_v2 import QuoteSnapshotV2
from services.quote_snapshot_v2_service import QuoteSnapshotV2Service
from services.template_architecture_scope import require_canonical_template_code

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-quote-snapshot-v2"],
    dependencies=[Depends(get_current_user)],
)


class QuoteSnapshotV2PreviewRequest(BaseModel):
    workspace_id: str | None = None
    quote_id: str | None = None
    quote_input: dict[str, Any] | None = None
    currency: str = Field(default="RON", min_length=3, max_length=3)
    requested_by: str | None = None


class QuoteSnapshotV2FreezeRequest(BaseModel):
    workspace_id: str | None = None
    quote_id: str | None = None
    quote_input: dict[str, Any] | None = None
    currency: str = Field(default="RON", min_length=3, max_length=3)
    frozen_by: str | None = None


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.post(
    "/quote-snapshot-v2/preview/{template_code}",
    response_model=QuoteSnapshotV2,
)
async def post_quote_snapshot_v2_preview(
    template_code: str,
    body: QuoteSnapshotV2PreviewRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> QuoteSnapshotV2:
    """
    Build and return a read-only dual quote snapshot preview.

    Composes 7G CommercialPriceProposal + 7H EstimatedInternalCost.
    No persist, no /price, no quote update, no order/task creation.
    """
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
                canonical_template_code=identity.canonical_template_code,
                resolution_type=identity.resolution_type,
                legacy_alias_used=identity.legacy_alias_used,
                resolution_source=identity.resolution_source,
            ),
        )

    canonical = identity.canonical_template_code
    request = body or QuoteSnapshotV2PreviewRequest()
    service = QuoteSnapshotV2Service(db)
    snapshot = await service.build_preview(
        canonical,
        workspace_id=request.workspace_id,
        quote_id=request.quote_id,
        quote_input=request.quote_input,
        currency=request.currency,
        requested_by=request.requested_by,
    )
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "quote_snapshot_v2_preview_not_found",
                template_code=template_code,
                workspace_id=request.workspace_id,
            ),
        )
    return snapshot


@router.post(
    "/quote-snapshot-v2/freeze/{template_code}",
    response_model=QuoteSnapshotV2,
)
async def post_quote_snapshot_v2_freeze(
    template_code: str,
    body: QuoteSnapshotV2FreezeRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> QuoteSnapshotV2:
    """
    Attempt to freeze dual quote snapshot.

    Returns blocked_schema_missing when no safe persistence path exists.
    Never calls /price, CostEngine, or QuoteOrchestrator.
    """
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
                canonical_template_code=identity.canonical_template_code,
                resolution_type=identity.resolution_type,
                legacy_alias_used=identity.legacy_alias_used,
                resolution_source=identity.resolution_source,
            ),
        )

    canonical = identity.canonical_template_code
    request = body or QuoteSnapshotV2FreezeRequest()
    service = QuoteSnapshotV2Service(db)
    snapshot = await service.freeze(
        canonical,
        workspace_id=request.workspace_id,
        quote_id=request.quote_id,
        quote_input=request.quote_input,
        currency=request.currency,
        frozen_by=request.frozen_by,
    )
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "quote_snapshot_v2_freeze_not_found",
                template_code=template_code,
                workspace_id=request.workspace_id,
            ),
        )
    return snapshot


@router.get(
    "/quote-snapshot-v2/{snapshot_code}",
    response_model=QuoteSnapshotV2,
)
async def get_quote_snapshot_v2_by_code(
    snapshot_code: str,
    db: AsyncSession = Depends(get_db),
) -> QuoteSnapshotV2:
    """Retrieve a persisted dual quote snapshot by snapshot_code."""
    service = QuoteSnapshotV2Service(db)
    snapshot = await service.get_by_snapshot_code(snapshot_code)
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "quote_snapshot_v2_not_found",
                snapshot_code=snapshot_code,
            ),
        )
    return snapshot
