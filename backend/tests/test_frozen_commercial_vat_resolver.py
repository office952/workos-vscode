"""Unit tests — frozen commercial VAT resolver (post-freeze)."""

from __future__ import annotations

import pytest

from schemas.commercial_price_proposal import (
	CommercialPriceProposalPreview,
	CommercialProductBreakdown,
)
from services.frozen_commercial_vat_resolver import (
	FROZEN_VAT_PROVENANCE_INCOMPLETE,
	PROVENANCE_CPP_BREAKDOWN,
	PROVENANCE_NOTES_PRICED_WRITE,
	PROVENANCE_NOTES_TRACE,
	FrozenVatMissingError,
	resolve_frozen_commercial_vat_rate,
	stamp_commercial_adjustment_trace_vat,
	stamp_cpp_supplementary_vat_rate,
)


def test_notes_primary_wins_over_cpp() -> None:
	cpp = CommercialPriceProposalPreview(
		template_code="TPL",
		commercial_product_breakdown=CommercialProductBreakdown(vat_rate_percent=19.0),
	)
	resolved = resolve_frozen_commercial_vat_rate(
		notes={"commercial_adjustment_trace": {"vat_percent": 21.0}},
		cpp=cpp,
	)
	assert resolved.vat_rate == 21.0
	assert resolved.provenance == PROVENANCE_NOTES_TRACE


def test_nested_priced_write_trace_fallback() -> None:
	notes = {
		"intake_v6_linkage_v1": {
			"intake_v6_priced_quote_write_v1": {
				"commercial_adjustment_trace": {"vat_percent": 19.0},
			}
		}
	}
	resolved = resolve_frozen_commercial_vat_rate(notes=notes, cpp=None)
	assert resolved.vat_rate == 19.0
	assert resolved.provenance == PROVENANCE_NOTES_PRICED_WRITE


def test_cpp_supplementary_when_notes_missing() -> None:
	cpp = CommercialPriceProposalPreview(
		template_code="TPL",
		commercial_product_breakdown=CommercialProductBreakdown(vat_rate_percent=21.0),
	)
	resolved = resolve_frozen_commercial_vat_rate(notes={}, cpp=cpp)
	assert resolved.vat_rate == 21.0
	assert resolved.provenance == PROVENANCE_CPP_BREAKDOWN


def test_fail_closed_when_missing() -> None:
	with pytest.raises(FrozenVatMissingError) as exc:
		resolve_frozen_commercial_vat_rate(notes={}, cpp=None)
	assert exc.value.code == FROZEN_VAT_PROVENANCE_INCOMPLETE


def test_does_not_guess_from_quote_vat_amount_field() -> None:
	# quote.vat amount must never be treated as % — not present on notes path as rate.
	with pytest.raises(FrozenVatMissingError):
		resolve_frozen_commercial_vat_rate(
			notes={"vat": 210.0, "total_before_vat": 1000.0},
			cpp=None,
		)


def test_stamp_notes_preserves_existing_trace_keys() -> None:
	notes = stamp_commercial_adjustment_trace_vat(
		{"commercial_adjustment_trace": {"markup_percent": 10.0}},
		vat_percent=21.0,
		currency="RON",
	)
	assert notes["commercial_adjustment_trace"]["markup_percent"] == 10.0
	assert notes["commercial_adjustment_trace"]["vat_percent"] == 21.0
	assert notes["commercial_adjustment_trace"]["currency"] == "RON"


def test_stamp_cpp_supplementary() -> None:
	cpp = CommercialPriceProposalPreview(template_code="TPL", commercial_total=100.0)
	stamped = stamp_cpp_supplementary_vat_rate(cpp, vat_percent=21.0)
	assert stamped.commercial_product_breakdown is not None
	assert stamped.commercial_product_breakdown.vat_rate_percent == 21.0
	assert (
		stamped.commercial_product_breakdown.vat_policy_source
		== "company_commercial_settings.default_vat_pct"
	)
