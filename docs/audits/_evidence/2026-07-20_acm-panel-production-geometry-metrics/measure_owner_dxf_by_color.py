"""Read-only owner DXF measurement — SPLINE by ACI color (Plan Mode)."""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import ezdxf
from ezdxf import path as ezpath

FILES = [
    Path(r"C:\Users\offic\Desktop\un-pliu.dxf"),
    Path(r"C:\Users\offic\Desktop\2-pliuri-100x30.dxf"),
]
OUT = Path(__file__).with_name("dxf-measure-by-color.json")


def approx_len(entity):
    p = ezpath.make_path(entity)
    pts = list(p.flattening(0.01))
    if len(pts) < 2:
        return None, []
    total = 0.0
    xy = []
    for i, pt in enumerate(pts):
        xy.append((pt.x, pt.y))
        if i:
            total += math.hypot(pt.x - pts[i - 1].x, pt.y - pts[i - 1].y)
    return total, xy


def analyze(path: Path) -> dict:
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    by_color: dict[int, dict] = defaultdict(lambda: {"count": 0, "length_mm": 0.0})
    all_pts = []
    rows = []
    for idx, e in enumerate(msp):
        color = int(getattr(e.dxf, "color", 256) or 256)
        length, pts = approx_len(e)
        by_color[color]["count"] += 1
        if length is not None:
            by_color[color]["length_mm"] += length
        all_pts.extend(pts)
        rows.append(
            {
                "i": idx,
                "type": e.dxftype(),
                "color": color,
                "degree": getattr(e.dxf, "degree", None),
                "closed": bool(getattr(e, "closed", False)),
                "length_mm": None if length is None else round(length, 6),
                "bbox": None
                if not pts
                else {
                    "w": round(max(p[0] for p in pts) - min(p[0] for p in pts), 6),
                    "h": round(max(p[1] for p in pts) - min(p[1] for p in pts), 6),
                    "min_x": round(min(p[0] for p in pts), 6),
                    "min_y": round(min(p[1] for p in pts), 6),
                    "max_x": round(max(p[0] for p in pts), 6),
                    "max_y": round(max(p[1] for p in pts), 6),
                },
            }
        )
    bbox = None
    if all_pts:
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        bbox = {
            "min_x": round(min(xs), 6),
            "min_y": round(min(ys), 6),
            "max_x": round(max(xs), 6),
            "max_y": round(max(ys), 6),
            "width": round(max(xs) - min(xs), 6),
            "height": round(max(ys) - min(ys), 6),
        }
    colors = {
        str(k): {
            "count": v["count"],
            "length_mm": round(v["length_mm"], 6),
            "length_ml": round(v["length_mm"] / 1000.0, 6),
        }
        for k, v in sorted(by_color.items())
    }
    total = sum(v["length_mm"] for v in by_color.values())
    return {
        "file": path.name,
        "insunits": doc.header.get("$INSUNITS"),
        "insunits_meaning": "mm" if doc.header.get("$INSUNITS") == 4 else str(doc.header.get("$INSUNITS")),
        "entity_count": len(rows),
        "envelope_bbox_mm": bbox,
        "by_color": colors,
        "total_length_mm": round(total, 6),
        "total_length_ml": round(total / 1000.0, 6),
        "entities": rows,
    }


def main() -> None:
    out = [analyze(p) for p in FILES]
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
