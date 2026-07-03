"""Parse SVG path geometry grouped by layer/group id — upload-time summary only."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from services.intake_v3_svg_drawable_layer_summary import build_drawable_layer_summary_from_svg_text
from services.svg_metrics_service import SvgMetricsService, _to_float
from services.svg_path_metrics import parse_path_metrics

SKIP_SUBTREE_TAGS = frozenset(
    {"defs", "clipPath", "metadata", "symbol", "title", "desc", "mask", "pattern"}
)


def _local_tag(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _attr(elem: ET.Element, name: str) -> str | None:
    value = elem.get(name)
    if value is not None:
        return value
    for key, val in elem.attrib.items():
        if key.endswith(f"}}{name}") or key == name:
            return val
    return None


def _is_inkscape_layer_group(elem: ET.Element) -> bool:
    for key, val in elem.attrib.items():
        if key.split("}", 1)[-1] == "groupmode" and str(val).strip().lower() == "layer":
            return True
    return False


def _group_layer_key(elem: ET.Element) -> str | None:
    group_id = _attr(elem, "id")
    if group_id and group_id.strip():
        return group_id.strip()
    if _is_inkscape_layer_group(elem):
        label = _attr(elem, "label") or _attr(elem, "data-name")
        if label and label.strip():
            return label.strip()
    return None


def _resolve_scale(root: ET.Element, warnings: list[str]) -> tuple[float, float]:
    width_mm = SvgMetricsService._parse_length_mm(_attr(root, "width"), warnings)
    height_mm = SvgMetricsService._parse_length_mm(_attr(root, "height"), warnings)
    vb = _attr(root, "viewBox") or _attr(root, "viewbox")
    vb_w: float | None = None
    vb_h: float | None = None
    if vb:
        parts = re.split(r"[\s,]+", vb.strip())
        if len(parts) == 4:
            vb_w = _to_float(parts[2])
            vb_h = _to_float(parts[3])
    if width_mm is None or height_mm is None:
        warnings.append("document_units_assumed_mm")
        return 1.0, 1.0
    if vb_w and vb_h and vb_w > 0 and vb_h > 0:
        return width_mm / vb_w, height_mm / vb_h
    return 1.0, 1.0


def _length_to_mm(length_user: float, scale_x: float, scale_y: float) -> float:
    return length_user * (scale_x + scale_y) / 2.0


def _collect_layer_paths(
    elem: ET.Element,
    stack: list[str],
    layer_paths: dict[str, list[str]],
    layer_names: dict[str, str | None],
) -> None:
    tag = _local_tag(elem.tag)
    if tag in SKIP_SUBTREE_TAGS:
        return

    pushed: str | None = None
    if tag == "g":
        layer_key = _group_layer_key(elem)
        if layer_key:
            stack.append(layer_key)
            pushed = layer_key
            layer_names.setdefault(layer_key, _attr(elem, "data-name"))
    elif tag == "path":
        if not stack:
            return
        d_attr = _attr(elem, "d")
        if d_attr and str(d_attr).strip():
            layer_id = stack[-1]
            layer_paths.setdefault(layer_id, []).append(str(d_attr))
    for child in list(elem):
        _collect_layer_paths(child, stack, layer_paths, layer_names)
    if pushed is not None:
        stack.pop()


def _path_metrics_for_layer(
    paths: list[str],
    *,
    scale_x: float,
    scale_y: float,
) -> dict[str, Any]:
    closed_count = 0
    perimeter_user = 0.0
    area_user = 0.0
    for d in paths:
        pm = parse_path_metrics(d)
        perimeter_user += pm.total_length
        area_user += pm.total_closed_area
        closed_count += sum(1 for s in pm.subpaths if s.closed)
    perimeter_mm = round(_length_to_mm(perimeter_user, scale_x, scale_y), 6)
    return {
        "path_count": len(paths),
        "closed_contour_count": closed_count,
        "perimeter_mm": perimeter_mm,
        "area_mm2": round(area_user * scale_x * scale_y, 6) if area_user > 0 else None,
    }


def _merge_drawable_and_path_layers(
    drawable_summary: dict[str, Any] | None,
    path_layers: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    drawable_layers = (drawable_summary or {}).get("layers") or []
    seen: set[str] = set()

    for drawable in drawable_layers:
        if not isinstance(drawable, dict):
            continue
        layer_id = drawable.get("layer_id") or drawable.get("layer_key")
        if not layer_id:
            continue
        layer_key = str(layer_id)
        seen.add(layer_key)
        row = dict(drawable)
        path_metrics = path_layers.get(layer_key)
        if path_metrics:
            row.update(path_metrics)
        else:
            counts = row.get("element_counts") or {}
            row.setdefault("path_count", counts.get("paths", 0))
            row.setdefault("closed_contour_count", counts.get("paths", 0))
            row.setdefault("perimeter_mm", None)
            row.setdefault("area_mm2", None)
        merged.append(row)

    for layer_key, metrics in path_layers.items():
        if layer_key in seen:
            continue
        merged.append(
            {
                "layer_id": layer_key,
                "layer_name": metrics.get("layer_name"),
                "layer_key": layer_key,
                "display_name": metrics.get("layer_name") or layer_key,
                "source": "path_geometry",
                **metrics,
            }
        )
    return merged


def build_layer_path_geometry_from_svg_text(svg_text: str) -> dict[str, Any] | None:
    """Return per-layer drawable + path metrics; None when SVG cannot be parsed."""
    if not svg_text or not svg_text.strip():
        return None
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return None
    if _local_tag(root.tag) != "svg":
        return None

    warnings: list[str] = []
    scale_x, scale_y = _resolve_scale(root, warnings)

    layer_paths: dict[str, list[str]] = {}
    layer_names: dict[str, str | None] = {}
    _collect_layer_paths(root, [], layer_paths, layer_names)

    path_layers: dict[str, dict[str, Any]] = {}
    total_cutting_perimeter_mm = 0.0
    for layer_id, paths in layer_paths.items():
        metrics = _path_metrics_for_layer(paths, scale_x=scale_x, scale_y=scale_y)
        layer_name = layer_names.get(layer_id)
        path_layers[layer_id] = {
            "layer_id": layer_id,
            "layer_name": layer_name,
            **metrics,
        }
        perimeter_mm = metrics.get("perimeter_mm") or 0.0
        total_cutting_perimeter_mm += float(perimeter_mm)

    drawable_summary = build_drawable_layer_summary_from_svg_text(svg_text)
    layers = _merge_drawable_and_path_layers(drawable_summary, path_layers)

    contour_split: dict[str, Any] = {
        "outer_contour_perimeter_mm": None,
        "inner_hole_perimeter_mm": None,
        "total_cutting_perimeter_mm": round(total_cutting_perimeter_mm, 6)
        if total_cutting_perimeter_mm > 0
        else None,
        "split_quality": "missing",
    }

    result: dict[str, Any] = {
        "layers": layers,
        "layer_count": len(layers),
        "contour_split": contour_split,
        "warnings": list(dict.fromkeys(warnings)),
    }
    if drawable_summary:
        result["drawable_layers"] = drawable_summary.get("layers") or []
        result["font_evidence"] = drawable_summary.get("font_evidence")
    return result
