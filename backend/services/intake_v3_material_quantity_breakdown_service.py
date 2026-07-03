"""Intake V3 material quantity / geometry / material cost breakdown — read-only, materials-only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data_models.intake_v3_contracts import PILOT_TEMPLATE_CODE
from models.inventory_materials import Inventory_materials
from models.orders import Orders
from models.quotes import Quotes
from schemas.intake_v3 import (
    ConfirmedProductionModel,
    FinishAssignment,
    IntakeV3GeometrySummary,
    IntakeV3MaterialBreakdownResponse,
    IntakeV3MaterialBreakdownTotals,
    IntakeV3MaterialBreakdownWarning,
    IntakeV3MaterialCostRow,
    IntakeV3MaterialQuantityRow,
    IntakeV3Workspace,
)
from services.intake_v3_draft_quote_review_service import parse_intake_v3_quote_notes
from services.intake_v3_finish_material_service import derive_material_intent
from services.intake_v3_order_production_readiness_service import (
    _load_workspace_from_sections,
    _resolve_product_template,
    _snapshot_sections,
    is_iv3_order,
    load_iv3_order_linkage,
    load_quote_intake_v3_linkage,
    load_source_quote_for_iv3_order,
)
from services.intake_v3_pricing_input_adapter import build_pricing_input_candidate
from services.intake_v3_real_commercial_quote_creation_service import (
    INTAKE_V3_SOURCE_MODULE,
    check_existing_quote_for_intake_v3_workspace,
)
from services.intake_v3_workspace_service import sanitize_intake_v3_workspace_payload
from services.orders import OrdersService
from services.quotes import QuotesService
from services.volumetric_material_rate_resolver import PROFILE_DEPTH_MM_TO_VARIANT_CODE

WASTE_PERCENT = 20.0
BREAKDOWN_SCOPE = "materials_only_informative"

OWNER_CONFIRMED_FALLBACKS: dict[str, dict[str, Any]] = {
    "plexiglas_face": {
        "registry_code": "MAT-ACP-FATA-LITERE",
        "unit_price": 16.0,
        "currency": "EUR",
        "unit": "m2",
    },
    "forex_backing": {
        "registry_code": "MAT-SPATE-PVC-LITERE",
        "unit_price": 16.0,
        "currency": "EUR",
        "unit": "m2",
    },
    "face_vinyl": {
        "registry_code": "MAT-ORACAL-651",
        "unit_price": 5.0,
        "currency": "EUR",
        "unit": "m2",
    },
    "led_modules": {
        "registry_code": "MAT-LED-MODULE",
        "unit_price": 0.5,
        "currency": "EUR",
        "unit": "buc",
    },
}

RETURN_DEPTH_FALLBACK_EUR_ML: dict[int, float] = {30: 2.0, 60: 3.0, 80: 4.0, 100: 5.0}
PSU_FALLBACK_REGISTRY_CODE = "MAT-LED-PSU-12V"

GEOMETRY_KEY_ALIASES: dict[str, tuple[str, ...]] = {
    "face_cutting_perimeter_ml": ("face_cutting_perimeter_ml", "face_cutting_perimeter_m"),
    "total_letter_perimeter_ml": ("total_letter_perimeter_ml", "letter_perimeter_m", "letter_perimeter_ml"),
    "return_material_perimeter_ml": (
        "return_material_perimeter_ml",
        "return_perimeter_m",
        "return_material_perimeter_m",
    ),
    "cutting_perimeter_ml": ("cutting_perimeter_ml", "cut_perimeter_m", "total_cut_perimeter_m"),
    "bevel_perimeter_ml": ("bevel_perimeter_ml", "bevel_perimeter_m"),
    "face_area_m2": ("face_area_m2", "letter_face_area_m2"),
    "backing_area_m2": ("backing_area_m2", "letter_backing_area_m2"),
    "vinyl_area_m2": ("vinyl_area_m2", "face_vinyl_area_m2", "letter_face_area_m2"),
    "led_module_count": ("led_module_count", "led_modules_count", "led_count"),
    "led_power_supply_count": ("led_power_supply_count", "psu_count", "power_supply_count"),
}


@dataclass
class Iv3SourceContext:
    source_type: str
    source_id: str
    is_intake_v3: bool
    order: Orders | None
    quote: Quotes | None
    quote_linkage: dict[str, Any] | None
    order_linkage: dict[str, Any] | None
    sections: dict[str, Any]
    linkage_sections: dict[str, Any]
    workspace: IntakeV3Workspace | None
    product_template: str


def _warning(
    code: str,
    message: str,
    *,
    severity: str = "warning",
    source: str,
) -> IntakeV3MaterialBreakdownWarning:
    return IntakeV3MaterialBreakdownWarning(
        code=code,
        severity=severity,
        message=message,
        source=source,
    )


def _positive_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _positive_int(value: Any) -> int | None:
    parsed = _positive_float(value)
    if parsed is None:
        return None
    return int(parsed)


def _apply_waste(quantity: float | None) -> float | None:
    if quantity is None:
        return None
    return round(quantity * (1.0 + WASTE_PERCENT / 100.0), 6)


def _collect_geometry_sources(sections: dict[str, Any], workspace: IntakeV3Workspace | None) -> dict[str, Any]:
    from services.intake_v3_geometry_metrics_snapshot_service import (
        parse_snapshot_from_sections,
        parse_snapshot_from_workspace,
        snapshot_to_legacy_geometry_dict,
    )

    merged: dict[str, Any] = {}
    snapshot = parse_snapshot_from_sections(sections)
    if snapshot is None:
        snapshot = parse_snapshot_from_workspace(workspace)
    if snapshot is not None:
        merged.update(snapshot_to_legacy_geometry_dict(snapshot))

    sources: list[dict[str, Any]] = []
    for key in ("geometry_metrics_snapshot", "layer_role_confirmation_snapshot"):
        payload = sections.get(key)
        if isinstance(payload, dict):
            sources.append(payload)
            if key == "layer_role_confirmation_snapshot":
                status = payload.get("confirmation_status")
                if status:
                    merged["layer_role_confirmation_status"] = status
    confirmed_raw = sections.get("confirmed_production_model_snapshot")
    if isinstance(confirmed_raw, dict):
        nested = confirmed_raw.get("geometry_metrics")
        if isinstance(nested, dict):
            sources.append(nested)
    pricing_raw = sections.get("pricing_input_candidate_snapshot")
    if isinstance(pricing_raw, dict):
        quote_input = pricing_raw.get("quote_input_payload")
        if isinstance(quote_input, dict):
            sources.append(quote_input)
    if workspace is not None:
        candidate = build_pricing_input_candidate(workspace)
        sources.append(candidate.quote_input_payload)
        if workspace.layer_role_confirmation_snapshot and isinstance(
            workspace.layer_role_confirmation_snapshot, dict
        ):
            status = workspace.layer_role_confirmation_snapshot.get("confirmation_status")
            if status:
                merged["layer_role_confirmation_status"] = status
        dims = candidate.candidate.dimensions
        if dims.area_m2 is not None:
            sources.append(
                {
                    "bounding_box_area_m2": dims.area_m2,
                    "width_mm": dims.width_mm,
                    "height_mm": dims.height_mm,
                }
            )
    for source in sources:
        merged.update(source)
    return merged


def _read_geometry_metric(sources: dict[str, Any], canonical_key: str) -> float | None:
    for alias in GEOMETRY_KEY_ALIASES.get(canonical_key, (canonical_key,)):
        value = _positive_float(sources.get(alias))
        if value is not None:
            return value
    return None


def extract_confirmed_production_model(context: Iv3SourceContext) -> ConfirmedProductionModel | None:
    raw = context.sections.get("confirmed_production_model_snapshot")
    if isinstance(raw, dict):
        try:
            return ConfirmedProductionModel.model_validate(raw)
        except Exception:
            return None
    if context.workspace and context.workspace.confirmed_production_model:
        return context.workspace.confirmed_production_model
    return None


def extract_finish_assignments(context: Iv3SourceContext) -> FinishAssignment | None:
    raw = context.sections.get("finish_assignment_snapshot")
    if isinstance(raw, dict):
        try:
            return FinishAssignment.model_validate(raw)
        except Exception:
            return None
    if context.workspace and context.workspace.finish_assignment:
        return context.workspace.finish_assignment
    return None


def extract_geometry_summary(context: Iv3SourceContext) -> tuple[IntakeV3GeometrySummary, list[IntakeV3MaterialBreakdownWarning]]:
    warnings: list[IntakeV3MaterialBreakdownWarning] = []
    confirmed = extract_confirmed_production_model(context)
    geometry_sources = _collect_geometry_sources(context.sections, context.workspace)
    snapshot_source = geometry_sources.get("geometry_snapshot_source")

    real_letters = confirmed.letter_count if confirmed else 0
    closed_contours = confirmed.cut_contour_count if confirmed else 0
    holes = confirmed.inner_hole_count if confirmed else 0
    outer_contours = 0
    if confirmed and confirmed.cut_contour_model:
        outer_contours = confirmed.cut_contour_model.outer_contour_count or 0
        if outer_contours == 0:
            outer_contours = sum(
                1 for c in confirmed.cut_contour_model.contours if c.role == "outer"
            )

    total_letter_perimeter = _read_geometry_metric(geometry_sources, "total_letter_perimeter_ml")
    face_cutting_perimeter = _read_geometry_metric(geometry_sources, "face_cutting_perimeter_ml")
    cutting_perimeter: float | None = None
    if face_cutting_perimeter is not None:
        total_letter_perimeter = face_cutting_perimeter
        cutting_perimeter = face_cutting_perimeter
    return_perimeter = _read_geometry_metric(geometry_sources, "return_material_perimeter_ml")
    if cutting_perimeter is None:
        cutting_perimeter = _read_geometry_metric(geometry_sources, "cutting_perimeter_ml")
    bevel_perimeter = _read_geometry_metric(geometry_sources, "bevel_perimeter_ml")

    perimeter_classification_status = geometry_sources.get("perimeter_classification_status")
    perimeter_classification_confidence = geometry_sources.get("perimeter_classification_confidence")
    perimeter_classification_source = None
    layer_role_confirmation_status = geometry_sources.get("layer_role_confirmation_status")
    operator_confirmed_layer_roles = False
    if geometry_sources.get("geometry_path_perimeter_classification"):
        perimeter_classification_source = "geometry_path_perimeter_classification"
    elif perimeter_classification_status:
        perimeter_classification_source = "geometry_metrics_snapshot.path_perimeter_classification"
    if layer_role_confirmation_status in {"complete", "partial"}:
        operator_confirmed_layer_roles = True
        if perimeter_classification_source:
            perimeter_classification_source = (
                "operator_confirmed_layer_role+" + perimeter_classification_source
            )
        else:
            perimeter_classification_source = "operator_confirmed_layer_role"

    classification = geometry_sources.get("path_perimeter_classification")
    if isinstance(classification, dict):
        perimeter_classification_status = perimeter_classification_status or classification.get(
            "classification_status"
        )
        for code in (
            "backing_perimeter_missing",
            "return_perimeter_missing",
            "bevel_perimeter_missing",
            "contour_role_split_missing",
            "face_perimeter_missing",
        ):
            if any(item.get("code") == code for item in classification.get("warnings") or [] if isinstance(item, dict)):
                warnings.append(
                    _warning(
                        code,
                        f"Path perimeter classification: {code.replace('_', ' ')}.",
                        source="geometry_path_perimeter_classification",
                    )
                )
    face_area = _read_geometry_metric(geometry_sources, "face_area_m2")
    backing_area = _read_geometry_metric(geometry_sources, "backing_area_m2")
    vinyl_area = _read_geometry_metric(geometry_sources, "vinyl_area_m2")

    area_quality = "missing"
    if face_area is not None and backing_area is not None:
        area_quality = "calculated"
    elif face_area is not None or backing_area is not None:
        area_quality = "partial"
    elif _positive_float(geometry_sources.get("bounding_box_area_m2")) is not None:
        bbox_area = _positive_float(geometry_sources.get("bounding_box_area_m2"))
        if face_area is None:
            face_area = bbox_area
            area_quality = "estimated"
            warnings.append(
                _warning(
                    "material_quantity_estimated",
                    "Face area estimated from bounding box dimensions — not path geometry.",
                    source="pricing_input_candidate_snapshot.dimensions.area_m2",
                )
            )
        if backing_area is None:
            backing_area = bbox_area
            if area_quality == "missing":
                area_quality = "estimated"
            warnings.append(
                _warning(
                    "material_quantity_estimated",
                    "Backing area estimated from bounding box dimensions — not path geometry.",
                    source="pricing_input_candidate_snapshot.dimensions.area_m2",
                )
            )

    perimeter_present = any(
        value is not None
        for value in (total_letter_perimeter, return_perimeter, cutting_perimeter, bevel_perimeter)
    )
    if not perimeter_present:
        warnings.append(
            _warning(
                "missing_geometry_perimeters",
                "Geometry perimeters are missing from snapshot; perimeter-based quantities cannot be calculated.",
                source="snapshot.sections.geometry_metrics_snapshot",
            )
        )
    if face_area is None:
        warnings.append(
            _warning(
                "missing_face_area",
                "Face area is missing; plexiglas quantity cannot be calculated.",
                source="snapshot.geometry.face_area_m2",
            )
        )
    if backing_area is None:
        warnings.append(
            _warning(
                "missing_backing_area",
                "Backing area is missing; Forex/backing quantity cannot be calculated.",
                source="snapshot.geometry.backing_area_m2",
            )
        )
    if return_perimeter is None:
        warnings.append(
            _warning(
                "missing_return_perimeter",
                "Return material perimeter is missing; aluminum return quantity cannot be calculated.",
                source="snapshot.geometry.return_material_perimeter_ml",
            )
        )

    calc_quality = "missing"
    if confirmed and real_letters > 0:
        calc_quality = "partial"
    if perimeter_present and area_quality in {"calculated", "estimated"}:
        calc_quality = "calculated" if area_quality == "calculated" else "estimated"
    elif perimeter_present:
        calc_quality = "partial"
    if confirmed is None:
        calc_quality = "missing"
        warnings.append(
            _warning(
                "missing_confirmed_production_model",
                "Confirmed production model is missing; geometry counts unavailable.",
                severity="blocking",
                source="snapshot.sections.confirmed_production_model_snapshot",
            )
        )

    summary = IntakeV3GeometrySummary(
        product_template=context.product_template,
        source="geometry_metrics_snapshot" if snapshot_source else "confirmed_production_model_snapshot",
        geometry_snapshot_source=str(snapshot_source) if snapshot_source else None,
        real_letters_count=real_letters,
        closed_contours_count=closed_contours,
        holes_count=holes,
        outer_contours_count=outer_contours or real_letters,
        inner_holes_count=holes,
        total_letter_perimeter_ml=total_letter_perimeter or 0.0,
        return_material_perimeter_ml=return_perimeter or 0.0,
        cutting_perimeter_ml=cutting_perimeter or 0.0,
        bevel_perimeter_ml=bevel_perimeter or 0.0,
        face_area_m2=face_area or 0.0,
        backing_area_m2=backing_area or 0.0,
        vinyl_area_m2=vinyl_area or (face_area or 0.0),
        face_cutting_perimeter_ml=face_cutting_perimeter or total_letter_perimeter or 0.0,
        perimeter_classification_status=str(perimeter_classification_status)
        if perimeter_classification_status
        else None,
        perimeter_classification_source=perimeter_classification_source,
        operator_confirmed_layer_roles=operator_confirmed_layer_roles,
        calculation_quality=calc_quality,
        warnings=[item.code for item in warnings if item.code.startswith("missing_") or item.code.endswith("_estimated")],
    )
    from services.intake_v3_layer_role_confirmation_propagation_service import (
        downstream_propagation_fields,
    )

    propagation_fields, _, _ = downstream_propagation_fields(context)
    summary = summary.model_copy(
        update={
            "layer_role_confirmation_effective_source": propagation_fields.get(
                "layer_role_confirmation_effective_source"
            ),
            "layer_role_confirmation_snapshot_stale": propagation_fields.get(
                "layer_role_confirmation_snapshot_stale", False
            ),
        }
    )
    return summary, warnings


def _face_vinyl_required(finish: FinishAssignment | None) -> bool:
    if finish is None or not finish.active_groups():
        return False
    face = finish.active_groups()[0].face_finish
    return face.face_vinyl_active


def resolve_material_quantity_rows(
    context: Iv3SourceContext,
    geometry_summary: IntakeV3GeometrySummary,
    finish: FinishAssignment | None,
) -> tuple[list[IntakeV3MaterialQuantityRow], list[IntakeV3MaterialBreakdownWarning]]:
    warnings: list[IntakeV3MaterialBreakdownWarning] = []
    geometry_sources = _collect_geometry_sources(context.sections, context.workspace)
    vinyl_required = _face_vinyl_required(finish)

    def _row(
        material_key: str,
        display_name: str,
        category: str,
        quantity: float | None,
        unit: str,
        quantity_source: str,
        quantity_quality: str,
        *,
        included: bool = True,
        row_warnings: list[IntakeV3MaterialBreakdownWarning] | None = None,
    ) -> IntakeV3MaterialQuantityRow:
        qty = quantity if quantity is not None else 0.0
        with_waste = _apply_waste(quantity) if quantity is not None else None
        return IntakeV3MaterialQuantityRow(
            material_key=material_key,
            display_name=display_name,
            category=category,
            quantity=qty,
            unit=unit,
            quantity_source=quantity_source,
            quantity_quality=quantity_quality,
            waste_percent=WASTE_PERCENT if quantity is not None else None,
            quantity_with_waste=with_waste or 0.0,
            included=included,
            warnings=[w.code for w in (row_warnings or [])],
        )

    face_qty = geometry_summary.face_area_m2 if geometry_summary.face_area_m2 > 0 else None
    face_quality = "calculated" if face_qty else "missing"
    if face_quality == "calculated" and geometry_summary.calculation_quality == "estimated":
        face_quality = "estimated"

    backing_qty = geometry_summary.backing_area_m2 if geometry_summary.backing_area_m2 > 0 else None
    backing_quality = "calculated" if backing_qty else "missing"
    if backing_quality == "calculated" and geometry_summary.calculation_quality == "estimated":
        backing_quality = "estimated"

    vinyl_qty = None
    vinyl_quality = "not_applicable"
    if vinyl_required:
        vinyl_qty = geometry_summary.vinyl_area_m2 if geometry_summary.vinyl_area_m2 > 0 else None
        vinyl_quality = "calculated" if vinyl_qty else "missing"
        if vinyl_quality == "missing":
            warnings.append(
                _warning(
                    "missing_vinyl_area",
                    "Face vinyl finish requires vinyl area; quantity is missing.",
                    source="snapshot.geometry.vinyl_area_m2",
                )
            )
    else:
        warnings.append(
            _warning(
                "material_not_applicable",
                "Face vinyl row excluded — finish does not require face vinyl.",
                source="finish_assignment_snapshot.face_finish",
            )
        )

    return_qty = (
        geometry_summary.return_material_perimeter_ml
        if geometry_summary.return_material_perimeter_ml > 0
        else None
    )
    return_quality = "calculated" if return_qty else "missing"

    led_count = _read_geometry_metric(geometry_sources, "led_module_count")
    led_quality = "calculated" if led_count is not None else "missing"
    if led_count is None:
        warnings.append(
            _warning(
                "missing_led_count",
                "LED module count is missing from snapshot geometry metrics.",
                source="snapshot.geometry.led_module_count",
            )
        )

    psu_count = _read_geometry_metric(geometry_sources, "led_power_supply_count")
    led_quality_psu = "calculated" if psu_count is not None else "missing"
    if psu_count is None and context.workspace is not None:
        intent = derive_material_intent(context.workspace, finish_assignment=finish)
        if intent.power_supplies:
            psu_count = float(sum(item.quantity or 0 for item in intent.power_supplies)) or None
            if psu_count:
                led_quality_psu = "estimated"
            else:
                led_quality_psu = "missing"
        else:
            led_quality_psu = "missing"

    if psu_count is None:
        warnings.append(
            _warning(
                "missing_power_supply_count",
                "LED power supply count is missing; using finish/material intent if available.",
                source="snapshot.geometry.led_power_supply_count",
            )
        )

    rows = [
        _row(
            "plexiglas_face",
            "Plexiglas față",
            "sheet",
            face_qty,
            "m2",
            "face_area_m2",
            face_quality,
        ),
        _row(
            "forex_backing",
            "Forex / backing",
            "sheet",
            backing_qty,
            "m2",
            "backing_area_m2",
            backing_quality,
        ),
        _row(
            "face_vinyl",
            "Autocolant față",
            "vinyl",
            vinyl_qty,
            "m2",
            "vinyl_area_m2",
            vinyl_quality,
            included=vinyl_required,
        ),
        _row(
            "aluminum_return",
            "Cant aluminiu",
            "linear",
            return_qty,
            "ml",
            "return_material_perimeter_ml",
            return_quality,
        ),
        _row(
            "led_modules",
            "Module LED",
            "component",
            float(led_count) if led_count is not None else None,
            "buc",
            "snapshot_or_estimation",
            led_quality,
            row_warnings=[
                _warning(
                    "missing_led_count",
                    "LED module count missing.",
                    source="snapshot.geometry.led_module_count",
                )
            ]
            if led_count is None
            else [],
        ),
        _row(
            "led_power_supply",
            "Surse LED",
            "component",
            float(psu_count) if psu_count is not None else None,
            "buc",
            "snapshot_or_estimation",
            led_quality_psu if psu_count is not None else "missing",
        ),
    ]
    return rows, warnings


async def _lookup_registry_price(
    db: AsyncSession,
    code: str,
) -> tuple[float | None, str | None, str]:
    row = await db.scalar(select(Inventory_materials).where(Inventory_materials.code == code))
    if row is None:
        return None, None, "missing"
    cost = _positive_float(row.unit_cost)
    if cost is None or (row.status and row.status != "active"):
        return None, row.currency, "missing"
    return cost, row.currency or "EUR", "pricing_registry"


def _resolve_aluminum_return_price(
    finish: FinishAssignment | None,
) -> tuple[float | None, str, str, str | None]:
    depth_mm: int | None = None
    if finish and finish.active_groups():
        depth_mm = _positive_int(finish.active_groups()[0].return_finish.return_depth_mm)
    registry_code = None
    if depth_mm in PROFILE_DEPTH_MM_TO_VARIANT_CODE:
        registry_code = PROFILE_DEPTH_MM_TO_VARIANT_CODE[depth_mm]
    fallback_price = RETURN_DEPTH_FALLBACK_EUR_ML.get(depth_mm or -1)
    if fallback_price is not None:
        return fallback_price, "EUR", "owner_confirmed_fallback", registry_code
    return None, "EUR", "missing", registry_code


STOCK_TRACKED_MATERIAL_KEYS = frozenset(
    {
        "plexiglas_face",
        "forex_backing",
        "face_vinyl",
        "aluminum_return",
        "led_modules",
        "led_power_supply",
    }
)


def resolve_registry_code_for_row(
    material_key: str,
    finish: FinishAssignment | None,
) -> tuple[str | None, str]:
    if material_key == "aluminum_return":
        depth_mm: int | None = None
        if finish and finish.active_groups():
            depth_mm = _positive_int(finish.active_groups()[0].return_finish.return_depth_mm)
        if depth_mm in PROFILE_DEPTH_MM_TO_VARIANT_CODE:
            code = PROFILE_DEPTH_MM_TO_VARIANT_CODE[depth_mm]
            return code, f"aluminum_return_{depth_mm}mm"
        return None, "aluminum_return"
    if material_key == "led_power_supply":
        return PSU_FALLBACK_REGISTRY_CODE, "led_power_supply"
    fallback = OWNER_CONFIRMED_FALLBACKS.get(material_key)
    if fallback and fallback.get("registry_code"):
        return str(fallback["registry_code"]), material_key
    return None, material_key


def enrich_material_rows_with_registry_metadata(
    material_rows: list[IntakeV3MaterialQuantityRow],
    finish: FinishAssignment | None,
) -> list[IntakeV3MaterialQuantityRow]:
    enriched: list[IntakeV3MaterialQuantityRow] = []
    for row in material_rows:
        registry_code, material_intent = resolve_registry_code_for_row(row.material_key, finish)
        tracking = (
            "stock_tracked"
            if row.material_key in STOCK_TRACKED_MATERIAL_KEYS
            else "not_applicable"
        )
        enriched.append(
            row.model_copy(
                update={
                    "registry_code": registry_code,
                    "material_intent": material_intent,
                    "stock_tracking_class": tracking,
                }
            )
        )
    return enriched


async def resolve_material_unit_prices(
    db: AsyncSession,
    material_rows: list[IntakeV3MaterialQuantityRow],
    finish: FinishAssignment | None,
) -> dict[str, dict[str, Any]]:
    resolved: dict[str, dict[str, Any]] = {}
    for row in material_rows:
        if not row.included:
            continue
        if row.material_key == "aluminum_return":
            unit_price, currency, source, registry_code = _resolve_aluminum_return_price(finish)
            if registry_code:
                reg_price, reg_currency, reg_source = await _lookup_registry_price(db, registry_code)
                if reg_price is not None:
                    unit_price, currency, source = reg_price, reg_currency or currency, reg_source
            resolved[row.material_key] = {
                "unit_price": unit_price,
                "currency": currency,
                "price_source": source,
                "registry_code": registry_code,
            }
            continue

        fallback = OWNER_CONFIRMED_FALLBACKS.get(row.material_key)
        registry_code = fallback.get("registry_code") if fallback else None
        unit_price = None
        currency = fallback.get("currency", "EUR") if fallback else "EUR"
        source = "missing"
        if registry_code:
            reg_price, reg_currency, reg_source = await _lookup_registry_price(db, registry_code)
            if reg_price is not None:
                unit_price, currency, source = reg_price, reg_currency or currency, reg_source
        if unit_price is None and fallback:
            unit_price = fallback.get("unit_price")
            source = "owner_confirmed_fallback"
        if row.material_key == "led_power_supply" and unit_price is None:
            psu_code = PSU_FALLBACK_REGISTRY_CODE
            reg_price, reg_currency, reg_source = await _lookup_registry_price(db, psu_code)
            if reg_price is not None:
                unit_price, currency, source = reg_price, reg_currency or currency, reg_source
        resolved[row.material_key] = {
            "unit_price": unit_price,
            "currency": currency,
            "price_source": source,
            "registry_code": registry_code,
        }
    return resolved


def build_material_cost_rows(
    material_rows: list[IntakeV3MaterialQuantityRow],
    unit_prices: dict[str, dict[str, Any]],
) -> tuple[list[IntakeV3MaterialCostRow], list[IntakeV3MaterialBreakdownWarning]]:
    warnings: list[IntakeV3MaterialBreakdownWarning] = []
    cost_rows: list[IntakeV3MaterialCostRow] = []
    for row in material_rows:
        if not row.included:
            continue
        price_info = unit_prices.get(row.material_key, {})
        unit_price = price_info.get("unit_price")
        currency = str(price_info.get("currency") or "EUR")
        price_source = str(price_info.get("price_source") or "missing")
        qty_used = row.quantity_with_waste if row.quantity_with_waste > 0 else row.quantity
        material_cost = None
        cost_quality = "missing"
        row_warnings: list[str] = []
        if row.quantity_quality in {"missing", "not_applicable"}:
            cost_quality = "missing"
        elif unit_price is None:
            cost_quality = "missing"
            warnings.append(
                _warning(
                    "missing_unit_price",
                    f"Unit price missing for {row.display_name}.",
                    source=f"material_price.{row.material_key}",
                )
            )
            row_warnings.append("missing_unit_price")
        else:
            material_cost = round(float(qty_used) * float(unit_price), 4)
            cost_quality = "estimated" if row.quantity_quality == "estimated" else "calculated"
        cost_rows.append(
            IntakeV3MaterialCostRow(
                material_key=row.material_key,
                display_name=row.display_name,
                quantity=row.quantity,
                unit=row.unit,
                quantity_with_waste=row.quantity_with_waste,
                unit_price=unit_price,
                currency=currency,
                price_source=price_source,
                material_cost=material_cost,
                cost_quality=cost_quality,
                included_in_total=material_cost is not None,
                warnings=row_warnings,
            )
        )
    return cost_rows, warnings


def build_material_quantity_breakdown_response(
    context: Iv3SourceContext,
    geometry_summary: IntakeV3GeometrySummary,
    material_rows: list[IntakeV3MaterialQuantityRow],
    cost_rows: list[IntakeV3MaterialCostRow],
    warnings: list[IntakeV3MaterialBreakdownWarning],
) -> IntakeV3MaterialBreakdownResponse:
    currencies: dict[str, float] = {}
    contains_estimates = False
    contains_missing_prices = False
    contains_missing_quantities = False
    for row in material_rows:
        if row.included and row.quantity_quality in {"missing", "partial"}:
            contains_missing_quantities = True
        if row.quantity_quality == "estimated":
            contains_estimates = True
    for row in cost_rows:
        if row.cost_quality == "estimated":
            contains_estimates = True
        if row.unit_price is None:
            contains_missing_prices = True
        if row.material_cost is not None and row.included_in_total:
            currencies[row.currency] = currencies.get(row.currency, 0.0) + float(row.material_cost)

    if len(currencies) > 1:
        warnings.append(
            _warning(
                "mixed_currency_no_conversion",
                "Material costs span multiple currencies — totals are grouped per currency without FX conversion.",
                source="material_cost_totals",
            )
        )

    totals_by_currency = [
        IntakeV3MaterialBreakdownTotals(
            material_cost_total=round(total, 4),
            currency=currency,
            contains_estimates=contains_estimates,
            contains_missing_prices=contains_missing_prices,
            contains_missing_quantities=contains_missing_quantities,
        )
        for currency, total in sorted(currencies.items())
    ]
    primary_total = totals_by_currency[0] if len(totals_by_currency) == 1 else IntakeV3MaterialBreakdownTotals(
        material_cost_total=0.0,
        currency="EUR",
        contains_estimates=contains_estimates,
        contains_missing_prices=contains_missing_prices,
        contains_missing_quantities=contains_missing_quantities,
    )

    deduped: list[IntakeV3MaterialBreakdownWarning] = []
    seen: set[str] = set()
    for item in warnings:
        key = f"{item.code}:{item.source}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return IntakeV3MaterialBreakdownResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=context.source_type,
        source_id=context.source_id,
        order_id=context.order.id if context.order else None,
        quote_id=context.quote.id if context.quote else None,
        source_workspace_id=(
            (context.quote_linkage or {}).get("source_workspace_id")
            or (context.order_linkage or {}).get("source_workspace_id")
        ),
        is_intake_v3=context.is_intake_v3,
        breakdown_scope=BREAKDOWN_SCOPE,
        includes_geometry=True,
        includes_material_quantities=True,
        includes_material_costs=True,
        includes_operations_cost=False,
        includes_labor_cost=False,
        includes_markup=False,
        includes_profit=False,
        inventory_mutation_allowed=False,
        costengine_used=False,
        geometry_summary=geometry_summary,
        material_rows=material_rows,
        cost_rows=cost_rows,
        totals=primary_total,
        totals_by_currency=totals_by_currency,
        warnings=deduped,
        future_builds=[
            "material registry refinement",
            "production task generation dry-run",
        ],
    )


def _non_iv3_response(source_type: str, source_id: str, order: Orders | None = None) -> IntakeV3MaterialBreakdownResponse:
    return IntakeV3MaterialBreakdownResponse(
        source_module=INTAKE_V3_SOURCE_MODULE,
        source_type=source_type,
        source_id=source_id,
        order_id=order.id if order else None,
        is_intake_v3=False,
        breakdown_scope=BREAKDOWN_SCOPE,
        includes_geometry=True,
        includes_material_quantities=True,
        includes_material_costs=True,
        includes_operations_cost=False,
        includes_labor_cost=False,
        includes_markup=False,
        includes_profit=False,
        inventory_mutation_allowed=False,
        costengine_used=False,
        geometry_summary=IntakeV3GeometrySummary(
            product_template="unknown",
            source="none",
            calculation_quality="missing",
        ),
        warnings=[
            _warning(
                "not_intake_v3_source",
                "Source is not an Intake V3 order/quote/workspace payload.",
                source="source_detection",
            )
        ],
    )


async def _build_breakdown_from_context(db: AsyncSession, context: Iv3SourceContext) -> IntakeV3MaterialBreakdownResponse:
    if not context.is_intake_v3:
        return _non_iv3_response(context.source_type, context.source_id, context.order)

    geometry_summary, geometry_warnings = extract_geometry_summary(context)
    finish = extract_finish_assignments(context)
    if finish is None:
        geometry_warnings.append(
            _warning(
                "finish_assignments_missing",
                "Finish assignments are missing; vinyl inclusion rules may be incomplete.",
                source="snapshot.sections.finish_assignment_snapshot",
            )
        )
    material_rows, row_warnings = resolve_material_quantity_rows(context, geometry_summary, finish)
    material_rows = enrich_material_rows_with_registry_metadata(material_rows, finish)
    unit_prices = await resolve_material_unit_prices(db, material_rows, finish)
    cost_rows, cost_warnings = build_material_cost_rows(material_rows, unit_prices)
    all_warnings = geometry_warnings + row_warnings + cost_warnings

    from services.intake_v3_layer_role_confirmation_propagation_service import (
        downstream_propagation_fields,
    )

    propagation_fields, _, stale_warning_pairs = downstream_propagation_fields(context)
    for code, message in stale_warning_pairs:
        all_warnings.append(
            _warning(code, message, source="layer_role_confirmation_propagation")
        )

    response = build_material_quantity_breakdown_response(
        context,
        geometry_summary,
        material_rows,
        cost_rows,
        all_warnings,
    )
    return response.model_copy(update=propagation_fields)


def _sections_from_workspace(workspace: IntakeV3Workspace) -> dict[str, Any]:
    candidate = build_pricing_input_candidate(workspace)
    sections: dict[str, Any] = {
        "workspace_payload_snapshot": workspace.model_dump(mode="json"),
        "pricing_input_candidate_snapshot": candidate.candidate.model_dump(mode="json"),
    }
    if workspace.confirmed_production_model:
        sections["confirmed_production_model_snapshot"] = workspace.confirmed_production_model.model_dump(
            mode="json"
        )
    if workspace.finish_assignment:
        sections["finish_assignment_snapshot"] = workspace.finish_assignment.model_dump(mode="json")
    if workspace.geometry_metrics_snapshot:
        sections["geometry_metrics_snapshot"] = workspace.geometry_metrics_snapshot
    if workspace.layer_role_confirmation_snapshot:
        sections["layer_role_confirmation_snapshot"] = workspace.layer_role_confirmation_snapshot
    return sections


async def hydrate_live_workspace_snapshot_sections(
    db: AsyncSession,
    quote_linkage: dict[str, Any] | None,
    sections: dict[str, Any],
    workspace: IntakeV3Workspace | None,
    *,
    workspace_id_override: str | None = None,
) -> tuple[dict[str, Any], IntakeV3Workspace | None]:
    workspace_id = workspace_id_override
    if not workspace_id and quote_linkage:
        workspace_id = quote_linkage.get("source_workspace_id")
    if not workspace_id:
        return sections, workspace

    from services.intake_v3_workspace_service import get_intake_v3_workspace, sanitize_intake_v3_workspace_payload

    record = await get_intake_v3_workspace(db, workspace_id)
    if record is None:
        return sections, workspace

    live = sanitize_intake_v3_workspace_payload(record.payload)
    updated = dict(sections)
    if not live.layer_role_confirmation_snapshot:
        return sections, workspace

    updated["layer_role_confirmation_snapshot"] = live.layer_role_confirmation_snapshot
    if live.geometry_metrics_snapshot:
        updated["geometry_metrics_snapshot"] = live.geometry_metrics_snapshot
    workspace_payload = updated.get("workspace_payload_snapshot")
    if isinstance(workspace_payload, dict):
        nested = dict(workspace_payload)
        if live.path_geometry_summary:
            nested["path_geometry_summary"] = live.path_geometry_summary
        nested["layer_role_confirmation_snapshot"] = live.layer_role_confirmation_snapshot
        if live.geometry_metrics_snapshot:
            nested["geometry_metrics_snapshot"] = live.geometry_metrics_snapshot
        if live.raw_svg_analysis:
            nested["raw_svg_analysis"] = live.raw_svg_analysis
        updated["workspace_payload_snapshot"] = nested
    if workspace is not None:
        workspace_update: dict[str, Any] = {
            "layer_role_confirmation_snapshot": live.layer_role_confirmation_snapshot,
        }
        if live.geometry_metrics_snapshot:
            workspace_update["geometry_metrics_snapshot"] = live.geometry_metrics_snapshot
        if live.path_geometry_summary:
            workspace_update["path_geometry_summary"] = live.path_geometry_summary
        if live.raw_svg_analysis:
            workspace_update["raw_svg_analysis"] = live.raw_svg_analysis
        workspace = workspace.model_copy(update=workspace_update)
    else:
        workspace = live
    return updated, workspace


async def load_iv3_source_context(
    db: AsyncSession,
    *,
    order_id: int | None = None,
    quote_id: int | None = None,
    workspace_id: str | None = None,
) -> Iv3SourceContext:
    if order_id is not None:
        orders_service = OrdersService(db)
        order = await orders_service.get_by_id(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail={"error": "order_not_found", "order_id": order_id})
        order_linkage = load_iv3_order_linkage(order)
        quote = await load_source_quote_for_iv3_order(db, order)
        quote_linkage = None
        sections: dict[str, Any] = {}
        linkage_sections: dict[str, Any] = {}
        if quote:
            quote_linkage, _ = load_quote_intake_v3_linkage(quote)
            linkage_sections = dict(_snapshot_sections(quote_linkage))
            sections = dict(linkage_sections)
        workspace = _load_workspace_from_sections(sections)
        product_template = _resolve_product_template(sections, workspace)
        sections, workspace = await hydrate_live_workspace_snapshot_sections(
            db, quote_linkage, sections, workspace
        )
        return Iv3SourceContext(
            source_type="order",
            source_id=str(order_id),
            is_intake_v3=is_iv3_order(order, order_linkage),
            order=order,
            quote=quote,
            quote_linkage=quote_linkage,
            order_linkage=order_linkage,
            sections=sections,
            linkage_sections=linkage_sections,
            workspace=workspace,
            product_template=product_template,
        )

    if quote_id is not None:
        quotes_service = QuotesService(db)
        quote = await quotes_service.get_by_id(quote_id)
        if quote is None:
            raise HTTPException(status_code=404, detail={"error": "quote_not_found", "quote_id": quote_id})
        quote_linkage, _ = load_quote_intake_v3_linkage(quote)
        linkage_sections = dict(_snapshot_sections(quote_linkage))
        sections = dict(linkage_sections)
        workspace = _load_workspace_from_sections(sections)
        is_iv3 = bool(quote.intake_code and str(quote.intake_code).startswith("IV3-") and quote_linkage)
        sections, workspace = await hydrate_live_workspace_snapshot_sections(
            db, quote_linkage, sections, workspace
        )
        return Iv3SourceContext(
            source_type="quote",
            source_id=str(quote_id),
            is_intake_v3=is_iv3,
            order=None,
            quote=quote,
            quote_linkage=quote_linkage,
            order_linkage=None,
            sections=sections,
            linkage_sections=linkage_sections,
            workspace=workspace,
            product_template=_resolve_product_template(sections, workspace),
        )

    if workspace_id is not None:
        from services.intake_v3_workspace_service import get_intake_v3_workspace

        record = await get_intake_v3_workspace(db, workspace_id)
        workspace = sanitize_intake_v3_workspace_payload(record.payload)
        quote = await check_existing_quote_for_intake_v3_workspace(db, workspace_id)
        quote_linkage = None
        linkage_sections: dict[str, Any] = {}
        sections = _sections_from_workspace(workspace)
        if quote:
            quote_linkage, _ = parse_intake_v3_quote_notes(quote.notes)
            snapshot_sections = _snapshot_sections(quote_linkage)
            if snapshot_sections:
                linkage_sections = dict(snapshot_sections)
                sections = dict(linkage_sections)
                workspace = _load_workspace_from_sections(sections) or workspace
        sections, workspace = await hydrate_live_workspace_snapshot_sections(
            db,
            quote_linkage,
            sections,
            workspace,
            workspace_id_override=workspace_id,
        )
        return Iv3SourceContext(
            source_type="workspace",
            source_id=workspace_id,
            is_intake_v3=True,
            order=None,
            quote=quote,
            quote_linkage=quote_linkage,
            order_linkage=None,
            sections=sections,
            linkage_sections=linkage_sections,
            workspace=workspace,
            product_template=workspace.product_selection.template_code or PILOT_TEMPLATE_CODE,
        )

    raise ValueError("One of order_id, quote_id, workspace_id is required")


async def get_intake_v3_material_quantity_breakdown_for_order(
    db: AsyncSession,
    order_id: int,
) -> IntakeV3MaterialBreakdownResponse:
    context = await load_iv3_source_context(db, order_id=order_id)
    return await _build_breakdown_from_context(db, context)


async def get_intake_v3_material_quantity_breakdown_for_quote(
    db: AsyncSession,
    quote_id: int,
) -> IntakeV3MaterialBreakdownResponse:
    context = await load_iv3_source_context(db, quote_id=quote_id)
    return await _build_breakdown_from_context(db, context)


async def get_intake_v3_material_quantity_breakdown_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV3MaterialBreakdownResponse:
    context = await load_iv3_source_context(db, workspace_id=workspace_id)
    return await _build_breakdown_from_context(db, context)
