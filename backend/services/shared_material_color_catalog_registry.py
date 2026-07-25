"""Read-only, seedless material/color catalog registry.

This module defines canonical material families, series, colors, variants, and
inventory key previews without DB, seeds, API endpoints, or stock mutation.
It is intended to feed future logical-list enrichment, catalog admin pages, and
the future CNC operation pricing UI contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class MaterialFamily:
    family_code: str
    name: str
    usage_kind: str
    compatible_roles: tuple[str, ...]
    active: bool = True


@dataclass(frozen=True)
class MaterialSeries:
    series_code: str
    family_code: str
    brand: str | None
    series_number: str | None
    commercial_name: str
    material_kind: str
    default_unit: str
    active: bool = True


@dataclass(frozen=True)
class CatalogColor:
    color_code: str
    color_name: str
    supplier_color_code: str | None
    approximate_hex_for_ui_only: str | None
    finish_surface: str
    active: bool = True


@dataclass(frozen=True)
class MaterialVariant:
    material_variant_code: str
    material_code: str
    family_code: str
    series_code: str
    color_code: str
    color_name: str
    thickness_mm: float | None
    width_mm: int | None
    usable_width_mm: int | None
    sheet_width_mm: int | None
    sheet_height_mm: int | None
    finish_surface: str
    supplier_code: str | None
    unit: str
    active: bool
    cnc_processable: bool
    compatible_operations: tuple[str, ...]


@dataclass(frozen=True)
class InventoryKeyPreview:
    material_variant_code: str
    preview_key: str
    stock_identity_status: str


@dataclass(frozen=True)
class MaterialCompatibilityRule:
    material_variant_code: str
    compatible_roles: tuple[str, ...]
    compatible_operations: tuple[str, ...]
    notes: str


_MATERIAL_FAMILIES: Final[tuple[MaterialFamily, ...]] = (
    MaterialFamily("VINYL", "Vinyl", "vinyl_finish", ("LETTER_FACE", "RETURN_WRAP", "PANEL_FACE")),
    MaterialFamily("TRANSLUCENT_VINYL", "Translucent Vinyl", "illuminated_face_finish", ("LIGHTED_FACE", "ACRYLIC_FACE_BACKLIT")),
    MaterialFamily("PAINT", "Paint / Powder Coating", "paint_finish", ("RETURN_PAINT", "METAL_PAINT", "COATING")),
    MaterialFamily("PLEXIGLAS", "Plexiglas / Acrylic", "structural_face_panel", ("LETTER_FACE", "LOGO_FACE", "LIGHTBOX_FACE")),
    MaterialFamily("FOREX", "Forex / Expanded PVC", "structural_back_panel", ("LETTER_BACK", "LOGO_BACK", "MOUNT_TEMPLATE")),
    MaterialFamily("ACM", "ACM / Dibond", "rigid_panel", ("PANEL_FACE", "CASSETTE_FACE")),
    MaterialFamily("ALUMINUM_SHEET", "Aluminum Sheet", "metal_sheet", ("METAL_FACE", "PLATE_COMPONENT")),
    MaterialFamily("ALUMINUM_RETURN", "Aluminum Return", "return_profile", ("RETURN_PROFILE", "SIDE_WALL")),
    MaterialFamily("CNC_PROCESSABLE_MATERIAL", "CNC Processable Material", "cnc_capability_group", ("CNC_INPUT",)),
)


_MATERIAL_SERIES: Final[tuple[MaterialSeries, ...]] = (
    MaterialSeries("ORACAL_641", "VINYL", "Oracal", "641", "Oracal 641 Economy Cal", "standard_vinyl", "m2"),
    MaterialSeries("ORACAL_651", "VINYL", "Oracal", "651", "Oracal 651 Intermediate Cal", "premium_vinyl", "m2"),
    MaterialSeries("ORACAL_8500", "TRANSLUCENT_VINYL", "Oracal", "8500", "Oracal 8500 Translucent Cal", "translucent_vinyl", "m2"),
    MaterialSeries("RAL_PAINT", "PAINT", "RAL", "RAL", "RAL Paint", "paint_coating", "m2"),
    MaterialSeries("PLEXIGLAS_3MM", "PLEXIGLAS", None, "3MM", "plexiglas 3mm PMMA - opal", "acrylic_sheet", "m2"),
    MaterialSeries("FOREX_10MM", "FOREX", None, "10MM", "Forex 10 mm", "expanded_pvc_sheet", "m2"),
    MaterialSeries("ACM_3MM", "ACM", None, "3MM", "ACM 3 mm", "acm_sheet", "m2"),
    MaterialSeries("ALUMINUM_SHEET_GENERIC", "ALUMINUM_SHEET", None, None, "Aluminum Sheet Generic", "aluminum_sheet", "m2"),
    MaterialSeries("ALUMINUM_RETURN_GENERIC", "ALUMINUM_RETURN", None, None, "Aluminum Return Generic", "aluminum_return", "m"),
)


_CATALOG_COLORS: Final[tuple[CatalogColor, ...]] = (
    CatalogColor("UNKNOWN", "Unknown", None, None, "unknown"),
    CatalogColor("WHITE", "White", None, "#F5F5F0", "gloss"),
    CatalogColor("BLACK", "Black", None, "#101010", "gloss"),
    CatalogColor("ANTHRACITE_GREY", "Anthracite grey", None, "#383E42", "matte"),
    CatalogColor("RAL_9005", "Jet black", "9005", "#0A0A0A", "matte"),
    CatalogColor("RAL_9010", "Pure white", "9010", "#F4F4EF", "matte"),
    CatalogColor("RAL_7016", "Anthracite grey", "7016", "#383E42", "matte"),
    CatalogColor("ORACAL_WHITE", "Oracal white", "010", "#F5F5F2", "gloss"),
    CatalogColor("ORACAL_BLACK", "Oracal black", "070", "#111111", "gloss"),
    CatalogColor("ORACAL_GREEN", "Oracal green", "061", "#008E4F", "gloss"),
    CatalogColor("ORACAL_BLUE", "Oracal blue", "049", "#1157B7", "gloss"),
)


_MATERIAL_VARIANTS: Final[tuple[MaterialVariant, ...]] = (
    MaterialVariant("ORACAL_641_UNKNOWN", "ORACAL_641", "VINYL", "ORACAL_641", "UNKNOWN", "Unknown", None, 1000, 960, None, None, "gloss", None, "m2", True, False, ()),
    MaterialVariant("ORACAL_641_WHITE", "ORACAL_641", "VINYL", "ORACAL_641", "WHITE", "White", None, 1000, 960, None, None, "gloss", "641-010", "m2", True, False, ()),
    MaterialVariant("ORACAL_641_BLACK", "ORACAL_641", "VINYL", "ORACAL_641", "BLACK", "Black", None, 1000, 960, None, None, "gloss", "641-070", "m2", True, False, ()),
    MaterialVariant("ORACAL_651_UNKNOWN", "ORACAL_651", "VINYL", "ORACAL_651", "UNKNOWN", "Unknown", None, 1000, 960, None, None, "gloss", None, "m2", True, False, ()),
    MaterialVariant("ORACAL_651_WHITE", "ORACAL_651", "VINYL", "ORACAL_651", "WHITE", "White", None, 1000, 960, None, None, "gloss", "651-010", "m2", True, False, ()),
    MaterialVariant("ORACAL_651_BLACK", "ORACAL_651", "VINYL", "ORACAL_651", "BLACK", "Black", None, 1000, 960, None, None, "gloss", "651-070", "m2", True, False, ()),
    MaterialVariant("ORACAL_8500_UNKNOWN", "ORACAL_8500", "TRANSLUCENT_VINYL", "ORACAL_8500", "UNKNOWN", "Unknown", None, 1000, 960, None, None, "translucent", None, "m2", True, False, ()),
    MaterialVariant("ORACAL_8500_WHITE_TRANSLUCENT", "ORACAL_8500", "TRANSLUCENT_VINYL", "ORACAL_8500", "WHITE", "White translucent", None, 1000, 960, None, None, "translucent", "8500-010", "m2", True, False, ()),
    MaterialVariant("RAL_9005_MATTE_PAINT", "RAL_9005", "PAINT", "RAL_PAINT", "RAL_9005", "Jet black", None, None, None, None, None, "matte", "RAL-9005", "m2", True, False, ()),
    MaterialVariant("RAL_9010_MATTE_PAINT", "RAL_9010", "PAINT", "RAL_PAINT", "RAL_9010", "Pure white", None, None, None, None, None, "matte", "RAL-9010", "m2", True, False, ()),
    MaterialVariant("RAL_7016_MATTE_PAINT", "RAL_7016", "PAINT", "RAL_PAINT", "RAL_7016", "Anthracite grey", None, None, None, None, None, "matte", "RAL-7016", "m2", True, False, ()),
    MaterialVariant("PLEXIGLAS_3MM_OPAL", "PLEXIGLAS_3MM", "PLEXIGLAS", "PLEXIGLAS_3MM", "WHITE", "Opal", 3.0, None, None, 2050, 3050, "opal", "MAT-ACP-FATA-LITERE", "m2", True, True, ("CNC_CUT_PLEXIGLAS_3MM", "CNC_FLAT_RECESS_PLEXIGLAS_GLUE_SEAT", "CANAL_PLAT_GHIDAJ")),
    MaterialVariant("PLEXIGLAS_3MM_CLEAR", "PLEXIGLAS_3MM", "PLEXIGLAS", "PLEXIGLAS_3MM", "UNKNOWN", "Clear", 3.0, None, None, 2050, 3050, "clear", "MAT-ACP-FATA-LITERE", "m2", True, True, ("CNC_CUT_PLEXIGLAS_3MM", "CNC_FLAT_RECESS_PLEXIGLAS_GLUE_SEAT", "CANAL_PLAT_GHIDAJ")),
    MaterialVariant("FOREX_10MM_WHITE", "FOREX_10MM", "FOREX", "FOREX_10MM", "WHITE", "White", 10.0, None, None, 2050, 3050, "matte", "MAT-SPATE-PVC-LITERE", "m2", True, True, ("CNC_CUT_FOREX_10MM", "CNC_FLAT_RECESS_FOREX_BACK_SEAT")),
    MaterialVariant("ACM_3MM_GENERIC", "ACM_3MM", "ACM", "ACM_3MM", "UNKNOWN", "Generic ACM", 3.0, None, None, 1500, 4000, "generic", None, "m2", True, True, ("CNC_CUT_ACM_3MM", "CNC_FLAT_RECESS_ACM_PENDING")),
    MaterialVariant("ALUMINUM_SHEET_GENERIC", "ALUMINUM_SHEET_GENERIC", "ALUMINUM_SHEET", "ALUMINUM_SHEET_GENERIC", "UNKNOWN", "Generic aluminum sheet", 3.0, None, None, 1500, 3000, "generic", None, "m2", True, True, ("CNC_CUT_ALUMINUM_SHEET_LE_3_5MM",)),
    MaterialVariant("ALUMINUM_RETURN_GENERIC", "ALUMINUM_RETURN_GENERIC", "ALUMINUM_RETURN", "ALUMINUM_RETURN_GENERIC", "UNKNOWN", "Generic aluminum return", None, None, None, None, None, "generic", "MAT-PROFIL-LATERAL-LITERE", "m", True, False, ()),
)


_COMPATIBILITY_RULES: Final[tuple[MaterialCompatibilityRule, ...]] = (
    MaterialCompatibilityRule("ORACAL_641_UNKNOWN", ("LETTER_FACE",), (), "Read-only fallback for 641 face vinyl when color is unresolved."),
    MaterialCompatibilityRule("ORACAL_641_WHITE", ("LETTER_FACE",), (), "641 white remains distinct from 651 white for stock and pricing."),
    MaterialCompatibilityRule("ORACAL_641_BLACK", ("LETTER_FACE",), (), "641 black remains distinct from 651 black for stock and pricing."),
    MaterialCompatibilityRule("ORACAL_651_UNKNOWN", ("LETTER_FACE", "RETURN_WRAP"), (), "Default permanent Oracal fallback when color is unresolved."),
    MaterialCompatibilityRule("ORACAL_651_WHITE", ("LETTER_FACE", "RETURN_WRAP"), (), "651 white is a distinct permanent vinyl stock target."),
    MaterialCompatibilityRule("ORACAL_651_BLACK", ("LETTER_FACE", "RETURN_WRAP"), (), "651 black is a distinct permanent vinyl stock target."),
    MaterialCompatibilityRule("ORACAL_8500_UNKNOWN", ("LIGHTED_FACE",), (), "Translucent fallback for illuminated acrylic faces."),
    MaterialCompatibilityRule("ORACAL_8500_WHITE_TRANSLUCENT", ("LIGHTED_FACE", "ACRYLIC_FACE_BACKLIT"), (), "8500 remains separate from 641/651 and is compatible with illuminated faces only."),
    MaterialCompatibilityRule("RAL_9005_MATTE_PAINT", ("RETURN_PAINT", "METAL_PAINT"), (), "RAL paint is a process/finish path, not a vinyl path."),
    MaterialCompatibilityRule("RAL_9010_MATTE_PAINT", ("RETURN_PAINT", "METAL_PAINT"), (), "RAL paint is a process/finish path, not a vinyl path."),
    MaterialCompatibilityRule("RAL_7016_MATTE_PAINT", ("RETURN_PAINT", "METAL_PAINT"), (), "RAL paint is a process/finish path, not a vinyl path."),
    MaterialCompatibilityRule("PLEXIGLAS_3MM_OPAL", ("LETTER_FACE", "LOGO_FACE"), ("CNC_CUT_PLEXIGLAS_3MM", "CNC_FLAT_RECESS_PLEXIGLAS_GLUE_SEAT", "CANAL_PLAT_GHIDAJ"), "Future CNC pricing UI hook preserved for confirmed face cut + guide channel semantics."),
    MaterialCompatibilityRule("PLEXIGLAS_3MM_CLEAR", ("LETTER_FACE", "LOGO_FACE"), ("CNC_CUT_PLEXIGLAS_3MM", "CNC_FLAT_RECESS_PLEXIGLAS_GLUE_SEAT", "CANAL_PLAT_GHIDAJ"), "Future CNC pricing UI hook preserved for clear acrylic variants as well."),
    MaterialCompatibilityRule("FOREX_10MM_WHITE", ("LETTER_BACK", "LOGO_BACK"), ("CNC_CUT_FOREX_10MM", "CNC_FLAT_RECESS_FOREX_BACK_SEAT"), "Preserves the owner 3 + 2 = 5 pass Forex back model for future CNC UI."),
    MaterialCompatibilityRule("ACM_3MM_GENERIC", ("PANEL_FACE", "CASSETTE_FACE"), ("CNC_CUT_ACM_3MM", "CNC_FLAT_RECESS_ACM_PENDING"), "ACM flat recess remains a future pending CNC pricing/admin decision."),
    MaterialCompatibilityRule("ALUMINUM_SHEET_GENERIC", ("METAL_FACE",), ("CNC_CUT_ALUMINUM_SHEET_LE_3_5MM",), "Generic aluminum sheet keeps a future CNC cut pricing hook without implementing UI now."),
    MaterialCompatibilityRule("ALUMINUM_RETURN_GENERIC", ("RETURN_PROFILE", "SIDE_WALL"), (), "Return profile remains a stock/profile family, not a CNC sheet variant in this slice."),
)


_FAMILIES_BY_CODE: Final[dict[str, MaterialFamily]] = {item.family_code: item for item in _MATERIAL_FAMILIES}
_SERIES_BY_CODE: Final[dict[str, MaterialSeries]] = {item.series_code: item for item in _MATERIAL_SERIES}
_COLORS_BY_CODE: Final[dict[str, CatalogColor]] = {item.color_code: item for item in _CATALOG_COLORS}
_VARIANTS_BY_CODE: Final[dict[str, MaterialVariant]] = {item.material_variant_code: item for item in _MATERIAL_VARIANTS}
_RULES_BY_VARIANT: Final[dict[str, MaterialCompatibilityRule]] = {item.material_variant_code: item for item in _COMPATIBILITY_RULES}

_ORACAL_SERIES_ALIASES: Final[dict[str, str]] = {
    "641": "ORACAL_641",
    "ORACAL_641": "ORACAL_641",
    "oracal_641": "ORACAL_641",
    "651": "ORACAL_651",
    "ORACAL_651": "ORACAL_651",
    "oracal_651": "ORACAL_651",
    "8500": "ORACAL_8500",
    "ORACAL_8500": "ORACAL_8500",
    "oracal_8500": "ORACAL_8500",
}

_ORACAL_COLOR_ALIASES: Final[dict[str, str]] = {
    "": "UNKNOWN",
    "UNKNOWN": "UNKNOWN",
    "ORACAL_UNKNOWN": "UNKNOWN",
    "WHITE": "WHITE",
    "ORACAL_WHITE": "WHITE",
    "010": "WHITE",
    "BLACK": "BLACK",
    "ORACAL_BLACK": "BLACK",
    "070": "BLACK",
    "GREEN": "GREEN",
    "ORACAL_GREEN": "GREEN",
    "061": "GREEN",
    "BLUE": "BLUE",
    "ORACAL_BLUE": "BLUE",
    "049": "BLUE",
}

_RAL_CODE_ALIASES: Final[dict[str, str]] = {
    "9005": "RAL_9005",
    "RAL9005": "RAL_9005",
    "RAL_9005": "RAL_9005",
    "9010": "RAL_9010",
    "RAL9010": "RAL_9010",
    "RAL_9010": "RAL_9010",
    "7016": "RAL_7016",
    "RAL7016": "RAL_7016",
    "RAL_7016": "RAL_7016",
}


def _normalize_token(value: str | None) -> str:
    token = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    return token


def list_material_families() -> tuple[MaterialFamily, ...]:
    return _MATERIAL_FAMILIES


def list_material_series() -> tuple[MaterialSeries, ...]:
    return _MATERIAL_SERIES


def list_catalog_colors() -> tuple[CatalogColor, ...]:
    return _CATALOG_COLORS


def list_material_variants() -> tuple[MaterialVariant, ...]:
    return _MATERIAL_VARIANTS


def list_material_compatibility_rules() -> tuple[MaterialCompatibilityRule, ...]:
    return _COMPATIBILITY_RULES


def get_material_variant(material_variant_code: str) -> MaterialVariant | None:
    return _VARIANTS_BY_CODE.get(_normalize_token(material_variant_code))


def find_variants_by_series(series_code: str) -> tuple[MaterialVariant, ...]:
    normalized = _normalize_token(series_code)
    return tuple(item for item in _MATERIAL_VARIANTS if item.series_code == normalized)


def find_variants_by_family(family_code: str) -> tuple[MaterialVariant, ...]:
    normalized = _normalize_token(family_code)
    return tuple(item for item in _MATERIAL_VARIANTS if item.family_code == normalized)


def find_variants_by_color(color_code: str) -> tuple[MaterialVariant, ...]:
    normalized = _normalize_token(color_code)
    if normalized in _ORACAL_COLOR_ALIASES:
        normalized = _ORACAL_COLOR_ALIASES[normalized]
    return tuple(item for item in _MATERIAL_VARIANTS if item.color_code == normalized)


def build_inventory_key_preview(
    material_variant_code: str,
    roll_id: str | None = None,
    batch_id: str | None = None,
) -> InventoryKeyPreview:
    variant = get_material_variant(material_variant_code)
    if variant is None:
        raise ValueError(f"Unknown material_variant_code: {material_variant_code}")

    if variant.family_code in {"VINYL", "TRANSLUCENT_VINYL"}:
        if roll_id:
            return InventoryKeyPreview(variant.material_variant_code, f"{variant.material_variant_code}::ROLL::{roll_id}", "roll_assigned")
        return InventoryKeyPreview(variant.material_variant_code, f"{variant.material_variant_code}::ROLL_PENDING", "roll_pending")

    if variant.family_code == "PAINT":
        return InventoryKeyPreview(variant.material_variant_code, f"{variant.material_variant_code}::PROCESS_PENDING", "process_pending")

    if batch_id:
        return InventoryKeyPreview(variant.material_variant_code, f"{variant.material_variant_code}::BATCH::{batch_id}", "batch_assigned")
    return InventoryKeyPreview(variant.material_variant_code, f"{variant.material_variant_code}::BATCH_PENDING", "batch_pending")


def resolve_oracal_variant(series_code: str, color_code: str | None = None) -> MaterialVariant | None:
    normalized_series = _ORACAL_SERIES_ALIASES.get(_normalize_token(series_code))
    if normalized_series is None:
        return None
    normalized_color = _ORACAL_COLOR_ALIASES.get(_normalize_token(color_code), "UNKNOWN")
    mapping = {
        ("ORACAL_641", "WHITE"): "ORACAL_641_WHITE",
        ("ORACAL_641", "BLACK"): "ORACAL_641_BLACK",
        ("ORACAL_641", "UNKNOWN"): "ORACAL_641_UNKNOWN",
        ("ORACAL_651", "WHITE"): "ORACAL_651_WHITE",
        ("ORACAL_651", "BLACK"): "ORACAL_651_BLACK",
        ("ORACAL_651", "UNKNOWN"): "ORACAL_651_UNKNOWN",
        ("ORACAL_8500", "WHITE"): "ORACAL_8500_WHITE_TRANSLUCENT",
        ("ORACAL_8500", "UNKNOWN"): "ORACAL_8500_UNKNOWN",
    }
    variant_code = mapping.get((normalized_series, normalized_color))
    if variant_code is None:
        variant_code = mapping.get((normalized_series, "UNKNOWN"))
    return _VARIANTS_BY_CODE.get(variant_code) if variant_code else None


def resolve_ral_variant(ral_code: str, finish_surface: str | None = None) -> MaterialVariant | None:
    normalized_ral = _RAL_CODE_ALIASES.get(_normalize_token(ral_code))
    if normalized_ral is None:
        return None
    normalized_finish = _normalize_token(finish_surface or "matte")
    if normalized_finish != "MATTE":
        return None
    return _VARIANTS_BY_CODE.get(f"{normalized_ral}_MATTE_PAINT")


def is_cnc_processable(material_variant_code: str) -> bool:
    variant = get_material_variant(material_variant_code)
    return bool(variant and variant.cnc_processable)


def get_compatible_cnc_operations(material_variant_code: str) -> tuple[str, ...]:
    variant = get_material_variant(material_variant_code)
    if variant is None:
        return ()
    return variant.compatible_operations


__all__ = [
    "CatalogColor",
    "InventoryKeyPreview",
    "MaterialCompatibilityRule",
    "MaterialFamily",
    "MaterialSeries",
    "MaterialVariant",
    "build_inventory_key_preview",
    "find_variants_by_color",
    "find_variants_by_family",
    "find_variants_by_series",
    "get_compatible_cnc_operations",
    "get_material_variant",
    "is_cnc_processable",
    "list_catalog_colors",
    "list_material_compatibility_rules",
    "list_material_families",
    "list_material_series",
    "list_material_variants",
    "resolve_oracal_variant",
    "resolve_ral_variant",
]