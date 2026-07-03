"""Quote Snapshot V2 for backend-priced Intake V6 quotes.

Creates an immutable quote output snapshot from persisted quote totals only.
No quote total rewrite, no order, no downstream production/execution entities.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from schemas.commercial_price_proposal import CommercialPriceLine, CommercialPriceProposalPreview, CommercialProvenanceEntry
from schemas.estimated_internal_cost import EstimatedInternalCostPreview, InternalProvenanceEntry
from schemas.quote_snapshot_v2 import QUOTE_SNAPSHOT_V2_VERSION, QuoteSnapshotProvenanceEntry, QuoteSnapshotV2
from services.intake_v6_commercial_quote_service import INTAKE_V6_LINKAGE_JSON_KEY, intake_v6_linkage_code
from services.intake_v6_priced_quote_dry_run_service import V6_PRICED_DRY_RUN_SOURCE
from services.quotes import QuotesService

QUOTE_SNAPSHOT_V2 = "QUOTE_SNAPSHOT_V2"
V6_QUOTE_SNAPSHOT_KIND = "V6_PRICED_QUOTE_OFFICIAL_OFFER"
V6_QUOTE_SNAPSHOT_V2_CREATED = "V6_QUOTE_SNAPSHOT_V2_CREATED"
V6_QUOTE_SNAPSHOT_V2_BLOCKED = "V6_QUOTE_SNAPSHOT_V2_BLOCKED"

V6_SNAPSHOT_QUOTE_NOT_FOUND = "V6_SNAPSHOT_QUOTE_NOT_FOUND"
V6_SNAPSHOT_NOT_V6_QUOTE = "V6_SNAPSHOT_NOT_V6_QUOTE"
V6_SNAPSHOT_WORKSPACE_MISMATCH = "V6_SNAPSHOT_WORKSPACE_MISMATCH"
V6_SNAPSHOT_QUOTE_NOT_PRICED = "V6_SNAPSHOT_QUOTE_NOT_PRICED"
V6_SNAPSHOT_ZERO_TOTAL = "V6_SNAPSHOT_ZERO_TOTAL"
V6_SNAPSHOT_INVALID_TOTALS = "V6_SNAPSHOT_INVALID_TOTALS"
V6_SNAPSHOT_LINE_ITEMS_MISSING = "V6_SNAPSHOT_LINE_ITEMS_MISSING"
V6_SNAPSHOT_LINE_ITEMS_INVALID = "V6_SNAPSHOT_LINE_ITEMS_INVALID"
V6_SNAPSHOT_WRITE_PROVENANCE_MISSING = "V6_SNAPSHOT_WRITE_PROVENANCE_MISSING"
V6_SNAPSHOT_FRONTEND_PREVIEW_FORBIDDEN = "V6_SNAPSHOT_FRONTEND_PREVIEW_FORBIDDEN"
V6_SNAPSHOT_V2_V4_SOURCE_FORBIDDEN = "V6_SNAPSHOT_V2_V4_SOURCE_FORBIDDEN"
V6_SNAPSHOT_ALREADY_EXISTS = "V6_SNAPSHOT_ALREADY_EXISTS"
V6_SNAPSHOT_ORDER_EXISTS = "V6_SNAPSHOT_ORDER_EXISTS"
V6_SNAPSHOT_QUOTE_TERMINAL = "V6_SNAPSHOT_QUOTE_TERMINAL"
V6_SNAPSHOT_OPERATOR_CONFIRMATION_REQUIRED = "V6_SNAPSHOT_OPERATOR_CONFIRMATION_REQUIRED"
V6_SNAPSHOT_EXPECTED_TOTAL_MISMATCH = "V6_SNAPSHOT_EXPECTED_TOTAL_MISMATCH"
V6_SNAPSHOT_EXPECTED_HASH_MISMATCH = "V6_SNAPSHOT_EXPECTED_HASH_MISMATCH"
V6_SNAPSHOT_NOTES_INVALID = "V6_SNAPSHOT_NOTES_INVALID"
V6_SNAPSHOT_AMBIGUOUS_STATE = "V6_SNAPSHOT_AMBIGUOUS_STATE"

_TERMINAL_STATUSES = frozenset({"accepted", "rejected", "expired", "converted", "ordered"})


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _blocked(
	*,
	quote_id: int | None,
	quote_code: str | None = None,
	blockers: list[dict[str, str]],
	warnings: list[str] | None = None,
) -> dict[str, Any]:
	return {
		"status": V6_QUOTE_SNAPSHOT_V2_BLOCKED,
		"quote_id": quote_id,
		"quote_code": quote_code,
		"snapshot_id": None,
		"snapshot_version": QUOTE_SNAPSHOT_V2,
		"commercial": None,
		"line_items": [],
		"v6_linkage": {},
		"client_output": {},
		"blockers": blockers,
		"warnings": warnings or [],
		"can_accept_quote": False,
		"can_create_order": False,
		"order_snapshot_required": True,
		"quote_snapshot_created": False,
		"order_created": False,
		"product_aggregate_created": False,
		"task_graph_created": False,
		"execution_plan_created": False,
	}


def _money(value: Any) -> float:
	return round(float(value), 2)


def _positive(value: Any) -> float | None:
	try:
		number = float(value)
	except (TypeError, ValueError):
		return None
	return number if number > 0 else None


def _non_negative(value: Any) -> float | None:
	try:
		number = float(value)
	except (TypeError, ValueError):
		return None
	return number if number >= 0 else None


def _parse_json(raw: Any) -> Any:
	if raw is None:
		return None
	try:
		return json.loads(raw) if isinstance(raw, str) else raw
	except (json.JSONDecodeError, TypeError):
		return None


def _parse_notes(raw_notes: str | None) -> tuple[dict[str, Any] | None, bool]:
	if not raw_notes:
		return {}, False
	parsed = _parse_json(raw_notes)
	return (parsed, False) if isinstance(parsed, dict) else (None, True)


def _v6_linkage(notes_payload: dict[str, Any]) -> dict[str, Any] | None:
	linkage = notes_payload.get(INTAKE_V6_LINKAGE_JSON_KEY)
	return linkage if isinstance(linkage, dict) else None


def _write_trace(linkage: dict[str, Any]) -> dict[str, Any] | None:
	trace = linkage.get("intake_v6_priced_quote_write_v1")
	return trace if isinstance(trace, dict) else None


def _line_total(line: dict[str, Any]) -> float | None:
	return _positive(line.get("total"))


def _normalize_line_items(raw_line_items: Any) -> list[dict[str, Any]] | None:
	parsed = _parse_json(raw_line_items)
	if not isinstance(parsed, list) or not parsed:
		return None
	items: list[dict[str, Any]] = []
	for line in parsed:
		if not isinstance(line, dict):
			return None
		if line.get("client_visible") is not False and _line_total(line) is None:
			return None
		items.append(
			{
				"name": line.get("name") or line.get("description") or "V6 quote line",
				"description": line.get("description") or line.get("name") or "V6 quote line",
				"quantity": line.get("quantity"),
				"unit": line.get("unit"),
				"unit_price": _money(line.get("unit_price") or 0),
				"total": _money(line.get("total") or 0),
				"source_component": line.get("source_component"),
				"pricing_source": line.get("pricing_source"),
				"client_visible": line.get("client_visible") is not False,
			}
		)
	return items


def _commercial_payload(quote_obj: Any) -> dict[str, Any] | None:
	subtotal = _positive(getattr(quote_obj, "subtotal", None))
	total_before_vat = _positive(getattr(quote_obj, "total_before_vat", None))
	vat = _non_negative(getattr(quote_obj, "vat", None))
	grand_total = _positive(getattr(quote_obj, "grand_total", None))
	if subtotal is None or total_before_vat is None or vat is None or grand_total is None:
		return None
	return {
		"currency": "RON",
		"subtotal": _money(subtotal),
		"discount": _money(getattr(quote_obj, "discount", 0) or 0),
		"total_before_vat": _money(total_before_vat),
		"vat": _money(vat),
		"grand_total": _money(grand_total),
		"vat_rate": None,
		"margin_pct": getattr(quote_obj, "margin_pct", None),
	}


def _client_output(quote_obj: Any, commercial: dict[str, Any], line_items: list[dict[str, Any]]) -> dict[str, Any]:
	client_name = getattr(quote_obj, "client_name", None) or "Client"
	quote_code = getattr(quote_obj, "code", None) or "Quote"
	return {
		"title": f"Oferta {quote_code}",
		"summary": f"Oferta oficiala pentru {client_name}",
		"client_name": client_name,
		"client_id": getattr(quote_obj, "client_id", None),
		"quote_code": quote_code,
		"offer_lines": [line for line in line_items if line.get("client_visible") is not False],
		"total_net": commercial["total_before_vat"],
		"vat": commercial["vat"],
		"total_gross": commercial["grand_total"],
		"currency": commercial["currency"],
		"validity": getattr(quote_obj, "valid_until", None) or "Valabilitatea se confirma comercial inainte de acceptare.",
		"terms": ["Snapshot Quote V2 - oferta oficiala inghetata backend."],
		"notes": ["Preturile sunt generate din totalurile persistate ale ofertei, nu din preview frontend."],
		"generated_from": QUOTE_SNAPSHOT_V2,
	}


def _snapshot_hash(payload: dict[str, Any]) -> str:
	encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
	return hashlib.sha256(encoded).hexdigest()


async def _snapshot_count(db: AsyncSession, quote_id: int) -> int:
	result = await db.execute(select(func.count(QuoteSnapshotV2Record.id)).where(QuoteSnapshotV2Record.quote_id == quote_id))
	return int(result.scalar() or 0)


async def _order_count(db: AsyncSession, quote_id: int) -> int:
	result = await db.execute(select(func.count(Orders.id)).where(Orders.quote_id == quote_id))
	return int(result.scalar() or 0)


async def _next_snapshot_number(db: AsyncSession) -> int:
	result = await db.execute(select(func.count(QuoteSnapshotV2Record.id)))
	return int(result.scalar() or 0) + 1


def _quote_snapshot_v2_payload(
	*,
	quote_obj: Any,
	workspace_id: str,
	template_code: str,
	commercial: dict[str, Any],
	line_items: list[dict[str, Any]],
	write_trace: dict[str, Any],
	created_by: str | None,
	now: str,
) -> QuoteSnapshotV2:
	commercial_lines = [
		CommercialPriceLine(
			code=str(line.get("source_component") or line.get("name") or "v6_quote_line"),
			label=str(line.get("name") or line.get("description") or "V6 quote line"),
			component_code=line.get("source_component"),
			basis_type="unknown",
			quantity=line.get("quantity"),
			unit=line.get("unit"),
			commercial_unit_price=line.get("unit_price"),
			subtotal=line.get("total"),
			pricing_rule_code="V6_BACKEND_PRICED_QUOTE_LINE",
			source=V6_PRICED_DRY_RUN_SOURCE,
		)
		for line in line_items
	]
	commercial_preview = CommercialPriceProposalPreview(
		template_code=template_code,
		status="ready",
		commercial_price_lines=commercial_lines,
		subtotal_commercial=commercial["total_before_vat"],
		commercial_total=commercial["grand_total"],
		currency=commercial["currency"],
		provenance=[
			CommercialProvenanceEntry(
				key="intake_v6_priced_quote_write_v1",
				source="intake_v6_priced_quote_write_service",
				detail="official quote totals already persisted; snapshot reuses quote columns",
			)
		],
		confidence="high",
		quote_ready_for_commercial_review=True,
		notes=["Commercial snapshot built from persisted Intake V6 backend-priced quote totals."],
	)
	internal_summary = write_trace.get("internal_cost_trace_summary") if isinstance(write_trace.get("internal_cost_trace_summary"), dict) else {}
	internal_total = internal_summary.get("estimated_cost_total")
	internal_preview = EstimatedInternalCostPreview(
		template_code=template_code,
		status="ready" if internal_total is not None else "partial",
		estimated_total_internal_cost=internal_total,
		currency=str(internal_summary.get("currency") or "EUR"),
		provenance=[
			InternalProvenanceEntry(
				key="intake_v6_priced_quote_write_v1.internal_cost_trace_summary",
				source="intake_v6_priced_quote_write_service",
				detail="internal cost trace captured at priced quote write time",
			)
		],
		completeness=1.0 if internal_total is not None else 0.5,
		confidence="medium",
		ready_for_quote_snapshot=True,
		notes=["Internal cost snapshot copied from Intake V6 priced write trace; no CostEngine call."],
	)
	return QuoteSnapshotV2(
		quote_id=str(getattr(quote_obj, "id", "")),
		workspace_id=workspace_id,
		template_code=template_code,
		commercial_price_proposal_snapshot=commercial_preview,
		estimated_internal_cost_snapshot=internal_preview,
		readiness="ready_for_owner_review",
		frozen_at=now,
		frozen_by=created_by,
		version=1,
		provenance=[
			QuoteSnapshotProvenanceEntry(
				key="quote_snapshot_v2",
				source="intake_v6_quote_snapshot_v2_service",
				detail="persisted_from_backend_priced_v6_quote=true",
			),
			QuoteSnapshotProvenanceEntry(
				key="no_order_no_execution_no_inventory",
				source="intake_v6_quote_snapshot_v2_service",
				detail="snapshot_only=true",
			),
		],
		persist_status="persisted",
		notes=[
			"Quote Snapshot V2 frozen from persisted Intake V6 backend-priced quote totals.",
			"Does not create order, execution plan, execution tasks, inventory movement, or product/task aggregates.",
		],
		input_summary={
			"quote_code": getattr(quote_obj, "code", None),
			"workspace_id": workspace_id,
			"commercial_total": commercial["grand_total"],
			"source": V6_PRICED_DRY_RUN_SOURCE,
		},
	)


async def _persist_snapshot(
	db: AsyncSession,
	*,
	quote_obj: Any,
	snapshot_payload: dict[str, Any],
	commercial: dict[str, Any],
	client_output: dict[str, Any],
	created_by: str | None,
	content_hash: str,
	quote_snapshot_v2: QuoteSnapshotV2,
) -> QuoteSnapshotV2Record:
	number = await _next_snapshot_number(db)
	now_year = datetime.now(timezone.utc).year
	snapshot_code = f"QSN2-{now_year}-{number:04d}"
	snapshot_json = quote_snapshot_v2.model_dump_json()
	v2_content_hash = hashlib.sha256(snapshot_json.encode()).hexdigest()[:32]
	snapshot = QuoteSnapshotV2Record(
		snapshot_code=snapshot_code,
		snapshot_version=QUOTE_SNAPSHOT_V2_VERSION,
		version=number,
		quote_id=int(quote_obj.id),
		workspace_id=snapshot_payload["v6_linkage"].get("workspace_id"),
		template_code=snapshot_payload["v6_linkage"].get("template_code") or "TPL-VOLUMETRIC-LETTERS_v2",
		status="frozen",
		readiness="ready_for_owner_review",
		frozen_at=datetime.now(timezone.utc),
		frozen_by=created_by,
		snapshot_json=snapshot_json,
		content_hash=v2_content_hash,
		notes=json.dumps(
			{
				"snapshot_payload": snapshot_payload,
				"client_output": client_output,
				"legacy_content_hash": content_hash,
			},
			default=str,
		),
	)
	db.add(snapshot)
	await db.commit()
	await db.refresh(snapshot)
	return snapshot


async def create_v6_quote_snapshot_v2(
	db: AsyncSession,
	*,
	quote_id: int,
	workspace_id: str | int,
	operator_confirmation: bool = True,
	expected_grand_total: float | None = None,
	expected_pricing_hash: str | None = None,
	created_by: str | None = None,
) -> dict[str, Any]:
	workspace_id_str = str(workspace_id)
	if not operator_confirmation:
		return _blocked(
			quote_id=quote_id,
			blockers=[_blocker(V6_SNAPSHOT_OPERATOR_CONFIRMATION_REQUIRED, "Operator confirmation is required before creating Quote Snapshot V2.")],
		)

	quote_obj = await QuotesService(db).get_by_id(quote_id)
	if quote_obj is None:
		return _blocked(quote_id=quote_id, blockers=[_blocker(V6_SNAPSHOT_QUOTE_NOT_FOUND, "Quote was not found.")])

	quote_code = getattr(quote_obj, "code", None)
	notes_payload, notes_invalid = _parse_notes(getattr(quote_obj, "notes", None))
	if notes_invalid or notes_payload is None:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_NOTES_INVALID, "Quote notes are not valid JSON for V6 snapshot provenance.")])

	linkage = _v6_linkage(notes_payload)
	quote_intake_code = str(getattr(quote_obj, "intake_code", "") or "")
	expected_intake_code = intake_v6_linkage_code(workspace_id_str)
	if linkage is None and quote_intake_code != expected_intake_code:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_NOT_V6_QUOTE, "Quote is not linked as an Intake V6 quote.")])

	linked_workspace_id = str((linkage or {}).get("source_workspace_id") or "")
	if linked_workspace_id and linked_workspace_id != workspace_id_str:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_WORKSPACE_MISMATCH, "Quote workspace linkage does not match snapshot request.")])
	if quote_intake_code != expected_intake_code and linked_workspace_id != workspace_id_str:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_WORKSPACE_MISMATCH, "Quote workspace linkage does not match snapshot request.")])

	status = str(getattr(quote_obj, "status", "") or "")
	if status in _TERMINAL_STATUSES:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_QUOTE_TERMINAL, "Terminal or accepted quote cannot create a new V6 snapshot in this slice.")])
	if status != "priced" and not (status == "draft" and _positive(getattr(quote_obj, "grand_total", None)) is not None):
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_QUOTE_NOT_PRICED, "Quote must have official V6 priced totals before Quote Snapshot V2 can be created.")])

	commercial = _commercial_payload(quote_obj)
	if commercial is None:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_INVALID_TOTALS, "Quote totals are missing or invalid for Quote Snapshot V2.")])
	if commercial["grand_total"] <= 0:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_ZERO_TOTAL, "Zero quote total cannot be snapshotted as official V6 offer truth.")])
	if expected_grand_total is not None and abs(_money(expected_grand_total) - commercial["grand_total"]) > 0.01:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_EXPECTED_TOTAL_MISMATCH, "Expected grand total does not match persisted quote grand total.")])

	line_items = _normalize_line_items(getattr(quote_obj, "line_items", None))
	if line_items is None:
		parsed = _parse_json(getattr(quote_obj, "line_items", None))
		code = V6_SNAPSHOT_LINE_ITEMS_MISSING if not parsed else V6_SNAPSHOT_LINE_ITEMS_INVALID
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(code, "Quote line items are missing or invalid for Quote Snapshot V2.")])

	write_trace = _write_trace(linkage or {})
	if write_trace is None:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_WRITE_PROVENANCE_MISSING, "V6 priced quote write provenance is missing.")])
	if write_trace.get("frontend_preview_not_used") is not True:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_FRONTEND_PREVIEW_FORBIDDEN, "Snapshot cannot be created from frontend preview provenance.")])
	if write_trace.get("no_v4_v2_commercial_truth") is not True:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_V2_V4_SOURCE_FORBIDDEN, "Snapshot cannot use V2/V4 commercial truth for V6.")])
	if (linkage or {}).get("pricing_source") != V6_PRICED_DRY_RUN_SOURCE:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_V2_V4_SOURCE_FORBIDDEN, "Snapshot requires V6 backend priced dry-run pricing source.")])
	if expected_pricing_hash and expected_pricing_hash != write_trace.get("pricing_hash"):
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_EXPECTED_HASH_MISMATCH, "Expected pricing hash does not match V6 write provenance.")])

	if await _snapshot_count(db, quote_id) > 0:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_ALREADY_EXISTS, "A Quote Snapshot already exists for this quote.")])
	if await _order_count(db, quote_id) > 0:
		return _blocked(quote_id=quote_id, quote_code=quote_code, blockers=[_blocker(V6_SNAPSHOT_ORDER_EXISTS, "A linked order already exists for this quote.")])

	client_output = _client_output(quote_obj, commercial, line_items)
	now = datetime.now(timezone.utc).isoformat()
	template_code = (linkage or {}).get("template_code") or "TPL-VOLUMETRIC-LETTERS_v2"
	snapshot_payload = {
		"snapshot_version": QUOTE_SNAPSHOT_V2,
		"snapshot_kind": V6_QUOTE_SNAPSHOT_KIND,
		"quote": {
			"quote_id": int(getattr(quote_obj, "id", quote_id)),
			"quote_code": quote_code,
			"status_at_snapshot": status,
			"created_at": getattr(quote_obj, "created_at", None).isoformat() if getattr(quote_obj, "created_at", None) else None,
			"client_id": getattr(quote_obj, "client_id", None),
			"workspace_id": workspace_id_str,
			"intake_code": (linkage or {}).get("intake_code") or quote_intake_code,
		},
		"commercial": commercial,
		"line_items": line_items,
		"v6_linkage": {
			"workspace_id": workspace_id_str,
			"intake_code": (linkage or {}).get("intake_code") or quote_intake_code,
			"source_svg": (linkage or {}).get("source_svg"),
			"template_code": (linkage or {}).get("template_code"),
			"product_family": (linkage or {}).get("product_family") or "volumetric_letters",
			"product_truth_status": (linkage or {}).get("product_truth_status") or "runtime_product_truth_reference_unavailable",
			"pricing_source": (linkage or {}).get("pricing_source"),
			"no_v4_v2_commercial_truth": True,
			"frontend_preview_not_used": True,
		},
		"client_output": client_output,
		"internal_trace": {
			"pricing_input_trace": write_trace.get("pricing_input_trace"),
			"commercial_proposal_trace": write_trace.get("commercial_proposal_trace"),
			"internal_cost_trace_summary": write_trace.get("internal_cost_trace_summary"),
			"quote_write_trace": write_trace,
		},
		"gates": {
			"can_accept_quote": True,
			"can_create_order": False,
			"order_snapshot_required": True,
			"product_aggregate_created": False,
			"task_graph_created": False,
			"execution_plan_created": False,
		},
		"audit": {
			"created_by": created_by,
			"created_at": now,
			"source": "backend_quote_snapshot_v2_service",
			"immutable_after_create": True,
		},
	}
	quote_snapshot_v2 = _quote_snapshot_v2_payload(
		quote_obj=quote_obj,
		workspace_id=workspace_id_str,
		template_code=template_code,
		commercial=commercial,
		line_items=line_items,
		write_trace=write_trace,
		created_by=created_by,
		now=now,
	)
	content_hash = _snapshot_hash(snapshot_payload)
	snapshot = await _persist_snapshot(
		db,
		quote_obj=quote_obj,
		snapshot_payload=snapshot_payload,
		commercial=commercial,
		client_output=client_output,
		created_by=created_by,
		content_hash=content_hash,
		quote_snapshot_v2=quote_snapshot_v2,
	)

	return {
		"status": V6_QUOTE_SNAPSHOT_V2_CREATED,
		"quote_id": int(getattr(quote_obj, "id", quote_id)),
		"quote_code": quote_code,
		"snapshot_id": snapshot.id,
		"snapshot_code": snapshot.snapshot_code,
		"snapshot_version": QUOTE_SNAPSHOT_V2,
		"snapshot_kind": V6_QUOTE_SNAPSHOT_KIND,
		"content_hash": content_hash,
		"commercial": commercial,
		"line_items": line_items,
		"v6_linkage": snapshot_payload["v6_linkage"],
		"client_output": client_output,
		"internal_trace": snapshot_payload["internal_trace"],
		"blockers": [],
		"warnings": [],
		"can_accept_quote": True,
		"can_create_order": False,
		"order_snapshot_required": True,
		"quote_snapshot_created": True,
		"order_created": False,
		"product_aggregate_created": False,
		"task_graph_created": False,
		"execution_plan_created": False,
	}