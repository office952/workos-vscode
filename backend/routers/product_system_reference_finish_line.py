"""PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1 — frozen reference contracts."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.product_system_reference_finish_line import (
    CriticalMaterialPolicyResponse,
    FinishLineContractResponse,
    FormFieldOwnershipMapResponse,
)
from schemas.workflow_adv_analyzer_io_contract_v1 import (
    AnalyzerIoContractDocumentV1,
    build_analyzer_io_contract_document,
)
from services.product_system_reference_finish_line_service import (
    ProductSystemReferenceFinishLineService,
    build_form_field_ownership_map,
)

router = APIRouter(
    prefix="/api/v1/product-system/reference-finish-line",
    tags=["product-system-reference-finish-line"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/contract", response_model=FinishLineContractResponse)
async def get_finish_line_contract(
    db: AsyncSession = Depends(get_db),
) -> FinishLineContractResponse:
    return await ProductSystemReferenceFinishLineService(db).build_contract()


@router.get("/form-field-ownership-map", response_model=FormFieldOwnershipMapResponse)
async def get_form_field_ownership_map() -> FormFieldOwnershipMapResponse:
    return build_form_field_ownership_map()


@router.get("/analyzer-io-contract", response_model=AnalyzerIoContractDocumentV1)
async def get_analyzer_io_contract() -> AnalyzerIoContractDocumentV1:
    return build_analyzer_io_contract_document()


@router.get("/critical-materials", response_model=CriticalMaterialPolicyResponse)
async def get_critical_materials(
    db: AsyncSession = Depends(get_db),
) -> CriticalMaterialPolicyResponse:
    return await ProductSystemReferenceFinishLineService(db).build_critical_materials()
