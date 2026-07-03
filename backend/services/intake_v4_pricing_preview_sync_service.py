"""Persist derived Intake V4 pricing preview state (geometry + lighting) after analysis/finish."""

from __future__ import annotations

import math
from typing import Any

from schemas.intake_v4 import IntakeV4FinishSetup, IntakeV4WorkspacePayload
from services.intake_v3_lighting_plan_service import propose_psu_units, sync_lighting_plan
from services.intake_v4_finish_adapter import _map_v4_led_system, _map_v4_light_color
from services.intake_v4_led_lighting_service import (
    DEFAULT_PSU_RESERVE_PERCENT,
    compute_estimated_led_strip_watts,
    compute_estimated_led_watts,
    compute_required_psu_watts,
    led_module_count_from_perimeter_ml,
    normalize_led_strip_power_w_per_ml,
    normalize_led_module_power_w,
)
from services.intake_v4_backing_mode_service import (
    apply_backing_state_to_geometry_patch,
    resolve_volumetric_backing_state,
)
from services.shared_led_lighting_density_rules import (
    calculate_led_modules_for_area_lit_boxes,
    calculate_led_strip_length_by_area,
)
from services.intake_v4_quote_geometry_service import merge_quote_geometry_into_path_summary, resolve_v4_quote_geometry
from schemas.intake_v3 import IntakeV3LightingPlan, IntakeV3PsuPlanUnit

# Match material breakdown LED module pitch so preview rows stay consistent.
MATERIAL_BREAKDOWN_LED_PITCH_MM = 250.0


def _positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _led_module_count_from_geometry(path_geometry: dict[str, Any]) -> int | None:
    perimeter_ml = _positive(path_geometry.get("led_perimeter_ml")) or _positive(
        path_geometry.get("outer_letter_perimeter_ml")
    )
    if perimeter_ml is None:
        return None
    return int(math.ceil((perimeter_ml * 1000.0) / MATERIAL_BREAKDOWN_LED_PITCH_MM))


def _emblem_depth_mm_from_setup(setup: IntakeV4FinishSetup) -> float | None:
    artwork_depths = [
        depth
        for depth in (_positive(row.return_depth_mm) for row in setup.artwork_finishes or [])
        if depth is not None
    ]
    if artwork_depths:
        return max(artwork_depths)
    return _positive(setup.return_depth_mm)


def _artwork_depth_by_key(setup: IntakeV4FinishSetup) -> dict[str, float]:
    depths: dict[str, float] = {}
    for row in setup.artwork_finishes or []:
        depth = _positive(row.return_depth_mm)
        if depth is None:
            continue
        if row.layer_key:
            depths[row.layer_key] = depth
        if row.layer_name:
            depths[row.layer_name] = depth
    return depths


def _artwork_boxes_from_geometry(
    path_geometry: dict[str, Any],
    *,
    setup: IntakeV4FinishSetup,
    fallback_depth_mm: float | None,
) -> list[dict[str, Any]]:
    raw = path_geometry.get("artwork_boxes")
    if not isinstance(raw, list):
        return []
    depth_by_key = _artwork_depth_by_key(setup)
    boxes: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        box = dict(item)
        layer_depth = None
        layer_key = box.get("layer_key")
        layer_name = box.get("layer_name")
        if isinstance(layer_key, str):
            layer_depth = depth_by_key.get(layer_key)
        if layer_depth is None and isinstance(layer_name, str):
            layer_depth = depth_by_key.get(layer_name)
        box["depth_mm"] = layer_depth or _positive(box.get("depth_mm")) or fallback_depth_mm
        boxes.append(box)
    return boxes


def _flatten_psu_units(units: list[IntakeV3PsuPlanUnit]) -> list[int]:
    psu_configuration: list[int] = []
    for unit in units:
        for _ in range(max(int(unit.quantity), 0)):
            psu_configuration.append(int(unit.capacity_w))
    return psu_configuration


def _totals_stale_for_emblem_area_lit(
    setup: IntakeV4FinishSetup,
    *,
    emblem_mode: str,
    letter_module_count: int | None,
    total_module_count: int | None,
    module_power: float,
) -> bool:
    """True when stored watts/PSU reflect letter-only totals but emblem adds modules."""
    if emblem_mode == "area_lit":
        return True
    if (
        letter_module_count is None
        or total_module_count is None
        or total_module_count <= letter_module_count
    ):
        return False

    letter_watts = compute_estimated_led_watts(letter_module_count, module_power)
    stored_watts = _positive(setup.estimated_led_watts)
    if letter_watts is None or stored_watts is None:
        return False
    if abs(stored_watts - letter_watts) > 0.02:
        return False

    letter_required = compute_required_psu_watts(letter_watts, DEFAULT_PSU_RESERVE_PERCENT)
    stored_required = _positive(setup.required_psu_watts)
    if letter_required is None or stored_required is None:
        return True
    return abs(stored_required - letter_required) <= 0.05


def sync_intake_v4_finish_lighting(
    setup: IntakeV4FinishSetup,
    *,
    path_geometry: dict[str, Any],
) -> IntakeV4FinishSetup:
    """Derive LED watts + PSU configuration for illuminated jobs when not operator-set."""
    if setup.illuminated is False:
        return setup

    module_power = normalize_led_module_power_w(setup.led_module_power_w)
    strip_power = normalize_led_strip_power_w_per_ml(setup.led_strip_power_w_per_ml)
    lighting_system = str(setup.lighting_system_type or "led_modules").strip().lower()
    is_led_strip = lighting_system == "led_strip"
    perimeter_ml = _positive(path_geometry.get("led_perimeter_ml")) or _positive(
        path_geometry.get("outer_letter_perimeter_ml")
    )
    emblem_mode = str(setup.emblem_lighting_mode or "area_lit").strip().lower()
    emblem_area = _positive(path_geometry.get("artwork_area_m2"))
    depth_mm = _emblem_depth_mm_from_setup(setup)
    emblem_boxes = _artwork_boxes_from_geometry(
        path_geometry,
        setup=setup,
        fallback_depth_mm=depth_mm,
    )

    if is_led_strip:
        letter_strip_length_m = round(perimeter_ml, 3) if perimeter_ml is not None else None
        if emblem_mode == "area_lit":
            emblem_strip_length_m = calculate_led_strip_length_by_area(emblem_area)
        elif emblem_mode == "excluded":
            emblem_strip_length_m = 0.0
        else:
            emblem_strip_length_m = None
        total_strip_length_m = (
            round((letter_strip_length_m or 0.0) + (emblem_strip_length_m or 0.0), 3)
            if letter_strip_length_m is not None or emblem_strip_length_m is not None
            else None
        )
        estimated_watts = compute_estimated_led_strip_watts(total_strip_length_m, strip_power)
        required_watts = compute_required_psu_watts(estimated_watts, DEFAULT_PSU_RESERVE_PERCENT)
        psu_units = propose_psu_units(float(required_watts)) if required_watts else []
        psu_configuration = _flatten_psu_units(psu_units)
        updates: dict[str, Any] = {
            "led_module_power_w": module_power,
            "led_strip_power_w_per_ml": strip_power,
            "letter_led_module_count": None,
            "emblem_led_module_count": None,
            "led_module_count": None,
            "total_led_module_count": None,
            "letter_led_strip_length_m": letter_strip_length_m,
            "emblem_led_strip_length_m": emblem_strip_length_m,
            "total_led_strip_length_m": total_strip_length_m,
            "estimated_led_watts": estimated_watts,
            "required_psu_watts": required_watts,
            "psu_configuration": psu_configuration,
        }
        if psu_configuration:
            updates["selected_psu_watts"] = max(psu_configuration)
        return setup.model_copy(update=updates)

    letter_module_count = _led_module_count_from_geometry(path_geometry)
    if letter_module_count is None:
        letter_module_count = led_module_count_from_perimeter_ml(perimeter_ml)

    emblem_module_count: int | None = None
    if emblem_mode == "area_lit":
        emblem_module_count = calculate_led_modules_for_area_lit_boxes(
            emblem_boxes,
            fallback_area_sqm=emblem_area,
            depth_mm=depth_mm,
        )

    total_module_count: int | None = None
    if letter_module_count is not None:
        total_module_count = letter_module_count + (emblem_module_count or 0)
    module_count = total_module_count if total_module_count is not None else letter_module_count

    existing_psu = [int(w) for w in (setup.psu_configuration or []) if isinstance(w, (int, float)) and w > 0]
    stale_emblem_totals = _totals_stale_for_emblem_area_lit(
        setup,
        emblem_mode=emblem_mode,
        letter_module_count=letter_module_count,
        total_module_count=module_count,
        module_power=module_power,
    )
    has_operator_psu = bool(existing_psu) and not stale_emblem_totals
    has_operator_watts = _positive(setup.estimated_led_watts) is not None and not stale_emblem_totals
    has_operator_required_psu = (
        setup.required_psu_watts is not None
        and _positive(setup.required_psu_watts) is not None
        and not stale_emblem_totals
    )

    if module_count is None and not has_operator_watts:
        if setup.led_module_power_w != module_power:
            return setup.model_copy(update={"led_module_power_w": module_power})
        return setup

    if has_operator_watts and module_count is None:
        module_count = max(1, int(round(float(setup.estimated_led_watts) / float(module_power))))

    estimated_watts = compute_estimated_led_watts(module_count, module_power)
    if has_operator_watts:
        estimated_watts = float(setup.estimated_led_watts)  # type: ignore[arg-type]

    reserve = DEFAULT_PSU_RESERVE_PERCENT
    required_watts = compute_required_psu_watts(estimated_watts, reserve)
    if has_operator_required_psu:
        required_watts = float(setup.required_psu_watts)  # type: ignore[arg-type]

    psu_units: list[IntakeV3PsuPlanUnit] = []
    if has_operator_psu:
        psu_units = [
            IntakeV3PsuPlanUnit(capacity_w=float(watts), quantity=1, label=f"{watts}W", source="manual")
            for watts in existing_psu
        ]

    plan = IntakeV3LightingPlan(
        enabled=True,
        illumination_mode="frontlit",
        led_system=_map_v4_led_system(setup.lighting_system_type),
        light_color=_map_v4_light_color(setup.light_color) or "neutral_white",
        module_power_w=module_power,
        module_count=module_count,
        estimated_total_watts=estimated_watts,
        required_watts_with_reserve=required_watts,
        psu_units=psu_units,
        psu_strategy="auto" if not has_operator_psu else "manual",
        reserve_percent=reserve,
        is_confirmed=setup.confirmed is True,
    )
    synced = sync_lighting_plan(plan)

    updates: dict[str, Any] = {
        "led_module_power_w": module_power,
        "led_strip_power_w_per_ml": strip_power,
        "letter_led_strip_length_m": None,
        "emblem_led_strip_length_m": None,
        "total_led_strip_length_m": None,
    }
    if letter_module_count is not None:
        updates["letter_led_module_count"] = letter_module_count
    if emblem_module_count is not None:
        updates["emblem_led_module_count"] = emblem_module_count
    if module_count is not None:
        updates["led_module_count"] = module_count
        updates["total_led_module_count"] = module_count
    if synced.estimated_total_watts is not None and not has_operator_watts:
        updates["estimated_led_watts"] = synced.estimated_total_watts
    if synced.required_watts_with_reserve is not None and not has_operator_required_psu:
        updates["required_psu_watts"] = synced.required_watts_with_reserve

    if has_operator_psu:
        updates["psu_configuration"] = existing_psu
    elif synced.psu_units:
        psu_configuration = _flatten_psu_units(synced.psu_units)
        if psu_configuration:
            updates["psu_configuration"] = psu_configuration

    if not updates:
        return setup
    return setup.model_copy(update=updates)


def apply_v4_pricing_preview_derived_state(payload_raw: dict[str, Any]) -> None:
    """Mutate ``payload_raw`` with canonical quote geometry and synced finish lighting."""
    if not isinstance(payload_raw, dict):
        return

    payload = IntakeV4WorkspacePayload.model_validate(payload_raw)

    if not payload.svg_analysis_json or payload.layer_role_setup is None:
        return

    quote_geometry = resolve_v4_quote_geometry(payload)
    path_summary = payload.path_geometry_summary if isinstance(payload.path_geometry_summary, dict) else {}
    merged_path = merge_quote_geometry_into_path_summary(path_summary, quote_geometry)

    payload_raw["quote_geometry"] = quote_geometry
    payload_raw["path_geometry_summary"] = merged_path

    finish_dict = payload.finish_setup.model_dump(mode="json") if payload.finish_setup else {}
    layer_dict = (
        payload.layer_role_setup.model_dump(mode="json") if payload.layer_role_setup else None
    )
    _, backing_present, back_bevel = resolve_volumetric_backing_state(
        finish_dict,
        layer_dict,
        quote_geometry=quote_geometry if isinstance(quote_geometry, dict) else None,
    )
    backing_patch = apply_backing_state_to_geometry_patch(
        {},
        backing_present=backing_present,
        back_bevel_enabled=back_bevel,
    )
    merged_path = {**merged_path, **backing_patch}
    payload_raw["path_geometry_summary"] = merged_path

    if payload.finish_setup is not None:
        synced_finish = sync_intake_v4_finish_lighting(payload.finish_setup, path_geometry=merged_path)
        synced_finish_dict = synced_finish.model_dump(mode="json")
        if payload.finish_setup.commercial_inputs is not None:
            synced_finish_dict["commercial_inputs"] = payload.finish_setup.commercial_inputs.model_dump(mode="json")
        payload_raw["finish_setup"] = synced_finish_dict
