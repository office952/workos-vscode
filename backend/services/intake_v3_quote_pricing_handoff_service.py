"""Intake V3 quote pricing handoff summary — read-only checklist from quote notes snapshot."""

from __future__ import annotations

from typing import Any

from models.quotes import Quotes
from schemas.intake_v3 import IntakeV3DraftQuotePricingHandoff
from services.intake_v3_quote_linkage_utils import is_pricing_review_completed
from services.intake_v3_real_commercial_quote_creation_service import parse_intake_v3_linkage_from_notes

PRICING_HANDOFF_CHECKLIST_KEYS = (
    "source_workspace_identified",
    "owner_decision_attached",
    "confirmed_model_attached",
    "finish_assignments_attached",
    "finish_variations_attached",
    "pricing_input_preview_attached",
    "final_commercial_price_missing",
    "cost_engine_not_called",
    "requires_pricing_review",
    "ready_for_manual_pricing_review",
)


def _safe_parse_notes(notes: str | None) -> tuple[dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    if not notes:
        return None, warnings
    linkage = parse_intake_v3_linkage_from_notes(notes)
    if linkage is None:
        warnings.append("NOTES_JSON_INVALID_OR_MISSING_LINKAGE")
    return linkage, warnings


def build_intake_v3_quote_pricing_handoff(
    quote: Quotes | None,
    *,
    linkage: dict[str, Any] | None = None,
    notes_warnings: list[str] | None = None,
) -> IntakeV3DraftQuotePricingHandoff:
    """Build pricing handoff checklist without CostEngine or final price calculation."""
    warnings = list(notes_warnings or [])
    if quote is None:
        return IntakeV3DraftQuotePricingHandoff(
            pricing_handoff_status="not_created",
            requires_pricing_review=True,
            cost_engine_called=False,
            final_price_present=False,
            pricing_review_items=[],
            missing_pricing_inputs=["intake_v3_draft_quote"],
            safe_next_actions=["Create guarded draft quote from Intake V3 workspace"],
            blocked_actions=[
                "Accept quote",
                "Convert to order",
                "Start production",
            ],
            checklist={key: False for key in PRICING_HANDOFF_CHECKLIST_KEYS},
            warnings=warnings,
        )

    if linkage is None:
        parsed_linkage, parse_warnings = _safe_parse_notes(quote.notes)
        linkage = parsed_linkage
        warnings.extend(parse_warnings)
    if linkage is None:
        linkage = {}

    snapshot = linkage.get("snapshot") if isinstance(linkage, dict) else None
    sections: dict[str, Any] = {}
    if isinstance(snapshot, dict):
        sections = snapshot.get("sections") if isinstance(snapshot.get("sections"), dict) else {}

    requires_pricing_review = bool(linkage.get("requires_pricing_review", True))
    pricing_review_completed = is_pricing_review_completed(linkage)
    cost_engine_called = bool(linkage.get("cost_engine_called", False))
    grand_total = float(quote.grand_total or 0)
    final_price_present = grand_total > 0 and (pricing_review_completed or not requires_pricing_review)

    checklist = {
        "source_workspace_identified": bool(linkage.get("source_workspace_id")),
        "owner_decision_attached": isinstance(linkage.get("owner_decision"), dict),
        "confirmed_model_attached": sections.get("confirmed_production_model_snapshot") is not None,
        "finish_assignments_attached": sections.get("finish_assignment_snapshot") is not None,
        "finish_variations_attached": sections.get("finish_variation_summary_snapshot") is not None,
        "pricing_input_preview_attached": sections.get("pricing_input_candidate_snapshot") is not None,
        "final_commercial_price_missing": not final_price_present,
        "cost_engine_not_called": not cost_engine_called,
        "requires_pricing_review": requires_pricing_review and not pricing_review_completed,
        "ready_for_manual_pricing_review": requires_pricing_review and not final_price_present,
    }

    pricing_review_items = [
        label
        for key, label in (
            ("source_workspace_identified", "Source workspace identified"),
            ("owner_decision_attached", "Owner decision attached"),
            ("confirmed_model_attached", "Confirmed model attached"),
            ("finish_assignments_attached", "Finish assignments attached"),
            ("finish_variations_attached", "Finish variations attached"),
            ("pricing_input_preview_attached", "Pricing input preview attached"),
            ("final_commercial_price_missing", "Final commercial price missing"),
            ("cost_engine_not_called", "CostEngine not called"),
            ("requires_pricing_review", "Requires pricing review"),
            ("ready_for_manual_pricing_review", "Ready for manual pricing review"),
        )
        if checklist.get(key)
    ]

    missing_pricing_inputs: list[str] = []
    if not checklist["pricing_input_preview_attached"]:
        missing_pricing_inputs.append("pricing_input_candidate_snapshot")
    if checklist["final_commercial_price_missing"]:
        missing_pricing_inputs.append("final_commercial_price")

    pricing_handoff_status = (
        "completed"
        if pricing_review_completed
        else ("requires_review" if requires_pricing_review else "review_complete")
    )

    if pricing_review_completed and final_price_present:
        safe_next_actions = [
            "Quote is priced draft; accept/convert remains separate guarded flow.",
        ]
        blocked_actions = [
            "Accept quote",
            "Convert to order",
            "Start production",
        ]
    elif requires_pricing_review:
        safe_next_actions = [
            "Review pricing input candidate",
            "Complete manual pricing review in Intake V3",
        ]
        blocked_actions = [
            "Accept quote",
            "Convert to order",
            "Start production",
        ]
    else:
        safe_next_actions = [
            "Review pricing input candidate",
            "Run explicit pricing step in a dedicated build",
        ]
        blocked_actions = []

    return IntakeV3DraftQuotePricingHandoff(
        pricing_handoff_status=pricing_handoff_status,
        requires_pricing_review=requires_pricing_review and not pricing_review_completed,
        cost_engine_called=cost_engine_called,
        final_price_present=final_price_present,
        pricing_review_items=pricing_review_items,
        missing_pricing_inputs=missing_pricing_inputs,
        safe_next_actions=safe_next_actions,
        blocked_actions=blocked_actions,
        checklist=checklist,
        warnings=warnings,
    )
