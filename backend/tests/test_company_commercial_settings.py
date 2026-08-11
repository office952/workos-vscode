"""Tests for company commercial settings — VAT + fail-closed FX authority."""

from __future__ import annotations

import pytest
from sqlalchemy import delete, select, update

from models.company_commercial_settings import CompanyCommercialSettings
from services.company_commercial_settings_service import (
    EUR_TO_RON_RATE_MISSING,
    CompanyCommercialSettingsService,
    DEFAULT_EUR_TO_RON_RATE,
    DEFAULT_VAT_PCT,
    get_eur_to_ron_rate,
    require_configured_eur_to_ron_rate,
    resolve_configured_eur_to_ron_rate,
    validate_vat_pct,
)


@pytest.mark.asyncio
async def test_default_vat_pct_when_row_missing_fx_null_until_configured(db_session):
    await db_session.execute(delete(CompanyCommercialSettings))
    await db_session.commit()
    svc = CompanyCommercialSettingsService(db_session)
    data = await svc.get_settings()
    assert data["default_vat_pct"] == DEFAULT_VAT_PCT
    assert data["eur_to_ron_rate"] is None


@pytest.mark.asyncio
async def test_get_settings_does_not_persist_fx_on_read(db_session):
    await db_session.execute(delete(CompanyCommercialSettings))
    await db_session.commit()
    svc = CompanyCommercialSettingsService(db_session)
    await svc.get_settings()
    await svc.get_settings()
    row = (await db_session.execute(select(CompanyCommercialSettings))).scalars().first()
    assert row is not None
    assert row.eur_to_ron_rate is None


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
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from core.database import get_db
    from dependencies.auth import get_current_user
    from routers.company_commercial_settings import router as settings_router
    from schemas.auth import UserResponse

    # Session seed may have been mutated by prior tests; reset then clear FX for null proof.
    await db_session.execute(
        update(CompanyCommercialSettings).values(
            default_vat_pct=DEFAULT_VAT_PCT,
            eur_to_ron_rate=None,
        )
    )
    await db_session.commit()

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
        body = get_resp.json()
        assert body["default_vat_pct"] == DEFAULT_VAT_PCT
        assert body["eur_to_ron_rate"] is None

        put_resp = client.put(
            "/api/v1/company-commercial-settings",
            json={"default_vat_pct": 0, "eur_to_ron_rate": 4.97},
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["default_vat_pct"] == 0.0
        assert put_resp.json()["eur_to_ron_rate"] == pytest.approx(4.97)

        put_bad = client.put(
            "/api/v1/company-commercial-settings",
            json={"default_vat_pct": 101},
        )
        assert put_bad.status_code == 422


@pytest.mark.asyncio
async def test_matrix_a_settings_persistence_4_97(db_session):
    svc = CompanyCommercialSettingsService(db_session)
    await svc.update_settings(eur_to_ron_rate=4.97)
    data = await svc.get_settings()
    assert data["eur_to_ron_rate"] == pytest.approx(4.97)
    rate = await require_configured_eur_to_ron_rate(db_session)
    assert rate == pytest.approx(4.97)


@pytest.mark.asyncio
async def test_matrix_b_missing_fx_fail_closed_no_write(db_session):
    await db_session.execute(
        update(CompanyCommercialSettings).values(eur_to_ron_rate=None)
    )
    await db_session.commit()
    rate, err = await resolve_configured_eur_to_ron_rate(db_session)
    assert rate is None
    assert err == EUR_TO_RON_RATE_MISSING
    with pytest.raises(ValueError, match=EUR_TO_RON_RATE_MISSING):
        await require_configured_eur_to_ron_rate(db_session)
    with pytest.raises(ValueError, match=EUR_TO_RON_RATE_MISSING):
        await get_eur_to_ron_rate(db_session)
    row = (await db_session.execute(select(CompanyCommercialSettings))).scalars().first()
    assert row is not None
    assert row.eur_to_ron_rate is None


@pytest.mark.asyncio
async def test_matrix_c_no_row_money_read_does_not_persist_fx(db_session):
    await db_session.execute(delete(CompanyCommercialSettings))
    await db_session.commit()
    rate, err = await resolve_configured_eur_to_ron_rate(db_session)
    assert rate is None
    assert err is not None
    # Editor get_or_create may create a row with NULL FX — never 5.0.
    data = await CompanyCommercialSettingsService(db_session).get_settings()
    assert data["eur_to_ron_rate"] is None
    row = (await db_session.execute(select(CompanyCommercialSettings))).scalars().first()
    assert row is not None
    assert row.eur_to_ron_rate is None
    assert DEFAULT_EUR_TO_RON_RATE == 5.0  # placeholder constant only
