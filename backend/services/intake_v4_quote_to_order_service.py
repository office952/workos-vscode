"""Intake V4 quote → order commercial spine — pricing review, owner approval, accept, convert."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from data_models.product_contracts import iso_now
from models.execution_plan import ExecutionPlan
from models.intake_v4_workspace import IntakeV4WorkspaceRecord
from models.orders import Orders
from models.quotes import Quotes
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
)
from services.intake_v4_commercial_quote_service import (
    INTAKE_V4_LINKAGE_JSON_KEY,
    INTAKE_V4_SOURCE_MODULE,
    parse_intake_v4_linkage_from_notes,
)
from services.intake_v4_quote_linkage_utils import (
    INTAKE_V4_ORDER_LINKAGE_JSON_KEY,
    OWNER_APPROVAL_JSON_KEY,
    V4_ACCEPTED_STATUS,
    is_iv4_quote,
    is_pricing_review_completed,
    is_v4_accept_completed,
    is_v4_convert_completed,
    is_v4_owner_approval_valid,
    linkage_workspace_id,
    snapshot_analysis_hash_from_linkage,
    template_code_from_linkage,
)
from services.intake_v4_workspace_service import _get_record_or_404, _json_loads, _parse_payload
from services.order_currency_conversion_service import (
    convert_quote_totals_to_order_base,
    extract_currency_from_quote_snapshot,
)
from services.orders import OrdersService
from services.quotes import QuotesService
from validators.status_lifecycle import validate_transition

logger = logging.getLogger(__name__)

PRICING_METHOD_MANUAL = "manual_review"
PRICING_METHOD_QUOTE_PRICED = "quote_priced_review"
TOTAL_TOLERANCE = 0.05
ALLOWED_CURRENCIES = frozenset({"EUR", "RON", "USD"})
FORBIDDEN_PRICING_REVIEW_BODY_KEYS = frozenset({
    "subtotal",
    "total",
    "vat_amount",
    "vat_percent",
    "discount_amount",
    "currency",
})
ACCEPT_DECISION_APPROVED = "approved"
CONVERT_DECISION_APPROVED = "approved"
INTERMEDIATE_PRICED_STATUS = "priced"
TERMINAL_QUOTE_STATUSES = frozenset({"rejected", "expired"})


def _raise_blocked(error: str, message: str, blockers: list[str] | None = None) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "error": error,
            "message": message,
            "blockers": blockers or [error],
        },
    )


def _load_notes_payload(notes: str | None) -> dict[str, Any]:
    if not notes:
        _raise_blocked("NOTES_EMPTY", "Quote notes are empty.")
    try:
        payload = json.loads(notes)
    except json.JSONDecodeError as exc:
        _raise_blocked("NOTES_JSON_INVALID", f"Quote notes are not valid JSON: {exc.msg}")
    if not isinstance(payload, dict):
        _raise_blocked("NOTES_JSON_INVALID", "Quote notes JSON root must be an object.")
    return payload


def _require_iv4_linkage(quote: Quotes) -> dict[str, Any]:
    if not is_iv4_quote(quote):
        _raise_blocked("NOT_IV4_QUOTE", "Quote intake_code is not an Intake V4 linkage code.")
    linkage = parse_intake_v4_linkage_from_notes(quote.notes)
    if linkage is None:
        _raise_blocked("NOT_IV4_QUOTE", "Quote is not linked to Intake V4.")
    return linkage


async def _load_workspace_for_linkage(
    db: AsyncSession,
    linkage: dict[str, Any],
) -> tuple[IntakeV4WorkspaceRecord, Any]:
    workspace_id = linkage_workspace_id(linkage)
    if not workspace_id:
        _raise_blocked("WORKSPACE_ID_MISSING", "Intake V4 linkage is missing source_workspace_id.")
    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    payload = _parse_payload(payload_raw)
    return record, payload


def _workspace_analysis_hash_from_payload(payload) -> str | None:
    svg_source = payload.svg_source
    if svg_source is not None and svg_source.file_hash:
        return svg_source.file_hash
    return None


def _source_fingerprint(analysis_hash: str | None, linkage: dict[str, Any]) -> str:
    snapshot = linkage.get("snapshot")
    finish_raw = ""
    if isinstance(snapshot, dict):
        ws = snapshot.get("workspace_payload_snapshot")
        if isinstance(ws, dict):
            finish = ws.get("finish_setup")
            if isinstance(finish, dict):
                finish_raw = json.dumps(finish, sort_keys=True, separators=(",", ":"))
    parts = [analysis_hash or "no_analysis_hash", finish_raw, template_code_from_linkage(linkage) or ""]
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _assert_analysis_hash_sync(
    linkage: dict[str, Any],
    workspace_hash: str | None,
    *,
    context: str,
) -> None:
    snap_hash = snapshot_analysis_hash_from_linkage(linkage)
    if workspace_hash and snap_hash and workspace_hash != snap_hash:
        _raise_blocked(
            "ANALYSIS_HASH_MISMATCH",
            f"Workspace analysis hash differs from quote snapshot ({context}).",
            ["analysis_hash_mismatch"],
        )


def _final_price_present(quote: Quotes, linkage: dict[str, Any]) -> bool:
    if float(quote.grand_total or 0) > 0:
        return True
    record = get_pricing_review_record(linkage)
    if record and float(record.get("total") or 0) > 0:
        return True
    return False


def _reject_client_supplied_totals(body: dict[str, Any]) -> None:
    supplied = sorted(FORBIDDEN_PRICING_REVIEW_BODY_KEYS.intersection(body.keys()))
    if supplied:
        _raise_blocked(
            "PLACEHOLDER_TOTALS_NOT_ALLOWED",
            "Pricing review totals must come from the priced quote — do not supply commercial totals in the request.",
            ["PLACEHOLDER_TOTALS_NOT_ALLOWED"],
        )


def _parse_quote_line_items_snapshot(quote: Quotes) -> Any:
    if not quote.line_items:
        return None
    try:
        parsed = json.loads(quote.line_items)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed.get("snapshot") or parsed
    return None


def _extract_commercial_totals_from_quote(quote: Quotes) -> dict[str, Any]:
    grand_total = float(quote.grand_total or 0)
    if grand_total <= 0:
        _raise_blocked(
            "QUOTE_NOT_PRICED",
            "Quote has no commercial totals — price the quote in QuoteWizard before completing pricing review.",
            ["QUOTE_NOT_PRICED"],
        )

    subtotal = float(quote.subtotal or 0)
    discount = float(quote.discount or 0)
    net = float(quote.total_before_vat or 0)
    if net <= 0:
        net = subtotal - discount
    if net <= 0:
        _raise_blocked(
            "QUOTE_NOT_PRICED",
            "Quote net total is missing — price the quote in QuoteWizard before completing pricing review.",
            ["QUOTE_NOT_PRICED"],
        )

    vat_percent = float(quote.vat or 0)
    vat_amount = grand_total - net
    if vat_amount < -TOTAL_TOLERANCE:
        _raise_blocked(
            "QUOTE_TOTALS_INCONSISTENT",
            "Quote commercial totals are inconsistent — re-price in QuoteWizard.",
            ["QUOTE_TOTALS_INCONSISTENT"],
        )

    line_items_snapshot = _parse_quote_line_items_snapshot(quote)
    currency = extract_currency_from_quote_snapshot(line_items_snapshot)
    if currency not in ALLOWED_CURRENCIES:
        currency = "EUR"

    return {
        "subtotal": subtotal,
        "discount_amount": discount,
        "vat_percent": vat_percent,
        "vat_amount": vat_amount,
        "total": grand_total,
        "net_before_vat": net,
        "currency": currency,
        "pricing_totals_source": "quote_columns",
        "pricing_totals_captured": True,
    }


def quote_commercial_totals_summary(quote: Quotes | None) -> dict[str, Any]:
    if quote is None:
        return {
            "available": False,
            "grand_total": None,
            "blocker": "quote_missing",
            "pricing_totals_source": None,
        }
    grand_total = float(quote.grand_total or 0)
    if grand_total <= 0:
        return {
            "available": False,
            "grand_total": grand_total,
            "blocker": "QUOTE_NOT_PRICED",
            "pricing_totals_source": None,
        }
    return {
        "available": True,
        "grand_total": grand_total,
        "blocker": None,
        "pricing_totals_source": "quote_columns",
    }


def _validate_quote_priced_totals(totals: dict[str, Any]) -> None:
    currency = (totals.get("currency") or "").strip().upper()
    if currency not in ALLOWED_CURRENCIES:
        _raise_blocked("CURRENCY_UNSUPPORTED", f"Currency {totals.get('currency')!r} is not supported.")
    subtotal = float(totals["subtotal"])
    discount = float(totals.get("discount_amount") or 0)
    vat_amount = float(totals["vat_amount"])
    total = float(totals["total"])
    for name, value in (
        ("subtotal", subtotal),
        ("discount_amount", discount),
        ("vat_amount", vat_amount),
        ("total", total),
    ):
        if value < 0:
            _raise_blocked("INVALID_TOTALS", f"{name} must be >= 0.")
    if discount > subtotal + TOTAL_TOLERANCE:
        _raise_blocked("INVALID_TOTALS", "discount_amount cannot exceed subtotal.")
    net = subtotal - discount
    if abs(net + vat_amount - total) > TOTAL_TOLERANCE:
        _raise_blocked("INVALID_TOTALS", "Quote totals are inconsistent.")


def _validate_manual_totals(body: dict[str, Any]) -> None:
    del body  # legacy hook removed — totals come from quote only


def _update_linkage_in_notes(notes: str | None, linkage: dict[str, Any]) -> str:
    payload = _load_notes_payload(notes)
    payload[INTAKE_V4_LINKAGE_JSON_KEY] = linkage
    return json.dumps(payload, default=str)


async def _collect_accept_critical_blockers(
    db: AsyncSession,
    record: IntakeV4WorkspaceRecord,
    payload,
    payload_raw: dict[str, Any],
    workspace_id: str,
) -> list[str]:
    from services.intake_v4_analysis_boundary_service import list_v4_analysis_boundary_blockers
    from services.intake_v4_template_option_contract_service import evaluate_v4_template_option_contract

    del db, record, payload_raw, workspace_id
    blockers: list[str] = []
    blockers.extend(list_v4_analysis_boundary_blockers(payload))
    contract = evaluate_v4_template_option_contract(payload)
    blockers.extend(b.code for b in contract.blockers if b.severity == "blocking")
    return blockers


def build_v4_pricing_review_record(
    quote: Quotes,
    linkage: dict[str, Any],
    totals: dict[str, Any],
    body: dict[str, Any],
    current_user: UserResponse,
    *,
    workspace_id: str,
    analysis_hash: str | None,
) -> dict[str, Any]:
    quote_input = linkage.get("quote_input_payload")
    quote_input_hash = None
    if isinstance(quote_input, dict):
        encoded = json.dumps(quote_input, sort_keys=True, separators=(",", ":")).encode("utf-8")
        quote_input_hash = hashlib.sha256(encoded).hexdigest()
    return {
        "status": "completed",
        "method": PRICING_METHOD_QUOTE_PRICED,
        "source": INTAKE_V4_SOURCE_MODULE,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_by_user_id": current_user.id,
        "reviewed_by_display_name": current_user.name or current_user.email,
        "reason": str(body.get("pricing_review_reason") or "").strip(),
        "currency": str(totals.get("currency") or "EUR").strip().upper(),
        "subtotal": float(totals["subtotal"]),
        "discount_amount": float(totals.get("discount_amount") or 0),
        "vat_percent": float(totals["vat_percent"]),
        "vat_amount": float(totals["vat_amount"]),
        "total": float(totals["total"]),
        "net_before_vat": float(totals["net_before_vat"]),
        "pricing_totals_source": totals.get("pricing_totals_source"),
        "pricing_totals_captured": totals.get("pricing_totals_captured", True),
        "workspace_id": workspace_id,
        "analysis_hash": analysis_hash,
        "quote_input_payload_hash": quote_input_hash,
        "cost_engine_called": False,
        "quote_stays_draft": True,
        "priced_draft": True,
        "order_created": False,
        "execution_plan_created": False,
        "inventory_mutated": False,
        "quote_id": quote.id,
        "quote_code": quote.code,
        "intake_code": quote.intake_code,
    }


async def complete_v4_pricing_review(
    db: AsyncSession,
    quote_id: int,
    body: dict[str, Any],
    current_user: UserResponse,
) -> dict[str, Any]:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        _raise_blocked("QUOTE_NOT_FOUND", f"Quote id={quote_id} was not found.")
    linkage = _require_iv4_linkage(quote)

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
    quote_totals = _extract_commercial_totals_from_quote(quote)
    _validate_quote_priced_totals(quote_totals)

    if body.get("expected_quote_id") is not None and int(body["expected_quote_id"]) != quote.id:
        _raise_blocked("QUOTE_ID_MISMATCH", "expected_quote_id does not match quote.")
    if body.get("expected_intake_code") and body["expected_intake_code"] != quote.intake_code:
        _raise_blocked("INTAKE_CODE_MISMATCH", "expected_intake_code does not match quote.")

    record, payload = await _load_workspace_for_linkage(db, linkage)
    workspace_id = record.id
    workspace_hash = _workspace_analysis_hash_from_payload(payload)
    client_hash = body.get("client_analysis_hash")
    if client_hash and workspace_hash and client_hash != workspace_hash:
        _raise_blocked(
            "ANALYSIS_HASH_MISMATCH",
            "client_analysis_hash does not match workspace.",
            ["analysis_hash_mismatch"],
        )

    orders_before = await db.scalar(select(func.count()).select_from(Orders))
    plans_before = await db.scalar(select(func.count()).select_from(ExecutionPlan))

    pricing_record = build_v4_pricing_review_record(
        quote,
        linkage,
        quote_totals,
        body,
        current_user,
        workspace_id=workspace_id,
        analysis_hash=workspace_hash,
    )
    linkage = dict(linkage)
    linkage["requires_pricing_review"] = False
    linkage["priced_draft"] = True
    linkage[PRICING_REVIEW_JSON_KEY] = pricing_record
    updated_notes = _update_linkage_in_notes(quote.notes, linkage)

    updated = await quotes_service.update(
        quote.id,
        {
            "status": "draft",
            "notes": updated_notes,
        },
    )
    if updated is None:
        _raise_blocked("QUOTE_UPDATE_FAILED", "Failed to persist pricing review.")

    orders_after = await db.scalar(select(func.count()).select_from(Orders))
    plans_after = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    if orders_after != orders_before or plans_after != plans_before:
        _raise_blocked("SAFETY_VIOLATION", "Unexpected order or execution side effect during pricing review.")

    logger.info("Intake V4 pricing review completed: quote_id=%s user=%s", quote.id, current_user.id)
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


async def persist_v4_owner_approval(
    db: AsyncSession,
    quote_id: int,
    body: dict[str, Any],
    current_user: UserResponse,
) -> dict[str, Any]:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        _raise_blocked("QUOTE_NOT_FOUND", f"Quote id={quote_id} was not found.")
    linkage = _require_iv4_linkage(quote)

    if not all(
        (
            body.get("acknowledged_no_execution_tasks"),
            body.get("acknowledged_no_stock_consumption"),
        )
    ):
        _raise_blocked(
            "CONFIRMATIONS_REQUIRED",
            "Owner must acknowledge no execution tasks and no stock consumption.",
        )

    if not str(body.get("decision_reason") or "").strip():
        _raise_blocked("DECISION_REASON_REQUIRED", "decision_reason is required.")

    record, payload = await _load_workspace_for_linkage(db, linkage)
    workspace_hash = _workspace_analysis_hash_from_payload(payload)
    client_hash = body.get("client_analysis_hash")
    if client_hash and workspace_hash and client_hash != workspace_hash:
        _raise_blocked(
            "ANALYSIS_HASH_MISMATCH",
            "client_analysis_hash does not match workspace.",
            ["analysis_hash_mismatch"],
        )

    orders_before = await db.scalar(select(func.count()).select_from(Orders))
    plans_before = await db.scalar(select(func.count()).select_from(ExecutionPlan))

    approval_record = {
        "approved": True,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "approved_by_user_id": current_user.id,
        "approved_by_display_name": current_user.name or current_user.email,
        "approval_scope": "intake_v4_quote_to_order",
        "analysis_hash": workspace_hash,
        "source_fingerprint": _source_fingerprint(workspace_hash, linkage),
        "acknowledged_blockers": list(body.get("acknowledged_blockers") or []),
        "acknowledged_warnings": list(body.get("acknowledged_warnings") or []),
        "acknowledged_no_execution_tasks": True,
        "acknowledged_no_stock_consumption": True,
        "decision_reason": str(body.get("decision_reason") or "").strip(),
        "source": INTAKE_V4_SOURCE_MODULE,
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


async def accept_v4_quote(
    db: AsyncSession,
    quote_id: int,
    body: dict[str, Any],
    current_user: UserResponse,
) -> dict[str, Any]:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        _raise_blocked("QUOTE_NOT_FOUND", f"Quote id={quote_id} was not found.")
    linkage = _require_iv4_linkage(quote)

    if is_v4_accept_completed(linkage, quote.status):
        _raise_blocked("ACCEPT_ALREADY_COMPLETED", "Quote already accepted.")

    if quote.status in TERMINAL_QUOTE_STATUSES:
        _raise_blocked("QUOTE_TERMINAL", f"Quote status {quote.status!r} cannot be accepted.")

    if bool(linkage.get("requires_pricing_review", True)) or not is_pricing_review_completed(linkage):
        _raise_blocked("PRICING_REVIEW_REQUIRED", "Pricing review must be completed before accept.")

    record, payload = await _load_workspace_for_linkage(db, linkage)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    workspace_hash = _workspace_analysis_hash_from_payload(payload)
    _assert_analysis_hash_sync(linkage, workspace_hash, context="accept")

    exists, valid, stale = is_v4_owner_approval_valid(linkage, workspace_hash)
    if not exists:
        _raise_blocked("OWNER_APPROVAL_MISSING", "Owner approval is required before accept.")
    if stale or not valid:
        _raise_blocked("OWNER_APPROVAL_STALE", "Owner approval is stale — re-approve after workspace changes.")

    critical = await _collect_accept_critical_blockers(db, record, payload, payload_raw, record.id)
    if critical:
        _raise_blocked(
            "READINESS_BLOCKERS",
            "Quote cannot be accepted while workspace has critical readiness blockers.",
            critical,
        )

    if not _final_price_present(quote, linkage):
        _raise_blocked("FINAL_PRICE_MISSING", "Final commercial price is required before accept.")

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

    if str(body.get("accept_decision") or "") != ACCEPT_DECISION_APPROVED:
        _raise_blocked("ACCEPT_DECISION_INVALID", "accept_decision must be approved.")

    orders_before = await db.scalar(select(func.count()).select_from(Orders))
    plans_before = await db.scalar(select(func.count()).select_from(ExecutionPlan))

    quote_status_before = quote.status
    accept_record = {
        "status": ACCEPT_DECISION_APPROVED,
        "accepted_at": datetime.now(timezone.utc).isoformat(),
        "accepted_by_user_id": current_user.id,
        "accepted_by_display_name": current_user.name or current_user.email,
        "reason": str(body.get("accept_reason") or "").strip(),
        "source": INTAKE_V4_SOURCE_MODULE,
        "analysis_hash": workspace_hash,
        "snapshot_hash": snapshot_analysis_hash_from_linkage(linkage),
        "approved_owner_approval_reference": linkage.get(OWNER_APPROVAL_JSON_KEY),
        "pricing_review_completed": True,
        "quote_status_before": quote_status_before,
        "quote_status_after": V4_ACCEPTED_STATUS,
        "order_created": False,
        "execution_plan_created": False,
        "inventory_mutated": False,
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
        {"status": V4_ACCEPTED_STATUS, "notes": updated_notes},
    )
    if updated is None:
        _raise_blocked("QUOTE_UPDATE_FAILED", "Quote update failed after accept.")

    orders_after = await db.scalar(select(func.count()).select_from(Orders))
    plans_after = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    if orders_after != orders_before or plans_after != plans_before:
        _raise_blocked("SAFETY_VIOLATION", "Unexpected order or execution side effect during accept.")

    logger.info("Intake V4 quote accepted: quote_id=%s user=%s", quote.id, current_user.id)
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


async def _build_v4_handoff_snapshots(
    db: AsyncSession,
    workspace_id: str,
    payload_raw: dict[str, Any],
    payload,
) -> dict[str, Any]:
    snapshots: dict[str, Any] = {}
    try:
        from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown_with_registry

        breakdown = await build_intake_v4_material_breakdown_with_registry(db, workspace_id, payload_raw)
        snapshots["material_breakdown_snapshot"] = breakdown.model_dump(mode="json")
    except Exception as exc:
        snapshots["material_breakdown_snapshot"] = {"error": str(exc), "captured": False}
    try:
        from services.intake_v4_production_handoff_preview_service import build_intake_v4_production_handoff_preview

        handoff = await build_intake_v4_production_handoff_preview(db, workspace_id, payload_raw, payload)
        snapshots["production_handoff_preview_snapshot"] = handoff.model_dump(mode="json")
    except Exception as exc:
        snapshots["production_handoff_preview_snapshot"] = {"error": str(exc), "captured": False}
    try:
        from services.intake_v4_task_generation_dry_run_service import build_intake_v4_task_generation_dry_run

        dry_run = await build_intake_v4_task_generation_dry_run(db, workspace_id, payload_raw, payload)
        snapshots["task_generation_dry_run_snapshot"] = {
            "summary": dry_run.summary,
            "task_candidates_count": len(dry_run.task_candidates),
            "idempotency_entries_count": len(dry_run.idempotency_plan),
            "can_generate_tasks": dry_run.can_generate_tasks,
        }
    except Exception as exc:
        snapshots["task_generation_dry_run_snapshot"] = {"error": str(exc), "captured": False}
    return snapshots


def build_v4_order_snapshot_payload(
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
    order_linkage = {
        "source_module": INTAKE_V4_SOURCE_MODULE,
        "source_intake_version": "V4",
        "source_quote_id": quote.id,
        "source_workspace_id": workspace_id,
        "quote_intake_code": quote.intake_code,
        "quote_code": quote.code,
        "analysis_hash": workspace_hash or snapshot_analysis_hash_from_linkage(linkage),
        "template_code": template_code_from_linkage(linkage),
        "created_from_intake_v4": True,
        "no_execution_plan_created": True,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "production_started": False,
    }
    return {
        "source_module": INTAKE_V4_SOURCE_MODULE,
        "source_intake_version": "V4",
        "snapshot_type": "intake_v4_guarded_convert_order_snapshot_v1",
        INTAKE_V4_ORDER_LINKAGE_JSON_KEY: order_linkage,
        "source_workspace_id": workspace_id,
        "source_quote_id": quote.id,
        "analysis_hash": workspace_hash or snapshot_analysis_hash_from_linkage(linkage),
        "template_code": template_code_from_linkage(linkage),
        "workspace_payload_snapshot": snapshot.get("workspace_payload_snapshot"),
        "quote_input_payload": snapshot.get("quote_input_payload") or linkage.get("quote_input_payload"),
        "owner_approval_snapshot": linkage.get(OWNER_APPROVAL_JSON_KEY),
        "pricing_review_snapshot": linkage.get(PRICING_REVIEW_JSON_KEY),
        "accept_decision_snapshot": linkage.get(ACCEPT_DECISION_JSON_KEY),
        "commercial_line_items": json.loads(quote.line_items) if quote.line_items else [],
        "final_price": final_price,
        "commercial_currency_handoff": currency_handoff,
        "handoff_snapshots": handoff_snapshots,
        "no_execution_plan_created": True,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "production_started": False,
        "created_from": "intake_v4",
    }


async def convert_v4_quote_to_order(
    db: AsyncSession,
    quote_id: int,
    body: dict[str, Any],
    current_user: UserResponse,
) -> dict[str, Any]:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        _raise_blocked("QUOTE_NOT_FOUND", f"Quote id={quote_id} was not found.")
    linkage = _require_iv4_linkage(quote)

    existing_order = await check_existing_order_for_iv3_quote(db, quote_id)
    if existing_order is not None or is_v4_convert_completed(linkage):
        _raise_blocked(
            "ORDER_ALREADY_EXISTS",
            f"An order already exists for quote id={quote.id}.",
            ["ORDER_ALREADY_EXISTS"],
        )

    if not is_v4_accept_completed(linkage, quote.status) or quote.status != V4_ACCEPTED_STATUS:
        _raise_blocked("QUOTE_NOT_ACCEPTED", "Quote must be accepted before convert.")

    if bool(linkage.get("requires_pricing_review", True)) or not is_pricing_review_completed(linkage):
        _raise_blocked("PRICING_REVIEW_REQUIRED", "Pricing review must be completed before convert.")

    record, payload = await _load_workspace_for_linkage(db, linkage)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
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

    pricing_review = get_pricing_review_record(linkage) or {}
    currency = str(pricing_review.get("currency") or "EUR")
    gross_total = float(quote.grand_total or pricing_review.get("total") or 0)
    net_total = float(pricing_review.get("subtotal") or quote.total_before_vat or gross_total)
    if gross_total <= 0:
        _raise_blocked("FINAL_PRICE_MISSING", "Final commercial price is not present on the quote.")

    orders_before = await db.scalar(select(func.count()).select_from(Orders))
    plans_before = await db.scalar(select(func.count()).select_from(ExecutionPlan))

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
    handoff_snapshots = await _build_v4_handoff_snapshots(db, record.id, payload_raw, payload)
    snapshot_dict = build_v4_order_snapshot_payload(
        quote,
        linkage,
        currency_handoff=currency_handoff.to_dict(),
        final_price=final_price,
        handoff_snapshots=handoff_snapshots,
        workspace_hash=workspace_hash,
    )

    order_code = f"ORD-IV4-{int(datetime.now(timezone.utc).timestamp())}-{quote.id}"
    order_notes_payload = {INTAKE_V4_ORDER_LINKAGE_JSON_KEY: snapshot_dict[INTAKE_V4_ORDER_LINKAGE_JSON_KEY]}
    readiness_snapshot = {
        "source": "intake_v4_guarded_convert",
        "snapshot_type": "intake_v4_accepted_quote_at_order_creation",
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "quote_status": quote.status,
        "source_intake_version": "V4",
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
        "status": CONVERT_DECISION_APPROVED,
        "converted_at": datetime.now(timezone.utc).isoformat(),
        "converted_by_user_id": current_user.id,
        "converted_by_display_name": current_user.name or current_user.email,
        "source": INTAKE_V4_SOURCE_MODULE,
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

    logger.info("Intake V4 convert completed: quote_id=%s order_id=%s user=%s", quote.id, order.id, current_user.id)
    return {
        "converted": True,
        "quote_id": quote.id,
        "quote_code": quote.code,
        "quote_status": quote.status,
        "order_id": order.id,
        "order_code": order.code,
        "order_status": order.status,
        "source_module": INTAKE_V4_SOURCE_MODULE,
        "order_created": True,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "creates_execution_tasks": False,
        "writes_execution_plan": False,
        "stock_consumption": False,
        "v4_order_conversion": {
            "converted": True,
            "order_id": order.id,
            "blocked_reasons": [],
        },
    }


async def get_v4_commercial_spine_state(
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
        from services.intake_v4_commercial_quote_service import check_existing_quote_for_intake_v4_workspace

        quote = await check_existing_quote_for_intake_v4_workspace(db, workspace_id)
    if quote is None:
        return {
            "quote_exists": False,
            "is_iv4_quote": False,
            "v4_quote_to_order_enabled": True,
            "creates_execution_tasks": False,
            "writes_execution_plan": False,
        }

    linkage = parse_intake_v4_linkage_from_notes(quote.notes)
    is_v4 = is_iv4_quote(quote) and linkage is not None
    workspace_hash = None
    owner_exists, owner_valid, owner_stale = False, False, False
    if is_v4 and linkage is not None:
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

    convert_blockers: list[str] = []
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
        "is_iv4_quote": is_v4,
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
        "quote_accepted": is_v4_accept_completed(linkage, quote.status),
        "quote_commercial_totals": quote_commercial_totals_summary(quote),
        "v4_order_conversion": {
            "available": is_v4 and len(convert_blockers) == 0,
            "converted": existing_order is not None or is_v4_convert_completed(linkage),
            "order_id": existing_order.id if existing_order else None,
            "order_code": existing_order.code if existing_order else None,
            "blocked_reasons": convert_blockers,
        },
        "creates_execution_tasks": False,
        "writes_execution_plan": False,
        "stock_consumption": False,
        "owner_approval_persisted": owner_exists,
        "v4_quote_to_order_enabled": True,
    }
