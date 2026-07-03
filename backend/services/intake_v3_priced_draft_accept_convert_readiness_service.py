"""Intake V3 priced draft accept/convert readiness — read-only audit, actions remain blocked."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.quotes import Quotes
from schemas.intake_v3 import (
    IntakeV3PricedDraftAcceptConvertReadiness,
    IntakeV3QuoteAcceptConvertNextStep,
    IntakeV3QuoteAcceptGuardContract,
    IntakeV3QuoteAcceptReadiness,
    IntakeV3QuoteConvertGuardContract,
    IntakeV3QuoteConvertReadiness,
    IntakeV3QuoteReadinessBlocker,
    IntakeV3QuoteReadinessWarning,
)
from services.intake_v3_draft_quote_review_service import (
    parse_intake_v3_quote_notes,
    quote_is_intake_v3_draft,
)
from services.intake_v3_quote_linkage_utils import (
    get_pricing_review_record,
    is_iv3_accept_completed,
    is_iv3_convert_completed,
    is_pricing_review_completed,
)
from services.intake_v3_real_commercial_quote_creation_service import (
    INTAKE_V3_LINKAGE_CODE_PREFIX,
    check_existing_quote_for_intake_v3_workspace,
)
from services.intake_v3_guarded_convert_to_order_service import check_existing_order_for_iv3_quote
from services.intake_v3_order_production_readiness_service import (
    build_iv3_order_production_readiness_response,
    load_iv3_order_linkage,
)
from services.orders import OrdersService
from services.quotes import QuotesService

CONVERT_ACTION_BUILD = "INTAKE_V3_GUARDED_CONVERT_FLOW"


def build_iv3_accept_guard_contract() -> IntakeV3QuoteAcceptGuardContract:
    return IntakeV3QuoteAcceptGuardContract(
        requires_priced_draft=True,
        requires_pricing_review_completed=True,
        requires_owner_confirmation=True,
        requires_no_order_created=True,
        requires_no_execution_created=True,
        next_build_required=False,
    )


def build_iv3_convert_guard_contract() -> IntakeV3QuoteConvertGuardContract:
    return IntakeV3QuoteConvertGuardContract(
        requires_accepted_quote=True,
        requires_duplicate_order_check=True,
        requires_order_snapshot=True,
        requires_no_execution_creation_in_same_step=True,
        next_build_required=False,
    )


def _blocker(code: str, message: str) -> IntakeV3QuoteReadinessBlocker:
    return IntakeV3QuoteReadinessBlocker(code=code, message=message)


def _warning(code: str, message: str) -> IntakeV3QuoteReadinessWarning:
    return IntakeV3QuoteReadinessWarning(code=code, message=message)


def _linkage_has_snapshot(linkage: dict[str, Any] | None) -> bool:
    if not isinstance(linkage, dict):
        return False
    snapshot = linkage.get("snapshot")
    return isinstance(snapshot, dict) and bool(snapshot)


def _linkage_has_owner_decision(linkage: dict[str, Any] | None) -> bool:
    return isinstance(linkage, dict) and isinstance(linkage.get("owner_decision"), dict)


def _linkage_has_production_handoff_preview(linkage: dict[str, Any] | None) -> bool:
    if not isinstance(linkage, dict):
        return False
    snapshot = linkage.get("snapshot")
    if isinstance(snapshot, dict):
        sections = snapshot.get("sections")
        if isinstance(sections, dict):
            preview = sections.get("production_handoff_preview")
            if isinstance(preview, dict) and preview:
                return True
    preview = linkage.get("production_handoff_preview")
    return isinstance(preview, dict) and bool(preview)


def _final_price_present(quote: Quotes, linkage: dict[str, Any] | None) -> bool:
    if float(quote.grand_total or 0) > 0:
        return True
    record = get_pricing_review_record(linkage)
    if record and float(record.get("total") or 0) > 0:
        return True
    return False


def build_iv3_quote_accept_blockers(
    quote: Quotes,
    linkage: dict[str, Any] | None,
    *,
    notes_warnings: list[str] | None = None,
    order_exists: bool = False,
    execution_plan_exists: bool = False,
) -> list[IntakeV3QuoteReadinessBlocker]:
    blockers: list[IntakeV3QuoteReadinessBlocker] = []

    if notes_warnings:
        for code in notes_warnings:
            if code in {"NOTES_JSON_INVALID", "LINKAGE_MISSING", "NOTES_EMPTY"}:
                blockers.append(_blocker(code, "Quote notes linkage is invalid or missing."))

    if not quote.intake_code or not str(quote.intake_code).startswith(INTAKE_V3_LINKAGE_CODE_PREFIX):
        blockers.append(_blocker("NOT_IV3_QUOTE", "Quote is not linked to Intake V3."))
        return blockers

    if linkage is None:
        blockers.append(_blocker("LINKAGE_MISSING", "Intake V3 linkage is missing from quote notes."))
        return blockers

    if is_iv3_accept_completed(linkage, quote.status):
        return []

    if quote.status not in ("draft", "priced"):
        blockers.append(
            _blocker(
                "QUOTE_STATUS_NOT_ACCEPTABLE",
                f"IV3 accept expects draft or priced status; got {quote.status!r}.",
            )
        )

    if not is_pricing_review_completed(linkage) or bool(linkage.get("requires_pricing_review", True)):
        blockers.append(
            _blocker("PRICING_REVIEW_REQUIRED", "Manual pricing review must be completed first.")
        )

    if not _linkage_has_snapshot(linkage):
        blockers.append(_blocker("SNAPSHOT_MISSING", "Intake V3 snapshot is missing from quote notes."))

    if not _linkage_has_owner_decision(linkage):
        blockers.append(_blocker("OWNER_DECISION_MISSING", "Owner decision record is missing from quote notes."))

    if not bool(linkage.get("priced_draft")) and not is_pricing_review_completed(linkage):
        blockers.append(_blocker("PRICED_DRAFT_REQUIRED", "Quote is not marked as a priced draft."))

    if not _final_price_present(quote, linkage):
        blockers.append(_blocker("FINAL_PRICE_MISSING", "Final commercial price is not present on the quote."))

    if order_exists:
        blockers.append(_blocker("ORDER_ALREADY_EXISTS", "An order already exists for this quote."))

    if execution_plan_exists:
        blockers.append(_blocker("EXECUTION_PLAN_EXISTS", "An execution plan already exists for this quote order."))

    return blockers


def build_iv3_quote_convert_blockers(
    quote: Quotes,
    linkage: dict[str, Any] | None,
    *,
    accept_blockers: list[IntakeV3QuoteReadinessBlocker],
    order_exists: bool = False,
) -> list[IntakeV3QuoteReadinessBlocker]:
    blockers: list[IntakeV3QuoteReadinessBlocker] = []

    pricing_codes = {b.code for b in accept_blockers if b.code == "PRICING_REVIEW_REQUIRED"}
    if pricing_codes:
        blockers.append(_blocker("PRICING_REVIEW_REQUIRED", "Pricing review must be completed before convert readiness."))
        return blockers

    if quote.status not in ("accepted",):
        blockers.append(
            _blocker(
                "QUOTE_NOT_ACCEPTED",
                "Quote must be accepted before convert readiness can be evaluated.",
            )
        )

    if order_exists:
        blockers.append(_blocker("ORDER_ALREADY_EXISTS", "An order already exists for this quote."))

    return blockers


def evaluate_iv3_quote_accept_readiness(
    quote: Quotes,
    linkage: dict[str, Any] | None,
    *,
    notes_warnings: list[str] | None = None,
    order_exists: bool = False,
    execution_plan_exists: bool = False,
) -> IntakeV3QuoteAcceptReadiness:
    if linkage and is_iv3_accept_completed(linkage, quote.status):
        return IntakeV3QuoteAcceptReadiness(
            accept_readiness_status="accepted",
            can_accept_now=False,
            accept_action_enabled=False,
            is_accept_ready_preview=False,
            accept_blockers=[],
            accept_guard_contract=build_iv3_accept_guard_contract(),
        )

    blockers = build_iv3_quote_accept_blockers(
        quote,
        linkage,
        notes_warnings=notes_warnings,
        order_exists=order_exists,
        execution_plan_exists=execution_plan_exists,
    )
    pricing_blocked = any(b.code == "PRICING_REVIEW_REQUIRED" for b in blockers)

    if pricing_blocked:
        return IntakeV3QuoteAcceptReadiness(
            accept_readiness_status="blocked_pricing_review_required",
            can_accept_now=False,
            accept_action_enabled=False,
            is_accept_ready_preview=False,
            accept_blockers=blockers,
            accept_guard_contract=build_iv3_accept_guard_contract(),
        )

    if blockers:
        return IntakeV3QuoteAcceptReadiness(
            accept_readiness_status="blocked",
            can_accept_now=False,
            accept_action_enabled=False,
            is_accept_ready_preview=False,
            accept_blockers=blockers,
            accept_guard_contract=build_iv3_accept_guard_contract(),
        )

    return IntakeV3QuoteAcceptReadiness(
        accept_readiness_status="ready_for_guarded_accept",
        can_accept_now=True,
        accept_action_enabled=True,
        is_accept_ready_preview=True,
        accept_blockers=[],
        accept_warnings=[
            _warning(
                "GUARDED_ACCEPT_REQUIRED",
                "Use the Intake V3 guarded accept flow — generic quote accept remains blocked.",
            )
        ],
        accept_guard_contract=build_iv3_accept_guard_contract(),
    )


def evaluate_iv3_quote_convert_readiness(
    quote: Quotes,
    linkage: dict[str, Any] | None,
    *,
    accept_blockers: list[IntakeV3QuoteReadinessBlocker],
    order_exists: bool = False,
) -> IntakeV3QuoteConvertReadiness:
    if linkage and (is_iv3_convert_completed(linkage) or order_exists):
        return IntakeV3QuoteConvertReadiness(
            convert_readiness_status="converted_to_order",
            can_convert_now=False,
            convert_action_enabled=False,
            is_convert_ready_preview=False,
            convert_blockers=[],
            convert_guard_contract=build_iv3_convert_guard_contract(),
        )

    blockers = build_iv3_quote_convert_blockers(
        quote,
        linkage,
        accept_blockers=accept_blockers,
        order_exists=order_exists,
    )

    if any(b.code == "PRICING_REVIEW_REQUIRED" for b in blockers):
        return IntakeV3QuoteConvertReadiness(
            convert_readiness_status="blocked_pricing_review_required",
            can_convert_now=False,
            convert_action_enabled=False,
            is_convert_ready_preview=False,
            convert_blockers=blockers,
            convert_guard_contract=build_iv3_convert_guard_contract(),
        )

    if quote.status not in ("accepted",):
        return IntakeV3QuoteConvertReadiness(
            convert_readiness_status="blocked_acceptance_required",
            can_convert_now=False,
            convert_action_enabled=False,
            is_convert_ready_preview=False,
            convert_blockers=blockers,
            convert_guard_contract=build_iv3_convert_guard_contract(),
        )

    real_blockers = [b for b in blockers if b.code not in {"ORDER_ALREADY_EXISTS"}]
    if not real_blockers:
        return IntakeV3QuoteConvertReadiness(
            convert_readiness_status="ready_for_guarded_convert",
            can_convert_now=True,
            convert_action_enabled=True,
            is_convert_ready_preview=True,
            convert_blockers=[],
            convert_warnings=[
                _warning(
                    "GUARDED_CONVERT_REQUIRED",
                    "Use the Intake V3 guarded convert flow — generic quote convert remains blocked.",
                )
            ],
            convert_guard_contract=build_iv3_convert_guard_contract(),
        )

    return IntakeV3QuoteConvertReadiness(
        convert_readiness_status="blocked",
        can_convert_now=False,
        convert_action_enabled=False,
        is_convert_ready_preview=False,
        convert_blockers=blockers,
        convert_guard_contract=build_iv3_convert_guard_contract(),
    )


def build_iv3_accept_convert_next_steps(
    quote: Quotes,
    accept: IntakeV3QuoteAcceptReadiness,
    convert: IntakeV3QuoteConvertReadiness,
) -> list[IntakeV3QuoteAcceptConvertNextStep]:
    steps: list[IntakeV3QuoteAcceptConvertNextStep] = []

    if convert.convert_readiness_status == "converted_to_order":
        steps.append(
            IntakeV3QuoteAcceptConvertNextStep(
                code="PRODUCTION_HANDOFF_AUDIT",
                title="Production handoff readiness audit",
                description=(
                    "Order created from IV3 accepted quote. Review production readiness audit — "
                    "task generation and inventory remain separate guarded flows."
                ),
            )
        )
    elif accept.accept_readiness_status == "accepted":
        steps.append(
            IntakeV3QuoteAcceptConvertNextStep(
                code="GUARDED_CONVERT_TO_ORDER",
                title="Guarded convert to order",
                description=(
                    "Quote is accepted. Use the guarded convert panel to create an Order only — "
                    "no execution or inventory side effects."
                ),
            )
        )
    elif accept.accept_readiness_status == "ready_for_guarded_accept":
        steps.append(
            IntakeV3QuoteAcceptConvertNextStep(
                code="GUARDED_ACCEPT",
                title="Complete guarded accept",
                description=(
                    "Use the Intake V3 guarded accept panel to accept the priced draft quote. "
                    "This does not create an order."
                ),
            )
        )
    elif any(b.code == "PRICING_REVIEW_REQUIRED" for b in accept.accept_blockers):
        steps.append(
            IntakeV3QuoteAcceptConvertNextStep(
                code="COMPLETE_PRICING_REVIEW",
                title="Complete pricing review",
                description="Finish manual pricing review before accept/convert readiness can advance.",
            )
        )

    steps.append(
        IntakeV3QuoteAcceptConvertNextStep(
            code="NEXT_BUILD_PRODUCTION_HANDOFF",
            title="Production handoff remains a separate build",
            description=(
                "Task generation, inventory checks, and production start require future guarded builds."
            ),
        )
    )
    return steps


async def _side_effect_flags(
    db: AsyncSession,
    quote_id: int,
) -> tuple[bool, bool]:
    orders_service = OrdersService(db)
    existing = await orders_service.get_list(
        skip=0,
        limit=10,
        query_dict={"quote_id": quote_id},
        sort="id",
    )
    order_items = existing.get("items", [])
    order_exists = len(order_items) > 0
    execution_plan_exists = False
    if order_items:
        order_ids = [item.id for item in order_items if item.id is not None]
        if order_ids:
            plan_count = await db.scalar(
                select(func.count())
                .select_from(ExecutionPlan)
                .where(ExecutionPlan.order_id.in_(order_ids))
            )
            execution_plan_exists = bool(plan_count and plan_count > 0)
    return order_exists, execution_plan_exists


def build_iv3_priced_draft_accept_convert_readiness_from_quote(
    quote: Quotes,
    *,
    order_exists: bool = False,
    order: Orders | None = None,
    execution_plan_exists: bool = False,
) -> IntakeV3PricedDraftAcceptConvertReadiness:
    linkage, note_warnings = parse_intake_v3_quote_notes(quote.notes)
    warning_codes = [w.code for w in note_warnings]

    if not quote_is_intake_v3_draft(quote, linkage) and not (
        quote.intake_code and str(quote.intake_code).startswith(INTAKE_V3_LINKAGE_CODE_PREFIX)
    ):
        return IntakeV3PricedDraftAcceptConvertReadiness(
            review_status="not_applicable",
            is_intake_v3_quote=False,
            quote_id=quote.id,
            quote_code=quote.code,
            quote_status=quote.status,
            message="Quote is not an Intake V3 draft quote.",
            accept=IntakeV3QuoteAcceptReadiness(
                accept_readiness_status="not_applicable",
                accept_guard_contract=build_iv3_accept_guard_contract(),
            ),
            convert=IntakeV3QuoteConvertReadiness(
                convert_readiness_status="not_applicable",
                convert_guard_contract=build_iv3_convert_guard_contract(),
            ),
        )

    pricing_completed = is_pricing_review_completed(linkage) if linkage else False
    priced_draft = bool(linkage.get("priced_draft") if linkage else False) or pricing_completed
    requires_pricing = bool(linkage.get("requires_pricing_review", True) if linkage else True) and not pricing_completed
    final_price = _final_price_present(quote, linkage)
    workspace_id = str(linkage.get("source_workspace_id") or "") if linkage else None

    accept = evaluate_iv3_quote_accept_readiness(
        quote,
        linkage,
        notes_warnings=warning_codes,
        order_exists=order_exists,
        execution_plan_exists=execution_plan_exists,
    )
    convert = evaluate_iv3_quote_convert_readiness(
        quote,
        linkage,
        accept_blockers=accept.accept_blockers,
        order_exists=order_exists,
    )
    next_steps = build_iv3_accept_convert_next_steps(quote, accept, convert)

    production_status: str | None = None
    production_blockers: list[str] = []
    ready_for_handoff_preview = False
    order_id: int | None = order.id if order else None
    if order is not None:
        order_linkage = load_iv3_order_linkage(order)
        production = build_iv3_order_production_readiness_response(
            order,
            quote,
            linkage,
            order_linkage,
            quote_note_warnings=warning_codes,
        )
        production_status = production.production_readiness_status
        production_blockers = production.production_readiness_blockers
        ready_for_handoff_preview = production.ready_for_handoff_preview
        order_id = order.id

    return IntakeV3PricedDraftAcceptConvertReadiness(
        review_status="quote_found",
        is_intake_v3_quote=True,
        quote_id=quote.id,
        quote_code=quote.code,
        quote_status=quote.status,
        intake_code=quote.intake_code,
        source_workspace_id=workspace_id or None,
        pricing_review_completed=pricing_completed,
        priced_draft=priced_draft,
        requires_pricing_review=requires_pricing,
        final_price_present=final_price,
        order_exists=order_exists,
        order_id=order_id,
        execution_plan_exists=execution_plan_exists,
        inventory_mutated=False,
        production_readiness_status=production_status,
        production_readiness_blockers=production_blockers,
        ready_for_handoff_preview=ready_for_handoff_preview,
        can_generate_execution_plan_now=False,
        can_generate_execution_tasks_now=False,
        can_mutate_inventory_now=False,
        can_start_production_now=False,
        accept=accept,
        convert=convert,
        next_steps=next_steps,
        warnings=warning_codes,
        no_order_created=not order_exists,
        no_execution_created=not execution_plan_exists,
        no_inventory_mutated=True,
    )


async def get_iv3_priced_draft_accept_convert_readiness(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3PricedDraftAcceptConvertReadiness:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        return IntakeV3PricedDraftAcceptConvertReadiness(
            review_status="quote_missing",
            is_intake_v3_quote=False,
            quote_id=quote_id,
            message=f"Quote id={quote_id} was not found.",
            accept=IntakeV3QuoteAcceptReadiness(
                accept_readiness_status="quote_missing",
                accept_guard_contract=build_iv3_accept_guard_contract(),
            ),
            convert=IntakeV3QuoteConvertReadiness(
                convert_readiness_status="quote_missing",
                convert_guard_contract=build_iv3_convert_guard_contract(),
            ),
        )

    order_exists, execution_plan_exists = await _side_effect_flags(db, quote.id)
    order = await check_existing_order_for_iv3_quote(db, quote.id)
    return build_iv3_priced_draft_accept_convert_readiness_from_quote(
        quote,
        order_exists=order_exists,
        order=order,
        execution_plan_exists=execution_plan_exists,
    )


async def get_iv3_priced_draft_accept_convert_readiness_by_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3PricedDraftAcceptConvertReadiness:
    quote = await check_existing_quote_for_intake_v3_workspace(db, workspace_id)
    if quote is None:
        return IntakeV3PricedDraftAcceptConvertReadiness(
            review_status="not_created",
            is_intake_v3_quote=False,
            source_workspace_id=workspace_id,
            requires_pricing_review=True,
            message="No Intake V3 draft quote has been created for this workspace yet.",
            accept=IntakeV3QuoteAcceptReadiness(
                accept_readiness_status="not_created",
                accept_blockers=[_blocker("DRAFT_QUOTE_NOT_CREATED", "Create guarded draft quote first.")],
                accept_guard_contract=build_iv3_accept_guard_contract(),
            ),
            convert=IntakeV3QuoteConvertReadiness(
                convert_readiness_status="not_created",
                convert_blockers=[_blocker("DRAFT_QUOTE_NOT_CREATED", "Create guarded draft quote first.")],
                convert_guard_contract=build_iv3_convert_guard_contract(),
            ),
            next_steps=[
                IntakeV3QuoteAcceptConvertNextStep(
                    code="CREATE_DRAFT_QUOTE",
                    title="Create guarded draft quote",
                    description="Accept/convert readiness requires an IV3 draft quote linked to this workspace.",
                )
            ],
        )

    state = await get_iv3_priced_draft_accept_convert_readiness(db, quote.id)
    if state.source_workspace_id and state.source_workspace_id != workspace_id:
        state.warnings.append("WORKSPACE_ID_MISMATCH")
    return state
