"""Intake V3 safe SVG validation and raw analysis — no JS execution, no network, no disk storage."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from fastapi import HTTPException, status

from schemas.intake_v3 import RawSvgAnalysis, RawSvgObject, VectorAsset
from services.svg_metrics_service import _MAX_SVG_BYTES
from services.work_intake_svg_spec_mapper import sanitize_upload_filename

# Warning / rejection codes (raw analysis only — not production truth)
WARNING_MISSING_VIEW_BOX = "MISSING_VIEW_BOX"
WARNING_MISSING_WIDTH_HEIGHT = "MISSING_WIDTH_HEIGHT"
WARNING_EXTERNAL_REFERENCES = "EXTERNAL_REFERENCES"
WARNING_RASTER_IMAGE_EMBEDDED = "RASTER_IMAGE_EMBEDDED"
WARNING_TEXT_NOT_CONVERTED_TO_PATHS = "TEXT_NOT_CONVERTED_TO_PATHS"
WARNING_TOO_MANY_PATHS = "TOO_MANY_PATHS"
WARNING_UNKNOWN_UNITS = "UNKNOWN_UNITS"

_MAX_PATH_COUNT_WARNING = 2000
_EXTERNAL_HREF_PATTERN = re.compile(
    r'(?:xlink:href|href)\s*=\s*["\']\s*https?://',
    re.IGNORECASE,
)
_SCRIPT_PATTERN = re.compile(r"<\s*script\b", re.IGNORECASE)
_COLOR_FROM_STYLE = re.compile(
    r"(?:fill|stroke)\s*:\s*([^;}\s]+)",
    re.IGNORECASE,
)
_PATH_CLOSE_PATTERN = re.compile(r"[Zz]")
_UNIT_PATTERN = re.compile(r"^\s*[\d.]+\s*(mm|cm|in|pt|pc|px|%)\s*$", re.IGNORECASE)


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


def _normalize_color(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned or cleaned.lower() in {"none", "transparent", "currentcolor"}:
        return None
    return cleaned


def _extract_colors_from_style(style: str | None) -> list[str]:
    if not style:
        return []
    colors: list[str] = []
    for match in _COLOR_FROM_STYLE.finditer(style):
        color = _normalize_color(match.group(1))
        if color:
            colors.append(color)
    return colors


def _path_is_closed(d_attr: str | None) -> bool:
    if not d_attr:
        return False
    return bool(_PATH_CLOSE_PATTERN.search(d_attr))


def _estimate_hole_count(groups: list[str], paths_closed: int) -> int:
    hole_groups = sum(
        1
        for group_id in groups
        if any(token in group_id.lower() for token in ("hole", "inner", "counter"))
    )
    return max(hole_groups, 0) if hole_groups else max(0, paths_closed // 4)


def _compute_confidence(warnings: list[str], path_count: int) -> float:
    score = 1.0
    if WARNING_MISSING_VIEW_BOX in warnings:
        score -= 0.15
    if WARNING_MISSING_WIDTH_HEIGHT in warnings:
        score -= 0.1
    if WARNING_TEXT_NOT_CONVERTED_TO_PATHS in warnings:
        score -= 0.2
    if WARNING_EXTERNAL_REFERENCES in warnings:
        score -= 0.25
    if WARNING_RASTER_IMAGE_EMBEDDED in warnings:
        score -= 0.15
    if WARNING_TOO_MANY_PATHS in warnings:
        score -= 0.2
    if WARNING_UNKNOWN_UNITS in warnings:
        score -= 0.05
    if path_count == 0:
        score -= 0.3
    return max(0.1, min(1.0, round(score, 2)))


@dataclass(frozen=True)
class SvgUploadValidationResult:
    file_name: str
    file_size_bytes: int
    svg_text: str
    file_hash: str
    mime_type: str


def validate_svg_upload(
    *,
    raw_name: str,
    content_type: str | None,
    raw_bytes: bytes,
) -> SvgUploadValidationResult:
    """Validate upload bytes before analysis. Raises HTTPException on reject."""
    try:
        file_name = sanitize_upload_filename(raw_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_svg", "message": str(exc)},
        ) from exc

    mime = (content_type or "").strip().lower()
    if mime and "svg" not in mime and mime != "application/octet-stream":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_svg", "message": f"Unsupported MIME type: {mime}"},
        )

    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_svg", "message": "Uploaded file is empty."},
        )

    if len(raw_bytes) > _MAX_SVG_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "svg_too_large",
                "message": f"File exceeds limit of {_MAX_SVG_BYTES} bytes.",
                "max_bytes": _MAX_SVG_BYTES,
            },
        )

    try:
        svg_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_svg", "message": "SVG must be UTF-8 text."},
        ) from exc

    if "<svg" not in svg_text.lower():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_svg", "message": "Content does not appear to be SVG."},
        )

    if _SCRIPT_PATTERN.search(svg_text):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "svg_scripts_forbidden", "message": "SVG contains <script> elements."},
        )

    if _EXTERNAL_HREF_PATTERN.search(svg_text):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "svg_external_references",
                "message": "SVG contains external http(s) href references.",
            },
        )

    file_hash = hashlib.sha256(raw_bytes).hexdigest()
    return SvgUploadValidationResult(
        file_name=file_name,
        file_size_bytes=len(raw_bytes),
        svg_text=svg_text,
        file_hash=file_hash,
        mime_type=mime or "image/svg+xml",
    )


def analyze_svg_content(
    *,
    file_name: str,
    file_size_bytes: int,
    svg_text: str,
) -> tuple[RawSvgAnalysis, VectorAsset]:
    """Parse SVG safely and return raw analysis facts (not confirmed production model)."""
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_svg_xml", "message": f"Invalid SVG XML: {exc}"},
        ) from exc

    if _local_tag(root.tag) != "svg":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_svg", "message": "Root element must be <svg>."},
        )

    warnings: list[str] = []
    colors: set[str] = set()
    detected_groups: list[str] = []
    raw_objects: list[RawSvgObject] = []

    view_box = _attr(root, "viewBox") or _attr(root, "viewbox")
    svg_width = _attr(root, "width")
    svg_height = _attr(root, "height")

    if not view_box:
        warnings.append(WARNING_MISSING_VIEW_BOX)
    if not svg_width or not svg_height:
        warnings.append(WARNING_MISSING_WIDTH_HEIGHT)

    for dim in (svg_width, svg_height):
        if dim and not _UNIT_PATTERN.match(dim):
            warnings.append(WARNING_UNKNOWN_UNITS)
            break

    path_count = 0
    closed_path_count = 0
    polygon_count = 0
    rect_count = 0
    text_count = 0
    image_count = 0

    for elem in root.iter():
        tag = _local_tag(elem.tag)

        if tag == "g":
            group_id = _attr(elem, "id")
            if group_id:
                detected_groups.append(group_id)

        if tag == "text":
            text_count += 1

        if tag == "image":
            image_count += 1

        if tag == "path":
            path_count += 1
            d_attr = _attr(elem, "d")
            is_closed = _path_is_closed(d_attr)
            if is_closed:
                closed_path_count += 1

            fill = _normalize_color(_attr(elem, "fill"))
            stroke = _normalize_color(_attr(elem, "stroke"))
            style_colors = _extract_colors_from_style(_attr(elem, "style"))
            for color in (fill, stroke, *style_colors):
                if color:
                    colors.add(color)

            object_id = _attr(elem, "id") or f"path-{path_count}"
            raw_objects.append(
                RawSvgObject(
                    object_id=object_id,
                    object_type="path",
                    raw_role_guess="letter_candidate" if is_closed else "unknown",
                    fill=fill,
                    stroke=stroke,
                    closed_contours=1 if is_closed else 0,
                    color=fill or stroke,
                    layer_name=_attr(elem, "data-name"),
                    confidence=0.6 if is_closed else 0.4,
                )
            )

        elif tag == "polygon":
            polygon_count += 1
            fill = _normalize_color(_attr(elem, "fill"))
            if fill:
                colors.add(fill)
            raw_objects.append(
                RawSvgObject(
                    object_id=_attr(elem, "id") or f"polygon-{polygon_count}",
                    object_type="polygon",
                    raw_role_guess="letter_candidate",
                    fill=fill,
                    closed_contours=1,
                    color=fill,
                )
            )

        elif tag == "rect":
            rect_count += 1
            fill = _normalize_color(_attr(elem, "fill"))
            if fill:
                colors.add(fill)

    open_path_count = max(0, path_count - closed_path_count)
    raw_object_count = path_count + polygon_count + rect_count

    if text_count > 0:
        warnings.append(WARNING_TEXT_NOT_CONVERTED_TO_PATHS)
    if image_count > 0:
        warnings.append(WARNING_RASTER_IMAGE_EMBEDDED)
    if path_count > _MAX_PATH_COUNT_WARNING:
        warnings.append(WARNING_TOO_MANY_PATHS)

    estimated_inner_hole_count = _estimate_hole_count(detected_groups, closed_path_count)
    confidence = _compute_confidence(warnings, path_count)

    analysis = RawSvgAnalysis(
        file_name=file_name,
        file_size_bytes=file_size_bytes,
        svg_width=svg_width,
        svg_height=svg_height,
        path_count=path_count,
        polygon_count=polygon_count,
        rect_count=rect_count,
        closed_contour_count=closed_path_count,
        open_path_count=open_path_count,
        raw_object_count=raw_object_count,
        estimated_inner_hole_count=estimated_inner_hole_count,
        detected_color_count=len(colors),
        detected_groups=detected_groups,
        view_box=view_box,
        warnings=warnings,
        confidence=confidence,
        raw_objects=raw_objects[:50],
    )

    vector_asset = VectorAsset(
        file_name=file_name,
        file_hash=None,  # set by caller after hash computed
        mime_type="image/svg+xml",
        source="intake_v3_upload",
        view_box=view_box,
        upload_status="parsed",
    )

    return analysis, vector_asset


def build_vector_asset_from_validation(
    validation: SvgUploadValidationResult,
    analysis: RawSvgAnalysis,
) -> VectorAsset:
    return VectorAsset(
        file_name=validation.file_name,
        file_hash=validation.file_hash,
        mime_type=validation.mime_type,
        source="intake_v3_upload",
        view_box=analysis.view_box,
        upload_status="parsed",
    )
