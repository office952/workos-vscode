from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.product_template_availability import ProductTemplateAvailabilityResponse
from services.product_template_availability_service import ProductTemplateAvailabilityService


router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-template-availability"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/template-availability", response_model=ProductTemplateAvailabilityResponse)
async def list_product_template_availability(
    offerable_only: bool = Query(False),
    include_runtime_modules: bool = Query(True),
    include_archived: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> ProductTemplateAvailabilityResponse:
    return await ProductTemplateAvailabilityService(db).list_availability(
        offerable_only=offerable_only,
        include_runtime_modules=include_runtime_modules,
        include_archived=include_archived,
    )
