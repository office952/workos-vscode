"""Scenario A — frozen VAT survives Settings default change (post-freeze)."""

from __future__ import annotations

import json

import pytest

from models.quotes import Quotes
from services.company_commercial_settings_service import (
	CompanyCommercialSettingsService,
	get_default_vat_pct,
)
from services.intake_v6_commercial_quote_service import INTAKE_V6_LINKAGE_JSON_KEY
from services.intake_v6_snapshot_authoritative_offer_service import (
	V6_OFFER_FROM_SNAPSHOT_WRITTEN,
	write_intake_v6_offer_from_frozen_snapshot_v2,
)
from services.intake_v6_snapshot_authoritative_pricing_review_service import (
	extract_v6_pricing_review_totals_authoritative,
	resolve_v6_pricing_review_authority,
)
from tests.test_intake_v6_snapshot_authoritative_offer import (
	_expected_gross_from_net,
	_insert_snapshot_with_lines,
)
from tests.test_quote_snapshot_v2_accept_gate import _seed_v6_quote

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


@pytest.mark.asyncio
async def test_scenario_a_frozen_offer_and_review_ignore_live_settings_vat(
	volumetric_v2_db,
) -> None:
	settings = CompanyCommercialSettingsService(volumetric_v2_db)
	await settings.update_default_vat_pct(21.0)

	quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=0.0)
	# Confirm notes primary frozen source is 21 at freeze-time commercial write shape.
	notes = json.loads(quote.notes or "{}")
	assert float(notes["commercial_adjustment_trace"]["vat_percent"]) == 21.0

	await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)

	expected_gross_21 = _expected_gross_from_net(1000.0, vat_pct=21.0)
	first = await write_intake_v6_offer_from_frozen_snapshot_v2(
		volumetric_v2_db,
		workspace_id,
		quote_id=quote.id,
		expected_total_gross=expected_gross_21,
		operator_confirmation=True,
		operator_identifier="vat-boundary@example.com",
	)
	assert first["status"] == V6_OFFER_FROM_SNAPSHOT_WRITTEN
	assert float(first["commercial_totals"]["vat_rate"]) == 21.0
	assert float(first["commercial_totals"]["total_gross"]) == expected_gross_21

	# Live Settings changes after freeze — must not move authoritative frozen gross.
	await settings.update_default_vat_pct(19.0)
	assert float(await get_default_vat_pct(volumetric_v2_db)) == 19.0

	refreshed = await volumetric_v2_db.get(Quotes, quote.id)
	assert refreshed is not None
	linkage = json.loads(refreshed.notes)[INTAKE_V6_LINKAGE_JSON_KEY]
	review_totals = await extract_v6_pricing_review_totals_authoritative(
		volumetric_v2_db, refreshed, linkage
	)
	assert float(review_totals["vat_percent"]) == 21.0
	assert float(review_totals["total"]) == expected_gross_21

	_, read_model = await resolve_v6_pricing_review_authority(
		volumetric_v2_db, refreshed, linkage, fail_on_drift=False
	)
	assert read_model["pre_freeze"] is False
	assert float(read_model["commercial_totals"]["vat_rate"]) == 21.0
	assert float(read_model["commercial_totals"]["total_gross"]) == expected_gross_21

	# Idempotent restamp with original expected gross still succeeds at 21%.
	second = await write_intake_v6_offer_from_frozen_snapshot_v2(
		volumetric_v2_db,
		workspace_id,
		quote_id=quote.id,
		expected_total_gross=expected_gross_21,
		operator_confirmation=True,
		operator_identifier="vat-boundary@example.com",
	)
	assert second["status"] in {
		V6_OFFER_FROM_SNAPSHOT_WRITTEN,
		"V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT",
	}
	assert float(second["commercial_totals"]["vat_rate"]) == 21.0

	# Persisted quote amounts remain freeze-time VAT (amount), notes rate remains 21.
	await volumetric_v2_db.refresh(refreshed)
	assert float(refreshed.grand_total) == expected_gross_21
	assert float(refreshed.vat) == round(1000.0 * 0.21, 2)
	notes_after = json.loads(refreshed.notes or "{}")
	assert float(notes_after["commercial_adjustment_trace"]["vat_percent"]) == 21.0

	# PRE_FREEZE: new commercial default follows live Settings (19).
	assert float(await get_default_vat_pct(volumetric_v2_db)) == 19.0


@pytest.mark.asyncio
async def test_post_freeze_fail_closed_without_frozen_vat_provenance(
	volumetric_v2_db,
) -> None:
	quote, workspace_id, _ = await _seed_v6_quote(volumetric_v2_db, grand_total=0.0)
	# Strip frozen VAT provenance deliberately.
	linkage = json.loads(quote.notes)[INTAKE_V6_LINKAGE_JSON_KEY]
	quote.notes = json.dumps({INTAKE_V6_LINKAGE_JSON_KEY: linkage})
	await volumetric_v2_db.commit()
	await volumetric_v2_db.refresh(quote)

	await _insert_snapshot_with_lines(
		volumetric_v2_db,
		quote_id=quote.id,
		workspace_id=workspace_id,
		commercial_total=1000.0,
	)

	result = await write_intake_v6_offer_from_frozen_snapshot_v2(
		volumetric_v2_db,
		workspace_id,
		quote_id=quote.id,
		expected_total_gross=_expected_gross_from_net(1000.0, vat_pct=21.0),
		operator_confirmation=True,
	)
	assert result["status"] == "V6_OFFER_FROM_SNAPSHOT_BLOCKED"
	assert result["blockers"][0]["code"] == "V6_OFFER_FROZEN_VAT_PROVENANCE_INCOMPLETE"
