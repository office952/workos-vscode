"""Server-side SVG geometry analyzer for Intake V5.

Parses SVG paths to extract:
- Document dimensions (mm)
- Letter groups by fill color (face area, perimeter, letter count)
- Artwork/outline groups (stroke-only paths)
- Totals for auto-populating V5 form inputs
"""

from __future__ import annotations

import re
import math
from io import StringIO
from xml.etree import ElementTree as ET
from typing import NamedTuple

from svgpathtools import parse_path, Path


# ── Helpers ──────────────────────────────────────────────────────────────────

_SVG_NS = "http://www.w3.org/2000/svg"
_NS = {"svg": _SVG_NS}
_SCRIPT_RE = re.compile(r"<script\b[^>]*>[\s\S]*?</script>", re.IGNORECASE)
_ENTITY_RE = re.compile(r"<!ENTITY", re.IGNORECASE)
_COLOR_NAME_MAP = {
    "#00a0e3": "blue",
    "#e31e24": "red",
    "#009846": "green",
    "#ef7f1a": "orange",
    "#ff0000": "red",
    "#00ff00": "green",
    "#0000ff": "blue",
    "#ffff00": "yellow",
    "#ffffff": "white",
    "#000000": "black",
}


class _PathInfo(NamedTuple):
    d: str
    fill: str | None
    stroke: str | None
    layer_name: str | None


def _color_label(hex_color: str) -> str:
    """Return a human label for a hex color."""
    key = hex_color.lower().strip()
    if key in _COLOR_NAME_MAP:
        return _COLOR_NAME_MAP[key]
    return hex_color


def _resolve_fill(el: ET.Element) -> str | None:
    """Get effective fill from attributes or inline style."""
    fill = el.get("fill")
    style = el.get("style", "")
    if style:
        m = re.search(r"fill\s*:\s*([^;]+)", style, re.IGNORECASE)
        if m:
            fill = m.group(1).strip()
    if fill and fill.lower() == "none":
        return None
    return fill


def _resolve_stroke(el: ET.Element) -> str | None:
    """Get effective stroke from attributes or inline style."""
    stroke = el.get("stroke")
    style = el.get("style", "")
    if style:
        m = re.search(r"stroke\s*:\s*([^;]+)", style, re.IGNORECASE)
        if m:
            stroke = m.group(1).strip()
    if stroke and stroke.lower() == "none":
        return None
    return stroke


# ── Scale detection ──────────────────────────────────────────────────────────

_UNIT_RE = re.compile(r"^([+-]?\d*\.?\d+(?:e[+-]?\d+)?)\s*(mm|cm|in|px|pt)?$", re.IGNORECASE)
_PX_PER_MM = 96.0 / 25.4


def _parse_length_mm(raw: str | None) -> float | None:
    """Parse an SVG length attribute to mm."""
    if not raw:
        return None
    m = _UNIT_RE.match(raw.strip())
    if not m:
        return None
    val = float(m.group(1))
    unit = (m.group(2) or "").lower()
    if unit == "mm":
        return val
    if unit == "cm":
        return val * 10.0
    if unit == "in":
        return val * 25.4
    if unit == "pt":
        return val * 25.4 / 72.0
    if unit == "px":
        return val / _PX_PER_MM
    # unitless — assume user units, need viewBox for scale
    return None


def _viewbox_tuple(raw: str | None) -> tuple[float, float, float, float] | None:
    if not raw:
        return None
    parts = re.split(r"[\s,]+", raw.strip())
    if len(parts) != 4:
        return None
    try:
        return tuple(float(p) for p in parts)  # type: ignore[return-value]
    except ValueError:
        return None


def _compute_scale(root: ET.Element) -> tuple[float, float, float | None, float | None]:
    """Return (scale_x, scale_y, width_mm, height_mm).

    scale converts viewBox user-units to mm.
    """
    w_raw = root.get("width")
    h_raw = root.get("height")
    vb = _viewbox_tuple(root.get("viewBox"))

    w_mm = _parse_length_mm(w_raw)
    h_mm = _parse_length_mm(h_raw)

    if vb:
        _, _, vb_w, vb_h = vb
        if w_mm and h_mm and vb_w > 0 and vb_h > 0:
            return w_mm / vb_w, h_mm / vb_h, w_mm, h_mm
        # No physical units — heuristic: if viewBox values > 200, likely mm/10 or mm
        if vb_w > 200:
            # CorelDRAW often uses mm in viewBox directly or mm*10
            # Try to detect: if w_raw has no unit, viewBox IS the physical size
            if w_raw and not _parse_length_mm(w_raw):
                # unitless width — could be viewBox units = user units
                try:
                    w_val = float(w_raw.strip().replace("px", ""))
                    h_val = float((h_raw or "0").strip().replace("px", ""))
                    if abs(w_val - vb_w) < 0.01:
                        # width == viewBox width → 1:1 mapping, assume mm
                        return 1.0, 1.0, vb_w, vb_h
                except ValueError:
                    pass
            # Fallback: assume viewBox in mm (CorelDRAW default)
            return 1.0, 1.0, vb_w, vb_h
        # Small viewBox values — assume px
        scale = 1.0 / _PX_PER_MM
        return scale, scale, vb_w * scale, vb_h * scale

    # No viewBox — use physical dimensions if available
    if w_mm and h_mm:
        return 1.0, 1.0, w_mm, h_mm

    return 1.0, 1.0, None, None


# ── SVG parsing & path extraction ────────────────────────────────────────────

def _sanitize_svg(raw: str) -> str:
    """Remove dangerous content from SVG string."""
    if _ENTITY_RE.search(raw):
        raise ValueError("SVG conține entități externe — respins.")
    text = _SCRIPT_RE.sub("", raw)
    return text


def _extract_paths(root: ET.Element) -> list[_PathInfo]:
    """Walk SVG tree and extract all <path> elements with fill/stroke/layer info."""
    paths: list[_PathInfo] = []

    def _walk(el: ET.Element, layer_name: str | None):
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag

        # Detect layer (SVG <g> with inkscape:label or id)
        current_layer = layer_name
        if tag == "g":
            label = (
                el.get("{http://www.inkscape.org/namespaces/inkscape}label")
                or el.get("id")
                or layer_name
            )
            current_layer = label

        if tag == "path":
            d = el.get("d")
            if d:
                paths.append(_PathInfo(
                    d=d,
                    fill=_resolve_fill(el),
                    stroke=_resolve_stroke(el),
                    layer_name=current_layer,
                ))

        for child in el:
            _walk(child, current_layer)

    _walk(root, None)
    return paths


# ── Geometry calculation ─────────────────────────────────────────────────────

def _path_metrics(d: str, scale_x: float, scale_y: float) -> dict:
    """Calculate path length and area using svgpathtools."""
    try:
        path = parse_path(d)
    except Exception:
        return {"length_mm": 0.0, "area_mm2": 0.0, "subpath_count": 0}

    avg_scale = (scale_x + scale_y) / 2.0
    area_scale = scale_x * scale_y

    # Total path length in user units → mm
    try:
        length_uu = path.length()
    except Exception:
        length_uu = 0.0
    length_mm = length_uu * avg_scale

    # Area via shoelace on flattened path (closed subpaths)
    area_mm2 = 0.0
    try:
        # svgpathtools doesn't have a direct area method for complex paths
        # Use enclosed_area for closed paths via Green's theorem approximation
        # For each continuous subpath, we'll check if it's closed and compute area
        area_uu = _shoelace_area_from_path(path)
        area_mm2 = abs(area_uu) * area_scale
    except Exception:
        pass

    # Count subpaths (separated by M commands)
    subpath_count = len(re.findall(r"[Mm]", d))

    return {
        "length_mm": length_mm,
        "area_mm2": area_mm2,
        "subpath_count": max(subpath_count, 1),
    }


def _shoelace_area_from_path(path: Path, num_samples: int = 200) -> float:
    """Approximate enclosed area using sampled points and shoelace formula."""
    if len(path) == 0:
        return 0.0

    # Find continuous subpaths
    subpaths = path.continuous_subpaths()
    total_area = 0.0

    for sp in subpaths:
        if not sp.isclosed():
            continue
        # Sample points along the subpath
        n = max(num_samples, len(sp) * 20)
        points = []
        try:
            for i in range(n):
                t = i / n
                pt = sp.point(t)
                points.append((pt.real, pt.imag))
        except Exception:
            continue

        if len(points) < 3:
            continue

        # Shoelace formula
        area = 0.0
        for i in range(len(points)):
            j = (i + 1) % len(points)
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        total_area += abs(area) * 0.5

    return total_area


# ── Main analysis function ───────────────────────────────────────────────────

class LetterGroup:
    """A group of paths sharing the same fill color."""
    def __init__(self, color: str, label: str):
        self.color = color
        self.label = label
        self.face_area_mm2: float = 0.0
        self.perimeter_mm: float = 0.0
        self.path_count: int = 0
        self.subpath_count: int = 0

    def to_dict(self) -> dict:
        return {
            "color": self.color,
            "label": self.label,
            "face_area_m2": round(self.face_area_mm2 / 1_000_000, 4),
            "perimeter_m": round(self.perimeter_mm / 1000, 3),
            "path_count": self.path_count,
            "subpath_count": self.subpath_count,
        }


class ArtworkGroup:
    """A stroke-only path group (outlines, mounting marks, logos)."""
    def __init__(self, label: str, stroke_color: str | None):
        self.label = label
        self.stroke_color = stroke_color
        self.perimeter_mm: float = 0.0
        self.path_count: int = 0

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "stroke_color": self.stroke_color,
            "perimeter_m": round(self.perimeter_mm / 1000, 3),
            "path_count": self.path_count,
        }


def analyze_svg(svg_content: str, filename: str = "upload.svg") -> dict:
    """Analyze an SVG file and extract geometry for V5 BOM calculation.

    Returns a dict with:
    - document: width_mm, height_mm
    - letter_groups: per-color group geometry
    - artwork_groups: stroke-only path geometry
    - totals: aggregated values for V5 form auto-fill
    """
    sanitized = _sanitize_svg(svg_content)
    root = ET.fromstring(sanitized)

    # Remove namespace prefix for easier access
    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if tag != "svg":
        raise ValueError("Fișierul nu este un SVG valid.")

    # Scale
    scale_x, scale_y, width_mm, height_mm = _compute_scale(root)

    # Extract paths
    all_paths = _extract_paths(root)

    # Group paths by fill color
    filled_groups: dict[str, LetterGroup] = {}
    artwork_groups: list[ArtworkGroup] = []
    artwork_idx = 0

    for pi in all_paths:
        metrics = _path_metrics(pi.d, scale_x, scale_y)

        if pi.fill and pi.fill.lower() not in ("none", "transparent"):
            # Filled path → letter group
            color_key = pi.fill.lower()
            if color_key not in filled_groups:
                label = _color_label(color_key)
                filled_groups[color_key] = LetterGroup(
                    color=pi.fill,
                    label=f"Grup litere ({label})",
                )
            grp = filled_groups[color_key]
            grp.face_area_mm2 += metrics["area_mm2"]
            grp.perimeter_mm += metrics["length_mm"]
            grp.path_count += 1
            grp.subpath_count += metrics["subpath_count"]
        elif pi.stroke and pi.stroke.lower() not in ("none", "transparent"):
            # Stroke-only → artwork/outline
            artwork_idx += 1
            name = pi.layer_name or f"Outline {artwork_idx}"
            ag = ArtworkGroup(label=name, stroke_color=pi.stroke)
            ag.perimeter_mm = metrics["length_mm"]
            ag.path_count = 1
            artwork_groups.append(ag)

    # Build totals
    total_face_area_mm2 = sum(g.face_area_mm2 for g in filled_groups.values())
    total_perimeter_mm = sum(g.perimeter_mm for g in filled_groups.values())
    total_artwork_perimeter_mm = sum(a.perimeter_mm for a in artwork_groups)
    total_letter_count = sum(g.subpath_count for g in filled_groups.values())

    return {
        "filename": filename,
        "document": {
            "width_mm": round(width_mm, 1) if width_mm else None,
            "height_mm": round(height_mm, 1) if height_mm else None,
        },
        "letter_groups": [g.to_dict() for g in filled_groups.values()],
        "artwork_groups": [a.to_dict() for a in artwork_groups],
        "totals": {
            "letter_group_count": len(filled_groups),
            "letter_count": total_letter_count,
            "letter_face_area_m2": round(total_face_area_mm2 / 1_000_000, 4),
            "letter_perimeter_m": round(total_perimeter_mm / 1000, 3),
            "artwork_count": len(artwork_groups),
            "artwork_perimeter_m": round(total_artwork_perimeter_mm / 1000, 3),
            "total_perimeter_m": round((total_perimeter_mm + total_artwork_perimeter_mm) / 1000, 3),
        },
    }
