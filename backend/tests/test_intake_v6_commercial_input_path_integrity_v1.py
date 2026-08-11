"""WORKOS_INTAKE_V6_COMMERCIAL_INPUT_PATH_AND_COMPLETE_OFFER_INTEGRITY_V1 matrix."""

from __future__ import annotations

import pytest

from services.company_commercial_settings_service import CompanyCommercialSettingsService
from services.intake_v6_priced_quote_dry_run_service import (
	_apply_commercial_adjustments_to_base,
	_round_money,
)
from services.intake_v6_snapshot_authoritative_offer_service import (
	commercial_totals_from_frozen_cpp,
)
from types import SimpleNamespace


def test_adjustment_order_markup_then_manual_then_discount():
	"""Historical order lock: base → markup → manual → discount → VAT."""
	out = _apply_commercial_adjustments_to_base(
		base_subtotal=1000.0,
		commercial_inputs={
			"markup_percent": 10.0,
			"discount_percent": 10.0,
			"vat_percent": 0.0,
			"manual_adjustment_ron": 50.0,
		},
		manual_adjustment_commercial=50.0,
	)
	# markup 100 → 1100; +manual 50 → 1150; discount 10% → 115; net 1035
	assert out["subtotal_net"] == 1035.0
	assert out["commercial_adjustment_trace"]["markup_value"] == 100.0
	assert out["commercial_adjustment_trace"]["discount_value"] == 115.0


def test_manual_ron_to_eur_uses_canonical_round_money():
	rate = 4.97
	ron = 100.0
	assert _round_money(ron / rate) == round(100.0 / 4.97, 2)


def test_frozen_totals_prefer_quote_columns_with_adjustment_identity():
	cpp = SimpleNamespace(
		subtotal_commercial=1000.0,
		commercial_total=1000.0,
		currency="EUR",
	)
	trace = {
		"markup_percent": 50.0,
		"markup_value": 500.0,
		"discount_percent": 0.0,
		"discount_value": 0.0,
		"manual_adjustment_ron": 0.0,
		"manual_adjustment_commercial": 0.0,
		"manual_adjustment_eur": 0.0,
		"vat_percent": 21.0,
		"currency": "EUR",
	}
	quote = SimpleNamespace(
		grand_total=1815.0,
		total_before_vat=1500.0,
		subtotal=1500.0,
		vat=315.0,
	)
	totals = commercial_totals_from_frozen_cpp(
		cpp,
		vat_rate=21.0,
		quote=quote,
		notes={"commercial_adjustment_trace": trace},
	)
	assert totals["total_gross"] == 1815.0
	assert totals["subtotal_net"] == 1500.0
	assert totals["pricing_totals_source"] == "quote_columns_frozen_priced_write"
	assert totals["commercial_adjustment_trace"]["markup_percent"] == 50.0


@pytest.mark.asyncio
async def test_matrix_manual_ron_with_configured_fx(db_session):
	await CompanyCommercialSettingsService(db_session).update_settings(eur_to_ron_rate=5.0)
	from services.intake_v6_priced_quote_dry_run_service import (
		resolve_manual_adjustment_for_commercial_currency,
	)

	amount, prov, err = await resolve_manual_adjustment_for_commercial_currency(
		db_session,
		manual_adjustment_ron=100.0,
		commercial_currency="EUR",
	)
	assert err is None
	assert amount == 20.0
	assert prov["manual_adjustment_eur"] == 20.0
	assert prov["eur_to_ron_rate"] == 5.0
	assert prov["rate_source"] == "company_commercial_settings.eur_to_ron_rate"


@pytest.mark.asyncio
async def test_matrix_manual_ron_missing_fx_errors(db_session):
	from sqlalchemy import update

	from models.company_commercial_settings import CompanyCommercialSettings
	from services.intake_v6_priced_quote_dry_run_service import (
		resolve_manual_adjustment_for_commercial_currency,
	)

	await db_session.execute(update(CompanyCommercialSettings).values(eur_to_ron_rate=None))
	await db_session.commit()
	amount, _prov, err = await resolve_manual_adjustment_for_commercial_currency(
		db_session,
		manual_adjustment_ron=25.0,
		commercial_currency="EUR",
	)
	assert amount == 0.0
	assert err == "eur_to_ron_rate_missing"
	# Restore session-seeded FX so later suite tests stay green.
	await CompanyCommercialSettingsService(db_session).update_settings(eur_to_ron_rate=5.0)
