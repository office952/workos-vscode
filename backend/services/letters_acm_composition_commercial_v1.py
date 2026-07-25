"""Letters↔ACM composition commercial connection lines (CPP).

Owner SoT: frontend lettersAcmCompositionConnectionPrices.ts
+ LETTERS_ACM_COMPATIBILITY_CONTRACT_V1.
Not CostEngine BOM rewrite. Not hourly.
"""

from __future__ import annotations

from typing import Any, Mapping

# Line codes / rates mirrored in data.commercial_rules_volumetric_v2
COMPOSITION_LINE_PREFIX = "letters_acm_conn_"
LINE_SABLON = "letters_acm_conn_sablon_process"
LINE_PACK = "letters_acm_conn_pack"
PRICING_PACK_MIN = "LETTERS_ACM_PACK_M2_MIN"


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def is_letters_acm_composition_active(payload: Mapping[str, Any] | None) -> bool:
    """True when ACM boxed mounting carries applied letters content."""
    if not isinstance(payload, Mapping):
        return False
    from services.acm_boxed_support_composition_v1 import (
        APPLIED_CONTENT_LETTERS,
        read_applied_content,
    )
    from services.acm_quote_input_helpers import is_acm_boxed_mounting_payload

    if not is_acm_boxed_mounting_payload(payload):
        return False
    return read_applied_content(payload) == APPLIED_CONTENT_LETTERS


def _positive_float(value: Any) -> float | None:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    return n


def resolve_letters_layer_outbox_m2(
    payload: Mapping[str, Any] | None,
) -> tuple[float | None, str]:
    """Qty for mp connection lines — prefer explicit outbox; fallback mounting_template_area.

    Never invents per-glyph sum. Caller must treat fallback as honesty warning.
    """
    if not isinstance(payload, Mapping):
        return None, "missing_payload"

    finish = _as_mapping(payload.get("finish_setup")) or {}
    quote_input = _as_mapping(payload.get("quote_input")) or {}
    quote_geometry = _as_mapping(payload.get("quote_geometry")) or {}

    for path_label, raw in (
        ("letters_layer_outbox_m2", payload.get("letters_layer_outbox_m2")),
        ("finish_setup.letters_layer_outbox_m2", finish.get("letters_layer_outbox_m2")),
        ("quote_input.letters_layer_outbox_m2", quote_input.get("letters_layer_outbox_m2")),
        (
            "finish_setup.mounting_template_area_m2",
            finish.get("mounting_template_area_m2"),
        ),
        ("mounting_template_area_m2", payload.get("mounting_template_area_m2")),
        (
            "quote_input.mounting_template_area_m2",
            quote_input.get("mounting_template_area_m2"),
        ),
    ):
        qty = _positive_float(raw)
        if qty is not None:
            return qty, path_label

    # Last resort: document / letter face area (still integral bbox-ish, not per piece)
    for path_label, raw in (
        ("letter_face_area_m2", payload.get("letter_face_area_m2")),
        ("quote_geometry.letter_face_area_m2", quote_geometry.get("letter_face_area_m2")),
        ("quote_input.letter_face_area_m2", quote_input.get("letter_face_area_m2")),
        ("document_area_m2", payload.get("document_area_m2")),
    ):
        qty = _positive_float(raw)
        if qty is not None:
            return qty, path_label

    return None, "missing_letters_layer_outbox_m2"
