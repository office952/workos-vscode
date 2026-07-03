"""Map server-side SVG analysis into intake product_spec_json vector_* fields."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

from services.svg_face_vinyl_pieces_service import extract_letter_bounding_boxes_from_svg
from services.svg_layer_analysis_service import (
    SvgLayerAnalysisResult,
    SvgLayerAnalysisRow,
    _discover_layers,
)
from services.svg_metrics_service import _local_name
from services.svg_path_metrics import estimate_letter_count_from_subpaths, parse_path_metrics

LETTERS_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"

_DRAWABLE_TAGS = frozenset(
    {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "use", "image"}
)

_TEMPLATE_TO_ROLE = {
    LETTERS_TEMPLATE_CODE: "volumetric_letters",
    "TPL-ACM-CASSETTED-PANEL": "support_panel",
    "TPL-CUT-ACM-LETTERS": "letter_face",
}

_TEMPLATE_TO_MAPPING_TARGET = {
    LETTERS_TEMPLATE_CODE: LETTERS_TEMPLATE_CODE,
    "TPL-ACM-CASSETTED-PANEL": "support_bars",
    "TPL-CUT-ACM-LETTERS": LETTERS_TEMPLATE_CODE,
}


def _count_drawable_elements(layer_elem: ET.Element) -> int:
    count = 0
    for node in layer_elem.iter():
        if _local_name(node.tag) in _DRAWABLE_TAGS:
            count += 1
    return max(count, 1)


def _suggest_role(layer_name: str, mapped_template_code: str | None, detected_kind: str) -> str:
    if mapped_template_code:
        return _TEMPLATE_TO_ROLE.get(mapped_template_code, "unknown")
    lowered = (layer_name or "").lower()
    if "structur" in lowered or "metal" in lowered or "cadru" in lowered:
        return "metal_frame"
    if "litere" in lowered or "volumetr" in lowered:
        return "volumetric_letters"
    if detected_kind == "template_code":
        return "volumetric_letters"
    return "unknown"


def _find_analysis_row_for_role(
    analysis: SvgLayerAnalysisResult,
    role: str,
) -> SvgLayerAnalysisRow | None:
    for row in analysis.layers:
        if _suggest_role(row.svg_layer_name, row.mapped_template_code, row.detected_kind) == role:
            return row
    return None


def _estimate_letter_count_for_layer(svg_text: str, layer_id: str) -> int | None:
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return None

    layer_elem = None
    for found_id, _layer_name, elem in _discover_layers(root):
        if found_id == layer_id:
            layer_elem = elem
            break
    if layer_elem is None:
        return None

    total = 0
    for node in layer_elem.iter():
        if _local_name(node.tag) != "path":
            continue
        d_attr = node.attrib.get("d")
        if not d_attr or not str(d_attr).strip():
            continue
        parsed = parse_path_metrics(str(d_attr))
        total += estimate_letter_count_from_subpaths(parsed.subpaths)
    return total if total > 0 else None


def _build_geometry_suggestion_fields(
    *,
    svg_text: str,
    analysis: SvgLayerAnalysisResult,
    primary_letters: dict[str, Any] | None,
) -> dict[str, Any]:
    """Map server layer analysis into vector_suggested_* fields for V2 geometry panel.

    Letter metrics and support/frame metrics are stored separately; only letter
    fields may feed TPL-VOLUMETRIC-LETTERS quote geometry (see
    docs/architecture/PRODUCT_TEMPLATE_COMPOSITION_DIRECTION.md).
    """
    letters_row = _find_analysis_row_for_role(analysis, "volumetric_letters")
    structure_row = _find_analysis_row_for_role(analysis, "metal_frame")

    if letters_row is None and primary_letters:
        letters_row = next(
            (row for row in analysis.layers if row.svg_layer_id == primary_letters.get("id")),
            None,
        )

    suggestions: dict[str, Any] = {}
    if letters_row and letters_row.metrics.metrics_confidence != "unavailable":
        metrics = letters_row.metrics
        if metrics.bbox_width_mm is not None:
            suggestions["vector_suggested_letter_layer_width_mm"] = metrics.bbox_width_mm
            suggestions["vector_suggested_assembly_width_mm"] = metrics.bbox_width_mm
        if metrics.bbox_height_mm is not None:
            suggestions["vector_suggested_letter_layer_height_mm"] = metrics.bbox_height_mm
            suggestions["vector_suggested_assembly_height_mm"] = metrics.bbox_height_mm
        if metrics.path_perimeter_m is not None:
            suggestions["vector_suggested_letter_perimeter_m"] = metrics.path_perimeter_m
        if metrics.path_area_m2 is not None:
            suggestions["vector_suggested_letter_face_area_m2"] = metrics.path_area_m2

        letter_count = letters_row.quote_input_suggestions.get("letter_count")
        if letter_count is None and primary_letters:
            letter_count = _estimate_letter_count_for_layer(svg_text, str(primary_letters["id"]))
        if letter_count is not None and int(letter_count) >= 1:
            suggestions["vector_suggested_letter_count"] = int(letter_count)

        if suggestions.get("vector_suggested_letter_perimeter_m"):
            suggestions["vector_geometry_confidence"] = "high"

    if structure_row and structure_row.metrics.metrics_confidence != "unavailable":
        sm = structure_row.metrics
        if sm.bbox_width_mm is not None:
            suggestions["vector_suggested_support_width_mm"] = sm.bbox_width_mm
            suggestions["vector_suggested_frame_width_mm"] = sm.bbox_width_mm
        if sm.bbox_height_mm is not None:
            suggestions["vector_suggested_support_height_mm"] = sm.bbox_height_mm
            suggestions["vector_suggested_frame_height_mm"] = sm.bbox_height_mm
        support_area = sm.bbox_area_m2 if sm.bbox_area_m2 is not None else sm.path_area_m2
        if support_area is not None:
            suggestions["vector_suggested_support_area_m2"] = support_area

    return suggestions


def _extract_svg_dimensions(svg_text: str) -> tuple[str | None, str | None, str | None]:
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return None, None, None
    if _local_name(root.tag) != "svg":
        return None, None, None
    width = (root.attrib.get("width") or "").strip() or None
    height = (root.attrib.get("height") or "").strip() or None
    viewbox = (root.attrib.get("viewBox") or root.attrib.get("viewbox") or "").strip() or None
    return width, height, viewbox


def build_vector_spec_updates(
    *,
    filename: str,
    size_bytes: int,
    content_type: str,
    svg_text: str,
    analysis: SvgLayerAnalysisResult,
    selected_at: str | None = None,
) -> dict[str, Any]:
    """Return flat vector_* fields to merge into product_spec_json."""
    selected_at = selected_at or datetime.now(timezone.utc).isoformat()
    extension = "svg"
    mime = content_type.strip() or "image/svg+xml"

    width, height, viewbox = _extract_svg_dimensions(svg_text)

    try:
        root = ET.fromstring(svg_text)
        layer_groups = _discover_layers(root)
        element_counts = {
            layer_id: _count_drawable_elements(layer_elem)
            for layer_id, _layer_name, layer_elem in layer_groups
        }
    except ET.ParseError:
        layer_groups = []
        element_counts = {}

    detected_layers: list[dict[str, Any]] = []
    detected_layers_summary: list[dict[str, Any]] = []
    svg_layer_mappings: dict[str, str] = {}
    warnings = list(analysis.warnings or [])

    for row in analysis.layers:
        role = _suggest_role(row.svg_layer_name, row.mapped_template_code, row.detected_kind)
        element_count = element_counts.get(row.svg_layer_id, 1)
        detected_layers.append(
            {
                "id": row.svg_layer_id,
                "label": row.svg_layer_name,
                "element_count": element_count,
                "suggested_role": role,
                "confirmed_role": role,
            }
        )
        summary_row: dict[str, Any] = {
            "layer_name": row.svg_layer_name,
            "mapping_status": row.mapping_status,
            "mapped_by": row.mapped_by,
            "mapped_target": _TEMPLATE_TO_MAPPING_TARGET.get(row.mapped_template_code or ""),
            "mapped_template_code": row.mapped_template_code,
            "detected_kind": row.detected_kind or None,
        }
        detected_layers_summary.append(summary_row)
        if row.mapped_template_code:
            target = _TEMPLATE_TO_MAPPING_TARGET.get(row.mapped_template_code)
            if target:
                svg_layer_mappings[row.svg_layer_name] = target

    parse_status = analysis.parse_status
    if parse_status not in {"parsed", "parsed_sanitized"}:
        parse_status = "failed"

    primary_letters = next(
        (layer for layer in detected_layers if layer["suggested_role"] == "volumetric_letters"),
        detected_layers[0] if detected_layers else None,
    )

    updates: dict[str, Any] = {
        "intake_input_pathway": "vector",
        "vector_file_present": True,
        "vector_file_name": filename,
        "vector_file_type": "svg",
        "vector_file_source": "server_upload",
        "vector_file_mime": mime,
        "vector_file_size_bytes": size_bytes,
        "vector_file_selected_at": selected_at,
        "vector_file_extension": extension,
        "vector_analysis_status": "analyzed",
        "vector_metrics_source": "svg_analysis",
        "vector_parse_status": parse_status,
        "vector_svg_analyzed": True,
        "vector_analysis_warnings": warnings or None,
        "vector_layer_analysis_warnings": warnings or None,
        "vector_detected_layer_count": len(detected_layers),
        "vector_detected_layers": detected_layers or None,
        "vector_detected_layers_summary": detected_layers_summary or None,
        "vector_layer_mapping_status": "mapped"
        if any(v == LETTERS_TEMPLATE_CODE for v in svg_layer_mappings.values())
        else "pending",
        "vector_geometry_analyzed": False,
    }

    if width:
        updates["vector_svg_width"] = width
    if height:
        updates["vector_svg_height"] = height
    if viewbox:
        updates["vector_svg_viewbox"] = viewbox
    if svg_layer_mappings:
        updates["svg_layer_mappings"] = svg_layer_mappings
    if primary_letters:
        updates["vector_primary_letters_layer_id"] = primary_letters["id"]
        updates["vector_primary_letters_layer_name"] = primary_letters["label"]
        updates["vector_letters_layer_suggestion_confidence"] = "medium"

    updates.update(
        _build_geometry_suggestion_fields(
            svg_text=svg_text,
            analysis=analysis,
            primary_letters=primary_letters,
        )
    )

    letter_boxes: list[dict[str, Any]] = []
    if any(v == LETTERS_TEMPLATE_CODE for v in svg_layer_mappings.values()):
        letter_boxes = extract_letter_bounding_boxes_from_svg(
            svg_text,
            svg_layer_mappings=svg_layer_mappings,
        )
    if letter_boxes:
        updates["letter_bounding_boxes"] = letter_boxes

    # Drop None values so merge does not overwrite with nulls.
    return {k: v for k, v in updates.items() if v is not None}


def sanitize_upload_filename(raw_name: str) -> str:
    base = (raw_name or "").strip().replace("\\", "/").split("/")[-1]
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    if not base.lower().endswith(".svg"):
        raise ValueError("Filename must end with .svg")
    if base in {"", ".", "..", ".svg"}:
        raise ValueError("Filename is not valid")
    return base
