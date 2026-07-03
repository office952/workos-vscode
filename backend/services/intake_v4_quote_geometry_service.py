"""Merge nest2 svg_analysis_json quote metrics into path_geometry_summary for V4."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from services.intake_v4_letter_part_classification_service import classify_letter_parts_from_analysis

if TYPE_CHECKING:
    from schemas.intake_v4 import IntakeV4WorkspacePayload

LETTER_FACE_ROLES = frozenset({"face"})
ARTWORK_ROLES = frozenset({"printed_artwork", "logo", "policromie"})


def _positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
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


def build_quote_geometry_from_analysis(
    svg_analysis_json: dict[str, Any],
    layer_role_setup: dict[str, Any],
) -> dict[str, Any]:
    """Derive quote metrics from nest2 JSON + operator-confirmed roles."""
    layers = svg_analysis_json.get("layers")
    if not isinstance(layers, list):
        layers = []

    face_perimeter_ml = 0.0
    face_area_sqm = 0.0
    artwork_area_sqm = 0.0
    artwork_boxes: list[dict[str, Any]] = []
    face_layer_count = 0
    primary_key: str | None = None

    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_id = str(layer.get("id") or "")
        layer_name = str(layer.get("name") or layer_id)
        role = _confirmed_role(layer_role_setup, layer_id, layer_name)
        area = _positive(layer.get("filledAreaSqm")) or _positive(layer.get("boundingAreaSqm"))

        if role in ARTWORK_ROLES:
            if area:
                artwork_area_sqm += area
            artwork_boxes.append(
                {
                    "layer_key": layer_id or layer_name,
                    "layer_name": layer_name,
                    "width_mm": _positive(layer.get("widthMm")),
                    "height_mm": _positive(layer.get("heightMm")),
                    "area_m2": round(area, 4) if area else None,
                }
            )
            continue

        if role not in LETTER_FACE_ROLES:
            continue

        perimeter_ml = _positive(layer.get("perimeterMl"))
        if perimeter_ml is None:
            perimeter_mm = _positive(layer.get("perimeterMm"))
            perimeter_ml = perimeter_mm / 1000 if perimeter_mm else None
        if perimeter_ml:
            face_perimeter_ml += perimeter_ml
            face_layer_count += 1
            if primary_key is None:
                primary_key = layer_id or layer_name

        area = _positive(layer.get("filledAreaSqm")) or _positive(layer.get("boundingAreaSqm"))
        if area:
            face_area_sqm += area

    classification = classify_letter_parts_from_analysis(svg_analysis_json, layer_role_setup)
    real_letters_count = classification.get("real_letters_count")
    letter_count: int | None = None
    if isinstance(real_letters_count, int) and real_letters_count > 0:
        letter_count = real_letters_count
    elif face_layer_count > 0:
        letter_count = face_layer_count

    document = svg_analysis_json.get("document")
    width_mm = _positive(document.get("widthMm")) if isinstance(document, dict) else None
    height_mm = _positive(document.get("heightMm")) if isinstance(document, dict) else None

    geometry_source = "missing"
    letter_perimeter_m: float | None = None
    outer_perimeter_mm = classification.get("outer_perimeter_mm")
    hole_perimeter_mm = classification.get("hole_perimeter_mm")
    cutting_perimeter_mm = classification.get("cutting_perimeter_mm")

    if isinstance(outer_perimeter_mm, (int, float)) and outer_perimeter_mm > 0:
        letter_perimeter_m = round(float(outer_perimeter_mm) / 1000.0, 4)
        face_perimeter_ml = letter_perimeter_m
        geometry_source = "nest2_face_parts_outer"
    elif face_perimeter_ml > 0:
        letter_perimeter_m = round(face_perimeter_ml, 4)
        geometry_source = "nest2_face_layers"
    else:
        geometry_block = svg_analysis_json.get("geometry")
        if isinstance(geometry_block, dict):
            doc_perimeter_ml = _positive(geometry_block.get("perimeterMl"))
            if doc_perimeter_ml is None:
                doc_perimeter_mm = _positive(geometry_block.get("perimeterMm"))
                doc_perimeter_ml = doc_perimeter_mm / 1000 if doc_perimeter_mm else None
            if doc_perimeter_ml:
                letter_perimeter_m = round(doc_perimeter_ml, 4)
                face_perimeter_ml = doc_perimeter_ml
                geometry_source = "nest2_document_geometry"
                if isinstance(document, dict):
                    face_area_sqm = (
                        _positive(document.get("boundingAreaSqm"))
                        or _positive(document.get("filledAreaSqm"))
                        or 0.0
                    )

    confirmed = layer_role_setup.get("confirmation_status") == "complete"

    cutting_perimeter_ml = (
        round(float(cutting_perimeter_mm) / 1000.0, 4)
        if isinstance(cutting_perimeter_mm, (int, float)) and cutting_perimeter_mm > 0
        else None
    )
    hole_perimeter_ml = (
        round(float(hole_perimeter_mm) / 1000.0, 4)
        if isinstance(hole_perimeter_mm, (int, float)) and hole_perimeter_mm > 0
        else None
    )

    return {
        "letter_perimeter_m": letter_perimeter_m,
        "total_letter_perimeter_ml": round(face_perimeter_ml, 4) if face_perimeter_ml > 0 else None,
        "return_material_perimeter_ml": round(face_perimeter_ml, 4) if face_perimeter_ml > 0 else None,
        "face_cutting_perimeter_ml": cutting_perimeter_ml,
        "cutting_perimeter_ml": cutting_perimeter_ml,
        "hole_perimeter_ml": hole_perimeter_ml,
        "face_area_m2": round(face_area_sqm, 4) if face_area_sqm > 0 else None,
        "artwork_area_m2": round(artwork_area_sqm, 4) if artwork_area_sqm > 0 else None,
        "artwork_boxes": artwork_boxes,
        "letter_count": letter_count,
        "real_letters_count": letter_count,
        "inner_holes_count": classification.get("inner_holes_count"),
        "cutting_contours_count": classification.get("cutting_contours_count"),
        "material_piece_count": classification.get("material_piece_count"),
        "part_classification_confidence": classification.get("classification_confidence"),
        "part_classification_warnings": list(classification.get("warnings") or []),
        "primary_letters_layer_key": primary_key,
        "width_mm": width_mm,
        "height_mm": height_mm,
        "geometry_source": geometry_source,
        "confirmed": confirmed,
    }


def resolve_v4_quote_geometry(payload: "IntakeV4WorkspacePayload") -> dict[str, Any]:
    """Single canonical geometry derive for pricing, breakdown, and quote guards.

    When ``svg_analysis_json`` and ``layer_role_setup`` exist, metrics always come
    from ``build_quote_geometry_from_analysis`` — persisted ``quote_geometry`` is
    not treated as a parallel truth for dimensions/counts.
    """
    persisted: dict[str, Any] = (
        dict(payload.quote_geometry) if isinstance(payload.quote_geometry, dict) else {}
    )

    if not payload.svg_analysis_json or payload.layer_role_setup is None:
        return persisted

    derived = build_quote_geometry_from_analysis(
        payload.svg_analysis_json,
        payload.layer_role_setup.model_dump(mode="json"),
    )
    if payload.finish_setup is not None:
        from services.intake_v4_volumetric_return_metrics_service import enrich_quote_geometry_with_volumetric_return

        derived = enrich_quote_geometry_with_volumetric_return(
            derived,
            finish_setup=payload.finish_setup.model_dump(mode="json"),
            svg_analysis_json=payload.svg_analysis_json,
            layer_role_setup=payload.layer_role_setup.model_dump(mode="json"),
        )
    quote = dict(derived)
    if persisted.get("confirmed") is True and derived.get("confirmed"):
        quote["confirmed"] = True
    return quote


def merge_quote_geometry_into_path_summary(
    path_summary: dict[str, Any],
    quote_geometry: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(path_summary)
    mapping = {
        "letter_perimeter_m": "letter_perimeter_m",
        "total_letter_perimeter_ml": "total_letter_perimeter_ml",
        "return_material_perimeter_ml": "return_material_perimeter_ml",
        "face_cutting_perimeter_ml": "face_cutting_perimeter_ml",
        "cutting_perimeter_ml": "cutting_perimeter_ml",
        "hole_perimeter_ml": "hole_perimeter_ml",
        "face_area_m2": "face_area_m2",
        "letter_face_area_m2": "face_area_m2",
        "artwork_area_m2": "artwork_area_m2",
        "artwork_boxes": "artwork_boxes",
        "letter_count": "letter_count",
        "real_letters_count": "real_letters_count",
        "inner_holes_count": "inner_holes_count",
        "cutting_contours_count": "cutting_contours_count",
        "material_piece_count": "material_piece_count",
        "letter_return_perimeter_ml": "letter_return_perimeter_ml",
        "artwork_return_perimeter_ml": "artwork_return_perimeter_ml",
        "led_perimeter_ml": "led_perimeter_ml",
        "artwork_piece_count": "artwork_piece_count",
        "volumetric_piece_count": "volumetric_piece_count",
        "outer_letter_perimeter_ml": "outer_letter_perimeter_ml",
        "inner_hole_letter_perimeter_ml": "inner_hole_letter_perimeter_ml",
        "cnc_cutting_perimeter_ml": "cnc_cutting_perimeter_ml",
        "led_perimeter_ml": "led_perimeter_ml",
        "width_mm": "width_mm",
        "height_mm": "height_mm",
        "primary_letters_layer_key": "primary_letters_layer_key",
    }
    for target_key, source_key in mapping.items():
        value = quote_geometry.get(source_key)
        if value is not None:
            merged[target_key] = value
    return merged
