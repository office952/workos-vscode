"""Classify nest2 parts into real letters vs inner holes for Intake V4 metrics.

Conceptually aligned with SVG Analyzer / nest2 subpath-shape-grouping: outer contours
are production letters; inner holes contribute to cutting perimeter but not letter count.
"""

from __future__ import annotations

from typing import Any

LETTER_PRODUCTION_ROLES = frozenset({"face"})
NON_PRODUCTION_PART_ROLES = frozenset(
    {
        "printed_artwork",
        "logo",
        "policromie",
        "backing",
        "return",
        "bevel",
        "inner_hole",
        "support_panel",
        "bond_panel",
        "frame",
        "vinyl",
        "ignore",
        "reference",
    }
)

BBOX_CONTAINMENT_TOLERANCE_MM = 0.5
HOLE_AREA_RATIO_MAX = 0.85


def _positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _positive_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _confirmed_role(layer_setup: dict[str, Any], layer_id: str, layer_name: str) -> str | None:
    layers = layer_setup.get("layers")
    if not isinstance(layers, list):
        return None
    for entry in layers:
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("layer_key") or "")
        lid = str(entry.get("layer_id") or "")
        lname = str(entry.get("layer_name") or "")
        if key not in {layer_id, layer_name} and lid != layer_id and lname != layer_name:
            continue
        if entry.get("confirmation_state") == "ignored":
            return None
        return str(entry.get("confirmed_role") or entry.get("auto_role") or "unknown")
    return None


def _part_bounds(item: dict[str, Any]) -> dict[str, float] | None:
    bounds = item.get("bounds")
    if not isinstance(bounds, dict):
        return None
    x = bounds.get("xMm")
    y = bounds.get("yMm")
    width = bounds.get("widthMm")
    height = bounds.get("heightMm")
    if x is None or y is None or width is None or height is None:
        return None
    try:
        return {
            "x": float(x),
            "y": float(y),
            "width": float(width),
            "height": float(height),
        }
    except (TypeError, ValueError):
        return None


def _bbox_area(bounds: dict[str, float] | None) -> float:
    if not bounds:
        return 0.0
    return max(0.0, bounds["width"] * bounds["height"])


def _bbox_contains(
    outer: dict[str, float],
    inner: dict[str, float],
    *,
    tolerance_mm: float = BBOX_CONTAINMENT_TOLERANCE_MM,
) -> bool:
    return (
        inner["x"] >= outer["x"] - tolerance_mm
        and inner["y"] >= outer["y"] - tolerance_mm
        and inner["x"] + inner["width"] <= outer["x"] + outer["width"] + tolerance_mm
        and inner["y"] + inner["height"] <= outer["y"] + outer["height"] + tolerance_mm
    )


def _part_geometry(item: dict[str, Any]) -> dict[str, Any]:
    geometry = item.get("geometry")
    return geometry if isinstance(geometry, dict) else {}


def _part_role(item: dict[str, Any], layer_setup: dict[str, Any]) -> str:
    source = item.get("source")
    if not isinstance(source, dict):
        return "unknown"
    layer_id = str(source.get("layerId") or "")
    layer_name = str(source.get("layerName") or layer_id)
    return _confirmed_role(layer_setup, layer_id, layer_name) or "unknown"


def _is_orphan_hole_candidate(
    inner_item: dict[str, Any],
    outer_item: dict[str, Any],
) -> bool:
    inner_bounds = _part_bounds(inner_item)
    outer_bounds = _part_bounds(outer_item)
    if not inner_bounds or not outer_bounds:
        return False
    if inner_item.get("id") == outer_item.get("id"):
        return False
    inner_area = _bbox_area(inner_bounds)
    outer_area = _bbox_area(outer_bounds)
    if inner_area <= 0 or outer_area <= 0:
        return False
    if inner_area >= outer_area * HOLE_AREA_RATIO_MAX:
        return False
    return _bbox_contains(outer_bounds, inner_bounds)


def classify_letter_parts_from_analysis(
    svg_analysis_json: dict[str, Any],
    layer_role_setup: dict[str, Any],
) -> dict[str, Any]:
    """Return per-part classification rows and aggregate production metrics."""
    parts = svg_analysis_json.get("parts")
    items: list[dict[str, Any]] = []
    if isinstance(parts, dict) and isinstance(parts.get("items"), list):
        items = [item for item in parts["items"] if isinstance(item, dict)]

    warnings: list[str] = []
    classification_confidence = "high"

    split_diag = parts.get("splitDiagnostics") if isinstance(parts, dict) else None
    subpath_diag: list[dict[str, Any]] = []
    if isinstance(split_diag, dict) and isinstance(split_diag.get("subPathDiagnostics"), list):
        subpath_diag = [row for row in split_diag["subPathDiagnostics"] if isinstance(row, dict)]
        if any(row.get("classification") == "ambiguous" for row in subpath_diag):
            classification_confidence = "low"
            warnings.append("SUBPATH_CONTAINMENT_AMBIGUOUS — unele contururi interioare pot fi incorect clasificate.")

    rows: list[dict[str, Any]] = []
    face_items: list[dict[str, Any]] = []

    for item in items:
        role = _part_role(item, layer_role_setup)
        source = item.get("source") if isinstance(item.get("source"), dict) else {}
        layer_name = str(source.get("layerName") or source.get("layerId") or "")
        geometry = _part_geometry(item)
        bounds = _part_bounds(item)
        inner_count = _positive_int(item.get("innerContourCount")) or 0
        outer_count = _positive_int(item.get("outerContourCount")) or 0
        contour_count = _positive_int(item.get("contourCount")) or 0

        is_face_production = role in LETTER_PRODUCTION_ROLES
        is_non_production = role in NON_PRODUCTION_PART_ROLES or role == "unknown"

        row = {
            "part_id": str(item.get("id") or ""),
            "source_layer": layer_name,
            "role": role,
            "bounds": bounds,
            "area": _bbox_area(bounds),
            "perimeter": _positive(geometry.get("totalContourPerimeterMm")),
            "outer_perimeter_mm": _positive(geometry.get("outerPerimeterMm")),
            "inner_perimeter_mm": _positive(geometry.get("innerPerimeterMm")),
            "embedded_inner_hole_count": inner_count if is_face_production else 0,
            "is_closed": contour_count > 0,
            "is_outer_contour": outer_count > 0 and inner_count == 0,
            "is_inner_hole": False,
            "parent_part_id": None,
            "nestable": bool(item.get("canNest")) and is_face_production,
            "counts_as_letter": False,
            "counts_as_material_piece": False,
            "counts_for_cutting_perimeter": False,
            "classification_confidence": classification_confidence,
        }
        rows.append(row)

        if is_face_production:
            face_items.append(item)
        elif is_non_production and role != "unknown":
            row["nestable"] = False

    orphan_hole_ids: set[str] = set()
    parent_by_hole: dict[str, str] = {}

    by_layer: dict[str, list[dict[str, Any]]] = {}
    for item in face_items:
        source = item.get("source") if isinstance(item.get("source"), dict) else {}
        layer_name = str(source.get("layerName") or source.get("layerId") or "")
        by_layer.setdefault(layer_name, []).append(item)

    for layer_items in by_layer.values():
        sorted_items = sorted(
            layer_items,
            key=lambda candidate: _bbox_area(_part_bounds(candidate)),
            reverse=True,
        )
        for index, candidate in enumerate(sorted_items):
            candidate_bounds = _part_bounds(candidate)
            if not candidate_bounds:
                continue
            for outer in sorted_items[:index]:
                if _is_orphan_hole_candidate(candidate, outer):
                    orphan_hole_ids.add(str(candidate.get("id") or ""))
                    parent_by_hole[str(candidate.get("id") or "")] = str(outer.get("id") or "")
                    classification_confidence = "low"
                    warnings.append(
                        f"Part {candidate.get('id')} reclassified as inner hole inside {outer.get('id')}."
                    )
                    break

    real_letter_items = [
        item for item in face_items if str(item.get("id") or "") not in orphan_hole_ids
    ]

    embedded_inner_holes = 0
    outer_perimeter_mm = 0.0
    inner_perimeter_mm = 0.0
    cutting_perimeter_mm = 0.0
    material_area_sqm = 0.0
    cutting_contours_count = 0

    for item in real_letter_items:
        geometry = _part_geometry(item)
        embedded_inner_holes += _positive_int(item.get("innerContourCount")) or 0
        outer_perimeter_mm += _positive(geometry.get("outerPerimeterMm")) or 0.0
        inner_perimeter_mm += _positive(geometry.get("innerPerimeterMm")) or 0.0
        cutting_perimeter_mm += _positive(geometry.get("totalContourPerimeterMm")) or 0.0
        bounds = _part_bounds(item)
        material_area_sqm += _bbox_area(bounds) / 1_000_000.0
        cutting_contours_count += _positive_int(item.get("contourCount")) or 0

    orphan_inner_holes = len(orphan_hole_ids)
    for item in face_items:
        if str(item.get("id") or "") not in orphan_hole_ids:
            continue
        geometry = _part_geometry(item)
        inner_perimeter_mm += _positive(geometry.get("outerPerimeterMm")) or _positive(geometry.get("totalContourPerimeterMm")) or 0.0
        cutting_perimeter_mm += _positive(geometry.get("totalContourPerimeterMm")) or _positive(geometry.get("outerPerimeterMm")) or 0.0
        cutting_contours_count += max(_positive_int(item.get("contourCount")) or 0, 1)

    inner_holes_count = embedded_inner_holes + orphan_inner_holes
    real_letters_count = len(real_letter_items)
    material_piece_count = real_letters_count

    row_by_id = {row["part_id"]: row for row in rows}
    for item in real_letter_items:
        row = row_by_id.get(str(item.get("id") or ""))
        if not row:
            continue
        row["counts_as_letter"] = True
        row["counts_as_material_piece"] = True
        row["counts_for_cutting_perimeter"] = True
        row["nestable"] = bool(item.get("canNest"))

    for hole_id in orphan_hole_ids:
        row = row_by_id.get(hole_id)
        if not row:
            continue
        row["is_inner_hole"] = True
        row["is_outer_contour"] = False
        row["parent_part_id"] = parent_by_hole.get(hole_id)
        row["counts_as_letter"] = False
        row["counts_as_material_piece"] = False
        row["counts_for_cutting_perimeter"] = True
        row["nestable"] = False

    for item in items:
        part_id = str(item.get("id") or "")
        row = row_by_id.get(part_id)
        if not row:
            continue
        role = row["role"]
        if role in NON_PRODUCTION_PART_ROLES or (role == "unknown" and part_id not in orphan_hole_ids):
            row["counts_as_letter"] = False
            row["counts_as_material_piece"] = False
            if role in {"printed_artwork", "logo", "policromie"}:
                row["nestable"] = False
                row["counts_for_cutting_perimeter"] = False

    if not items:
        nestable = _positive_int(parts.get("nestableCount") if isinstance(parts, dict) else None)
        count = _positive_int(parts.get("count") if isinstance(parts, dict) else None)
        real_letters_count = nestable or count or 0
        material_piece_count = real_letters_count
        cutting_contours_count = count or real_letters_count
        classification_confidence = "low"
        warnings.append("PART_ITEMS_MISSING — folosim agregate nest2 fără clasificare per-part.")

    layer_summary = _build_layer_summary(rows, layer_role_setup)

    return {
        "parts": rows,
        "real_letters_count": real_letters_count,
        "inner_holes_count": inner_holes_count,
        "cutting_contours_count": cutting_contours_count,
        "material_piece_count": material_piece_count,
        "child_parts_count": len(face_items),
        "outer_perimeter_mm": round(outer_perimeter_mm, 6) if outer_perimeter_mm > 0 else None,
        "hole_perimeter_mm": round(inner_perimeter_mm, 6) if inner_perimeter_mm > 0 else None,
        "cutting_perimeter_mm": round(cutting_perimeter_mm, 6) if cutting_perimeter_mm > 0 else None,
        "material_area_sqm": round(material_area_sqm, 6) if material_area_sqm > 0 else None,
        "classification_confidence": classification_confidence,
        "warnings": warnings,
        "layer_summary": layer_summary,
    }


def _build_layer_summary(
    rows: list[dict[str, Any]],
    layer_role_setup: dict[str, Any],
) -> list[dict[str, Any]]:
    by_layer: dict[str, dict[str, Any]] = {}
    for row in rows:
        layer_name = str(row.get("source_layer") or "")
        if not layer_name:
            continue
        role = row.get("role")
        if role not in LETTER_PRODUCTION_ROLES:
            continue
        bucket = by_layer.setdefault(
            layer_name,
            {
                "layer_name": layer_name,
                "outer_contours_count": 0,
                "inner_holes_count": 0,
                "real_letters_count": 0,
                "cutting_contours_count": 0,
                "material_piece_count": 0,
                "cutting_perimeter_total_mm": 0.0,
                "outer_perimeter_total_mm": 0.0,
                "hole_perimeter_total_mm": 0.0,
                "area_material_sqm": 0.0,
            },
        )
        if row.get("is_inner_hole"):
            bucket["inner_holes_count"] += 1
            bucket["hole_perimeter_total_mm"] += row.get("inner_perimeter_mm") or row.get("perimeter") or 0.0
            bucket["cutting_perimeter_total_mm"] += row.get("perimeter") or 0.0
            continue
        if row.get("counts_as_letter"):
            bucket["real_letters_count"] += 1
            bucket["material_piece_count"] += 1
            bucket["outer_contours_count"] += 1
            bucket["inner_holes_count"] += row.get("embedded_inner_hole_count") or 0
            bucket["outer_perimeter_total_mm"] += row.get("outer_perimeter_mm") or 0.0
            bucket["hole_perimeter_total_mm"] += row.get("inner_perimeter_mm") or 0.0
            bucket["cutting_perimeter_total_mm"] += row.get("perimeter") or 0.0
            bucket["area_material_sqm"] += (row.get("area") or 0.0) / 1_000_000.0

    for bucket in by_layer.values():
        bucket["cutting_contours_count"] = bucket["real_letters_count"] + bucket["inner_holes_count"]

    _ = layer_role_setup
    return list(by_layer.values())
