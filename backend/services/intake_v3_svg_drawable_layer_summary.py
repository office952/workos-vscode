"""Intake V3 drawable SVG layer summary — paths, polygons, rects, colors, fill groups, font evidence."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Any

_COLOR_FROM_STYLE = re.compile(
    r"(?:fill|stroke)\s*:\s*([^;}\s]+)",
    re.IGNORECASE,
)

DRAWABLE_TAGS = frozenset(
    {"path", "polygon", "polyline", "rect", "circle", "ellipse", "text"}
)
SKIP_SUBTREE_TAGS = frozenset(
    {"defs", "clipPath", "metadata", "symbol", "title", "desc", "mask", "pattern"}
)

FONT_CONVERTED_NOTE = (
    "Text converted to paths — font not recoverable from SVG."
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


def _normalize_color(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned or cleaned.lower() in {"none", "transparent", "currentcolor"}:
        return None
    if cleaned.startswith("#") and len(cleaned) in {4, 7}:
        if len(cleaned) == 4:
            return (
                "#"
                + cleaned[1] * 2
                + cleaned[2] * 2
                + cleaned[3] * 2
            ).upper()
        return cleaned.upper()
    return cleaned


def _colors_from_style(style: str | None) -> tuple[str | None, str | None]:
    if not style:
        return None, None
    fill: str | None = None
    stroke: str | None = None
    for match in _COLOR_FROM_STYLE.finditer(style):
        prop = match.group(0).split(":", 1)[0].strip().lower()
        color = _normalize_color(match.group(1))
        if not color:
            continue
        if prop == "fill" and fill is None:
            fill = color
        elif prop == "stroke" and stroke is None:
            stroke = color
    return fill, stroke


def _resolve_paint(
    elem: ET.Element,
    *,
    attr: str,
    inherited: dict[str, str | None],
) -> str | None:
    direct = _normalize_color(_attr(elem, attr))
    if direct:
        return direct
    style_fill, style_stroke = _colors_from_style(_attr(elem, "style"))
    if attr == "fill" and style_fill:
        return style_fill
    if attr == "stroke" and style_stroke:
        return style_stroke
    return inherited.get(attr)


class _LayerAccumulator:
    def __init__(self, layer_key: str) -> None:
        self.layer_key = layer_key
        self.paths = 0
        self.polygons = 0
        self.polylines = 0
        self.rects = 0
        self.circles = 0
        self.ellipses = 0
        self.texts = 0
        self.fills: Counter[str] = Counter()
        self.strokes: Counter[str] = Counter()
        self.fill_group_counts: Counter[str] = Counter()
        self.font_families: set[str] = set()


def _accumulate_element(
    accum: _LayerAccumulator,
    elem: ET.Element,
    inherited: dict[str, str | None],
) -> None:
    tag = _local_tag(elem.tag)
    fill = _resolve_paint(elem, attr="fill", inherited=inherited)
    stroke = _resolve_paint(elem, attr="stroke", inherited=inherited)

    if tag == "path":
        accum.paths += 1
    elif tag == "polygon":
        accum.polygons += 1
    elif tag == "polyline":
        accum.polylines += 1
    elif tag == "rect":
        accum.rects += 1
    elif tag == "circle":
        accum.circles += 1
    elif tag == "ellipse":
        accum.ellipses += 1
    elif tag == "text":
        accum.texts += 1
        family = _attr(elem, "font-family")
        if family and family.strip():
            accum.font_families.add(family.strip().strip('"').strip("'"))

    if fill:
        accum.fills[fill] += 1
        accum.fill_group_counts[fill] += 1
    if stroke:
        accum.strokes[stroke] += 1


def _collect_drawable_layers(
    elem: ET.Element,
    stack: list[str],
    group_inherited: list[dict[str, str | None]],
    layers: dict[str, _LayerAccumulator],
    detected_group_order: list[str],
) -> None:
    tag = _local_tag(elem.tag)
    if tag in SKIP_SUBTREE_TAGS:
        return

    pushed_key: str | None = None
    pushed_inherited: dict[str, str | None] | None = None

    if tag == "g":
        layer_key = _group_layer_key(elem)
        parent_inherited = group_inherited[-1] if group_inherited else {"fill": None, "stroke": None}
        group_fill = _resolve_paint(elem, attr="fill", inherited=parent_inherited)
        group_stroke = _resolve_paint(elem, attr="stroke", inherited=parent_inherited)
        next_inherited = {"fill": group_fill, "stroke": group_stroke}
        group_inherited.append(next_inherited)
        if layer_key:
            stack.append(layer_key)
            pushed_key = layer_key
            if layer_key not in layers:
                layers[layer_key] = _LayerAccumulator(layer_key)
                detected_group_order.append(layer_key)
    elif tag in DRAWABLE_TAGS:
        if not stack:
            return
        layer_key = stack[-1]
        accum = layers.setdefault(layer_key, _LayerAccumulator(layer_key))
        inherited = group_inherited[-1] if group_inherited else {"fill": None, "stroke": None}
        _accumulate_element(accum, elem, inherited)

    for child in list(elem):
        _collect_drawable_layers(child, stack, group_inherited, layers, detected_group_order)

    if tag == "g":
        if group_inherited:
            group_inherited.pop()
        if pushed_key is not None:
            stack.pop()


def _dominant_color(counter: Counter[str]) -> str | None:
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def _build_color_evidence(accum: _LayerAccumulator) -> dict[str, Any]:
    fills = sorted(accum.fills.keys())
    strokes = sorted(accum.strokes.keys())
    fill_groups = [
        {
            "color": color,
            "label": color,
            "element_count": count,
            "kind": "fill",
        }
        for color, count in sorted(
            accum.fill_group_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
    distinct_fill_count = len(fills)
    is_multicolor = (
        (accum.polygons >= 50 and distinct_fill_count >= 3)
        or (accum.polygons >= 20 and distinct_fill_count >= 8)
        or distinct_fill_count >= 12
    )
    return {
        "fills": fills,
        "strokes": strokes,
        "dominant_fill": _dominant_color(accum.fills),
        "dominant_stroke": _dominant_color(accum.strokes),
        "is_multicolor": is_multicolor,
        "fill_groups": fill_groups,
    }


def _build_element_counts(accum: _LayerAccumulator) -> dict[str, int]:
    total = (
        accum.paths
        + accum.polygons
        + accum.polylines
        + accum.rects
        + accum.circles
        + accum.ellipses
        + accum.texts
    )
    return {
        "paths": accum.paths,
        "polygons": accum.polygons,
        "polylines": accum.polylines,
        "rects": accum.rects,
        "circles": accum.circles,
        "ellipses": accum.ellipses,
        "texts": accum.texts,
        "total": total,
    }


def _layer_font_evidence(
    accum: _LayerAccumulator,
    *,
    document_has_text: bool,
    document_has_paths: bool,
) -> dict[str, Any]:
    has_text = accum.texts > 0
    converted = not document_has_text and document_has_paths and not has_text
    note: str | None = None
    if converted:
        note = FONT_CONVERTED_NOTE
    elif has_text and accum.font_families:
        note = None
    return {
        "has_text": has_text,
        "font_families": sorted(accum.font_families),
        "converted_to_paths": converted,
        "note": note,
    }


def build_drawable_layer_summary_from_svg_text(svg_text: str) -> dict[str, Any] | None:
    """Return per-layer drawable evidence; None when SVG cannot be parsed."""
    if not svg_text or not svg_text.strip():
        return None
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return None
    if _local_tag(root.tag) != "svg":
        return None

    layers: dict[str, _LayerAccumulator] = {}
    detected_group_order: list[str] = []
    _collect_drawable_layers(root, [], [{"fill": None, "stroke": None}], layers, detected_group_order)

    document_has_text = any(acc.texts > 0 for acc in layers.values())
    document_has_paths = any(acc.paths > 0 for acc in layers.values())

    layer_rows: list[dict[str, Any]] = []
    for layer_key in detected_group_order:
        accum = layers.get(layer_key)
        if accum is None:
            continue
        element_counts = _build_element_counts(accum)
        if element_counts["total"] <= 0:
            continue
        layer_rows.append(
            {
                "layer_id": layer_key,
                "layer_name": layer_key,
                "layer_key": layer_key,
                "display_name": layer_key,
                "source": "drawable_summary",
                "element_counts": element_counts,
                "color_evidence": _build_color_evidence(accum),
                "font_evidence": _layer_font_evidence(
                    accum,
                    document_has_text=document_has_text,
                    document_has_paths=document_has_paths,
                ),
            }
        )

    workspace_font_evidence = {
        "has_text": document_has_text,
        "font_families": sorted(
            {
                family
                for acc in layers.values()
                for family in acc.font_families
            }
        ),
        "converted_to_paths": not document_has_text and document_has_paths,
        "note": FONT_CONVERTED_NOTE if not document_has_text and document_has_paths else None,
    }

    return {
        "layers": layer_rows,
        "layer_count": len(layer_rows),
        "font_evidence": workspace_font_evidence,
    }
