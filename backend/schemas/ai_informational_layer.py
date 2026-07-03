"""WorkOS AI Informational Layer — cross-cutting suggestion contract (read-only foundation).

AI informs, suggests, explains, and structures unclear data.
AI does NOT decide pricing, production, tasks, or business state without confirmation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

AI_INFORMATIONAL_SUGGESTION_SCHEMA_VERSION = "ai_informational_suggestion_v1"

AI_INFORMATIONAL_SOURCE_CONTEXT = Literal[
    "intake_v4_svg_review",
    "website_chatbot",
    "website_order_form",
    "work_intake_internal",
    "product_template_assist",
]

AI_SUGGESTION_CATEGORY = Literal[
    "semantic_classification",
    "missing_information",
    "template_recommendation",
    "client_intake_summary",
    "production_risk_hint",
    "material_intent_hint",
    "file_quality_hint",
    "question_suggestion",
    "operator_explanation",
]

AI_INFORMATIONAL_SOURCE_CONTEXTS: tuple[str, ...] = (
    "intake_v4_svg_review",
    "website_chatbot",
    "website_order_form",
    "work_intake_internal",
    "product_template_assist",
)

AI_SUGGESTION_CATEGORIES: tuple[str, ...] = (
    "semantic_classification",
    "missing_information",
    "template_recommendation",
    "client_intake_summary",
    "production_risk_hint",
    "material_intent_hint",
    "file_quality_hint",
    "question_suggestion",
    "operator_explanation",
)


class AiInformationalBoundaryFlags(BaseModel):
    is_ai_suggestion: bool = True
    informational_only: bool = True
    requires_operator_confirmation: bool = True
    used_for_pricing: bool = False
    used_for_production: bool = False
    used_for_task_generation: bool = False
    can_create_order: bool = False
    can_create_execution_tasks: bool = False


class AiInformationalSuggestionItem(BaseModel):
    suggestion_id: str
    category: AI_SUGGESTION_CATEGORY
    title: str | None = None
    summary: str | None = None
    confidence: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = True
    boundary_flags: AiInformationalBoundaryFlags = Field(default_factory=AiInformationalBoundaryFlags)


class AiInformationalSuggestionEnvelope(BaseModel):
    schema_version: str = AI_INFORMATIONAL_SUGGESTION_SCHEMA_VERSION
    source_context: AI_INFORMATIONAL_SOURCE_CONTEXT
    suggestions: list[AiInformationalSuggestionItem] = Field(default_factory=list)
    confidence: float = 0.0
    requires_confirmation: bool = True
    confirmed_by_user_id: int | None = None
    confirmed_at: datetime | None = None
    used_for_pricing: bool = False
    used_for_production: bool = False
    used_for_task_generation: bool = False
    writes_business_state: bool = False
    warnings: list[str] = Field(default_factory=list)


class AiInformationalConfirmationContract(BaseModel):
    schema_version: str = "ai_informational_confirmation_v1"
    status: Literal["not_persisted", "draft"] = "not_persisted"
    note: str | None = None
    applies_to_contexts: list[AI_INFORMATIONAL_SOURCE_CONTEXT] = Field(default_factory=list)
    fields_available_for_future_build: list[str] = Field(default_factory=list)


class AiInformationalAssistPreviewResponse(BaseModel):
    """Generic read-only AI assist preview shell — context-specific candidate payload in `candidate_payload`."""

    preview_only: bool = True
    ai_not_called: bool = True
    context: AI_INFORMATIONAL_SOURCE_CONTEXT
    candidate_payload: dict[str, Any] = Field(default_factory=dict)
    mock_suggestions: list[AiInformationalSuggestionItem] = Field(default_factory=list)
    informational_envelope: AiInformationalSuggestionEnvelope
    boundary_flags: AiInformationalBoundaryFlags = Field(default_factory=AiInformationalBoundaryFlags)
    operator_confirmation_contract: AiInformationalConfirmationContract = Field(
        default_factory=AiInformationalConfirmationContract
    )
