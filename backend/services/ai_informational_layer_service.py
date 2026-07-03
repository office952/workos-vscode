"""WorkOS AI Informational Layer — shared factories and adapters (no external AI calls)."""

from __future__ import annotations

from schemas.ai_informational_layer import (
    AI_INFORMATIONAL_SUGGESTION_SCHEMA_VERSION,
    AI_INFORMATIONAL_SOURCE_CONTEXTS,
    AI_SUGGESTION_CATEGORIES,
    AiInformationalBoundaryFlags,
    AiInformationalConfirmationContract,
    AiInformationalSuggestionEnvelope,
    AiInformationalSuggestionItem,
)
from schemas.intake_v4 import (
    IntakeV4AiSemanticClassificationCandidatePayload,
    IntakeV4AiSemanticClassificationSuggestionResponse,
)


def ai_informational_boundary_flags() -> AiInformationalBoundaryFlags:
    return AiInformationalBoundaryFlags(
        is_ai_suggestion=True,
        informational_only=True,
        requires_operator_confirmation=True,
        used_for_pricing=False,
        used_for_production=False,
        used_for_task_generation=False,
        can_create_order=False,
        can_create_execution_tasks=False,
    )


def ai_informational_confirmation_contract() -> AiInformationalConfirmationContract:
    return AiInformationalConfirmationContract(
        schema_version="ai_informational_confirmation_v1",
        status="not_persisted",
        note=(
            "AI informational suggestions are not persisted or applied to business state in this build. "
            "Only operator/client confirmed values may be written in future builds."
        ),
        applies_to_contexts=list(AI_INFORMATIONAL_SOURCE_CONTEXTS),
        fields_available_for_future_build=[
            "suggestion_id",
            "source_context",
            "category",
            "accepted_suggestion",
            "confirmed_value",
            "operator_notes",
            "client_notes",
            "ai_confidence_at_confirmation",
            "confirmed_at",
            "confirmed_by_user_id",
            "confirmation_source",
        ],
    )


def _aggregate_confidence(items: list[AiInformationalSuggestionItem]) -> float:
    if not items:
        return 0.0
    return round(sum(item.confidence for item in items) / len(items), 4)


def build_informational_envelope(
    *,
    source_context: str,
    suggestions: list[AiInformationalSuggestionItem],
    warnings: list[str] | None = None,
) -> AiInformationalSuggestionEnvelope:
    return AiInformationalSuggestionEnvelope(
        schema_version=AI_INFORMATIONAL_SUGGESTION_SCHEMA_VERSION,
        source_context=source_context,  # type: ignore[arg-type]
        suggestions=suggestions,
        confidence=_aggregate_confidence(suggestions),
        requires_confirmation=True,
        confirmed_by_user_id=None,
        confirmed_at=None,
        used_for_pricing=False,
        used_for_production=False,
        used_for_task_generation=False,
        writes_business_state=False,
        warnings=warnings or [],
    )


def semantic_classification_to_informational_suggestions(
    semantic: IntakeV4AiSemanticClassificationSuggestionResponse,
    *,
    candidate: IntakeV4AiSemanticClassificationCandidatePayload,
) -> list[AiInformationalSuggestionItem]:
    """Adapt Intake V4 SVG semantic mock into cross-cutting informational suggestion items."""
    flags = ai_informational_boundary_flags()
    items: list[AiInformationalSuggestionItem] = []

    layer_by_group = {group.group_id: group.source_layer for group in candidate.groups}

    for suggestion in semantic.suggestions:
        layer_name = layer_by_group.get(suggestion.group_id, suggestion.group_id)
        items.append(
            AiInformationalSuggestionItem(
                suggestion_id=f"semantic_{suggestion.group_id}",
                category="semantic_classification",
                title=f"Semantic classification — {layer_name}",
                summary=f"Suggested kind: {suggestion.suggested_kind}",
                confidence=suggestion.confidence,
                reasons=suggestion.reasons,
                payload={
                    "group_id": suggestion.group_id,
                    "source_layer": layer_name,
                    "suggested_kind": suggestion.suggested_kind,
                    "suggested_text": suggestion.suggested_text,
                    "suggested_label": suggestion.suggested_label,
                },
                requires_confirmation=True,
                boundary_flags=flags,
            )
        )

    for index, warning in enumerate(semantic.warnings):
        items.append(
            AiInformationalSuggestionItem(
                suggestion_id=f"file_quality_hint_{index}",
                category="file_quality_hint",
                title="File quality hint",
                summary=warning,
                confidence=0.0,
                reasons=[warning],
                payload={"hint_type": "svg_text_curves_or_mock"},
                requires_confirmation=False,
                boundary_flags=flags,
            )
        )

    return items


def placeholder_future_context_examples() -> dict[str, list[dict[str, str]]]:
    """Documentation-only examples for website chatbot / order form — not invoked at runtime."""
    return {
        "website_chatbot": [
            {
                "category": "missing_information",
                "summary": "Client has not provided approximate dimensions.",
            },
            {
                "category": "template_recommendation",
                "summary": "Possible template: TPL-VOLUMETRIC-LETTERS (needs operator confirmation).",
            },
        ],
        "website_order_form": [
            {
                "category": "client_intake_summary",
                "summary": "Illuminated exterior volumetric letters — draft only.",
            },
            {
                "category": "question_suggestion",
                "summary": "Do you have a vector logo file?",
            },
        ],
    }


def supported_categories() -> tuple[str, ...]:
    return AI_SUGGESTION_CATEGORIES
