"""Extract flat-material piece geometry from SVG (generic mm bboxes).

Architecture
------------
``letter_bounding_boxes`` stores **material-agnostic** flat piece geometry
(``width_mm``, ``height_mm``) detected from SVG vector data. Downstream
material adapters consume the same pieces differently:

* **Roll / vinyl** — ``face_vinyl_piece_nesting`` → ``nested_roll_length_m``,
  ``recommended_roll_length_m``, ``material_width_m``, ``quantity_m2`` (mp).
* **Sheet / plate** (plexiglas, Forex, ACM — future) — a separate sheet nesting
  adapter would emit ``sheets_used``, ``sheet_width_mm``, ``sheet_height_mm``,
  ``placements``, ``allocated_sheet_area_m2``, ``waste_area_m2`` (no ml).

This module is named ``svg_face_vinyl_pieces_service`` for the face-vinyl build
boundary; the extraction logic is intentionally generic and can move to
``flat_material_geometry_service`` when sheet nesting lands.

Production rule
---------------
Pieces are emitted only when the letters layer is **semantically mapped** to
``TPL-VOLUMETRIC-LETTERS`` in ``svg_layer_mappings``. Parseable bbox alone is
not enough — unmapped generic layers must not feed nesting.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from services.svg_layer_analysis_service import _discover_layers
from services.svg_metrics_service import (
    SvgMetricsService,
    _local_name,
    _parse_points,
    _to_float,
)
from services.svg_path_metrics import extract_letter_subpath_bboxes

LETTERS_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"

_MIN_PIECE_MM = 5.0
_MAX_PIECES = 200
_SKIP_TAGS = frozenset({"defs", "metadata", "title", "desc", "style", "clipPath", "mask"})


def _letters_layer_is_mapped(svg_layer_mappings: dict[str, str]) -> bool:
    return LETTERS_TEMPLATE_CODE in svg_layer_mappings.values()


def _document_scale_factors(root: ET.Element) -> tuple[float, float]:
    """Return scale_x, scale_y from SVG user units to millimeters."""
    warnings: list[str] = []
    width_mm = SvgMetricsService._parse_length_mm(root.attrib.get("width"), warnings)
    height_mm = SvgMetricsService._parse_length_mm(root.attrib.get("height"), warnings)

    vb = root.attrib.get("viewBox") or root.attrib.get("viewbox")
    vb_w: float | None = None
    vb_h: float | None = None
    if vb:
        parts = re.split(r"[\s,]+", vb.strip())
        if len(parts) == 4:
            vb_w = _to_float(parts[2])
            vb_h = _to_float(parts[3])

    if width_mm is None or height_mm is None:
        return 1.0, 1.0
    if vb_w and vb_h and vb_w > 0 and vb_h > 0:
        return width_mm / vb_w, height_mm / vb_h
    return 1.0, 1.0


def _bbox_to_mm_dims(
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    scale_x: float,
    scale_y: float,
) -> tuple[float, float] | None:
    width_mm = (max_x - min_x) * scale_x
    height_mm = (max_y - min_y) * scale_y
    if width_mm < _MIN_PIECE_MM or height_mm < _MIN_PIECE_MM:
        return None
    return round(width_mm, 3), round(height_mm, 3)


def _resolve_mapped_letters_layer(
    layer_groups: list[tuple[str, str, ET.Element]],
    svg_layer_mappings: dict[str, str],
) -> tuple[str, str, ET.Element] | None:
    """Resolve letters layer only when explicitly mapped to volumetric template."""
    if not _letters_layer_is_mapped(svg_layer_mappings):
        return None
    for layer_id, layer_name, elem in layer_groups:
        if svg_layer_mappings.get(layer_name) == LETTERS_TEMPLATE_CODE:
            return layer_id, layer_name, elem
    for layer_id, layer_name, elem in layer_groups:
        if svg_layer_mappings.get(layer_id) == LETTERS_TEMPLATE_CODE:
            return layer_id, layer_name, elem
    return None


def _user_unit_bboxes_from_node(node: ET.Element) -> list[tuple[float, float, float, float]]:
    tag = _local_name(node.tag)
    if tag == "rect":
        x = _to_float(node.attrib.get("x")) or 0.0
        y = _to_float(node.attrib.get("y")) or 0.0
        w = _to_float(node.attrib.get("width"))
        h = _to_float(node.attrib.get("height"))
        if w is None or h is None or w <= 0 or h <= 0:
            return []
        return [(x, y, x + w, y + h)]

    if tag == "path":
        d_attr = node.attrib.get("d")
        if not d_attr or not str(d_attr).strip():
            return []
        return extract_letter_subpath_bboxes(str(d_attr))

    if tag in {"polygon", "polyline"}:
        points = _parse_points(node.attrib.get("points"))
        if len(points) < 3:
            return []
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return [(min(xs), min(ys), max(xs), max(ys))]

    if tag == "circle":
        cx = _to_float(node.attrib.get("cx")) or 0.0
        cy = _to_float(node.attrib.get("cy")) or 0.0
        r = _to_float(node.attrib.get("r"))
        if r is None or r <= 0:
            return []
        return [(cx - r, cy - r, cx + r, cy + r)]

    if tag == "ellipse":
        cx = _to_float(node.attrib.get("cx")) or 0.0
        cy = _to_float(node.attrib.get("cy")) or 0.0
        rx = _to_float(node.attrib.get("rx"))
        ry = _to_float(node.attrib.get("ry"))
        if rx is None or ry is None or rx <= 0 or ry <= 0:
            return []
        return [(cx - rx, cy - ry, cx + rx, cy + ry)]

    return []


def _collect_layer_piece_bboxes(layer_elem: ET.Element) -> list[tuple[float, float, float, float]]:
    boxes: list[tuple[float, float, float, float]] = []
    for node in layer_elem.iter():
        tag = _local_name(node.tag)
        if tag in _SKIP_TAGS or tag in {"svg", "g"}:
            continue
        boxes.extend(_user_unit_bboxes_from_node(node))
    return boxes


def extract_flat_material_pieces_from_svg(
    svg_text: str,
    *,
    svg_layer_mappings: dict[str, str] | None = None,
    primary_letters_layer_id: str | None = None,
) -> list[dict[str, Any]]:
    """Generic flat piece bboxes (mm) from a mapped letters SVG layer.

    ``primary_letters_layer_id`` is accepted for API compatibility but ignored
    unless the layer is present in ``svg_layer_mappings`` with target
    ``TPL-VOLUMETRIC-LETTERS``.
    """
    del primary_letters_layer_id  # mapping gate is authoritative
    if not svg_text or not svg_text.strip():
        return []

    mappings = svg_layer_mappings or {}
    if not _letters_layer_is_mapped(mappings):
        return []

    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return []

    if _local_name(root.tag) != "svg":
        return []

    layer_groups = _discover_layers(root)
    if not layer_groups:
        return []

    resolved = _resolve_mapped_letters_layer(layer_groups, mappings)
    if resolved is None:
        return []

    layer_id, _layer_name, layer_elem = resolved
    scale_x, scale_y = _document_scale_factors(root)
    user_boxes = _collect_layer_piece_bboxes(layer_elem)
    if not user_boxes:
        return []

    pieces: list[dict[str, Any]] = []
    for index, (min_x, min_y, max_x, max_y) in enumerate(user_boxes[: _MAX_PIECES]):
        dims = _bbox_to_mm_dims(min_x, min_y, max_x, max_y, scale_x, scale_y)
        if dims is None:
            continue
        width_mm, height_mm = dims
        piece_id = f"letter_{layer_id}_{index + 1:03d}"
        pieces.append(
            {
                "piece_id": piece_id,
                "width_mm": width_mm,
                "height_mm": height_mm,
                "source": "svg_layer_mapped",
                "source_layer_id": layer_id,
                "confidence": "measured",
            }
        )

    return pieces


def extract_letter_bounding_boxes_from_svg(
    svg_text: str,
    *,
    svg_layer_mappings: dict[str, str] | None = None,
    primary_letters_layer_id: str | None = None,
) -> list[dict[str, Any]]:
    """Face-vinyl alias for :func:`extract_flat_material_pieces_from_svg`."""
    return extract_flat_material_pieces_from_svg(
        svg_text,
        svg_layer_mappings=svg_layer_mappings,
        primary_letters_layer_id=primary_letters_layer_id,
    )
