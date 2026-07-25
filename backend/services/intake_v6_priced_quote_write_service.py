"""Guarded Intake V6 priced quote write service.

Writes official quote totals only from the backend V6 priced dry-run result.
No quote creation, no snapshot, no order, no V4 draft payload.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.orders import Orders
from models.quote_output_snapshots import QuoteOutputSnapshot
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from services.intake_v6_commercial_quote_service import INTAKE_V6_LINKAGE_JSON_KEY, intake_v6_linkage_code
from services.intake_v6_priced_quote_dry_run_service import (
	V6_PRICED_DRY_RUN_READY,
	V6_PRICED_DRY_RUN_SOURCE,
	build_intake_v6_priced_quote_dry_run,
)
from services.quotes import QuotesService

V6_PRICED_QUOTE_WRITTEN = "V6_PRICED_QUOTE_WRITTEN"
V6_PRICED_QUOTE_WRITE_BLOCKED = "V6_PRICED_QUOTE_WRITE_BLOCKED"

V6_PRICED_QUOTE_WRITE_DRY_RUN_BLOCKED = "V6_PRICED_QUOTE_WRITE_DRY_RUN_BLOCKED"
V6_PRICED_QUOTE_WRITE_ZERO_TOTAL = "V6_PRICED_QUOTE_WRITE_ZERO_TOTAL"
V6_PRICED_QUOTE_WRITE_EXPECTED_TOTAL_MISMATCH = "V6_PRICED_QUOTE_WRITE_EXPECTED_TOTAL_MISMATCH"
V6_PRICED_QUOTE_WRITE_NOT_V6_QUOTE = "V6_PRICED_QUOTE_WRITE_NOT_V6_QUOTE"
V6_PRICED_QUOTE_WRITE_WORKSPACE_MISMATCH = "V6_PRICED_QUOTE_WRITE_WORKSPACE_MISMATCH"
V6_PRICED_QUOTE_WRITE_ALREADY_PRICED = "V6_PRICED_QUOTE_WRITE_ALREADY_PRICED"
V6_PRICED_QUOTE_WRITE_SNAPSHOT_EXISTS = "V6_PRICED_QUOTE_WRITE_SNAPSHOT_EXISTS"
V6_PRICED_QUOTE_WRITE_SNAPSHOT_ALREADY_FROZEN = "V6_PRICED_QUOTE_WRITE_SNAPSHOT_ALREADY_FROZEN"
V6_PRICED_QUOTE_WRITE_ORDER_EXISTS = "V6_PRICED_QUOTE_WRITE_ORDER_EXISTS"
V6_PRICED_QUOTE_WRITE_OPERATOR_CONFIRMATION_REQUIRED = "V6_PRICED_QUOTE_WRITE_OPERATOR_CONFIRMATION_REQUIRED"
V6_PRICED_QUOTE_WRITE_FORBIDDEN_SOURCE = "V6_PRICED_QUOTE_WRITE_FORBIDDEN_SOURCE"
V6_PRICED_QUOTE_WRITE_LINE_ITEMS_MISSING = "V6_PRICED_QUOTE_WRITE_LINE_ITEMS_MISSING"
V6_PRICED_QUOTE_WRITE_NOTES_INVALID = "V6_PRICED_QUOTE_WRITE_NOTES_INVALID"

_TERMINAL_OR_CONVERTED_STATUSES = frozenset({"accepted", "rejected", "expired", "converted", "ordered"})


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
) -> dict[str, Any]:
	return {
		"status": V6_PRICED_QUOTE_WRITE_BLOCKED,
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
	}


def _as_positive_number(value: Any) -> float | None:
	try:
		number = float(value)
	except (TypeError, ValueError):
		return None
	return number if number > 0 else None


def _money(value: Any) -> float:
	return round(float(value), 2)


def _pricing_hash(dry_run: dict[str, Any]) -> str:
	payload = {
		"pricing_source": dry_run.get("pricing_source"),
		"commercial_totals": dry_run.get("commercial_totals"),
		"commercial_line_items": dry_run.get("commercial_line_items"),
		"pricing_input_trace": dry_run.get("pricing_input_trace"),
		"commercial_proposal_trace": dry_run.get("commercial_proposal_trace"),
	}
	encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
	return hashlib.sha256(encoded).hexdigest()


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


def _quote_is_zero_valued(quote_obj: Any) -> bool:
	for field in ("subtotal", "total_before_vat", "vat", "grand_total"):
		try:
			if float(getattr(quote_obj, field, 0) or 0) > 0:
				return False
		except (TypeError, ValueError):
			return False
	return True


def dry_run_line_to_quote_line(line: dict[str, Any]) -> dict[str, Any]:
	unit_price = _money(line.get("commercial_unit_price") or 0)
	total = _money(line.get("subtotal") or 0)
	return {
		"description": line.get("label") or line.get("code") or "V6 commercial line",
		"name": line.get("label") or line.get("code") or "V6 commercial line",
		"quantity": line.get("quantity"),
		"unit": line.get("unit"),
		"unit_price": unit_price,
		"total": total,
		"source_component": line.get("component_code") or line.get("module_code"),
		"module_code": line.get("module_code"),
		"component_code": line.get("component_code"),
		"pricing_rule_code": line.get("pricing_rule_code"),
		"pricing_source": V6_PRICED_DRY_RUN_SOURCE,
		"client_visible": True,
		"warnings": list(line.get("warnings") or []),
	}


def map_dry_run_lines_to_quote_items(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
	mapped = [dry_run_line_to_quote_line(line) for line in lines if isinstance(line, dict)]
	return [line for line in mapped if _as_positive_number(line.get("total")) is not None]


async def _snapshot_count(db: AsyncSession, quote_id: int) -> int:
	result = await db.execute(select(func.count(QuoteOutputSnapshot.id)).where(QuoteOutputSnapshot.quote_id == quote_id))
	return int(result.scalar() or 0)


async def _order_count(db: AsyncSession, quote_id: int) -> int:
	result = await db.execute(select(func.count(Orders.id)).where(Orders.quote_id == quote_id))
	return int(result.scalar() or 0)


async def _has_frozen_quote_snapshot_v2(
	db: AsyncSession,
	*,
	quote_id: int,
	workspace_id: str,
) -> bool:
	query = (
		select(func.count(QuoteSnapshotV2Record.id))
		.where(
			QuoteSnapshotV2Record.quote_id == quote_id,
			QuoteSnapshotV2Record.status == "frozen",
		)
	)
	result = await db.execute(query)
	if int(result.scalar() or 0) > 0:
		return True
	ws_query = (
		select(func.count(QuoteSnapshotV2Record.id))
		.where(
			QuoteSnapshotV2Record.workspace_id == workspace_id,
			QuoteSnapshotV2Record.status == "frozen",
		)
	)
	ws_result = await db.execute(ws_query)
	return int(ws_result.scalar() or 0) > 0


def _internal_cost_trace_summary(dry_run: dict[str, Any]) -> dict[str, Any]:
	trace = dry_run.get("internal_cost_trace") if isinstance(dry_run.get("internal_cost_trace"), dict) else {}
	return {
		"available": trace.get("available"),
		"estimated_cost_total": trace.get("estimated_cost_total"),
		"material_cost_total": trace.get("material_cost_total"),
		"currency": trace.get("currency"),
		"contains_estimates": trace.get("contains_estimates"),
		"contains_missing_prices": trace.get("contains_missing_prices"),
	}


def _priced_human_summary(workspace_code: Any, workspace_id: str) -> str:
	display_code = str(workspace_code or workspace_id)
	return (
		f"Oferta pretuita din Intake V6 workspace {display_code}. "
		"Totalurile comerciale V6 au fost scrise pe oferta ca pret comercial final. "
		"Oferta ramane in revizie interna pana la aprobarea/trimiterea catre client. "
		"Nu a fost creata comanda, executie sau miscare de stoc."
	)


async def write_intake_v6_priced_quote_totals(
	db: AsyncSession,
	workspace_id: str | int,
	*,
	quote_id: int,
	expected_total_gross: float,
	expected_pricing_hash: str | None = None,
	operator_confirmation: bool = True,
	operator_identifier: str | None = None,
) -> dict[str, Any]:
	workspace_id_str = str(workspace_id)

	if not operator_confirmation:
		return _blocked(
			quote_id=quote_id,
			blockers=[
				_blocker(
					V6_PRICED_QUOTE_WRITE_OPERATOR_CONFIRMATION_REQUIRED,
					"Operator confirmation is required before writing V6 priced quote totals.",
				)
			],
		)

	if await _has_frozen_quote_snapshot_v2(db, quote_id=quote_id, workspace_id=workspace_id_str):
		return _blocked(
			quote_id=quote_id,
			blockers=[
				_blocker(
					V6_PRICED_QUOTE_WRITE_SNAPSHOT_ALREADY_FROZEN,
					"Frozen Quote Snapshot V2 exists; priced-quote/write cannot reprice. Use handoff-to-offer with snapshot authority.",
				)
			],
		)

	dry_run = await build_intake_v6_priced_quote_dry_run(db, workspace_id_str, pricing_mode="write_priced_quote")
	totals = dry_run.get("commercial_totals") if isinstance(dry_run.get("commercial_totals"), dict) else {}
	dry_run_lines = dry_run.get("commercial_line_items") if isinstance(dry_run.get("commercial_line_items"), list) else []
	warnings = list(dry_run.get("warnings") or [])

	if dry_run.get("pricing_status") != V6_PRICED_DRY_RUN_READY:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			line_items=dry_run_lines,
			blockers=[
				_blocker(
					V6_PRICED_QUOTE_WRITE_DRY_RUN_BLOCKED,
					"V6 priced quote dry-run is blocked; official totals were not written.",
				),
				*list(dry_run.get("blockers") or []),
			],
			warnings=warnings,
		)

	if dry_run.get("pricing_source") != V6_PRICED_DRY_RUN_SOURCE:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			line_items=dry_run_lines,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_FORBIDDEN_SOURCE, "V6 write requires backend V6 dry-run pricing source.")],
			warnings=warnings,
		)

	subtotal = _as_positive_number(totals.get("subtotal_net"))
	total_gross = _as_positive_number(totals.get("total_gross"))
	if subtotal is None or total_gross is None:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			line_items=dry_run_lines,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_ZERO_TOTAL, "Zero or missing dry-run totals cannot be written as official quote totals.")],
			warnings=warnings,
		)

	if abs(_money(total_gross) - _money(expected_total_gross)) > 0.01:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			line_items=dry_run_lines,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_EXPECTED_TOTAL_MISMATCH, "Expected total does not match server recomputed V6 dry-run total.")],
			warnings=warnings,
		)

	pricing_hash = _pricing_hash(dry_run)
	if expected_pricing_hash and expected_pricing_hash != pricing_hash:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			line_items=dry_run_lines,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_EXPECTED_TOTAL_MISMATCH, "Expected pricing hash does not match server recomputed V6 dry-run hash.")],
			warnings=warnings,
		)

	mapped_line_items = map_dry_run_lines_to_quote_items(dry_run_lines)
	if not mapped_line_items:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			line_items=[],
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_LINE_ITEMS_MISSING, "V6 dry-run has no positive commercial line items to write.")],
			warnings=warnings,
		)

	quotes_service = QuotesService(db)
	quote_obj = await quotes_service.get_by_id(quote_id)
	if quote_obj is None:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			line_items=mapped_line_items,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_NOT_V6_QUOTE, "Target quote was not found or is not a V6 quote.")],
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
			line_items=mapped_line_items,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_NOT_V6_QUOTE, "Target quote is not linked as an Intake V6 quote.")],
			warnings=warnings,
		)

	linked_workspace_id = str((linkage or {}).get("source_workspace_id") or "")
	if quote_intake_code != expected_intake_code and linked_workspace_id != workspace_id_str:
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=mapped_line_items,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_WORKSPACE_MISMATCH, "Target quote linkage does not match the Intake V6 workspace.")],
			warnings=warnings,
		)

	status = str(getattr(quote_obj, "status", "") or "")
	if status in _TERMINAL_OR_CONVERTED_STATUSES:
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=mapped_line_items,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_ORDER_EXISTS, "Accepted or converted quotes cannot be overwritten by V6 priced write.")],
			warnings=warnings,
		)

	if not _quote_is_zero_valued(quote_obj):
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=mapped_line_items,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_ALREADY_PRICED, "Target quote already has positive commercial totals.")],
			warnings=warnings,
		)

	if getattr(quote_obj, "accepted_snapshot_v2_id", None):
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=mapped_line_items,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_SNAPSHOT_EXISTS, "Target quote already references an accepted snapshot.")],
			warnings=warnings,
		)

	if await _snapshot_count(db, quote_id) > 0:
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=mapped_line_items,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_SNAPSHOT_EXISTS, "Target quote already has output snapshots and cannot be overwritten.")],
			warnings=warnings,
		)

	if await _order_count(db, quote_id) > 0:
		return _blocked(
			quote_id=quote_id,
			quote_code=getattr(quote_obj, "code", None),
			commercial_totals=totals,
			line_items=mapped_line_items,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_ORDER_EXISTS, "Target quote already has an order and cannot be overwritten.")],
			warnings=warnings,
		)

	now = datetime.now(timezone.utc).isoformat()
	linkage_payload = dict(linkage or {})
	linkage_payload.update(
		{
			"source_module": "intake_v6",
			"source_workspace_id": workspace_id_str,
			"source_workspace_code": dry_run.get("workspace_code"),
			"pricing_source": V6_PRICED_DRY_RUN_SOURCE,
			"requires_pricing_review": False,
		}
	)
	linkage_payload["intake_v6_priced_quote_write_v1"] = {
		"workspace_id": workspace_id_str,
		"workspace_code": dry_run.get("workspace_code"),
		"intake_code": dry_run.get("intake_code"),
		"pricing_source": V6_PRICED_DRY_RUN_SOURCE,
		"dry_run_generated_at": now,
		"write_timestamp": now,
		"write_operator": operator_identifier,
		"expected_total_gross": _money(expected_total_gross),
		"written_total_gross": _money(total_gross),
		"pricing_hash": pricing_hash,
		"pricing_input_trace": dry_run.get("pricing_input_trace"),
		"commercial_proposal_trace": dry_run.get("commercial_proposal_trace"),
		"internal_cost_trace_summary": _internal_cost_trace_summary(dry_run),
		"previous_unpriced_quote_totals": {
			"subtotal": getattr(quote_obj, "subtotal", None),
			"total_before_vat": getattr(quote_obj, "total_before_vat", None),
			"vat": getattr(quote_obj, "vat", None),
			"grand_total": getattr(quote_obj, "grand_total", None),
		},
		"notes_invalid_preserved_as_legacy_raw": notes_invalid,
		"no_v4_v2_commercial_truth": True,
		"frontend_preview_not_used": True,
		"quote_snapshot_created": False,
		"order_created": False,
	}
	if legacy_notes_raw is not None:
		notes_payload["legacy_notes_raw"] = legacy_notes_raw
	notes_payload["human_summary"] = _priced_human_summary(dry_run.get("workspace_code"), workspace_id_str)
	notes_payload[INTAKE_V6_LINKAGE_JSON_KEY] = linkage_payload

	vat_amount = _money(totals.get("vat_amount") or 0)
	adjustment_trace = (
		totals.get("commercial_adjustment_trace")
		if isinstance(totals.get("commercial_adjustment_trace"), dict)
		else {}
	)
	# Quote.margin_pct stores operator Adaos comercial % (markup on 7G base), not true margin.
	markup_percent = adjustment_trace.get("markup_percent")
	try:
		margin_pct = float(markup_percent) if markup_percent is not None else 0.0
	except (TypeError, ValueError):
		margin_pct = 0.0
	discount_percent = adjustment_trace.get("discount_percent")
	try:
		discount_pct = float(discount_percent) if discount_percent is not None else 0.0
	except (TypeError, ValueError):
		discount_pct = 0.0
	discount_value = adjustment_trace.get("discount_value")
	try:
		discount_amount = float(discount_value) if discount_value is not None else 0.0
	except (TypeError, ValueError):
		discount_amount = 0.0
	linkage_payload["intake_v6_priced_quote_write_v1"]["commercial_adjustment_trace"] = adjustment_trace
	update_data = {
		"status": "priced",
		"line_items": json.dumps(mapped_line_items, default=str),
		"subtotal": _money(subtotal),
		"discount": _money(discount_amount),
		"discount_pct": discount_pct,
		"total_before_vat": _money(subtotal),
		"vat": vat_amount,
		"grand_total": _money(total_gross),
		"margin_pct": margin_pct,
		"notes": json.dumps(notes_payload, default=str),
	}
	updated = await quotes_service.update(quote_id, update_data)
	if updated is None:
		return _blocked(
			quote_id=quote_id,
			commercial_totals=totals,
			line_items=mapped_line_items,
			blockers=[_blocker(V6_PRICED_QUOTE_WRITE_NOT_V6_QUOTE, "Target quote disappeared before V6 priced write.")],
			warnings=warnings,
		)

	return {
		"status": V6_PRICED_QUOTE_WRITTEN,
		"quote_id": int(getattr(updated, "id", quote_id)),
		"quote_code": getattr(updated, "code", None),
		"commercial_totals": {
			"subtotal_net": _money(subtotal),
			"discount": 0.0,
			"total_before_vat": _money(subtotal),
			"vat": vat_amount,
			"vat_rate": totals.get("vat_rate"),
			"total_gross": _money(total_gross),
			"currency": totals.get("currency") or "RON",
		},
		"line_items": mapped_line_items,
		"pricing_trace": {
			"pricing_source": V6_PRICED_DRY_RUN_SOURCE,
			"pricing_hash": pricing_hash,
			"dry_run_generated_at": now,
			"no_v4_v2_commercial_truth": True,
			"frontend_preview_not_used": True,
		},
		"blockers": [],
		"warnings": warnings,
		"can_create_quote_snapshot": True,
		"can_accept_quote": False,
		"quote_snapshot_created": False,
		"order_created": False,
	}