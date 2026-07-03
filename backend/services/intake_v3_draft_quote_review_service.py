"""Intake V3 draft quote review — read-only audit of guarded Quote drafts linked to workspaces."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models.quotes import Quotes
from schemas.intake_v3 import (
    IntakeV3DraftQuoteConversionGuard,
    IntakeV3DraftQuoteReview,
    IntakeV3DraftQuoteReviewWarning,
    IntakeV3DraftQuoteSnapshotSummary,
)
from services.intake_v3_quote_pricing_handoff_service import build_intake_v3_quote_pricing_handoff
from services.intake_v3_quote_linkage_utils import is_pricing_review_completed
from services.intake_v3_real_commercial_quote_creation_service import (
    INTAKE_V3_LINKAGE_CODE_PREFIX,
    INTAKE_V3_LINKAGE_JSON_KEY,
    INTAKE_V3_SOURCE_MODULE,
    check_existing_quote_for_intake_v3_workspace,
    intake_v3_linkage_code,
    parse_intake_v3_linkage_from_notes,
)
from services.quotes import QuotesService

NOT_CREATED_MESSAGE = "No Intake V3 draft quote has been created for this workspace yet."


def parse_intake_v3_quote_notes(notes: str | None) -> tuple[dict[str, Any] | None, list[IntakeV3DraftQuoteReviewWarning]]:
    """Safe parse of quote notes JSON for intake_v3_linkage_v1."""
    warnings: list[IntakeV3DraftQuoteReviewWarning] = []
    if not notes:
        warnings.append(
            IntakeV3DraftQuoteReviewWarning(code="NOTES_EMPTY", message="Quote notes are empty.")
        )
        return None, warnings
    try:
        payload = json.loads(notes)
    except json.JSONDecodeError as exc:
        warnings.append(
            IntakeV3DraftQuoteReviewWarning(
                code="NOTES_JSON_INVALID",
                message=f"Quote notes are not valid JSON: {exc.msg}",
            )
        )
        return None, warnings
    if not isinstance(payload, dict):
        warnings.append(
            IntakeV3DraftQuoteReviewWarning(
                code="NOTES_JSON_INVALID",
                message="Quote notes JSON root must be an object.",
            )
        )
        return None, warnings
    linkage = payload.get(INTAKE_V3_LINKAGE_JSON_KEY)
    if not isinstance(linkage, dict):
        warnings.append(
            IntakeV3DraftQuoteReviewWarning(
                code="LINKAGE_MISSING",
                message=f"Missing or invalid {INTAKE_V3_LINKAGE_JSON_KEY} in quote notes.",
            )
        )
        return None, warnings
    return linkage, warnings


def quote_is_intake_v3_draft(quote: Quotes, linkage: dict[str, Any] | None) -> bool:
    if not quote.intake_code or not str(quote.intake_code).startswith(INTAKE_V3_LINKAGE_CODE_PREFIX):
        return False
    if linkage is None:
        return False
    if quote.status != "draft":
        return False
    return True


def build_intake_v3_quote_snapshot_summary(
    quote: Quotes,
    linkage: dict[str, Any] | None,
) -> IntakeV3DraftQuoteSnapshotSummary:
    if linkage is None:
        return IntakeV3DraftQuoteSnapshotSummary(
            snapshot_present=False,
            owner_decision_present=False,
            confirmed_model_present=False,
            finish_variation_present=False,
            raw_analysis_not_production_truth=True,
            holes_not_letters=True,
            section_keys=[],
            integrity_markers={},
        )

    snapshot = linkage.get("snapshot") if isinstance(linkage.get("snapshot"), dict) else {}
    sections = snapshot.get("sections") if isinstance(snapshot.get("sections"), dict) else {}
    integrity = linkage.get("integrity_markers") if isinstance(linkage.get("integrity_markers"), dict) else {}
    raw_ref = sections.get("raw_svg_analysis_reference") if isinstance(sections, dict) else None
    raw_not_truth = True
    if isinstance(raw_ref, dict):
        raw_not_truth = bool(raw_ref.get("not_production_truth", True))

    return IntakeV3DraftQuoteSnapshotSummary(
        snapshot_present=bool(snapshot),
        owner_decision_present=isinstance(linkage.get("owner_decision"), dict),
        confirmed_model_present=sections.get("confirmed_production_model_snapshot") is not None,
        finish_variation_present=sections.get("finish_variation_summary_snapshot") is not None,
        finish_assignment_present=sections.get("finish_assignment_snapshot") is not None,
        pricing_input_preview_present=sections.get("pricing_input_candidate_snapshot") is not None,
        raw_analysis_not_production_truth=bool(
            snapshot.get("raw_analysis_not_production_truth", raw_not_truth)
        ),
        holes_not_letters=bool(snapshot.get("holes_not_letters", integrity.get("holes_not_letters", True))),
        section_keys=sorted(str(key) for key in sections.keys()),
        integrity_markers=integrity,
        owner_decision_summary=linkage.get("owner_decision") if isinstance(linkage.get("owner_decision"), dict) else {},
    )


def build_intake_v3_quote_conversion_guard_summary(
    quote: Quotes | None,
    linkage: dict[str, Any] | None,
    *,
    is_intake_v3_quote: bool,
) -> IntakeV3DraftQuoteConversionGuard:
    if not is_intake_v3_quote or quote is None or linkage is None:
        return IntakeV3DraftQuoteConversionGuard(
            can_accept_quote=True,
            can_convert_to_order=True,
            conversion_blockers=[],
            blocked_actions=[],
        )

    requires_pricing_review = bool(linkage.get("requires_pricing_review", True))
    pricing_review_completed = is_pricing_review_completed(linkage)
    blockers: list[str] = ["INTAKE_V3_ACCEPT_CONVERT_SEPARATE_FLOW"]
    if quote.status == "draft":
        blockers.append("QUOTE_STATUS_DRAFT")
    if requires_pricing_review and not pricing_review_completed:
        blockers.append("REQUIRES_PRICING_REVIEW")
    if float(quote.grand_total or 0) <= 0 and not pricing_review_completed:
        blockers.append("FINAL_PRICE_MISSING")

    blocked_actions = [
        "Accept quote",
        "Convert to order",
        "Start production",
    ]

    return IntakeV3DraftQuoteConversionGuard(
        can_accept_quote=False,
        can_convert_to_order=False,
        conversion_blockers=blockers,
        blocked_actions=blocked_actions,
    )


def build_intake_v3_quote_pricing_review_summary(
    quote: Quotes | None,
    linkage: dict[str, Any] | None,
    warnings: list[IntakeV3DraftQuoteReviewWarning],
) -> dict[str, Any]:
    handoff = build_intake_v3_quote_pricing_handoff(quote, linkage=linkage, notes_warnings=[w.code for w in warnings])
    return {
        "pricing_status": handoff.pricing_handoff_status,
        "requires_pricing_review": handoff.requires_pricing_review,
        "pricing_review_items": handoff.pricing_review_items,
        "pricing_handoff": handoff,
    }


def _build_review_from_quote(quote: Quotes) -> IntakeV3DraftQuoteReview:
    linkage, warnings = parse_intake_v3_quote_notes(quote.notes)
    is_iv3 = quote_is_intake_v3_draft(quote, linkage)

    if not is_iv3:
        return IntakeV3DraftQuoteReview(
            review_status="not_applicable",
            is_intake_v3_quote=False,
            quote_id=quote.id,
            quote_code=quote.code,
            quote_status=quote.status,
            message="Quote is not an Intake V3 guarded draft.",
            can_accept_quote=True,
            can_convert_to_order=True,
            conversion_guard=IntakeV3DraftQuoteConversionGuard(
                can_accept_quote=True,
                can_convert_to_order=True,
            ),
            warnings=warnings,
        )

    requires_pricing_review = bool(linkage.get("requires_pricing_review", True)) if linkage else True
    pricing_review_completed = is_pricing_review_completed(linkage) if linkage else False
    priced_draft = bool(linkage.get("priced_draft") or pricing_review_completed) if linkage else False
    snapshot_summary = build_intake_v3_quote_snapshot_summary(quote, linkage)
    conversion_guard = build_intake_v3_quote_conversion_guard_summary(
        quote, linkage, is_intake_v3_quote=True
    )
    pricing_bundle = build_intake_v3_quote_pricing_review_summary(quote, linkage, warnings)

    return IntakeV3DraftQuoteReview(
        review_status="quote_found",
        is_intake_v3_quote=True,
        quote_id=quote.id,
        quote_code=quote.code,
        quote_status=quote.status,
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_workspace_id=str(linkage.get("source_workspace_id") or "") if linkage else None,
        source_workspace_code=str(linkage.get("source_workspace_code") or "") if linkage else None,
        intake_code=quote.intake_code,
        requires_pricing_review=requires_pricing_review,
        pricing_status=str(pricing_bundle["pricing_status"]),
        snapshot_present=snapshot_summary.snapshot_present,
        owner_decision_present=snapshot_summary.owner_decision_present,
        confirmed_model_present=snapshot_summary.confirmed_model_present,
        finish_variation_present=snapshot_summary.finish_variation_present,
        can_accept_quote=conversion_guard.can_accept_quote,
        can_convert_to_order=conversion_guard.can_convert_to_order,
        conversion_blockers=conversion_guard.conversion_blockers,
        pricing_review_items=list(pricing_bundle["pricing_review_items"]),
        snapshot_summary=snapshot_summary,
        pricing_handoff=pricing_bundle["pricing_handoff"],
        conversion_guard=conversion_guard,
        warnings=warnings,
        totals_zero=float(quote.grand_total or 0) <= 0,
        cost_engine_called=bool(linkage.get("cost_engine_called", False)) if linkage else False,
        pricing_review_completed=pricing_review_completed,
        priced_draft=priced_draft,
    )


def build_not_created_review(workspace_id: str) -> IntakeV3DraftQuoteReview:
    return IntakeV3DraftQuoteReview(
        review_status="not_created",
        is_intake_v3_quote=False,
        source_workspace_id=workspace_id,
        intake_code=intake_v3_linkage_code(workspace_id),
        requires_pricing_review=True,
        pricing_status="requires_review",
        can_accept_quote=False,
        can_convert_to_order=False,
        conversion_blockers=["DRAFT_QUOTE_NOT_CREATED"],
        pricing_review_items=["Draft quote not created yet"],
        message=NOT_CREATED_MESSAGE,
        conversion_guard=IntakeV3DraftQuoteConversionGuard(
            can_accept_quote=False,
            can_convert_to_order=False,
            conversion_blockers=["DRAFT_QUOTE_NOT_CREATED"],
            blocked_actions=["Accept quote", "Convert to order", "Start production"],
        ),
        pricing_handoff=build_intake_v3_quote_pricing_handoff(None),
    )


async def get_intake_v3_draft_quote_review(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3DraftQuoteReview:
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if quote is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "quote_not_found", "quote_id": quote_id},
        )
    return _build_review_from_quote(quote)


async def get_intake_v3_draft_quote_review_by_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3DraftQuoteReview:
    quote = await check_existing_quote_for_intake_v3_workspace(db, workspace_id)
    if quote is None:
        return build_not_created_review(workspace_id)
    review = _build_review_from_quote(quote)
    if review.source_workspace_id and review.source_workspace_id != workspace_id:
        review.warnings.append(
            IntakeV3DraftQuoteReviewWarning(
                code="WORKSPACE_ID_MISMATCH",
                message="Linked quote workspace id does not match requested workspace.",
            )
        )
    return review
