"""Intake V3 manual pricing review completion — priced draft only, no CostEngine/order/execution/inventory."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from schemas.auth import UserResponse
from schemas.intake_v3 import (
    IntakeV3CompletePricingReviewRequest,
    IntakeV3CompletePricingReviewResponse,
    IntakeV3PricingReviewCompletionState,
    IntakeV3PricingReviewRecord,
)
from services.intake_v3_quote_linkage_utils import (
    PRICING_REVIEW_JSON_KEY,
    get_pricing_review_record,
    is_pricing_review_completed,
)
from services.intake_v3_real_commercial_quote_creation_service import (
    INTAKE_V3_LINKAGE_CODE_PREFIX,
    INTAKE_V3_LINKAGE_JSON_KEY,
    INTAKE_V3_SOURCE_MODULE,
    check_existing_quote_for_intake_v3_workspace,
    parse_intake_v3_linkage_from_notes,
)
from services.quotes import QuotesService

logger = logging.getLogger(__name__)

PRICING_METHOD_MANUAL = "manual_review"
TOTAL_TOLERANCE = 0.05
ALLOWED_CURRENCIES = frozenset({"EUR", "RON", "USD"})


def _raise_blocked(error: str, message: str, blockers: list[str] | None = None) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "error": error,
            "message": message,
            "blockers": blockers or [error],
        },
    )


def _parse_iv3_linkage_or_block(notes: str | None) -> dict[str, Any]:
    linkage = parse_intake_v3_linkage_from_notes(notes)
    if linkage is None:
        _raise_blocked(
            "NOTES_JSON_INVALID",
            "Intake V3 linkage notes are invalid — pricing review cannot proceed.",
        )
    return linkage


def _load_notes_payload(notes: str | None) -> dict[str, Any]:
    if not notes:
        _raise_blocked("NOTES_EMPTY", "Quote notes are empty — cannot complete pricing review.")
    try:
        payload = json.loads(notes)
    except json.JSONDecodeError as exc:
        _raise_blocked(
            "NOTES_JSON_INVALID",
            f"Quote notes are not valid JSON: {exc.msg}",
        )
    if not isinstance(payload, dict):
        _raise_blocked("NOTES_JSON_INVALID", "Quote notes JSON root must be an object.")
    return payload


def _require_iv3_draft_quote(quote: Quotes) -> dict[str, Any]:
    if not quote.intake_code or not str(quote.intake_code).startswith(INTAKE_V3_LINKAGE_CODE_PREFIX):
        _raise_blocked("NOT_IV3_QUOTE", "Quote intake_code is not an Intake V3 linkage code.")
    linkage = parse_intake_v3_linkage_from_notes(quote.notes)
    if linkage is None:
        _raise_blocked("NOT_IV3_QUOTE", "Quote is not linked to Intake V3.")
    if quote.status != "draft":
        _raise_blocked(
            "QUOTE_NOT_DRAFT",
            f"Pricing review completion requires draft status; got {quote.status!r}.",
        )
    if is_pricing_review_completed(linkage):
        _raise_blocked(
            "PRICING_REVIEW_ALREADY_COMPLETED",
            "Pricing review has already been completed for this quote.",
        )
    if bool(linkage.get("requires_pricing_review", True)) is False and float(quote.grand_total or 0) > 0:
        _raise_blocked(
            "PRICING_REVIEW_ALREADY_COMPLETED",
            "Quote already appears priced without pending pricing review.",
        )
    snapshot = linkage.get("snapshot")
    if not isinstance(snapshot, dict) or not snapshot:
        _raise_blocked("SNAPSHOT_MISSING", "Intake V3 snapshot is missing from quote notes.")
    if not isinstance(linkage.get("owner_decision"), dict):
        _raise_blocked("OWNER_DECISION_MISSING", "Owner decision record is missing from quote notes.")
    return linkage


def _validate_confirmations(request: IntakeV3CompletePricingReviewRequest) -> None:
    if not all(
        (
            request.reviewer_confirmation,
            request.confirm_quote_stays_draft,
            request.confirm_no_order,
            request.confirm_no_execution,
            request.confirm_no_inventory,
        )
    ):
        _raise_blocked(
            "CONFIRMATIONS_REQUIRED",
            "All reviewer and safety confirmations must be true.",
        )
    if request.pricing_method != PRICING_METHOD_MANUAL:
        _raise_blocked(
            "PRICING_METHOD_UNSUPPORTED",
            f"Unsupported pricing method {request.pricing_method!r}; only manual_review is allowed.",
        )
    if not request.pricing_review_reason or not request.pricing_review_reason.strip():
        _raise_blocked("PRICING_REVIEW_REASON_REQUIRED", "pricing_review_reason is required.")


def _validate_manual_totals(request: IntakeV3CompletePricingReviewRequest) -> None:
    currency = (request.currency or "").strip().upper()
    if currency not in ALLOWED_CURRENCIES:
        _raise_blocked(
            "CURRENCY_UNSUPPORTED",
            f"Currency {request.currency!r} is not supported; allowed: {sorted(ALLOWED_CURRENCIES)}.",
        )
    for field_name, value in (
        ("subtotal", request.subtotal),
        ("discount_amount", request.discount_amount),
        ("vat_percent", request.vat_percent),
        ("vat_amount", request.vat_amount),
        ("total", request.total),
    ):
        if value < 0:
            _raise_blocked("INVALID_TOTALS", f"{field_name} must be >= 0.")
    if request.discount_amount > request.subtotal + TOTAL_TOLERANCE:
        _raise_blocked("INVALID_TOTALS", "discount_amount cannot exceed subtotal.")
    net = request.subtotal - request.discount_amount
    expected_total = net + request.vat_amount
    if abs(expected_total - request.total) > TOTAL_TOLERANCE:
        _raise_blocked(
            "INVALID_TOTALS",
            "total must equal (subtotal - discount_amount) + vat_amount within tolerance.",
        )


def validate_pricing_review_can_be_completed(
    quote: Quotes,
    linkage: dict[str, Any],
    request: IntakeV3CompletePricingReviewRequest,
    current_user: UserResponse | None,
) -> None:
    if current_user is None or not current_user.id:
        _raise_blocked("REVIEWER_IDENTITY_UNCLEAR", "Current user identity is required.")
    _validate_confirmations(request)
    _validate_manual_totals(request)
    if request.expected_quote_id is not None and request.expected_quote_id != quote.id:
        _raise_blocked(
            "QUOTE_ID_MISMATCH",
            f"expected_quote_id {request.expected_quote_id} does not match quote {quote.id}.",
        )
    if request.expected_intake_code and request.expected_intake_code != quote.intake_code:
        _raise_blocked(
            "INTAKE_CODE_MISMATCH",
            "expected_intake_code does not match linked quote intake_code.",
        )


def build_manual_pricing_review_record(
    quote: Quotes,
    request: IntakeV3CompletePricingReviewRequest,
    current_user: UserResponse,
) -> dict[str, Any]:
    net = request.subtotal - request.discount_amount
    return {
        "status": "completed",
        "method": PRICING_METHOD_MANUAL,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "completed_by_user_id": current_user.id,
        "completed_by_display_name": current_user.name or current_user.email,
        "reason": request.pricing_review_reason.strip(),
        "currency": request.currency.strip().upper(),
        "subtotal": float(request.subtotal),
        "discount_amount": float(request.discount_amount),
        "vat_percent": float(request.vat_percent),
        "vat_amount": float(request.vat_amount),
        "total": float(request.total),
        "net_before_vat": float(net),
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


def build_pricing_review_audit_snapshot(
    quote: Quotes,
    request: IntakeV3CompletePricingReviewRequest,
    current_user: UserResponse,
) -> dict[str, Any]:
    record = build_manual_pricing_review_record(quote, request, current_user)
    return {
        "audit_type": "intake_v3_manual_pricing_review_completion",
        "quote_id": quote.id,
        "quote_status_before": quote.status,
        "quote_status_after": "draft",
        "pricing_review": record,
    }


def update_quote_notes_with_pricing_review(
    notes: str | None,
    pricing_review_record: dict[str, Any],
) -> str:
    payload = _load_notes_payload(notes)
    linkage = payload.get(INTAKE_V3_LINKAGE_JSON_KEY)
    if not isinstance(linkage, dict):
        _raise_blocked("LINKAGE_MISSING", "Cannot update notes — Intake V3 linkage missing.")
    linkage = dict(linkage)
    linkage["requires_pricing_review"] = False
    linkage["priced_draft"] = True
    linkage[PRICING_REVIEW_JSON_KEY] = pricing_review_record
    payload[INTAKE_V3_LINKAGE_JSON_KEY] = linkage
    return json.dumps(payload, default=str)


def _quote_field_updates(request: IntakeV3CompletePricingReviewRequest) -> dict[str, Any]:
    net = request.subtotal - request.discount_amount
    discount_pct = (request.discount_amount / request.subtotal * 100.0) if request.subtotal > 0 else 0.0
    return {
        "status": "draft",
        "subtotal": float(request.subtotal),
        "discount": float(request.discount_amount),
        "discount_pct": float(discount_pct),
        "total_before_vat": float(net),
        "vat": float(request.vat_percent),
        "grand_total": float(request.total),
    }


def build_priced_draft_quote_response(
    quote: Quotes,
    pricing_review_record: dict[str, Any],
) -> IntakeV3CompletePricingReviewResponse:
    return IntakeV3CompletePricingReviewResponse(
        pricing_review_completed=True,
        quote_id=quote.id,
        quote_code=quote.code,
        quote_status=quote.status,
        source_module=INTAKE_V3_SOURCE_MODULE,
        requires_pricing_review=False,
        priced_draft=True,
        pricing_method=PRICING_METHOD_MANUAL,
        currency=str(pricing_review_record.get("currency") or "EUR"),
        subtotal=float(quote.subtotal or 0),
        discount_amount=float(quote.discount or 0),
        vat_percent=float(quote.vat or 0),
        vat_amount=float(pricing_review_record.get("vat_amount") or 0),
        total=float(quote.grand_total or 0),
        order_created=False,
        execution_plan_created=False,
        inventory_mutated=False,
        cost_engine_called=False,
        can_accept_quote=False,
        can_convert_to_order=False,
    )


def get_pricing_review_completion_state_from_quote(quote: Quotes) -> IntakeV3PricingReviewCompletionState:
    linkage = parse_intake_v3_linkage_from_notes(quote.notes)
    is_iv3 = (
        linkage is not None
        and quote.intake_code
        and str(quote.intake_code).startswith(INTAKE_V3_LINKAGE_CODE_PREFIX)
        and quote.status == "draft"
    )
    if not is_iv3 or linkage is None:
        return IntakeV3PricingReviewCompletionState(
            review_status="not_applicable",
            is_intake_v3_quote=False,
            quote_id=quote.id,
            message="Quote is not an Intake V3 draft quote.",
        )

    completed = is_pricing_review_completed(linkage)
    record = get_pricing_review_record(linkage)
    requires = bool(linkage.get("requires_pricing_review", True)) and not completed

    return IntakeV3PricingReviewCompletionState(
        review_status="completed" if completed else "pending_review",
        is_intake_v3_quote=True,
        quote_id=quote.id,
        quote_code=quote.code,
        quote_status=quote.status,
        intake_code=quote.intake_code,
        source_workspace_id=str(linkage.get("source_workspace_id") or ""),
        requires_pricing_review=requires,
        pricing_review_completed=completed,
        priced_draft=bool(linkage.get("priced_draft") or completed),
        pricing_method=str(record.get("method") or "") if record else None,
        subtotal=float(quote.subtotal or 0) if completed else None,
        total=float(quote.grand_total or 0) if completed else None,
        currency=str(record.get("currency") or "") if record else None,
        can_complete_pricing_review=not completed and requires,
        can_accept_quote=False,
        can_convert_to_order=False,
        warnings=[],
    )


async def get_pricing_review_completion_state(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3PricingReviewCompletionState:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "quote_not_found", "quote_id": quote_id},
        )
    return get_pricing_review_completion_state_from_quote(quote)


async def get_pricing_review_completion_state_by_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3PricingReviewCompletionState:
    quote = await check_existing_quote_for_intake_v3_workspace(db, workspace_id)
    if quote is None:
        return IntakeV3PricingReviewCompletionState(
            review_status="not_created",
            is_intake_v3_quote=False,
            source_workspace_id=workspace_id,
            requires_pricing_review=True,
            pricing_review_completed=False,
            can_complete_pricing_review=False,
            message="No Intake V3 draft quote has been created for this workspace yet.",
        )
    state = get_pricing_review_completion_state_from_quote(quote)
    if state.source_workspace_id and state.source_workspace_id != workspace_id:
        state.warnings.append("WORKSPACE_ID_MISMATCH")
    return state


async def complete_intake_v3_quote_pricing_review(
    db: AsyncSession,
    quote_id: int,
    request: IntakeV3CompletePricingReviewRequest,
    current_user: UserResponse,
) -> IntakeV3CompletePricingReviewResponse:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "quote_not_found", "quote_id": quote_id},
        )

    orders_before = await db.scalar(select(func.count()).select_from(Orders))
    plans_before = await db.scalar(select(func.count()).select_from(ExecutionPlan))

    linkage = _require_iv3_draft_quote(quote)
    validate_pricing_review_can_be_completed(quote, linkage, request, current_user)

    pricing_review_record = build_manual_pricing_review_record(quote, request, current_user)
    updated_notes = update_quote_notes_with_pricing_review(quote.notes, pricing_review_record)
    field_updates = _quote_field_updates(request)
    field_updates["notes"] = updated_notes

    updated = await quotes_service.update(quote.id, field_updates)
    if updated is None:
        _raise_blocked("QUOTE_UPDATE_FAILED", "Quote update failed after pricing review validation.")

    orders_after = await db.scalar(select(func.count()).select_from(Orders))
    plans_after = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    if orders_after != orders_before or plans_after != plans_before:
        _raise_blocked(
            "SAFETY_VIOLATION",
            "Unexpected order or execution side effect detected during pricing review completion.",
        )

    logger.info(
        "Intake V3 manual pricing review completed: quote_id=%s user=%s total=%s",
        quote.id,
        current_user.id,
        request.total,
    )
    return build_priced_draft_quote_response(updated, pricing_review_record)


async def complete_intake_v3_quote_pricing_review_by_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3CompletePricingReviewRequest,
    current_user: UserResponse,
) -> IntakeV3CompletePricingReviewResponse:
    quote = await check_existing_quote_for_intake_v3_workspace(db, workspace_id)
    if quote is None:
        _raise_blocked(
            "DRAFT_QUOTE_NOT_CREATED",
            "No Intake V3 draft quote exists for this workspace.",
        )
    return await complete_intake_v3_quote_pricing_review(db, quote.id, request, current_user)
