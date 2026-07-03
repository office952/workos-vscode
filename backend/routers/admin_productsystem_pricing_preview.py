from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.productsystem_pricing_preview_service import ProductSystemPricingPreviewService


router = APIRouter(
    prefix="/api/admin/productsystem",
    tags=["admin_productsystem_pricing_preview"],
    dependencies=[Depends(get_current_user)],
)


class ProductSystemPricingPreviewRequest(BaseModel):
    material_code: str = Field(..., min_length=1)
    quantity: float = Field(default=1.0)
    vat_percent: Optional[float] = Field(default=None)
    include_vat: Optional[bool] = Field(default=True)
    requested_scope: Optional[str] = None
    notes: Optional[str] = None


@router.post("/pricing-preview")
async def run_pricing_preview(
    body: ProductSystemPricingPreviewRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.view")),
) -> Dict[str, Any]:
    service = ProductSystemPricingPreviewService(db)
    try:
        return await service.preview(
            material_code=body.material_code,
            quantity=body.quantity,
            vat_percent=body.vat_percent,
            include_vat=bool(body.include_vat),
            requested_scope=body.requested_scope,
            notes=body.notes,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))