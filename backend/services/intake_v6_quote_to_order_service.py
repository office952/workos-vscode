"""Intake V6 quote-to-order commercial spine service namespace."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from data_models.product_contracts import iso_now
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quote_snapshot_v2 import QuoteSnapshotV2Record
from models.quotes import Quotes
from schemas.quote_snapshot_v2 import QuoteSnapshotV2
from schemas.auth import UserResponse
from services.company_commercial_settings_service import get_eur_to_ron_rate
from services.intake_v3_guarded_convert_to_order_service import (
    IV3_ORDER_STATUS_LOCKED,
    check_existing_order_for_iv3_quote,
)
from services.intake_v3_quote_linkage_utils import (
    ACCEPT_DECISION_JSON_KEY,
    CONVERT_DECISION_JSON_KEY,
    PRICING_REVIEW_JSON_KEY,
    get_pricing_review_record,
    is_pricing_review_completed,
)
from services.intake_v4_quote_to_order_service import (
    ALLOWED_CURRENCIES,
    INTERMEDIATE_PRICED_STATUS,
    TERMINAL_QUOTE_STATUSES,
    _collect_accept_critical_blockers,
    _extract_commercial_totals_from_quote,
    _final_price_present,
    _reject_client_supplied_totals,
    _validate_quote_priced_totals,
    build_v4_pricing_review_record,
    quote_commercial_totals_summary,
)
from services.intake_v4_quote_linkage_utils import (
    OWNER_APPROVAL_JSON_KEY,
    V4_ACCEPTED_STATUS,
    is_v4_accept_completed,
    is_v4_convert_completed,
    is_v4_owner_approval_valid,
    linkage_workspace_id,
    snapshot_analysis_hash_from_linkage,
    template_code_from_linkage,
)
from services.intake_v6_commercial_quote_service import (
    INTAKE_V6_LINKAGE_JSON_KEY,
    check_existing_quote_for_intake_v6_workspace,
    parse_intake_v6_linkage_from_notes,
)
from services.intake_v6_material_breakdown_service import get_material_breakdown_for_workspace
from services.intake_v6_production_handoff_preview_service import build_intake_v6_production_handoff_preview
from services.intake_v6_snapshot_authoritative_offer_service import (
    INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY,
    V6_SNAPSHOT_OFFER_PRICING_SOURCE,
)
from services.intake_v6_workspace_service import _get_record_or_404, _json_loads, _parse_payload
from services.order_execution_snapshot_mapper import resolve_canonical_task_type
from services.order_currency_conversion_service import convert_quote_totals_to_order_base
from services.orders import OrdersService
from services.quotes import QuotesService
from services.order_snapshot_v2_convert_service import convert_accepted_quote_snapshot_v2_to_order
from services.quote_snapshot_v2_accept_gate_service import (
    build_accept_snapshot_metadata,
    resolve_snapshot_for_accept,
    validate_snapshot_for_accept,
)
from validators.status_lifecycle import validate_transition


INTAKE_V6_SOURCE_MODULE = "intake_v6"
INTAKE_V6_ORDER_LINKAGE_JSON_KEY = "intake_v6_order_linkage_v1"


def _raise_blocked(error: str, message: str, blockers: list[str] | None = None) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "error": error,
            "message": message,
            "blockers": blockers or [error],
        },
    )


def _require_v6_linkage(quote: Quotes) -> dict[str, Any]:
    if not _is_v6_quote(quote):
        _raise_blocked("NOT_IV6_QUOTE", "Quote intake_code is not an Intake V6 linkage code.")
    linkage = parse_intake_v6_linkage_from_notes(quote.notes)
    if linkage is None:
        _raise_blocked("NOT_IV6_QUOTE", "Quote is not linked to Intake V6.")
    return linkage


async def _load_workspace_for_linkage(db: AsyncSession, linkage: dict[str, Any]):
    workspace_id = linkage_workspace_id(linkage)
    if not workspace_id:
        _raise_blocked("WORKSPACE_ID_MISSING", "Intake V6 linkage is missing source_workspace_id.")
    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    payload = _parse_payload(payload_raw)
    return record, payload, payload_raw


def _assert_analysis_hash_sync(linkage: dict[str, Any], workspace_hash: str | None, *, context: str) -> None:
    snap_hash = snapshot_analysis_hash_from_linkage(linkage)
    if workspace_hash and snap_hash and workspace_hash != snap_hash:
        _raise_blocked(
            "ANALYSIS_HASH_MISMATCH",
            f"Workspace analysis hash differs from quote snapshot ({context}).",
            ["analysis_hash_mismatch"],
        )


def _update_linkage_in_notes(notes: str | None, linkage: dict[str, Any]) -> str:
    payload: dict[str, Any]
    if not notes:
        payload = {}
    else:
        try:
            parsed = json.loads(notes)
        except json.JSONDecodeError:
            parsed = {}
        payload = parsed if isinstance(parsed, dict) else {}
    payload[INTAKE_V6_LINKAGE_JSON_KEY] = linkage
    return json.dumps(payload, default=str)


def _extract_v6_order_linkage_from_order(order: Orders) -> dict[str, Any] | None:
    for raw in (getattr(order, "notes", None), getattr(order, "snapshot_line_items", None)):
        if not raw or not str(raw).strip():
            continue
        try:
            parsed = json.loads(raw)
        except Exception:
            continue
        if not isinstance(parsed, dict):
            continue
        linkage = parsed.get(INTAKE_V6_ORDER_LINKAGE_JSON_KEY)
        if isinstance(linkage, dict):
            return linkage
    return None


def _extract_quote_snapshot_for_order(quote: Quotes) -> dict[str, Any] | None:
    raw = getattr(quote, "line_items", None)
    if not raw or not str(raw).strip():
        return None
    try:
        parsed = json.loads(raw)
    except Exception:
        return None

    if not isinstance(parsed, dict):
        return None

    candidate = parsed.get("line_items") if isinstance(parsed.get("line_items"), dict) else parsed
    if not isinstance(candidate, dict):
        return None
    if "product_definition" not in candidate:
        return None
    if not any(key in candidate for key in ("cost_result", "pricing", "price")):
        return None
    return candidate


def _normalize_snapshot_process_types_for_execution(snapshot: dict[str, Any]) -> dict[str, Any]:
    product_definition = snapshot.get("product_definition")
    if not isinstance(product_definition, dict):
        return snapshot

    layers = product_definition.get("layers")
    if not isinstance(layers, list):
        return snapshot

    normalized_snapshot = dict(snapshot)
    normalized_product_definition = dict(product_definition)
    normalized_layers: list[Any] = []
    changed = False

    for layer in layers:
        if not isinstance(layer, dict):
            normalized_layers.append(layer)
            continue
        processes = layer.get("processes")
        if not isinstance(processes, list):
            normalized_layers.append(layer)
            continue

        normalized_processes: list[Any] = []
        layer_changed = False
        for process in processes:
            if not isinstance(process, dict):
                normalized_processes.append(process)
                continue
            canonical = resolve_canonical_task_type(
                process_id=str(process.get("process_id") or ""),
                legacy_type=str(process.get("type") or ""),
            )
            if canonical and canonical != process.get("type"):
                patched_process = dict(process)
                patched_process["type"] = canonical
                normalized_processes.append(patched_process)
                layer_changed = True
                changed = True
            else:
                normalized_processes.append(process)

        if layer_changed:
            patched_layer = dict(layer)
            patched_layer["processes"] = normalized_processes
            normalized_layers.append(patched_layer)
        else:
            normalized_layers.append(layer)

    if changed:
        normalized_product_definition["layers"] = normalized_layers
        normalized_snapshot["product_definition"] = normalized_product_definition
        return normalized_snapshot
    return snapshot


async def _build_v6_order_financial_snapshot(
    db: AsyncSession,
    quote: Quotes,
    linkage: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    pricing_review = get_pricing_review_record(linkage) or {}
    currency = str(pricing_review.get("currency") or "EUR")
    gross_total = float(quote.grand_total or pricing_review.get("total") or 0)
    net_total = float(pricing_review.get("subtotal") or quote.total_before_vat or gross_total)
    if gross_total <= 0:
        _raise_blocked("FINAL_PRICE_MISSING", "Final commercial price is not present on the quote.")

    try:
        eur_to_ron_rate = await get_eur_to_ron_rate(db)
        currency_handoff = convert_quote_totals_to_order_base(
            gross_amount=gross_total,
            net_amount=net_total,
            source_currency=currency,
            eur_to_ron_rate=eur_to_ron_rate,
        )
    except ValueError as exc:
        _raise_blocked("CURRENCY_CONVERSION_FAILED", str(exc))

    final_price = {
        "net": currency_handoff.base_total_net if currency_handoff.base_total_net is not None else net_total,
        "gross": currency_handoff.base_total_ron,
        "commercial_currency": currency_handoff.commercial_currency,
    }
    return currency_handoff.to_dict(), final_price


async def _resolve_snapshot_for_v6_pricing_review(
    db: AsyncSession,
    quote: Quotes,
    linkage: dict[str, Any],
) -> QuoteSnapshotV2Record | None:
    """Latest frozen Quote Snapshot V2 for IV6 pricing review handoff."""
    workspace_id = linkage_workspace_id(linkage)
    query = (
        select(QuoteSnapshotV2Record)
        .where(
            QuoteSnapshotV2Record.quote_id == quote.id,
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


def _snapshot_state(record: QuoteSnapshotV2Record | None) -> dict[str, Any]:
    return {
        "exists": record is not None,
        "snapshot_id": record.id if record is not None else None,
        "snapshot_code": record.snapshot_code if record is not None else None,
        "status": record.status if record is not None else None,
        "readiness": record.readiness if record is not None else None,
        "accept_allowed": record is not None and record.status == "frozen" and record.readiness in {"ready_for_owner_review", "partial_with_owner_decisions"},
    }


def _extract_commercial_totals_from_snapshot_v2_record(
    record: QuoteSnapshotV2Record,
) -> dict[str, Any]:
    """Read canonical commercial total from persisted snapshot JSON — no live pricing."""
    try:
        parsed = QuoteSnapshotV2.model_validate_json(record.snapshot_json)
    except Exception as exc:
        _raise_blocked(
            "SNAPSHOT_V2_INVALID",
            f"Quote Snapshot V2 JSON invalid: {exc}",
            ["snapshot_v2_invalid"],
        )
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
    currency = (cpp.currency or "RON").strip().upper()
    if currency not in ALLOWED_CURRENCIES:
        currency = "RON"
    total = float(commercial_total)
    return {
        "subtotal": total,
        "discount_amount": 0.0,
        "vat_percent": 0.0,
        "vat_amount": 0.0,
        "total": total,
        "net_before_vat": total,
        "currency": currency,
        "pricing_totals_source": "quote_snapshot_v2",
        "pricing_totals_captured": True,
        "snapshot_v2_id": record.id,
        "snapshot_code": record.snapshot_code,
    }


async def _extract_v6_pricing_review_totals(
    db: AsyncSession,
    quote: Quotes,
    linkage: dict[str, Any],
) -> dict[str, Any]:
    """Quote columns first; IV6 handoff may use frozen Quote Snapshot V2 commercial total."""
    if float(quote.grand_total or 0) > 0:
        return _extract_commercial_totals_from_quote(quote)
    snapshot_record = await _resolve_snapshot_for_v6_pricing_review(db, quote, linkage)
    if snapshot_record is None:
        _raise_blocked(
            "QUOTE_NOT_PRICED",
            (
                "Quote has no commercial totals — write the official V6 backend totals on the quote "
                "or freeze a Quote Snapshot V2 with commercial total before completing pricing review."
            ),
            ["QUOTE_NOT_PRICED"],
        )
    return _extract_commercial_totals_from_snapshot_v2_record(snapshot_record)


def _build_v6_pricing_review_record(
    quote: Quotes,
    linkage: dict[str, Any],
    totals: dict[str, Any],
    body: dict[str, Any],
    current_user: UserResponse,
    *,
    workspace_id: str,
    analysis_hash: str | None,
) -> dict[str, Any]:
    record = build_v4_pricing_review_record(
        quote,
        linkage,
        totals,
        body,
        current_user,
        workspace_id=workspace_id,
        analysis_hash=analysis_hash,
    )
    record["source"] = INTAKE_V6_SOURCE_MODULE
    return record


async def complete_v6_pricing_review(
    db: AsyncSession,
    quote_id: int,
    body: dict[str, Any],
    current_user: UserResponse,
) -> dict[str, Any]:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        _raise_blocked("QUOTE_NOT_FOUND", f"Quote id={quote_id} was not found.")
    linkage = _require_v6_linkage(quote)

    if quote.status in TERMINAL_QUOTE_STATUSES:
        _raise_blocked("QUOTE_TERMINAL", f"Quote status {quote.status!r} cannot complete pricing review.")
    if is_pricing_review_completed(linkage):
        _raise_blocked("PRICING_REVIEW_ALREADY_COMPLETED", "Pricing review already completed.")
    if not all(
        (
            body.get("reviewer_confirmation"),
            body.get("confirm_quote_stays_draft"),
            body.get("confirm_no_order"),
            body.get("confirm_no_execution"),
            body.get("confirm_no_inventory"),
        )
    ):
        _raise_blocked("CONFIRMATIONS_REQUIRED", "All reviewer confirmations must be true.")
    if not str(body.get("pricing_review_reason") or "").strip():
        _raise_blocked("PRICING_REVIEW_REASON_REQUIRED", "pricing_review_reason is required.")

    _reject_client_supplied_totals(body)
    snapshot_record = await _resolve_snapshot_for_v6_pricing_review(db, quote, linkage)
    if snapshot_record is None:
        _raise_blocked(
            "MISSING_SNAPSHOT_V2",
            "Creeaza Snapshot V2 inainte de Review si Accept.",
            ["missing_active_snapshot"],
        )
    quote_totals = await _extract_v6_pricing_review_totals(db, quote, linkage)
    _validate_quote_priced_totals(quote_totals)

    if body.get("expected_quote_id") is not None and int(body["expected_quote_id"]) != quote.id:
        _raise_blocked("QUOTE_ID_MISMATCH", "expected_quote_id does not match quote.")
    if body.get("expected_intake_code") and body["expected_intake_code"] != quote.intake_code:
        _raise_blocked("INTAKE_CODE_MISMATCH", "expected_intake_code does not match quote.")

    record, payload, _payload_raw = await _load_workspace_for_linkage(db, linkage)
    workspace_hash = _workspace_analysis_hash_from_payload(payload)
    client_hash = body.get("client_analysis_hash")
    if client_hash and workspace_hash and client_hash != workspace_hash:
        _raise_blocked("ANALYSIS_HASH_MISMATCH", "client_analysis_hash does not match workspace.", ["analysis_hash_mismatch"])

    orders_before = await db.scalar(select(func.count()).select_from(Orders))
    plans_before = await db.scalar(select(func.count()).select_from(ExecutionPlan))

    pricing_record = _build_v6_pricing_review_record(
        quote,
        linkage,
        quote_totals,
        body,
        current_user,
        workspace_id=record.id,
        analysis_hash=workspace_hash,
    )
    linkage = dict(linkage)
    linkage["requires_pricing_review"] = False
    linkage["priced_draft"] = True
    linkage[PRICING_REVIEW_JSON_KEY] = pricing_record
    updated_notes = _update_linkage_in_notes(quote.notes, linkage)

    updated = await quotes_service.update(quote.id, {"status": "draft", "notes": updated_notes})
    if updated is None:
        _raise_blocked("QUOTE_UPDATE_FAILED", "Failed to persist pricing review.")

    orders_after = await db.scalar(select(func.count()).select_from(Orders))
    plans_after = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    if orders_after != orders_before or plans_after != plans_before:
        _raise_blocked("SAFETY_VIOLATION", "Unexpected order or execution side effect during pricing review.")

    return {
        "pricing_review_completed": True,
        "quote_id": updated.id,
        "quote_code": updated.code,
        "quote_status": updated.status,
        "requires_pricing_review": False,
        "pricing_review": pricing_record,
        "pricing_totals_source": quote_totals.get("pricing_totals_source"),
        "creates_execution_tasks": False,
        "writes_execution_plan": False,
        "stock_consumption": False,
    }


async def persist_v6_owner_approval(
    db: AsyncSession,
    quote_id: int,
    body: dict[str, Any],
    current_user: UserResponse,
) -> dict[str, Any]:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        _raise_blocked("QUOTE_NOT_FOUND", f"Quote id={quote_id} was not found.")
    linkage = _require_v6_linkage(quote)

    if not all((body.get("acknowledged_no_execution_tasks"), body.get("acknowledged_no_stock_consumption"))):
        _raise_blocked("CONFIRMATIONS_REQUIRED", "Owner must acknowledge no execution tasks and no stock consumption.")
    if not str(body.get("decision_reason") or "").strip():
        _raise_blocked("DECISION_REASON_REQUIRED", "decision_reason is required.")

    record, payload, _payload_raw = await _load_workspace_for_linkage(db, linkage)
    workspace_hash = _workspace_analysis_hash_from_payload(payload)
    client_hash = body.get("client_analysis_hash")
    if client_hash and workspace_hash and client_hash != workspace_hash:
        _raise_blocked("ANALYSIS_HASH_MISMATCH", "client_analysis_hash does not match workspace.", ["analysis_hash_mismatch"])

    orders_before = await db.scalar(select(func.count()).select_from(Orders))
    plans_before = await db.scalar(select(func.count()).select_from(ExecutionPlan))

    approval_record = {
        "approved": True,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "approved_by_user_id": current_user.id,
        "approved_by_display_name": current_user.name or current_user.email,
        "approval_scope": "intake_v6_quote_to_order",
        "analysis_hash": workspace_hash,
        "acknowledged_blockers": list(body.get("acknowledged_blockers") or []),
        "acknowledged_warnings": list(body.get("acknowledged_warnings") or []),
        "acknowledged_no_execution_tasks": True,
        "acknowledged_no_stock_consumption": True,
        "decision_reason": str(body.get("decision_reason") or "").strip(),
        "source": INTAKE_V6_SOURCE_MODULE,
        "quote_id": quote.id,
        "workspace_id": record.id,
    }
    linkage = dict(linkage)
    linkage[OWNER_APPROVAL_JSON_KEY] = approval_record
    updated_notes = _update_linkage_in_notes(quote.notes, linkage)
    updated = await quotes_service.update(quote.id, {"notes": updated_notes})
    if updated is None:
        _raise_blocked("QUOTE_UPDATE_FAILED", "Failed to persist owner approval.")

    orders_after = await db.scalar(select(func.count()).select_from(Orders))
    plans_after = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    if orders_after != orders_before or plans_after != plans_before:
        _raise_blocked("SAFETY_VIOLATION", "Unexpected order or execution side effect during owner approval.")

    exists, valid, stale = is_v4_owner_approval_valid(linkage, workspace_hash)
    return {
        "owner_approval_persisted": True,
        "quote_id": quote.id,
        "owner_approval": approval_record,
        "owner_approval_exists": exists,
        "owner_approval_valid": valid,
        "owner_approval_stale": stale,
        "creates_execution_tasks": False,
        "writes_execution_plan": False,
    }


async def accept_v6_quote(
    db: AsyncSession,
    quote_id: int,
    body: dict[str, Any],
    current_user: UserResponse,
) -> dict[str, Any]:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        _raise_blocked("QUOTE_NOT_FOUND", f"Quote id={quote_id} was not found.")
    linkage = _require_v6_linkage(quote)

    if is_v4_accept_completed(linkage, quote.status):
        _raise_blocked("ACCEPT_ALREADY_COMPLETED", "Quote already accepted.")
    if quote.status in TERMINAL_QUOTE_STATUSES:
        _raise_blocked("QUOTE_TERMINAL", f"Quote status {quote.status!r} cannot be accepted.")
    if bool(linkage.get("requires_pricing_review", True)) or not is_pricing_review_completed(linkage):
        _raise_blocked("PRICING_REVIEW_REQUIRED", "Pricing review must be completed before accept.")

    record, payload, payload_raw = await _load_workspace_for_linkage(db, linkage)
    workspace_hash = _workspace_analysis_hash_from_payload(payload)
    _assert_analysis_hash_sync(linkage, workspace_hash, context="accept")

    exists, valid, stale = is_v4_owner_approval_valid(linkage, workspace_hash)
    if not exists:
        _raise_blocked("OWNER_APPROVAL_MISSING", "Owner approval is required before accept.")
    if stale or not valid:
        _raise_blocked("OWNER_APPROVAL_STALE", "Owner approval is stale — re-approve after workspace changes.")

    snapshot_record = await resolve_snapshot_for_accept(db, quote, linkage)
    if snapshot_record is None:
        _raise_blocked(
            "MISSING_SNAPSHOT_V2",
            "A persisted Quote Snapshot V2 is required before accept.",
            ["missing_active_snapshot"],
        )

    gate_result = validate_snapshot_for_accept(
        snapshot_record,
        quote_id=quote.id,
        workspace_id=linkage_workspace_id(linkage),
        confirm_owner_decisions_acknowledged=bool(
            body.get("confirm_owner_decisions_acknowledged")
        ),
    )
    if not gate_result.accept_allowed:
        _raise_blocked(
            gate_result.error_code or "SNAPSHOT_ACCEPT_BLOCKED",
            gate_result.message or "Quote Snapshot V2 accept gate blocked.",
            gate_result.blockers or [gate_result.gate_status],
        )

    critical = await _collect_accept_critical_blockers(db, record, payload, payload_raw, record.id)
    if critical:
        _raise_blocked("READINESS_BLOCKERS", "Quote cannot be accepted while workspace has critical readiness blockers.", critical)

    if not all(
        (
            body.get("reviewer_confirmation"),
            body.get("confirm_pricing_review_completed"),
            body.get("confirm_no_order"),
            body.get("confirm_no_execution"),
            body.get("confirm_no_inventory"),
            body.get("confirm_convert_separate"),
        )
    ):
        _raise_blocked("CONFIRMATIONS_REQUIRED", "All accept confirmations must be true.")

    orders_before = await db.scalar(select(func.count()).select_from(Orders))
    plans_before = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    quote_status_before = quote.status
    accept_record = {
        "status": "approved",
        "accepted_at": datetime.now(timezone.utc).isoformat(),
        "accepted_by_user_id": current_user.id,
        "accepted_by_display_name": current_user.name or current_user.email,
        "reason": str(body.get("accept_reason") or "").strip(),
        "source": INTAKE_V6_SOURCE_MODULE,
        "analysis_hash": workspace_hash,
        "snapshot_hash": snapshot_analysis_hash_from_linkage(linkage),
        "approved_owner_approval_reference": linkage.get(OWNER_APPROVAL_JSON_KEY),
        "pricing_review_completed": True,
        "quote_status_before": quote_status_before,
        "quote_status_after": V4_ACCEPTED_STATUS,
        "order_created": False,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "snapshot_v2": build_accept_snapshot_metadata(snapshot_record, gate_result),
    }
    linkage = dict(linkage)
    linkage[ACCEPT_DECISION_JSON_KEY] = accept_record
    updated_notes = _update_linkage_in_notes(quote.notes, linkage)

    working_quote = quote
    if quote_status_before == "draft":
        intermediate = await quotes_service.update(quote.id, {"status": INTERMEDIATE_PRICED_STATUS})
        if intermediate is None:
            _raise_blocked("QUOTE_UPDATE_FAILED", "Failed to set intermediate priced status.")
        working_quote = intermediate

    validate_transition("quotes", working_quote.status, V4_ACCEPTED_STATUS)
    updated = await quotes_service.update(
        quote.id,
        {
            "status": V4_ACCEPTED_STATUS,
            "notes": updated_notes,
            "accepted_snapshot_v2_id": snapshot_record.id,
        },
    )
    if updated is None:
        _raise_blocked("QUOTE_UPDATE_FAILED", "Quote update failed after accept.")

    orders_after = await db.scalar(select(func.count()).select_from(Orders))
    plans_after = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    if orders_after != orders_before or plans_after != plans_before:
        _raise_blocked("SAFETY_VIOLATION", "Unexpected order or execution side effect during accept.")

    return {
        "accepted": True,
        "quote_id": updated.id,
        "quote_code": updated.code,
        "quote_status": updated.status,
        "quote_status_before": quote_status_before,
        "accept_decision": accept_record,
        "order_created": False,
        "execution_plan_created": False,
        "creates_execution_tasks": False,
        "writes_execution_plan": False,
    }


async def _build_v6_handoff_snapshots(db: AsyncSession, workspace_id: str, payload_raw: dict[str, Any], payload) -> dict[str, Any]:
    snapshots: dict[str, Any] = {}
    try:
        breakdown = await get_material_breakdown_for_workspace(db, workspace_id)
        snapshots["material_breakdown_snapshot"] = breakdown.model_dump(mode="json")
    except Exception as exc:
        snapshots["material_breakdown_snapshot"] = {"error": str(exc), "captured": False}
    try:
        handoff = await build_intake_v6_production_handoff_preview(db, workspace_id, payload_raw, payload)
        snapshots["production_handoff_preview_snapshot"] = handoff.model_dump(mode="json")
    except Exception as exc:
        snapshots["production_handoff_preview_snapshot"] = {"error": str(exc), "captured": False}
    try:
        dry_run = await build_intake_v6_task_generation_dry_run(db, workspace_id, payload_raw, payload)
        snapshots["task_generation_dry_run_snapshot"] = {
            "summary": dry_run.summary,
            "task_candidates_count": len(dry_run.task_candidates),
            "idempotency_entries_count": len(dry_run.idempotency_plan),
            "can_generate_tasks": dry_run.can_generate_tasks,
        }
    except Exception as exc:
        snapshots["task_generation_dry_run_snapshot"] = {"error": str(exc), "captured": False}
    return snapshots


def _build_v6_order_snapshot_payload(
    quote: Quotes,
    linkage: dict[str, Any],
    *,
    currency_handoff: dict[str, Any],
    final_price: dict[str, Any],
    handoff_snapshots: dict[str, Any],
    workspace_hash: str | None,
) -> dict[str, Any]:
    workspace_id = linkage_workspace_id(linkage)
    snapshot = linkage.get("snapshot") if isinstance(linkage.get("snapshot"), dict) else {}
    quote_snapshot = _extract_quote_snapshot_for_order(quote)
    if not isinstance(quote_snapshot, dict):
        _raise_blocked(
            "QUOTE_SNAPSHOT_MISSING",
            "Quote line_items do not contain the canonical priced snapshot required for order conversion.",
            ["QUOTE_SNAPSHOT_MISSING"],
        )

    order_snapshot = _normalize_snapshot_process_types_for_execution(dict(quote_snapshot))
    order_linkage = {
        "source_module": INTAKE_V6_SOURCE_MODULE,
        "source_intake_version": "V6",
        "source_quote_id": quote.id,
        "source_workspace_id": workspace_id,
        "quote_intake_code": quote.intake_code,
        "quote_code": quote.code,
        "analysis_hash": workspace_hash or snapshot_analysis_hash_from_linkage(linkage),
        "template_code": template_code_from_linkage(linkage),
        "created_from_intake_v6": True,
        "no_execution_plan_created": True,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "production_started": False,
    }
    order_snapshot["source_module"] = INTAKE_V6_SOURCE_MODULE
    order_snapshot["source_intake_version"] = "V6"
    order_snapshot["snapshot_type"] = "intake_v6_guarded_convert_order_snapshot_v1"
    order_snapshot[INTAKE_V6_ORDER_LINKAGE_JSON_KEY] = order_linkage
    order_snapshot["source_workspace_id"] = workspace_id
    order_snapshot["source_quote_id"] = quote.id
    order_snapshot["analysis_hash"] = workspace_hash or snapshot_analysis_hash_from_linkage(linkage)
    order_snapshot["template_code"] = template_code_from_linkage(linkage)
    order_snapshot["workspace_payload_snapshot"] = snapshot.get("workspace_payload_snapshot")
    order_snapshot["quote_input_payload"] = snapshot.get("quote_input_payload") or linkage.get("quote_input_payload")
    order_snapshot["owner_approval_snapshot"] = linkage.get(OWNER_APPROVAL_JSON_KEY)
    order_snapshot["pricing_review_snapshot"] = linkage.get(PRICING_REVIEW_JSON_KEY)
    order_snapshot["accept_decision_snapshot"] = linkage.get(ACCEPT_DECISION_JSON_KEY)
    order_snapshot["commercial_line_items"] = json.loads(quote.line_items) if quote.line_items else []
    order_snapshot["final_price"] = final_price
    order_snapshot["commercial_currency_handoff"] = currency_handoff
    order_snapshot["handoff_snapshots"] = handoff_snapshots
    order_snapshot["no_execution_plan_created"] = True
    order_snapshot["execution_plan_created"] = False
    order_snapshot["execution_task_created"] = False
    order_snapshot["inventory_mutated"] = False
    order_snapshot["production_started"] = False
    order_snapshot["created_from"] = INTAKE_V6_SOURCE_MODULE
    return order_snapshot


async def convert_v6_quote_to_order(
    db: AsyncSession,
    quote_id: int,
    body: dict[str, Any],
    current_user: UserResponse,
) -> dict[str, Any]:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        _raise_blocked("QUOTE_NOT_FOUND", f"Quote id={quote_id} was not found.")
    linkage = _require_v6_linkage(quote)

    if getattr(quote, "accepted_snapshot_v2_id", None):
        return await convert_accepted_quote_snapshot_v2_to_order(
            db,
            quote_id,
            body,
            current_user,
        )

    existing_order = await check_existing_order_for_iv3_quote(db, quote_id)
    if existing_order is not None or is_v4_convert_completed(linkage):
        _raise_blocked("ORDER_ALREADY_EXISTS", f"An order already exists for quote id={quote.id}.", ["ORDER_ALREADY_EXISTS"])
    if not is_v4_accept_completed(linkage, quote.status) or quote.status != V4_ACCEPTED_STATUS:
        _raise_blocked("QUOTE_NOT_ACCEPTED", "Quote must be accepted before convert.")
    if bool(linkage.get("requires_pricing_review", True)) or not is_pricing_review_completed(linkage):
        _raise_blocked("PRICING_REVIEW_REQUIRED", "Pricing review must be completed before convert.")

    record, payload, payload_raw = await _load_workspace_for_linkage(db, linkage)
    workspace_hash = _workspace_analysis_hash_from_payload(payload)
    _assert_analysis_hash_sync(linkage, workspace_hash, context="convert")

    exists, valid, stale = is_v4_owner_approval_valid(linkage, workspace_hash)
    if not exists:
        _raise_blocked("OWNER_APPROVAL_MISSING", "Owner approval is required before convert.")
    if stale or not valid:
        _raise_blocked("OWNER_APPROVAL_STALE", "Owner approval is stale.")
    if not all(
        (
            body.get("reviewer_confirmation"),
            body.get("confirm_quote_accepted"),
            body.get("confirm_pricing_review_completed"),
            body.get("confirm_create_order_only"),
            body.get("confirm_no_execution_plan"),
            body.get("confirm_no_execution_tasks"),
            body.get("confirm_no_inventory"),
            body.get("confirm_production_separate"),
        )
    ):
        _raise_blocked("CONFIRMATIONS_REQUIRED", "All convert confirmations must be true.")
    if not _final_price_present(quote, linkage):
        _raise_blocked("FINAL_PRICE_MISSING", "Final commercial price is required before convert.")

    orders_before = await db.scalar(select(func.count()).select_from(Orders))
    plans_before = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    currency_handoff, final_price = await _build_v6_order_financial_snapshot(db, quote, linkage)
    handoff_snapshots = await _build_v6_handoff_snapshots(db, record.id, payload_raw, payload)
    snapshot_dict = _build_v6_order_snapshot_payload(
        quote,
        linkage,
        currency_handoff=currency_handoff,
        final_price=final_price,
        handoff_snapshots=handoff_snapshots,
        workspace_hash=workspace_hash,
    )

    order_code = f"ORD-IV6-{int(datetime.now(timezone.utc).timestamp())}-{quote.id}"
    order_notes_payload = {INTAKE_V6_ORDER_LINKAGE_JSON_KEY: snapshot_dict[INTAKE_V6_ORDER_LINKAGE_JSON_KEY]}
    readiness_snapshot = {
        "source": "intake_v6_guarded_convert",
        "snapshot_type": "intake_v6_accepted_quote_at_order_creation",
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "quote_status": quote.status,
        "source_intake_version": "V6",
        "requires_production_handoff_build": True,
        "production_started": False,
        "execution_plan_created": False,
        "inventory_mutated": False,
        "no_execution_plan_created": True,
    }

    orders_service = OrdersService(db)
    order = await orders_service.create(
        {
            "code": order_code,
            "quote_id": quote.id,
            "quote_code": quote.code,
            "client_name": quote.client_name,
            "contact_person": quote.contact_person,
            "status": IV3_ORDER_STATUS_LOCKED,
            "payment_status": "pending",
            "total_amount": currency_handoff.base_total_ron,
            "locked_at": iso_now(),
            "snapshot_version": 1,
            "snapshot_line_items": json.dumps(snapshot_dict, ensure_ascii=False),
            "notes": json.dumps(order_notes_payload, ensure_ascii=False),
            "readiness_snapshot": readiness_snapshot,
        }
    )
    if order is None:
        _raise_blocked("ORDER_CREATE_FAILED", "Order persistence failed.")

    snapshot_dict["order_id"] = order.id
    order.snapshot_line_items = json.dumps(snapshot_dict, ensure_ascii=False)
    convert_record = {
        "status": "approved",
        "converted_at": datetime.now(timezone.utc).isoformat(),
        "converted_by_user_id": current_user.id,
        "converted_by_display_name": current_user.name or current_user.email,
        "source": INTAKE_V6_SOURCE_MODULE,
        "order_created": True,
        "order_id": order.id,
        "order_code": order.code,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "analysis_hash": workspace_hash,
    }
    linkage = dict(linkage)
    linkage[CONVERT_DECISION_JSON_KEY] = convert_record
    updated_notes = _update_linkage_in_notes(quote.notes, linkage)
    await quotes_service.update(quote.id, {"notes": updated_notes})
    await db.commit()
    await db.refresh(order)

    orders_after = await db.scalar(select(func.count()).select_from(Orders))
    plans_after = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    if orders_after != orders_before + 1 or plans_after != plans_before:
        await db.rollback()
        _raise_blocked("SAFETY_VIOLATION", "Unexpected order or execution plan side effect during convert.")

    return {
        "converted": True,
        "quote_id": quote.id,
        "quote_code": quote.code,
        "quote_status": quote.status,
        "order_id": order.id,
        "order_code": order.code,
        "order_status": order.status,
        "source_module": INTAKE_V6_SOURCE_MODULE,
        "order_created": True,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "creates_execution_tasks": False,
        "writes_execution_plan": False,
        "stock_consumption": False,
        "v6_order_conversion": {
            "converted": True,
            "order_id": order.id,
            "blocked_reasons": [],
        },
    }


async def rebuild_v6_order_snapshot_for_existing_order(
    db: AsyncSession,
    *,
    order_id: int,
) -> dict[str, Any]:
    orders_service = OrdersService(db)
    order = await orders_service.get_by_id(order_id)
    if order is None:
        _raise_blocked("ORDER_NOT_FOUND", f"Order id={order_id} was not found.")

    linkage = _extract_v6_order_linkage_from_order(order)
    if linkage is None:
        _raise_blocked("NOT_IV6_ORDER", "Order is not linked to Intake V6.")

    source_quote_id = linkage.get("source_quote_id")
    try:
        quote_id = int(source_quote_id)
    except (TypeError, ValueError):
        _raise_blocked("SOURCE_QUOTE_ID_MISSING", "Order linkage is missing source_quote_id.")

    quote = await QuotesService(db).get_by_id(quote_id)
    if quote is None:
        _raise_blocked("QUOTE_NOT_FOUND", f"Quote id={quote_id} was not found for V6 order rebuild.")

    quote_linkage = _require_v6_linkage(quote)
    record, payload, payload_raw = await _load_workspace_for_linkage(db, quote_linkage)
    workspace_hash = _workspace_analysis_hash_from_payload(payload)
    currency_handoff, final_price = await _build_v6_order_financial_snapshot(db, quote, quote_linkage)
    handoff_snapshots = await _build_v6_handoff_snapshots(db, record.id, payload_raw, payload)
    snapshot_dict = _build_v6_order_snapshot_payload(
        quote,
        quote_linkage,
        currency_handoff=currency_handoff,
        final_price=final_price,
        handoff_snapshots=handoff_snapshots,
        workspace_hash=workspace_hash,
    )
    snapshot_dict["order_id"] = order.id
    order_notes_payload = {INTAKE_V6_ORDER_LINKAGE_JSON_KEY: snapshot_dict[INTAKE_V6_ORDER_LINKAGE_JSON_KEY]}
    existing_plan = await db.scalar(select(ExecutionPlan).where(ExecutionPlan.order_id == order.id))
    readiness_snapshot = order.readiness_snapshot if isinstance(order.readiness_snapshot, dict) else {}
    patched_readiness_snapshot = dict(readiness_snapshot)
    patched_readiness_snapshot["execution_plan_created"] = existing_plan is not None
    patched_readiness_snapshot["no_execution_plan_created"] = existing_plan is None

    updated = await orders_service.update(
        order.id,
        {
            "snapshot_line_items": json.dumps(snapshot_dict, ensure_ascii=False),
            "notes": json.dumps(order_notes_payload, ensure_ascii=False),
            "readiness_snapshot": patched_readiness_snapshot,
        },
    )
    if updated is None:
        _raise_blocked("ORDER_UPDATE_FAILED", f"Failed to update order id={order.id}.")

    return {
        "order_id": updated.id,
        "order_code": updated.code,
        "quote_id": quote.id,
        "quote_code": quote.code,
        "template_code": template_code_from_linkage(quote_linkage),
        "rebuild_applied": True,
        "snapshot_type": snapshot_dict.get("snapshot_type"),
        "product_id": ((snapshot_dict.get("product_definition") or {}).get("product_id")),
    }


def _is_v6_quote(quote: Quotes) -> bool:
    return str(quote.intake_code or "").startswith("IV6-")


def _workspace_analysis_hash_from_payload(payload) -> str | None:
    svg_source = payload.svg_source
    if svg_source is not None and svg_source.file_hash:
        return svg_source.file_hash
    return None


async def get_v6_commercial_spine_state(
    db: AsyncSession,
    *,
    quote_id: int | None = None,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    quotes_service = QuotesService(db)
    quote: Quotes | None = None
    if quote_id is not None:
        quote = await quotes_service.get_by_id(quote_id)
    elif workspace_id is not None:
        quote = await check_existing_quote_for_intake_v6_workspace(db, workspace_id)
    if quote is None:
        return {
            "quote_exists": False,
            "is_v6_quote": False,
            "v6_quote_to_order_enabled": True,
            "creates_execution_tasks": False,
            "writes_execution_plan": False,
            "stock_consumption": False,
            "v6_order_conversion": {},
        }

    linkage = parse_intake_v6_linkage_from_notes(quote.notes)
    is_v6 = _is_v6_quote(quote) and linkage is not None
    workspace_hash = None
    owner_exists, owner_valid, owner_stale = False, False, False
    if is_v6 and linkage is not None:
        ws_id = linkage_workspace_id(linkage)
        if ws_id:
            try:
                record = await _get_record_or_404(db, ws_id)
                payload = _parse_payload(_json_loads(record.payload_json, {}))
                workspace_hash = _workspace_analysis_hash_from_payload(payload)
            except HTTPException:
                workspace_hash = None
        owner_exists, owner_valid, owner_stale = is_v4_owner_approval_valid(linkage, workspace_hash)

    existing_order = await check_existing_order_for_iv3_quote(db, quote.id) if quote else None
    pricing_record = linkage.get(PRICING_REVIEW_JSON_KEY) if isinstance(linkage, dict) else None
    pricing_completed = is_pricing_review_completed(linkage) if linkage else False
    snapshot_record = await _resolve_snapshot_for_v6_pricing_review(db, quote, linkage) if is_v6 and linkage else None
    snapshot_info = _snapshot_state(snapshot_record)
    offer_stamp = None
    pricing_totals_source = "quote_columns"
    if isinstance(linkage, dict):
        raw_stamp = linkage.get(INTAKE_V6_SNAPSHOT_AUTHORITATIVE_OFFER_JSON_KEY)
        if isinstance(raw_stamp, dict):
            offer_stamp = raw_stamp
            pricing_totals_source = V6_SNAPSHOT_OFFER_PRICING_SOURCE

    quote_totals = quote_commercial_totals_summary(quote)
    if pricing_totals_source == V6_SNAPSHOT_OFFER_PRICING_SOURCE:
        quote_totals = {
            **quote_totals,
            "pricing_totals_source": V6_SNAPSHOT_OFFER_PRICING_SOURCE,
        }

    convert_blockers: list[str] = []
    if not snapshot_info["exists"]:
        convert_blockers.append("SNAPSHOT_V2_REQUIRED")
    if not pricing_completed:
        convert_blockers.append("PRICING_REVIEW_REQUIRED")
    if not owner_exists or not owner_valid or owner_stale:
        convert_blockers.append("OWNER_APPROVAL_REQUIRED")
    if not is_v4_accept_completed(linkage, quote.status):
        convert_blockers.append("QUOTE_NOT_ACCEPTED")
    if existing_order is not None:
        convert_blockers.append("ORDER_ALREADY_EXISTS")

    return {
        "quote_exists": True,
        "is_v6_quote": is_v6,
        "quote_id": quote.id,
        "quote_code": quote.code,
        "quote_status": quote.status,
        "intake_code": quote.intake_code,
        "workspace_id": linkage_workspace_id(linkage) if linkage else None,
        "requires_pricing_review": bool(linkage.get("requires_pricing_review", True)) if linkage else True,
        "pricing_review": {
            "completed": pricing_completed,
            "completed_at": pricing_record.get("completed_at") if isinstance(pricing_record, dict) else None,
            "completed_by_user_id": pricing_record.get("reviewed_by_user_id") if isinstance(pricing_record, dict) else None,
        },
        "owner_approval": {
            "exists": owner_exists,
            "valid": owner_valid,
            "stale": owner_stale,
            "approved_at": (linkage.get(OWNER_APPROVAL_JSON_KEY) or {}).get("approved_at") if linkage else None,
            "approved_by_user_id": (linkage.get(OWNER_APPROVAL_JSON_KEY) or {}).get("approved_by_user_id") if linkage else None,
        },
        "snapshot_v2": snapshot_info,
        "snapshot_authoritative_offer": offer_stamp,
        "quote_accepted": is_v4_accept_completed(linkage, quote.status),
        "quote_commercial_totals": quote_totals,
        "v6_order_conversion": {
            "available": is_v6 and len(convert_blockers) == 0,
            "converted": existing_order is not None or is_v4_convert_completed(linkage),
            "order_id": existing_order.id if existing_order else None,
            "order_code": existing_order.code if existing_order else None,
            "blocked_reasons": convert_blockers,
        },
        "creates_execution_tasks": False,
        "writes_execution_plan": False,
        "stock_consumption": False,
        "owner_approval_persisted": owner_exists,
        "v6_quote_to_order_enabled": True,
    }
