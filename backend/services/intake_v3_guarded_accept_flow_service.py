"""Intake V3 guarded accept flow — priced draft to accepted, no Order/Execution/Inventory/CostEngine."""

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
    IntakeV3AcceptDecisionRecord,
    IntakeV3AcceptQuoteRequest,
    IntakeV3AcceptQuoteResponse,
    IntakeV3AcceptState,
)
from services.intake_v3_quote_linkage_utils import (
    ACCEPT_DECISION_JSON_KEY,
    IV3_ACCEPTED_STATUS,
    get_accept_decision_record,
    is_iv3_accept_completed,
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
from validators.status_lifecycle import validate_transition

logger = logging.getLogger(__name__)

ACCEPT_DECISION_APPROVED = "approved"
INTERMEDIATE_PRICED_STATUS = "priced"


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
        _raise_blocked("NOTES_EMPTY", "Quote notes are empty — cannot accept IV3 quote.")
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
    pricing_review = linkage.get("pricing_review")
    if isinstance(pricing_review, dict) and float(pricing_review.get("total") or 0) > 0:
        return True
    return False


def _validate_priced_draft_ready(quote: Quotes, linkage: dict[str, Any]) -> None:
    if is_iv3_accept_completed(linkage, quote.status):
        _raise_blocked("ACCEPT_ALREADY_COMPLETED", "Quote has already been accepted via IV3 guarded flow.")
    if quote.status not in ("draft", INTERMEDIATE_PRICED_STATUS):
        _raise_blocked(
            "QUOTE_STATUS_NOT_ACCEPTABLE",
            f"IV3 guarded accept requires draft or priced status; got {quote.status!r}.",
        )
    if not is_pricing_review_completed(linkage):
        _raise_blocked("PRICING_REVIEW_REQUIRED", "Manual pricing review must be completed before accept.")
    if bool(linkage.get("requires_pricing_review", True)):
        _raise_blocked("PRICING_REVIEW_REQUIRED", "Quote still requires pricing review.")
    if not bool(linkage.get("priced_draft")) and not is_pricing_review_completed(linkage):
        _raise_blocked("PRICED_DRAFT_REQUIRED", "Quote is not marked as a priced draft.")
    if not _final_price_present(quote, linkage):
        _raise_blocked("FINAL_PRICE_MISSING", "Final commercial price is not present on the quote.")
    snapshot = linkage.get("snapshot")
    if not isinstance(snapshot, dict) or not snapshot:
        _raise_blocked("SNAPSHOT_MISSING", "Intake V3 snapshot is missing from quote notes.")
    if not isinstance(linkage.get("owner_decision"), dict):
        _raise_blocked("OWNER_DECISION_MISSING", "Owner decision record is missing from quote notes.")


def validate_iv3_quote_can_be_accepted(
    quote: Quotes,
    linkage: dict[str, Any],
    request: IntakeV3AcceptQuoteRequest,
    current_user: UserResponse,
) -> None:
    del current_user
    _validate_priced_draft_ready(quote, linkage)

    if request.accept_decision != ACCEPT_DECISION_APPROVED:
        _raise_blocked("ACCEPT_DECISION_INVALID", "accept_decision must be approved.")
    if not request.accept_reason.strip():
        _raise_blocked("ACCEPT_REASON_REQUIRED", "accept_reason is required.")
    if not all(
        (
            request.reviewer_confirmation,
            request.confirm_pricing_review_completed,
            request.confirm_quote_stays_commercial,
            request.confirm_no_order,
            request.confirm_no_execution,
            request.confirm_no_inventory,
            request.confirm_convert_separate,
        )
    ):
        _raise_blocked("CONFIRMATIONS_REQUIRED", "All accept confirmations must be true.")

    if request.expected_quote_id is not None and request.expected_quote_id != quote.id:
        _raise_blocked("QUOTE_ID_MISMATCH", "expected_quote_id does not match quote.")
    if request.expected_intake_code and request.expected_intake_code != quote.intake_code:
        _raise_blocked("INTAKE_CODE_MISMATCH", "expected_intake_code does not match quote.")


def build_iv3_accept_decision_record(
    quote: Quotes,
    request: IntakeV3AcceptQuoteRequest,
    current_user: UserResponse,
    *,
    quote_status_before: str,
    quote_status_after: str,
) -> dict[str, Any]:
    display_name = getattr(current_user, "full_name", None) or getattr(current_user, "email", None) or str(
        current_user.id
    )
    return {
        "status": ACCEPT_DECISION_APPROVED,
        "accepted_at": datetime.now(timezone.utc).isoformat(),
        "accepted_by_user_id": str(current_user.id),
        "accepted_by_display_name": display_name,
        "reason": request.accept_reason.strip(),
        "source": request.acceptance_source,
        "pricing_review_completed": True,
        "quote_status_before": quote_status_before,
        "quote_status_after": quote_status_after,
        "order_created": False,
        "execution_plan_created": False,
        "execution_task_created": False,
        "inventory_mutated": False,
        "convert_separate": True,
    }


def update_quote_notes_with_iv3_accept_decision(
    notes: str | None,
    accept_decision_record: dict[str, Any],
) -> str:
    payload = _load_notes_payload(notes)
    linkage = payload.get(INTAKE_V3_LINKAGE_JSON_KEY)
    if not isinstance(linkage, dict):
        _raise_blocked(
            "LINKAGE_MISSING",
            "Cannot update accept decision — intake_v3_linkage_v1 missing from notes.",
        )
    linkage[ACCEPT_DECISION_JSON_KEY] = accept_decision_record
    payload[INTAKE_V3_LINKAGE_JSON_KEY] = linkage
    return json.dumps(payload, ensure_ascii=False)


def _resolve_accept_transitions(current_status: str) -> None:
    """Validate lifecycle transitions for IV3 guarded accept."""
    if current_status == "draft":
        try:
            validate_transition("quotes", "draft", INTERMEDIATE_PRICED_STATUS)
            validate_transition("quotes", INTERMEDIATE_PRICED_STATUS, IV3_ACCEPTED_STATUS)
        except ValueError as exc:
            _raise_blocked("TRANSITION_BLOCKED", str(exc))
        return
    if current_status == INTERMEDIATE_PRICED_STATUS:
        try:
            validate_transition("quotes", INTERMEDIATE_PRICED_STATUS, IV3_ACCEPTED_STATUS)
        except ValueError as exc:
            _raise_blocked("TRANSITION_BLOCKED", str(exc))
        return
    _raise_blocked(
        "TRANSITION_BLOCKED",
        f"Cannot accept IV3 quote from status {current_status!r}.",
    )


def build_iv3_accept_response(
    quote: Quotes,
    accept_decision_record: dict[str, Any],
    *,
    quote_status_before: str,
) -> IntakeV3AcceptQuoteResponse:
    return IntakeV3AcceptQuoteResponse(
        accepted=True,
        quote_id=quote.id,
        quote_code=quote.code,
        quote_status_before=quote_status_before,
        quote_status_after=quote.status,
        source_module=INTAKE_V3_SOURCE_MODULE,
        accept_decision_record_attached=True,
        pricing_review_completed=True,
        order_created=False,
        execution_plan_created=False,
        execution_task_created=False,
        inventory_mutated=False,
        can_convert_now=False,
        convert_action_enabled=False,
    )


def build_iv3_accept_state_from_quote(quote: Quotes, linkage: dict[str, Any] | None) -> IntakeV3AcceptState:
    if linkage is None or not quote.intake_code or not str(quote.intake_code).startswith(INTAKE_V3_LINKAGE_CODE_PREFIX):
        return IntakeV3AcceptState(
            review_status="not_applicable",
            is_intake_v3_quote=False,
            quote_id=quote.id,
            message="Quote is not an Intake V3 quote.",
        )

    accepted = is_iv3_accept_completed(linkage, quote.status)
    pricing_completed = is_pricing_review_completed(linkage)
    blockers: list[str] = []

    if accepted:
        record = get_accept_decision_record(linkage)
        return IntakeV3AcceptState(
            review_status="accepted",
            is_intake_v3_quote=True,
            quote_id=quote.id,
            quote_code=quote.code,
            quote_status=quote.status,
            intake_code=quote.intake_code,
            source_workspace_id=str(linkage.get("source_workspace_id") or "") or None,
            pricing_review_completed=pricing_completed,
            priced_draft=bool(linkage.get("priced_draft")),
            accept_completed=True,
            can_accept_now=False,
            accept_action_enabled=False,
            accept_blockers=[],
            accept_decision_summary=IntakeV3AcceptDecisionRecord.model_validate(record) if record else None,
        )

    if not pricing_completed or bool(linkage.get("requires_pricing_review", True)):
        blockers.append("PRICING_REVIEW_REQUIRED")
    if quote.status not in ("draft", INTERMEDIATE_PRICED_STATUS):
        blockers.append("QUOTE_STATUS_NOT_ACCEPTABLE")
    if not _final_price_present(quote, linkage):
        blockers.append("FINAL_PRICE_MISSING")

    can_accept = len(blockers) == 0
    return IntakeV3AcceptState(
        review_status="ready_for_guarded_accept" if can_accept else "blocked",
        is_intake_v3_quote=True,
        quote_id=quote.id,
        quote_code=quote.code,
        quote_status=quote.status,
        intake_code=quote.intake_code,
        source_workspace_id=str(linkage.get("source_workspace_id") or "") or None,
        pricing_review_completed=pricing_completed,
        priced_draft=bool(linkage.get("priced_draft")),
        accept_completed=False,
        can_accept_now=can_accept,
        accept_action_enabled=can_accept,
        accept_blockers=blockers,
    )


async def get_iv3_accept_state(db: AsyncSession, quote_id: int) -> IntakeV3AcceptState:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        return IntakeV3AcceptState(
            review_status="quote_missing",
            is_intake_v3_quote=False,
            quote_id=quote_id,
            message=f"Quote id={quote_id} was not found.",
        )
    linkage = parse_intake_v3_linkage_from_notes(quote.notes)
    return build_iv3_accept_state_from_quote(quote, linkage)


async def get_iv3_accept_state_by_workspace(db: AsyncSession, workspace_id: str) -> IntakeV3AcceptState:
    quote = await check_existing_quote_for_intake_v3_workspace(db, workspace_id)
    if quote is None:
        return IntakeV3AcceptState(
            review_status="not_created",
            is_intake_v3_quote=False,
            source_workspace_id=workspace_id,
            message="No Intake V3 draft quote has been created for this workspace yet.",
        )
    state = await get_iv3_accept_state(db, quote.id)
    if state.source_workspace_id and state.source_workspace_id != workspace_id:
        state.warnings.append("WORKSPACE_ID_MISMATCH")
    return state


async def accept_iv3_priced_draft_quote(
    db: AsyncSession,
    quote_id: int,
    request: IntakeV3AcceptQuoteRequest,
    current_user: UserResponse,
) -> IntakeV3AcceptQuoteResponse:
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
    validate_iv3_quote_can_be_accepted(quote, linkage, request, current_user)

    quote_status_before = quote.status
    _resolve_accept_transitions(quote_status_before)

    accept_record = build_iv3_accept_decision_record(
        quote,
        request,
        current_user,
        quote_status_before=quote_status_before,
        quote_status_after=IV3_ACCEPTED_STATUS,
    )
    updated_notes = update_quote_notes_with_iv3_accept_decision(quote.notes, accept_record)

    working_quote = quote
    if quote_status_before == "draft":
        intermediate = await quotes_service.update(quote.id, {"status": INTERMEDIATE_PRICED_STATUS})
        if intermediate is None:
            _raise_blocked("QUOTE_UPDATE_FAILED", "Failed to set intermediate priced status.")
        working_quote = intermediate

    validate_transition("quotes", working_quote.status, IV3_ACCEPTED_STATUS)
    updated = await quotes_service.update(
        quote.id,
        {"status": IV3_ACCEPTED_STATUS, "notes": updated_notes},
    )
    if updated is None:
        _raise_blocked("QUOTE_UPDATE_FAILED", "Quote update failed after accept validation.")

    orders_after = await db.scalar(select(func.count()).select_from(Orders))
    plans_after = await db.scalar(select(func.count()).select_from(ExecutionPlan))
    if orders_after != orders_before or plans_after != plans_before:
        _raise_blocked(
            "SAFETY_VIOLATION",
            "Unexpected order or execution side effect detected during IV3 accept.",
        )

    logger.info(
        "Intake V3 guarded accept completed: quote_id=%s user=%s status=%s->%s",
        quote.id,
        current_user.id,
        quote_status_before,
        IV3_ACCEPTED_STATUS,
    )
    return build_iv3_accept_response(
        updated,
        accept_record,
        quote_status_before=quote_status_before,
    )


async def accept_iv3_priced_draft_quote_by_workspace(
    db: AsyncSession,
    workspace_id: str,
    request: IntakeV3AcceptQuoteRequest,
    current_user: UserResponse,
) -> IntakeV3AcceptQuoteResponse:
    quote = await check_existing_quote_for_intake_v3_workspace(db, workspace_id)
    if quote is None:
        _raise_blocked(
            "DRAFT_QUOTE_NOT_CREATED",
            "No Intake V3 draft quote has been created for this workspace yet.",
        )
    if request.expected_intake_code is None:
        request.expected_intake_code = quote.intake_code
    if request.expected_quote_id is None:
        request.expected_quote_id = quote.id
    return await accept_iv3_priced_draft_quote(db, quote.id, request, current_user)
