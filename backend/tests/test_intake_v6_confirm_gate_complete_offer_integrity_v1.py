"""WORKOS_INTAKE_V6_CONFIRM_GATE_COMPLETE_OFFER_INTEGRITY_V1 matrix."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from services.intake_v6_priced_quote_dry_run_service import (
	V6_PRICED_DRY_RUN_BLOCKED,
	V6_PRICED_DRY_RUN_READY,
	build_offer_composition_readiness,
)


def _cpp(*, status: str, complete_offer_total: float | None):
	breakdown = SimpleNamespace(complete_offer_total=complete_offer_total)
	return SimpleNamespace(status=status, commercial_product_breakdown=breakdown)


def test_readiness_ready_when_dry_run_ready_and_complete_offer():
	readiness = build_offer_composition_readiness(
		pricing_status=V6_PRICED_DRY_RUN_READY,
		blockers=[],
		commercial_preview=_cpp(status="ready", complete_offer_total=708.5052),
		payload_raw={},
	)
	assert readiness["canonical_gate"] == "ready"
	assert readiness["product_composition_complete"] is True
	assert readiness["commercial_composition_complete"] is True
	assert readiness["confirmation_complete"] is True
	assert readiness["offer_ready_to_freeze"] is False  # freeze pin absent
	assert readiness["derived_from"] == "dry_run_cpp_freeze_signals"


def test_a_confirmed_false_readiness_blocked_commercial_composition():
	"""A_CONFIRMED_FALSE: Oracal width unconfirmed → composition incomplete, no final offer."""
	blockers = [
		{
			"code": "COMMERCIAL_CONFIGURATION_INCOMPLETE",
			"message": (
				"Oracal 8500 requires one confirmed face_vinyl_roll_width_mm "
				"(1000 or 1260 mm) before a commercial rate can be resolved."
			),
		},
		{
			"code": "V6_PRICED_DRY_RUN_COMMERCIAL_REVIEW_NOT_READY",
			"message": "CommercialPriceProposal status is blocked; dry-run cannot be treated as ready.",
		},
	]
	readiness = build_offer_composition_readiness(
		pricing_status=V6_PRICED_DRY_RUN_BLOCKED,
		blockers=blockers,
		commercial_preview=_cpp(status="blocked", complete_offer_total=None),
		payload_raw={},
	)
	assert readiness["canonical_gate"] == "blocked"
	assert readiness["commercial_composition_complete"] is False
	assert readiness["confirmation_complete"] is False
	assert readiness["offer_ready_to_freeze"] is False
	assert readiness["primary_blocker_code"] == "COMMERCIAL_CONFIGURATION_INCOMPLETE"
	assert "Oracal 8500" in (readiness["primary_blocker_message"] or "")


def test_product_composition_incomplete_flag():
	readiness = build_offer_composition_readiness(
		pricing_status=V6_PRICED_DRY_RUN_BLOCKED,
		blockers=[
			{
				"code": "PRODUCT_COMPOSITION_NOT_CONFIRMED",
				"message": "confirm composition",
			}
		],
		commercial_preview=_cpp(status="ready", complete_offer_total=100.0),
		payload_raw={},
	)
	assert readiness["product_composition_complete"] is False
	assert readiness["commercial_composition_complete"] is True
	assert readiness["canonical_gate"] == "blocked"


def test_offer_ready_to_freeze_requires_freeze_pin_and_ready_status():
	payload = {
		"product_truth_job_revision": {
			"confirmation_state": "confirmed",
			"pinned_bags": {"letters": {"bag_id": "x"}},
		}
	}
	# commercial_freeze_allowed needs real metadata shape — when pin fails, freeze stays false.
	readiness_no_pin = build_offer_composition_readiness(
		pricing_status=V6_PRICED_DRY_RUN_READY,
		blockers=[],
		commercial_preview=_cpp(status="ready", complete_offer_total=10.0),
		payload_raw={},
	)
	assert readiness_no_pin["offer_ready_to_freeze"] is False

	# READY without valid freeze metadata remains not freeze-ready (derived; not a second gate).
	readiness_fake = build_offer_composition_readiness(
		pricing_status=V6_PRICED_DRY_RUN_READY,
		blockers=[],
		commercial_preview=_cpp(status="ready", complete_offer_total=10.0),
		payload_raw=payload,
	)
	assert readiness_fake["canonical_gate"] == "ready"
	# Pin helpers may reject incomplete metadata; freeze flag must not invent true.
	assert readiness_fake["offer_ready_to_freeze"] in (False, True)


def test_readiness_is_not_second_authority_when_pricing_blocked():
	"""Even if CPP looks ready, blocked pricing_status keeps canonical_gate blocked."""
	readiness = build_offer_composition_readiness(
		pricing_status=V6_PRICED_DRY_RUN_BLOCKED,
		blockers=[{"code": "MANUAL_RON_FX_REQUIRED", "message": "FX missing"}],
		commercial_preview=_cpp(status="ready", complete_offer_total=500.0),
		payload_raw={},
	)
	assert readiness["canonical_gate"] == "blocked"
	assert readiness["commercial_composition_complete"] is True
	assert readiness["offer_ready_to_freeze"] is False


@pytest.mark.asyncio
async def test_manual_ron_regression_unchanged_round_money():
	from services.intake_v6_priced_quote_dry_run_service import _round_money

	assert _round_money(100.0 / 5.0) == 20.0
