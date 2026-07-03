"""Fail-closed guard for degraded client analysis bundles (layer-level collapse)."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

_MIN_BBOX_MM = 1e-6


def _part_width_mm(item: dict[str, Any]) -> float | None:
    bounds = item.get("bounds")
    if not isinstance(bounds, dict):
        return None
    width = bounds.get("widthMm")
    return float(width) if isinstance(width, (int, float)) else None


def _part_height_mm(item: dict[str, Any]) -> float | None:
    bounds = item.get("bounds")
    if not isinstance(bounds, dict):
        return None
    height = bounds.get("heightMm")
    return float(height) if isinstance(height, (int, float)) else None


def _has_valid_part_bounds(item: dict[str, Any]) -> bool:
    width = _part_width_mm(item)
    height = _part_height_mm(item)
    return width is not None and height is not None and width > _MIN_BBOX_MM and height > _MIN_BBOX_MM


def analysis_bundle_has_degraded_child_parts(svg_analysis_json: dict[str, Any] | None) -> bool:
    """True when split-preferred analysis collapsed to layer-level parts with invalid bounds."""
    if not isinstance(svg_analysis_json, dict):
        return False

    parts = svg_analysis_json.get("parts")
    if not isinstance(parts, dict):
        return False

    items = parts.get("items")
    if not isinstance(items, list) or not items:
        return False

    split_diag = parts.get("splitDiagnostics")
    split_diag = split_diag if isinstance(split_diag, dict) else {}
    sub_path_count = int(split_diag.get("subPathCount") or 0)
    groups_created = int(split_diag.get("groupsCreated") or 0)
    extraction_mode = split_diag.get("extractionMode") or parts.get("extractionMode")
    fallback_used = bool(split_diag.get("fallbackUsed"))

    if sub_path_count < 8:
        return False

    if fallback_used or extraction_mode not in (None, "split-preferred", "subpath-shape-grouping"):
        return False

    split_items = [
        item
        for item in items
        if isinstance(item, dict) and item.get("partExtractionMethod") == "subpath-shape-grouping"
    ]
    if not split_items:
        return False

    invalid_split_bounds = [item for item in split_items if not _has_valid_part_bounds(item)]
    collapsed_groups = groups_created <= 3 and sub_path_count >= 10
    collapsed_items = len(items) <= 3 and sub_path_count >= 10

    if collapsed_groups or collapsed_items:
        return True

    if len(invalid_split_bounds) == len(split_items) and len(split_items) >= 2:
        return True

    return False


def assert_analysis_bundle_child_parts_or_raise(svg_analysis_json: dict[str, Any] | None) -> None:
    if not analysis_bundle_has_degraded_child_parts(svg_analysis_json):
        return

    parts = (svg_analysis_json or {}).get("parts") if isinstance(svg_analysis_json, dict) else {}
    split_diag = parts.get("splitDiagnostics") if isinstance(parts, dict) else {}
    split_diag = split_diag if isinstance(split_diag, dict) else {}

    raise HTTPException(
        status_code=422,
        detail={
            "error": "degraded_child_parts_analysis",
            "message": (
                "SVG analysis bundle collapsed child parts to layer-level geometry. "
                "Re-analyze the SVG before persisting."
            ),
            "sub_path_count": split_diag.get("subPathCount"),
            "groups_created": split_diag.get("groupsCreated"),
            "parts_count": parts.get("count") if isinstance(parts, dict) else None,
        },
    )
