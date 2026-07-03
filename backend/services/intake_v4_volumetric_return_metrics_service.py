"""Volumetric return / cant perimeter metrics — letters vs artwork with active return."""

from __future__ import annotations

from typing import Any

from services.intake_v4_letter_part_classification_service import classify_letter_parts_from_analysis

RETURN_INACTIVE_TOKENS = frozenset({"", "none", "no_return", "without_return"})
ARTWORK_ROLES = frozenset({"printed_artwork", "logo", "policromie"})


def return_finish_active(finish_type: str | None) -> bool:
    token = (finish_type or "").strip().lower()
    return token not in RETURN_INACTIVE_TOKENS


def _positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _layer_perimeter_ml(analysis: dict[str, Any], layer_key: str, layer_name: str) -> float | None:
    layers = analysis.get("layers")
    if not isinstance(layers, list):
        return None
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_id = str(layer.get("id") or "")
        name = str(layer.get("name") or layer_id)
        if layer_key not in {layer_id, name} and layer_name not in {layer_id, name}:
            continue
        perimeter_ml = _positive(layer.get("perimeterMl"))
        if perimeter_ml is None:
            perimeter_mm = _positive(layer.get("perimeterMm"))
            perimeter_ml = perimeter_mm / 1000 if perimeter_mm else None
        return perimeter_ml
    return None


def _artwork_outer_perimeter_ml(
    *,
    analysis: dict[str, Any],
    classification_parts: list[dict[str, Any]],
    layer_key: str,
    layer_name: str,
) -> float | None:
    total_mm = 0.0
    found = False
    for row in classification_parts:
        if row.get("role") not in ARTWORK_ROLES:
            continue
        if str(row.get("source_layer") or "") not in {layer_key, layer_name}:
            continue
        outer_mm = _positive(row.get("outer_perimeter_mm"))
        if outer_mm is None:
            outer_mm = _positive(row.get("perimeter"))
        if outer_mm:
            total_mm += outer_mm
            found = True
    if found:
        return round(total_mm / 1000.0, 6)
    return _layer_perimeter_ml(analysis, layer_key, layer_name)


def _face_layers_return_active(finish_setup: dict[str, Any]) -> bool:
    default_return = finish_setup.get("return_finish_type")
    letter_groups = finish_setup.get("letter_group_finishes") or []
    if letter_groups:
        return any(
            return_finish_active(str(group.get("return_finish_type") or default_return or ""))
            for group in letter_groups
            if isinstance(group, dict)
        )
    return return_finish_active(default_return)


def _letter_perimeter_metrics_from_classification(
    base_quote: dict[str, Any],
    classification: dict[str, Any],
) -> tuple[float | None, float | None, float | None]:
    """Return (outer_ml, inner_hole_ml, cutting_ml) for face letter production parts."""
    outer_mm = _positive(classification.get("outer_perimeter_mm"))
    inner_mm = _positive(classification.get("hole_perimeter_mm"))

    outer_ml = round(outer_mm / 1000.0, 6) if outer_mm else _positive(base_quote.get("letter_perimeter_m"))
    inner_ml = round(inner_mm / 1000.0, 6) if inner_mm else _positive(base_quote.get("hole_perimeter_ml"))
    cnc_ml = round((outer_ml or 0.0) + (inner_ml or 0.0), 6) if outer_ml is not None else None
    return outer_ml, inner_ml, cnc_ml


def _return_profile_key(finish_type: str | None, depth_mm: Any) -> tuple[str, str | None]:
    finish = (finish_type or "").strip().lower() or "standard_aluminum"
    depth = _positive(depth_mm)
    depth_token = str(int(depth)) if depth is not None else None
    return finish, depth_token


def build_layer_return_metric_audit(
    *,
    svg_analysis_json: dict[str, Any],
    layer_role_setup: dict[str, Any],
    finish_setup: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Per-layer flags for letter vs artwork return / LED scope."""
    finish_setup = finish_setup or {}
    letter_groups = finish_setup.get("letter_group_finishes") or []
    artwork_finishes = finish_setup.get("artwork_finishes") or []
    group_by_layer = {
        str(row.get("layer_name") or row.get("group_key") or ""): row
        for row in letter_groups
        if isinstance(row, dict)
    }
    artwork_by_layer = {
        str(row.get("layer_name") or row.get("layer_key") or ""): row
        for row in artwork_finishes
        if isinstance(row, dict)
    }

    classification = classify_letter_parts_from_analysis(svg_analysis_json, layer_role_setup)
    rows: list[dict[str, Any]] = []
    layers = svg_analysis_json.get("layers")
    if not isinstance(layers, list):
        return rows

    from services.intake_v4_quote_geometry_service import _confirmed_role

    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_id = str(layer.get("id") or "")
        layer_name = str(layer.get("name") or layer_id)
        role = _confirmed_role(layer_role_setup, layer_id, layer_name) or "unknown"
        group = group_by_layer.get(layer_name) or group_by_layer.get(layer_id)
        artwork = artwork_by_layer.get(layer_name) or artwork_by_layer.get(layer_id)

        face_finish = str((group or artwork or {}).get("face_finish_type") or finish_setup.get("face_finish_type") or "none")
        return_finish = str(
            (group or artwork or {}).get("return_finish_type")
            or finish_setup.get("return_finish_type")
            or "none"
        )
        return_depth = (group or artwork or {}).get("return_depth_mm") or finish_setup.get("return_depth_mm")
        return_active = return_finish_active(return_finish)

        is_face = role == "face"
        is_artwork = role in ARTWORK_ROLES
        execution = str((artwork or {}).get("execution_type") or "needs_decision")

        layer_parts = [p for p in classification.get("parts") or [] if str(p.get("source_layer") or "") in {layer_name, layer_id}]
        outer_mm = sum(_positive(p.get("outer_perimeter_mm")) or 0.0 for p in layer_parts if p.get("counts_as_letter"))
        if outer_mm <= 0:
            outer_mm = sum(_positive(p.get("outer_perimeter_mm")) or 0.0 for p in layer_parts if p.get("role") in ARTWORK_ROLES)
        hole_mm = sum(_positive(p.get("inner_perimeter_mm")) or 0.0 for p in layer_parts if p.get("counts_as_letter"))
        outer_ml = round(outer_mm / 1000.0, 4) if outer_mm > 0 else _layer_perimeter_ml(svg_analysis_json, layer_id, layer_name)
        hole_ml = round(hole_mm / 1000.0, 4) if hole_mm > 0 else None
        cutting_ml = round((outer_mm + hole_mm) / 1000.0, 4) if (outer_mm + hole_mm) > 0 else None
        return_ml = None
        if is_face and return_active and cutting_ml is not None:
            return_ml = cutting_ml
        elif is_artwork and return_active and outer_ml is not None:
            return_ml = outer_ml

        layer_inner_holes = sum(
            int(p.get("embedded_inner_hole_count") or 0)
            for p in layer_parts
            if p.get("counts_as_letter")
        )
        real_letters = sum(1 for p in layer_parts if p.get("counts_as_letter"))

        rows.append(
            {
                "layer_name": layer_name,
                "role": role,
                "outer_perimeter_ml": outer_ml,
                "inner_hole_perimeter_ml": hole_ml,
                "cutting_perimeter_ml": cutting_ml,
                "return_perimeter_ml": return_ml,
                "led_perimeter_ml": outer_ml if is_face else None,
                "real_letter_count": real_letters if is_face else 0,
                "inner_hole_count": layer_inner_holes if is_face else 0,
                "hole_perimeter_ml": hole_ml,
                "face_finish_type": face_finish,
                "return_finish_type": return_finish,
                "return_depth_mm": return_depth,
                "artwork_execution_type": execution if is_artwork else None,
                "counts_for_letter_count": is_face,
                "counts_for_artwork_piece_count": is_artwork and return_active,
                "counts_for_volumetric_piece_count": is_face or (is_artwork and return_active),
                "counts_for_led_perimeter": is_face,
                "counts_for_return_perimeter": (is_face and return_active) or (is_artwork and return_active),
            }
        )
    return rows


def enrich_quote_geometry_with_volumetric_return(
    base_quote: dict[str, Any],
    *,
    finish_setup: dict[str, Any] | None,
    svg_analysis_json: dict[str, Any],
    layer_role_setup: dict[str, Any],
    classification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Letter return = outer + inner holes when cant active; LED = outer letters only."""
    finish_setup = finish_setup or {}
    classification = classification or classify_letter_parts_from_analysis(svg_analysis_json, layer_role_setup)
    classification_parts = classification.get("parts") or []

    outer_letter_ml, inner_hole_letter_ml, cnc_cutting_ml = _letter_perimeter_metrics_from_classification(
        base_quote,
        classification,
    )

    letter_return_ml = outer_letter_ml
    if _face_layers_return_active(finish_setup) and outer_letter_ml is not None:
        letter_return_ml = round(outer_letter_ml + (inner_hole_letter_ml or 0.0), 4)

    artwork_finishes = finish_setup.get("artwork_finishes") or []
    artwork_piece_count = 0
    artwork_return_ml = 0.0
    artwork_return_layers: list[dict[str, Any]] = []

    for row in artwork_finishes:
        if not isinstance(row, dict):
            continue
        if not return_finish_active(row.get("return_finish_type")):
            continue
        layer_key = str(row.get("layer_key") or "")
        layer_name = str(row.get("layer_name") or layer_key)
        perimeter_ml = _artwork_outer_perimeter_ml(
            analysis=svg_analysis_json,
            classification_parts=classification_parts,
            layer_key=layer_key,
            layer_name=layer_name,
        )
        if not perimeter_ml:
            continue
        piece_count = int(row.get("element_count") or 1)
        artwork_piece_count += max(piece_count, 1)
        artwork_return_ml += perimeter_ml
        artwork_return_layers.append(
            {
                "layer_key": layer_key,
                "layer_name": layer_name,
                "return_finish_type": row.get("return_finish_type"),
                "return_depth_mm": row.get("return_depth_mm"),
                "return_perimeter_ml": round(perimeter_ml, 4),
                "execution_type": row.get("execution_type") or "needs_decision",
            }
        )

    real_letters = int(base_quote.get("real_letters_count") or base_quote.get("letter_count") or 0)
    total_return_ml = (letter_return_ml or 0.0) + artwork_return_ml

    enriched = dict(base_quote)
    enriched["outer_letter_perimeter_ml"] = round(outer_letter_ml, 4) if outer_letter_ml else None
    enriched["inner_hole_letter_perimeter_ml"] = round(inner_hole_letter_ml, 4) if inner_hole_letter_ml else None
    enriched["letter_return_perimeter_ml"] = round(letter_return_ml, 4) if letter_return_ml else None
    enriched["artwork_return_perimeter_ml"] = round(artwork_return_ml, 4) if artwork_return_ml > 0 else None
    enriched["return_material_perimeter_ml"] = round(total_return_ml, 4) if total_return_ml > 0 else None
    enriched["cnc_cutting_perimeter_ml"] = round(cnc_cutting_ml, 4) if cnc_cutting_ml else None
    enriched["led_perimeter_ml"] = round(outer_letter_ml, 4) if outer_letter_ml else None
    enriched["led_perimeter_policy"] = "outer_face_letters_excludes_holes_and_artwork"
    enriched["artwork_piece_count"] = artwork_piece_count
    enriched["volumetric_piece_count"] = real_letters + artwork_piece_count
    enriched["artwork_return_layers"] = artwork_return_layers
    return enriched


def letter_and_artwork_return_profiles_match(
    *,
    letter_groups: list[Any],
    artwork_finish: dict[str, Any],
    default_return_finish: str,
    default_return_depth: Any,
) -> bool:
    if not letter_groups:
        return True
    art_finish, art_depth = _return_profile_key(
        artwork_finish.get("return_finish_type"),
        artwork_finish.get("return_depth_mm"),
    )
    for group in letter_groups:
        if not isinstance(group, dict):
            continue
        if not return_finish_active(group.get("return_finish_type") or default_return_finish):
            continue
        letter_finish, letter_depth = _return_profile_key(
            group.get("return_finish_type"),
            group.get("return_depth_mm") or default_return_depth,
        )
        if (letter_finish, letter_depth) != (art_finish, art_depth):
            return False
    return True
