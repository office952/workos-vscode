"""ACM template quote_input derivation and validation (no pricing)."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple


def _fold_length_mm(
    width_mm: float, height_mm: float, fold_sides: str
) -> Optional[float]:
    sides = str(fold_sides).strip().lower().replace("-", "_").replace(" ", "_")
    if sides in {"all", "toate", "toate_laturile"}:
        return 2.0 * (width_mm + height_mm)
    if sides in {"top_bottom", "sus_jos", "tb"}:
        return 2.0 * width_mm
    if sides in {"left_right", "stanga_dreapta", "lr"}:
        return 2.0 * height_mm
    return None


def derive_acm_casetted_quote_input(
    raw: Mapping[str, Any],
) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """Merge derived geometry keys; return (payload, warnings, blockers)."""
    out: Dict[str, Any] = dict(raw)
    warnings: List[str] = []
    blockers: List[str] = []

    try:
        w = float(raw["panel_width_mm"])
        h = float(raw["panel_height_mm"])
    except (KeyError, TypeError, ValueError):
        blockers.append("missing_panel_dimensions")
        return out, warnings, blockers

    if w <= 0 or h <= 0:
        blockers.append("invalid_panel_dimensions")
        return out, warnings, blockers

    out["panel_area_m2"] = round((w * h) / 1_000_000.0, 6)
    out["panel_perimeter_m"] = round(2.0 * (w + h) / 1000.0, 6)

    fold_sides = raw.get("fold_sides", "all")
    fold_mm = _fold_length_mm(w, h, str(fold_sides))
    if fold_mm is None:
        blockers.append("invalid_fold_sides")
    else:
        out["fold_length_m"] = round(fold_mm / 1000.0, 6)

    try:
        return_depth = float(raw.get("return_depth_mm", 0))
    except (TypeError, ValueError):
        return_depth = 0.0

    if return_depth > 0 and fold_mm is not None:
        out["return_strip_area_m2"] = round(
            (fold_mm / 1000.0) * (return_depth / 1000.0), 6
        )

    try:
        rear_lip = float(raw.get("rear_lip_mm", 0))
    except (TypeError, ValueError):
        rear_lip = 0.0

    if rear_lip > 0 and rear_lip < 25:
        warnings.append("rear_lip_below_minimum_25mm_two_fold")

    return out, warnings, blockers


def derive_cut_acm_quote_input(
    raw: Mapping[str, Any],
) -> Tuple[Dict[str, Any], List[str], List[str]]:
    out: Dict[str, Any] = dict(raw)
    warnings: List[str] = []
    blockers: List[str] = []

    for key in ("cut_area_m2", "cut_perimeter_m"):
        if key not in raw or raw[key] is None:
            blockers.append(f"missing_{key}")
            continue
        try:
            val = float(raw[key])
        except (TypeError, ValueError):
            blockers.append(f"invalid_{key}")
            continue
        if val <= 0:
            blockers.append(f"invalid_{key}")
        else:
            out[key] = val

    return out, warnings, blockers
