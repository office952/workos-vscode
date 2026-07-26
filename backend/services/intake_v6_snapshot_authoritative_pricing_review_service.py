"""Intake V6 snapshot-authoritative pricing review read model (W4-T01B).

Post-freeze pricing review must consume frozen QuoteSnapshotV2 commercial truth.
Quote columns are projection validation only — never independent authority.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from models.quotes import Quotes
from schemas.quote_snapshot_v2 import QuoteSnapshotV2
from services.company_commercial_settings_service import get_default_vat_pct
from services.intake_v4_quote_linkage_utils import linkage_workspace_id
from services.intake_v4_quote_to_order_service import (
	ALLOWED_CURRENCIES,
	TOTAL_TOLERANCE,
	_raise_blocked,
	_extract_commercial_totals_from_quote,
)
from services.intake_v6_snapshot_authoritative_offer_service import (
	INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY,
	V6_SNAPSHOT_OFFER_PRICING_SOURCE,
	_existing_snapshot_offer_stamp,
	commercial_totals_from_frozen_cpp,
	resolve_frozen_quote_snapshot_v2_record,
)

V6_PRICING_REVIEW_PRE_FREEZE_SOURCE = "pre_freeze_quote_projection"

SNAPSHOT_QUOTE_TOTAL_DRIFT = "SNAPSHOT_QUOTE_TOTAL_DRIFT"
SNAPSHOT_HASH_MISMATCH = "SNAPSHOT_HASH_MISMATCH"
SNAPSHOT_LINKAGE_MISMATCH = "SNAPSHOT_LINKAGE_MISMATCH"
FROZEN_SNAPSHOT_NOT_FOUND = "FROZEN_SNAPSHOT_NOT_FOUND"
POST_FREEZE_REVIEW_NOT_SNAPSHOT_AUTHORITATIVE = "POST_FREEZE_REVIEW_NOT_SNAPSHOT_AUTHORITATIVE"

V6_PRICING_REVIEW_COLUMN_POLICY = "SNAPSHOT_READ_DIRECT_COLUMNS_VALIDATION_ONLY"
V6_PRICING_REVIEW_PRE_FREEZE_POLICY = "PRE_FREEZE_REVIEW_ALLOWED_NOT_ACCEPTABLE"


def _money(value: Any) -> float:
	return round(float(value), 2)


def _quote_projection_totals(quote: Quotes) -> dict[str, Any] | None:
	grand_total = float(quote.grand_total or 0)
	if grand_total <= 0:
		return None
	net = float(quote.total_before_vat or quote.subtotal or 0)
	vat_amount = _money(grand_total - net) if net > 0 else 0.0
	return {
		"subtotal": _money(quote.subtotal or net),
		"discount_amount": _money(quote.discount or 0),
		"vat_percent": _money(quote.vat or 0),
		"vat_amount": vat_amount,
		"total": _money(grand_total),
		"net_before_vat": _money(net),
		"currency": "RON",
		"pricing_totals_source": "quote_columns",
	}


def _totals_from_frozen_snapshot_record(
	record: QuoteSnapshotV2Record,
	parsed: QuoteSnapshotV2,
	*,
	vat_rate: float,
) -> dict[str, Any]:
	cpp = parsed.commercial_price_proposal_snapshot
	if cpp is None:
		_raise_blocked(
			"SNAPSHOT_COMMERCIAL_MISSING",
			"Quote Snapshot V2 commercial proposal missing.",
			["commercial_snapshot_missing"],
		)
	commercial_total = cpp.commercial_total
	if commercial_total is None or float(commercial_total) <= 0:
		_raise_blocked(
			"QUOTE_NOT_PRICED",
			"Quote Snapshot V2 has no commercial total for pricing review.",
			["QUOTE_NOT_PRICED"],
		)
	frozen_totals = commercial_totals_from_frozen_cpp(cpp, vat_rate=vat_rate)
	currency = str(frozen_totals.get("currency") or "RON").strip().upper()
	if currency not in ALLOWED_CURRENCIES:
		currency = "RON"
	return {
		"subtotal": _money(frozen_totals["subtotal_net"]),
		"discount_amount": 0.0,
		"vat_percent": _money(frozen_totals["vat_rate"]),
		"vat_amount": _money(frozen_totals["vat_amount"]),
		"total": _money(frozen_totals["total_gross"]),
		"net_before_vat": _money(frozen_totals["subtotal_net"]),
		"currency": currency,
		"pricing_totals_source": V6_SNAPSHOT_OFFER_PRICING_SOURCE,
		"pricing_totals_captured": True,
		"snapshot_v2_id": record.id,
		"snapshot_code": record.snapshot_code,
		"content_hash": record.content_hash,
		"readiness": record.readiness,
	}


def _validate_offer_stamp_linkage(
	record: QuoteSnapshotV2Record,
	linkage: dict[str, Any],
	*,
	workspace_id: str | None,
) -> dict[str, Any] | None:
	stamp = _existing_snapshot_offer_stamp(linkage)
	if stamp is None:
		return None
	if stamp.get("snapshot_id") is not None and int(stamp["snapshot_id"]) != int(record.id):
		_raise_blocked(
			SNAPSHOT_LINKAGE_MISMATCH,
			"Offer stamp snapshot_id does not match frozen Quote Snapshot V2.",
			[SNAPSHOT_LINKAGE_MISMATCH],
		)
	if stamp.get("content_hash") and record.content_hash and stamp["content_hash"] != record.content_hash:
		_raise_blocked(
			SNAPSHOT_HASH_MISMATCH,
			"Offer stamp content_hash does not match frozen Quote Snapshot V2.",
			[SNAPSHOT_HASH_MISMATCH],
		)
	if workspace_id and stamp.get("workspace_id") and str(stamp["workspace_id"]) != str(workspace_id):
		_raise_blocked(
			SNAPSHOT_LINKAGE_MISMATCH,
			"Offer stamp workspace_id does not match quote linkage.",
			[SNAPSHOT_LINKAGE_MISMATCH],
		)
	if stamp.get("quote_id") is not None and int(stamp["quote_id"]) != int(record.quote_id):
		_raise_blocked(
			SNAPSHOT_LINKAGE_MISMATCH,
			"Offer stamp quote_id does not match quote.",
			[SNAPSHOT_LINKAGE_MISMATCH],
		)
	return stamp


def _detect_column_drift(
	quote_projection: dict[str, Any] | None,
	snapshot_totals: dict[str, Any],
) -> list[str]:
	if quote_projection is None:
		return []
	findings: list[str] = []
	if abs(float(quote_projection["total"]) - float(snapshot_totals["total"])) > TOTAL_TOLERANCE:
		findings.append(SNAPSHOT_QUOTE_TOTAL_DRIFT)
	if abs(float(quote_projection["net_before_vat"]) - float(snapshot_totals["net_before_vat"])) > TOTAL_TOLERANCE:
		findings.append(SNAPSHOT_QUOTE_TOTAL_DRIFT)
	if abs(float(quote_projection["vat_amount"]) - float(snapshot_totals["vat_amount"])) > TOTAL_TOLERANCE:
		findings.append(SNAPSHOT_QUOTE_TOTAL_DRIFT)
	quote_currency = str(quote_projection.get("currency") or "").strip().upper()
	snapshot_currency = str(snapshot_totals.get("currency") or "").strip().upper()
	if quote_currency and snapshot_currency and quote_currency != snapshot_currency:
		findings.append(SNAPSHOT_QUOTE_TOTAL_DRIFT)
	return sorted(set(findings))


def _internal_cost_review_projection(parsed: QuoteSnapshotV2) -> dict[str, Any]:
	eic = parsed.estimated_internal_cost_snapshot
	if eic is None:
		return {
			"available": False,
			"status": "missing",
			"visibility": "restricted",
			"execution_blocked": True,
		}
	status = str(eic.status or "unknown")
	return {
		"available": True,
		"status": status,
		"estimated_total_internal_cost": eic.estimated_total_internal_cost,
		"currency": eic.currency,
		"visibility": "restricted",
		"execution_blocked": status in {"blocked", "partial"},
		"offer_and_order_allowed": True,
	}


def build_pricing_review_read_model(
	*,
	snapshot_totals: dict[str, Any],
	record: QuoteSnapshotV2Record,
	parsed: QuoteSnapshotV2,
	offer_stamp: dict[str, Any] | None,
	column_drift: list[str],
	pre_freeze: bool,
) -> dict[str, Any]:
	return {
		"authority_source": (
			V6_PRICING_REVIEW_PRE_FREEZE_SOURCE if pre_freeze else V6_SNAPSHOT_OFFER_PRICING_SOURCE
		),
		"pre_freeze": pre_freeze,
		"column_policy": V6_PRICING_REVIEW_COLUMN_POLICY,
		"pre_freeze_policy": V6_PRICING_REVIEW_PRE_FREEZE_POLICY if pre_freeze else None,
		"commercial_totals": {
			"subtotal_net": snapshot_totals["net_before_vat"],
			"vat_amount": snapshot_totals["vat_amount"],
			"vat_rate": snapshot_totals["vat_percent"],
			"total_gross": snapshot_totals["total"],
			"currency": snapshot_totals["currency"],
			"pricing_totals_source": snapshot_totals["pricing_totals_source"],
		},
		"snapshot_v2": {
			"snapshot_id": record.id,
			"snapshot_code": record.snapshot_code,
			"content_hash": record.content_hash,
			"readiness": record.readiness,
			"status": record.status,
		},
		"offer_stamp_present": offer_stamp is not None,
		"column_drift": column_drift,
		"column_drift_blocked": len(column_drift) > 0,
		"internal_cost": _internal_cost_review_projection(parsed),
		"owner_decision_codes": [d.code for d in parsed.owner_decisions_snapshot],
		"live_dry_run_used": False,
	}


async def resolve_v6_pricing_review_authority(
	db: AsyncSession,
	quote: Quotes,
	linkage: dict[str, Any],
	*,
	fail_on_drift: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
	"""Resolve pricing-review totals and read model from frozen snapshot when present."""
	workspace_id = linkage_workspace_id(linkage)
	record = await resolve_frozen_quote_snapshot_v2_record(
		db,
		quote_id=quote.id,
		workspace_id=workspace_id,
	)
	if record is None:
		if float(quote.grand_total or 0) > 0:
			totals = _extract_commercial_totals_from_quote(quote)
			totals["pricing_totals_source"] = V6_PRICING_REVIEW_PRE_FREEZE_SOURCE
			read_model = {
				"authority_source": V6_PRICING_REVIEW_PRE_FREEZE_SOURCE,
				"pre_freeze": True,
				"column_policy": V6_PRICING_REVIEW_COLUMN_POLICY,
				"pre_freeze_policy": V6_PRICING_REVIEW_PRE_FREEZE_POLICY,
				"commercial_totals": {
					"subtotal_net": totals["net_before_vat"],
					"vat_amount": totals["vat_amount"],
					"vat_rate": totals["vat_percent"],
					"total_gross": totals["total"],
					"currency": totals["currency"],
					"pricing_totals_source": V6_PRICING_REVIEW_PRE_FREEZE_SOURCE,
				},
				"snapshot_v2": {"exists": False},
				"offer_stamp_present": False,
				"column_drift": [],
				"column_drift_blocked": False,
				"internal_cost": {"available": False, "visibility": "restricted"},
				"owner_decision_codes": [],
				"live_dry_run_used": False,
			}
			return totals, read_model
		_raise_blocked(
			FROZEN_SNAPSHOT_NOT_FOUND,
			(
				"Quote has no commercial totals — write the official V6 backend totals on the quote "
				"or freeze a Quote Snapshot V2 with commercial total before completing pricing review."
			),
			[FROZEN_SNAPSHOT_NOT_FOUND],
		)

	try:
		parsed = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
	except Exception as exc:
		_raise_blocked(
			"SNAPSHOT_V2_INVALID",
			f"Quote Snapshot V2 JSON invalid: {exc}",
			["snapshot_v2_invalid"],
		)

	offer_stamp = _validate_offer_stamp_linkage(record, linkage, workspace_id=workspace_id)
	vat_rate = await get_default_vat_pct(db)
	snapshot_totals = _totals_from_frozen_snapshot_record(record, parsed, vat_rate=vat_rate)
	quote_projection = _quote_projection_totals(quote)
	column_drift = _detect_column_drift(quote_projection, snapshot_totals)

	if fail_on_drift and column_drift:
		_raise_blocked(
			SNAPSHOT_QUOTE_TOTAL_DRIFT,
			"Quote column projection drifts from frozen Quote Snapshot V2 commercial truth.",
			column_drift,
		)

	read_model = build_pricing_review_read_model(
		snapshot_totals=snapshot_totals,
		record=record,
		parsed=parsed,
		offer_stamp=offer_stamp,
		column_drift=column_drift,
		pre_freeze=False,
	)
	return snapshot_totals, read_model


async def extract_v6_pricing_review_totals_authoritative(
	db: AsyncSession,
	quote: Quotes,
	linkage: dict[str, Any],
) -> dict[str, Any]:
	"""Authoritative totals for complete_v6_pricing_review — blocks on column drift post-freeze."""
	totals, _read_model = await resolve_v6_pricing_review_authority(
		db,
		quote,
		linkage,
		fail_on_drift=True,
	)
	return totals


async def build_v6_pricing_review_spine_projection(
	db: AsyncSession,
	quote: Quotes,
	linkage: dict[str, Any],
) -> dict[str, Any]:
	"""Read-only pricing-review projection for commercial spine GET — does not block on drift."""
	_totals, read_model = await resolve_v6_pricing_review_authority(
		db,
		quote,
		linkage,
		fail_on_drift=False,
	)
	return read_model
