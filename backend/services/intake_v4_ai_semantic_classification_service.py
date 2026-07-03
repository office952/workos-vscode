"""Intake V4 AI-assisted semantic classification — read-only contract + mock suggestions.

Geometry calculates. AI interprets (future). Operator confirms (future build).

No external AI calls. Suggestions never feed pricing, production, or task generation.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from schemas.intake_v4 import (
    IntakeV4AiInformationalAssistPreviewResponse,
    IntakeV4AiSemanticClassificationPreviewResponse,
    IntakeV4AiSemanticClassificationCandidatePayload,
    IntakeV4AiSemanticClassificationGroup,
    IntakeV4AiSemanticClassificationGroupGeometry,
    IntakeV4AiSemanticClassificationRenderPreview,
    IntakeV4AiSemanticClassificationSuggestion,
    IntakeV4AiSemanticClassificationSuggestionResponse,
    IntakeV4AiSemanticClassificationSystemClassification,
    IntakeV4WorkspacePayload,
)
from schemas.ai_informational_layer import AiInformationalBoundaryFlags
from services.ai_informational_layer_service import (
    ai_informational_boundary_flags,
    ai_informational_confirmation_contract,
    build_informational_envelope,
    semantic_classification_to_informational_suggestions,
)
from services.intake_v4_letter_part_classification_service import classify_letter_parts_from_analysis
from services.intake_v4_volumetric_return_metrics_service import build_layer_return_metric_audit

AI_SEMANTIC_CLASSIFICATION_SCHEMA_VERSION = "ai_semantic_classification_suggestion_v1"

SuggestedKind = Literal[
    "letters",
    "logo_or_emblem",
    "artwork",
    "shape_symbol",
    "mixed",
    "unknown",
]

_ROLE_TO_KIND: dict[str, SuggestedKind] = {
    "face": "letters",
    "printed_artwork": "logo_or_emblem",
    "logo": "logo_or_emblem",
    "policromie": "artwork",
    "inner_hole": "shape_symbol",
}

_KIND_CONFIDENCE: dict[str, float] = {
    "letters": 0.78,
    "logo_or_emblem": 0.72,
    "artwork": 0.70,
    "shape_symbol": 0.55,
    "mixed": 0.45,
    "unknown": 0.35,
}


def ai_semantic_boundary_flags() -> AiInformationalBoundaryFlags:
    return ai_informational_boundary_flags()


def _slug_group_id(layer_key: str, role: str) -> str:
    safe = re.sub(r"[^a-z0-9_]+", "_", layer_key.strip().lower()).strip("_") or "layer"
    role_token = re.sub(r"[^a-z0-9_]+", "_", role.strip().lower()).strip("_") or "unknown"
    return f"{safe}_{role_token}_group"


def _positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _positive_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _system_classification(role: str) -> IntakeV4AiSemanticClassificationSystemClassification:
    return IntakeV4AiSemanticClassificationSystemClassification(
        counts_as_letters=role == "face",
        counts_as_artwork=role in {"printed_artwork", "policromie", "artwork"},
        counts_as_logo=role == "logo",
    )


def _suggested_kind_for_role(role: str, *, real_letter_count: int, inner_hole_count: int) -> SuggestedKind:
    if role == "face" and inner_hole_count > 0 and real_letter_count > 1:
        return "letters"
    if role == "face" and real_letter_count > 1:
        return "letters"
    if role == "face" and real_letter_count == 1:
        return "logo_or_emblem"
    mapped = _ROLE_TO_KIND.get(role)
    if mapped:
        return mapped
    return "unknown"


def _suggestion_reasons(
    *,
    role: str,
    suggested_kind: SuggestedKind,
    real_letter_count: int,
    inner_hole_count: int,
) -> list[str]:
    reasons: list[str] = []
    if role:
        reasons.append(f"operator role is {role}")
    if suggested_kind == "letters":
        reasons.append("aligned glyph-like shapes")
        if real_letter_count > 1:
            reasons.append("multiple separated contours on face layer")
        if inner_hole_count > 0:
            reasons.append("inner holes present — not separate letter pieces")
    elif suggested_kind in {"logo_or_emblem", "artwork"}:
        reasons.append("single compact artwork group")
    elif suggested_kind == "shape_symbol":
        reasons.append("layer role indicates cut-out or symbol geometry")
    elif suggested_kind == "unknown":
        reasons.append("ambiguous layer role — operator confirmation required")
    reasons.append("heuristic mock only — no AI model invoked")
    return reasons


def build_ai_semantic_classification_candidate_payload(
    *,
    workspace_id: str,
    payload: IntakeV4WorkspacePayload,
) -> IntakeV4AiSemanticClassificationCandidatePayload:
    template_code = payload.product_binding.template_code
    layer_setup = payload.layer_role_setup.model_dump(mode="json") if payload.layer_role_setup else {}
    finish_setup = payload.finish_setup.model_dump(mode="json") if payload.finish_setup else {}
    analysis = payload.svg_analysis_json if isinstance(payload.svg_analysis_json, dict) else {}

    audit_rows = build_layer_return_metric_audit(
        svg_analysis_json=analysis,
        layer_role_setup=layer_setup,
        finish_setup=finish_setup,
    )
    classification = classify_letter_parts_from_analysis(analysis, layer_setup)

    groups: list[IntakeV4AiSemanticClassificationGroup] = []
    for row in audit_rows:
        layer_name = str(row.get("layer_name") or "")
        role = str(row.get("role") or "unknown")
        layer_key = layer_name
        for layer_entry in layer_setup.get("layers") or []:
            if not isinstance(layer_entry, dict):
                continue
            if str(layer_entry.get("layer_name") or "") == layer_name or str(layer_entry.get("layer_key") or "") == layer_name:
                layer_key = str(layer_entry.get("layer_key") or layer_name)
                break

        outer_ml = _positive(row.get("outer_perimeter_ml"))
        hole_ml = _positive(row.get("inner_hole_perimeter_ml"))
        cutting_ml = _positive(row.get("cutting_perimeter_ml"))
        if cutting_ml is None and outer_ml is not None:
            cutting_ml = round(outer_ml + (hole_ml or 0.0), 4)

        area_sqm = None
        for layer in analysis.get("layers") or []:
            if not isinstance(layer, dict):
                continue
            if str(layer.get("name") or layer.get("id") or "") in {layer_name, layer_key}:
                area_sqm = _positive(layer.get("filledAreaSqm")) or _positive(layer.get("boundingAreaSqm"))
                break

        groups.append(
            IntakeV4AiSemanticClassificationGroup(
                group_id=_slug_group_id(layer_key, role),
                source_layer=layer_name,
                operator_role=role,
                geometry=IntakeV4AiSemanticClassificationGroupGeometry(
                    outer_contours_count=_positive_int(row.get("real_letter_count")),
                    inner_holes_count=_positive_int(row.get("inner_hole_count")),
                    area_sqm=round(area_sqm, 6) if area_sqm else None,
                    outer_perimeter_ml=outer_ml,
                    inner_hole_perimeter_ml=hole_ml,
                    cutting_perimeter_ml=cutting_ml,
                    return_perimeter_ml=_positive(row.get("return_perimeter_ml")),
                    bbox_mm=None,
                ),
                current_system_classification=_system_classification(role),
            )
        )

    _ = classification  # reserved for future per-part semantic hints

    return IntakeV4AiSemanticClassificationCandidatePayload(
        workspace_id=workspace_id,
        template_id=template_code,
        source_file_type="svg",
        render_preview=IntakeV4AiSemanticClassificationRenderPreview(
            available=False,
            png_preview_token=None,
            note="Render preview not wired in this build; contract field reserved.",
        ),
        groups=groups,
    )


def build_mock_ai_semantic_suggestion(
    candidate: IntakeV4AiSemanticClassificationCandidatePayload,
) -> IntakeV4AiSemanticClassificationSuggestionResponse:
    """Heuristic mock — simulates future AI output without external calls or invented text."""
    suggestions: list[IntakeV4AiSemanticClassificationSuggestion] = []
    warnings: list[str] = [
        "Text appears converted to curves; exact character recognition is approximate.",
        "Mock suggestion only — AI provider not connected.",
    ]

    for group in candidate.groups:
        role = group.operator_role
        real_letters = group.geometry.outer_contours_count
        inner_holes = group.geometry.inner_holes_count
        suggested_kind = _suggested_kind_for_role(
            role,
            real_letter_count=real_letters,
            inner_hole_count=inner_holes,
        )
        confidence = _KIND_CONFIDENCE.get(suggested_kind, 0.35)
        if role == "unknown":
            confidence = min(confidence, 0.40)

        suggested_label = None
        if suggested_kind == "logo_or_emblem":
            suggested_label = "emblem"
        elif suggested_kind == "artwork":
            suggested_label = "artwork"

        suggestions.append(
            IntakeV4AiSemanticClassificationSuggestion(
                group_id=group.group_id,
                suggested_kind=suggested_kind,
                suggested_text=None,
                suggested_label=suggested_label,
                confidence=confidence,
                reasons=_suggestion_reasons(
                    role=role,
                    suggested_kind=suggested_kind,
                    real_letter_count=real_letters,
                    inner_hole_count=inner_holes,
                ),
                requires_operator_confirmation=True,
                boundary_flags=ai_semantic_boundary_flags(),
            )
        )

    return IntakeV4AiSemanticClassificationSuggestionResponse(
        schema_version=AI_SEMANTIC_CLASSIFICATION_SCHEMA_VERSION,
        suggestions=suggestions,
        warnings=warnings,
    )


def build_intake_v4_ai_informational_assist_preview(
    *,
    workspace_id: str,
    payload: IntakeV4WorkspacePayload,
) -> IntakeV4AiInformationalAssistPreviewResponse:
    candidate = build_ai_semantic_classification_candidate_payload(
        workspace_id=workspace_id,
        payload=payload,
    )
    semantic_mock = build_mock_ai_semantic_suggestion(candidate)
    mock_suggestions = semantic_classification_to_informational_suggestions(
        semantic_mock,
        candidate=candidate,
    )
    envelope = build_informational_envelope(
        source_context="intake_v4_svg_review",
        suggestions=mock_suggestions,
        warnings=semantic_mock.warnings,
    )
    flags = ai_informational_boundary_flags()
    return IntakeV4AiInformationalAssistPreviewResponse(
        workspace_id=workspace_id,
        template_code=payload.product_binding.template_code,
        preview_only=True,
        ai_not_called=True,
        context="intake_v4_svg_review",
        candidate_payload=candidate,
        mock_suggestions=mock_suggestions,
        informational_envelope=envelope,
        boundary_flags=flags,
        operator_confirmation_contract=ai_informational_confirmation_contract(),
        mock_suggestion=semantic_mock,
    )


def build_intake_v4_ai_semantic_classification_preview(
    *,
    workspace_id: str,
    payload: IntakeV4WorkspacePayload,
) -> IntakeV4AiSemanticClassificationPreviewResponse:
    informational = build_intake_v4_ai_informational_assist_preview(
        workspace_id=workspace_id,
        payload=payload,
    )
    assert informational.mock_suggestion is not None
    return IntakeV4AiSemanticClassificationPreviewResponse(
        workspace_id=informational.workspace_id,
        template_code=informational.template_code,
        preview_only=informational.preview_only,
        ai_not_called=informational.ai_not_called,
        candidate_payload=informational.candidate_payload,
        mock_suggestion=informational.mock_suggestion,
        boundary_flags=informational.boundary_flags,
        operator_confirmation_contract=informational.operator_confirmation_contract,
    )
