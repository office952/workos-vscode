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


def inactive_module_capture_codes_for_payload(payload_raw: dict[str, Any]) -> frozenset[str]:
    """Return capture codes that must not gate readiness/UI for the current sold scope.

    Full product / legacy (no subset) keeps all capture fatals unchanged.
    """
    from services.offer_scope_resolver_service import extract_offer_scope, resolve_offer_scope

    scope = extract_offer_scope(payload_raw, None)
    resolved = resolve_offer_scope(scope)
    if resolved.use_legacy or resolved.mode != "component_subset":
        return frozenset()

    sold = set(resolved.canonical_sold_modules)
    inactive: set[str] = set()
    # Mounting / șablon are not Slice-1 sold modules — never fatal on subsets.
    inactive.update(MOUNTING_CAPTURE_FATAL_CODES)
    if "LIGHTING" not in sold and "ELECTRICAL" not in sold:
        inactive.update(LIGHTING_CAPTURE_FATAL_CODES)
    if "FACE" not in sold:
        inactive.update(FACE_CAPTURE_FATAL_CODES)
    if "RETURN-CANT" not in sold:
        inactive.update(RETURN_CANT_CAPTURE_FATAL_CODES)
    return frozenset(inactive)
