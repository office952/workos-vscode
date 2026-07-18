"""ACP internal frame domain rules — OWNER_CONFIRMED formulas (no UI authority)."""

from __future__ import annotations

import math
from typing import Any, Literal

from data.product_system.structural_resource_options_v1 import (
    CROSSBAR_RULE_CODE,
    CROSSBAR_SPACING_ALUMINIUM_MM,
    CROSSBAR_SPACING_STEEL_MM,
    FRAME_DIMENSION_RULE_CODE,
    MAT_STRUCT_ALUMINIUM,
    MAT_STRUCT_STEEL,
    REGISTRY_VERSION,
    TOTAL_FIT_ALLOWANCE_MM,
    get_accepted_options,
    get_material,
    get_profile,
    material_profile_compatible,
)

CrossbarOrientation = Literal["VERTICAL", "HORIZONTAL"]

ACM_BOXED_TEMPLATE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"


def compute_frame_outer_dimensions(
    *,
    panel_outer_width_mm: float,
    panel_outer_height_mm: float,
    panel_material_thickness_mm: float,
    total_fit_allowance_mm: float = TOTAL_FIT_ALLOWANCE_MM,
) -> dict[str, Any]:
    """frame = panel_outer - 2*thickness - fit_allowance (OWNER_CONFIRMED)."""
    blockers: list[str] = []
    w = float(panel_outer_width_mm)
    h = float(panel_outer_height_mm)
    t = float(panel_material_thickness_mm)
    fit = float(total_fit_allowance_mm)
    if not (w > 0 and h > 0):
        blockers.append("panel_outer_dimensions_invalid")
    if not (t > 0):
        blockers.append("panel_material_thickness_invalid")
    if fit < 0:
        blockers.append("fit_allowance_invalid")
    frame_w = w - (2.0 * t) - fit
    frame_h = h - (2.0 * t) - fit
    if frame_w <= 0 or frame_h <= 0:
        blockers.append("frame_outer_dimensions_non_positive")
    return {
        "rule_code": FRAME_DIMENSION_RULE_CODE,
        "panel_outer_width_mm": w,
        "panel_outer_height_mm": h,
        "panel_material_thickness_mm": t,
        "total_fit_allowance_mm": fit,
        "frame_outer_width_mm": frame_w,
        "frame_outer_height_mm": frame_h,
        "blockers": blockers,
        "valid": len(blockers) == 0,
    }


def max_crossbar_spacing_mm(material_code: str) -> float | None:
    material = get_material(material_code)
    if not material:
        return None
    code = material["code"]
    if code == MAT_STRUCT_STEEL:
        return CROSSBAR_SPACING_STEEL_MM
    if code == MAT_STRUCT_ALUMINIUM:
        return CROSSBAR_SPACING_ALUMINIUM_MM
    return None


def suggest_crossbar_count(*, length_mm: float, max_spacing_mm: float) -> dict[str, Any]:
    """Spans along L with max gap S: ceil(L/S) spans → max(0, spans-1) internal bars.

    L is the clear axis perpendicular to bar orientation (V1 suggestion semantics).
    Profile thickness / joints not subtracted → BOM quantity remains GUARDED.
    """
    L = float(length_mm)
    S = float(max_spacing_mm)
    if not (L > 0 and S > 0):
        return {
            "suggested_crossbar_count": 0,
            "number_of_spans": 0,
            "result_spacing_mm": None,
            "valid": False,
            "blockers": ["crossbar_inputs_invalid"],
        }
    spans = int(math.ceil(L / S))
    count = max(0, spans - 1)
    result_spacing = L / spans if spans > 0 else None
    return {
        "suggested_crossbar_count": count,
        "number_of_spans": spans,
        "result_spacing_mm": result_spacing,
        "max_spacing_mm": S,
        "length_mm": L,
        "valid": True,
        "blockers": [],
        "authority": "SUGGESTION_ONLY",
    }


def suggest_crossbars_for_orientation(
    *,
    material_code: str,
    frame_outer_width_mm: float,
    frame_outer_height_mm: float,
    orientation: CrossbarOrientation,
) -> dict[str, Any]:
    spacing = max_crossbar_spacing_mm(material_code)
    if spacing is None:
        return {
            "crossbar_rule_code": CROSSBAR_RULE_CODE,
            "orientation": orientation,
            "valid": False,
            "blockers": ["material_spacing_unknown"],
        }
    length = frame_outer_width_mm if orientation == "VERTICAL" else frame_outer_height_mm
    member_length = frame_outer_height_mm if orientation == "VERTICAL" else frame_outer_width_mm
    suggestion = suggest_crossbar_count(length_mm=length, max_spacing_mm=spacing)
    return {
        "crossbar_rule_code": CROSSBAR_RULE_CODE,
        "orientation": orientation,
        "max_crossbar_spacing_mm": spacing,
        "axis_length_mm": length,
        "crossbar_member_length_mm": member_length,
        **suggestion,
    }


def empty_internal_frame_config() -> dict[str, Any]:
    return {
        "enabled": False,
        "material_code": None,
        "profile_code": None,
        "panel_outer_width_mm": None,
        "panel_outer_height_mm": None,
        "panel_material_thickness_mm": None,
        "total_fit_allowance_mm": TOTAL_FIT_ALLOWANCE_MM,
        "frame_outer_width_mm": None,
        "frame_outer_height_mm": None,
        "crossbar_rule_code": CROSSBAR_RULE_CODE,
        "max_crossbar_spacing_mm": None,
        "crossbar_orientation": None,
        "suggested_crossbar_count": None,
        "confirmed_crossbar_count": None,
        "override_reason": None,
        "structural_review_required": False,
        "confirmation_status": "NOT_APPLICABLE",
        "quantity_status": "NOT_APPLICABLE",
        "blockers": [],
        "provenance": {"resource_registry_version": REGISTRY_VERSION},
    }


def normalize_internal_frame_config(
    raw: Any,
    *,
    panel_width_mm: float | None = None,
    panel_height_mm: float | None = None,
    panel_thickness_mm: float | None = None,
    fold_count: int | None = None,
) -> dict[str, Any]:
    """Normalize nested internal_frame; inactive → strict zero leakage."""
    base = empty_internal_frame_config()
    if not isinstance(raw, dict):
        enabled = False
    else:
        enabled = bool(raw.get("enabled"))
    if not enabled:
        return base

    cfg = dict(base)
    cfg["enabled"] = True
    cfg["confirmation_status"] = "INCOMPLETE"
    cfg["quantity_status"] = "GUARDED"
    material_code = str(raw.get("material_code") or "").strip() or None
    profile_code = str(raw.get("profile_code") or "").strip() or None
    cfg["material_code"] = material_code
    cfg["profile_code"] = profile_code

    w = _num(raw.get("panel_outer_width_mm"), panel_width_mm)
    h = _num(raw.get("panel_outer_height_mm"), panel_height_mm)
    t = _num(raw.get("panel_material_thickness_mm"), panel_thickness_mm)
    if t is None:
        t = 3.0
    cfg["panel_outer_width_mm"] = w
    cfg["panel_outer_height_mm"] = h
    cfg["panel_material_thickness_mm"] = t
    cfg["total_fit_allowance_mm"] = TOTAL_FIT_ALLOWANCE_MM
    # Fold count must not affect frame size (OWNER_CONFIRMED).
    cfg["fold_count_ignored_for_frame"] = fold_count

    blockers: list[str] = []
    accepted = get_accepted_options(ACM_BOXED_TEMPLATE) or {}
    accepted_materials = set(accepted.get("accepted_material_codes") or [])
    accepted_profiles = list(accepted.get("accepted_profile_codes") or [])

    if not material_code:
        blockers.append("internal_frame_material_missing")
    elif material_code not in accepted_materials or not get_material(material_code):
        blockers.append("internal_frame_material_invalid")

    if not accepted_profiles:
        blockers.append("internal_frame_profile_catalog_empty")
    elif not profile_code:
        blockers.append("internal_frame_profile_missing")
    elif profile_code not in accepted_profiles or not get_profile(profile_code):
        blockers.append("internal_frame_profile_invalid")
    elif material_code and not material_profile_compatible(material_code, profile_code):
        blockers.append("internal_frame_material_profile_incompatible")

    if w is None or h is None or t is None:
        blockers.append("internal_frame_panel_dimensions_missing")
    else:
        dims = compute_frame_outer_dimensions(
            panel_outer_width_mm=w,
            panel_outer_height_mm=h,
            panel_material_thickness_mm=t,
        )
        cfg["frame_outer_width_mm"] = dims["frame_outer_width_mm"]
        cfg["frame_outer_height_mm"] = dims["frame_outer_height_mm"]
        if not dims["valid"]:
            blockers.extend(dims["blockers"])

    orientation = str(raw.get("crossbar_orientation") or "").strip().upper() or None
    if orientation not in {"VERTICAL", "HORIZONTAL", None}:
        blockers.append("internal_frame_crossbar_orientation_invalid")
        orientation = None
    cfg["crossbar_orientation"] = orientation

    if material_code and cfg.get("frame_outer_width_mm") and orientation:
        suggestion = suggest_crossbars_for_orientation(
            material_code=material_code,
            frame_outer_width_mm=float(cfg["frame_outer_width_mm"]),
            frame_outer_height_mm=float(cfg["frame_outer_height_mm"]),
            orientation=orientation,  # type: ignore[arg-type]
        )
        cfg["max_crossbar_spacing_mm"] = suggestion.get("max_crossbar_spacing_mm")
        cfg["suggested_crossbar_count"] = suggestion.get("suggested_crossbar_count")
        cfg["crossbar_member_length_mm"] = suggestion.get("crossbar_member_length_mm")
        cfg["result_spacing_mm"] = suggestion.get("result_spacing_mm")
    elif material_code:
        cfg["max_crossbar_spacing_mm"] = max_crossbar_spacing_mm(material_code)

    confirmed = raw.get("confirmed_crossbar_count")
    if confirmed is not None:
        try:
            cfg["confirmed_crossbar_count"] = int(confirmed)
        except (TypeError, ValueError):
            blockers.append("internal_frame_crossbar_count_invalid")
    override = raw.get("override_reason")
    cfg["override_reason"] = str(override).strip() if override else None
    if (
        cfg.get("confirmed_crossbar_count") is not None
        and cfg.get("suggested_crossbar_count") is not None
        and int(cfg["confirmed_crossbar_count"]) != int(cfg["suggested_crossbar_count"])
        and not cfg["override_reason"]
    ):
        blockers.append("internal_frame_crossbar_override_reason_required")

    if orientation is None:
        blockers.append("internal_frame_crossbar_unconfirmed")
    elif cfg.get("confirmed_crossbar_count") is None:
        blockers.append("internal_frame_crossbar_unconfirmed")

    cfg["structural_review_required"] = bool(raw.get("structural_review_required"))
    cfg["blockers"] = blockers
    if not blockers:
        cfg["confirmation_status"] = "CONFIRMED"
    else:
        cfg["confirmation_status"] = "INCOMPLETE"

    provenance = raw.get("provenance") if isinstance(raw.get("provenance"), dict) else {}
    cfg["provenance"] = {
        "source": provenance.get("source") or "INTAKE_STEP_2",
        "resource_registry_version": REGISTRY_VERSION,
        **{k: v for k, v in provenance.items() if k not in {"resource_registry_version"}},
    }
    return cfg


def build_aggregate_frame_projection(internal_frame: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(internal_frame, dict) or not internal_frame.get("enabled"):
        return None
    return {
        "kind": "acp_internal_frame",
        "material_code": internal_frame.get("material_code"),
        "profile_code": internal_frame.get("profile_code"),
        "frame_outer_width_mm": internal_frame.get("frame_outer_width_mm"),
        "frame_outer_height_mm": internal_frame.get("frame_outer_height_mm"),
        "crossbar_orientation": internal_frame.get("crossbar_orientation"),
        "confirmed_crossbar_count": internal_frame.get("confirmed_crossbar_count"),
        "suggested_crossbar_count": internal_frame.get("suggested_crossbar_count"),
        "quantity_status": "GUARDED",
        "process_intent": [
            "debitare_profil",
            "asamblare_cadru",
            "fixare_cadru_in_panou",
        ],
        "confirmation_status": internal_frame.get("confirmation_status"),
        "blockers": list(internal_frame.get("blockers") or []),
        "notes": [
            "Perimeter/crossbar cut lengths GUARDED until joint/waste owner rules.",
            "No CPP / task materialization in this projection.",
        ],
    }


def _num(*candidates: Any) -> float | None:
    for value in candidates:
        if value is None or value == "":
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            return number
    return None
