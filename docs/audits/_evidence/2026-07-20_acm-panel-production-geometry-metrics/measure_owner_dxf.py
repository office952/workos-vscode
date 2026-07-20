"""Read-only owner DXF measurement for Plan Mode — not a product dependency."""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import ezdxf
from ezdxf import path as ezpath
from ezdxf.math import Vec3


def _seg_len(a, b) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _polyline_len(points) -> float:
    pts = list(points)
    if len(pts) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(pts)):
        total += _seg_len(pts[i - 1], pts[i])
    return total


def _entity_length(entity) -> float | None:
    dxftype = entity.dxftype()
    if dxftype == "LINE":
        s, e = entity.dxf.start, entity.dxf.end
        return _seg_len((s.x, s.y), (e.x, e.y))
    if dxftype in {"LWPOLYLINE", "POLYLINE"}:
        try:
            if dxftype == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in entity.get_points("xy")]
                closed = bool(entity.closed)
            else:
                pts = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
                closed = bool(entity.is_closed)
            length = _polyline_len(pts)
            if closed and len(pts) >= 2:
                length += _seg_len(pts[-1], pts[0])
            return length
        except Exception:
            pass
    if dxftype == "ARC":
        r = float(entity.dxf.radius)
        start = math.radians(float(entity.dxf.start_angle))
        end = math.radians(float(entity.dxf.end_angle))
        sweep = end - start
        while sweep <= 0:
            sweep += 2 * math.pi
        return abs(r * sweep)
    if dxftype == "CIRCLE":
        return 2 * math.pi * float(entity.dxf.radius)
    if dxftype in {"SPLINE", "ELLIPSE"}:
        try:
            p = ezpath.make_path(entity)
            return float(p.approximate_length(segments=64))
        except Exception:
            return None
    return None


def _bbox_of_points(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if not xs:
        return None
    return {
        "min_x": min(xs),
        "min_y": min(ys),
        "max_x": max(xs),
        "max_y": max(ys),
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys),
    }


def analyze(path: Path) -> dict:
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    units = doc.header.get("$INSUNITS", None)
    layers = {}
    by_layer_len = defaultdict(float)
    by_layer_count = defaultdict(int)
    by_type = defaultdict(int)
    all_pts = []
    entity_rows = []

    for e in msp:
        t = e.dxftype()
        by_type[t] += 1
        layer = getattr(e.dxf, "layer", "0") or "0"
        length = _entity_length(e)
        by_layer_count[layer] += 1
        if length is not None:
            by_layer_len[layer] += length
        # collect points for bbox
        try:
            if t == "LINE":
                all_pts.append((e.dxf.start.x, e.dxf.start.y))
                all_pts.append((e.dxf.end.x, e.dxf.end.y))
            elif t == "LWPOLYLINE":
                for p in e.get_points("xy"):
                    all_pts.append((p[0], p[1]))
            elif t == "POLYLINE":
                for v in e.vertices:
                    all_pts.append((v.dxf.location.x, v.dxf.location.y))
        except Exception:
            pass
        entity_rows.append(
            {
                "type": t,
                "layer": layer,
                "length_mm": None if length is None else round(length, 6),
                "color": getattr(e.dxf, "color", None),
            }
        )

    # Heuristic layer classification by name
    cut_layers = []
    v1_layers = []
    v2_layers = []
    for layer in by_layer_len:
        name = layer.upper()
        if any(k in name for k in ("CUT", "DEBIT", "OUTLINE", "CONTUR", "MILL_CUT", "CNC_CUT")):
            cut_layers.append(layer)
        if any(k in name for k in ("V1", "L1", "GROOVE1", "V-GROOVE-L1", "VG1", "PLIU1", "FOLD1")):
            v1_layers.append(layer)
        if any(k in name for k in ("V2", "L2", "GROOVE2", "V-GROOVE-L2", "VG2", "PLIU2", "FOLD2")):
            v2_layers.append(layer)
        if "VGROOVE" in name.replace("-", "").replace("_", "") or "V_GROOVE" in name or "V-GROOVE" in name:
            if "2" in name or "L2" in name:
                v2_layers.append(layer)
            elif "1" in name or "L1" in name:
                v1_layers.append(layer)

    cut_layers = sorted(set(cut_layers))
    v1_layers = sorted(set(v1_layers))
    v2_layers = sorted(set(v2_layers))

    def sum_layers(names):
        return round(sum(by_layer_len[n] for n in names), 6)

    # Also report top layers by length for manual mapping
    top_layers = sorted(by_layer_len.items(), key=lambda kv: -kv[1])

    return {
        "file": str(path),
        "insunits": units,
        "entity_types": dict(by_type),
        "layer_lengths_mm": {k: round(v, 6) for k, v in top_layers},
        "layer_counts": dict(by_layer_count),
        "bbox_mm": _bbox_of_points(all_pts),
        "heuristic": {
            "cut_layers": cut_layers,
            "v_groove_l1_layers": v1_layers,
            "v_groove_l2_layers": v2_layers,
            "cut_length_mm": sum_layers(cut_layers) if cut_layers else None,
            "v_groove_l1_mm": sum_layers(v1_layers) if v1_layers else None,
            "v_groove_l2_mm": sum_layers(v2_layers) if v2_layers else None,
        },
        "total_all_entities_length_mm": round(sum(by_layer_len.values()), 6),
        "entity_sample": entity_rows[:40],
        "entity_count": len(entity_rows),
    }


def main():
    paths = [Path(p) for p in sys.argv[1:]]
    out = [analyze(p) for p in paths]
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
