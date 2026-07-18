"""Mounting fixing system contracts — technical wall attachment (not commercial mounting).

OWNER_CONFIRMED: Brat otel vertical uses PROFILE-SHS-20X20X1_5.
This profile is NOT accepted for ACP internal frame (separate gate).
"""

from __future__ import annotations

from typing import Any

from data.product_system.structural_resource_options_v1 import (
    MAT_STRUCT_STEEL,
    REGISTRY_VERSION,
)

FIXING_CONTRACT_VERSION = "mounting_fixing_system/v1"
VERTICAL_STEEL_BRACKET = "FIXING-SYSTEM-VERTICAL-STEEL-BRACKET"
PROFILE_SHS_20X20X1_5 = "PROFILE-SHS-20X20X1_5"

# Profile identity for fixing bracket only (also registered in structural RO catalog).
FIXING_MAIN_PROFILE: dict[str, Any] = {
    "code": PROFILE_SHS_20X20X1_5,
    "label": "Țeavă pătrată 20×20×1.5 mm",
    "shape": "SHS",
    "width_mm": 20.0,
    "height_mm": 20.0,
    "wall_thickness_mm": 1.5,
    "compatible_material_codes": [MAT_STRUCT_STEEL],
    "status": "active",
    "version": 1,
    "aliases": ["20x20x1.5", "20×20×1.5"],
    "provenance": {
        "source": "OWNER_CONFIRMED",
        "usage": "vertical_steel_fixing_bracket",
        "not_for": "acp_internal_frame",
        "date": "2026-07-18",
        "registry_version": REGISTRY_VERSION,
    },
}

FIXING_SYSTEM_TYPES: dict[str, dict[str, Any]] = {
    VERTICAL_STEEL_BRACKET: {
        "type_code": VERTICAL_STEEL_BRACKET,
        "owner_label": "Brat otel vertical",
        "material_code": MAT_STRUCT_STEEL,
        "main_profile_code": PROFILE_SHS_20X20X1_5,
        "top_angle": {
            "resource_type": "STEEL_ANGLE",
            "resource_family": "STEEL_ANGLE",
            "dimension_mode": "MANUAL_CONFIRMATION_REQUIRED",
            "length_mm": None,
            "notes": "Cornier debitat din bara cornier otel; cotă per lucrare.",
        },
        "bottom_horizontal_bar": {
            "material_code": MAT_STRUCT_STEEL,
            "dimension_mode": "MANUAL_CONFIRMATION_REQUIRED",
            "length_mm": None,
            "notes": "Bara orizontală sudată inferior; cotă per lucrare.",
        },
        "lower_fastener": {
            "type": "SELF_DRILLING_HEX_HEAD",
            "owner_label": "Autoforante cap hexagonal 4.5x60 mm",
            "diameter_mm": 4.5,
            "length_mm": 60,
        },
        "geometry_notes": [
            "Geometrie practică tip T întors + cornier superior.",
            "Nu există default dimensional sau formulă automată pentru cornier/bara inferioară.",
        ],
    }
}

# Parent product templates that may expose fixing systems in Intake.
PARENT_FIXING_AVAILABILITY: dict[str, dict[str, Any]] = {
    "TPL-VOLUMETRIC-LETTERS_v2": {
        "available_types": [VERTICAL_STEEL_BRACKET],
        "required": False,
        "independent_of_commercial_mounting_scope": True,
        "independent_of_acp_internal_frame": True,
        "independent_of_metal_premount": True,
    },
    "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1": {
        "available_types": [VERTICAL_STEEL_BRACKET],
        "required": False,
        "independent_of_commercial_mounting_scope": True,
        "independent_of_acp_internal_frame": True,
        "independent_of_metal_premount": True,
    },
}


def get_fixing_type(type_code: str) -> dict[str, Any] | None:
    return FIXING_SYSTEM_TYPES.get(str(type_code or "").strip())


def available_for_template(template_code: str) -> dict[str, Any] | None:
    return PARENT_FIXING_AVAILABILITY.get(str(template_code or "").strip())
