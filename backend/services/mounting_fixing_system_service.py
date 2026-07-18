"""Normalize / project mounting fixing systems (wall attachment)."""

from __future__ import annotations

from typing import Any, Mapping

from data.product_system.mounting_fixing_system_v1 import (
    FIXING_CONTRACT_VERSION,
    VERTICAL_STEEL_BRACKET,
    get_fixing_type,
)
from data.product_system.structural_resource_options_v1 import get_material, get_profile


def empty_fixing_system() -> dict[str, Any]:
    return {
        "type_code": None,
        "material_code": None,
        "main_profile_code": None,
        "top_angle": None,
        "bottom_horizontal_bar": None,
        "lower_fastener": None,
        "confirmation_status": "NOT_APPLICABLE",
        "quantity_status": "NOT_APPLICABLE",
        "blockers": [],
        "provenance": {"contract_version": FIXING_CONTRACT_VERSION},
    }


def normalize_mounting_fixing_system(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        return empty_fixing_system()
    type_code = str(raw.get("type_code") or "").strip() or None
    if not type_code:
        return empty_fixing_system()
    spec = get_fixing_type(type_code)
    if not spec:
        return {
            **empty_fixing_system(),
            "type_code": type_code,
            "confirmation_status": "INCOMPLETE",
            "blockers": ["fixing_system_type_unknown"],
        }

    top = dict(spec["top_angle"])
    bottom = dict(spec["bottom_horizontal_bar"])
    # Manual lengths may be captured later; null is valid MANUAL_CONFIRMATION_REQUIRED.
    raw_top = raw.get("top_angle") if isinstance(raw.get("top_angle"), Mapping) else {}
    raw_bottom = raw.get("bottom_horizontal_bar") if isinstance(raw.get("bottom_horizontal_bar"), Mapping) else {}
    top["length_mm"] = _optional_positive_mm(raw_top.get("length_mm"))
    top["dimension_status"] = "MANUAL_CONFIRMATION_REQUIRED"
    bottom["length_mm"] = _optional_positive_mm(raw_bottom.get("length_mm"))
    bottom["dimension_status"] = "MANUAL_CONFIRMATION_REQUIRED"

    material_code = str(raw.get("material_code") or spec["material_code"]).strip()
    profile_code = str(raw.get("main_profile_code") or spec["main_profile_code"]).strip()
    blockers: list[str] = []
    if not get_material(material_code):
        blockers.append("fixing_material_invalid")
    if not get_profile(profile_code):
        blockers.append("fixing_main_profile_invalid")
    elif material_code not in (get_profile(profile_code) or {}).get("compatible_material_codes", []):
        blockers.append("fixing_material_profile_incompatible")

    fastener = dict(spec["lower_fastener"])
    confirmation = "CONFIRMED_WITH_MANUAL_DIMENSIONS" if not blockers else "INCOMPLETE"
    provenance = raw.get("provenance") if isinstance(raw.get("provenance"), Mapping) else {}
    return {
        "type_code": type_code,
        "owner_label": spec.get("owner_label"),
        "material_code": material_code,
        "main_profile_code": profile_code,
        "top_angle": top,
        "bottom_horizontal_bar": bottom,
        "lower_fastener": fastener,
        "geometry_notes": list(spec.get("geometry_notes") or []),
        "confirmation_status": confirmation,
        "quantity_status": "CONFIGURED_WITH_MANUAL_DIMENSIONS",
        "blockers": blockers,
        "provenance": {
            "source": provenance.get("source") or "INTAKE_STEP_2",
            "contract_version": FIXING_CONTRACT_VERSION,
            **{k: v for k, v in provenance.items() if k != "contract_version"},
        },
    }


def build_fixing_aggregate_projection(fixing: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(fixing, Mapping) or not fixing.get("type_code"):
        return None
    return {
        "kind": "mounting_fixing_system",
        "type_code": fixing.get("type_code"),
        "material_code": fixing.get("material_code"),
        "main_profile_code": fixing.get("main_profile_code"),
        "top_angle": fixing.get("top_angle"),
        "bottom_horizontal_bar": fixing.get("bottom_horizontal_bar"),
        "lower_fastener": fixing.get("lower_fastener"),
        "quantity_status": fixing.get("quantity_status") or "CONFIGURED_WITH_MANUAL_DIMENSIONS",
        "confirmation_status": fixing.get("confirmation_status"),
        "process_intent": [
            "debitare_profil",
            "debitare_cornier",
            "sudare_cornier",
            "sudare_bara_inferioara",
            "pregatire_prindere",
        ],
        "notes": [
            "Manual cornier/bottom-bar lengths — quantity GUARDED (no invented cut lengths).",
            "Independent of commercial mounting_scope and ACP internal_frame.",
        ],
        "blockers": list(fixing.get("blockers") or []),
    }


def select_vertical_steel_bracket() -> dict[str, Any]:
    return normalize_mounting_fixing_system({"type_code": VERTICAL_STEEL_BRACKET})


def _optional_positive_mm(raw: Any) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None
