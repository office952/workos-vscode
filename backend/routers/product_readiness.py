from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.product_readiness import ProductReadinessDTO
from services.intake_product_spec_loader import load_intake_product_spec
from services.product_readiness_service import ProductReadinessService

router = APIRouter(
    tags=["product_readiness"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/api/v1/product_system/readiness/{template_id}", response_model=ProductReadinessDTO)
async def get_product_readiness(
    template_id: int,
    intake_id: Optional[int] = Query(None, description="Optional intake id for vector file context"),
    db: AsyncSession = Depends(get_db),
) -> ProductReadinessDTO:
    service = ProductReadinessService(db)
    product_spec = await load_intake_product_spec(db, intake_id)
    result = await service.evaluate(template_id, product_spec=product_spec)
    return ProductReadinessDTO(**result.to_dict())


@router.get("/api/v1/product-readiness/blueprints/{blueprint_id}", response_model=ProductReadinessDTO)
async def get_blueprint_readiness(
    blueprint_id: int,
    intake_id: Optional[int] = Query(None, description="Optional intake id for vector file context"),
    db: AsyncSession = Depends(get_db),
) -> ProductReadinessDTO:
    service = ProductReadinessService(db)
    product_spec = await load_intake_product_spec(db, intake_id)
    result = await service.evaluate(blueprint_id, product_spec=product_spec)
    return ProductReadinessDTO(**result.to_dict())
