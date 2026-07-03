"""Shared LED area rules for area-lit emblem / lightbox surfaces.

The physical rule is owned by ProductSystem, not by a form.  LED modules use a
depth-aware grid constrained by maximum edge distance; LED strip uses
continuous rows.
"""

from __future__ import annotations

import math
from typing import Any

LED_AREA_MODULE_LENGTH_MM = 75.0
LED_AREA_MODULE_WIDTH_MM = 15.0
LED_AREA_MODULE_INLINE_GAP_MM = 40.0
LED_AREA_MODULE_ROW_GAP_MM = 80.0
LED_AREA_MODULE_MAX_EDGE_DISTANCE_MM = 70.0
LED_AREA_MODULE_BASE_DEPTH_MM = 60.0
LED_AREA_MODULE_DEPTH_STEP_MM = 20.0
LED_AREA_MODULE_GAP_STEP_MM = 20.0

LED_AREA_MODULE_PITCH_X_MM = LED_AREA_MODULE_LENGTH_MM + LED_AREA_MODULE_INLINE_GAP_MM
LED_AREA_MODULE_PITCH_Y_MM = LED_AREA_MODULE_WIDTH_MM + LED_AREA_MODULE_ROW_GAP_MM

LED_AREA_REFERENCE_WIDTH_MM = 1000.0
LED_AREA_REFERENCE_HEIGHT_MM = 1000.0

LED_STRIP_AREA_ROW_SPACING_MM = 40.0
LED_STRIP_AREA_LENGTH_M_PER_SQM = 1000.0 / LED_STRIP_AREA_ROW_SPACING_MM


def _positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def resolve_led_area_module_layout_rule(depth_mm: float | None) -> dict[str, float]:
    depth = _positive(depth_mm)
    normalized_depth = max(LED_AREA_MODULE_BASE_DEPTH_MM, depth or LED_AREA_MODULE_BASE_DEPTH_MM)
    depth_steps = max(
        0,
        int(math.floor((normalized_depth - LED_AREA_MODULE_BASE_DEPTH_MM) / LED_AREA_MODULE_DEPTH_STEP_MM)),
    )
    gap_increase_mm = depth_steps * LED_AREA_MODULE_GAP_STEP_MM
    inline_gap_mm = LED_AREA_MODULE_INLINE_GAP_MM + gap_increase_mm
    row_gap_mm = LED_AREA_MODULE_ROW_GAP_MM + gap_increase_mm
    return {
        "depth_mm": LED_AREA_MODULE_BASE_DEPTH_MM + depth_steps * LED_AREA_MODULE_DEPTH_STEP_MM,
        "inline_gap_mm": inline_gap_mm,
        "row_gap_mm": row_gap_mm,
        "pitch_x_mm": LED_AREA_MODULE_LENGTH_MM + inline_gap_mm,
        "pitch_y_mm": LED_AREA_MODULE_WIDTH_MM + row_gap_mm,
    }


def _count_axis_modules_for_max_edge_distance(
    span_mm: float | None,
    *,
    module_mm: float,
    gap_mm: float,
    max_edge_distance_mm: float,
) -> int | None:
    span = _positive(span_mm)
    if span is None:
        return None
    pitch_mm = module_mm + gap_mm
    uncovered_span_mm = span - 2.0 * max_edge_distance_mm + gap_mm
    return max(1, int(math.ceil(uncovered_span_mm / pitch_mm)))


def calculate_led_module_grid_for_area_lit_box(
    *,
    width_mm: float | None,
    height_mm: float | None,
    depth_mm: float | None = None,
) -> dict[str, int] | None:
    layout = resolve_led_area_module_layout_rule(depth_mm)
    columns = _count_axis_modules_for_max_edge_distance(
        width_mm,
        module_mm=LED_AREA_MODULE_LENGTH_MM,
        gap_mm=layout["inline_gap_mm"],
        max_edge_distance_mm=LED_AREA_MODULE_MAX_EDGE_DISTANCE_MM,
    )
    rows = _count_axis_modules_for_max_edge_distance(
        height_mm,
        module_mm=LED_AREA_MODULE_WIDTH_MM,
        gap_mm=layout["row_gap_mm"],
        max_edge_distance_mm=LED_AREA_MODULE_MAX_EDGE_DISTANCE_MM,
    )
    if columns is None or rows is None:
        return None
    return {"columns": columns, "rows": rows, "modules": columns * rows}


_REFERENCE_GRID = calculate_led_module_grid_for_area_lit_box(
    width_mm=LED_AREA_REFERENCE_WIDTH_MM,
    height_mm=LED_AREA_REFERENCE_HEIGHT_MM,
    depth_mm=LED_AREA_MODULE_BASE_DEPTH_MM,
)

LED_AREA_DENSITY_MODULES_PER_SQM = float((_REFERENCE_GRID or {"modules": 80})["modules"]) / (
    LED_AREA_REFERENCE_WIDTH_MM * LED_AREA_REFERENCE_HEIGHT_MM / 1_000_000.0
)


def led_area_density_modules_per_sqm(depth_mm: float | None = None) -> float:
    grid = calculate_led_module_grid_for_area_lit_box(
        width_mm=LED_AREA_REFERENCE_WIDTH_MM,
        height_mm=LED_AREA_REFERENCE_HEIGHT_MM,
        depth_mm=depth_mm,
    )
    return float((grid or {"modules": LED_AREA_DENSITY_MODULES_PER_SQM})["modules"]) / (
        LED_AREA_REFERENCE_WIDTH_MM * LED_AREA_REFERENCE_HEIGHT_MM / 1_000_000.0
    )


def calculate_led_modules_by_area(
    area_sqm: float | None,
    *,
    depth_mm: float | None = None,
    density_modules_per_sqm: float | None = None,
) -> int | None:
    """Area-only fallback when no bounding dimensions are available."""
    area = _positive(area_sqm)
    if area_sqm is None:
        return None
    if area is None:
        return 0
    density = density_modules_per_sqm or led_area_density_modules_per_sqm(depth_mm)
    if density <= 0:
        return None
    return int(math.ceil(area * density))


def calculate_led_modules_for_area_lit_boxes(
    boxes: list[dict[str, Any]] | None,
    *,
    fallback_area_sqm: float | None = None,
    depth_mm: float | None = None,
) -> int | None:
    if boxes:
        total = 0
        used_any = False
        for box in boxes:
            if not isinstance(box, dict):
                continue
            box_depth = _positive(box.get("depth_mm")) or depth_mm
            grid = calculate_led_module_grid_for_area_lit_box(
                width_mm=_positive(box.get("width_mm")),
                height_mm=_positive(box.get("height_mm")),
                depth_mm=box_depth,
            )
            if grid is not None:
                total += grid["modules"]
                used_any = True
                continue
            fallback = calculate_led_modules_by_area(
                _positive(box.get("area_m2")),
                depth_mm=box_depth,
            )
            if fallback is not None:
                total += fallback
                used_any = True
        if used_any:
            return total
    return calculate_led_modules_by_area(fallback_area_sqm, depth_mm=depth_mm)


def calculate_led_strip_length_by_area(area_sqm: float | None) -> float | None:
    area = _positive(area_sqm)
    if area_sqm is None:
        return None
    if area is None:
        return 0.0
    return round(area * LED_STRIP_AREA_LENGTH_M_PER_SQM, 3)
