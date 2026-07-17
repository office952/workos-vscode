"""Template Lifecycle Control System V1 — read-only Product System endpoints.

GET-only. No writes. No parallel registry. Product System remains authority.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.template_lifecycle_control import (
    TemplateLifecycleImpactResponse,
    TemplateLifecycleInspectResponse,
    TemplateLifecycleReadiness,
    TemplateLifecycleValidateResponse,
)
from services.template_lifecycle_control_service import TemplateLifecycleControlService

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-template-lifecycle"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/templates/{template_code}/lifecycle-readiness",
    response_model=TemplateLifecycleReadiness,
)
async def get_template_lifecycle_readiness(
    template_code: str,
    db: AsyncSession = Depends(get_db),
) -> TemplateLifecycleReadiness:
    code = (template_code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail={"error": "template_code_required"})
    return await TemplateLifecycleControlService(db).build_readiness(code)


@router.get(
    "/templates/{template_code}/lifecycle-impact",
    response_model=TemplateLifecycleImpactResponse,
)
async def get_template_lifecycle_impact(
    template_code: str,
    db: AsyncSession = Depends(get_db),
) -> TemplateLifecycleImpactResponse:
    code = (template_code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail={"error": "template_code_required"})
    return await TemplateLifecycleControlService(db).build_impact(code)


@router.get(
    "/templates/{template_code}/lifecycle-inspect",
    response_model=TemplateLifecycleInspectResponse,
)
async def inspect_template_lifecycle(
    template_code: str,
    db: AsyncSession = Depends(get_db),
) -> TemplateLifecycleInspectResponse:
    code = (template_code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail={"error": "template_code_required"})
    return await TemplateLifecycleControlService(db).inspect(code)


@router.get(
    "/template-lifecycle/validate",
    response_model=TemplateLifecycleValidateResponse,
)
async def validate_template_lifecycle(
    template_code: list[str] | None = Query(default=None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> TemplateLifecycleValidateResponse:
    return await TemplateLifecycleControlService(db).validate(
        template_codes=template_code,
        active_only=active_only,
    )
