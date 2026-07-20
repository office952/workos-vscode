"""ACM template quote_input derivation and validation (no pricing)."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

ACM_BOXED_MOUNTING_STANDALONE_REQUIRED_KEYS: tuple[str, ...] = (
    "panel_width_mm",
    "panel_height_mm",
    "acm_thickness_mm",
    "return_depth_mm",
    "fold_sides",
)


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


def is_acm_boxed_mounting_standalone_root_template(template_code: str | None) -> bool:
    from services.mounting_solution_service import ACM_BOXED_MOUNTING_TEMPLATE_CODE
    from services.template_architecture_scope import normalize_template_code

    return normalize_template_code(template_code) == normalize_template_code(
        ACM_BOXED_MOUNTING_TEMPLATE_CODE
    )


def _standalone_root_configuration(payload: Mapping[str, Any]) -> Dict[str, Any] | None:
    from services.mounting_solution_service import (
        ACM_BOXED_MOUNTING_TEMPLATE_CODE,
        normalize_acm_mounting_configuration,
    )

    if not is_acm_boxed_mounting_standalone_root_template(
        payload.get("template_code") or payload.get("product_id")
    ):
        if payload.get("panel_width_mm") is None or payload.get("panel_height_mm") is None:
            return None
        if payload.get("finish_setup") or payload.get("mounting_solution"):
            return None
        return normalize_acm_mounting_configuration(payload)

    config = normalize_acm_mounting_configuration(payload)
    client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
    if config.get("panel_width_mm") in (None, 0) and client.get("width_mm") is not None:
        config["panel_width_mm"] = client["width_mm"]
    if config.get("panel_height_mm") in (None, 0) and client.get("height_mm") is not None:
        config["panel_height_mm"] = client["height_mm"]
    if config.get("panel_width_mm") in (None, 0) or config.get("panel_height_mm") in (None, 0):
        return None
    out = dict(config)
    out.setdefault("template_code", ACM_BOXED_MOUNTING_TEMPLATE_CODE)
    return out


def merge_acm_boxed_mounting_derived_fields(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Merge derived ACM boxed mounting geometry into a quote/CPP/EIC payload.

    Injects assembly_* and applies commercial geometry adapter (Slice C):
    face area from assembly; cut/fold from sum of panel perimeters.
    Never remaps panel_width_mm/panel_height_mm to assembly dims.
    """
    from services.acm_commercial_geometry import apply_acm_commercial_geometry
    from services.mounting_solution_service import (
        ACM_BOXED_MOUNTING_TEMPLATE_CODE,
        normalize_acm_mounting_configuration,
        read_mounting_solution,
    )

    out: Dict[str, Any] = dict(payload)
    standalone_config = _standalone_root_configuration(payload)
    if standalone_config is not None:
        derived, _warnings, _blockers = derive_acm_casetted_quote_input(standalone_config)
        out.update(derived)
        out.setdefault("template_code", ACM_BOXED_MOUNTING_TEMPLATE_CODE)
        apply_acm_commercial_geometry(out)
        return out

    finish = out.get("finish_setup") if isinstance(out.get("finish_setup"), dict) else {}
    solution = read_mounting_solution(finish) or read_mounting_solution(out)
    if not solution or solution.get("template_code") != ACM_BOXED_MOUNTING_TEMPLATE_CODE:
        apply_acm_commercial_geometry(out)
        return out

    config = normalize_acm_mounting_configuration(solution.get("configuration"))
    client = out.get("client") if isinstance(out.get("client"), dict) else {}
    if config.get("panel_width_mm") in (None, 0) and client.get("width_mm") is not None:
        config["panel_width_mm"] = client["width_mm"]
    if config.get("panel_height_mm") in (None, 0) and client.get("height_mm") is not None:
        config["panel_height_mm"] = client["height_mm"]
    derived, _warnings, _blockers = derive_acm_casetted_quote_input(config)
    out.update(derived)
    # Preserve envelope/primary contour dims — do not overwrite with assembly.
    apply_acm_commercial_geometry(out)
    return out


def is_acm_boxed_mounting_payload(payload: Mapping[str, Any] | None) -> bool:
    from services.mounting_solution_service import (
        ACM_BOXED_MOUNTING_TEMPLATE_CODE,
        read_mounting_solution,
    )

    if not isinstance(payload, Mapping):
        return False
    if _standalone_root_configuration(payload) is not None:
        return True
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    solution = read_mounting_solution(finish) or read_mounting_solution(payload)
    return bool(
        solution and str(solution.get("template_code") or "").strip() == ACM_BOXED_MOUNTING_TEMPLATE_CODE
    )
