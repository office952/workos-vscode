"""Build 3.1 — suppress runtime-capture fatals for modules outside offer_scope."""

from __future__ import annotations

from typing import Any

# Capture fatals that belong to mounting / installation template — not sold in Slice-1 subsets.
MOUNTING_CAPTURE_FATAL_CODES = frozenset(
    {
        "MOUNTING_SOLUTION_MISSING",
        "MOUNTING_SOLUTION_INVALID",
        "MOUNTING_SCOPE_MISSING",
        "MOUNTING_SYSTEM_CONFIRMATION_REQUIRED",
    }
)

# Capture fatals that belong to lighting / electrical sold modules.
LIGHTING_CAPTURE_FATAL_CODES = frozenset(
    {
        "LIGHTING_MODE_CONFIRMATION_REQUIRED",
    }
)

FACE_CAPTURE_FATAL_CODES = frozenset(
    {
        "FACE_MATERIAL_MISSING",
        "FACE_FINISH_TARGET_MISSING",
        "PRINT_REQUIRED_UNKNOWN",
        "LAMINATION_REQUIRED_UNKNOWN",
        "SELECTED_FACE_LAYER_MISSING",
    }
)

RETURN_CANT_CAPTURE_FATAL_CODES = frozenset(
    {
        "RETURN_CANT_MATERIAL_MISSING",
        "RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED",
    }
)

# VL letter/artwork capture fatals — not applicable to ACM panel-alone (support_only).
ACM_PANEL_ONLY_LETTER_CAPTURE_FATAL_CODES = frozenset(
    {
        "SELECTED_LAYER_REFS_EMPTY",
        "FINISH_TARGET_MISSING",
        "PRINT_REQUIRED_UNKNOWN",
        "LAMINATION_REQUIRED_UNKNOWN",
        *FACE_CAPTURE_FATAL_CODES,
        *RETURN_CANT_CAPTURE_FATAL_CODES,
        *LIGHTING_CAPTURE_FATAL_CODES,
    }
)

ACM_SUPPORT_TEMPLATE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"


def is_acm_panel_only_composition(payload_raw: dict[str, Any]) -> bool:
    """True when operator path is ACM panel-alone (no letters/logo sold composition)."""
    recommendation = payload_raw.get("product_composition_recommendation")
    if isinstance(recommendation, dict):
        ctype = str(recommendation.get("composition_type") or "").strip().lower()
        if ctype in {"support_only", "support_only_pending"}:
            return True

    confirmed = payload_raw.get("product_composition_confirmed")
    if not (isinstance(confirmed, dict) and confirmed.get("confirmed") is True):
        return False
    items = confirmed.get("items")
    if not isinstance(items, list) or not items:
        return False
    codes = {
        str(it.get("template_code") or "").strip()
        for it in items
        if isinstance(it, dict)
    }
    codes.discard("")
    return codes == {ACM_SUPPORT_TEMPLATE}


def inactive_module_capture_codes_for_payload(payload_raw: dict[str, Any]) -> frozenset[str]:
    """Return capture codes that must not gate readiness/UI for the current sold scope.

    Full product / legacy (no subset) keeps all capture fatals unchanged — except
    ACM panel-alone composition, which suppresses VL letter/artwork capture fatals.
    """
    from services.offer_scope_resolver_service import extract_offer_scope, resolve_offer_scope

    inactive: set[str] = set()
    if is_acm_panel_only_composition(payload_raw):
        inactive.update(ACM_PANEL_ONLY_LETTER_CAPTURE_FATAL_CODES)

    scope = extract_offer_scope(payload_raw, None)
    resolved = resolve_offer_scope(scope)
    if resolved.use_legacy or resolved.mode != "component_subset":
        return frozenset(inactive)

    sold = set(resolved.canonical_sold_modules)
    # Mounting / șablon are not Slice-1 sold modules — never fatal on subsets.
    inactive.update(MOUNTING_CAPTURE_FATAL_CODES)
    if "LIGHTING" not in sold and "ELECTRICAL" not in sold:
        inactive.update(LIGHTING_CAPTURE_FATAL_CODES)
    if "FACE" not in sold:
        inactive.update(FACE_CAPTURE_FATAL_CODES)
    if "RETURN-CANT" not in sold:
        inactive.update(RETURN_CANT_CAPTURE_FATAL_CODES)
    return frozenset(inactive)
