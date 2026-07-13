"""Product System mounting solution reference — Intake V6 composition contract."""

from __future__ import annotations

from typing import Any, Mapping

from schemas.intake_v4 import IntakeV4MountingSolution
from services.mounting_scope_service import is_mounting_preparation_active, normalize_mounting_scope

METAL_PREMOUNT_TEMPLATE_CODE = "TPL-METAL-PREMOUNT-STRUCTURE_v1"
ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES = frozenset({METAL_PREMOUNT_TEMPLATE_CODE})
BAR_MOUNTING_LEGACY = frozenset({"steel_bars", "aluminum_bars"})

DEFAULT_METAL_MOUNTING_CONFIGURATION: dict[str, Any] = {
    "bar_count": 2,
    "mounting_bar_profile": "30x30x1.5",
    "bar_material": "steel",
}


def _coerce_configuration(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    return dict(raw)


def read_mounting_solution(setup: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(setup, Mapping):
        return None
    raw = setup.get("mounting_solution")
    if not isinstance(raw, dict):
        return None
    template_code = str(raw.get("template_code") or "").strip()
    if not template_code:
        return None
    return {
        "template_code": template_code,
        "configuration": _coerce_configuration(raw.get("configuration")),
    }


def hydrate_mounting_solution_from_legacy(setup: Mapping[str, Any] | None) -> dict[str, Any] | None:
    existing = read_mounting_solution(setup)
    if existing:
        return existing
    if not isinstance(setup, Mapping):
        return None
    mounting_system = str(setup.get("mounting_system") or "").strip()
    if mounting_system not in BAR_MOUNTING_LEGACY:
        return None
    bar_material = "aluminum" if mounting_system == "aluminum_bars" else "steel"
    profile = str(setup.get("mounting_bar_profile") or DEFAULT_METAL_MOUNTING_CONFIGURATION["mounting_bar_profile"]).strip()
    return {
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


def is_mounting_solution_composition_active(setup: Mapping[str, Any] | None) -> bool:
    if not isinstance(setup, Mapping):
        return False
    if not is_mounting_preparation_active(setup):
        return False
    solution = resolve_effective_mounting_solution(setup)
    if not solution:
        return False
    return str(solution.get("template_code") or "").strip() in ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES


def is_structura_suport_active(setup: Mapping[str, Any] | None) -> bool:
    return is_mounting_solution_composition_active(setup)


def legacy_mounting_system_from_solution(solution: Mapping[str, Any] | None) -> str | None:
    if not isinstance(solution, Mapping):
        return None
    if str(solution.get("template_code") or "").strip() != METAL_PREMOUNT_TEMPLATE_CODE:
        return None
    config = normalize_metal_mounting_configuration(_coerce_configuration(solution.get("configuration")))
    return "aluminum_bars" if config["bar_material"] == "aluminum" else "steel_bars"


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

    if solution and str(solution.get("template_code") or "").strip() in ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES:
        normalized_solution = {
            "template_code": str(solution["template_code"]).strip(),
            "configuration": normalize_metal_mounting_configuration(solution.get("configuration")),
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
    module_input = dict(defaults if isinstance(defaults, Mapping) else {})
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
