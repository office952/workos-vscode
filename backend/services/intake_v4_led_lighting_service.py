"""Intake V4 LED module wattage + preview sizing (finish_setup / material preview only)."""

from __future__ import annotations

import math
from typing import Any

# Match material breakdown pitch — 250 mm module spacing for V4 previews.
INTAKE_V4_LED_PITCH_MM = 250.0
DEFAULT_LED_MODULE_POWER_W = 0.75
DEFAULT_LED_STRIP_POWER_W_PER_ML = 5.0
ALLOWED_LED_MODULE_POWER_W: tuple[float, ...] = (0.75, 1.0, 1.44)
DEFAULT_PSU_RESERVE_PERCENT = 30.0


def normalize_led_module_power_w(value: Any) -> float:
    """Snap operator wattage to allowed catalog values; default 0.75 W."""
    if value is None:
        return DEFAULT_LED_MODULE_POWER_W
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return DEFAULT_LED_MODULE_POWER_W
    if parsed <= 0:
        return DEFAULT_LED_MODULE_POWER_W
    for allowed in ALLOWED_LED_MODULE_POWER_W:
        if abs(parsed - allowed) < 0.02:
            return allowed
    # Legacy V2/V3 0.72 W maps to V4 0.75 W option.
    if abs(parsed - 0.72) < 0.02:
        return 0.75
    return DEFAULT_LED_MODULE_POWER_W


def led_module_count_from_perimeter_ml(perimeter_ml: float | None) -> int | None:
    if perimeter_ml is None or perimeter_ml <= 0:
        return None
    return int(math.ceil((float(perimeter_ml) * 1000.0) / INTAKE_V4_LED_PITCH_MM))


def compute_estimated_led_watts(module_count: int | None, module_power_w: float) -> float | None:
    if module_count is None or module_count <= 0:
        return None
    return round(float(module_count) * float(module_power_w), 2)


def normalize_led_strip_power_w_per_ml(value: Any) -> float:
    if value is None:
        return DEFAULT_LED_STRIP_POWER_W_PER_ML
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return DEFAULT_LED_STRIP_POWER_W_PER_ML
    return parsed if parsed > 0 else DEFAULT_LED_STRIP_POWER_W_PER_ML


def compute_estimated_led_strip_watts(
    strip_length_m: float | None,
    strip_power_w_per_ml: float = DEFAULT_LED_STRIP_POWER_W_PER_ML,
) -> float | None:
    if strip_length_m is None or strip_length_m <= 0:
        return None
    power = normalize_led_strip_power_w_per_ml(strip_power_w_per_ml)
    return round(float(strip_length_m) * power, 2)


def compute_required_psu_watts(estimated_led_watts: float | None, reserve_percent: float = DEFAULT_PSU_RESERVE_PERCENT) -> float | None:
    if estimated_led_watts is None or estimated_led_watts <= 0:
        return None
    return round(float(estimated_led_watts) * (1.0 + float(reserve_percent) / 100.0), 2)
