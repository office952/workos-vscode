"""Product Template publication lifecycle endpoints.

POST transitions are hard-gated by E2E readiness for publish / e2e_checked.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.product_template_publication import (
    ProductTemplatePublicationState,
    ProductTemplatePublicationTransitionRequest,
    ProductTemplatePublicationTransitionResponse,
)
from services.product_template_publication_service import ProductTemplatePublicationService

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-publication"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/templates/{template_code}/publication",
    response_model=ProductTemplatePublicationState,
)
async def get_product_template_publication(
    template_code: str,
    db: AsyncSession = Depends(get_db),
) -> ProductTemplatePublicationState:
    code = (template_code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail={"error": "template_code_required"})
    return await ProductTemplatePublicationService(db).get_state(code)


@router.post(
    "/templates/{template_code}/publication/transition",
    response_model=ProductTemplatePublicationTransitionResponse,
)
async def transition_product_template_publication(
    template_code: str,
    body: ProductTemplatePublicationTransitionRequest,
    db: AsyncSession = Depends(get_db),
) -> ProductTemplatePublicationTransitionResponse:
    code = (template_code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail={"error": "template_code_required"})
    return await ProductTemplatePublicationService(db).transition(code, body)
