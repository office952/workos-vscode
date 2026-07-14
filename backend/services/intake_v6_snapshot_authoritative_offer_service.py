"""Intake V6 snapshot-authoritative Offer consumer (W4-T01).

When a frozen QuoteSnapshotV2 exists, Offer-facing quote state must be projected
from the snapshot — never from live dry-run repricing.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.commercial_price_proposal import CommercialPriceLine
from schemas.quote_snapshot_v2 import QuoteSnapshotV2
from services.company_commercial_settings_service import get_default_vat_pct
from services.intake_v6_commercial_quote_service import INTAKE_V6_LINKAGE_JSON_KEY, intake_v6_linkage_code
from services.intake_v6_priced_quote_dry_run_service import _official_totals_from_7g
from services.quote_snapshot_v2_service import FREEZE_ALLOWED_READINESS, HARD_BLOCKED_READINESS
from services.quotes import QuotesService

V6_OFFER_FROM_SNAPSHOT_WRITTEN = "V6_OFFER_FROM_SNAPSHOT_WRITTEN"
V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT = "V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT"
V6_OFFER_FROM_SNAPSHOT_BLOCKED = "V6_OFFER_FROM_SNAPSHOT_BLOCKED"

V6_OFFER_SNAPSHOT_NOT_FOUND = "V6_OFFER_SNAPSHOT_NOT_FOUND"
V6_OFFER_SNAPSHOT_READINESS_BLOCKED = "V6_OFFER_SNAPSHOT_READINESS_BLOCKED"
V6_OFFER_SNAPSHOT_COMMERCIAL_BLOCKED = "V6_OFFER_SNAPSHOT_COMMERCIAL_BLOCKED"
V6_OFFER_SNAPSHOT_QUOTE_MISMATCH = "V6_OFFER_SNAPSHOT_QUOTE_MISMATCH"
V6_OFFER_SNAPSHOT_WORKSPACE_MISMATCH = "V6_OFFER_SNAPSHOT_WORKSPACE_MISMATCH"
V6_OFFER_SNAPSHOT_EXPECTED_TOTAL_MISMATCH = "V6_OFFER_SNAPSHOT_EXPECTED_TOTAL_MISMATCH"
V6_OFFER_SNAPSHOT_OPERATOR_CONFIRMATION_REQUIRED = "V6_OFFER_SNAPSHOT_OPERATOR_CONFIRMATION_REQUIRED"
V6_OFFER_SNAPSHOT_HASH_MISMATCH = "V6_OFFER_SNAPSHOT_HASH_MISMATCH"
V6_OFFER_SNAPSHOT_LINE_ITEMS_MISSING = "V6_OFFER_SNAPSHOT_LINE_ITEMS_MISSING"

INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY = "intake_v6_snapshot_authoritative_offer_v1"
V6_SNAPSHOT_OFFER_PRICING_SOURCE = "quote_snapshot_v2"

_TERMINAL_OR_CONVERTED_STATUSES = frozenset({"accepted", "rejected", "expired", "converted", "ordered"})


def _parse_notes_preserving_raw(raw_notes: str | None) -> tuple[dict[str, Any], str | None, bool]:
	if not raw_notes:
		return {}, None, False
	try:
		parsed = json.loads(raw_notes)
	except json.JSONDecodeError:
		return {"legacy_notes_raw": raw_notes}, raw_notes, True
	if isinstance(parsed, dict):
		return parsed, None, False
	return {"legacy_notes_raw": raw_notes}, raw_notes, True


def _existing_v6_linkage(notes_payload: dict[str, Any]) -> dict[str, Any] | None:
	linkage = notes_payload.get(INTAKE_V6_LINKAGE_JSON_KEY)
	return linkage if isinstance(linkage, dict) else None


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _blocked(
	*,
	quote_id: int | None,
	quote_code: str | None = None,
	commercial_totals: dict[str, Any] | None = None,
	line_items: list[dict[str, Any]] | None = None,
	blockers: list[dict[str, str]],
	warnings: list[str] | None = None,
	snapshot_v2: dict[str, Any] | None = None,
) -> dict[str, Any]:
	return {
		"status": V6_OFFER_FROM_SNAPSHOT_BLOCKED,
		"quote_id": quote_id,
		"quote_code": quote_code,
		"commercial_totals": commercial_totals,
		"line_items": line_items or [],
		"blockers": blockers,
		"warnings": warnings or [],
		"can_create_quote_snapshot": False,
		"can_accept_quote": False,
		"quote_snapshot_created": False,
		"order_created": False,
		"commercial_authority_source": V6_SNAPSHOT_OFFER_PRICING_SOURCE,
		"snapshot_v2": snapshot_v2,
		"pricing_trace": {
			"pricing_source": V6_SNAPSHOT_OFFER_PRICING_SOURCE,
			"live_dry_run_used": False,
		},
	}


def _money(value: Any) -> float:
	return round(float(value), 2)


def _as_positive_number(value: Any) -> float | None:
	try:
		number = float(value)
	except (TypeError, ValueError):
		return None
	return number if number > 0 else None


def _snapshot_v2_meta(record: QuoteSnapshotV2Record) -> dict[str, Any]:
	return {
		"snapshot_id": record.id,
		"snapshot_code": record.snapshot_code,
		"content_hash": record.content_hash,
		"readiness": record.readiness,
		"status": record.status,
		"quote_id": record.quote_id,
		"workspace_id": record.workspace_id,
	}


async def resolve_frozen_quote_snapshot_v2_record(
	db: AsyncSession,
	*,
	quote_id: int,
	workspace_id: str | None = None,
) -> QuoteSnapshotV2Record | None:
	query = (
		select(QuoteSnapshotV2Record)
		.where(
			QuoteSnapshotV2Record.quote_id == quote_id,
			QuoteSnapshotV2Record.status == "frozen",
		)
		.order_by(QuoteSnapshotV2Record.version.desc())
		.limit(1)
	)
	result = await db.execute(query)
	record = result.scalar_one_or_none()
	if record is not None:
		return record
	if not workspace_id:
		return None
	ws_query = (
		select(QuoteSnapshotV2Record)
		.where(
			QuoteSnapshotV2Record.workspace_id == workspace_id,
			QuoteSnapshotV2Record.status == "frozen",
		)
		.order_by(QuoteSnapshotV2Record.version.desc())
		.limit(1)
	)
	ws_result = await db.execute(ws_query)
	return ws_result.scalar_one_or_none()


async def has_frozen_quote_snapshot_v2(
	db: AsyncSession,
	*,
	quote_id: int,
	workspace_id: str | None = None,
) -> bool:
	record = await resolve_frozen_quote_snapshot_v2_record(
		db,
		quote_id=quote_id,
		workspace_id=workspace_id,
	)
	return record is not None


def _existing_snapshot_offer_stamp(linkage: dict[str, Any] | None) -> dict[str, Any] | None:
	if not isinstance(linkage, dict):
		return None
	stamp = linkage.get(INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY)
	return stamp if isinstance(stamp, dict) else None


def cpp_line_to_quote_line(line: CommercialPriceLine) -> dict[str, Any]:
	unit_price = _money(line.commercial_unit_price or 0)
	total = _money(line.subtotal or 0)
	return {
		"description": line.label or line.code,
		"name": line.label or line.code,
		"quantity": line.quantity,
		"unit": line.unit,
		"unit_price": unit_price,
		"total": total,
		"source_component": line.component_code or line.module_code,
		"module_code": line.module_code,
		"component_code": line.component_code,
		"pricing_rule_code": line.pricing_rule_code,
		"pricing_source": V6_SNAPSHOT_OFFER_PRICING_SOURCE,
		"client_visible": True,
		"warnings": list(line.warnings or []),
	}


def map_cpp_lines_to_quote_items(lines: list[CommercialPriceLine]) -> list[dict[str, Any]]:
	mapped = [cpp_line_to_quote_line(line) for line in lines]
	return [line for line in mapped if _as_positive_number(line.get("total")) is not None]


def commercial_totals_from_frozen_cpp(
	cpp: Any,
	*,
	vat_rate: float,
) -> dict[str, Any]:
	subtotal = cpp.subtotal_commercial if cpp.subtotal_commercial is not None else cpp.commercial_total
	if subtotal is None:
		raise ValueError("Frozen commercial subtotal missing from snapshot.")
	totals = _official_totals_from_7g(subtotal=float(subtotal), vat_rate=float(vat_rate))
	totals["currency"] = str(cpp.currency or "RON").strip().upper()
	totals["pricing_totals_source"] = V6_SNAPSHOT_OFFER_PRICING_SOURCE
	return totals


def _internal_cost_reference(parsed: QuoteSnapshotV2) -> dict[str, Any]:
	eic = parsed.estimated_internal_cost_snapshot
	if eic is None:
		return {"available": False, "visibility": "restricted"}
	return {
		"available": True,
		"status": eic.status,
		"estimated_total_internal_cost": eic.estimated_total_internal_cost,
		"currency": eic.currency,
		"owner_decision_codes": [d.code for d in parsed.owner_decisions_snapshot],
		"visibility": "restricted",
	}


def _build_snapshot_offer_stamp(
	record: QuoteSnapshotV2Record,
	parsed: QuoteSnapshotV2,
	*,
	workspace_id: str,
	operator_identifier: str | None,
	totals: dict[str, Any],
) -> dict[str, Any]:
	now = datetime.now(timezone.utc).isoformat()
	eic = parsed.estimated_internal_cost_snapshot
	return {
		"snapshot_id": record.id,
		"snapshot_code": record.snapshot_code,
		"content_hash": record.content_hash,
		"readiness": record.readiness,
		"workspace_id": workspace_id,
		"quote_id": record.quote_id,
		"stamped_at": now,
		"stamped_by": operator_identifier,
		"pricing_source": V6_SNAPSHOT_OFFER_PRICING_SOURCE,
		"commercial_authority": "commercial_price_proposal_7g",
		"internal_cost_status": eic.status if eic is not None else None,
		"owner_decision_codes": [d.code for d in parsed.owner_decisions_snapshot],
		"written_total_gross": totals.get("total_gross"),
		"written_subtotal_net": totals.get("subtotal_net"),
		"live_dry_run_used": False,
		"no_reprice_policy": True,
	}


def _success_response(
	*,
	status: str,
	quote_id: int,
	quote_code: str | None,
	totals: dict[str, Any],
	line_items: list[dict[str, Any]],
	record: QuoteSnapshotV2Record,
	parsed: QuoteSnapshotV2,
	warnings: list[str],
) -> dict[str, Any]:
	return {
		"status": status,
		"quote_id": quote_id,
		"quote_code": quote_code,
		"commercial_totals": {
			"subtotal_net": totals.get("subtotal_net"),
			"discount": 0.0,
			"total_before_vat": totals.get("subtotal_net"),
			"vat": totals.get("vat_amount"),
			"vat_rate": totals.get("vat_rate"),
			"total_gross": totals.get("total_gross"),
			"currency": totals.get("currency") or "RON",
			"pricing_totals_source": V6_SNAPSHOT_OFFER_PRICING_SOURCE,
		},
		"line_items": line_items,
		"pricing_trace": {
			"pricing_source": V6_SNAPSHOT_OFFER_PRICING_SOURCE,
			"snapshot_id": record.id,
			"snapshot_code": record.snapshot_code,
			"content_hash": record.content_hash,
			"live_dry_run_used": False,
			"no_reprice_policy": True,
		},
		"blockers": [],
		"warnings": warnings,
		"can_create_quote_snapshot": False,
		"can_accept_quote": record.readiness in FREEZE_ALLOWED_READINESS,
		"quote_snapshot_created": True,
		"order_created": False,
		"commercial_authority_source": V6_SNAPSHOT_OFFER_PRICING_SOURCE,
		"snapshot_v2": _snapshot_v2_meta(record),
		"internal_cost_reference": _internal_cost_reference(parsed),
		"owner_decisions_snapshot": [
			{"code": d.code, "label": d.label, "source": d.source}
			for d in parsed.owner_decisions_snapshot
		],
		"product_aggregate_present": parsed.product_aggregate_snapshot is not None,
	}


async def write_intake_v6_offer_from_frozen_snapshot_v2(
	db: AsyncSession,
	workspace_id: str | int,
	*,
	quote_id: int,
	expected_total_gross: float,
	operator_confirmation: bool = True,
	operator_identifier: str | None = None,
) -> dict[str, Any]:
	workspace_id_str = str(workspace_id)

	if not operator_confirmation:
		return _blocked(
			quote_id=quote_id,
			blockers=[
				_blocker(
					V6_OFFER_SNAPSHOT_OPERATOR_CONFIRMATION_REQUIRED,
					"Operator confirmation is required before stamping Offer from frozen snapshot.",
				)
			],
		)

	record = await resolve_frozen_quote_snapshot_v2_record(
		db,
		quote_id=quote_id,
		workspace_id=workspace_id_str,
	)
	if record is None:
		return _blocked(
			quote_id=quote_id,
			blockers=[
				_blocker(
					V6_OFFER_SNAPSHOT_NOT_FOUND,
					"No frozen Quote Snapshot V2 exists for this quote/workspace.",
				)
			],
		)

	try:
		parsed = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
	except Exception as exc:
		return _blocked(
			quote_id=quote_id,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[_blocker("V6_OFFER_SNAPSHOT_JSON_INVALID", f"Snapshot JSON invalid: {exc}")],
		)

	if record.readiness in HARD_BLOCKED_READINESS:
		return _blocked(
			quote_id=quote_id,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[
				_blocker(
					V6_OFFER_SNAPSHOT_READINESS_BLOCKED,
					f"Snapshot readiness {record.readiness!r} blocks Offer consumption.",
				)
			],
		)
	if record.readiness not in FREEZE_ALLOWED_READINESS:
		return _blocked(
			quote_id=quote_id,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[
				_blocker(
					V6_OFFER_SNAPSHOT_READINESS_BLOCKED,
					f"Snapshot readiness {record.readiness!r} is not allowed for Offer.",
				)
			],
		)

	cpp = parsed.commercial_price_proposal_snapshot
	if cpp is None or cpp.status == "blocked":
		return _blocked(
			quote_id=quote_id,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[
				_blocker(
					V6_OFFER_SNAPSHOT_COMMERCIAL_BLOCKED,
					"Frozen commercial proposal is missing or blocked.",
				)
			],
		)

	warnings = list(parsed.warnings_snapshot or [])
	vat_rate = float(await get_default_vat_pct(db))
	try:
		totals = commercial_totals_from_frozen_cpp(cpp, vat_rate=vat_rate)
	except ValueError as exc:
		return _blocked(
			quote_id=quote_id,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[_blocker(V6_OFFER_SNAPSHOT_COMMERCIAL_BLOCKED, str(exc))],
		)

	total_gross = _money(totals["total_gross"])
	if abs(_money(expected_total_gross) - total_gross) > 0.01:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[
				_blocker(
					V6_OFFER_SNAPSHOT_EXPECTED_TOTAL_MISMATCH,
					"Expected total does not match frozen snapshot commercial gross.",
				)
			],
			warnings=warnings,
		)

	line_items = map_cpp_lines_to_quote_items(list(cpp.commercial_price_lines or []))
	if not line_items:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[
				_blocker(
					V6_OFFER_SNAPSHOT_LINE_ITEMS_MISSING,
					"Frozen commercial lines are missing from snapshot.",
				)
			],
			warnings=warnings,
		)

	quotes_service = QuotesService(db)
	quote_obj = await quotes_service.get_by_id(quote_id)
	if quote_obj is None:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			line_items=line_items,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[_blocker(V6_OFFER_SNAPSHOT_QUOTE_MISMATCH, "Target quote was not found.")],
			warnings=warnings,
		)

	if record.quote_id is not None and record.quote_id != quote_id:
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=line_items,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[
				_blocker(
					V6_OFFER_SNAPSHOT_QUOTE_MISMATCH,
					"Frozen snapshot quote_id does not match target quote.",
				)
			],
			warnings=warnings,
		)

	notes_payload, legacy_notes_raw, notes_invalid = _parse_notes_preserving_raw(getattr(quote_obj, "notes", None))
	linkage = _existing_v6_linkage(notes_payload)
	expected_intake_code = intake_v6_linkage_code(workspace_id_str)
	quote_intake_code = str(getattr(quote_obj, "intake_code", "") or "")
	is_v6_quote = quote_intake_code == expected_intake_code or (
		isinstance(linkage, dict) and linkage.get("source_module") == "intake_v6"
	)
	if not is_v6_quote:
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=line_items,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[_blocker(V6_OFFER_SNAPSHOT_QUOTE_MISMATCH, "Target quote is not an Intake V6 quote.")],
			warnings=warnings,
		)

	linked_workspace_id = str((linkage or {}).get("source_workspace_id") or "")
	if record.workspace_id and record.workspace_id != workspace_id_str:
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=line_items,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[
				_blocker(
					V6_OFFER_SNAPSHOT_WORKSPACE_MISMATCH,
					"Frozen snapshot workspace_id does not match request workspace.",
				)
			],
			warnings=warnings,
		)
	if quote_intake_code != expected_intake_code and linked_workspace_id != workspace_id_str:
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=line_items,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[
				_blocker(
					V6_OFFER_SNAPSHOT_WORKSPACE_MISMATCH,
					"Target quote linkage does not match workspace.",
				)
			],
			warnings=warnings,
		)

	status = str(getattr(quote_obj, "status", "") or "")
	if status in _TERMINAL_OR_CONVERTED_STATUSES:
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=line_items,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[_blocker("V6_OFFER_SNAPSHOT_QUOTE_TERMINAL", "Terminal quotes cannot be restamped from snapshot.")],
			warnings=warnings,
		)

	existing_stamp = _existing_snapshot_offer_stamp(linkage)
	if (
		existing_stamp is not None
		and existing_stamp.get("content_hash") == record.content_hash
		and existing_stamp.get("snapshot_id") == record.id
	):
		return _success_response(
			status=V6_OFFER_FROM_SNAPSHOT_IDEMPOTENT,
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			totals=totals,
			line_items=line_items,
			record=record,
			parsed=parsed,
			warnings=warnings,
		)

	if existing_stamp is not None and existing_stamp.get("content_hash") not in (None, record.content_hash):
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=line_items,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[
				_blocker(
					V6_OFFER_SNAPSHOT_HASH_MISMATCH,
					"Quote already stamped from a different frozen snapshot hash.",
				)
			],
			warnings=warnings,
		)

	linkage_payload = dict(linkage or {})
	linkage_payload.update(
		{
			"source_module": "intake_v6",
			"source_workspace_id": workspace_id_str,
			"pricing_source": V6_SNAPSHOT_OFFER_PRICING_SOURCE,
			"requires_pricing_review": False,
		}
	)
	linkage_payload[INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY] = _build_snapshot_offer_stamp(
		record,
		parsed,
		workspace_id=workspace_id_str,
		operator_identifier=operator_identifier,
		totals=totals,
	)
	if legacy_notes_raw is not None:
		notes_payload["legacy_notes_raw"] = legacy_notes_raw
	notes_payload["human_summary"] = (
		f"Oferta Intake V6 proiectata din snapshot inghetat {record.snapshot_code}. "
		"Totalurile comerciale provin din Quote Snapshot V2 (7G) — fara repricing live."
	)
	notes_payload[INTAKE_V6_LINKAGE_JSON_KEY] = linkage_payload

	vat_amount = _money(totals.get("vat_amount") or 0)
	subtotal_net = _money(totals.get("subtotal_net") or 0)
	update_data = {
		"status": "priced",
		"line_items": json.dumps(line_items, default=str),
		"subtotal": subtotal_net,
		"discount": 0.0,
		"discount_pct": 0.0,
		"total_before_vat": subtotal_net,
		"vat": vat_amount,
		"grand_total": total_gross,
		"margin_pct": 0.0,
		"notes": json.dumps(notes_payload, default=str),
	}
	updated = await quotes_service.update(quote_id, update_data)
	if updated is None:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			line_items=line_items,
			snapshot_v2=_snapshot_v2_meta(record),
			blockers=[_blocker(V6_OFFER_SNAPSHOT_QUOTE_MISMATCH, "Quote update failed during snapshot Offer stamp.")],
			warnings=warnings,
		)

	return _success_response(
		status=V6_OFFER_FROM_SNAPSHOT_WRITTEN,
		quote_id=int(getattr(updated, "id", quote_id)),
		quote_code=getattr(updated, "code", None),
		totals=totals,
		line_items=line_items,
		record=record,
		parsed=parsed,
		warnings=warnings,
	)
