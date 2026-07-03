"""Tests for shared LED area density rules."""

from __future__ import annotations

import math

from services.shared_led_lighting_density_rules import (
    LED_AREA_DENSITY_MODULES_PER_SQM,
    LED_AREA_MODULE_BASE_DEPTH_MM,
    LED_AREA_MODULE_GAP_STEP_MM,
    LED_AREA_MODULE_INLINE_GAP_MM,
    LED_AREA_MODULE_LENGTH_MM,
    LED_AREA_MODULE_MAX_EDGE_DISTANCE_MM,
    LED_AREA_MODULE_PITCH_X_MM,
    LED_AREA_MODULE_PITCH_Y_MM,
    LED_AREA_MODULE_ROW_GAP_MM,
    LED_AREA_MODULE_WIDTH_MM,
    calculate_led_module_grid_for_area_lit_box,
    calculate_led_modules_by_area,
    calculate_led_strip_length_by_area,
    led_area_density_modules_per_sqm,
    resolve_led_area_module_layout_rule,
)


def test_led_area_density_ceil():
    # Area-only fallback uses the 100 x 100 cm reference grid at 60 mm depth.
    assert calculate_led_modules_by_area(0.45) == 36
    assert calculate_led_modules_by_area(0.01) == 1


def test_led_area_density_derived_from_physical_layout():
    assert LED_AREA_MODULE_LENGTH_MM == 75.0
    assert LED_AREA_MODULE_WIDTH_MM == 15.0
    assert LED_AREA_MODULE_BASE_DEPTH_MM == 60.0
    assert LED_AREA_MODULE_INLINE_GAP_MM == 40.0
    assert LED_AREA_MODULE_ROW_GAP_MM == 80.0
    assert LED_AREA_MODULE_GAP_STEP_MM == 20.0
    assert LED_AREA_MODULE_MAX_EDGE_DISTANCE_MM == 70.0
    assert LED_AREA_MODULE_PITCH_X_MM == 115.0
    assert LED_AREA_MODULE_PITCH_Y_MM == 95.0
    grid = calculate_led_module_grid_for_area_lit_box(
        width_mm=1000.0,
        height_mm=1000.0,
        depth_mm=60.0,
    )
    assert grid == {"columns": 8, "rows": 10, "modules": 80}
    assert LED_AREA_DENSITY_MODULES_PER_SQM == 80.0
    assert led_area_density_modules_per_sqm(60.0) == 80.0


def test_depth_rule_expands_module_gaps_for_deeper_returns():
    rule_60 = resolve_led_area_module_layout_rule(60.0)
    rule_80 = resolve_led_area_module_layout_rule(80.0)
    rule_100 = resolve_led_area_module_layout_rule(100.0)
    rule_140 = resolve_led_area_module_layout_rule(140.0)

    assert rule_60["inline_gap_mm"] == 40.0
    assert rule_60["row_gap_mm"] == 80.0
    assert rule_80["inline_gap_mm"] == 60.0
    assert rule_80["row_gap_mm"] == 100.0
    assert rule_100["inline_gap_mm"] == 80.0
    assert rule_100["row_gap_mm"] == 120.0
    assert rule_140["inline_gap_mm"] == 120.0
    assert rule_140["row_gap_mm"] == 160.0

    assert calculate_led_module_grid_for_area_lit_box(
        width_mm=1000.0,
        height_mm=1000.0,
        depth_mm=80.0,
    ) == {"columns": 7, "rows": 9, "modules": 63}
    assert calculate_led_module_grid_for_area_lit_box(
        width_mm=1000.0,
        height_mm=1000.0,
        depth_mm=100.0,
    ) == {"columns": 7, "rows": 8, "modules": 56}


def test_led_strip_area_uses_continuous_rows():
    assert calculate_led_strip_length_by_area(0.2) == 5.0


def test_pbl_style_emblem_area():
    area = 0.5834
    expected = int(math.ceil(area * LED_AREA_DENSITY_MODULES_PER_SQM))
    assert calculate_led_modules_by_area(area) == expected
