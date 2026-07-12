"""Intake V4 backing mode — operator selection vs layer-role fallback."""

from __future__ import annotations

from typing import Any, Literal

from services.intake_v4_nesting_material_precision import backing_layer_confirmed

VolumetricBackingMode = Literal["none", "forex_10_no_bevel", "forex_10_with_bevel"]
EmblemLightingMode = Literal["excluded", "area_lit", "needs_decision"]

BACKING_MODE_LABELS: dict[str, str] = {
    "forex_10_no_bevel": "Forex 10 mm fără șanfren",
    "forex_10_with_bevel": "Forex 10 mm cu șanfren",
}


def normalize_backing_mode(raw: str | None) -> VolumetricBackingMode | None:
    token = str(raw or "").strip().lower()
    if token in {"", "none", "no_backing", "fara_spate"}:
        return "forex_10_no_bevel"
    if token in {"forex_10_no_bevel", "forex_10_with_bevel"}:
        return token  # type: ignore[return-value]
    return None


def resolve_backing_mode_from_finish(finish: dict[str, Any] | None) -> VolumetricBackingMode | None:
    if not isinstance(finish, dict):
        return None
    return normalize_backing_mode(finish.get("backing_mode"))


def resolve_layer_backing_mode(
    layer: dict[str, Any] | None,
    global_finish: dict[str, Any] | None,
) -> VolumetricBackingMode:
    """Per-layer backing with narrow legacy fallback to global finish_setup."""
    if isinstance(layer, dict) and layer.get("backing_mode") is not None:
        explicit = normalize_backing_mode(layer.get("backing_mode"))
        if explicit is not None:
            return explicit
    global_mode = resolve_backing_mode_from_finish(global_finish)
    if global_mode is not None:
        return global_mode
    return "forex_10_no_bevel"


def finish_has_explicit_layer_backing_modes(finish: dict[str, Any] | None) -> bool:
    if not isinstance(finish, dict):
        return False
    for group in finish.get("letter_group_finishes") or []:
        if isinstance(group, dict) and group.get("backing_mode") is not None:
            return True
    for artwork in finish.get("artwork_finishes") or []:
        if isinstance(artwork, dict) and artwork.get("backing_mode") is not None:
            return True
    return False


def resolve_volumetric_backing_state(
    finish: dict[str, Any] | None,
    layer_role_setup: dict[str, Any] | None,
    *,
    quote_geometry: dict[str, Any] | None = None,
) -> tuple[VolumetricBackingMode, bool, bool]:
    """Return (backing_mode, backing_present, back_bevel_enabled)."""
    mode = resolve_backing_mode_from_finish(finish)
    if mode is not None:
        backing_present = mode != "none"
        explicit_bevel = finish.get("back_bevel_enabled") if isinstance(finish, dict) else None
        if backing_present and isinstance(explicit_bevel, bool):
            effective_mode: VolumetricBackingMode = (
                "forex_10_with_bevel" if explicit_bevel else "forex_10_no_bevel"
            )
            return effective_mode, True, explicit_bevel
        return mode, backing_present, mode == "forex_10_with_bevel"

    backing_confirmed = backing_layer_confirmed(layer_role_setup)
    back_bevel = False
    if isinstance(quote_geometry, dict) and quote_geometry.get("back_bevel_enabled"):
        back_bevel = True
    if not backing_confirmed:
        return "forex_10_no_bevel", True, False
    if back_bevel:
        return "forex_10_with_bevel", True, True
    return "forex_10_no_bevel", True, False


def backing_mode_operator_label(mode: VolumetricBackingMode) -> str:
    return BACKING_MODE_LABELS.get(mode, mode)


def apply_backing_state_to_geometry_patch(
    patch: dict[str, Any],
    *,
    backing_present: bool,
    back_bevel_enabled: bool,
) -> dict[str, Any]:
    out = dict(patch)
    out["backing_present"] = backing_present
    out["back_bevel_enabled"] = back_bevel_enabled if backing_present else False
    if backing_present:
        out.setdefault("backing_material", "FOREX_10MM")
        out.setdefault("backing_thickness_mm", 10.0)
    return out


BASIS_BACKING_AREA_FACE_QUOTEABLE_FALLBACK = "backing_area_fallback_from_face_quoteable_area"
BASIS_BACKING_AREA_GROSS_FACE_FALLBACK = "backing_area_fallback_from_gross_face_area"


def resolve_backing_material_area_m2(
    *,
    backing_confirmed: bool,
    backing_area_m2: float | None,
    sheet_backing_area_sqm: float | None,
    sheet_face_quoteable_area_sqm: float | None,
    face_area_gross_m2: float | None,
) -> tuple[float | None, str | None, str | None, bool]:
    """Resolve Forex backing material area when dedicated backing geometry is missing.

    Returns (quantity_m2, quantity_basis, quantity_source, used_quoteable_fallback).
    """
    if not backing_confirmed:
        return None, None, None, False

    if sheet_backing_area_sqm is not None and sheet_backing_area_sqm > 0:
        return sheet_backing_area_sqm, None, None, False
    if backing_area_m2 is not None and backing_area_m2 > 0:
        return backing_area_m2, "area_fallback", "quote_geometry|path_geometry_summary", False
    if sheet_face_quoteable_area_sqm is not None and sheet_face_quoteable_area_sqm > 0:
        return (
            sheet_face_quoteable_area_sqm,
            BASIS_BACKING_AREA_FACE_QUOTEABLE_FALLBACK,
            "sheet_nesting_face_quoteable|backing_area_missing",
            True,
        )
    if face_area_gross_m2 is not None and face_area_gross_m2 > 0:
        return (
            face_area_gross_m2,
            BASIS_BACKING_AREA_GROSS_FACE_FALLBACK,
            "face_area_gross|backing_area_missing",
            False,
        )
    return None, None, None, False
