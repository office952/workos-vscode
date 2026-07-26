"""Read-only EstimatedInternalCost preview endpoint (Step 7H)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.template_architecture_scope import require_canonical_template_code

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-estimated-internal-cost"],
    dependencies=[Depends(get_current_user)],
)


class EstimatedInternalCostPreviewRequest(BaseModel):
    workspace_id: str | None = None
    quote_input: dict[str, Any] | None = None
    currency: str = Field(default="RON", min_length=3, max_length=3)


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.post(
    "/estimated-internal-cost-preview/{template_code}",
    response_model=EstimatedInternalCostPreview,
)
async def post_estimated_internal_cost_preview(
    template_code: str,
    body: EstimatedInternalCostPreviewRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> EstimatedInternalCostPreview:
    """
    Build and return a read-only EstimatedInternalCost preview.

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
    request = body or EstimatedInternalCostPreviewRequest()
    service = EstimatedInternalCostService(db)
    preview = await service.build_preview(
        canonical,
        workspace_id=request.workspace_id,
        quote_input=request.quote_input,
        currency=request.currency,
    )
    if preview is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "estimated_internal_cost_preview_not_found",
                template_code=template_code,
                workspace_id=request.workspace_id,
            ),
        )
    return preview
