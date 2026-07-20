"""Quote Snapshot V2 for backend-priced Intake V6 quotes.

Freezes canonical dual snapshot (7G + 7H) via QuoteSnapshotV2Service at snapshot time.
Validates persisted quote totals against live 7G authority — no synthetic CPP from quote lines.
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
from schemas.quote_snapshot_v2 import QUOTE_SNAPSHOT_V2_VERSION, QuoteSnapshotV2
from services.intake_v6_commercial_quote_service import INTAKE_V6_LINKAGE_JSON_KEY, intake_v6_linkage_code
from services.intake_v6_priced_quote_dry_run_service import (
	V6_OFFICIAL_COMMERCIAL_AUTHORITY,
	V6_PRICED_DRY_RUN_READY,
	V6_PRICED_DRY_RUN_SOURCE,
	build_intake_v6_priced_quote_dry_run,
	resolve_intake_v6_canonical_quote_input,
)
from services.quote_snapshot_v2_service import (
	FREEZE_ALLOWED_READINESS,
	HARD_BLOCKED_READINESS,
	QuoteSnapshotV2Service,
)
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
V6_SNAPSHOT_PRODUCT_TRUTH_NOT_CONFIRMED = "V6_SNAPSHOT_PRODUCT_TRUTH_NOT_CONFIRMED"
V6_SNAPSHOT_ALREADY_EXISTS = "V6_SNAPSHOT_ALREADY_EXISTS"
V6_SNAPSHOT_ORDER_EXISTS = "V6_SNAPSHOT_ORDER_EXISTS"
V6_SNAPSHOT_QUOTE_TERMINAL = "V6_SNAPSHOT_QUOTE_TERMINAL"
V6_SNAPSHOT_OPERATOR_CONFIRMATION_REQUIRED = "V6_SNAPSHOT_OPERATOR_CONFIRMATION_REQUIRED"
V6_SNAPSHOT_EXPECTED_TOTAL_MISMATCH = "V6_SNAPSHOT_EXPECTED_TOTAL_MISMATCH"
V6_SNAPSHOT_EXPECTED_HASH_MISMATCH = "V6_SNAPSHOT_EXPECTED_HASH_MISMATCH"
V6_SNAPSHOT_NOTES_INVALID = "V6_SNAPSHOT_NOTES_INVALID"
V6_SNAPSHOT_AMBIGUOUS_STATE = "V6_SNAPSHOT_AMBIGUOUS_STATE"
V6_SNAPSHOT_OFFER_SCOPE_INVALID = "V6_SNAPSHOT_OFFER_SCOPE_INVALID"
V6_SNAPSHOT_COMPONENT_SCOPE_MISSING = "V6_SNAPSHOT_COMPONENT_SCOPE_MISSING"
V6_SNAPSHOT_CANONICAL_COMPOSE_FAILED = "V6_SNAPSHOT_CANONICAL_COMPOSE_FAILED"
V6_SNAPSHOT_COMMERCIAL_AUTHORITY_BLOCKED = "V6_SNAPSHOT_COMMERCIAL_AUTHORITY_BLOCKED"
V6_SNAPSHOT_COMMERCIAL_TOTAL_MISMATCH = "V6_SNAPSHOT_COMMERCIAL_TOTAL_MISMATCH"
V6_SNAPSHOT_READINESS_BLOCKED = "V6_SNAPSHOT_READINESS_BLOCKED"
V6_SNAPSHOT_SYNTHETIC_CPP_FORBIDDEN = "V6_SNAPSHOT_SYNTHETIC_CPP_FORBIDDEN"
V6_SNAPSHOT_DRY_RUN_REPRICE_BLOCKED = "V6_SNAPSHOT_DRY_RUN_REPRICE_BLOCKED"

_SYNTHETIC_CPP_PRICING_RULE = "V6_BACKEND_PRICED_QUOTE_LINE"
_TERMINAL_STATUSES = frozenset({"accepted", "rejected", "expired", "converted", "ordered"})


def _blocker(code: str, message: str) -> dict[str, str]:
	return {"code": code, "message": message}


def _blocked(
	*,
	quote_id: int | None,
	quote_code: str | None = None,
	blockers: list[dict[str, str]],
	warnings: list[str] | None = None,
	readiness: str | None = None,
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
		"readiness": readiness,
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
		"notes": ["Preturile comerciale provin din 7G; costul intern din 7H — nu din linii de oferta sintetizate."],
		"generated_from": QUOTE_SNAPSHOT_V2,
	}


def _snapshot_hash(payload: dict[str, Any]) -> str:
	encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
	return hashlib.sha256(encoded).hexdigest()


def _apply_v6_commercial_first_readiness(snapshot: QuoteSnapshotV2) -> QuoteSnapshotV2:
	"""Commercial snapshot may freeze when 7G is ready even if 7H is blocked."""
	commercial = snapshot.commercial_price_proposal_snapshot
	if (
		snapshot.readiness == "blocked_missing_internal"
		and commercial.status != "blocked"
		and _positive(commercial.commercial_total) is not None
	):
		snapshot.readiness = "partial_with_owner_decisions"
		warning = "V6 commercial snapshot frozen with incomplete internal cost (7H blocked separately)."
		if warning not in snapshot.warnings_snapshot:
			snapshot.warnings_snapshot.append(warning)
	return snapshot


def _validate_canonical_snapshot(
	snapshot: QuoteSnapshotV2,
	*,
	quote_grand_total: float,
	quote_total_before_vat: float | None = None,
) -> list[dict[str, str]]:
	blockers: list[dict[str, str]] = []
	commercial = snapshot.commercial_price_proposal_snapshot

	if commercial.status == "blocked":
		blockers.append(
			_blocker(
				V6_SNAPSHOT_COMMERCIAL_AUTHORITY_BLOCKED,
				"7G commercial proposal is blocked; snapshot cannot claim official commercial truth.",
			)
		)

	for line in commercial.commercial_price_lines:
		if line.pricing_rule_code == _SYNTHETIC_CPP_PRICING_RULE:
			blockers.append(
				_blocker(
					V6_SNAPSHOT_SYNTHETIC_CPP_FORBIDDEN,
					"Synthetic CPP from quote-line reconstruction is forbidden for V6 snapshots.",
				)
			)
			break

	cpp_net = commercial.subtotal_commercial if commercial.subtotal_commercial is not None else commercial.commercial_total
	quote_net = quote_total_before_vat if quote_total_before_vat is not None else quote_grand_total
	if cpp_net is None or abs(_money(cpp_net) - _money(quote_net)) > 0.01:
		blockers.append(
			_blocker(
				V6_SNAPSHOT_COMMERCIAL_TOTAL_MISMATCH,
				"7G commercial subtotal does not match persisted quote commercial totals.",
			)
		)

	if snapshot.readiness in HARD_BLOCKED_READINESS:
		blockers.append(
			_blocker(
				V6_SNAPSHOT_READINESS_BLOCKED,
				f"Snapshot readiness {snapshot.readiness} is hard-blocked for V6 freeze.",
			)
		)
	elif snapshot.readiness not in FREEZE_ALLOWED_READINESS:
		blockers.append(
			_blocker(
				V6_SNAPSHOT_READINESS_BLOCKED,
				f"Snapshot readiness {snapshot.readiness} is not allowed for V6 freeze.",
			)
		)

	return blockers


def _enrich_v6_provenance(snapshot: QuoteSnapshotV2, *, write_trace: dict[str, Any]) -> None:
	from schemas.quote_snapshot_v2 import QuoteSnapshotProvenanceEntry

	snapshot.provenance.append(
		QuoteSnapshotProvenanceEntry(
			key="intake_v6_priced_quote_write_v1",
			source="intake_v6_priced_quote_write_service",
			detail=f"pricing_hash={write_trace.get('pricing_hash')}",
		)
	)
	snapshot.provenance.append(
		QuoteSnapshotProvenanceEntry(
			key="v6_official_commercial_authority",
			source="commercial_price_proposal_7g",
			detail=V6_OFFICIAL_COMMERCIAL_AUTHORITY,
		)
	)
	snapshot.provenance.append(
		QuoteSnapshotProvenanceEntry(
			key="no_order_no_execution_no_inventory",
			source="intake_v6_quote_snapshot_v2_service",
			detail="snapshot_only=true",
		)
	)
	snapshot.notes.extend(
		[
			"Quote Snapshot V2 frozen via canonical QuoteSnapshotV2Service compose (7G + 7H).",
			"Commercial total validated against persisted quote; no quote-line CPP synthesis.",
			"Does not create order, execution plan, execution tasks, inventory movement, or task aggregates.",
		]
	)


async def _snapshot_count(db: AsyncSession, quote_id: int) -> int:
	result = await db.execute(select(func.count(QuoteSnapshotV2Record.id)).where(QuoteSnapshotV2Record.quote_id == quote_id))
	return int(result.scalar() or 0)


async def _order_count(db: AsyncSession, quote_id: int) -> int:
	result = await db.execute(select(func.count(Orders.id)).where(Orders.quote_id == quote_id))
	return int(result.scalar() or 0)


async def _next_snapshot_number(db: AsyncSession) -> int:
	result = await db.execute(select(func.count(QuoteSnapshotV2Record.id)))
	return int(result.scalar() or 0) + 1


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
	now = datetime.now(timezone.utc)
	now_year = now.year
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
		readiness=quote_snapshot_v2.readiness,
		frozen_at=now,
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

	# Freeze requires non-stale ConfirmJobProductTruth with pinned bags (no live-draft race).
	from models.intake_v6_workspace import IntakeV6WorkspaceRecord
	from services.product_truth_job_confirm_service import (
		commercial_freeze_allowed,
		get_job_revision_metadata,
	)

	ws_result = await db.execute(
		select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id_str)
	)
	ws_record = ws_result.scalar_one_or_none()
	if ws_record is None:
		ws_result = await db.execute(
			select(IntakeV6WorkspaceRecord).where(
				IntakeV6WorkspaceRecord.workspace_code == workspace_id_str
			)
		)
		ws_record = ws_result.scalar_one_or_none()
	ws_payload: dict[str, Any] = {}
	if ws_record is not None:
		try:
			ws_payload = json.loads(ws_record.payload_json or "{}")
		except Exception:
			ws_payload = {}
		if not isinstance(ws_payload, dict):
			ws_payload = {}
	if not commercial_freeze_allowed(ws_payload):
		meta = get_job_revision_metadata(ws_payload) or {}
		return _blocked(
			quote_id=quote_id,
			quote_code=quote_code,
			blockers=[
				_blocker(
					V6_SNAPSHOT_PRODUCT_TRUTH_NOT_CONFIRMED,
					"Quote Snapshot V2 freeze requires a non-stale ConfirmJobProductTruth revision "
					f"(state={meta.get('confirmation_state') or 'unconfirmed'}).",
				)
			],
		)
	job_truth_meta = get_job_revision_metadata(ws_payload) or {}

	dry_run = await build_intake_v6_priced_quote_dry_run(db, workspace_id_str, pricing_mode="snapshot_v2")
	if dry_run.get("pricing_status") != V6_PRICED_DRY_RUN_READY:
		return _blocked(
			quote_id=quote_id,
			quote_code=quote_code,
			blockers=[
				_blocker(
					V6_SNAPSHOT_DRY_RUN_REPRICE_BLOCKED,
					"Live V6 dry-run is blocked; snapshot cannot freeze stale or unverified commercial truth.",
				),
				*[
					_blocker(str(b.get("code") or "DRY_RUN_BLOCKER"), str(b.get("message") or ""))
					for b in dry_run.get("blockers") or []
					if isinstance(b, dict)
				],
			],
			warnings=list(dry_run.get("warnings") or []),
		)
	dry_totals = dry_run.get("commercial_totals") if isinstance(dry_run.get("commercial_totals"), dict) else {}
	dry_gross = _positive(dry_totals.get("total_gross"))
	if dry_gross is None or abs(_money(dry_gross) - commercial["grand_total"]) > 0.01:
		return _blocked(
			quote_id=quote_id,
			quote_code=quote_code,
			blockers=[
				_blocker(
					V6_SNAPSHOT_COMMERCIAL_TOTAL_MISMATCH,
					"Live 7G dry-run gross does not match persisted quote grand total.",
				)
			],
		)

	resolved = await resolve_intake_v6_canonical_quote_input(db, workspace_id_str)
	if resolved is None:
		return _blocked(
			quote_id=quote_id,
			quote_code=quote_code,
			blockers=[_blocker(V6_SNAPSHOT_CANONICAL_COMPOSE_FAILED, "V6 canonical quote_input could not be resolved.")],
		)
	template_code, quote_input = resolved

	canonical_service = QuoteSnapshotV2Service(db)
	quote_snapshot_v2 = await canonical_service.build_preview(
		template_code,
		workspace_id=workspace_id_str,
		quote_id=str(quote_id),
		quote_input=quote_input,
		currency=commercial["currency"],
		requested_by=created_by,
	)
	if quote_snapshot_v2 is None:
		return _blocked(
			quote_id=quote_id,
			quote_code=quote_code,
			blockers=[_blocker(V6_SNAPSHOT_CANONICAL_COMPOSE_FAILED, "Canonical Quote Snapshot V2 preview could not be composed.")],
		)

	if quote_snapshot_v2.offer_scope_snapshot and quote_snapshot_v2.offer_scope_snapshot.validation_errors:
		return _blocked(
			quote_id=quote_id,
			quote_code=quote_code,
			blockers=[
				_blocker(
					V6_SNAPSHOT_OFFER_SCOPE_INVALID,
					"Invalid offer_scope cannot be frozen into Quote Snapshot V2.",
				)
			],
			warnings=list(quote_snapshot_v2.offer_scope_snapshot.validation_errors),
		)

	quote_snapshot_v2 = _apply_v6_commercial_first_readiness(quote_snapshot_v2)
	validation_blockers = _validate_canonical_snapshot(
		quote_snapshot_v2,
		quote_grand_total=commercial["grand_total"],
		quote_total_before_vat=commercial["total_before_vat"],
	)
	if validation_blockers:
		return _blocked(
			quote_id=quote_id,
			quote_code=quote_code,
			blockers=validation_blockers,
			warnings=list(quote_snapshot_v2.warnings_snapshot),
			readiness=quote_snapshot_v2.readiness,
		)

	quote_snapshot_v2.frozen_at = now
	quote_snapshot_v2.frozen_by = created_by
	quote_snapshot_v2.persist_status = "persisted"
	_enrich_v6_provenance(quote_snapshot_v2, write_trace=write_trace)

	can_accept = quote_snapshot_v2.readiness in FREEZE_ALLOWED_READINESS

	snapshot_payload = {
		"snapshot_version": QUOTE_SNAPSHOT_V2,
		"snapshot_kind": V6_QUOTE_SNAPSHOT_KIND,
		"readiness": quote_snapshot_v2.readiness,
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
			"product_truth_status": "confirmed_job_revision",
			"product_truth_revision": job_truth_meta.get("revision"),
			"product_truth_content_hash": job_truth_meta.get("content_hash"),
			"product_truth_confirmed_at": job_truth_meta.get("confirmed_at"),
			"root_template_code": job_truth_meta.get("root_template_code"),
			"pricing_source": (linkage or {}).get("pricing_source"),
			"no_v4_v2_commercial_truth": True,
			"frontend_preview_not_used": True,
			"freeze_from_pinned_product_truth": True,
		},
		"client_output": client_output,
		"internal_trace": {
			"pricing_input_trace": write_trace.get("pricing_input_trace"),
			"commercial_proposal_trace": write_trace.get("commercial_proposal_trace"),
			"internal_cost_trace_summary": write_trace.get("internal_cost_trace_summary"),
			"quote_write_trace": write_trace,
			"estimated_internal_cost_snapshot_status": quote_snapshot_v2.estimated_internal_cost_snapshot.status,
			"commercial_price_proposal_snapshot_status": quote_snapshot_v2.commercial_price_proposal_snapshot.status,
		},
		"gates": {
			"can_accept_quote": can_accept,
			"can_create_order": False,
			"order_snapshot_required": True,
			"product_aggregate_created": False,
			"task_graph_created": False,
			"execution_plan_created": False,
		},
		"audit": {
			"created_by": created_by,
			"created_at": now,
			"source": "intake_v6_quote_snapshot_v2_service",
			"canonical_compose": "quote_snapshot_v2_service",
			"immutable_after_create": True,
		},
	}
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
		"readiness": quote_snapshot_v2.readiness,
		"content_hash": content_hash,
		"commercial": commercial,
		"line_items": line_items,
		"v6_linkage": snapshot_payload["v6_linkage"],
		"client_output": client_output,
		"internal_trace": snapshot_payload["internal_trace"],
		"blockers": list(quote_snapshot_v2.blockers_snapshot),
		"warnings": list(quote_snapshot_v2.warnings_snapshot),
		"can_accept_quote": can_accept,
		"can_create_order": False,
		"order_snapshot_required": True,
		"quote_snapshot_created": True,
		"order_created": False,
		"product_aggregate_created": False,
		"task_graph_created": False,
		"execution_plan_created": False,
	}
