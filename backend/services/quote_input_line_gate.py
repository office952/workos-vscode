"""Generic quote_input gating for formula-based template lines (skip, no invented cost)."""

from __future__ import annotations

from typing import Any, Mapping

from services.volumetric_quote_input_policy import (
    is_backing_present_for_costing,
    is_cant_ral_paint_enabled,
    is_illumination_enabled,
    normalize_mounting_bar_profile,
    normalize_mounting_template_material_type,
)


def _truthy(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return False
    if isinstance(raw, (int, float)):
        return raw != 0
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_mounting_system(raw: Any) -> str:
    value = str(raw or "").strip()
    if value == "forex_template":
        return "direct_wall"
    return value


def _face_finish(raw: Any) -> str:
    value = str(raw or "none").strip()
    return value if value else "none"


def _mounting_template_enabled(raw: Any, *, mounting_system: Any = None) -> bool:
    """Default true when unset — preserves baseline sablon cost; legacy forex_template → true."""
    if raw is not None:
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, (int, float)):
            return raw != 0
        text = str(raw).strip().lower()
        if text in {"false", "0", "no", "off"}:
            return False
        if text in {"true", "1", "yes", "on"}:
            return True
    if str(mounting_system or "").strip() == "forex_template":
        return True
    return True


def _volume_finish(raw: Any) -> str:
    return str(raw or "").strip()


def should_skip_quote_input_gated_line(
    entry: Mapping[str, Any],
    quote_input: Mapping[str, Any] | None,
) -> str | None:
    """Return skip reason when line is inactive for current quote_input; else None."""
    params = entry.get("formula_params") or {}
    if not isinstance(params, dict):
        return None

    qi = quote_input or {}

    # Legacy template flag — MAT-VOPSEA-RAL uses conditional=paint_finish.
    if params.get("conditional") == "paint_finish":
        if not is_cant_ral_paint_enabled(qi):
            return "gate:paint_finish_inactive"

    if params.get("conditional") == "illumination_enabled":
        if not is_illumination_enabled(qi):
            return "gate:illumination_disabled"

    gate = params.get("gate")
    if not isinstance(gate, dict) or not gate:
        return None
    mount = _normalize_mounting_system(qi.get("mounting_system"))
    face = _face_finish(qi.get("face_finish_type"))

    if "mounting_template_enabled" in gate:
        expected = bool(gate["mounting_template_enabled"])
        actual = _mounting_template_enabled(
            qi.get("mounting_template_enabled"),
            mounting_system=qi.get("mounting_system"),
        )
        if actual != expected:
            return "gate:mounting_template_enabled"

    if "mounting_template_material_type" in gate:
        expected = str(gate["mounting_template_material_type"]).strip().lower()
        actual = normalize_mounting_template_material_type(qi)
        if actual != expected:
            return "gate:mounting_template_material_type"

    if "face_finish_type" in gate:
        expected = gate["face_finish_type"]
        if face != str(expected):
            return "gate:face_finish_type"

    if "face_finish_type_in" in gate:
        allowed = gate["face_finish_type_in"]
        if not isinstance(allowed, list) or face not in {str(v) for v in allowed}:
            return "gate:face_finish_type_in"

    if "face_finish_type_not" in gate:
        blocked = str(gate["face_finish_type_not"])
        if face == blocked:
            return "gate:face_finish_type_not"

    if "mounting_system" in gate:
        if mount != str(gate["mounting_system"]):
            return "gate:mounting_system"

    if "mounting_system_in" in gate:
        allowed = gate["mounting_system_in"]
        if not isinstance(allowed, list) or mount not in {str(v) for v in allowed}:
            return "gate:mounting_system_in"

    if "mounting_bar_profile_in" in gate:
        allowed_raw = gate["mounting_bar_profile_in"]
        if not isinstance(allowed_raw, list):
            return "gate:mounting_bar_profile_in"
        allowed = {normalize_mounting_bar_profile(v) for v in allowed_raw}
        profile = normalize_mounting_bar_profile(qi.get("mounting_bar_profile"))
        if profile not in allowed:
            return "gate:mounting_bar_profile_in"

    if "bar_material" in gate:
        expected = str(gate["bar_material"]).strip().lower()
        actual = str(qi.get("bar_material") or "").strip().lower()
        if actual != expected:
            return "gate:bar_material"

    if "bar_material_in" in gate:
        allowed_raw = gate["bar_material_in"]
        if not isinstance(allowed_raw, list):
            return "gate:bar_material_in"
        allowed = {str(v).strip().lower() for v in allowed_raw}
        actual = str(qi.get("bar_material") or "").strip().lower()
        if actual not in allowed:
            return "gate:bar_material_in"

    if "volume_finish" in gate:
        expected = str(gate["volume_finish"]).strip()
        actual = _volume_finish(qi.get("volume_finish"))
        if actual != expected:
            return "gate:volume_finish"

    if "volume_finish_not" in gate:
        blocked = str(gate["volume_finish_not"]).strip()
        if _volume_finish(qi.get("volume_finish")) == blocked:
            return "gate:volume_finish_not"

    if gate.get("paint_finish") is True:
        if not is_cant_ral_paint_enabled(qi):
            return "gate:paint_finish_inactive"

    if gate.get("illumination_enabled") is True:
        if not is_illumination_enabled(qi):
            return "gate:illumination_disabled"

    if gate.get("backing_present") is True:
        if not is_backing_present_for_costing(qi):
            return "gate:backing_absent"

    return None
