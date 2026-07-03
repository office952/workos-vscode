"""Company commercial settings API — canonical VAT % for quotes."""

import logging

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from schemas.auth import UserResponse
from services.company_commercial_settings_service import (
    CompanyCommercialSettingsService,
    validate_eur_to_ron_rate,
    validate_vat_pct,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/company-commercial-settings",
    tags=["company-commercial-settings"],
    dependencies=[Depends(get_current_user)],
)


class CompanyCommercialSettingsData(BaseModel):
    default_vat_pct: float | None = Field(default=None, ge=0, le=100)
    eur_to_ron_rate: float | None = Field(default=None, gt=0)


class CompanyCommercialSettingsResponse(BaseModel):
    default_vat_pct: float
    eur_to_ron_rate: float


@router.get("", response_model=CompanyCommercialSettingsResponse)
async def get_company_commercial_settings(
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("settings.view")),
):
    svc = CompanyCommercialSettingsService(db)
    data = await svc.get_settings()
    return CompanyCommercialSettingsResponse(**data)


@router.put("", response_model=CompanyCommercialSettingsResponse)
async def update_company_commercial_settings(
    body: CompanyCommercialSettingsData,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("settings.update")),
):
    try:
        if body.default_vat_pct is not None:
            validate_vat_pct(body.default_vat_pct)
        if body.eur_to_ron_rate is not None:
            validate_eur_to_ron_rate(body.eur_to_ron_rate)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    svc = CompanyCommercialSettingsService(db)
    data = await svc.update_settings(
        default_vat_pct=body.default_vat_pct,
        eur_to_ron_rate=body.eur_to_ron_rate,
    )
    return CompanyCommercialSettingsResponse(**data)
