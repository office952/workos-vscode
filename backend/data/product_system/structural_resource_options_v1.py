"""Shared Technical Resource Options — structural materials & profiles (V1).

Technical authority only. No supplier, unit_cost, or CPP fields.
Profiles list starts empty until owner confirms ACP (or other) sections.
"""

from __future__ import annotations

from typing import Any

REGISTRY_VERSION = "structural_resource_options/v1"
ACM_BOXED_TEMPLATE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"

MAT_STRUCT_STEEL = "MAT-STRUCT-STEEL"
MAT_STRUCT_ALUMINIUM = "MAT-STRUCT-ALUMINIUM"

TOTAL_FIT_ALLOWANCE_MM = 2.0
CROSSBAR_SPACING_STEEL_MM = 1000.0
CROSSBAR_SPACING_ALUMINIUM_MM = 750.0
CROSSBAR_RULE_CODE = "MATERIAL_SPACING_V1"
FRAME_DIMENSION_RULE_CODE = "FRAME_FROM_PANEL_OUTER_DIMENSIONS_V1"

STRUCTURAL_MATERIALS: list[dict[str, Any]] = [
    {
        "code": MAT_STRUCT_STEEL,
        "label": "Oțel",
        "family": "structural_metal",
        "base_material": "steel",
        "status": "active",
        "version": 1,
        "aliases": ["steel", "otel"],
        "compatible_profile_shapes": ["SHS", "RHS"],
        "allowed_finishes": [],
        "provenance": {
            "source": "OWNER_CONFIRMED",
            "date": "2026-07-18",
            "registry_version": REGISTRY_VERSION,
        },
    },
    {
        "code": MAT_STRUCT_ALUMINIUM,
        "label": "Aluminiu",
        "family": "structural_metal",
        "base_material": "aluminium",
        "status": "active",
        "version": 1,
        "aliases": ["aluminum", "aluminiu", "aluminium"],
        "compatible_profile_shapes": ["SHS", "RHS"],
        "allowed_finishes": [],
        "provenance": {
            "source": "OWNER_CONFIRMED",
            "date": "2026-07-18",
            "registry_version": REGISTRY_VERSION,
        },
    },
]

# Profiles in shared catalog. ACP internal_frame accepted_profile_codes stays empty
# until owner confirms ACP sections. PROFILE-SHS-20X20X1_5 is OWNER_CONFIRMED for
# vertical steel fixing bracket only (see mounting_fixing_system_v1).
STRUCTURAL_PROFILES: list[dict[str, Any]] = [
    {
        "code": "PROFILE-SHS-20X20X1_5",
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
            "usage": ["vertical_steel_fixing_bracket"],
            "not_for": ["acp_internal_frame"],
            "date": "2026-07-18",
            "registry_version": REGISTRY_VERSION,
        },
    },
]

# Product System accepted options for ACP nested internal frame.
COMPONENT_ACCEPTED_OPTIONS: dict[str, dict[str, Any]] = {
    ACM_BOXED_TEMPLATE: {
        "component_template_code": ACM_BOXED_TEMPLATE,
        "capability": "internal_frame",
        "accepted_material_codes": [MAT_STRUCT_STEEL, MAT_STRUCT_ALUMINIUM],
        "accepted_profile_shapes": ["SHS", "RHS"],
        "accepted_profile_codes": [],  # PROFILE_INITIAL_SET_OWNER_GATE
        "dimension_rule": FRAME_DIMENSION_RULE_CODE,
        "crossbar_rule": CROSSBAR_RULE_CODE,
        "total_fit_allowance_mm": TOTAL_FIT_ALLOWANCE_MM,
        "crossbar_spacing_by_material": {
            MAT_STRUCT_STEEL: CROSSBAR_SPACING_STEEL_MM,
            MAT_STRUCT_ALUMINIUM: CROSSBAR_SPACING_ALUMINIUM_MM,
        },
        "profile_gate": "PROFILE_INITIAL_SET_OWNER_GATE_REQUIRED",
    }
}


def list_materials(*, active_only: bool = True) -> list[dict[str, Any]]:
    rows = list(STRUCTURAL_MATERIALS)
    if active_only:
        rows = [m for m in rows if str(m.get("status")) == "active"]
    return rows


def list_profiles(*, active_only: bool = True) -> list[dict[str, Any]]:
    rows = list(STRUCTURAL_PROFILES)
    if active_only:
        rows = [p for p in rows if str(p.get("status")) == "active"]
    return rows


def get_material(code: str) -> dict[str, Any] | None:
    key = str(code or "").strip()
    if not key:
        return None
    for row in STRUCTURAL_MATERIALS:
        if row["code"] == key:
            return dict(row)
        aliases = row.get("aliases") or []
        if key.lower() in {str(a).lower() for a in aliases}:
            return dict(row)
    return None


def get_profile(code: str) -> dict[str, Any] | None:
    key = str(code or "").strip()
    for row in STRUCTURAL_PROFILES:
        if row["code"] == key:
            return dict(row)
    return None


def get_accepted_options(template_code: str) -> dict[str, Any] | None:
    return COMPONENT_ACCEPTED_OPTIONS.get(str(template_code or "").strip())


def material_profile_compatible(material_code: str, profile_code: str) -> bool:
    material = get_material(material_code)
    profile = get_profile(profile_code)
    if not material or not profile:
        return False
    if str(material.get("status")) != "active" or str(profile.get("status")) != "active":
        return False
    shape = str(profile.get("shape") or "").upper()
    if shape not in {str(s).upper() for s in (material.get("compatible_profile_shapes") or [])}:
        return False
    compat = profile.get("compatible_material_codes") or []
    return material["code"] in compat


def registry_snapshot() -> dict[str, Any]:
    return {
        "registry_version": REGISTRY_VERSION,
        "materials": list_materials(active_only=False),
        "profiles": list_profiles(active_only=False),
        "component_accepted_options": dict(COMPONENT_ACCEPTED_OPTIONS),
        "notes": [
            "Technical authority only — no pricing fields.",
            "ACP accepted_profile_codes empty until owner confirms sections.",
        ],
    }
