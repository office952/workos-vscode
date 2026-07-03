"""Intake V3 guarded convert to order — Order only, no Execution/Inventory/CostEngine."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from data_models.product_contracts import iso_now
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from schemas.auth import UserResponse
from schemas.intake_v3 import (
    IntakeV3ConvertDecisionRecord,
    IntakeV3ConvertToOrderRequest,
    IntakeV3ConvertToOrderResponse,
    IntakeV3ConvertToOrderState,
    IntakeV3OrderSnapshotPayload,
)
from services.company_commercial_settings_service import get_eur_to_ron_rate
from services.intake_v3_quote_linkage_utils import (
    CONVERT_DECISION_JSON_KEY,
    IV3_ACCEPTED_STATUS,
    IV3_ORDER_LINKAGE_JSON_KEY,
    IV3_ORDER_STATUS_LOCKED,
    get_convert_decision_record,
    get_pricing_review_record,
    is_iv3_accept_completed,
    is_iv3_convert_completed,
    is_pricing_review_completed,
)
from services.intake_v3_real_commercial_quote_creation_service import (
    INTAKE_V3_LINKAGE_CODE_PREFIX,
    INTAKE_V3_LINKAGE_JSON_KEY,
    INTAKE_V3_SOURCE_MODULE,
    check_existing_quote_for_intake_v3_workspace,
    parse_intake_v3_linkage_from_notes,
)
from services.order_currency_conversion_service import convert_quote_totals_to_order_base
from services.orders import OrdersService
from services.quotes import QuotesService

logger = logging.getLogger(__name__)

CONVERT_DECISION_APPROVED = "approved"


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
        _raise_blocked("NOTES_EMPTY", "Quote notes are empty — cannot convert IV3 quote.")
    try:
        payload = json.loads(notes)
    except json.JSONDecodeError as exc:
        _raise_blocked("NOTES_JSON_INVALID", f"Quote notes are not valid JSON: {exc.msg}")
    if not isinstance(payload, dict):
        _raise_blocked("NOTES_JSON_INVALID", "Quote notes JSON root must be an object.")
    return payload


def _require_iv3_linkage(quote: Quotes) -> dict[str, Any]:
    if not quote.intake_code or not str(quote.intake_code).startswith(INTAKE_V3_LINKAGE_CODE_PREFIX):
        _raise_blocked("NOT_IV3_QUOTE", "Quote intake_code is not an Intake V3 linkage code.")
    _load_notes_payload(quote.notes)
    linkage = parse_intake_v3_linkage_from_notes(quote.notes)
    if linkage is None:
        _raise_blocked("NOT_IV3_QUOTE", "Quote is not linked to Intake V3.")
    return linkage


def _final_price_present(quote: Quotes, linkage: dict[str, Any]) -> bool:
    if float(quote.grand_total or 0) > 0:
        return True
    record = get_pricing_review_record(linkage)
    if record and float(record.get("total") or 0) > 0:
        return True
    return False


def _linkage_has_snapshot(linkage: dict[str, Any]) -> bool:
    snapshot = linkage.get("snapshot")
    return isinstance(snapshot, dict) and bool(snapshot)


async def check_existing_order_for_iv3_quote(db: AsyncSession, quote_id: int) -> Orders | None:
    orders_service = OrdersService(db)
    existing = await orders_service.get_list(
        skip=0,
        limit=1,
        query_dict={"quote_id": quote_id},
        sort="id",
    )
    items = existing.get("items", [])
    return items[0] if items else None


def validate_iv3_quote_can_convert_to_order(
    quote: Quotes,
    linkage: dict[str, Any],
    request: IntakeV3ConvertToOrderRequest,
    *,
    existing_order: Orders | None = None,
) -> None:
    if is_iv3_convert_completed(linkage):
        _raise_blocked("CONVERT_ALREADY_COMPLETED", "Quote has already been converted via IV3 guarded flow.")
    if existing_order is not None:
        _raise_blocked(
            "ORDER_ALREADY_EXISTS",
            f"An order already exists for quote id={quote.id}.",
            ["ORDER_ALREADY_EXISTS"],
        )
    if not is_iv3_accept_completed(linkage, quote.status):
        _raise_blocked("QUOTE_NOT_ACCEPTED", "Quote must be accepted before guarded convert.")
    if quote.status != IV3_ACCEPTED_STATUS:
        _raise_blocked(
            "QUOTE_STATUS_NOT_ACCEPTED",
            f"IV3 guarded convert requires accepted status; got {quote.status!r}.",
        )
    if not is_pricing_review_completed(linkage):
        _raise_blocked("PRICING_REVIEW_REQUIRED", "Manual pricing review must be completed before convert.")
    if not _final_price_present(quote, linkage):
        _raise_blocked("FINAL_PRICE_MISSING", "Final commercial price is not present on the quote.")
    if not _linkage_has_snapshot(linkage):
        _raise_blocked("SNAPSHOT_MISSING", "Intake V3 snapshot is missing from quote notes.")

    if request.convert_decision != CONVERT_DECISION_APPROVED:
        _raise_blocked("CONVERT_DECISION_INVALID", "convert_decision must be approved.")
    if not request.convert_reason.strip():
        _raise_blocked("CONVERT_REASON_REQUIRED", "convert_reason is required.")
    if not all(
        (
            request.reviewer_confirmation,
            request.confirm_quote_accepted,
            request.confirm_pricing_review_completed,
            request.confirm_create_order_only,
            request.confirm_no_execution_plan,
            request.confirm_no_execution_tasks,
            request.confirm_no_inventory,
            request.confirm_production_separate,
        )
    ):
        _raise_blocked("CONFIRMATIONS_REQUIRED", "All convert confirmations must be true.")

    if request.expected_quote_id is not None and request.expected_quote_id != quote.id:
        _raise_blocked("QUOTE_ID_MISMATCH", "expected_quote_id does not match quote.")
    if request.expected_intake_code and request.expected_intake_code != quote.intake_code:
        _raise_blocked("INTAKE_CODE_MISMATCH", "expected_intake_code does not match quote.")


def build_iv3_convert_decision_record(
    quote: Quotes,
    request: IntakeV3ConvertToOrderRequest,
    current_user: UserResponse,
    *,
    order: Orders,
) -> dict[str, Any]:
    display_name = getattr(current_user, "full_name", None) or getattr(current_user, "email", None) or str(
        current_user.id
    )
    return {
        "status": CONVERT_DECISION_APPROVED,
        "converted_at": datetime.now(timezone.utc).isoformat(),
        "converted_by_user_id": str(current_user.id),
        "converted_by_display_name": display_name,
        "reason": request.convert_reason.strip(),
        "source": request.conversion_source,
        "quote_status": quote.status,
        "order_id": order.id,
        "order_code": order.code,
        "order_status": order.status,
        "order_created": True,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "production_started": False,
        "production_separate": True,
    }


def build_iv3_order_snapshot_payload(
    quote: Quotes,
    linkage: dict[str, Any],
    *,
    currency_handoff: dict[str, Any],
    final_price: dict[str, Any],
) -> dict[str, Any]:
    workspace_id = str(linkage.get("source_workspace_id") or "") or None
    order_linkage = {
        "source_module": INTAKE_V3_SOURCE_MODULE,
        "source_quote_id": quote.id,
        "source_workspace_id": workspace_id,
        "quote_intake_code": quote.intake_code,
        "quote_code": quote.code,
        "created_from_guarded_convert": True,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "production_started": False,
    }
    pricing_review = get_pricing_review_record(linkage)
    return {
        "source_module": INTAKE_V3_SOURCE_MODULE,
        "snapshot_type": "intake_v3_guarded_convert_order_snapshot_v1",
        IV3_ORDER_LINKAGE_JSON_KEY: order_linkage,
        "final_price": final_price,
        "commercial_currency_handoff": currency_handoff,
        "pricing_review_summary": pricing_review,
        "iv3_snapshot_ref": {
            "source_workspace_id": workspace_id,
            "quote_intake_code": quote.intake_code,
            "snapshot_policy_version": linkage.get("snapshot_policy_version"),
        },
        "production_started": False,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
    }


def update_quote_notes_with_iv3_convert_decision(
    notes: str | None,
    convert_decision_record: dict[str, Any],
) -> str:
    payload = _load_notes_payload(notes)
    linkage = payload.get(INTAKE_V3_LINKAGE_JSON_KEY)
    if not isinstance(linkage, dict):
        _raise_blocked(
            "LINKAGE_MISSING",
            "Cannot update convert decision — intake_v3_linkage_v1 missing from notes.",
        )
    linkage[CONVERT_DECISION_JSON_KEY] = convert_decision_record
    payload[INTAKE_V3_LINKAGE_JSON_KEY] = linkage
    return json.dumps(payload, ensure_ascii=False)


async def create_or_delegate_order_from_iv3_quote(
    db: AsyncSession,
    quote: Quotes,
    linkage: dict[str, Any],
    request: IntakeV3ConvertToOrderRequest,
    current_user: UserResponse,
) -> Orders:
    del request, current_user
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
        code = str(exc)
        if code in {"eur_to_ron_rate_missing", "eur_to_ron_rate_invalid"}:
            _raise_blocked(
                code.upper(),
                "Set EUR/RON rate in Settings before converting IV3 quote to order.",
            )
        _raise_blocked("CURRENCY_CONVERSION_FAILED", code)

    final_price = {
        "net": currency_handoff.base_total_net if currency_handoff.base_total_net is not None else net_total,
        "gross": currency_handoff.base_total_ron,
        "commercial_currency": currency_handoff.commercial_currency,
    }
    currency_handoff_dict = currency_handoff.to_dict()
    snapshot_dict = build_iv3_order_snapshot_payload(
        quote,
        linkage,
        currency_handoff=currency_handoff_dict,
        final_price=final_price,
    )

    order_code = f"ORD-{int(datetime.now(timezone.utc).timestamp())}-{quote.id}"
    order_notes_payload = {IV3_ORDER_LINKAGE_JSON_KEY: snapshot_dict[IV3_ORDER_LINKAGE_JSON_KEY]}
    readiness_snapshot = {
        "source": "intake_v3_guarded_convert",
        "snapshot_type": "intake_v3_accepted_quote_at_order_creation",
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "quote_status": quote.status,
        "requires_production_handoff_build": True,
        "production_started": False,
        "execution_plan_created": False,
        "inventory_mutated": False,
    }

    orders_service = OrdersService(db)
    order_data = {
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
    order = await orders_service.create(order_data)
    if order is None:
        _raise_blocked("ORDER_CREATE_FAILED", "Order persistence failed.")

    snapshot_dict["order_id"] = order.id
    order.snapshot_line_items = json.dumps(snapshot_dict, ensure_ascii=False)
    await db.commit()
    await db.refresh(order)
    return order


def build_iv3_convert_to_order_response(
    quote: Quotes,
    order: Orders,
) -> IntakeV3ConvertToOrderResponse:
    return IntakeV3ConvertToOrderResponse(
        converted=True,
        quote_id=quote.id,
        quote_code=quote.code,
        quote_status=quote.status,
        order_id=order.id,
        order_code=order.code,
        order_status=order.status,
        source_module=INTAKE_V3_SOURCE_MODULE,
        convert_decision_record_attached=True,
        order_created=True,
        execution_plan_created=False,
        execution_task_created=False,
        inventory_mutated=False,
        production_started=False,
        can_start_production_now=False,
    )


def build_iv3_convert_to_order_state_from_quote(
    quote: Quotes,
    linkage: dict[str, Any] | None,
    *,
    existing_order: Orders | None = None,
) -> IntakeV3ConvertToOrderState:
    if linkage is None or not quote.intake_code or not str(quote.intake_code).startswith(INTAKE_V3_LINKAGE_CODE_PREFIX):
        return IntakeV3ConvertToOrderState(
            review_status="not_applicable",
            is_intake_v3_quote=False,
            quote_id=quote.id,
            message="Quote is not an Intake V3 quote.",
        )

    converted = is_iv3_convert_completed(linkage) or existing_order is not None
    accept_completed = is_iv3_accept_completed(linkage, quote.status)
    pricing_completed = is_pricing_review_completed(linkage)
    blockers: list[str] = []

    if converted and existing_order is not None:
        record = get_convert_decision_record(linkage)
        summary = IntakeV3ConvertDecisionRecord.model_validate(record) if record else None
        return IntakeV3ConvertToOrderState(
            review_status="converted_to_order",
            is_intake_v3_quote=True,
            quote_id=quote.id,
            quote_code=quote.code,
            quote_status=quote.status,
            intake_code=quote.intake_code,
            source_workspace_id=str(linkage.get("source_workspace_id") or "") or None,
            accept_completed=accept_completed,
            pricing_review_completed=pricing_completed,
            order_exists=True,
            existing_order_id=existing_order.id,
            existing_order_code=existing_order.code,
            convert_completed=True,
            can_convert_now=False,
            convert_action_enabled=False,
            convert_blockers=[],
            convert_decision_summary=summary,
        )

    if not accept_completed or quote.status != IV3_ACCEPTED_STATUS:
        blockers.append("QUOTE_NOT_ACCEPTED")
    if not pricing_completed:
        blockers.append("PRICING_REVIEW_REQUIRED")
    if not _linkage_has_snapshot(linkage):
        blockers.append("SNAPSHOT_MISSING")
    if not _final_price_present(quote, linkage):
        blockers.append("FINAL_PRICE_MISSING")

    can_convert = len(blockers) == 0
    snapshot_summary = None
    if can_convert:
        snapshot_summary = IntakeV3OrderSnapshotPayload(
            source_quote_id=quote.id,
            source_workspace_id=str(linkage.get("source_workspace_id") or "") or None,
            quote_intake_code=quote.intake_code,
            quote_code=quote.code,
        )

    return IntakeV3ConvertToOrderState(
        review_status="ready_for_guarded_convert" if can_convert else "blocked",
        is_intake_v3_quote=True,
        quote_id=quote.id,
        quote_code=quote.code,
        quote_status=quote.status,
        intake_code=quote.intake_code,
        source_workspace_id=str(linkage.get("source_workspace_id") or "") or None,
        accept_completed=accept_completed,
        pricing_review_completed=pricing_completed,
        order_exists=False,
        convert_completed=False,
        can_convert_now=can_convert,
        convert_action_enabled=can_convert,
        convert_blockers=blockers,
        order_snapshot_summary=snapshot_summary,
    )


async def get_iv3_convert_to_order_state(db: AsyncSession, quote_id: int) -> IntakeV3ConvertToOrderState:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        return IntakeV3ConvertToOrderState(
            review_status="quote_missing",
            is_intake_v3_quote=False,
            quote_id=quote_id,
            message=f"Quote id={quote_id} was not found.",
        )
    linkage = parse_intake_v3_linkage_from_notes(quote.notes)
    existing_order = await check_existing_order_for_iv3_quote(db, quote_id)
    return build_iv3_convert_to_order_state_from_quote(quote, linkage, existing_order=existing_order)


async def get_iv3_convert_to_order_state_by_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3ConvertToOrderState:
    quote = await check_existing_quote_for_intake_v3_workspace(db, workspace_id)
    if quote is None:
        return IntakeV3ConvertToOrderState(
            review_status="not_created",
            is_intake_v3_quote=False,
            source_workspace_id=workspace_id,
            message="No Intake V3 quote has been created for this workspace yet.",
        )
    state = await get_iv3_convert_to_order_state(db, quote.id)
    if state.source_workspace_id and state.source_workspace_id != workspace_id:
        state.warnings.append("WORKSPACE_ID_MISMATCH")
    return state


async def convert_iv3_accepted_quote_to_order(
    db: AsyncSession,
    quote_id: int,
    request: IntakeV3ConvertToOrderRequest,
    current_user: UserResponse,
) -> IntakeV3ConvertToOrderResponse:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "quote_not_found", "quote_id": quote_id},
        )

    orders_before = await db.scalar(select(func.count()).select_from(Orders))
    plans_before = await db.scalar(select(func.count()).select_from(ExecutionPlan))

    linkage = _require_iv3_linkage(quote)
    existing_order = await check_existing_order_for_iv3_quote(db, quote_id)
    validate_iv3_quote_can_convert_to_order(
        quote,
        linkage,
        request,
        existing_order=existing_order,
    )

    order = await create_or_delegate_order_from_iv3_quote(
        db,
        quote,
        linkage,
        request,
        current_user,
    )
    convert_record = build_iv3_convert_decision_record(quote, request, current_user, order=order)
    updated_notes = update_quote_notes_with_iv3_convert_decision(quote.notes, convert_record)
    updated = await quotes_service.update(quote.id, {"notes": updated_notes})
    if updated is None:
        _raise_blocked("QUOTE_UPDATE_FAILED", "Failed to attach convert decision to quote notes.")

    orders_after = await db.scalar(select(func.count()).select_from(Orders))
    plans_after = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    if orders_after != orders_before + 1 or plans_after != plans_before:
        _raise_blocked(
            "SAFETY_VIOLATION",
            "Unexpected side effect detected during IV3 guarded convert.",
        )

    logger.info(
        "Intake V3 guarded convert completed: quote_id=%s order_id=%s user=%s",
        quote.id,
        order.id,
        current_user.id,
    )
    return build_iv3_convert_to_order_response(updated, order)


async def convert_iv3_accepted_quote_to_order_by_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3ConvertToOrderRequest,
    current_user: UserResponse,
) -> IntakeV3ConvertToOrderResponse:
    quote = await check_existing_quote_for_intake_v3_workspace(db, workspace_id)
    if quote is None:
        _raise_blocked(
            "DRAFT_QUOTE_NOT_CREATED",
            "No Intake V3 quote has been created for this workspace yet.",
        )
    if request.expected_intake_code is None:
        request.expected_intake_code = quote.intake_code
    if request.expected_quote_id is None:
        request.expected_quote_id = quote.id
    return await convert_iv3_accepted_quote_to_order(db, quote.id, request, current_user)
