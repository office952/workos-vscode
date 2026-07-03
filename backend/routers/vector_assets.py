from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from schemas.vector_assets import (
    SvgLayerAnalysisRequest,
    SvgLayerAnalysisResponse,
    SvgMetricsPreviewRequest,
    VectorAssetPreviewResponse,
    VectorAssetRegisterRequest,
    VectorAssetRegisterResponse,
    VectorAssetDTO,
    VectorAssetSheetFitPreviewResponse,
)
from services.vector_asset_service import VectorAssetService

router = APIRouter(
    prefix="/api/v1/vector-assets",
    tags=["vector_assets"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/preview-metrics", response_model=VectorAssetPreviewResponse)
async def preview_metrics(
    request: SvgMetricsPreviewRequest,
    db: AsyncSession = Depends(get_db),
) -> VectorAssetPreviewResponse:
    service = VectorAssetService(db)
    result = await service.preview_metrics(svg_text=request.svg_text)
    return VectorAssetPreviewResponse(**result.model_dump())


@router.post("/analyze-layers", response_model=SvgLayerAnalysisResponse)
async def analyze_svg_layers(
    request: SvgLayerAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> SvgLayerAnalysisResponse:
    """Read-only SVG layer → template_code analysis for preliminary quote prep."""
    service = VectorAssetService(db)
    result = await service.analyze_layers(
        svg_text=request.svg_text,
        known_template_codes=request.known_template_codes,
        source_file_name=request.source_file_name,
        manual_layer_mappings=request.manual_layer_mappings,
    )
    return SvgLayerAnalysisResponse(**result)


@router.post("/register-from-storage", response_model=VectorAssetRegisterResponse)
async def register_from_storage(
    request: VectorAssetRegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> VectorAssetRegisterResponse:
    service = VectorAssetService(db)
    asset = await service.register_from_storage(req=request, current_user=current_user)
    return VectorAssetRegisterResponse(asset=asset)


@router.get("/{asset_id}", response_model=VectorAssetDTO)
async def get_vector_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
) -> VectorAssetDTO:
    service = VectorAssetService(db)
    return await service.get_asset(asset_id=asset_id)


@router.get("/{asset_id}/sheet-fit-preview", response_model=VectorAssetSheetFitPreviewResponse)
async def get_sheet_fit_preview(
    asset_id: int,
    material_id: int,
    db: AsyncSession = Depends(get_db),
) -> VectorAssetSheetFitPreviewResponse:
    service = VectorAssetService(db)
    return await service.get_sheet_fit_preview(asset_id=asset_id, material_id=material_id)
