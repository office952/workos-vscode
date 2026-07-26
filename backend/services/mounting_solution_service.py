"""Product System mounting solution reference — Intake V6 composition contract."""

from __future__ import annotations

from typing import Any, Mapping

from schemas.intake_v4 import IntakeV4MountingSolution
from services.acm_bond_material_rate_resolver import BOXED_MOUNTING_SUPPORTED_THICKNESS_MM
from services.acm_quote_input_helpers import derive_acm_casetted_quote_input
from services.mounting_scope_service import is_mounting_preparation_active, normalize_mounting_scope

METAL_PREMOUNT_TEMPLATE_CODE = "TPL-METAL-PREMOUNT-STRUCTURE_v1"
ACM_BOXED_MOUNTING_TEMPLATE_CODE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES = frozenset(
    {METAL_PREMOUNT_TEMPLATE_CODE, ACM_BOXED_MOUNTING_TEMPLATE_CODE}
)
INSTALLATION_TEMPLATE_KIND = "installation_template"
PRODUCT_SYSTEM_TEMPLATE_KIND = "product_system_template"
BAR_MOUNTING_LEGACY = frozenset({"steel_bars", "aluminum_bars"})
ACM_PANEL_LEGACY = "acm_panel"

DEFAULT_METAL_MOUNTING_CONFIGURATION: dict[str, Any] = {
    "bar_count": 2,
    "mounting_bar_profile": "30x30x1.5",
    "bar_material": "steel",
}

DEFAULT_ACM_MOUNTING_CONFIGURATION: dict[str, Any] = {
    "panel_width_mm": 1000,
    "panel_height_mm": 600,
    "acm_thickness_mm": 3,
    "return_depth_mm": 60,
    "rear_lip_mm": 25,
    "fold_sides": "all",
    "v_groove_angle_deg": 135,
    "frame_clearance_mm": 0,
}


def _coerce_configuration(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    return dict(raw)


def is_installation_template_solution(solution: Mapping[str, Any] | None) -> bool:
    if not isinstance(solution, Mapping):
        return False
    return str(solution.get("kind") or "").strip() == INSTALLATION_TEMPLATE_KIND


def is_mounting_template_fields_complete(setup: Mapping[str, Any] | None) -> bool:
    """Installation-template sentinel is readiness-complete only with template fields filled."""
    if not isinstance(setup, Mapping):
        return False
    if setup.get("mounting_template_enabled") is not True:
        return False
    try:
        area = float(setup.get("mounting_template_area_m2"))
    except (TypeError, ValueError):
        return False
    if area <= 0:
        return False
    material = str(setup.get("mounting_template_material_type") or "").strip().lower()
    return material in {"forex", "paper"}


def read_mounting_solution(setup: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(setup, Mapping):
        return None
    raw = setup.get("mounting_solution")
    if not isinstance(raw, dict):
        return None
    kind = str(raw.get("kind") or "").strip()
    if kind == INSTALLATION_TEMPLATE_KIND:
        return {
            "kind": INSTALLATION_TEMPLATE_KIND,
            "template_code": None,
            "configuration": _coerce_configuration(raw.get("configuration")),
        }
    template_code = str(raw.get("template_code") or "").strip()
    if not template_code:
        return None
    return {
        "kind": PRODUCT_SYSTEM_TEMPLATE_KIND,
        "template_code": template_code,
        "configuration": _coerce_configuration(raw.get("configuration")),
    }


def normalize_acm_mounting_configuration(config: Mapping[str, Any] | None) -> dict[str, Any]:
    merged = dict(DEFAULT_ACM_MOUNTING_CONFIGURATION)
    if isinstance(config, Mapping):
        merged.update(_coerce_configuration(config))
    for key in ("panel_width_mm", "panel_height_mm", "return_depth_mm", "rear_lip_mm", "frame_clearance_mm"):
        try:
            merged[key] = float(merged.get(key) or DEFAULT_ACM_MOUNTING_CONFIGURATION[key])
        except (TypeError, ValueError):
            merged[key] = DEFAULT_ACM_MOUNTING_CONFIGURATION[key]
    try:
        thickness = int(round(float(merged.get("acm_thickness_mm") or 3)))
    except (TypeError, ValueError):
        thickness = 3
    if thickness in BOXED_MOUNTING_SUPPORTED_THICKNESS_MM:
        merged["acm_thickness_mm"] = thickness
    else:
        # Preserve unsupported thickness (e.g. 4 mm) — boxed resolver blocks explicitly.
        merged["acm_thickness_mm"] = thickness
    fold_sides = str(merged.get("fold_sides") or "all").strip().lower()
    if fold_sides not in {"all", "top_bottom", "left_right"}:
        fold_sides = "all"
    merged["fold_sides"] = fold_sides
    try:
        merged["v_groove_angle_deg"] = float(merged.get("v_groove_angle_deg") or 135)
    except (TypeError, ValueError):
        merged["v_groove_angle_deg"] = 135
    # Optional SVG panel confirmation fields (typed; no commercial authority).
    for key in (
        "fold_count",
        "finished_depth_mm",
        "svg_support_element_id",
        "geometry_hash",
        "contour_id",
        "panel_area_mm2",
        "panel_perimeter_mm",
        "internal_frame_enabled",
    ):
        if key in merged:
            continue
        if isinstance(config, Mapping) and key in config:
            merged[key] = config[key]
    if "fold_count" in merged:
        try:
            fc = int(merged["fold_count"])
            merged["fold_count"] = 2 if fc == 2 else 1 if fc == 1 else merged["fold_count"]
        except (TypeError, ValueError):
            pass
    if "internal_frame_enabled" in merged:
        merged["internal_frame_enabled"] = bool(merged["internal_frame_enabled"])

    # Nested typed internal_frame (Shared RO) — wins over bare boolean.
    from services.acp_internal_frame_domain import normalize_internal_frame_config

    raw_frame = merged.get("internal_frame")
    enabled_flag = bool(merged.get("internal_frame_enabled"))
    if isinstance(raw_frame, Mapping):
        frame_in = dict(raw_frame)
        if "enabled" not in frame_in:
            frame_in["enabled"] = enabled_flag
    elif enabled_flag:
        frame_in = {"enabled": True}
    else:
        frame_in = {"enabled": False}
    fold = merged.get("fold_count")
    try:
        fold_i = int(fold) if fold is not None else None
    except (TypeError, ValueError):
        fold_i = None
    normalized_frame = normalize_internal_frame_config(
        frame_in,
        panel_width_mm=merged.get("panel_width_mm"),
        panel_height_mm=merged.get("panel_height_mm"),
        panel_thickness_mm=merged.get("acm_thickness_mm"),
        fold_count=fold_i,
    )
    merged["internal_frame"] = normalized_frame
    merged["internal_frame_enabled"] = bool(normalized_frame.get("enabled"))
    # Legacy frame_clearance_mm is not fit-allowance authority; keep numeric coalesce only.
    return merged


def normalize_solution_configuration(
    template_code: str,
    config: Mapping[str, Any] | None,
) -> dict[str, Any]:
    code = str(template_code or "").strip()
    if code == METAL_PREMOUNT_TEMPLATE_CODE:
        return normalize_metal_mounting_configuration(config)
    if code == ACM_BOXED_MOUNTING_TEMPLATE_CODE:
        return normalize_acm_mounting_configuration(config)
    return _coerce_configuration(config)


def hydrate_mounting_solution_from_legacy(setup: Mapping[str, Any] | None) -> dict[str, Any] | None:
    existing = read_mounting_solution(setup)
    if existing:
        return existing
    if not isinstance(setup, Mapping):
        return None
    mounting_system = str(setup.get("mounting_system") or "").strip()
    if mounting_system == ACM_PANEL_LEGACY:
        return {
            "kind": PRODUCT_SYSTEM_TEMPLATE_KIND,
            "template_code": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
            "configuration": normalize_acm_mounting_configuration({}),
        }
    if mounting_system not in BAR_MOUNTING_LEGACY:
        return None
    bar_material = "aluminum" if mounting_system == "aluminum_bars" else "steel"
    profile = str(setup.get("mounting_bar_profile") or DEFAULT_METAL_MOUNTING_CONFIGURATION["mounting_bar_profile"]).strip()
    return {
        "kind": PRODUCT_SYSTEM_TEMPLATE_KIND,
        "template_code": METAL_PREMOUNT_TEMPLATE_CODE,
        "configuration": {
            **DEFAULT_METAL_MOUNTING_CONFIGURATION,
            "bar_material": bar_material,
            "mounting_bar_profile": profile,
        },
    }


def resolve_effective_mounting_solution(setup: Mapping[str, Any] | None) -> dict[str, Any] | None:
    return read_mounting_solution(setup) or hydrate_mounting_solution_from_legacy(setup)


def normalize_metal_mounting_configuration(config: Mapping[str, Any] | None) -> dict[str, Any]:
    merged = dict(DEFAULT_METAL_MOUNTING_CONFIGURATION)
    if isinstance(config, Mapping):
        merged.update(_coerce_configuration(config))
    bar_material = str(merged.get("bar_material") or "steel").strip().lower()
    if bar_material not in {"steel", "aluminum"}:
        bar_material = "steel"
    merged["bar_material"] = bar_material
    profile = str(merged.get("mounting_bar_profile") or DEFAULT_METAL_MOUNTING_CONFIGURATION["mounting_bar_profile"]).strip()
    merged["mounting_bar_profile"] = profile or DEFAULT_METAL_MOUNTING_CONFIGURATION["mounting_bar_profile"]
    try:
        merged["bar_count"] = max(1, int(merged.get("bar_count") or DEFAULT_METAL_MOUNTING_CONFIGURATION["bar_count"]))
    except (TypeError, ValueError):
        merged["bar_count"] = DEFAULT_METAL_MOUNTING_CONFIGURATION["bar_count"]
    return merged


def is_acp_product_component_active(setup: Mapping[str, Any] | None) -> bool:
    """ACP boxed panel is a product component — independent of commercial mounting_scope."""
    if not isinstance(setup, Mapping):
        return False
    solution = resolve_effective_mounting_solution(setup)
    if not solution or is_installation_template_solution(solution):
        return False
    return str(solution.get("template_code") or "").strip() == ACM_BOXED_MOUNTING_TEMPLATE_CODE


def is_mounting_solution_composition_active(setup: Mapping[str, Any] | None) -> bool:
    """Product System support children in composition.

    ACP boxed panel is product truth and remains active when commercial mounting_scope=none.
    Metal Premount remains gated by commercial preparation scope.
    """
    if not isinstance(setup, Mapping):
        return False
    solution = resolve_effective_mounting_solution(setup)
    if not solution or is_installation_template_solution(solution):
        return False
    code = str(solution.get("template_code") or "").strip()
    if code not in ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES:
        return False
    if code == ACM_BOXED_MOUNTING_TEMPLATE_CODE:
        return True
    return is_mounting_preparation_active(setup)


def is_structura_suport_active(setup: Mapping[str, Any] | None) -> bool:
    return is_mounting_solution_composition_active(setup)


def legacy_mounting_system_from_solution(solution: Mapping[str, Any] | None) -> str | None:
    if not isinstance(solution, Mapping):
        return None
    if is_installation_template_solution(solution):
        return "direct_wall"
    template_code = str(solution.get("template_code") or "").strip()
    if template_code == METAL_PREMOUNT_TEMPLATE_CODE:
        config = normalize_metal_mounting_configuration(_coerce_configuration(solution.get("configuration")))
        return "aluminum_bars" if config["bar_material"] == "aluminum" else "steel_bars"
    if template_code == ACM_BOXED_MOUNTING_TEMPLATE_CODE:
        return ACM_PANEL_LEGACY
    return None


def hydrate_mounting_solution_fields(setup: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize mounting_solution and sunset legacy dual-write when canonical is present."""
    scope = normalize_mounting_scope(setup.get("mounting_scope"), setup=setup)
    updates: dict[str, Any] = {}

    solution = read_mounting_solution(setup)
    if solution is None and scope != "none":
        hydrated = hydrate_mounting_solution_from_legacy(setup)
        if hydrated:
            solution = hydrated
            updates["mounting_solution"] = IntakeV4MountingSolution.model_validate(hydrated)

    if solution and is_installation_template_solution(solution):
        updates["mounting_solution"] = IntakeV4MountingSolution.model_validate(
            {
                "kind": INSTALLATION_TEMPLATE_KIND,
                "template_code": None,
                "configuration": _coerce_configuration(solution.get("configuration")),
            }
        )
        updates["mounting_system"] = None
        updates["mounting_bar_profile"] = None
        return updates

    if solution and str(solution.get("template_code") or "").strip() in ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES:
        template_code = str(solution["template_code"]).strip()
        normalized_solution = {
            "kind": PRODUCT_SYSTEM_TEMPLATE_KIND,
            "template_code": template_code,
            "configuration": normalize_solution_configuration(template_code, solution.get("configuration")),
        }
        updates["mounting_solution"] = IntakeV4MountingSolution.model_validate(normalized_solution)
        updates["mounting_system"] = None
        updates["mounting_bar_profile"] = None

    return updates


def build_linked_module_input_from_solution(
    *,
    solution: Mapping[str, Any],
    quote_input: Mapping[str, Any],
    defaults: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if is_installation_template_solution(solution):
        return dict(defaults if isinstance(defaults, Mapping) else {})
    module_input = dict(defaults if isinstance(defaults, Mapping) else {})
    template_code = str(solution.get("template_code") or "").strip()

    if template_code == ACM_BOXED_MOUNTING_TEMPLATE_CODE:
        config = normalize_acm_mounting_configuration(_coerce_configuration(solution.get("configuration")))
        if config.get("panel_width_mm") in (None, 0) and quote_input.get("width_mm") is not None:
            config["panel_width_mm"] = quote_input["width_mm"]
        if config.get("panel_height_mm") in (None, 0) and quote_input.get("height_mm") is not None:
            config["panel_height_mm"] = quote_input["height_mm"]
        module_input.update(config)
        derived, _warnings, _blockers = derive_acm_casetted_quote_input(module_input)
        module_input.update(derived)
        return module_input

    config = normalize_metal_mounting_configuration(_coerce_configuration(solution.get("configuration")))
    module_input.update(config)
    width_mm = quote_input.get("width_mm")
    if width_mm is not None:
        premount_length_ml = round(float(width_mm) / 1000.0, 4)
        module_input["premount_bar_length_ml"] = premount_length_ml
        module_input["mounting_bar_length_m"] = premount_length_ml
        module_input["letter_perimeter_m"] = premount_length_ml
    bar_material = str(config.get("bar_material") or "steel").strip().lower()
    module_input["bar_material"] = bar_material
    module_input["mounting_bar_profile"] = config.get("mounting_bar_profile")
    module_input["bar_count"] = config.get("bar_count")
    return module_input
