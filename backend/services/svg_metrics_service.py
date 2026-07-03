from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from services.svg_path_metrics import parse_path_metrics


_MAX_SVG_BYTES = 500000
_MAX_XML_NODES = 5000

_UNIT_TO_MM = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "in": 25.4,
    "pt": 25.4 / 72.0,
    "pc": 25.4 / 6.0,
    "px": 25.4 / 96.0,
}

_LENGTH_RE = re.compile(r"^\s*([+-]?(?:\d+\.?\d*|\d*\.\d+))(mm|cm|m|in|pt|pc|px)?\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class SvgMetrics:
    bbox_w_mm: float | None = None
    bbox_h_mm: float | None = None
    area_mm2_approx: float | None = None
    perimeter_mm_approx: float | None = None


@dataclass(frozen=True)
class SvgParseResult:
    parse_status: str
    warnings: list[str] = field(default_factory=list)
    error_code: str | None = None
    error_detail: str | None = None
    metrics: SvgMetrics = SvgMetrics()
    metrics_version: str = "v2-path-metrics"


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_points(raw: str | None) -> list[tuple[float, float]]:
    if not raw:
        return []
    tokens = re.split(r"[\s,]+", raw.strip())
    vals: list[float] = []
    for t in tokens:
        if not t:
            continue
        try:
            vals.append(float(t))
        except ValueError:
            return []
    if len(vals) < 4:
        return []
    if len(vals) % 2 == 1:
        vals = vals[:-1]
    pts: list[tuple[float, float]] = []
    for idx in range(0, len(vals), 2):
        pts.append((vals[idx], vals[idx + 1]))
    return pts


def _line_length(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def _polygon_area(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5


def _polygon_perimeter(points: list[tuple[float, float]], close_shape: bool) -> float:
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(len(points) - 1):
        total += _line_length(points[i], points[i + 1])
    if close_shape:
        total += _line_length(points[-1], points[0])
    return total


class SvgMetricsService:
    @staticmethod
    def _parse_length_mm(value: str | None, warnings: list[str]) -> float | None:
        if value is None:
            return None
        m = _LENGTH_RE.match(value)
        if not m:
            return None
        numeric = float(m.group(1))
        unit = (m.group(2) or "").lower()
        if not unit:
            warnings.append("document_units_assumed_mm")
            return numeric
        if unit not in _UNIT_TO_MM:
            return None
        return numeric * _UNIT_TO_MM[unit]

    @classmethod
    def parse_svg_metrics(cls, svg_text: str, *, max_bytes: int = _MAX_SVG_BYTES, max_nodes: int = _MAX_XML_NODES) -> SvgParseResult:
        if not isinstance(svg_text, str) or not svg_text.strip():
            return SvgParseResult(parse_status="failed", error_code="empty_input", error_detail="SVG content is empty")

        raw_bytes = svg_text.encode("utf-8", errors="ignore")
        if len(raw_bytes) > max_bytes:
            return SvgParseResult(
                parse_status="failed",
                error_code="input_too_large",
                error_detail=f"SVG exceeds max bytes limit ({max_bytes})",
            )

        lowered = svg_text.lower()
        if "<!doctype" in lowered or "<!entity" in lowered:
            return SvgParseResult(
                parse_status="failed",
                error_code="xml_unsafe_construct",
                error_detail="DTD/ENTITY declarations are not allowed",
            )

        try:
            root = ET.fromstring(svg_text)
        except ET.ParseError as exc:
            return SvgParseResult(
                parse_status="failed",
                error_code="invalid_xml",
                error_detail=str(exc),
            )

        if _local_name(root.tag) != "svg":
            return SvgParseResult(
                parse_status="failed",
                error_code="not_svg_root",
                error_detail="Root element must be <svg>",
            )

        nodes = list(root.iter())
        if len(nodes) > max_nodes:
            return SvgParseResult(
                parse_status="failed",
                error_code="node_limit_exceeded",
                error_detail=f"SVG node count exceeds limit ({max_nodes})",
            )

        warnings: list[str] = []
        warning_set: set[str] = set()

        def _warn(code: str) -> None:
            if code not in warning_set:
                warning_set.add(code)
                warnings.append(code)

        width_mm = cls._parse_length_mm(root.attrib.get("width"), warnings)
        height_mm = cls._parse_length_mm(root.attrib.get("height"), warnings)

        vb = root.attrib.get("viewBox")
        vb_w: float | None = None
        vb_h: float | None = None
        if vb:
            parts = re.split(r"[\s,]+", vb.strip())
            if len(parts) == 4:
                vb_w = _to_float(parts[2])
                vb_h = _to_float(parts[3])

        min_x: float | None = None
        min_y: float | None = None
        max_x: float | None = None
        max_y: float | None = None
        area = 0.0
        perimeter = 0.0

        def _bbox_update(x0: float, y0: float, x1: float, y1: float) -> None:
            nonlocal min_x, min_y, max_x, max_y
            lo_x = min(x0, x1)
            lo_y = min(y0, y1)
            hi_x = max(x0, x1)
            hi_y = max(y0, y1)
            min_x = lo_x if min_x is None else min(min_x, lo_x)
            min_y = lo_y if min_y is None else min(min_y, lo_y)
            max_x = hi_x if max_x is None else max(max_x, hi_x)
            max_y = hi_y if max_y is None else max(max_y, hi_y)

        used_viewbox_fallback = False

        for node in nodes:
            tag = _local_name(node.tag)
            if tag in {"svg", "g", "metadata", "defs", "title", "desc"}:
                continue

            if tag == "rect":
                x = _to_float(node.attrib.get("x")) or 0.0
                y = _to_float(node.attrib.get("y")) or 0.0
                w = _to_float(node.attrib.get("width"))
                h = _to_float(node.attrib.get("height"))
                if w is None or h is None or w <= 0 or h <= 0:
                    _warn("invalid_rect_dimensions")
                    continue
                _bbox_update(x, y, x + w, y + h)
                area += w * h
                perimeter += 2.0 * (w + h)
                continue

            if tag == "circle":
                cx = _to_float(node.attrib.get("cx")) or 0.0
                cy = _to_float(node.attrib.get("cy")) or 0.0
                r = _to_float(node.attrib.get("r"))
                if r is None or r <= 0:
                    _warn("invalid_circle_radius")
                    continue
                _bbox_update(cx - r, cy - r, cx + r, cy + r)
                area += math.pi * r * r
                perimeter += 2.0 * math.pi * r
                continue

            if tag == "ellipse":
                cx = _to_float(node.attrib.get("cx")) or 0.0
                cy = _to_float(node.attrib.get("cy")) or 0.0
                rx = _to_float(node.attrib.get("rx"))
                ry = _to_float(node.attrib.get("ry"))
                if rx is None or ry is None or rx <= 0 or ry <= 0:
                    _warn("invalid_ellipse_radius")
                    continue
                _bbox_update(cx - rx, cy - ry, cx + rx, cy + ry)
                area += math.pi * rx * ry
                perimeter += 2.0 * math.pi * math.sqrt((rx * rx + ry * ry) / 2.0)
                continue

            if tag == "line":
                x1 = _to_float(node.attrib.get("x1")) or 0.0
                y1 = _to_float(node.attrib.get("y1")) or 0.0
                x2 = _to_float(node.attrib.get("x2")) or 0.0
                y2 = _to_float(node.attrib.get("y2")) or 0.0
                _bbox_update(x1, y1, x2, y2)
                perimeter += _line_length((x1, y1), (x2, y2))
                continue

            if tag in {"polyline", "polygon"}:
                points = _parse_points(node.attrib.get("points"))
                if not points:
                    _warn(f"invalid_{tag}_points")
                    continue
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                _bbox_update(min(xs), min(ys), max(xs), max(ys))
                if tag == "polygon":
                    area += _polygon_area(points)
                perimeter += _polygon_perimeter(points, close_shape=(tag == "polygon"))
                continue

            if tag == "path":
                d_attr = node.attrib.get("d")
                if not d_attr or not str(d_attr).strip():
                    _warn("invalid_path_d")
                    continue
                pm = parse_path_metrics(str(d_attr))
                for code in pm.warnings:
                    _warn(code)
                if (
                    pm.bbox_min_x is None
                    or pm.bbox_min_y is None
                    or pm.bbox_max_x is None
                    or pm.bbox_max_y is None
                    or pm.total_length <= 0
                ):
                    _warn("unsupported_path")
                    continue
                _bbox_update(pm.bbox_min_x, pm.bbox_min_y, pm.bbox_max_x, pm.bbox_max_y)
                area += pm.total_closed_area
                perimeter += pm.total_length
                continue

            _warn(f"unsupported_element:{tag}")

        if min_x is None or min_y is None or max_x is None or max_y is None:
            if vb_w is not None and vb_h is not None:
                min_x = 0.0
                min_y = 0.0
                max_x = vb_w
                max_y = vb_h
                used_viewbox_fallback = True
                _warn("viewbox_bbox_fallback")
            elif width_mm is not None and height_mm is not None:
                return SvgParseResult(
                    parse_status="parsed",
                    warnings=warnings,
                    metrics=SvgMetrics(
                        bbox_w_mm=round(width_mm, 6),
                        bbox_h_mm=round(height_mm, 6),
                        area_mm2_approx=None,
                        perimeter_mm_approx=None,
                    ),
                )
            else:
                return SvgParseResult(
                    parse_status="failed",
                    warnings=warnings,
                    error_code="no_supported_geometry",
                    error_detail="No supported SVG geometry elements were found",
                )

        span_w = max(0.0, (max_x - min_x))
        span_h = max(0.0, (max_y - min_y))

        # Supported element coordinates are interpreted in document units.
        if width_mm is None or height_mm is None:
            scale_x = 1.0
            scale_y = 1.0
            _warn("document_units_assumed_mm")
        elif vb_w and vb_h and vb_w > 0 and vb_h > 0:
            scale_x = width_mm / vb_w
            scale_y = height_mm / vb_h
        else:
            # No viewBox means one user unit follows the explicit width/height units.
            scale_x = 1.0
            scale_y = 1.0

        bbox_w_mm = span_w * scale_x
        bbox_h_mm = span_h * scale_y
        area_mm2_approx = area * scale_x * scale_y if perimeter > 0 or area > 0 else None
        perimeter_mm_approx = (
            perimeter * (scale_x + scale_y) / 2.0 if perimeter > 0 else None
        )
        if used_viewbox_fallback and perimeter <= 0:
            area_mm2_approx = None
            perimeter_mm_approx = None

        return SvgParseResult(
            parse_status="parsed",
            warnings=warnings,
            metrics=SvgMetrics(
                bbox_w_mm=round(bbox_w_mm, 6),
                bbox_h_mm=round(bbox_h_mm, 6),
                area_mm2_approx=(
                    round(area_mm2_approx, 6) if area_mm2_approx is not None else None
                ),
                perimeter_mm_approx=(
                    round(perimeter_mm_approx, 6)
                    if perimeter_mm_approx is not None
                    else None
                ),
            ),
        )
