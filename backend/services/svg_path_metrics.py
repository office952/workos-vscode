"""SVG path `d` metrics — subpath length, closed area, bbox (user units).

Approximate curve sampling for quote estimation (not CNC-exact).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PathPoint:
    x: float
    y: float


@dataclass(frozen=True)
class PathSubpathMetrics:
    closed: bool
    length: float
    area: float
    point_count: int
    bbox_min_x: float | None = None
    bbox_min_y: float | None = None
    bbox_max_x: float | None = None
    bbox_max_y: float | None = None


@dataclass(frozen=True)
class PathMetricsResult:
    subpaths: list[PathSubpathMetrics] = field(default_factory=list)
    total_length: float = 0.0
    total_closed_area: float = 0.0
    subpath_count: int = 0
    bbox_min_x: float | None = None
    bbox_min_y: float | None = None
    bbox_max_x: float | None = None
    bbox_max_y: float | None = None
    warnings: list[str] = field(default_factory=list)


_CMD_RE = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])")
_NUM_RE = re.compile(r"-?\d*\.?\d+(?:e[-+]?\d+)?", re.IGNORECASE)

_CUBIC_STEPS = 16
_QUAD_STEPS = 12

MIN_LETTER_SUBPATH_LENGTH_USER = 5.0


def _tokenize_path(d: str) -> list[str]:
    normalized = _CMD_RE.sub(r" \1 ", d).replace(",", " ")
    tokens: list[str] = []
    for part in normalized.split():
        part = part.strip()
        if not part:
            continue
        if len(part) == 1 and part.isalpha():
            tokens.append(part)
        elif _NUM_RE.fullmatch(part):
            tokens.append(part)
    return tokens


def _dist(a: PathPoint, b: PathPoint) -> float:
    return math.hypot(b.x - a.x, b.y - a.y)


def _shoelace_area(points: list[PathPoint]) -> float:
    if len(points) < 3:
        return 0.0
    total = 0.0
    for i in range(len(points)):
        j = (i + 1) % len(points)
        total += points[i].x * points[j].y - points[j].x * points[i].y
    return abs(total) * 0.5


def _cubic_at(p0: PathPoint, p1: PathPoint, p2: PathPoint, p3: PathPoint, t: float) -> PathPoint:
    u = 1.0 - t
    return PathPoint(
        x=u * u * u * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t * t * t * p3.x,
        y=u * u * u * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t * t * t * p3.y,
    )


def _flatten_cubic(
    p0: PathPoint, p1: PathPoint, p2: PathPoint, p3: PathPoint, steps: int = _CUBIC_STEPS
) -> list[PathPoint]:
    return [_cubic_at(p0, p1, p2, p3, i / steps) for i in range(1, steps + 1)]


def _flatten_quadratic(
    p0: PathPoint, p1: PathPoint, p2: PathPoint, steps: int = _QUAD_STEPS
) -> list[PathPoint]:
    pts: list[PathPoint] = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1.0 - t
        pts.append(
            PathPoint(
                x=u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x,
                y=u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y,
            )
        )
    return pts


def _polyline_length(points: list[PathPoint], closed: bool) -> float:
    if len(points) < 2:
        return 0.0
    total = sum(_dist(points[i - 1], points[i]) for i in range(1, len(points)))
    if closed:
        total += _dist(points[-1], points[0])
    return total


def _bbox_expand(
    min_x: float | None,
    min_y: float | None,
    max_x: float | None,
    max_y: float | None,
    x: float,
    y: float,
) -> tuple[float | None, float | None, float | None, float | None]:
    if min_x is None:
        return x, y, x, y
    return min(min_x, x), min(min_y, y), max(max_x, x), max(max_y, y)


def parse_path_metrics(d: str) -> PathMetricsResult:
    warnings: list[str] = []
    tokens = _tokenize_path(d)
    i = 0
    cmd = ""
    cx = 0.0
    cy = 0.0
    subpath_start = PathPoint(0.0, 0.0)
    current: list[PathPoint] = []
    subpaths: list[PathSubpathMetrics] = []

    min_x: float | None = None
    min_y: float | None = None
    max_x: float | None = None
    max_y: float | None = None

    def track_point(x: float, y: float) -> None:
        nonlocal min_x, min_y, max_x, max_y
        min_x, min_y, max_x, max_y = _bbox_expand(min_x, min_y, max_x, max_y, x, y)

    def read_num() -> float:
        nonlocal i
        if i >= len(tokens):
            return 0.0
        try:
            v = float(tokens[i])
        except ValueError:
            v = 0.0
        i += 1
        return v

    def finish_subpath(closed: bool) -> None:
        nonlocal current
        if len(current) < 2:
            current = []
            return
        length = _polyline_length(current, closed)
        area = _shoelace_area(current) if closed else 0.0
        xs = [p.x for p in current]
        ys = [p.y for p in current]
        subpaths.append(
            PathSubpathMetrics(
                closed=closed,
                length=length,
                area=area,
                point_count=len(current),
                bbox_min_x=min(xs) if xs else None,
                bbox_min_y=min(ys) if ys else None,
                bbox_max_x=max(xs) if xs else None,
                bbox_max_y=max(ys) if ys else None,
            )
        )
        current = []

    def start_subpath(x: float, y: float) -> None:
        nonlocal cx, cy, subpath_start, current
        finish_subpath(False)
        cx, cy = x, y
        subpath_start = PathPoint(x, y)
        current = [PathPoint(x, y)]
        track_point(x, y)

    while i < len(tokens):
        t = tokens[i]
        if len(t) == 1 and t.isalpha():
            cmd = t
            i += 1
            if cmd.upper() == "Z":
                finish_subpath(True)
                cx, cy = subpath_start.x, subpath_start.y
                cmd = ""
            continue

        if not cmd:
            i += 1
            continue

        rel = cmd == cmd.lower()
        c = cmd.upper()

        try:
            if c == "M":
                x = read_num()
                y = read_num()
                ax = cx + x if rel else x
                ay = cy + y if rel else y
                start_subpath(ax, ay)
                cmd = "l" if rel else "L"
            elif c == "L":
                x = read_num()
                y = read_num()
                p = PathPoint(cx + x if rel else x, cy + y if rel else y)
                current.append(p)
                cx, cy = p.x, p.y
                track_point(p.x, p.y)
            elif c == "H":
                x = read_num()
                p = PathPoint(cx + x if rel else x, cy)
                current.append(p)
                cx = p.x
                track_point(p.x, p.y)
            elif c == "V":
                y = read_num()
                p = PathPoint(cx, cy + y if rel else y)
                current.append(p)
                cy = p.y
                track_point(p.x, p.y)
            elif c == "C":
                x1 = read_num()
                y1 = read_num()
                x2 = read_num()
                y2 = read_num()
                x = read_num()
                y = read_num()
                p0 = PathPoint(cx, cy)
                p1 = PathPoint(cx + x1 if rel else x1, cy + y1 if rel else y1)
                p2 = PathPoint(cx + x2 if rel else x2, cy + y2 if rel else y2)
                p3 = PathPoint(cx + x if rel else x, cy + y if rel else y)
                for pt in _flatten_cubic(p0, p1, p2, p3):
                    current.append(pt)
                    track_point(pt.x, pt.y)
                cx, cy = p3.x, p3.y
                warnings.append("path_curve_metrics_approximate")
            elif c == "Q":
                x1 = read_num()
                y1 = read_num()
                x = read_num()
                y = read_num()
                p0 = PathPoint(cx, cy)
                p1 = PathPoint(cx + x1 if rel else x1, cy + y1 if rel else y1)
                p2 = PathPoint(cx + x if rel else x, cy + y if rel else y)
                for pt in _flatten_quadratic(p0, p1, p2):
                    current.append(pt)
                    track_point(pt.x, pt.y)
                cx, cy = p2.x, p2.y
                warnings.append("path_curve_metrics_approximate")
            elif c in {"S", "T"}:
                warnings.append(f"path_command_{c}_linearized")
                x = read_num()
                y = read_num()
                p = PathPoint(cx + x if rel else x, cy + y if rel else y)
                current.append(p)
                cx, cy = p.x, p.y
                track_point(p.x, p.y)
            elif c == "A":
                read_num()
                read_num()
                read_num()
                read_num()
                read_num()
                x = read_num()
                y = read_num()
                p = PathPoint(cx + x if rel else x, cy + y if rel else y)
                current.append(p)
                cx, cy = p.x, p.y
                track_point(p.x, p.y)
                warnings.append("path_arc_metrics_approximate")
            else:
                warnings.append(f"unsupported_path_command:{c}")
                i += 1
        except (IndexError, ValueError):
            warnings.append("path_parse_partial")
            break

    finish_subpath(False)

    total_length = sum(s.length for s in subpaths)
    total_closed_area = sum(s.area for s in subpaths if s.closed)

    deduped_warnings = list(dict.fromkeys(warnings))

    return PathMetricsResult(
        subpaths=subpaths,
        total_length=total_length,
        total_closed_area=total_closed_area,
        subpath_count=len(subpaths),
        bbox_min_x=min_x,
        bbox_min_y=min_y,
        bbox_max_x=max_x,
        bbox_max_y=max_y,
        warnings=deduped_warnings,
    )


def estimate_letter_count_from_subpaths(
    subpaths: list[PathSubpathMetrics],
    min_length: float = MIN_LETTER_SUBPATH_LENGTH_USER,
) -> int:
    return sum(
        1
        for s in subpaths
        if s.length >= min_length and s.point_count >= 3
    )


def extract_letter_subpath_bboxes(
    d: str,
    *,
    min_length: float = MIN_LETTER_SUBPATH_LENGTH_USER,
) -> list[tuple[float, float, float, float]]:
    """Return (min_x, min_y, max_x, max_y) user-unit bboxes for letter-like subpaths."""
    parsed = parse_path_metrics(d)
    boxes: list[tuple[float, float, float, float]] = []
    for subpath in parsed.subpaths:
        if subpath.point_count < 3 or subpath.length < min_length:
            continue
        if (
            subpath.bbox_min_x is None
            or subpath.bbox_min_y is None
            or subpath.bbox_max_x is None
            or subpath.bbox_max_y is None
        ):
            continue
        if subpath.bbox_max_x <= subpath.bbox_min_x or subpath.bbox_max_y <= subpath.bbox_min_y:
            continue
        boxes.append(
            (
                subpath.bbox_min_x,
                subpath.bbox_min_y,
                subpath.bbox_max_x,
                subpath.bbox_max_y,
            )
        )
    return boxes
