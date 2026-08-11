"""WORKOS_FX_COMMERCIAL_AUTHORITY_CLOSURE_V1 — matrix D/E/F/G (+ profitability freeze)."""

from __future__ import annotations

import pytest
from sqlalchemy import update

from models.company_commercial_settings import CompanyCommercialSettings
from models.orders import Orders
from schemas.order_snapshot_v2 import OrderSnapshotV2
from services.company_commercial_settings_service import (
    EUR_TO_RON_RATE_MISSING,
    CompanyCommercialSettingsService,
    require_configured_eur_to_ron_rate,
)
from services.intake_v6_quote_to_order_service import convert_v6_quote_to_order
from services.linked_logo_commercial_price_service import _canonical_eur_to_ron_rate
from services.order_currency_conversion_service import convert_quote_totals_to_order_base
from tests.test_order_snapshot_v2_convert import _accept_v2_quote, _valid_convert_body
from tests.test_quote_snapshot_v2_accept_gate import _seed_v6_quote, _test_user

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


@pytest.fixture(autouse=True)
def no_workspace_critical_blockers(monkeypatch):
    async def _empty(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "services.intake_v6_quote_to_order_service._collect_accept_critical_blockers",
        _empty,
    )


@pytest.mark.asyncio
async def test_matrix_d_quote_to_order_uses_configured_4_97(volumetric_v2_db):
    await CompanyCommercialSettingsService(volumetric_v2_db).update_settings(
        eur_to_ron_rate=4.97
    )
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)
    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )
    order = await volumetric_v2_db.get(Orders, result["order_id"])
    payload = OrderSnapshotV2.model_validate_json(order.snapshot_v2_json)
    assert payload.profitability_fx_v1 is not None
    assert payload.profitability_fx_v1.eur_to_ron_rate == pytest.approx(4.97)
    assert payload.profitability_fx_v1.rate_source == (
        "company_commercial_settings.eur_to_ron_rate"
    )


@pytest.mark.asyncio
async def test_matrix_d_quote_to_order_missing_fx_blocked(volumetric_v2_db):
    await volumetric_v2_db.execute(
        update(CompanyCommercialSettings).values(eur_to_ron_rate=None)
    )
    await volumetric_v2_db.commit()
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await convert_v6_quote_to_order(
            volumetric_v2_db,
            accepted.id,
            _valid_convert_body(),
            _test_user(),
        )
    detail = exc.value.detail
    blob = detail if isinstance(detail, str) else str(detail)
    assert (
        "eur_to_ron_rate_missing" in blob
        or EUR_TO_RON_RATE_MISSING in blob
        or "PROFITABILITY_FX_RATE_MISSING" in blob
    )


@pytest.mark.asyncio
async def test_matrix_e_profitability_fx_frozen_after_settings_change(volumetric_v2_db):
    await CompanyCommercialSettingsService(volumetric_v2_db).update_settings(
        eur_to_ron_rate=4.97
    )
    quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db)
    accepted = await _accept_v2_quote(volumetric_v2_db, quote, workspace_id)
    result = await convert_v6_quote_to_order(
        volumetric_v2_db,
        accepted.id,
        _valid_convert_body(),
        _test_user(),
    )
    order = await volumetric_v2_db.get(Orders, result["order_id"])
    payload = OrderSnapshotV2.model_validate_json(order.snapshot_v2_json)
    frozen = payload.profitability_fx_v1.eur_to_ron_rate
    assert frozen == pytest.approx(4.97)

    await CompanyCommercialSettingsService(volumetric_v2_db).update_eur_to_ron_rate(5.10)
    order_reload = await volumetric_v2_db.get(Orders, result["order_id"])
    payload2 = OrderSnapshotV2.model_validate_json(order_reload.snapshot_v2_json)
    assert payload2.profitability_fx_v1.eur_to_ron_rate == pytest.approx(4.97)


@pytest.mark.asyncio
async def test_matrix_f_logo_cpp_fail_closed_and_configured(volumetric_v2_db):
    await volumetric_v2_db.execute(
        update(CompanyCommercialSettings).values(eur_to_ron_rate=None)
    )
    await volumetric_v2_db.commit()
    rate, err = await _canonical_eur_to_ron_rate(volumetric_v2_db)
    assert rate is None
    assert err in ("eur_to_ron_rate_unset", EUR_TO_RON_RATE_MISSING)

    await CompanyCommercialSettingsService(volumetric_v2_db).update_settings(
        eur_to_ron_rate=4.97
    )
    rate2, err2 = await _canonical_eur_to_ron_rate(volumetric_v2_db)
    assert err2 is None
    assert rate2 == pytest.approx(4.97)
    assert await require_configured_eur_to_ron_rate(volumetric_v2_db) == pytest.approx(4.97)


@pytest.mark.asyncio
async def test_matrix_conversion_math_still_requires_explicit_rate():
    with pytest.raises(ValueError, match="eur_to_ron_rate_missing"):
        convert_quote_totals_to_order_base(
            gross_amount=119.0,
            net_amount=100.0,
            source_currency="EUR",
            eur_to_ron_rate=None,
        )
