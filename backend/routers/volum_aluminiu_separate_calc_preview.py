"""Read-only separate calculation preview for aluminium return component."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.volum_aluminiu_separate_calc_preview import (
    VolumAluminiuSeparateCalcPreviewRequest,
    VolumAluminiuSeparateCalcPreviewResponse,
)
from services.volum_aluminiu_component_contract import TEMPLATE_CODE
from services.volum_aluminiu_separate_calc_preview_service import (
    VolumAluminiuSeparateCalcPreviewService,
)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-volum-aluminiu-separate-calc"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/templates/{template_code}/separate-calculation-preview",
    response_model=VolumAluminiuSeparateCalcPreviewResponse,
)
async def post_separate_calculation_preview(
    template_code: str,
    body: VolumAluminiuSeparateCalcPreviewRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> VolumAluminiuSeparateCalcPreviewResponse:
    """
    Deterministic read-only separate calc preview for TPL-VOLUM-ALUMINIU_v1.

    No Product Truth / Quote / Order / ExecutionPlan persistence.
    Does not activate or publish the component.
    """
    code = (template_code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail={"error": "template_code_required"})
    if code != TEMPLATE_CODE:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "separate_calculation_preview_unsupported_template",
                "template_code": code,
                "supported": [TEMPLATE_CODE],
            },
        )
    request = body or VolumAluminiuSeparateCalcPreviewRequest()
    return VolumAluminiuSeparateCalcPreviewService(db).build_preview(code, request)
