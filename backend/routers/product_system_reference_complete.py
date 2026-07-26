"""PRODUCT_SYSTEM_REFERENCE_COMPLETE — final laboratory closure endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.product_system_reference_complete import ProductSystemReferenceCompleteResponse
from services.product_system_reference_complete_service import (
    ProductSystemReferenceCompleteService,
)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-reference-complete"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/reference-complete", response_model=ProductSystemReferenceCompleteResponse)
async def get_product_system_reference_complete(
    db: AsyncSession = Depends(get_db),
) -> ProductSystemReferenceCompleteResponse:
    return await ProductSystemReferenceCompleteService(db).build()
