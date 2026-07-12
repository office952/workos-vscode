"""Intake V4 material nesting + consumables breakdown — informative, materials-only (no CostEngine)."""

from __future__ import annotations

from collections import Counter

import math
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.intake_v4 import (
    PILOT_V4_TEMPLATE_CODE,
    IntakeV4CncOperationRow,
    IntakeV4EdgeCantOperationRow,
    IntakeV4MaterialBreakdownResponse,
    IntakeV4MaterialBreakdownTotals,
    IntakeV4MaterialBreakdownWarning,
    IntakeV4MaterialQuantityRow,
    IntakeV4NestingMaterialRow,
    IntakeV4NestingPreviewResponse,
    IntakeV4SheetQuoteMaterialCandidates,
)
from services.intake_v4_artwork_complexity_service import (
    append_artwork_complexity_warnings,
    build_artwork_print_operation_preview_rows,
    effective_artwork_application,
    list_artwork_complexity_assessments,
    operator_artwork_application_map,
)
from services.intake_v4_backing_mode_service import (
    BASIS_BACKING_AREA_FACE_QUOTEABLE_FALLBACK,
    resolve_backing_mode_from_finish,
    resolve_backing_material_area_m2,
    resolve_layer_backing_mode,
    resolve_volumetric_backing_state,
)
from services.volumetric_material_rate_resolver import PROFILE_DEPTH_MM_TO_VARIANT_CODE
from dataclasses import asdict

from services.intake_v4_nesting_preview_service import build_intake_v4_nesting_preview
from services.intake_v4_nesting_material_precision import (
    BASIS_LAMINATE_AREA,
    BASIS_PRINT_AREA,
    BASIS_SHEET_NESTING_PRORATED_FALLBACK,
    CONFIDENCE_FORMULA,
    CONFIDENCE_NESTING_HIGH,
    CONFIDENCE_NESTING_MEDIUM,
    CONFIDENCE_PERIMETER,
    SHEET_EXCLUDED_ROLES,
    _layer_role_for_name as _sheet_layer_role_for_name,
    apply_sheet_material_quantity_floor,
    backing_layer_confirmed,
    compute_eligible_sheet_face_area_sum_sqm,
    compute_roll_nesting_vinyl_area_by_layer,
    compute_roll_nesting_vinyl_estimate,
    compute_sheet_nesting_material_split,
    compute_sheet_quote_material_candidates,
    SheetQuoteMaterialCandidates,
)
from services.intake_v4_sheet_footprint_override_service import (
    apply_operator_footprint_to_sheet_material_quantities,
    sheet_quote_override_from_payload,
)
from services.intake_v4_finish_truth_service import (
    INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE,
    any_letter_group_face_print_laminate,
    any_letter_group_face_vinyl_required,
    format_intake_v4_return_finish_operator_label,
    resolve_effective_return_depth_mm,
    resolve_effective_return_finish_label,
)
from services.intake_v4_consumables_adhesive_wiring_service import (
    is_intake_v4_owner_consumable_price_source,
)
from services.intake_v4_led_lighting_service import (
    normalize_led_module_power_w,
    normalize_led_strip_power_w_per_ml,
)
from services.shared_led_lighting_density_rules import calculate_led_strip_length_by_area
from services.intake_v4_volumetric_return_metrics_service import (
    ARTWORK_ROLES,
    letter_and_artwork_return_profiles_match,
    return_finish_active,
)
from services.intake_v4_oracal_face_pricing_service import (
    face_oracal_vinyl_areas_by_series,
    is_intake_v4_owner_oracal_price_source,
    resolve_intake_v4_owner_oracal_face_price,
)
from services.intake_v4_ral_paint_rules_service import (
    PRICE_SOURCE_OWNER_RAL_PAINT_SPRAY,
    RAL_PAINT_SPRAY_COVERAGE_M_PER_TUBE,
    RAL_PAINT_SPRAY_MATERIAL_CODE,
    RAL_PAINT_SPRAY_OWNER_EUR_PER_TUBE,
    RAL_PAINT_SPRAY_OWNER_RON_PER_TUBE,
    estimate_intake_v4_ral_paint_spray,
)
from services.intake_v4_quote_geometry_service import merge_quote_geometry_into_path_summary, resolve_v4_quote_geometry
from services.intake_v4_consumables_adhesive_wiring_service import (
    append_volumetric_adhesive_and_wiring_consumables,
)
from services.intake_v4_workspace_service import _get_record_or_404, _json_loads, _parse_payload
from services.shared_cnc_operation_model import (
    build_volumetric_letters_cnc_operation_rows,
    build_volumetric_letters_cnc_operation_rows_with_layer_backing,
    rows_to_schema_dicts,
)
from services.shared_edge_cant_rules import EdgeCantRuleInput, evaluate_edge_cant_rules, EDGE_CANT_LINEAR_UNIT

PRICE_SOURCE_INFORMATIONAL = "informational_only"

QUOTE_MATERIAL_COSTING_POLICY_V1 = "intake_v4_quote_material_cost_estimate_v1"
DEFAULT_QUOTE_WASTE_PERCENT = 20.0
WASTE_PERCENT = DEFAULT_QUOTE_WASTE_PERCENT
LED_PITCH_MM = 250.0

VOLUMETRIC_ARTWORK_EXECUTION_TYPES = frozenset({"separate_emblem"})
PRINT_ARTWORK_EXECUTION_TYPES = frozenset(
    {"print_laminate", "print_translucent", "printed_vinyl", "printed_laminated_vinyl", "printed_vinyl_on_face"},
)

# Registry codes only — no commercial unit prices in Intake V4.
MATERIAL_REGISTRY_CODES: dict[str, str] = {
    "plexiglas_face": "MAT-ACP-FATA-LITERE",
    "forex_backing": "MAT-SPATE-PVC-LITERE",
    "face_vinyl": "MAT-ORACAL-651",
    "led_modules": "MAT-LED-MODULE",
    "led_strip": "MAT-LED-STRIP",
    "print_vinyl": "MAT-VINYL-PRINT",
    "laminated_vinyl": "MAT-VINYL-PRINT-LAMINATED",
    "ral_paint_spray": RAL_PAINT_SPRAY_MATERIAL_CODE,
}

SHEET_CONFIG_LABELS: dict[str, str] = {
    "sheet_1300x900": "ACM / Forex 1300×900 mm",
    "sheet_1220x2440": "Placă 1220×2440 mm",
}

# Full sheet area (m²) per nest2 config — mirrors frontend nestingConfigs.ts dimensions.
SHEET_CONFIG_AREA_SQM: dict[str, float] = {
    "sheet_3000x2000": (3.0 * 2.0),
    "sheet_3000x1500": (3.0 * 1.5),
    "sheet_4000x1500": (4.0 * 1.5),
    "sheet_1300x900": (1.3 * 0.9),
    "sheet_1220x2440": (2.44 * 1.22),
}

BASIS_ROLL_NESTING = "roll_nesting_quote_estimate"
BASIS_SHEET_NESTING = "sheet_nesting_quote_estimate"  # legacy alias in tests/docs
BASIS_AREA_FALLBACK = "area_with_waste_fallback"
BASIS_ARTWORK_BOX_FOOTPRINT = "artwork_box_bounding_footprint_quote_estimate"
BASIS_BACKING_AREA_ARTWORK_BOX_FOOTPRINT = "backing_area_fallback_from_artwork_box_footprint"
BASIS_LINKED_LOGO_FACE_FOOTPRINT = "linked_logo_face_bounding_footprint_quote_estimate"
BASIS_LINKED_LOGO_BACKING_FOOTPRINT = "linked_logo_backing_bounding_footprint_quote_estimate"
BASIS_PERIMETER = "perimeter_with_waste"
CONFIDENCE_NESTING = "estimate_from_nesting_high"
CONFIDENCE_NESTING_PARTIAL = "estimate_from_nesting_medium"
CONFIDENCE_AREA_FALLBACK = "estimate_fallback_area"
RAW_VECTOR_TOTAL_MIN_DELTA_M = 0.05
# Legacy fallback prices — overridden by _apply_registry_prices / _apply_registry_operation_prices
# when DB rates exist (inventory_materials for materials, workcenter_rates for operations).
OWNER_PRINT_SERVICE_EUR_PER_M2 = 8.0
OWNER_LAMINATION_SERVICE_EUR_PER_M2 = 2.0
OWNER_APPLICATION_SERVICE_EUR_PER_M2 = 3.0
PRICE_SOURCE_OWNER_PRINT_SERVICE = "intake_v4_owner_print_service"
PRICE_SOURCE_OWNER_LAMINATION_SERVICE = "intake_v4_owner_lamination_service"
PRICE_SOURCE_OWNER_APPLICATION_SERVICE = "intake_v4_owner_application_service"
MOUNTING_ACCESSORIES_RATE = 0.05
MOUNTING_ACCESSORIES_MATERIAL_CODE = "MAT-CONSUMABILE-MONTAJ"
PRICE_SOURCE_OWNER_MOUNTING_ACCESSORIES = "cost_formula_mounting_accessories_5pct"
MOUNTING_ACCESSORIES_COST_BASIS = "manufacturing_cost_subtotal_before_markup"


def _positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _raw_vector_total_perimeter_ml(path_geometry: dict[str, Any]) -> float | None:
    """Total drawable vector curve length from the raw path parser, in meters."""
    candidates: list[float] = []
    contour_split = path_geometry.get("contour_split")
    if isinstance(contour_split, dict):
        total_mm = _positive(contour_split.get("total_cutting_perimeter_mm"))
        if total_mm is not None:
            candidates.append(total_mm / 1000.0)
    perimeter_mm = _positive(path_geometry.get("perimeter_mm_approx"))
    if perimeter_mm is not None:
        candidates.append(perimeter_mm / 1000.0)
    if not candidates:
        return None
    return round(max(candidates), 4)


def _raw_vector_total_should_override(raw_total_ml: float | None, current_ml: float | None) -> bool:
    if raw_total_ml is None:
        return False
    if current_ml is None:
        return True
    return raw_total_ml > current_ml + RAW_VECTOR_TOTAL_MIN_DELTA_M


def _path_geometry_with_raw_vector_total(
    path_geometry: dict[str, Any],
    raw_total_ml: float | None,
) -> dict[str, Any]:
    if raw_total_ml is None:
        return path_geometry
    current = _float_metric(
        [path_geometry],
        "cnc_cutting_perimeter_ml",
        "face_cutting_perimeter_ml",
        "cutting_perimeter_ml",
        "return_material_perimeter_ml",
    )
    if not _raw_vector_total_should_override(raw_total_ml, current):
        return path_geometry
    patched = dict(path_geometry)
    for key in (
        "return_material_perimeter_ml",
        "face_cutting_perimeter_ml",
        "cutting_perimeter_ml",
        "cnc_cutting_perimeter_ml",
        "bevel_perimeter_ml",
    ):
        patched[key] = raw_total_ml
    patched["raw_vector_total_perimeter_ml"] = raw_total_ml
    patched["vector_total_perimeter_source"] = "path_geometry_summary.perimeter_mm_approx"
    return patched


def _layer_metrics_from_analysis(
    analysis: dict[str, Any],
    layer_key: str,
    layer_name: str,
) -> tuple[float | None, float | None]:
    layers = analysis.get("layers")
    if not isinstance(layers, list):
        return None, None
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_id = str(layer.get("id") or "")
        name = str(layer.get("name") or layer_id)
        if layer_key not in {layer_id, name} and layer_name not in {layer_id, name}:
            continue
        area = _positive(layer.get("filledAreaSqm")) or _positive(layer.get("boundingAreaSqm"))
        perimeter_ml = _positive(layer.get("perimeterMl"))
        if perimeter_ml is None:
            perimeter_mm = _positive(layer.get("perimeterMm"))
            perimeter_ml = perimeter_mm / 1000 if perimeter_mm else None
        return area, perimeter_ml
    return None, None


def _artwork_box_footprint_area_sqm(*geom_sources: Any) -> float | None:
    for source in geom_sources:
        if not isinstance(source, dict):
            continue
        boxes = source.get("artwork_boxes")
        if not isinstance(boxes, list):
            continue
        total = 0.0
        found = False
        for box in boxes:
            if not isinstance(box, dict):
                continue
            width_mm = _positive(box.get("width_mm"))
            height_mm = _positive(box.get("height_mm"))
            if width_mm is None or height_mm is None:
                continue
            total += (width_mm * height_mm) / 1_000_000.0
            found = True
        if found and total > 0:
            return round(total, 4)
    return None


def _artwork_box_area_for_layer(
    layer_key: str,
    layer_name: str,
    *geom_sources: Any,
) -> float | None:
    for source in geom_sources:
        if not isinstance(source, dict):
            continue
        boxes = source.get("artwork_boxes")
        if not isinstance(boxes, list):
            continue
        for box in boxes:
            if not isinstance(box, dict):
                continue
            box_key = str(box.get("layer_key") or "")
            box_name = str(box.get("layer_name") or box_key)
            if layer_key not in {box_key, box_name} and layer_name not in {box_key, box_name}:
                continue
            width_mm = _positive(box.get("width_mm"))
            height_mm = _positive(box.get("height_mm"))
            if width_mm is not None and height_mm is not None:
                return round((width_mm * height_mm) / 1_000_000.0, 4)
            area = _positive(box.get("area_m2"))
            if area is not None:
                return round(area, 4)
    return None


def _has_confirmed_letter_face_content(
    *,
    layer_role_setup: dict[str, Any] | None,
    letter_groups: list[Any],
) -> bool:
    if letter_groups:
        for group in letter_groups:
            if not isinstance(group, dict):
                continue
            layer_key = str(group.get("group_key") or group.get("layer_key") or "")
            layer_name = str(group.get("layer_name") or layer_key)
            role = _sheet_layer_role_for_name(layer_role_setup, layer_key, layer_name)
            if role == "face":
                return True
            if role is None and (_positive(group.get("face_area_m2")) or _positive(group.get("perimeter_m"))):
                return True
    layers = (layer_role_setup or {}).get("layers") if isinstance(layer_role_setup, dict) else None
    if isinstance(layers, list):
        for layer in layers:
            if not isinstance(layer, dict):
                continue
            if str(layer.get("confirmation_state") or "").strip().lower() == "ignored":
                continue
            role = str(layer.get("confirmed_role") or layer.get("auto_role") or "").strip().lower()
            if role == "face":
                return True
    return False


def _append_artwork_volumetric_rows(
    *,
    artwork_finishes: list[Any],
    analysis: dict[str, Any],
    default_return_finish: str,
    material_rows: list[IntakeV4MaterialQuantityRow],
    warnings: list[IntakeV4MaterialBreakdownWarning],
) -> None:
    """Plexiglas + cant for volumetric artwork (separate_emblem) — excluded from letter face totals."""
    if not artwork_finishes:
        return

    for row in artwork_finishes:
        if not isinstance(row, dict):
            continue
        execution = str(row.get("execution_type") or "needs_decision").strip().lower()
        if execution not in VOLUMETRIC_ARTWORK_EXECUTION_TYPES:
            continue

        layer_key = str(row.get("layer_key") or "")
        layer_name = str(row.get("layer_name") or layer_key)
        if not layer_key:
            continue

        area = _positive(row.get("estimated_area_m2"))
        perimeter_ml: float | None = None
        if area is None:
            area, perimeter_ml = _layer_metrics_from_analysis(analysis, layer_key, layer_name)
        else:
            _, perimeter_ml = _layer_metrics_from_analysis(analysis, layer_key, layer_name)

        if not area:
            warnings.append(
                _warn(
                    "missing_artwork_area",
                    f"Artwork volumetric „{layer_name}” — lipsește suprafața față.",
                    source="finish_setup.artwork_finishes",
                )
            )
            continue

        fb_code = MATERIAL_REGISTRY_CODES["plexiglas_face"]
        material_rows.append(
            _cost_row(
                f"artwork_plexiglas_{layer_key}",
                f"Plexiglas față emblemă — {layer_name}",
                "material",
                area,
                "m2",
                quantity_basis=BASIS_AREA_FALLBACK,
                quantity_source="artwork_finishes|svg_analysis_json.layers",
                quantity_quality="calculated",
                registry_code=fb_code,
                confidence=CONFIDENCE_AREA_FALLBACK,
            )
        )

        raw_return_finish = str(row.get("return_finish_type") or "standard_aluminum")
        depth = row.get("return_depth_mm")
        if perimeter_ml and raw_return_finish.strip().lower() not in {"none", ""}:
            return_finish = format_intake_v4_return_finish_operator_label(
                raw_return_finish,
                default_return_finish,
            )
            depth_label = f" · {depth} mm" if depth else ""
            ret_code = _return_registry_code(depth)
            material_rows.append(
                _cost_row(
                    f"artwork_return_{layer_key}",
                    f"Cant / volum emblemă — {layer_name} ({return_finish}){depth_label}",
                    "material",
                    perimeter_ml,
                    EDGE_CANT_LINEAR_UNIT,
                    quantity_basis=BASIS_PERIMETER,
                    quantity_source="artwork_finishes|svg_analysis_json.layers",
                    quantity_quality="calculated",
                    registry_code=ret_code,
                )
            )
        elif execution in VOLUMETRIC_ARTWORK_EXECUTION_TYPES and not perimeter_ml:
            warnings.append(
                _warn(
                    "missing_artwork_perimeter",
                    f"Artwork volumetric „{layer_name}” — perimetru cant / volum indisponibil.",
                    source="svg_analysis_json.layers",
                )
            )


def _warn(code: str, message: str, *, source: str, severity: str = "warning") -> IntakeV4MaterialBreakdownWarning:
    return IntakeV4MaterialBreakdownWarning(code=code, severity=severity, message=message, source=source)


def _with_waste(qty: float | None, *, apply_buffer: bool = True) -> tuple[float, float, float | None]:
    if qty is None or qty <= 0:
        return 0.0, 0.0, None
    base = qty
    if not apply_buffer:
        return base, base, None
    priced = base * (1.0 + WASTE_PERCENT / 100.0)
    return base, round(priced, 4), WASTE_PERCENT


def _quote_cost_row(
    material_key: str,
    display_name: str,
    category: str,
    qty: float | None,
    unit: str,
    *,
    quantity_basis: str,
    quantity_source: str,
    quantity_quality: str,
    registry_code: str | None = None,
    confidence: str = "estimate_for_quote",
    apply_quote_waste: bool = True,
    unit_price: float | None = None,
    price_source: str = "missing",
    currency: str = "EUR",
    source_part_ids: list[str] | None = None,
    trace_markers: list[str] | None = None,
) -> IntakeV4MaterialQuantityRow:
    base, priced, waste_pct = _with_waste(qty, apply_buffer=apply_quote_waste)
    material_cost = round(priced * unit_price, 4) if unit_price is not None and priced > 0 else None
    return IntakeV4MaterialQuantityRow(
        material_key=material_key,
        display_name=display_name,
        material_name=display_name,
        category=category,  # type: ignore[arg-type]
        quantity=base,
        base_quantity=base,
        unit=unit,
        quantity_basis=quantity_basis,
        quantity_source=quantity_source,
        quantity_quality=quantity_quality,
        confidence=confidence,
        consumption_mode="quote_estimate",
        waste_percent=waste_pct,
        quantity_with_waste=priced,
        priced_quantity=priced,
        registry_code=registry_code,
        material_code=registry_code,
        unit_price=unit_price,
        material_cost=material_cost,
        estimated_cost=material_cost,
        price_source=price_source,
        currency=currency,
        source_part_ids=list(source_part_ids or []),
        trace_markers=list(trace_markers or []),
    )


def _cost_row(
    material_key: str,
    display_name: str,
    category: str,
    qty: float | None,
    unit: str,
    *,
    quantity_source: str,
    quantity_quality: str,
    registry_code: str | None = None,
    unit_price: float | None = None,
    quantity_basis: str | None = None,
    apply_quote_waste: bool = True,
    confidence: str = "estimate_for_quote",
    price_source: str = "missing",
    currency: str = "EUR",
    source_part_ids: list[str] | None = None,
    trace_markers: list[str] | None = None,
) -> IntakeV4MaterialQuantityRow:
    basis = quantity_basis or quantity_source
    return _quote_cost_row(
        material_key,
        display_name,
        category,
        qty,
        unit,
        quantity_basis=basis,
        quantity_source=quantity_source,
        quantity_quality=quantity_quality,
        registry_code=registry_code,
        confidence=confidence,
        apply_quote_waste=apply_quote_waste,
        unit_price=unit_price,
        price_source=price_source,
        currency=currency,
        source_part_ids=source_part_ids,
        trace_markers=trace_markers,
    )


def _logo_only_artwork_source_part_ids(
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
) -> list[str]:
    parts = (analysis.get("parts") or {}).get("items") if isinstance(analysis.get("parts"), dict) else None
    if not isinstance(parts, list):
        return []
    try:
        from services.intake_v4_letter_part_classification_service import classify_letter_parts_from_analysis

        classified = classify_letter_parts_from_analysis(analysis, layer_role_setup or {})
        hole_ids = {
            str(row.get("part_id") or "")
            for row in (classified.get("parts") or [])
            if isinstance(row, dict) and row.get("is_inner_hole")
        }
    except Exception:
        hole_ids = set()

    result: list[str] = []
    for item in parts:
        if not isinstance(item, dict):
            continue
        part_id = str(item.get("id") or "").strip()
        if not part_id or part_id in hole_ids:
            continue
        source = item.get("source") if isinstance(item.get("source"), dict) else {}
        layer_id = str(source.get("layerId") or "")
        layer_name = str(source.get("layerName") or layer_id)
        role = _sheet_layer_role_for_name(layer_role_setup, layer_id, layer_name)
        if role in {"printed_artwork", "logo", "policromie"}:
            result.append(part_id)
    return result


def _linked_volumetric_logo_boxes(payload_raw: dict[str, Any]) -> list[dict[str, Any]]:
    recommendation = payload_raw.get("product_composition_recommendation")
    quote_geometry = payload_raw.get("quote_geometry")
    if not isinstance(quote_geometry, dict):
        return []
    boxes = quote_geometry.get("artwork_boxes")
    if not isinstance(boxes, list):
        return []
    if isinstance(recommendation, dict):
        if recommendation.get("composition_type") in {"letters_plus_logo", "letters_plus_logo_plus_support"}:
            items = recommendation.get("composition_items")
            if isinstance(items, list) and any(isinstance(item, dict) and item.get("component_role") == "volumetric_logo" for item in items):
                return [box for box in boxes if isinstance(box, dict) and _positive(box.get("area_m2"))]

    finish_setup = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else {}
    artwork_finishes = finish_setup.get("artwork_finishes") if isinstance(finish_setup.get("artwork_finishes"), list) else []
    if not artwork_finishes:
        return []
    layer_role_setup = payload_raw.get("layer_role_setup") if isinstance(payload_raw.get("layer_role_setup"), dict) else None
    has_letter_face = False
    has_logo_artwork = False
    for layer in (layer_role_setup or {}).get("layers") or []:
        if not isinstance(layer, dict):
            continue
        role = str(layer.get("confirmed_role") or layer.get("auto_role") or "").strip().lower()
        state = str(layer.get("confirmation_state") or "").strip().lower()
        if state == "ignored":
            continue
        if role == "face":
            has_letter_face = True
        if role in {"printed_artwork", "logo", "policromie"}:
            has_logo_artwork = True
    if not (has_letter_face and has_logo_artwork):
        return []
    return [box for box in boxes if isinstance(box, dict) and _positive(box.get("area_m2"))]


def _linked_logo_source_part_ids_by_layer(analysis: dict[str, Any], layer_role_setup: dict[str, Any] | None) -> dict[str, list[str]]:
    parts = (analysis.get("parts") or {}).get("items") if isinstance(analysis.get("parts"), dict) else None
    if not isinstance(parts, list):
        return {}
    result: dict[str, list[str]] = {}
    for item in parts:
        if not isinstance(item, dict):
            continue
        part_id = str(item.get("id") or "").strip()
        if not part_id:
            continue
        source = item.get("source") if isinstance(item.get("source"), dict) else {}
        layer_id = str(source.get("layerId") or "")
        layer_name = str(source.get("layerName") or layer_id)
        role = _sheet_layer_role_for_name(layer_role_setup, layer_id, layer_name)
        if role not in {"printed_artwork", "logo", "policromie"}:
            continue
        for key in {layer_id, layer_name}:
            if not key:
                continue
            result.setdefault(key, []).append(part_id)
    return result


def _artwork_source_part_ids_by_layer(analysis: dict[str, Any], layer_role_setup: dict[str, Any] | None) -> dict[str, list[str]]:
    parts = (analysis.get("parts") or {}).get("items") if isinstance(analysis.get("parts"), dict) else None
    if not isinstance(parts, list):
        return {}

    result: dict[str, list[str]] = {}
    for item in parts:
        if not isinstance(item, dict):
            continue
        part_id = str(item.get("id") or "").strip()
        if not part_id:
            continue
        source = item.get("source") if isinstance(item.get("source"), dict) else {}
        layer_id = str(source.get("layerId") or "")
        layer_name = str(source.get("layerName") or layer_id)
        role = _sheet_layer_role_for_name(layer_role_setup, layer_id, layer_name)
        if role not in {"printed_artwork", "logo", "policromie"}:
            continue
        for key in {layer_id, layer_name}:
            if key:
                result.setdefault(key, []).append(part_id)
    return result


def _return_registry_code(return_depth_mm: Any) -> str | None:
    try:
        depth = int(return_depth_mm) if return_depth_mm is not None else None
    except (TypeError, ValueError):
        depth = None
    if depth in PROFILE_DEPTH_MM_TO_VARIANT_CODE:
        return PROFILE_DEPTH_MM_TO_VARIANT_CODE[depth]
    return None


def _psu_registry_code(psu_configuration: list[Any] | None) -> str | None:
    grouped_psu = _group_psu_configuration(psu_configuration)
    if not grouped_psu:
        return None
    return grouped_psu[0][1]


def _group_psu_configuration(psu_configuration: list[Any] | None) -> list[tuple[int, str | None, int]]:
    if not isinstance(psu_configuration, list) or not psu_configuration:
        return []
    watts_counter = Counter(
        int(watts)
        for watts in psu_configuration
        if isinstance(watts, (int, float)) and watts > 0
    )
    if not watts_counter:
        return []
    from services.volumetric_material_rate_resolver import PSU_WATTS_TO_VARIANT_CODE

    grouped: list[tuple[int, str | None, int]] = []
    for watts in sorted(watts_counter):
        grouped.append((watts, PSU_WATTS_TO_VARIANT_CODE.get(watts), watts_counter[watts]))
    return grouped


def _is_price_missing_for_quantity(row: IntakeV4MaterialQuantityRow) -> bool:
    if row.price_source == PRICE_SOURCE_INFORMATIONAL:
        return False
    return row.unit_price is None and row.quantity > 0


def _row_estimated_cost(row: IntakeV4MaterialQuantityRow) -> float:
    value = row.estimated_cost if row.estimated_cost is not None else row.material_cost
    try:
        parsed = float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0
    return parsed if parsed > 0 else 0.0


def _operation_estimated_cost(row: IntakeV4CncOperationRow | IntakeV4EdgeCantOperationRow) -> float:
    try:
        parsed = float(row.estimated_cost) if row.estimated_cost is not None else 0.0
    except (TypeError, ValueError):
        return 0.0
    return parsed if parsed > 0 else 0.0


def _is_price_missing_for_operation(row: IntakeV4CncOperationRow | IntakeV4EdgeCantOperationRow) -> bool:
    try:
        quantity = float(row.operation_equivalent_quantity or row.quantity or 0.0)
    except (TypeError, ValueError):
        quantity = 0.0
    if quantity <= 0:
        return False
    if row.pricing_status in {"missing_rate", "pending_mapping"}:
        return True
    return bool(row.pricing_rate_key and row.unit_price is None)


def _manufacturing_cost_subtotal_before_markup(
    *,
    material_rows: list[IntakeV4MaterialQuantityRow],
    consumable_rows: list[IntakeV4MaterialQuantityRow],
    operation_rows: list[IntakeV4CncOperationRow],
    edge_cant_operation_rows: list[IntakeV4EdgeCantOperationRow] | None = None,
) -> float:
    material_total = sum(
        _row_estimated_cost(row)
        for row in material_rows + consumable_rows
        if row.material_key != "mounting_accessories_percent"
    )
    operation_total = sum(_operation_estimated_cost(row) for row in operation_rows)
    edge_operation_total = sum(_operation_estimated_cost(row) for row in edge_cant_operation_rows or [])
    return round(material_total + operation_total + edge_operation_total, 4)


def _build_mounting_accessories_percent_row(
    manufacturing_subtotal: float,
) -> IntakeV4MaterialQuantityRow | None:
    if manufacturing_subtotal <= 0:
        return None
    accessory_cost = round(manufacturing_subtotal * MOUNTING_ACCESSORIES_RATE, 4)
    return IntakeV4MaterialQuantityRow(
        material_key="mounting_accessories_percent",
        display_name="Accesorii montaj / conectori (5% cost confectie)",
        material_name="Accesorii montaj / conectori",
        category="consumable",
        quantity=1.0,
        base_quantity=1.0,
        unit="job",
        quantity_basis=MOUNTING_ACCESSORIES_COST_BASIS,
        quantity_source=(
            f"{MOUNTING_ACCESSORIES_COST_BASIS}={manufacturing_subtotal:.2f}; "
            f"rate={MOUNTING_ACCESSORIES_RATE:.0%}; excludes_client_markup"
        ),
        quantity_quality="calculated",
        confidence="owner_rule",
        consumption_mode="quote_estimate",
        waste_percent=None,
        quantity_with_waste=1.0,
        priced_quantity=1.0,
        registry_code=None,
        material_code=MOUNTING_ACCESSORIES_MATERIAL_CODE,
        unit_price=accessory_cost,
        material_cost=accessory_cost,
        estimated_cost=accessory_cost,
        price_source=PRICE_SOURCE_OWNER_MOUNTING_ACCESSORIES,
        currency="EUR",
    )


def _append_ral_paint_spray_row(
    *,
    finish: dict[str, Any],
    geometry: dict[str, Any],
    analysis: dict[str, Any],
    default_return_finish: str,
    material_rows: list[IntakeV4MaterialQuantityRow],
) -> None:
    estimate = estimate_intake_v4_ral_paint_spray(
        finish_setup=finish,
        geometry=geometry,
        analysis=analysis,
        default_return_finish=default_return_finish,
    )
    if estimate is None:
        return
    color_parts = [part for part in (estimate.paint_ral_code, estimate.paint_ral_name) if part]
    color_label = f" ({' - '.join(color_parts)})" if color_parts else ""
    material_rows.append(
        IntakeV4MaterialQuantityRow(
            material_key="ral_paint_spray",
            display_name=f"Vopsea RAL spray / cant volum{color_label}",
            material_name="Vopsea RAL spray",
            category="material",
            quantity=float(estimate.charged_tubes),
            base_quantity=estimate.raw_tubes,
            unit="buc",
            quantity_basis="ral_paint_spray_tubes_from_painted_cant_perimeter",
            quantity_source=(
                f"painted_return_m={estimate.painted_return_m:.4f}; "
                f"coverage={RAL_PAINT_SPRAY_COVERAGE_M_PER_TUBE:g} m/tub; "
                f"owner_price={RAL_PAINT_SPRAY_OWNER_RON_PER_TUBE:g} RON/tub"
            ),
            quantity_quality="calculated",
            confidence="owner_rule",
            consumption_mode="quote_estimate",
            waste_percent=None,
            quantity_with_waste=float(estimate.charged_tubes),
            priced_quantity=float(estimate.charged_tubes),
            registry_code=RAL_PAINT_SPRAY_MATERIAL_CODE,
            material_code=RAL_PAINT_SPRAY_MATERIAL_CODE,
            unit_price=RAL_PAINT_SPRAY_OWNER_EUR_PER_TUBE,
            material_cost=estimate.material_cost_eur,
            estimated_cost=estimate.material_cost_eur,
            price_source=PRICE_SOURCE_OWNER_RAL_PAINT_SPRAY,
            currency="EUR",
            warnings=[
                (
                    f"{estimate.painted_return_m:.2f} m cant RAL / "
                    f"{RAL_PAINT_SPRAY_COVERAGE_M_PER_TUBE:g} m pe tub = "
                    f"{estimate.raw_tubes:.2f}; taxat {estimate.charged_tubes} tub(uri)."
                ),
                (
                    f"Owner rule: {RAL_PAINT_SPRAY_OWNER_RON_PER_TUBE:g} RON/tub, "
                    f"V4 foloseste {RAL_PAINT_SPRAY_OWNER_EUR_PER_TUBE:g} EUR/tub "
                    "conform registrului owner-confirmed."
                ),
            ],
        )
    )


async def resolve_v4_registry_material_price(
    db: AsyncSession,
    code: str,
    *,
    pricing_cache: dict[str, dict[str, Any]] | None = None,
) -> tuple[float | None, str | None, str]:
    """Quote-ready unit price from `/inventory/pricing` storage (inventory_materials BLK-18 bridge).

    Uses the same inclusion rules as CostEngine ``load_material_cost_dict`` /
    Pricing Registry ``cost_engine_materials`` — not the looser V3 row scan.
    """
    if pricing_cache is None:
        from services.inventory_materials_admin_service import load_material_pricing_dict

        pricing_cache = await load_material_pricing_dict(db)
    row = pricing_cache.get(code)
    if not row:
        return None, None, "missing"
    return float(row["unit_cost"]), str(row["currency"]), "pricing_registry"


async def _apply_registry_prices(
    db: AsyncSession,
    rows: list[IntakeV4MaterialQuantityRow],
) -> list[IntakeV4MaterialQuantityRow]:
    from services.inventory_materials_admin_service import load_material_pricing_dict

    pricing_cache = await load_material_pricing_dict(db)
    enriched: list[IntakeV4MaterialQuantityRow] = []
    for row in rows:
        if row.price_source == PRICE_SOURCE_INFORMATIONAL:
            enriched.append(row)
            continue
        registry_code = row.registry_code
        unit_price = row.unit_price
        price_source = row.price_source
        currency = row.currency
        if registry_code:
            reg_price, reg_currency, reg_source = await resolve_v4_registry_material_price(
                db,
                registry_code,
                pricing_cache=pricing_cache,
            )
            if reg_price is not None:
                unit_price, currency, price_source = reg_price, reg_currency or currency, reg_source
            elif price_source == "missing":
                price_source = "missing"
        material_cost = (
            round(row.priced_quantity * unit_price, 4)
            if unit_price is not None and row.priced_quantity > 0
            else None
        )
        enriched.append(
            row.model_copy(
                update={
                    "unit_price": unit_price,
                    "currency": currency,
                    "material_cost": material_cost,
                    "estimated_cost": material_cost,
                    "price_source": price_source,
                }
            )
        )
    return enriched


def _workcenter_code_from_rate_key(pricing_rate_key: str | None) -> str | None:
    if not pricing_rate_key:
        return None
    parts = pricing_rate_key.split(":")
    if len(parts) < 2 or parts[0] != "workcenter_rates":
        return None
    code = parts[1].strip()
    return code or None


async def _apply_registry_operation_prices(
    db: AsyncSession,
    rows: list[IntakeV4CncOperationRow] | list[IntakeV4EdgeCantOperationRow],
) -> list[IntakeV4CncOperationRow] | list[IntakeV4EdgeCantOperationRow]:
    from services.workcenter_rates_service import load_workcenter_rate_pricing_dict

    pricing_cache = await load_workcenter_rate_pricing_dict(db)
    enriched: list[IntakeV4CncOperationRow | IntakeV4EdgeCantOperationRow] = []
    for row in rows:
        if row.unit_price is not None:
            enriched.append(row)
            continue
        priced_quantity = row.operation_equivalent_quantity or row.quantity
        code = _workcenter_code_from_rate_key(row.pricing_rate_key)
        rate_row = pricing_cache.get(code) if code else None
        if not rate_row:
            fallback_source: str | None = None
            fallback_unit_price: float | None = None
            operation_unit = str(row.operation_equivalent_unit or row.unit or "").strip().lower()
            if operation_unit == "m2":
                if row.operation_type == "print_vinyl":
                    fallback_unit_price = OWNER_PRINT_SERVICE_EUR_PER_M2
                    fallback_source = PRICE_SOURCE_OWNER_PRINT_SERVICE
                elif row.operation_type == "lamination":
                    fallback_unit_price = OWNER_LAMINATION_SERVICE_EUR_PER_M2
                    fallback_source = PRICE_SOURCE_OWNER_LAMINATION_SERVICE
                elif row.operation_type == "vinyl_application":
                    fallback_unit_price = OWNER_APPLICATION_SERVICE_EUR_PER_M2
                    fallback_source = PRICE_SOURCE_OWNER_APPLICATION_SERVICE
            if fallback_unit_price is not None and priced_quantity is not None and priced_quantity > 0:
                estimated_cost = round(float(priced_quantity) * fallback_unit_price, 4)
                enriched.append(
                    row.model_copy(
                        update={
                            "unit_price": fallback_unit_price,
                            "estimated_cost": estimated_cost,
                            "pricing_status": fallback_source,
                        }
                    )
                )
                continue
            enriched.append(row)
            continue

        basis = str(rate_row.get("rate_basis") or "")
        unit_price: float | None = None
        if basis in {"per_linear_meter", "per_piece", "per_square_meter"}:
            raw_unit_price = rate_row.get("rate_per_linear_meter")
            unit_price = float(raw_unit_price) if raw_unit_price is not None else None
        elif basis == "per_hour":
            raw_unit_price = rate_row.get("rate_per_hour")
            unit_price = float(raw_unit_price) if raw_unit_price is not None else None

        estimated_cost = (
            round(float(priced_quantity) * unit_price, 4)
            if unit_price is not None and priced_quantity is not None and priced_quantity > 0
            else None
        )
        enriched.append(
            row.model_copy(
                update={
                    "unit_price": unit_price,
                    "estimated_cost": estimated_cost,
                    "pricing_status": "pricing_registry" if estimated_cost is not None else row.pricing_status,
                }
            )
        )
    return enriched


def _float_metric(sources: list[dict[str, Any] | None], *keys: str) -> float | None:
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in keys:
            raw = source.get(key)
            if raw is None:
                continue
            try:
                value = float(raw)
                if value > 0:
                    return value
            except (TypeError, ValueError):
                continue
    return None


def _compute_led_module_count(perimeter_ml: float | None) -> int | None:
    if perimeter_ml is None or perimeter_ml <= 0:
        return None
    return int(math.ceil((perimeter_ml * 1000.0) / LED_PITCH_MM))


def _face_finish_is_print_laminate(face_finish: str) -> bool:
    return face_finish.strip().lower() in {
        "print_laminate",
        "printed_vinyl",
        "printed_laminated_vinyl",
        "printed_vinyl_on_face",
    }


def _print_finish_needs_lamination(finish_type: str) -> bool:
    return finish_type.strip().lower() in {
        "print_laminate",
        "printed_laminated_vinyl",
    }


def _append_operation_service_row(
    operation_rows: list[IntakeV4CncOperationRow] | None,
    *,
    key: str,
    display_name: str,
    operation_type: str,
    quantity_m2: float,
    basis_key: str,
    basis_label: str,
    pricing_rate_key: str,
    tpl_operation_key: str,
    operation_catalog_key: str,
    workcenter_code: str,
) -> None:
    if operation_rows is None or quantity_m2 <= 0:
        return
    operation_rows.append(
        IntakeV4CncOperationRow(
            key=key,
            display_name=display_name,
            operation_type=operation_type,
            quantity=quantity_m2,
            unit="m2",
            basis_key=basis_key,
            basis_label=basis_label,
            operation_equivalent_quantity=quantity_m2,
            operation_equivalent_unit="m2",
            pricing_rate_key=pricing_rate_key,
            unit_price=None,
            estimated_cost=None,
            pricing_status="missing_rate",
            tpl_operation_key=tpl_operation_key,
            operation_catalog_key=operation_catalog_key,
            workcenter_code=workcenter_code,
            consumes_stock_now=False,
        )
    )


def _append_print_laminate_quote_rows(
    *,
    area_m2: float | None,
    material_rows: list[IntakeV4MaterialQuantityRow],
    operation_rows: list[IntakeV4CncOperationRow] | None = None,
    quantity_source: str,
    key_prefix: str,
    display_suffix: str,
    include_lamination: bool = True,
    include_application: bool = True,
) -> None:
    if not area_m2 or area_m2 <= 0:
        return
    priced_area_m2 = round(area_m2 * (1.0 + WASTE_PERCENT / 100.0), 4)
    material_rows.append(
        _cost_row(
            f"{key_prefix}_print_vinyl",
            f"Material print Orafol — {display_suffix}",
            "material",
            area_m2,
            "m2",
            quantity_basis=BASIS_PRINT_AREA,
            quantity_source=quantity_source,
            quantity_quality="calculated",
            registry_code=MATERIAL_REGISTRY_CODES["print_vinyl"],
            confidence=CONFIDENCE_AREA_FALLBACK,
        )
    )
    if include_lamination:
        material_rows.append(
            _cost_row(
                f"{key_prefix}_laminated_vinyl",
                f"Material laminare Orafol — {display_suffix}",
                "material",
                area_m2,
                "m2",
                quantity_basis=BASIS_LAMINATE_AREA,
                quantity_source=quantity_source,
                quantity_quality="calculated",
                confidence=CONFIDENCE_AREA_FALLBACK,
                registry_code=MATERIAL_REGISTRY_CODES["laminated_vinyl"],
            )
        )
    _append_operation_service_row(
        operation_rows,
        key=f"{key_prefix}_print_service",
        display_name=f"Serviciu print — {display_suffix}",
        operation_type="print_vinyl",
        quantity_m2=priced_area_m2,
        basis_key=BASIS_PRINT_AREA,
        basis_label="Arie print ofertata incl. waste",
        pricing_rate_key="workcenter_rates:LARGE_FORMAT_PRINT:per_square_meter",
        tpl_operation_key="PRINT_SOLVENT",
        operation_catalog_key="print_vinyl_artwork",
        workcenter_code="LARGE_FORMAT_PRINT",
    )
    if include_lamination:
        _append_operation_service_row(
            operation_rows,
            key=f"{key_prefix}_lamination_service",
            display_name=f"Serviciu laminare X-PRO — {display_suffix}",
            operation_type="lamination",
            quantity_m2=priced_area_m2,
            basis_key=BASIS_LAMINATE_AREA,
            basis_label="Arie laminare ofertata incl. waste",
            pricing_rate_key="workcenter_rates:WC_LAMINATE:per_square_meter",
            tpl_operation_key="LAMINATION",
            operation_catalog_key="laminare",
            workcenter_code="WC_LAMINATE",
        )
    if include_application:
        _append_operation_service_row(
            operation_rows,
            key=f"{key_prefix}_application_service",
            display_name=f"Serviciu aplicare — {display_suffix}",
            operation_type="vinyl_application",
            quantity_m2=priced_area_m2,
            basis_key=BASIS_PRINT_AREA,
            basis_label="Arie aplicare ofertata incl. waste",
            pricing_rate_key="workcenter_rates:WC_VINYL_APPLICATION:per_square_meter",
            tpl_operation_key="APPLY_VINYL",
            operation_catalog_key="colantare",
            workcenter_code="WC_VINYL_APPLICATION",
        )


def _append_artwork_complexity_print_preview(
    payload_raw: dict[str, Any],
    material_rows: list[IntakeV4MaterialQuantityRow],
    operation_preview_rows: list[IntakeV4CncOperationRow],
) -> None:
    assessments = list_artwork_complexity_assessments(payload_raw)
    operator_map = operator_artwork_application_map(payload_raw)
    for item in assessments:
        effective = effective_artwork_application(item, operator_map)
        if effective != "print_on_vinyl_laminated":
            continue
        try:
            area_f = float(item.get("artwork_area_estimate_m2") or 0)
        except (TypeError, ValueError):
            area_f = 0.0
        if area_f <= 0:
            continue
        artwork_id = str(item.get("artwork_id") or "artwork").replace(":", "_")
        layer_name = str(item.get("source_layer_name") or artwork_id)
        key_prefix = f"artwork_complexity_{artwork_id}"
        _append_print_laminate_quote_rows(
            area_m2=area_f,
            material_rows=material_rows,
            quantity_source="svg_analysis_json.artworkComplexity|covered_vector_area_estimate",
            key_prefix=key_prefix,
            display_suffix=layer_name,
        )
        operation_preview_rows.extend(
            build_artwork_print_operation_preview_rows(item, key_prefix, layer_name, area_f)
        )


def _append_artwork_active_return_rows(
    *,
    artwork_finishes: list[Any],
    analysis: dict[str, Any],
    default_return_finish: str,
    material_rows: list[IntakeV4MaterialQuantityRow],
) -> None:
    """Cant for artwork with active return — independent of print execution (Variant A)."""
    for row in artwork_finishes:
        if not isinstance(row, dict):
            continue
        execution = str(row.get("execution_type") or "needs_decision").strip().lower()
        if execution in VOLUMETRIC_ARTWORK_EXECUTION_TYPES:
            continue
        if not return_finish_active(row.get("return_finish_type")):
            continue
        layer_key = str(row.get("layer_key") or "")
        layer_name = str(row.get("layer_name") or layer_key)
        if not layer_key:
            continue
        _, perimeter_ml = _layer_metrics_from_analysis(analysis, layer_key, layer_name)
        if not perimeter_ml:
            continue
        return_finish = format_intake_v4_return_finish_operator_label(
            str(row.get("return_finish_type") or default_return_finish),
            default_return_finish,
        )
        depth = row.get("return_depth_mm")
        depth_label = f" · {depth} mm" if depth else ""
        ret_code = _return_registry_code(depth)
        material_rows.append(
            _cost_row(
                f"artwork_return_{layer_key}",
                f"Cant / volum emblemă — {layer_name} ({return_finish}){depth_label}",
                "material",
                perimeter_ml,
                EDGE_CANT_LINEAR_UNIT,
                quantity_basis=BASIS_PERIMETER,
                quantity_source="artwork_finishes|svg_analysis_json.layers|quote_geometry.artwork_return",
                quantity_quality="calculated",
                registry_code=ret_code,
            )
        )


def _artwork_row_counts_for_operator_cant(
    row: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
) -> bool:
    """True when artwork perimeter belongs in operator cant total.

    Matches intakeV4EdgeCantDisplay.buildIntakeV4EdgeCantLayerBreakdown: cant-active
    emblem/logo counts when vector perimeter exists (checked by caller). Print-laminate
    execution type does not exclude cant; raster-only without vector is excluded by
    missing perimeter, not by execution/role heuristics here.
    """
    _ = layer_role_setup
    return return_finish_active(row.get("return_finish_type"))


def _compute_operator_cant_perimeter_m(
    *,
    letter_groups: list[Any],
    artwork_finishes: list[Any],
    analysis: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    default_return_finish: str,
) -> tuple[float | None, float | None, float | None, list[IntakeV4MaterialBreakdownWarning]]:
    """Sum vector perimeters for cant-active letter groups + eligible emblem layers."""
    warnings: list[IntakeV4MaterialBreakdownWarning] = []
    letter_total = 0.0
    letter_any = False
    cant_active_missing_vector = False

    for group in letter_groups:
        if not isinstance(group, dict):
            continue
        finish = str(group.get("return_finish_type") or default_return_finish)
        if not return_finish_active(finish):
            continue
        perimeter = _positive(group.get("perimeter_m"))
        if perimeter is None:
            layer_key = str(group.get("group_key") or "")
            layer_name = str(group.get("layer_name") or layer_key)
            if layer_key or layer_name:
                _, perimeter = _layer_metrics_from_analysis(analysis, layer_key, layer_name)
        if perimeter:
            letter_total += perimeter
            letter_any = True
        else:
            cant_active_missing_vector = True

    artwork_total = 0.0
    artwork_any = False
    for row in artwork_finishes:
        if not isinstance(row, dict):
            continue
        if not _artwork_row_counts_for_operator_cant(row, layer_role_setup):
            continue
        layer_key = str(row.get("layer_key") or "")
        layer_name = str(row.get("layer_name") or layer_key)
        _, perimeter = _layer_metrics_from_analysis(analysis, layer_key, layer_name)
        if perimeter:
            artwork_total += perimeter
            artwork_any = True
        else:
            layer_label = layer_name or layer_key or "artwork"
            warnings.append(
                _warn(
                    "missing_artwork_perimeter",
                    f"Artwork volumetric „{layer_label}” — perimetru cant / volum indisponibil.",
                    source="svg_analysis_json.layers|artwork_finishes",
                )
            )

    if cant_active_missing_vector and not letter_any:
        warnings.append(
            _warn(
                "missing_operator_cant_perimeter",
                "Cant activ — perimetru vector indisponibil pentru straturi literă; verificare manuală necesară.",
                source="letter_group_finishes|svg_analysis_json.layers",
                severity="warning",
            )
        )

    letter_m = round(letter_total, 4) if letter_any else None
    artwork_m = round(artwork_total, 4) if artwork_any else None
    if letter_m is None and artwork_m is None:
        return None, None, None, warnings
    total = round((letter_m or 0.0) + (artwork_m or 0.0), 4)
    return total, letter_m, artwork_m, warnings


def _artwork_included_in_aggregated_volumetric_cant(
    artwork_finishes: list[Any],
    layer_role_setup: dict[str, Any] | None,
) -> bool:
    """True when cant-active artwork should appear in the combined cant material row."""
    _ = layer_role_setup
    return any(
        isinstance(row, dict) and return_finish_active(row.get("return_finish_type"))
        for row in artwork_finishes
    )


def _append_return_material_rows(
    *,
    letter_return_ml: float | None,
    artwork_return_ml: float | None,
    total_return_ml: float | None,
    inner_hole_letter_ml: float | None,
    letter_groups: list[Any],
    artwork_finishes: list[Any],
    layer_role_setup: dict[str, Any] | None,
    default_return_finish: str,
    default_return_depth: Any,
    return_finish: str,
    return_depth: Any,
    material_rows: list[IntakeV4MaterialQuantityRow],
) -> None:
    if not total_return_ml and not letter_return_ml:
        return

    has_separate_emblem = any(
        isinstance(row, dict)
        and str(row.get("execution_type") or "").strip().lower() in VOLUMETRIC_ARTWORK_EXECUTION_TYPES
        for row in artwork_finishes
    )
    active_artwork_returns = [
        row
        for row in artwork_finishes
        if isinstance(row, dict) and return_finish_active(row.get("return_finish_type"))
    ]
    split_artwork = any(
        not letter_and_artwork_return_profiles_match(
            letter_groups=letter_groups,
            artwork_finish=row,
            default_return_finish=default_return_finish,
            default_return_depth=default_return_depth,
        )
        for row in active_artwork_returns
    )

    depth_label = f" · {return_depth} mm" if return_depth else ""
    ret_code = _return_registry_code(return_depth)
    return_finish_display = format_intake_v4_return_finish_operator_label(
        return_finish,
        default_return_finish,
    )

    if has_separate_emblem or split_artwork:
        if letter_return_ml:
            material_rows.append(
                _cost_row(
                    "return_material",
                    f"Cant / volum litere + interioare ({return_finish_display}){depth_label}",
                    "material",
                    letter_return_ml,
                    EDGE_CANT_LINEAR_UNIT,
                    quantity_basis=BASIS_PERIMETER,
                    quantity_source="letter_group_finishes|quote_geometry.letter_return",
                    quantity_quality="calculated",
                    registry_code=ret_code,
                    confidence=CONFIDENCE_PERIMETER,
                )
            )
        return

    combined_ml = total_return_ml or letter_return_ml
    if not combined_ml:
        return
    artwork_in_label = _artwork_included_in_aggregated_volumetric_cant(
        artwork_finishes,
        layer_role_setup,
    )
    inferred_unclassified_artwork = bool(
        artwork_return_ml
        and not artwork_in_label
        and total_return_ml
        and letter_return_ml
        and total_return_ml > letter_return_ml + RAW_VECTOR_TOTAL_MIN_DELTA_M
    )
    if artwork_return_ml and not artwork_in_label and letter_return_ml and not inferred_unclassified_artwork:
        combined_ml = letter_return_ml
    has_inner = (inner_hole_letter_ml or 0) > 0
    if inferred_unclassified_artwork and has_inner:
        label = f"Cant / volum litere + interioare + vector neclasificat ({return_finish_display}){depth_label}"
    elif inferred_unclassified_artwork:
        label = f"Cant / volum litere + vector neclasificat ({return_finish_display}){depth_label}"
    elif artwork_in_label and has_inner:
        label = f"Cant / volum litere + interioare + artwork ({return_finish_display}){depth_label}"
    elif artwork_in_label:
        label = f"Cant / volum litere + artwork ({return_finish_display}){depth_label}"
    elif has_inner:
        label = f"Cant / volum litere + interioare eligibile ({return_finish_display}){depth_label}"
    else:
        label = f"Cant / volum litere — exterior + interioare eligibile ({return_finish_display}){depth_label}"
    if inferred_unclassified_artwork:
        source = "letter_group_finishes|path_geometry_summary.perimeter_mm_approx"
    else:
        source = (
            "letter_group_finishes|artwork_finishes|quote_geometry.return_material"
            if artwork_in_label or has_inner
            else "quote_geometry|path_geometry_summary"
        )
    material_rows.append(
        _cost_row(
            "return_material",
            label,
            "material",
            combined_ml,
            EDGE_CANT_LINEAR_UNIT,
            quantity_basis=BASIS_PERIMETER,
            quantity_source=source,
            quantity_quality="calculated",
            registry_code=ret_code,
            confidence=CONFIDENCE_PERIMETER,
        )
    )


def _append_artwork_print_rows(
    *,
    artwork_finishes: list[Any],
    analysis: dict[str, Any],
    quote_geometry: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    material_rows: list[IntakeV4MaterialQuantityRow],
    operation_rows: list[IntakeV4CncOperationRow] | None = None,
) -> None:
    source_part_ids_by_layer = _artwork_source_part_ids_by_layer(analysis, layer_role_setup)
    for row in artwork_finishes:
        if not isinstance(row, dict):
            continue
        execution = str(row.get("execution_type") or "needs_decision").strip().lower()
        if execution == "needs_decision":
            continue
        if execution not in PRINT_ARTWORK_EXECUTION_TYPES:
            continue
        layer_key = str(row.get("layer_key") or "")
        layer_name = str(row.get("layer_name") or layer_key)
        area = _artwork_box_area_for_layer(layer_key, layer_name, quote_geometry)
        quantity_source = "quote_geometry.artwork_boxes|bounding_box_footprint"
        if area is None:
            area = _positive(row.get("estimated_area_m2"))
            quantity_source = "artwork_finishes|svg_analysis_json.layers"
        if area is None:
            area, _ = _layer_metrics_from_analysis(analysis, layer_key, layer_name)
        if not area:
            continue
        include_lamination = execution in {"print_laminate", "printed_laminated_vinyl"}
        _append_print_laminate_quote_rows(
            area_m2=area,
            material_rows=material_rows,
            operation_rows=operation_rows,
            quantity_source=quantity_source,
            key_prefix=f"artwork_{layer_key}",
            display_suffix=layer_name,
            include_lamination=include_lamination,
        )
        source_part_ids = source_part_ids_by_layer.get(layer_key) or source_part_ids_by_layer.get(layer_name) or []
        for item in material_rows:
            if item.material_key in {f"artwork_{layer_key}_print_vinyl", f"artwork_{layer_key}_laminated_vinyl"}:
                item.source_part_ids = list(source_part_ids)


def _artwork_oracal_series(row: dict[str, Any]) -> str | None:
    material_code = str(row.get("material_code") or "").strip().upper()
    execution = str(row.get("execution_type") or "needs_decision").strip().lower()
    if material_code == "ORACAL_641":
        return "641"
    if material_code == "ORACAL_8500" or execution == "translucent_vinyl":
        return "8500"
    if material_code == "ORACAL_651" or execution == "cut_vinyl":
        return "651"
    return None


def _append_artwork_face_vinyl_rows(
    *,
    artwork_finishes: list[Any],
    analysis: dict[str, Any],
    quote_geometry: dict[str, Any],
    layer_role_setup: dict[str, Any] | None,
    material_rows: list[IntakeV4MaterialQuantityRow],
) -> None:
    source_part_ids_by_layer = _artwork_source_part_ids_by_layer(analysis, layer_role_setup)
    for row in artwork_finishes:
        if not isinstance(row, dict):
            continue
        if str(row.get("face_personalization_method") or "").strip().lower() != "oracal":
            continue
        series = _artwork_oracal_series(row)
        if not series:
            continue
        layer_key = str(row.get("layer_key") or "")
        layer_name = str(row.get("layer_name") or layer_key)
        area = _artwork_box_area_for_layer(layer_key, layer_name, quote_geometry)
        quantity_source = "quote_geometry.artwork_boxes|bounding_box_footprint"
        if area is None:
            area = _positive(row.get("estimated_area_m2"))
            quantity_source = "artwork_finishes|svg_analysis_json.layers"
        if area is None:
            area, _ = _layer_metrics_from_analysis(analysis, layer_key, layer_name)
        if not area:
            continue
        owner_price = resolve_intake_v4_owner_oracal_face_price(series)
        if not owner_price:
            continue
        unit_price, currency, price_source = owner_price
        material_rows.append(
            _cost_row(
                f"artwork_{layer_key}_face_vinyl_{series}",
                f"Vinil față Oracal {series} — {layer_name}",
                "material",
                area,
                "m2",
                quantity_basis=BASIS_AREA_FALLBACK,
                quantity_source=quantity_source,
                quantity_quality="calculated",
                registry_code=f"MAT-ORACAL-{series}",
                confidence=CONFIDENCE_AREA_FALLBACK,
                unit_price=unit_price,
                price_source=price_source,
                currency=currency,
                source_part_ids=source_part_ids_by_layer.get(layer_key) or source_part_ids_by_layer.get(layer_name) or [],
            )
        )


def _append_face_vinyl_application_rows(
    *,
    letter_groups: list[Any],
    default_face_finish: str,
    fallback_area_m2: float | None,
    operation_rows: list[IntakeV4CncOperationRow] | None,
) -> None:
    if operation_rows is None:
        return
    appended = False
    for group in letter_groups:
        if not isinstance(group, dict):
            continue
        face_finish = str(group.get("face_finish_type") or default_face_finish)
        if not _face_vinyl_required(face_finish) or _face_finish_is_print_laminate(face_finish):
            continue
        area_m2 = _positive(group.get("face_area_m2"))
        if not area_m2:
            continue
        layer_name = str(group.get("layer_name") or group.get("group_key") or "litere")
        group_key = str(group.get("group_key") or layer_name)
        priced_area_m2 = round(area_m2 * (1.0 + WASTE_PERCENT / 100.0), 4)
        _append_operation_service_row(
            operation_rows,
            key=f"letter_face_{group_key}_application_service",
            display_name=f"Serviciu aplicare — {layer_name}",
            operation_type="vinyl_application",
            quantity_m2=priced_area_m2,
            basis_key=BASIS_AREA_FALLBACK,
            basis_label="Arie aplicare vinil ofertata incl. waste",
            pricing_rate_key="workcenter_rates:WC_VINYL_APPLICATION:per_square_meter",
            tpl_operation_key="APPLY_VINYL",
            operation_catalog_key="colantare",
            workcenter_code="WC_VINYL_APPLICATION",
        )
        appended = True
    if appended or not fallback_area_m2 or fallback_area_m2 <= 0:
        return
    priced_area_m2 = round(fallback_area_m2 * (1.0 + WASTE_PERCENT / 100.0), 4)
    _append_operation_service_row(
        operation_rows,
        key="letter_face_application_service",
        display_name="Serviciu aplicare — litere",
        operation_type="vinyl_application",
        quantity_m2=priced_area_m2,
        basis_key=BASIS_AREA_FALLBACK,
        basis_label="Arie aplicare vinil ofertata incl. waste",
        pricing_rate_key="workcenter_rates:WC_VINYL_APPLICATION:per_square_meter",
        tpl_operation_key="APPLY_VINYL",
        operation_catalog_key="colantare",
        workcenter_code="WC_VINYL_APPLICATION",
    )


def _append_artwork_vinyl_application_rows(
    *,
    artwork_finishes: list[Any],
    analysis: dict[str, Any],
    quote_geometry: dict[str, Any],
    operation_rows: list[IntakeV4CncOperationRow] | None,
) -> None:
    if operation_rows is None:
        return
    for row in artwork_finishes:
        if not isinstance(row, dict):
            continue
        execution = str(row.get("execution_type") or "needs_decision").strip().lower()
        if execution not in {"vinyl_only", "cut_vinyl", "translucent_vinyl"}:
            continue
        layer_key = str(row.get("layer_key") or "")
        layer_name = str(row.get("layer_name") or layer_key)
        area = _artwork_box_area_for_layer(layer_key, layer_name, quote_geometry)
        if area is None:
            area = _positive(row.get("estimated_area_m2"))
        if area is None:
            area, _ = _layer_metrics_from_analysis(analysis, layer_key, layer_name)
        if not area:
            continue
        priced_area_m2 = round(area * (1.0 + WASTE_PERCENT / 100.0), 4)
        _append_operation_service_row(
            operation_rows,
            key=f"artwork_{layer_key}_application_service",
            display_name=f"Serviciu aplicare — {layer_name}",
            operation_type="vinyl_application",
            quantity_m2=priced_area_m2,
            basis_key=BASIS_AREA_FALLBACK,
            basis_label="Arie aplicare artwork ofertata incl. waste",
            pricing_rate_key="workcenter_rates:WC_VINYL_APPLICATION:per_square_meter",
            tpl_operation_key="APPLY_VINYL",
            operation_catalog_key="colantare",
            workcenter_code="WC_VINYL_APPLICATION",
        )


def _face_vinyl_required(face_finish: str) -> bool:
    token = face_finish.strip().lower()
    if token in {"none", "colored_plexiglas"}:
        return False
    return token in {
        "oracal_651",
        "oracal_8500",
        "oracal_641",
        "print_laminate",
        "printed_vinyl",
        "printed_laminated_vinyl",
        "oracal",
        "651",
        "8500",
    }


def _append_owner_oracal_face_vinyl_rows(
    *,
    letter_groups: list[Any],
    default_face_finish: str,
    total_area: float,
    material_rows: list[IntakeV4MaterialQuantityRow],
    quantity_basis: str,
    quantity_source: str,
    quantity_quality: str,
    confidence: str,
    apply_quote_waste: bool,
    roll_area_by_layer: dict[str, float] | None = None,
) -> bool:
    series_areas = face_oracal_vinyl_areas_by_series(
        letter_groups,
        default_face_finish,
        total_area,
        roll_area_by_layer=roll_area_by_layer,
    )
    if not series_areas:
        return False
    for series in sorted(series_areas):
        area = series_areas[series]
        owner_price = resolve_intake_v4_owner_oracal_face_price(series)
        if not owner_price:
            continue
        unit_price, currency, price_source = owner_price
        material_rows.append(
            _cost_row(
                f"face_vinyl_{series}",
                f"Vinil față Oracal {series}",
                "material",
                area,
                "m2",
                quantity_basis=quantity_basis,
                quantity_source=quantity_source,
                quantity_quality=quantity_quality,
                registry_code=f"MAT-ORACAL-{series}",
                apply_quote_waste=apply_quote_waste,
                confidence=confidence,
                unit_price=unit_price,
                price_source=price_source,
                currency=currency,
            )
        )
    return True


def _vinyl_area_from_letter_groups(
    letter_groups: list[Any],
    default_face_finish: str,
    fallback_area: float | None,
) -> float | None:
    """Sum vinyl-eligible face area per group; respect ``none`` (plexiglas brut)."""
    if not letter_groups:
        if _face_vinyl_required(default_face_finish):
            return fallback_area
        return None

    total = 0.0
    found = False
    for group in letter_groups:
        if not isinstance(group, dict):
            continue
        face_finish = str(group.get("face_finish_type") or default_face_finish)
        if not _face_vinyl_required(face_finish):
            continue
        area = _positive(group.get("face_area_m2"))
        if area:
            total += area
            found = True
    if found:
        return total
    if _face_vinyl_required(default_face_finish):
        return fallback_area
    return None


def _nesting_rows_from_analysis(nesting: dict[str, Any] | None) -> list[IntakeV4NestingMaterialRow]:
    if not isinstance(nesting, dict):
        return []
    rows: list[IntakeV4NestingMaterialRow] = []
    for sheet in nesting.get("sheets") or []:
        if not isinstance(sheet, dict):
            continue
        config_id = str(sheet.get("configId") or "sheet")
        label = SHEET_CONFIG_LABELS.get(config_id, config_id)
        sheets_used = int(sheet.get("sheetsUsed") or 0)
        if sheets_used <= 0:
            continue
        rows.append(
            IntakeV4NestingMaterialRow(
                material_key=f"nesting_sheet_{config_id}",
                display_name=label,
                nesting_kind="sheet",
                config_id=config_id,
                quantity=float(sheets_used),
                unit="buc",
                efficiency_percent=_float_metric([sheet], "efficiencyPercent"),
                waste_area_sqm=_float_metric([sheet], "wasteAreaSqm"),
                sheets_used=sheets_used,
            )
        )
    for roll in nesting.get("rolls") or []:
        if not isinstance(roll, dict):
            continue
        for job in roll.get("jobs") or []:
            if not isinstance(job, dict):
                continue
            consumed = _float_metric([job], "consumedLengthMm")
            if consumed is None:
                continue
            layer = job.get("sourceLayerName")
            color = job.get("colorKey")
            key_suffix = str(layer or color or "roll")
            rows.append(
                IntakeV4NestingMaterialRow(
                    material_key=f"nesting_roll_{key_suffix}",
                    display_name=f"Rolă vinil — {layer or color or 'material'}",
                    nesting_kind="roll",
                    source_layer=str(layer) if layer else None,
                    quantity=round(consumed / 1000.0, 3),
                    unit="ml",
                    efficiency_percent=_float_metric([job], "efficiencyPercent"),
                    consumed_length_mm=consumed,
                )
            )
    return rows


def _sheet_quote_candidates_to_schema(
    candidates: SheetQuoteMaterialCandidates,
) -> IntakeV4SheetQuoteMaterialCandidates:
    return IntakeV4SheetQuoteMaterialCandidates.model_validate(asdict(candidates))


def build_intake_v4_material_breakdown(
    workspace_id: str,
    payload_raw: dict[str, Any],
) -> IntakeV4MaterialBreakdownResponse:
    payload = _parse_payload(payload_raw)
    if payload.product_binding.template_code != PILOT_V4_TEMPLATE_CODE:
        raise HTTPException(
            status_code=422,
            detail={"error": "template_out_of_scope", "template_code": payload.product_binding.template_code},
        )

    warnings: list[IntakeV4MaterialBreakdownWarning] = []
    artwork_complexity_operation_rows: list[IntakeV4CncOperationRow] = []
    path_geom = payload.path_geometry_summary if isinstance(payload.path_geometry_summary, dict) else {}
    raw_quote_geom = payload_raw.get("quote_geometry") if isinstance(payload_raw.get("quote_geometry"), dict) else {}
    resolved_quote = resolve_v4_quote_geometry(payload)
    path_geom = merge_quote_geometry_into_path_summary(path_geom, resolved_quote)
    quote_geom = resolved_quote
    analysis = payload.svg_analysis_json if isinstance(payload.svg_analysis_json, dict) else {}
    geometry_block = analysis.get("geometry") if isinstance(analysis.get("geometry"), dict) else {}
    nesting = analysis.get("nesting") if isinstance(analysis.get("nesting"), dict) else {}
    finish = payload.finish_setup.model_dump(mode="json") if payload.finish_setup else {}
    raw_finish = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else {}

    if not analysis:
        warnings.append(_warn("missing_svg_analysis", "Lipsește analiza SVG persistată.", source="svg_analysis_json"))

    face_finish = str(finish.get("face_finish_type") or "oracal_651")
    default_return_finish = str(
        finish.get("return_finish_type") or INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE
    )
    illuminated = finish.get("illuminated") is not False
    global_return_depth = finish.get("return_depth_mm")
    letter_groups = finish.get("letter_group_finishes")
    if not isinstance(letter_groups, list):
        letter_groups = []
    artwork_finishes = finish.get("artwork_finishes")
    if not isinstance(artwork_finishes, list):
        artwork_finishes = []

    groups_present = bool(letter_groups)
    return_finish = resolve_effective_return_finish_label(
        letter_groups,
        artwork_finishes,
        default_return_finish,
    )
    return_depth = resolve_effective_return_depth_mm(
        letter_groups,
        artwork_finishes,
        global_return_depth,
    )
    face_vinyl_required_effective = (
        any_letter_group_face_vinyl_required(letter_groups, face_finish)
        if groups_present
        else _face_vinyl_required(face_finish)
    )
    print_laminate_effective = (
        any_letter_group_face_print_laminate(letter_groups, face_finish)
        if groups_present
        else _face_finish_is_print_laminate(face_finish)
    )
    artwork_only_face_finish = bool(artwork_finishes) and not groups_present
    if artwork_only_face_finish:
        face_vinyl_required_effective = False
        print_laminate_effective = False

    geom_sources = [path_geom, quote_geom, geometry_block]
    face_area = _float_metric(geom_sources, "face_area_m2", "letter_face_area_m2")
    backing_area = _float_metric(geom_sources, "backing_area_m2")
    vinyl_area_fallback = _float_metric(geom_sources, "vinyl_area_m2", "face_area_m2") or face_area
    return_ml = _float_metric(geom_sources, "return_material_perimeter_ml", "return_perimeter_m")
    letter_return_ml = _float_metric(geom_sources, "letter_return_perimeter_ml")
    artwork_return_ml = _float_metric(geom_sources, "artwork_return_perimeter_ml")
    inner_hole_letter_ml = _float_metric(geom_sources, "inner_hole_letter_perimeter_ml", "hole_perimeter_ml")
    letter_perimeter_ml = _float_metric(geom_sources, "total_letter_perimeter_ml", "letter_perimeter_m")
    if letter_return_ml is None:
        letter_return_ml = letter_perimeter_ml

    if not face_area and letter_groups:
        group_face_total = sum(_positive(group.get("face_area_m2")) or 0.0 for group in letter_groups if isinstance(group, dict))
        if group_face_total > 0:
            face_area = group_face_total
    if not return_ml and letter_groups:
        group_perimeter_total = sum(_positive(group.get("perimeter_m")) or 0.0 for group in letter_groups if isinstance(group, dict))
        if group_perimeter_total > 0:
            letter_return_ml = group_perimeter_total
            return_ml = group_perimeter_total + (artwork_return_ml or 0.0)
            if letter_perimeter_ml is None:
                letter_perimeter_ml = group_perimeter_total

    layer_role_setup_raw = payload_raw.get("layer_role_setup")
    layer_role_setup = layer_role_setup_raw if isinstance(layer_role_setup_raw, dict) else None
    quote_geom_dict = quote_geom if isinstance(quote_geom, dict) else {}
    backing_mode, backing_present, back_bevel_enabled = resolve_volumetric_backing_state(
        finish,
        layer_role_setup,
        quote_geometry=quote_geom_dict,
    )
    backing_mode_explicit = raw_finish.get("backing_mode") is not None
    backing_confirmed = backing_layer_confirmed(layer_role_setup) or backing_mode_explicit

    nesting_rows = _nesting_rows_from_analysis(nesting)
    roll_vinyl = compute_roll_nesting_vinyl_estimate(nesting, layer_role_setup=layer_role_setup)
    roll_vinyl_area_sqm = roll_vinyl.area_sqm
    roll_nesting_valid = roll_vinyl.fully_valid
    roll_area_by_layer = (
        compute_roll_nesting_vinyl_area_by_layer(nesting, layer_role_setup=layer_role_setup)
        if roll_vinyl_area_sqm is not None
        else None
    )
    sheet_split = compute_sheet_nesting_material_split(
        nesting,
        analysis,
        layer_role_setup,
        face_area=face_area,
        backing_area=backing_area,
    )
    sheet_split_pre_floor = sheet_split
    eligible_face_area_sum = compute_eligible_sheet_face_area_sum_sqm(
        analysis,
        layer_role_setup,
        letter_groups=letter_groups,
        artwork_finishes=artwork_finishes,
    )
    has_confirmed_letter_face_content = _has_confirmed_letter_face_content(
        layer_role_setup=layer_role_setup,
        letter_groups=letter_groups,
    )
    sheet_split, sheet_quantity_floor_applied = (
        (sheet_split, False)
        if sheet_split.mode == "prorated_fallback"
        else apply_sheet_material_quantity_floor(
            sheet_split,
            eligible_face_area_sqm=eligible_face_area_sum or face_area,
        )
    )
    sheet_quote_override = sheet_quote_override_from_payload(payload_raw)
    sheet_face_qty = sheet_split.face_area_sqm
    sheet_backing_qty = sheet_split.backing_area_sqm
    suppressed_logo_only_sheet_face_fallback = False
    if (
        sheet_split.mode == "prorated_fallback"
        and not has_confirmed_letter_face_content
        and bool(artwork_finishes)
    ):
        sheet_face_qty = None
        sheet_backing_qty = None
        suppressed_logo_only_sheet_face_fallback = True
    logo_only_artwork_box_footprint = (
        _artwork_box_footprint_area_sqm(raw_quote_geom, path_geom, quote_geom, geometry_block)
        if not has_confirmed_letter_face_content
        else None
    )
    logo_only_artwork_part_ids = (
        _logo_only_artwork_source_part_ids(analysis, layer_role_setup)
        if logo_only_artwork_box_footprint is not None
        else []
    )
    linked_logo_boxes = _linked_volumetric_logo_boxes(payload_raw) if has_confirmed_letter_face_content else []
    linked_logo_part_ids_by_layer = _linked_logo_source_part_ids_by_layer(analysis, layer_role_setup) if linked_logo_boxes else {}
    sheet_quote_candidates = compute_sheet_quote_material_candidates(
        nesting,
        analysis,
        layer_role_setup,
        eligible_face_area_sqm=eligible_face_area_sum or face_area,
        sheet_split_pre_floor=sheet_split_pre_floor,
        selected_quote_sheet_area_sqm=sheet_split.face_area_sqm,
        sheet_quantity_floor_applied=sheet_quantity_floor_applied,
        sheet_quote_override=sheet_quote_override,
    )
    from services.intake_v4_sheet_footprint_override_service import SheetFootprintCandidateAreas

    candidate_areas: SheetFootprintCandidateAreas | None = None
    if sheet_quote_candidates is not None:
        candidate_areas = SheetFootprintCandidateAreas(
            eligible_face_area_sqm=sheet_quote_candidates.eligible_face_area_sqm,
            placement_footprint_face_sqm=sheet_quote_candidates.placement_footprint_face_sqm,
            face_union_bbox_sqm=sheet_quote_candidates.face_union_bbox_sqm,
            layout_occupied_area_sqm=sheet_quote_candidates.layout_occupied_area_sqm,
            full_sheet_allocation_sqm=sheet_quote_candidates.full_sheet_allocation_sqm,
            operator_manual_footprint_sqm=sheet_quote_candidates.operator_manual_footprint_sqm,
        )
    sheet_face_qty, sheet_backing_qty, operator_footprint_applied = (
        apply_operator_footprint_to_sheet_material_quantities(
            sheet_face_qty=sheet_face_qty,
            sheet_backing_qty=sheet_backing_qty,
            override=sheet_quote_override,
            candidate_areas=candidate_areas,
            eligible_face_area_sqm=eligible_face_area_sum or face_area,
            base_selected_sqm=sheet_split.face_area_sqm,
            sheet_quantity_floor_applied=sheet_quantity_floor_applied,
        )
    )
    sheet_nesting_config = sheet_split.config_id
    sheet_nesting_valid = sheet_split.fully_valid
    sheet_quantity_basis = sheet_split.quantity_basis
    sheet_confidence = sheet_split.confidence
    vinyl_area = _vinyl_area_from_letter_groups(letter_groups, face_finish, vinyl_area_fallback)

    material_rows: list[IntakeV4MaterialQuantityRow] = []
    consumable_rows: list[IntakeV4MaterialQuantityRow] = []

    if face_area or sheet_face_qty or logo_only_artwork_box_footprint:
        if sheet_face_qty:
            material_rows.append(
                _cost_row(
                    "plexiglas_face",
                    "Plexiglas 3 mm",
                    "material",
                    sheet_face_qty,
                    "m2",
                    quantity_basis=sheet_quantity_basis,
                    quantity_source=f"svg_analysis_json.nesting|{sheet_nesting_config or 'sheet'}|{sheet_split.mode}",
                    quantity_quality="estimated",
                    registry_code=MATERIAL_REGISTRY_CODES["plexiglas_face"],
                    apply_quote_waste=False,
                    confidence=sheet_confidence if sheet_nesting_valid else CONFIDENCE_NESTING_MEDIUM,
                )
            )
        elif logo_only_artwork_box_footprint:
            material_rows.append(
                _cost_row(
                    "plexiglas_face",
                    "Plexiglas 3 mm",
                    "material",
                    logo_only_artwork_box_footprint,
                    "m2",
                    quantity_basis=BASIS_ARTWORK_BOX_FOOTPRINT,
                    quantity_source="quote_geometry.artwork_boxes|bounding_box_footprint",
                    quantity_quality="calculated",
                    registry_code=MATERIAL_REGISTRY_CODES["plexiglas_face"],
                    apply_quote_waste=False,
                    confidence=CONFIDENCE_NESTING_MEDIUM,
                    source_part_ids=logo_only_artwork_part_ids,
                    trace_markers=([] if logo_only_artwork_part_ids else ["SOURCE_PART_IDS_MISSING_FOR_LOGO_ONLY_FOOTPRINT"]),
                )
            )
        elif face_area:
            material_rows.append(
                _cost_row(
                    "plexiglas_face",
                    "Plexiglas 3 mm",
                    "material",
                    face_area,
                    "m2",
                    quantity_basis=BASIS_AREA_FALLBACK,
                    quantity_source="quote_geometry|path_geometry_summary",
                    quantity_quality="calculated",
                    registry_code=MATERIAL_REGISTRY_CODES["plexiglas_face"],
                    confidence=CONFIDENCE_AREA_FALLBACK,
                )
            )
    else:
        warnings.append(_warn("missing_face_area", "Suprafața față lipsește din geometrie.", source="geometry.face_area_m2"))

    backing_material_area, backing_material_basis, backing_material_source, backing_area_quoteable_fallback = (
        resolve_backing_material_area_m2(
            backing_confirmed=backing_confirmed,
            backing_area_m2=backing_area,
            sheet_backing_area_sqm=sheet_backing_qty,
            sheet_face_quoteable_area_sqm=sheet_face_qty,
            face_area_gross_m2=logo_only_artwork_box_footprint or face_area,
        )
    )
    if (
        logo_only_artwork_box_footprint is not None
        and backing_material_basis is not None
        and backing_material_area is not None
        and abs(backing_material_area - logo_only_artwork_box_footprint) < 1e-6
        and backing_material_basis != BASIS_BACKING_AREA_FACE_QUOTEABLE_FALLBACK
    ):
        backing_material_basis = BASIS_BACKING_AREA_ARTWORK_BOX_FOOTPRINT
        backing_material_source = "quote_geometry.artwork_boxes|bounding_box_footprint"
    if backing_area_quoteable_fallback:
        warnings.append(
            _warn(
                "backing_area_fallback_used",
                "Arie spate Forex — fallback din arie plexiglas ofertabilă / nesting (lipsește backing_area_m2 dedicată).",
                source="sheet_nesting_face_quoteable|backing_area_missing",
                severity="info",
            )
        )
    elif (
        backing_material_basis == BASIS_BACKING_AREA_ARTWORK_BOX_FOOTPRINT
        and backing_material_area is not None
    ):
        warnings.append(
            _warn(
                "backing_artwork_box_footprint_used",
                "Arie spate Forex — fallback explicit din bounding footprint artwork/logo deoarece backing dedicat lipsește.",
                source="quote_geometry.artwork_boxes|bounding_box_footprint",
                severity="info",
            )
        )

    if backing_confirmed and backing_material_area:
        if sheet_backing_qty and backing_material_area == sheet_backing_qty:
            material_rows.append(
                _cost_row(
                    "forex_backing",
                    "Forex 10 mm",
                    "material",
                    sheet_backing_qty,
                    "m2",
                    quantity_basis=sheet_quantity_basis,
                    quantity_source=f"svg_analysis_json.nesting|{sheet_nesting_config or 'sheet'}|{sheet_split.mode}",
                    quantity_quality="estimated",
                    registry_code=MATERIAL_REGISTRY_CODES["forex_backing"],
                    apply_quote_waste=False,
                    confidence=sheet_confidence if sheet_nesting_valid else CONFIDENCE_NESTING_MEDIUM,
                )
            )
        elif backing_material_basis == BASIS_BACKING_AREA_FACE_QUOTEABLE_FALLBACK:
            material_rows.append(
                _cost_row(
                    "forex_backing",
                    "Forex 10 mm",
                    "material",
                    backing_material_area,
                    "m2",
                    quantity_basis=backing_material_basis,
                    quantity_source=backing_material_source or "sheet_nesting_face_quoteable",
                    quantity_quality="estimated",
                    registry_code=MATERIAL_REGISTRY_CODES["forex_backing"],
                    apply_quote_waste=False,
                    confidence=sheet_confidence if sheet_nesting_valid else CONFIDENCE_NESTING_MEDIUM,
                )
            )
        elif backing_area and backing_material_area == backing_area:
            material_rows.append(
                _cost_row(
                    "forex_backing",
                    "Forex 10 mm",
                    "material",
                    backing_area,
                    "m2",
                    quantity_basis=BASIS_AREA_FALLBACK,
                    quantity_source="quote_geometry|path_geometry_summary",
                    quantity_quality="calculated",
                    registry_code=MATERIAL_REGISTRY_CODES["forex_backing"],
                    confidence=CONFIDENCE_AREA_FALLBACK,
                )
            )
        else:
            material_rows.append(
                _cost_row(
                    "forex_backing",
                    "Forex 10 mm",
                    "material",
                    backing_material_area,
                    "m2",
                    quantity_basis=backing_material_basis or BASIS_AREA_FALLBACK,
                    quantity_source=backing_material_source or "backing_area_fallback",
                    quantity_quality="estimated",
                    registry_code=MATERIAL_REGISTRY_CODES["forex_backing"],
                    confidence=CONFIDENCE_AREA_FALLBACK,
                    source_part_ids=logo_only_artwork_part_ids if backing_material_basis == BASIS_BACKING_AREA_ARTWORK_BOX_FOOTPRINT else None,
                    trace_markers=([] if logo_only_artwork_part_ids or backing_material_basis != BASIS_BACKING_AREA_ARTWORK_BOX_FOOTPRINT else ["SOURCE_PART_IDS_MISSING_FOR_LOGO_ONLY_FOOTPRINT"]),
                )
            )
    elif (backing_area or sheet_backing_qty or logo_only_artwork_box_footprint or backing_present) and not backing_confirmed:
        warnings.append(
            _warn(
                "backing_not_confirmed",
                "Backing neconfirmat — Forex/backing exclus din material estimate.",
                source="layer_role_setup",
                severity="info",
            )
        )

    for box in linked_logo_boxes:
        layer_key = str(box.get("layer_key") or "")
        layer_name = str(box.get("layer_name") or layer_key or "Linked logo")
        area = _positive(box.get("area_m2"))
        if area is None:
            continue
        source_part_ids = linked_logo_part_ids_by_layer.get(layer_key) or linked_logo_part_ids_by_layer.get(layer_name) or []
        trace_markers = [] if source_part_ids else ["SOURCE_PART_IDS_MISSING_FOR_LINKED_LOGO_FOOTPRINT"]
        material_rows.append(
            _cost_row(
                f"artwork_plexiglas_{layer_key}",
                f"Plexiglas față emblemă — {layer_name}",
                "material",
                area,
                "m2",
                quantity_basis=BASIS_LINKED_LOGO_FACE_FOOTPRINT,
                quantity_source="quote_geometry.artwork_boxes|bounding_box_footprint|linked_logo_segment",
                quantity_quality="calculated",
                registry_code=MATERIAL_REGISTRY_CODES["plexiglas_face"],
                apply_quote_waste=False,
                confidence=CONFIDENCE_NESTING_MEDIUM,
                source_part_ids=source_part_ids,
                trace_markers=trace_markers,
            )
        )
        material_rows.append(
            _cost_row(
                f"artwork_forex_backing_{layer_key}",
                f"Forex backing emblemă — {layer_name}",
                "material",
                area,
                "m2",
                quantity_basis=BASIS_LINKED_LOGO_BACKING_FOOTPRINT,
                quantity_source="quote_geometry.artwork_boxes|bounding_box_footprint|linked_logo_segment",
                quantity_quality="calculated",
                registry_code=MATERIAL_REGISTRY_CODES["forex_backing"],
                confidence=CONFIDENCE_NESTING_MEDIUM,
                source_part_ids=source_part_ids,
                trace_markers=trace_markers,
            )
        )
        warnings.append(
            _warn(
                "linked_logo_backing_fallback_used",
                f"Linked volumetric logo backing for {layer_name} folosește același bounding footprint ca fața logo, până la geometrie dedicată de backing.",
                source="quote_geometry.artwork_boxes|bounding_box_footprint|linked_logo_segment",
                severity="info",
            )
        )

    if print_laminate_effective and groups_present:
        for group in letter_groups:
            if not isinstance(group, dict):
                continue
            group_face = str(group.get("face_finish_type") or face_finish)
            if not _face_finish_is_print_laminate(group_face):
                continue
            group_area = _positive(group.get("face_area_m2"))
            layer_name = str(group.get("layer_name") or group.get("group_key") or "litere")
            group_key = str(group.get("group_key") or layer_name)
            _append_print_laminate_quote_rows(
                area_m2=group_area,
                material_rows=material_rows,
                operation_rows=artwork_complexity_operation_rows,
                quantity_source="letter_group_finishes|geometry",
                key_prefix=f"letter_face_{group_key}",
                display_suffix=layer_name,
                include_lamination=_print_finish_needs_lamination(group_face),
            )
    elif print_laminate_effective:
        _append_print_laminate_quote_rows(
            area_m2=face_area,
            material_rows=material_rows,
            operation_rows=artwork_complexity_operation_rows,
            quantity_source="finish_setup.face_finish_type|geometry",
            key_prefix="letter_face",
            display_suffix="litere",
            include_lamination=_print_finish_needs_lamination(face_finish),
        )

    elif face_vinyl_required_effective and (roll_vinyl_area_sqm or vinyl_area):
        if roll_vinyl_area_sqm:
            if _append_owner_oracal_face_vinyl_rows(
                letter_groups=letter_groups,
                default_face_finish=face_finish,
                total_area=roll_vinyl_area_sqm,
                material_rows=material_rows,
                quantity_basis=BASIS_ROLL_NESTING,
                quantity_source="svg_analysis_json.nesting|rolls",
                quantity_quality="estimated",
                apply_quote_waste=False,
                confidence=CONFIDENCE_NESTING_HIGH if roll_nesting_valid else CONFIDENCE_NESTING_MEDIUM,
                roll_area_by_layer=roll_area_by_layer,
            ):
                pass
            else:
                material_rows.append(
                    _cost_row(
                        "face_vinyl",
                        "Vinil față (per strat)",
                        "material",
                        roll_vinyl_area_sqm,
                        "m2",
                        quantity_basis=BASIS_ROLL_NESTING,
                        quantity_source="svg_analysis_json.nesting|rolls",
                        quantity_quality="estimated",
                        registry_code=MATERIAL_REGISTRY_CODES["face_vinyl"],
                        apply_quote_waste=False,
                        confidence=CONFIDENCE_NESTING_HIGH if roll_nesting_valid else CONFIDENCE_NESTING_MEDIUM,
                    )
                )
        elif vinyl_area:
            if _append_owner_oracal_face_vinyl_rows(
                letter_groups=letter_groups,
                default_face_finish=face_finish,
                total_area=vinyl_area,
                material_rows=material_rows,
                quantity_basis=BASIS_AREA_FALLBACK,
                quantity_source="letter_group_finishes|geometry",
                quantity_quality="calculated",
                apply_quote_waste=True,
                confidence=CONFIDENCE_AREA_FALLBACK,
            ):
                pass
            else:
                material_rows.append(
                    _cost_row(
                        "face_vinyl",
                        "Vinil față (per strat)",
                        "material",
                        vinyl_area,
                        "m2",
                        quantity_basis=BASIS_AREA_FALLBACK,
                        quantity_source="letter_group_finishes|geometry",
                        quantity_quality="calculated",
                        registry_code=MATERIAL_REGISTRY_CODES["face_vinyl"],
                        confidence=CONFIDENCE_AREA_FALLBACK,
                    )
                )
        elif face_vinyl_required_effective:
            warnings.append(
                _warn(
                    "missing_vinyl_area",
                    "Finisaj față Oracal — lipsește suprafața vinil și nesting rol.",
                    source="geometry.vinyl_area_m2",
                )
            )
        _append_face_vinyl_application_rows(
            letter_groups=letter_groups,
            default_face_finish=face_finish,
            fallback_area_m2=roll_vinyl_area_sqm or vinyl_area,
            operation_rows=artwork_complexity_operation_rows,
        )

    _append_artwork_complexity_print_preview(
        payload_raw,
        material_rows,
        artwork_complexity_operation_rows,
    )
    append_artwork_complexity_warnings(list_artwork_complexity_assessments(payload_raw), warnings)

    for row in artwork_finishes:
        if not isinstance(row, dict):
            continue
        execution = str(row.get("execution_type") or "needs_decision").strip().lower()
        if execution != "needs_decision":
            continue
        layer_name = str(row.get("layer_name") or row.get("layer_key") or "artwork")
        warnings.append(
            _warn(
                "artwork_execution_pending",
                f"Artwork „{layer_name}” — metodă execuție nedecisă; print/laminare blocate până la confirmare.",
                source="finish_setup.artwork_finishes",
                severity="warning",
            )
        )

    cant_letter_ml = letter_return_ml
    cant_artwork_ml = artwork_return_ml
    cant_total_ml = return_ml
    has_active_cant = any(
        return_finish_active(
            (group.get("return_finish_type") if isinstance(group, dict) else None) or default_return_finish
        )
        for group in letter_groups
    ) or any(
        return_finish_active(row.get("return_finish_type"))
        for row in artwork_finishes
        if isinstance(row, dict)
    )
    if letter_groups or artwork_finishes:
        operator_cant_m, operator_letter_m, operator_artwork_m, operator_cant_warnings = (
            _compute_operator_cant_perimeter_m(
                letter_groups=letter_groups,
                artwork_finishes=artwork_finishes,
                analysis=analysis,
                layer_role_setup=layer_role_setup,
                default_return_finish=default_return_finish,
            )
        )
        warnings.extend(operator_cant_warnings)
        if operator_cant_m is not None:
            cant_total_ml = operator_cant_m
            cant_letter_ml = operator_letter_m
            cant_artwork_ml = operator_artwork_m
        elif has_active_cant:
            cant_total_ml = None
            cant_letter_ml = None
            cant_artwork_ml = None

    raw_vector_total_ml = _raw_vector_total_perimeter_ml(path_geom)
    raw_vector_total_applied = False
    current_cant_total = cant_total_ml or return_ml
    if _raw_vector_total_should_override(raw_vector_total_ml, current_cant_total):
        raw_vector_total_applied = True
        path_geom = _path_geometry_with_raw_vector_total(path_geom, raw_vector_total_ml)
        previous_letter_or_total = cant_letter_ml or cant_total_ml or letter_return_ml or return_ml
        residual_ml = (
            round(raw_vector_total_ml - previous_letter_or_total, 4)
            if raw_vector_total_ml is not None and previous_letter_or_total is not None
            else None
        )
        cant_total_ml = raw_vector_total_ml
        if cant_letter_ml is None:
            cant_letter_ml = previous_letter_or_total or raw_vector_total_ml
        if residual_ml is not None and residual_ml > RAW_VECTOR_TOTAL_MIN_DELTA_M:
            cant_artwork_ml = round((cant_artwork_ml or 0.0) + residual_ml, 4)
        return_ml = cant_total_ml
        letter_return_ml = cant_letter_ml
        artwork_return_ml = cant_artwork_ml
        warnings.append(
            _warn(
                "raw_vector_total_perimeter_applied",
                (
                    "Perimetru vector total din SVG folosit pentru taiere/cant; "
                    "include contururi neclasificate de artwork/sigla."
                ),
                source="path_geometry_summary.perimeter_mm_approx",
                severity="info",
            )
        )
        if residual_ml is not None and residual_ml > RAW_VECTOR_TOTAL_MIN_DELTA_M:
            warnings.append(
                _warn(
                    "unclassified_vector_artwork_requires_decision",
                    (
                        f"Vector neclasificat detectat in SVG (~{residual_ml:.2f} m). "
                        "Operatorul trebuie sa confirme ce reprezinta, metoda de productie "
                        "si fisierul/grafica pentru handoff productie."
                    ),
                    source="path_geometry_summary.perimeter_mm_approx|finish_setup.artwork_finishes",
                    severity="warning",
                )
            )

    _append_return_material_rows(
        letter_return_ml=cant_letter_ml,
        artwork_return_ml=cant_artwork_ml,
        total_return_ml=cant_total_ml,
        inner_hole_letter_ml=inner_hole_letter_ml,
        letter_groups=letter_groups,
        artwork_finishes=artwork_finishes,
        layer_role_setup=layer_role_setup,
        default_return_finish=default_return_finish,
        default_return_depth=global_return_depth,
        return_finish=return_finish,
        return_depth=return_depth,
        material_rows=material_rows,
    )
    if return_depth is None and return_ml:
        ret_code = _return_registry_code(return_depth)
        if ret_code is None:
            warnings.append(
                _warn(
                    "missing_return_depth_registry",
                    "Cant — lipsește return_depth_mm pentru cod registry profil.",
                    source="finish_setup.return_depth_mm",
                )
            )

    has_separate_emblem = any(
        isinstance(row, dict)
        and str(row.get("execution_type") or "").strip().lower() in VOLUMETRIC_ARTWORK_EXECUTION_TYPES
        for row in artwork_finishes
    )
    split_artwork = any(
        isinstance(row, dict)
        and return_finish_active(row.get("return_finish_type"))
        and not letter_and_artwork_return_profiles_match(
            letter_groups=letter_groups,
            artwork_finish=row,
            default_return_finish=default_return_finish,
            default_return_depth=global_return_depth,
        )
        for row in artwork_finishes
    )
    if split_artwork and not has_separate_emblem:
        _append_artwork_active_return_rows(
            artwork_finishes=artwork_finishes,
            analysis=analysis,
            default_return_finish=default_return_finish,
            material_rows=material_rows,
        )

    _append_artwork_volumetric_rows(
        artwork_finishes=artwork_finishes,
        analysis=analysis,
        default_return_finish=default_return_finish,
        material_rows=material_rows,
        warnings=warnings,
    )
    _append_artwork_face_vinyl_rows(
        artwork_finishes=artwork_finishes,
        analysis=analysis,
        quote_geometry=quote_geom_dict,
        layer_role_setup=layer_role_setup,
        material_rows=material_rows,
    )

    _append_artwork_print_rows(
        artwork_finishes=artwork_finishes,
        analysis=analysis,
        quote_geometry=quote_geom_dict,
        layer_role_setup=layer_role_setup,
        material_rows=material_rows,
        operation_rows=artwork_complexity_operation_rows,
    )
    _append_artwork_vinyl_application_rows(
        artwork_finishes=artwork_finishes,
        analysis=analysis,
        quote_geometry=quote_geom_dict,
        operation_rows=artwork_complexity_operation_rows,
    )
    ral_paint_geometry = dict(path_geom)
    if cant_total_ml is not None:
        ral_paint_geometry["return_material_perimeter_ml"] = cant_total_ml
    if cant_letter_ml is not None:
        ral_paint_geometry["letter_return_perimeter_ml"] = cant_letter_ml
    if cant_artwork_ml is not None:
        ral_paint_geometry["artwork_return_perimeter_ml"] = cant_artwork_ml
    _append_ral_paint_spray_row(
        finish=finish,
        geometry=ral_paint_geometry,
        analysis=analysis,
        default_return_finish=default_return_finish,
        material_rows=material_rows,
    )

    if sheet_quantity_floor_applied:
        warnings.append(
            _warn(
                "sheet_nesting_quantity_floor_applied",
                "Nesting placă — cantitatea estimată a fost ridicată la suma ariilor fețelor eligibile (footprint nesting sub aria pieselor).",
                source="sheet_nesting|eligible_face_area_sum",
                severity="info",
            )
        )
    if sheet_quote_override and sheet_quote_override.get("areaSqm"):
        if sheet_quote_override.get("useForQuoteEstimate"):
            warnings.append(
                _warn(
                    "operator_sheet_footprint_estimate_active",
                    "Footprint manual operator folosit pentru estimarea internă material placă (nu consum stoc, nu preț final).",
                    source="sheet_quote_override|operator_manual_footprint",
                    severity="info",
                )
            )
        else:
            warnings.append(
                _warn(
                    "operator_sheet_footprint_candidate_saved",
                    "Footprint manual operator salvat ca candidat material placă — estimarea selectată rămâne pe floor arie eligibilă.",
                    source="sheet_quote_override|operator_manual_footprint",
                    severity="info",
                )
            )
    if sheet_split.used_sheet_area_sqm and not suppressed_logo_only_sheet_face_fallback:
        warnings.append(
            _warn(
                "nesting_used_for_quote_not_stock",
                "Nesting folosit pentru cantitate estimată de ofertă — nu consum real de stoc.",
                source="svg_analysis_json.nesting",
                severity="info",
            )
        )
    if sheet_split.mode == "prorated_fallback" and not suppressed_logo_only_sheet_face_fallback:
        warnings.append(
            _warn(
                "sheet_nesting_prorated_fallback",
                "Nesting placă — lipsesc metadata placements/role; suprafața plăcii este repartizată proporțional față/spate.",
                source="svg_analysis_json.nesting",
            )
        )
    elif suppressed_logo_only_sheet_face_fallback:
        warnings.append(
            _warn(
                "sheet_nesting_prorated_fallback_blocked_for_logo_only",
                "Nesting placă fallback pentru fața de litere a fost blocat: nu există Vector Litere confirmat, doar artwork/logo.",
                source="svg_analysis_json.nesting",
                severity="info",
            )
        )
    elif sheet_split.mode == "partial_role_split":
        warnings.append(
            _warn(
                "sheet_nesting_role_split_partial",
                "Nesting placă — split parțial pe role; placements fără metadata au fost alocate proporțional.",
                source="svg_analysis_json.nesting",
            )
        )
    elif sheet_split.unclassified_placements > 0:
        warnings.append(
            _warn(
                "missing_placement_role_metadata",
                "Nesting placă — unele placements nu au role/part kind confirmat.",
                source="svg_analysis_json.nesting",
            )
        )
    if roll_vinyl.job_count > 0 and len(roll_vinyl.color_keys) > 1:
        warnings.append(
            _warn(
                "roll_nesting_color_split_missing",
                "Nesting rolă — mai multe culori vinil în același rând Oracal (split pe culoare indisponibil).",
                source="svg_analysis_json.nesting|rolls",
            )
        )
    if roll_vinyl_area_sqm is None and vinyl_area and _face_vinyl_required(face_finish):
        warnings.append(
            _warn(
                "area_fallback_used",
                "Vinil Oracal — fallback arie folosit (nesting rolă indisponibil).",
                source="letter_group_finishes|geometry",
            )
        )

    lighting_system = str(finish.get("lighting_system_type") or "led_modules").strip().lower()
    is_led_strip = lighting_system == "led_strip"

    led_count_int: int | None = None
    if illuminated and not is_led_strip:
        total_led = finish.get("total_led_module_count")
        if total_led is not None:
            try:
                led_count_int = int(total_led)
            except (TypeError, ValueError):
                led_count_int = None
        if led_count_int is None:
            led_count = finish.get("led_module_count")
            if led_count is None:
                led_count = _compute_led_module_count(letter_perimeter_ml)
            if led_count:
                led_count_int = int(led_count)

    append_volumetric_adhesive_and_wiring_consumables(
        geom_sources=geom_sources,
        letter_return_ml=(cant_total_ml if raw_vector_total_applied else cant_letter_ml),
        total_return_ml=cant_total_ml,
        artwork_return_ml=(None if raw_vector_total_applied else cant_artwork_ml),
        illuminated=illuminated,
        led_module_count=led_count_int,
        consumable_rows=consumable_rows,
        warnings=warnings,
    )

    if illuminated:
        module_wattage = normalize_led_module_power_w(finish.get("led_module_power_w"))
        strip_power = normalize_led_strip_power_w_per_ml(finish.get("led_strip_power_w_per_ml"))
        led_total_watts = finish.get("estimated_led_watts")
        if is_led_strip:
            strip_length_m = _positive(finish.get("total_led_strip_length_m"))
            if strip_length_m is None:
                letter_strip_m = _positive(finish.get("letter_led_strip_length_m")) or letter_perimeter_ml
                emblem_strip_m = _positive(finish.get("emblem_led_strip_length_m"))
                if emblem_strip_m is None and str(finish.get("emblem_lighting_mode") or "").strip().lower() == "area_lit":
                    emblem_strip_m = calculate_led_strip_length_by_area(_float_metric(geom_sources, "artwork_area_m2"))
                if letter_strip_m is not None or emblem_strip_m is not None:
                    strip_length_m = round((letter_strip_m or 0.0) + (emblem_strip_m or 0.0), 3)
            if strip_length_m:
                consumable_rows.append(
                    _cost_row(
                        "led_strip",
                        f"Banda LED ({strip_power:g} W / ml)",
                        "consumable",
                        float(strip_length_m),
                        "ml",
                        quantity_basis="led_strip_continuous_length_estimate",
                        quantity_source=f"finish_setup.total_led_strip_length_m|strip_power_w_per_ml={strip_power:g}",
                        quantity_quality="calculated",
                        registry_code=MATERIAL_REGISTRY_CODES["led_strip"],
                        confidence=CONFIDENCE_FORMULA,
                    )
                )
                if led_total_watts is not None:
                    consumable_rows.append(
                        _cost_row(
                            "led_total_watts",
                            "Consum LED total (banda x W/ml) - informativ",
                            "consumable",
                            float(led_total_watts),
                            "W",
                            quantity_basis="led_strip_length_x_w_per_ml",
                            quantity_source="finish_setup.estimated_led_watts",
                            quantity_quality="calculated",
                            registry_code=None,
                            price_source=PRICE_SOURCE_INFORMATIONAL,
                            confidence=CONFIDENCE_FORMULA,
                        )
                    )
            else:
                warnings.append(
                    _warn(
                        "missing_led_strip_length",
                        "Iluminare activa - lungime banda LED indisponibila.",
                        source="finish_setup.total_led_strip_length_m",
                    )
                )
        elif led_count_int:
            consumable_rows.append(
                _cost_row(
                    "led_modules",
                    f"Module LED ({module_wattage:g} W / buc)",
                    "consumable",
                    float(led_count_int),
                    "buc",
                    quantity_basis="led_modules_perimeter_pitch_estimate",
                    quantity_source=f"finish_setup|geometry_perimeter|module_wattage={module_wattage:g}",
                    quantity_quality="estimated",
                    registry_code=MATERIAL_REGISTRY_CODES["led_modules"],
                    confidence=CONFIDENCE_FORMULA,
                )
            )
            if led_total_watts is not None:
                consumable_rows.append(
                    _cost_row(
                        "led_total_watts",
                        "Consum LED total (module × putere) — informativ",
                        "consumable",
                        float(led_total_watts),
                        "W",
                        quantity_basis="led_modules_count_x_module_wattage",
                        quantity_source="finish_setup.estimated_led_watts",
                        quantity_quality="calculated",
                        registry_code=None,
                        price_source=PRICE_SOURCE_INFORMATIONAL,
                        confidence=CONFIDENCE_FORMULA,
                    )
                )
        else:
            warnings.append(_warn("missing_led_count", "Iluminare activă — număr module LED indisponibil.", source="geometry.perimeter"))

        psu_config = finish.get("psu_configuration")
        grouped_psu = _group_psu_configuration(psu_config if isinstance(psu_config, list) else None)
        if grouped_psu:
            watts_required = finish.get("required_psu_watts")
            for watts_value, psu_code, psu_count in grouped_psu:
                label = (
                    f"Sursă LED 12V {watts_value}W ({watts_required} W necesari)"
                    if watts_required
                    else f"Sursă LED 12V {watts_value}W"
                )
                row = _cost_row(
                    f"led_psu_{watts_value}w",
                    label,
                    "consumable",
                    float(psu_count),
                    "buc",
                    quantity_basis="psu_configuration_quote_estimate",
                    quantity_source="finish_setup.psu_configuration",
                    quantity_quality="calculated",
                    registry_code=psu_code or "MAT-LED-PSU-12V",
                    confidence=CONFIDENCE_FORMULA,
                )
                row.trace_markers = list(row.trace_markers or []) + [f"psu_wattage:{watts_value}"]
                if psu_code is None:
                    row.warnings = list(row.warnings or []) + [
                        f"PSU material missing for {watts_value}W"
                    ]
                    row.price_source = "missing"
                    row.registry_code = "MAT-LED-PSU-12V"
                consumable_rows.append(row)
        elif finish.get("required_psu_watts"):
            warnings.append(_warn("missing_psu_config", "Consum LED estimat — configurează sursele PSU.", source="finish_setup.psu_configuration"))

    edge_cant_result = evaluate_edge_cant_rules(
        EdgeCantRuleInput(
            template_key=payload.product_binding.template_code,
            edge_depth_mm=float(return_depth) if return_depth is not None else None,
            edge_finish_key=return_finish,
            letter_return_ml=(cant_total_ml if raw_vector_total_applied else cant_letter_ml),
            total_return_ml=cant_total_ml,
            artwork_return_ml=(None if raw_vector_total_applied else cant_artwork_ml),
            letter_groups=letter_groups,
            default_return_finish=default_return_finish,
            edge_quote_waste_factor=DEFAULT_QUOTE_WASTE_PERCENT,
        )
    )
    for edge_material_row in edge_cant_result.material_rows:
        material_rows.append(edge_material_row)
    edge_cant_operation_rows = list(edge_cant_result.operation_rows)

    total = 0.0
    contains_estimates = False
    contains_missing_prices = False
    for row in material_rows + consumable_rows:
        if row.quantity_quality == "estimated":
            contains_estimates = True
        if _is_price_missing_for_quantity(row):
            contains_missing_prices = True
        if row.estimated_cost is not None:
            total += row.estimated_cost
        elif row.material_cost is not None:
            total += row.material_cost
    for row in edge_cant_operation_rows:
        if _is_price_missing_for_operation(row):
            contains_missing_prices = True
        total += _operation_estimated_cost(row)

    cost_total = round(total, 2)
    nesting_preview = build_intake_v4_nesting_preview(
        payload_raw,
        workspace_id=workspace_id,
        material_rows=material_rows,
        face_area=face_area,
        backing_area=backing_area if backing_confirmed else None,
    )

    back_bevel_enabled = back_bevel_enabled
    layer_backing_specs: list[tuple[float, str]] = []
    for group in letter_groups:
        if not isinstance(group, dict):
            continue
        perimeter = _positive(group.get("perimeter_m"))
        if perimeter is None:
            continue
        layer_backing_specs.append(
            (perimeter, resolve_layer_backing_mode(group, finish if isinstance(finish, dict) else None))
        )
    if not layer_backing_specs and artwork_finishes:
        back_ml = _positive(
            path_geom.get("backing_cnc_cutting_perimeter_ml")
            if isinstance(path_geom, dict)
            else None
        ) or _positive(
            path_geom.get("back_cutting_perimeter_ml") if isinstance(path_geom, dict) else None
        ) or _positive(
            path_geom.get("face_cutting_perimeter_ml") if isinstance(path_geom, dict) else None
        )
        if back_ml is not None:
            for artwork in artwork_finishes:
                if not isinstance(artwork, dict):
                    continue
                layer_backing_specs.append(
                    (
                        back_ml,
                        resolve_layer_backing_mode(
                            artwork,
                            finish if isinstance(finish, dict) else None,
                        ),
                    )
                )
    if layer_backing_specs:
        cnc_preview_rows = build_volumetric_letters_cnc_operation_rows_with_layer_backing(
            path_geom,
            layer_backing_specs=layer_backing_specs,
            configured_rate_eur_per_ml_pass=None,
        )
    else:
        cnc_preview_rows = build_volumetric_letters_cnc_operation_rows(
            path_geom,
            backing_mode=backing_mode,
            configured_rate_eur_per_ml_pass=None,
        )
    operation_rows = [
        IntakeV4CncOperationRow.model_validate(row_dict)
        for row_dict in rows_to_schema_dicts(cnc_preview_rows)
    ]
    operation_rows.extend(artwork_complexity_operation_rows)

    return IntakeV4MaterialBreakdownResponse(
        workspace_id=workspace_id,
        template_code=payload.product_binding.template_code,
        policy_version=QUOTE_MATERIAL_COSTING_POLICY_V1,
        quote_waste_percent_default=DEFAULT_QUOTE_WASTE_PERCENT,
        nesting_rows=nesting_rows,
        material_rows=material_rows,
        consumable_rows=consumable_rows,
        operation_rows=operation_rows,
        edge_cant_operation_rows=edge_cant_operation_rows,
        nesting_preview=nesting_preview,
        sheet_quote_material_candidates=(
            _sheet_quote_candidates_to_schema(sheet_quote_candidates)
            if sheet_quote_candidates is not None
            else None
        ),
        totals=IntakeV4MaterialBreakdownTotals(
            material_cost_total=cost_total,
            estimated_cost_total=cost_total,
            currency="EUR",
            contains_estimates=contains_estimates,
            contains_missing_prices=contains_missing_prices,
        ),
        warnings=warnings,
    )


async def build_intake_v4_material_breakdown_with_registry(
    db: AsyncSession,
    workspace_id: str,
    payload_raw: dict[str, Any],
) -> IntakeV4MaterialBreakdownResponse:
    response = build_intake_v4_material_breakdown(workspace_id, payload_raw)
    material_rows = await _apply_registry_prices(db, response.material_rows)
    consumable_rows = await _apply_registry_prices(db, response.consumable_rows)
    operation_rows = await _apply_registry_operation_prices(db, response.operation_rows)
    edge_cant_operation_rows = await _apply_registry_operation_prices(db, response.edge_cant_operation_rows)
    warnings = list(response.warnings)
    manufacturing_subtotal = _manufacturing_cost_subtotal_before_markup(
        material_rows=material_rows,
        consumable_rows=consumable_rows,
        operation_rows=operation_rows,
        edge_cant_operation_rows=edge_cant_operation_rows,
    )
    mounting_accessories_row = _build_mounting_accessories_percent_row(manufacturing_subtotal)
    if mounting_accessories_row is not None:
        consumable_rows = [*consumable_rows, mounting_accessories_row]
        warnings.append(
            _warn(
                "mounting_accessories_internal_cost_percent_applied",
                (
                    "Accesorii/conectori montaj calculate intern ca 5% din subtotalul de "
                    "confectie, inainte de adaos comercial; baza nu este pretul ofertat clientului."
                ),
                source=f"material_breakdown.{MOUNTING_ACCESSORIES_COST_BASIS}",
                severity="info",
            )
        )
    total = 0.0
    contains_missing_prices = False
    for row in material_rows + consumable_rows:
        if _is_price_missing_for_quantity(row):
            contains_missing_prices = True
        if row.estimated_cost is not None:
            total += row.estimated_cost
        elif row.material_cost is not None:
            total += row.material_cost
    for row in operation_rows:
        if _is_price_missing_for_operation(row):
            contains_missing_prices = True
        if row.estimated_cost is not None:
            total += row.estimated_cost
    for row in edge_cant_operation_rows:
        if _is_price_missing_for_operation(row):
            contains_missing_prices = True
        if row.estimated_cost is not None:
            total += row.estimated_cost
    cost_total = round(total, 2)
    return response.model_copy(
        update={
            "material_rows": material_rows,
            "consumable_rows": consumable_rows,
            "operation_rows": operation_rows,
            "edge_cant_operation_rows": edge_cant_operation_rows,
            "nesting_preview": response.nesting_preview,
            "warnings": warnings,
            "totals": response.totals.model_copy(
                update={
                    "material_cost_total": cost_total,
                    "estimated_cost_total": cost_total,
                    "contains_missing_prices": contains_missing_prices,
                }
            ),
        }
    )


async def get_material_breakdown_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV4MaterialBreakdownResponse:
    from services.intake_v4_analysis_boundary_service import assert_v4_analysis_boundary_or_raise

    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}
    payload = _parse_payload(payload_raw)
    assert_v4_analysis_boundary_or_raise(payload)
    return await build_intake_v4_material_breakdown_with_registry(db, workspace_id, payload_raw)


async def get_nesting_preview_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV4NestingPreviewResponse:
    breakdown = await get_material_breakdown_for_workspace(db, workspace_id)
    if breakdown.nesting_preview is not None:
        return breakdown.nesting_preview
    from schemas.intake_v4 import IntakeV4NestingPreviewBoundary, IntakeV4NestingPreviewResponse

    return IntakeV4NestingPreviewResponse(
        preview_only=True,
        mutates_inventory=False,
        uses_stock=False,
        source="intake_v4_workspace",
        workspace_id=workspace_id,
        disclaimer="Nesting preview unavailable for this workspace payload.",
        boundary=IntakeV4NestingPreviewBoundary(),
        warnings=[],
    )
