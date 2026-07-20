"""Measure AcmPanel production path lengths from DXF (SPLINE-capable).

Read-only geometry measurement — not a Pricing owner.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from services.acm_aci_semantic_mapping import (
    ACM_ACI_SEMANTIC_MAPPING_VERSION,
    classify_aci_color,
    mapping_metadata,
)

# SPLINE flattening distance (mm). Chosen to reproduce owner golden lengths.
SPLINE_FLATTENING_DISTANCE_MM = 0.01
# Compare tolerance for golden tests (mm on totals converted via /1000 → ml).
LENGTH_COMPARE_TOLERANCE_ML = 5e-5  # 0.05 mm


def _require_ezdxf():
    try:
        import ezdxf
        from ezdxf import path as ezpath
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "ezdxf is required for AcmPanel DXF measurement "
            "(install via backend requirements-dev.txt)."
        ) from exc
    return ezdxf, ezpath


def measure_spline_length_mm(entity: Any, *, flattening_distance_mm: float = SPLINE_FLATTENING_DISTANCE_MM) -> float | None:
    _, ezpath = _require_ezdxf()
    try:
        p = ezpath.make_path(entity)
        pts = list(p.flattening(flattening_distance_mm))
    except Exception:
        return None
    if len(pts) < 2:
        return None
    total = 0.0
    for i in range(1, len(pts)):
        total += math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y)
    return total


def measure_entity_length_mm(entity: Any) -> float | None:
    dxftype = entity.dxftype()
    if dxftype == "SPLINE":
        return measure_spline_length_mm(entity)
    if dxftype == "LINE":
        s, e = entity.dxf.start, entity.dxf.end
        return math.hypot(e.x - s.x, e.y - s.y)
    if dxftype == "LWPOLYLINE":
        pts = [(p[0], p[1]) for p in entity.get_points("xy")]
        if len(pts) < 2:
            return None
        total = 0.0
        for i in range(1, len(pts)):
            total += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        if bool(entity.closed):
            total += math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
        return total
    if dxftype == "ARC":
        r = float(entity.dxf.radius)
        start = math.radians(float(entity.dxf.start_angle))
        end = math.radians(float(entity.dxf.end_angle))
        sweep = end - start
        while sweep <= 0:
            sweep += 2 * math.pi
        return abs(r * sweep)
    return None


def measure_dxf_production_paths(path: str | Path) -> dict[str, Any]:
    """Measure CUT / V L1 / V L2 lengths from a DXF file using ACI semantic mapping."""
    ezdxf, _ = _require_ezdxf()
    file_path = Path(path)
    doc = ezdxf.readfile(str(file_path))
    msp = doc.modelspace()

    cut_mm = 0.0
    v_l1_mm = 0.0
    v_l2_mm = 0.0
    unknown_mm = 0.0
    warnings: list[str] = []
    entity_trace: list[dict[str, Any]] = []
    unknown_colors: set[int] = set()

    for idx, entity in enumerate(msp):
        color = int(getattr(entity.dxf, "color", 256) or 256)
        layer = str(getattr(entity.dxf, "layer", "") or "")
        semantic = classify_aci_color(color)
        length_mm = measure_entity_length_mm(entity)
        row = {
            "index": idx,
            "type": entity.dxftype(),
            "layer": layer,
            "aci_color": color,
            "semantic": semantic,
            "length_mm": None if length_mm is None else round(length_mm, 6),
        }
        entity_trace.append(row)
        if length_mm is None:
            warnings.append(f"unmeasured_entity:{entity.dxftype()}:idx={idx}:color={color}")
            continue
        if semantic == "CUT":
            cut_mm += length_mm
        elif semantic == "V_GROOVE_L1":
            v_l1_mm += length_mm
        elif semantic == "V_GROOVE_L2":
            v_l2_mm += length_mm
        else:
            unknown_mm += length_mm
            unknown_colors.add(color)
            warnings.append(f"unknown_aci_color:{color}:length_mm={round(length_mm, 6)}")

    cut_ml = round(cut_mm / 1000.0, 6)
    v_l1_ml = round(v_l1_mm / 1000.0, 6)
    v_l2_ml = round(v_l2_mm / 1000.0, 6)
    v_total_ml = round(v_l1_ml + v_l2_ml, 6)

    status = "measured"
    if cut_ml <= 0 and v_total_ml <= 0:
        status = "unavailable"
        warnings.append("no_classified_cut_or_v_groove_entities")

    return {
        "schema": "acm_panel_production_geometry_metrics_v1",
        "measurement_source": "imported_dxf",
        "measurement_status": status,
        "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
        "semantic_mapping": mapping_metadata(),
        "source_file": file_path.name,
        "insunits": doc.header.get("$INSUNITS"),
        "cut_length_ml": cut_ml,
        "v_groove_l1_ml": v_l1_ml,
        "v_groove_l2_ml": v_l2_ml,
        "v_groove_total_ml": v_total_ml,
        "unknown_length_ml": round(unknown_mm / 1000.0, 6),
        "unknown_aci_colors": sorted(unknown_colors),
        "warnings": list(dict.fromkeys(warnings)),
        "entity_trace": entity_trace,
        "flattening_distance_mm": SPLINE_FLATTENING_DISTANCE_MM,
        "compare_tolerance_ml": LENGTH_COMPARE_TOLERANCE_ML,
    }
