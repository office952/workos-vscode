from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_admin_user, get_current_user
from schemas.auth import UserResponse
from services.integration_settings_service import (
    clear_smartbill_token,
    get_smartbill_effective_config,
    get_smartbill_settings,
    record_smartbill_test_result,
    test_smartbill_config_local,
    upsert_smartbill_settings,
)
from services.smartbill_client import SmartbillClient, get_smartbill_config_health_for_db, normalize_tax_id

router = APIRouter(
    prefix="/api/v1/integrations/providers",
    tags=["provider_integrations"],
    dependencies=[Depends(get_current_user)],
)


class ProviderHealthPresentFields(BaseModel):
    base_url: bool
    username: bool
    token: bool
    lookup_path: bool
    timeout_seconds: bool


class ProviderHealthMasked(BaseModel):
    base_url_host: str | None = None
    username_hint: str | None = None


class ProviderHealthSettings(BaseModel):
    timeout_seconds: float | None = None
    lookup_path: str


class ProviderHealthLiveValidation(BaseModel):
    performed: bool = False
    status: Literal["not_run"] = "not_run"
    message: str


class SmartbillProviderHealthResponse(BaseModel):
    provider: Literal["smartbill"] = "smartbill"
    source: Literal["app_settings", "env", "none"]
    enabled: bool
    configured: bool
    status: Literal["disabled", "not_configured", "configured", "invalid_config"]
    missing_fields: list[str] = Field(default_factory=list)
    present_fields: ProviderHealthPresentFields
    masked: ProviderHealthMasked
    settings: ProviderHealthSettings
    live_validation: ProviderHealthLiveValidation
    warnings: list[str] = Field(default_factory=list)


class SmartbillConfigMaskedResponse(BaseModel):
    provider: Literal["smartbill"] = "smartbill"
    source: Literal["app_settings", "env", "none"]
    enabled: bool
    base_url: str | None = None
    username_present: bool
    username_hint: str | None = None
    token_present: bool
    lookup_path: str
    timeout_seconds: int
    last_test_status: str
    last_test_at: str | None = None
    last_test_message: str | None = None


class SmartbillConfigUpdateRequest(BaseModel):
    enabled: bool
    base_url: str | None = None
    username: str | None = None
    token: str | None = None
    lookup_path: str = "/fiscal-lookup"
    timeout_seconds: int = 5
    clear_token: bool = False


class SmartbillConfigTestResponse(BaseModel):
    provider: Literal["smartbill"] = "smartbill"
    source: Literal["app_settings", "env", "none"]
    status: Literal["disabled", "not_configured", "configured", "invalid_config"]
    ok: bool
    mode: Literal["local_config_validation"] = "local_config_validation"
    message: str
    warnings: list[str] = Field(default_factory=list)


class SmartbillUatLookupRequest(BaseModel):
    tax_id: str
    country: Literal["RO"] = "RO"


class SmartbillUatLookupResponse(BaseModel):
    provider: Literal["smartbill"] = "smartbill"
    mode: Literal["controlled_uat"] = "controlled_uat"
    live_call_executed: bool
    source: Literal["app_settings", "env", "none"]
    status: Literal[
        "not_configured",
        "invalid_input",
        "found",
        "not_found",
        "provider_timeout",
        "provider_error",
        "rate_limited",
    ]
    message: str
    normalized: dict | None = None
    warnings: list[str] = Field(default_factory=list)


def _to_masked_response(data) -> SmartbillConfigMaskedResponse:
    return SmartbillConfigMaskedResponse(**data.__dict__)


@router.get("/smartbill/config", response_model=SmartbillConfigMaskedResponse)
async def get_smartbill_provider_config(db: AsyncSession = Depends(get_db)) -> SmartbillConfigMaskedResponse:
    cfg = await get_smartbill_settings(db)
    return _to_masked_response(cfg)


@router.put("/smartbill/config", response_model=SmartbillConfigMaskedResponse)
async def put_smartbill_provider_config(
    body: SmartbillConfigUpdateRequest,
    current_user: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> SmartbillConfigMaskedResponse:
    cfg = await upsert_smartbill_settings(db, body.model_dump(), user_id=current_user.id)
    return _to_masked_response(cfg)


@router.post("/smartbill/test-connection", response_model=SmartbillConfigTestResponse)
async def post_smartbill_provider_test_connection(
    current_user: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> SmartbillConfigTestResponse:
    result = await test_smartbill_config_local(db, user_id=current_user.id)
    return SmartbillConfigTestResponse(**result)


@router.post("/smartbill/uat/test-lookup", response_model=SmartbillUatLookupResponse)
async def post_smartbill_provider_uat_test_lookup(
    body: SmartbillUatLookupRequest,
    current_user: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> SmartbillUatLookupResponse:
    if str(os.environ.get("SMARTBILL_UAT_ENABLED", "false")).strip().lower() not in {"1", "true", "yes", "on"}:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail="Controlled UAT is disabled. Set SMARTBILL_UAT_ENABLED=true explicitly.",
        )

    normalized_tax_id = normalize_tax_id(body.tax_id, country=body.country)
    if not normalized_tax_id:
        await record_smartbill_test_result(
            db,
            user_id=current_user.id,
            success=False,
            message="Controlled UAT lookup failed: invalid input.",
            warnings=["Invalid tax_id format for RO."],
        )
        return SmartbillUatLookupResponse(
            live_call_executed=False,
            source="env",
            status="invalid_input",
            message="Invalid tax_id format. Expected RO CUI.",
            warnings=["Controlled UAT lookup rejected invalid input."],
        )

    effective = await get_smartbill_effective_config(db)
    client = await SmartbillClient.from_db_or_env(db)
    source = effective.source

    result = await client.lookup_company(country=body.country, tax_id=normalized_tax_id)

    await record_smartbill_test_result(
        db,
        user_id=current_user.id,
        success=result.status == "found",
        message=f"Controlled UAT lookup status: {result.status}.",
        warnings=result.warnings,
    )

    return SmartbillUatLookupResponse(
        live_call_executed=True,
        source=source,
        status=result.status,
        message=result.message,
        normalized=result.normalized,
        warnings=result.warnings,
    )


@router.delete("/smartbill/secret/token", response_model=SmartbillConfigMaskedResponse)
async def delete_smartbill_provider_token(
    current_user: UserResponse = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> SmartbillConfigMaskedResponse:
    cfg = await clear_smartbill_token(db, user_id=current_user.id)
    return _to_masked_response(cfg)


@router.get("/smartbill/health", response_model=SmartbillProviderHealthResponse)
async def get_smartbill_provider_health(db: AsyncSession = Depends(get_db)) -> SmartbillProviderHealthResponse:
    health = await get_smartbill_config_health_for_db(db)
    return SmartbillProviderHealthResponse(**health.__dict__)