"""Variant-selector material identity — non-priced family codes.

ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1:

MAT-LED-PSU-12V is a selector/family placeholder. Purchase truth lives on watt
variants. Do not invent a generic unit_cost. Do not treat missing selector price
as ACTIVE_TEMPLATE_CRITICAL when variants are owner-confirmed.
"""

from __future__ import annotations

from typing import Any, Optional

from services.volumetric_material_rate_resolver import (
    PSU_WATTAGE_VARIANT_CODES,
    PSU_WATTS_TO_VARIANT_CODE,
    TEMPLATE_PROFILE_CODE,
    TEMPLATE_PSU_CODE,
    PROFILE_DEPTH_VARIANT_CODES,
    PROFILE_DEPTH_MM_TO_VARIANT_CODE,
)

# Codes that must never own a direct purchase price as physical SKU authority.
VARIANT_SELECTOR_CODES: frozenset[str] = frozenset(
    {
        TEMPLATE_PSU_CODE,
        TEMPLATE_PROFILE_CODE,
    }
)

SELECTOR_TO_VARIANTS: dict[str, frozenset[str]] = {
    TEMPLATE_PSU_CODE: PSU_WATTAGE_VARIANT_CODES,
    TEMPLATE_PROFILE_CODE: PROFILE_DEPTH_VARIANT_CODES,
}

SELECTOR_TO_SELECTION_KEY: dict[str, str] = {
    TEMPLATE_PSU_CODE: "selected_psu_watts|psu_watts",
    TEMPLATE_PROFILE_CODE: "return_depth_mm",
}

MATERIAL_ROLE_VARIANT_SELECTOR = "variant_selector"
MATERIAL_ROLE_PHYSICAL_SKU = "physical_sku"


def is_variant_selector(material_code: str | None) -> bool:
    return str(material_code or "").strip() in VARIANT_SELECTOR_CODES


def selector_variants(material_code: str | None) -> list[str]:
    code = str(material_code or "").strip()
    variants = SELECTOR_TO_VARIANTS.get(code)
    if not variants:
        return []
    return sorted(variants)


def resolve_psu_variant_code(selected_psu_watts: Any) -> Optional[str]:
    try:
        watts = int(selected_psu_watts)
    except (TypeError, ValueError):
        return None
    return PSU_WATTS_TO_VARIANT_CODE.get(watts)


def resolve_profile_variant_code(return_depth_mm: Any) -> Optional[str]:
    try:
        depth = int(return_depth_mm)
    except (TypeError, ValueError):
        return None
    return PROFILE_DEPTH_MM_TO_VARIANT_CODE.get(depth)


def selector_note_ro(material_code: str | None) -> str:
    code = str(material_code or "").strip()
    if code == TEMPLATE_PSU_CODE:
        return (
            "Selector familie PSU 12V — nu este SKU de achiziție. "
            "Prețul vine din varianta rezolvată (60/100/160/200W) via selected_psu_watts. "
            "Fără preț generic inventat."
        )
    if code == TEMPLATE_PROFILE_CODE:
        return (
            "Selector familie profil lateral — nu este SKU de achiziție. "
            "Prețul vine din varianta pe adâncime (return_depth_mm)."
        )
    return "Selector de variantă — fără preț direct pe codul generic."


def psu_identity_map_row() -> dict[str, Any]:
    return {
        "material_code": TEMPLATE_PSU_CODE,
        "material_role": MATERIAL_ROLE_VARIANT_SELECTOR,
        "variant_selector": SELECTOR_TO_SELECTION_KEY[TEMPLATE_PSU_CODE],
        "resolved_variants": sorted(PSU_WATTAGE_VARIANT_CODES),
        "price_source": "OWNER_CONFIRMED on variant SKUs only",
        "unit": "buc",
        "canonical_as_sku": False,
        "canonical_as_selector": True,
        "remediation": "Outcome A — classify selector; no generic price",
        "data_write_required": False,
        "confidence": "high",
    }
