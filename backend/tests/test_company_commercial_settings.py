"""Tests for company commercial settings — canonical VAT % governance."""

from __future__ import annotations

import pytest

from models.company_commercial_settings import CompanyCommercialSettings
from services.company_commercial_settings_service import (
    CompanyCommercialSettingsService,
    DEFAULT_EUR_TO_RON_RATE,
    DEFAULT_VAT_PCT,
    validate_vat_pct,
)


@pytest.mark.asyncio
async def test_default_vat_pct_when_row_missing(db_session):
    svc = CompanyCommercialSettingsService(db_session)
    data = await svc.get_settings()
    assert data["default_vat_pct"] == DEFAULT_VAT_PCT
    assert data["eur_to_ron_rate"] == DEFAULT_EUR_TO_RON_RATE


@pytest.mark.asyncio
async def test_get_default_vat_pct_helper(db_session):
    from services.company_commercial_settings_service import get_default_vat_pct

    pct = await get_default_vat_pct(db_session)
    assert pct == DEFAULT_VAT_PCT


@pytest.mark.asyncio
async def test_update_vat_21_ok(db_session):
    svc = CompanyCommercialSettingsService(db_session)
    data = await svc.update_default_vat_pct(21)
    assert data["default_vat_pct"] == 21.0


@pytest.mark.asyncio
async def test_update_vat_0_ok(db_session):
    svc = CompanyCommercialSettingsService(db_session)
    data = await svc.update_default_vat_pct(0)
    assert data["default_vat_pct"] == 0.0


def test_validate_vat_pct_rejects_negative():
    with pytest.raises(ValueError, match="between 0 and 100"):
        validate_vat_pct(-1)


def test_validate_vat_pct_rejects_over_100():
    with pytest.raises(ValueError, match="between 0 and 100"):
        validate_vat_pct(101)


def test_validate_vat_pct_accepts_zero():
    assert validate_vat_pct(0) == 0.0


@pytest.mark.asyncio
async def test_settings_api_get_and_put(db_fixture, db_session):
    """GET/PUT /api/v1/company-commercial-settings via isolated app."""
    from sqlalchemy import delete

    await db_session.execute(delete(CompanyCommercialSettings))
    await db_session.commit()
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from core.database import get_db
    from dependencies.auth import get_current_user
    from routers.company_commercial_settings import router as settings_router
    from schemas.auth import UserResponse

    app = FastAPI()
    app.include_router(settings_router)

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test Admin",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    with TestClient(app, raise_server_exceptions=False) as client:
        get_resp = client.get("/api/v1/company-commercial-settings")
        assert get_resp.status_code == 200
        assert get_resp.json()["default_vat_pct"] == DEFAULT_VAT_PCT
        assert get_resp.json()["eur_to_ron_rate"] == DEFAULT_EUR_TO_RON_RATE

        put_resp = client.put(
            "/api/v1/company-commercial-settings",
            json={"default_vat_pct": 0},
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["default_vat_pct"] == 0.0

        put_bad = client.put(
            "/api/v1/company-commercial-settings",
            json={"default_vat_pct": 101},
        )
        assert put_bad.status_code == 422
