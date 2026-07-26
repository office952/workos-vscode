"""PRODUCT_PRICE_BREAKDOWN_V1 — read-only price breakdown adapter."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.product_price_breakdown import ProductPriceBreakdownResponse
from services.product_price_breakdown_service import ProductPriceBreakdownService
from services.template_architecture_scope import require_canonical_template_code

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-price-breakdown"],
    dependencies=[Depends(get_current_user)],
)


class PriceBreakdownRequest(BaseModel):
    workspace_id: Optional[str] = None
    quote_input: Optional[dict[str, Any]] = None
    currency: str = Field(default="RON", min_length=3, max_length=3)
    fixture_id: Optional[str] = None


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.post(
    "/templates/{template_code}/price-breakdown",
    response_model=ProductPriceBreakdownResponse,
)
async def post_product_price_breakdown(
    template_code: str,
    body: PriceBreakdownRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ProductPriceBreakdownResponse:
    """
    Read-model over CPP + EIC + recipe. Does not recalculate or persist.
    Without workspace_id/quote_input, uses a built-in demo fixture when available.
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
            ),
        )

    request = body or PriceBreakdownRequest()
    service = ProductPriceBreakdownService(db)
    return await service.build(
        identity.canonical_template_code,
        workspace_id=request.workspace_id,
        quote_input=request.quote_input,
        currency=request.currency,
        fixture_id=request.fixture_id,
    )
