"""TPL-VOLUMETRIC-LETTERS — quote_input capture policy (warnings only, no invented pricing)."""

from __future__ import annotations

from typing import Any, Mapping

from services.mounting_scope_service import is_mounting_preparation_active
from services.volumetric_material_rate_resolver import is_volumetric_template_code

WARNING_CAPTURED_NOT_PRICED = "captured_option_not_priced"
WARNING_MOUNTING_LABOR_NOT_PRICED = "mounting_labor_not_priced"
WARNING_ACM_SEPARATE_TEMPLATE = "captured_option_requires_separate_template"
WARNING_MOUNTING_BAR_PROFILE_PRICE_MISSING = "mounting_bar_profile_price_missing"
WARNING_PRODUCTION_METADATA_MISSING = "production_metadata_missing"
WARNING_ORACAL_8500_PRICED_AS_651 = "production_metadata:oracal_8500_priced_as_oracal_651"

DEFAULT_MOUNTING_BAR_PROFILE = "30x30x1.5"
PRICED_STEEL_BAR_PROFILES = frozenset({DEFAULT_MOUNTING_BAR_PROFILE})
PRICED_ALUMINUM_BAR_PROFILES = frozenset({DEFAULT_MOUNTING_BAR_PROFILE})

FACE_FINISH_TYPES = frozenset(
    {"none", "oracal_651", "printed_vinyl", "printed_laminated_vinyl"}
)
DEFAULT_FACE_FINISH_TYPE = "none"

MOUNTING_SYSTEMS = frozenset(
    {
        "direct_wall",
        "steel_bars",
        "aluminum_bars",
        "acm_panel",
        "forex_template",
    }
)
DEFAULT_MOUNTING_SYSTEM = "direct_wall"
MOUNTING_LABOR_NOT_PRICED_SYSTEMS = frozenset({"steel_bars", "aluminum_bars"})
VOLUME_FINISH_PAINT_RAL = "paint_after_face_miter_bond"
MOUNTING_TEMPLATE_MATERIAL_TYPES = frozenset({"none", "paper", "forex"})
MAT_MOUNTING_TEMPLATE_FOREX = "MAT-SABLON-MONTAJ"
MAT_MOUNTING_TEMPLATE_PAPER = "MAT-SABLON-HARTIE"

ILLUMINATION_DISABLED_TYPES = frozenset({"none", "non_illuminated"})
ILLUMINATION_ENABLED_TYPES = frozenset({"frontlit", "backlit", "halo"})
LIGHTING_SYSTEM_ENABLED_TYPES = frozenset({"led_modules", "led_strip", "led_module"})


def normalize_mounting_bar_profile(raw: Any) -> str:
    text = str(raw or DEFAULT_MOUNTING_BAR_PROFILE).strip().lower()
    text = text.replace("×", "x").replace(" ", "")
    return text or DEFAULT_MOUNTING_BAR_PROFILE


def normalize_face_finish_type(raw: Any) -> str:
    value = str(raw or "").strip()
    if value in FACE_FINISH_TYPES:
        return value
    return DEFAULT_FACE_FINISH_TYPE


def normalize_mounting_system(raw: Any) -> str:
    value = str(raw or "").strip()
    if value == "forex_template":
        return "direct_wall"
    if value in MOUNTING_SYSTEMS:
        return value
    return DEFAULT_MOUNTING_SYSTEM


def normalize_mounting_template_enabled(
    raw: Any,
    *,
    mounting_system: Any = None,
    mounting_scope: Any = None,
    quote_input: Mapping[str, Any] | None = None,
) -> bool:
    """Default true when legacy forex_template or unset — preserves baseline sablon cost."""
    ctx = quote_input or {}
    if not is_mounting_preparation_active(
        ctx,
        mounting_scope=mounting_scope if mounting_scope is not None else ctx.get("mounting_scope"),
    ):
        return False
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


def normalize_mounting_template_material_type(qi: Mapping[str, Any]) -> str:
    """Resolve template material semantics: none | paper | forex.

    Legacy: mounting_template_enabled=true without material_type → forex.
    Explicit none or disabled template → none.
    """
    raw = qi.get("mounting_template_material_type")
    if raw is not None:
        value = str(raw).strip().lower()
        if value in MOUNTING_TEMPLATE_MATERIAL_TYPES:
            return value
    if not normalize_mounting_template_enabled(
        qi.get("mounting_template_enabled"),
        mounting_system=qi.get("mounting_system"),
        mounting_scope=qi.get("mounting_scope"),
        quote_input=qi,
    ):
        return "none"
    return "forex"


def resolve_mounting_template_material_code(qi: Mapping[str, Any]) -> str | None:
    """Map quote_input to inventory material code; None when no template material."""
    material_type = normalize_mounting_template_material_type(qi)
    if material_type == "paper":
        return MAT_MOUNTING_TEMPLATE_PAPER
    if material_type == "forex":
        return MAT_MOUNTING_TEMPLATE_FOREX
    return None


def _normalize_illumination_enum(raw: Any) -> str:
    return str(raw or "").strip().lower()


def is_illumination_enabled(qi: Mapping[str, Any]) -> bool:
    """True when LED/electrical materials and operations should be priced.

    Conservative rule: explicit ``none`` / ``non_illuminated`` on either
    ``illumination_type`` or ``lighting_system_type`` disables illumination.
    Legacy quotes with both fields absent remain enabled (pre-gate behaviour).
    """
    illum = _normalize_illumination_enum(qi.get("illumination_type"))
    lighting = _normalize_illumination_enum(qi.get("lighting_system_type"))

    if illum in ILLUMINATION_DISABLED_TYPES:
        return False
    if lighting == "none":
        return False

    if illum in ILLUMINATION_ENABLED_TYPES:
        return True
    if lighting in LIGHTING_SYSTEM_ENABLED_TYPES:
        return True

    if not illum and not lighting:
        return True

    if illum and illum not in ILLUMINATION_ENABLED_TYPES:
        return False
    if lighting and lighting not in LIGHTING_SYSTEM_ENABLED_TYPES:
        return False

    return True


def _truthy_bool(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return False
    if isinstance(raw, (int, float)):
        return raw != 0
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def is_backing_present_for_costing(qi: Mapping[str, Any] | None) -> bool:
    """Forex backing material and back_cut apply only when backing is confirmed present.

    Intake V4 sets ``backing_present`` explicitly (false when no backing layer).
    Legacy V2/V3 quotes without the key keep historical behaviour (backing assumed).
    """
    data = qi or {}
    if "backing_present" in data:
        return _truthy_bool(data.get("backing_present"))
    material = str(data.get("backing_material") or "").strip()
    if material and material.lower() not in {"none", "null"}:
        return True
    if str(data.get("intake_source") or "").strip().lower() == "intake_v4":
        return False
    return True


def is_cant_ral_paint_enabled(
    qi: Mapping[str, Any],
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> bool:
    """RAL / paint tubes apply only when cant paint finish is explicitly selected."""
    volume_finish = str(qi.get("volume_finish") or "").strip()
    if volume_finish:
        return volume_finish == VOLUME_FINISH_PAINT_RAL
    if product_spec is not None:
        spec_finish = str(product_spec.get("volume_finish") or "").strip()
        if spec_finish:
            return spec_finish == VOLUME_FINISH_PAINT_RAL
    return False


def _mounting_bar_material_kind(mounting_system: str) -> str | None:
    if mounting_system == "steel_bars":
        return "steel"
    if mounting_system == "aluminum_bars":
        return "aluminum"
    return None


def _collect_production_metadata_warnings(
    qi: Mapping[str, Any],
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> list[str]:
    """Soft production-metadata warnings — do not block simulate or invent costs."""
    warnings: list[str] = []
    face = normalize_face_finish_type(qi.get("face_finish_type"))
    if face == "oracal_651":
        if not str(qi.get("face_vinyl_color_code") or "").strip():
            warnings.append(f"{WARNING_PRODUCTION_METADATA_MISSING}:face_vinyl_color_code")
        roll = qi.get("face_vinyl_roll_width_mm")
        if roll not in (1000, 1260):
            warnings.append(f"{WARNING_PRODUCTION_METADATA_MISSING}:face_vinyl_roll_width_mm")
    if face in {"printed_vinyl", "printed_laminated_vinyl"}:
        if not str(qi.get("face_vinyl_color_code") or "").strip():
            warnings.append(f"{WARNING_PRODUCTION_METADATA_MISSING}:face_vinyl_color_code")
    try:
        tubes = float(qi.get("paint_tube_count") or 0)
    except (TypeError, ValueError):
        tubes = 0
    if (
        is_cant_ral_paint_enabled(qi, product_spec=product_spec)
        and tubes > 0
        and not str(qi.get("paint_ral_code") or "").strip()
    ):
        warnings.append(f"{WARNING_PRODUCTION_METADATA_MISSING}:paint_ral_code")
    subtype = str(qi.get("face_finish_subtype") or "").strip()
    if subtype == "oracal_8500":
        warnings.append(WARNING_ORACAL_8500_PRICED_AS_651)
    return warnings


def collect_volumetric_captured_unpriced_warnings(
    template_code: str | None,
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> list[str]:
    """Emit capture-only warnings for options not yet priced in CostEngine."""
    if not is_volumetric_template_code(template_code):
        return []

    qi = quote_input or {}
    warnings: list[str] = list(
        _collect_production_metadata_warnings(qi, product_spec=product_spec)
    )

    mount = normalize_mounting_system(qi.get("mounting_system"))
    if mount == "acm_panel":
        warnings.append(f"{WARNING_ACM_SEPARATE_TEMPLATE}:mounting_system={mount}")

    bar_kind = _mounting_bar_material_kind(mount)
    if bar_kind is not None:
        profile = normalize_mounting_bar_profile(qi.get("mounting_bar_profile"))
        priced = (
            PRICED_STEEL_BAR_PROFILES
            if bar_kind == "steel"
            else PRICED_ALUMINUM_BAR_PROFILES
        )
        if profile not in priced:
            warnings.append(
                f"{WARNING_MOUNTING_BAR_PROFILE_PRICE_MISSING}:{bar_kind}:{profile}"
            )
        else:
            warnings.append(
                f"{WARNING_MOUNTING_LABOR_NOT_PRICED}:mounting_system={mount}"
            )

    return warnings
