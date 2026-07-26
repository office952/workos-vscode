"""Component contract API — child/dual-role PT + used-by; no CT table."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.product_template_component_contract import (
    ComponentContractChildEdge,
    ComponentContractLinkPatchRequest,
    ProductTemplateComponentContractView,
)
from services.product_template_component_contract_service import (
    ProductTemplateComponentContractService,
)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-component-contracts"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/templates/{template_code}/component-contract",
    response_model=ProductTemplateComponentContractView,
)
async def get_component_contract(
    template_code: str,
    db: AsyncSession = Depends(get_db),
) -> ProductTemplateComponentContractView:
    code = (template_code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail={"error": "template_code_required"})
    return await ProductTemplateComponentContractService(db).get_contract(code)


@router.patch(
    "/module-links/{link_id}/component-contract",
    response_model=ComponentContractChildEdge,
)
async def patch_component_contract_link(
    link_id: int,
    body: ComponentContractLinkPatchRequest,
    db: AsyncSession = Depends(get_db),
) -> ComponentContractChildEdge:
    return await ProductTemplateComponentContractService(db).patch_link(link_id, body)
