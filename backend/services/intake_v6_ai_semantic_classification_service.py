"""Intake V6 AI semantic classification namespace."""

from __future__ import annotations

from services.intake_v4_ai_semantic_classification_service import (
    build_intake_v4_ai_informational_assist_preview,
    build_intake_v4_ai_semantic_classification_preview,
)
from services.intake_v6_response_normalization import normalize_intake_v6_value


def _normalized_payload(model):
    return normalize_intake_v6_value(model.model_dump(mode="json"))


def build_intake_v6_ai_informational_assist_preview(*args, **kwargs):
    return _normalized_payload(build_intake_v4_ai_informational_assist_preview(*args, **kwargs))


def build_intake_v6_ai_semantic_classification_preview(*args, **kwargs):
    return _normalized_payload(build_intake_v4_ai_semantic_classification_preview(*args, **kwargs))
