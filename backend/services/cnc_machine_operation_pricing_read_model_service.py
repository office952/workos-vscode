"""Read-only CNC machine operation pricing adapter for logical-list trace.

Implements the current architecture contract as in-memory configuration only.
It does not write DB state, mutate Pricing/CostEngine, or change commercial totals.
"""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_PASS_DEPTH_MM = 3.5
PLEXIGLAS_3MM = "PLEXIGLAS_3MM"
FOREX_10MM = "FOREX_10MM"
DIBOND_ACM_3MM = "DIBOND_ACM_3MM"
ALUMINUM_SHEET_LE_3_5MM = "ALUMINUM_SHEET_LE_3_5MM"
PLEXIGLAS_3MM_FACE_BATCH = "PLEXIGLAS_3MM_FACE_BATCH"
CONTRACT_BASELINE_PENDING_OWNER_CONFIRMATION = "contract_baseline_pending_owner_confirmation"
OWNER_CONFIRMED_PLEXIGLAS_CUT_BASELINE = "owner_confirmed_plexiglas_cut_baseline"
OWNER_CONFIRMED_PLEXIGLAS_GUIDE_CHANNEL_BASELINE = "owner_confirmed_plexiglas_guide_channel_baseline"


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _round(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def _rate_from_row(*, quantity: float | None, subtotal: float | None) -> float | None:
    if quantity is None or subtotal is None or quantity <= 0:
        return None
    return round(subtotal / quantity, 4)


def _cost_ml_pass(*, quantity_ml: float | None, pass_count: int | None, tariff_eur_per_ml_pass: float | None) -> float | None:
    if quantity_ml is None or quantity_ml <= 0 or pass_count is None or pass_count <= 0 or tariff_eur_per_ml_pass is None:
        return None
    return round(quantity_ml * pass_count * tariff_eur_per_ml_pass, 4)


def _cost_area(*, quantity_m2: float | None, tariff_eur_per_m2: float | None) -> float | None:
    if quantity_m2 is None or quantity_m2 <= 0 or tariff_eur_per_m2 is None:
        return None
    return round(quantity_m2 * tariff_eur_per_m2, 4)


def resolve_cnc_perimeter_ml(geometry: Mapping[str, Any]) -> float | None:
    for key in (
        "face_cutting_perimeter_ml",
        "cnc_cutting_perimeter_ml",
        "cutting_perimeter_ml",
        "backing_cnc_cutting_perimeter_ml",
        "back_cutting_perimeter_ml",
        "letter_perimeter_m",
    ):
        value = _number(geometry.get(key))
        if value is not None and value > 0:
            return round(value, 4)
    return None


def build_shared_plexiglas_face_batch_overrides(
    *,
    letter_face_row: Mapping[str, Any] | None,
    logo_face_area_m2: float | None,
) -> dict[str, dict[str, Any]]:
    letter_area = _number(letter_face_row.get("quantity") if letter_face_row else None)
    letter_subtotal = _number(letter_face_row.get("estimated_cost") if letter_face_row else None)
    if letter_subtotal is None and letter_face_row is not None:
        letter_subtotal = _number(letter_face_row.get("material_cost"))
    material_tariff_eur_per_m2 = _rate_from_row(quantity=letter_area, subtotal=letter_subtotal)
    shared_roles = ["LETTER_FACE"] + (["LOGO_FACE"] if isinstance(logo_face_area_m2, (int, float)) and logo_face_area_m2 > 0 else [])
    batch_trace = {
        "batch_code": PLEXIGLAS_3MM_FACE_BATCH,
        "material_code": PLEXIGLAS_3MM,
        "letter_face_area_m2": _round(letter_area, 6),
        "logo_face_area_m2": _round(_number(logo_face_area_m2), 6),
        "total_face_area_m2": _round((letter_area or 0.0) + (_number(logo_face_area_m2) or 0.0), 6),
        "nesting_method": "shared_face_batch_logical_trace",
        "material_tariff_source": "pricing_registry" if material_tariff_eur_per_m2 is not None else None,
        "material_tariff_eur_per_m2": material_tariff_eur_per_m2,
        "sheet_batch_note": "LETTER_FACE and LOGO_FACE share the same physical Plexiglas 3 mm batch.",
        "shared_batch_roles": shared_roles,
    }

    letter_override = {
        "material_code": PLEXIGLAS_3MM,
        "material_name": "Plexiglas 3 mm",
        "thickness_mm": 3.0,
        "nesting_group": PLEXIGLAS_3MM_FACE_BATCH,
        "batch_roles": ["LETTER_FACE"],
        "shared_batch_roles": shared_roles,
        "material_tariff_source": batch_trace["material_tariff_source"],
        "material_tariff_eur_per_m2": material_tariff_eur_per_m2,
        "batch_trace": batch_trace,
    }

    logo_quantity = _number(logo_face_area_m2)
    logo_subtotal = _cost_area(quantity_m2=logo_quantity, tariff_eur_per_m2=material_tariff_eur_per_m2)
    logo_warnings: list[str] = []
    logo_gaps: list[str] = []
    logo_status = "MATCHED"
    runtime_source = "shared_material_batch" if logo_subtotal is not None else None
    if logo_quantity is None or logo_quantity <= 0:
        logo_status = "PARTIAL"
        logo_gaps.append("LOGO_PLEXI_AREA_MISSING")
        logo_warnings.append("Logo/emblem plexiglas area is missing; shared Plexiglas tariff cannot be resolved.")
    elif material_tariff_eur_per_m2 is None:
        logo_status = "PARTIAL"
        logo_gaps.append("PLEXIGLAS_SHARED_BATCH_TARIFF_SOURCE_MISSING")
        logo_warnings.append("Shared Plexiglas tariff source is missing; no separate logo tariff was created.")
    else:
        logo_warnings.append("Logical logo/emblem row priced from shared PLEXIGLAS_3MM batch; no separate logo material tariff exists.")

    logo_override = {
        "status": logo_status,
        "subtotal": logo_subtotal,
        "currency": letter_face_row.get("currency") if letter_face_row else None,
        "runtime_source": runtime_source,
        "material_code": PLEXIGLAS_3MM,
        "material_name": "Plexiglas 3 mm",
        "thickness_mm": 3.0,
        "nesting_group": PLEXIGLAS_3MM_FACE_BATCH,
        "batch_roles": ["LOGO_FACE"],
        "shared_batch_roles": shared_roles,
        "material_tariff_source": batch_trace["material_tariff_source"],
        "material_tariff_eur_per_m2": material_tariff_eur_per_m2,
        "batch_trace": batch_trace,
        "warnings": logo_warnings,
        "gaps": logo_gaps,
    }
    return {
        "material.plexiglas_face": letter_override,
        "material.logo_plexiglas_face": logo_override,
    }


def _base_operation_override(
    *,
    operation_code: str,
    operation_kind: str,
    material_code: str,
    thickness_mm: float,
    operation_depth_mm: float | None,
    pass_depth_mm: float,
    pass_count: int,
    tariff_basis: str,
    tariff_eur_per_ml_pass: float | None = None,
    tariff_eur_per_ml: float | None = None,
    tariff_source: str | None = None,
    subtotal: float | None = None,
    quantity_ml: float | None = None,
    status: str = "MATCHED",
    warnings: list[str] | None = None,
    gaps: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "runtime_source": tariff_source,
        "subtotal": subtotal,
        "currency": "EUR" if subtotal is not None else None,
        "operation_code": operation_code,
        "operation_kind": operation_kind,
        "material_code": material_code,
        "thickness_mm": thickness_mm,
        "operation_depth_mm": operation_depth_mm,
        "pass_depth_mm": pass_depth_mm,
        "pass_count": pass_count,
        "tariff_basis": tariff_basis,
        "tariff_eur_per_ml_pass": tariff_eur_per_ml_pass,
        "tariff_eur_per_ml": tariff_eur_per_ml,
        "warnings": warnings or [],
        "gaps": gaps or [],
        **(extra or {}),
    }


def build_cnc_operation_pricing_overrides(
    *,
    face_cut_row: Mapping[str, Any] | None,
    face_flat_recess_row: Mapping[str, Any] | None,
    back_cut_row: Mapping[str, Any] | None,
    face_cut_quantity_fallback_ml: float | None = None,
    face_flat_recess_quantity_fallback_ml: float | None = None,
    back_cut_quantity_fallback_ml: float | None = None,
) -> dict[str, dict[str, Any]]:
    overrides: dict[str, dict[str, Any]] = {}

    face_cut_quantity = _number(face_cut_row.get("quantity") if face_cut_row else None)
    if face_cut_quantity is None:
        face_cut_quantity = _number(face_cut_quantity_fallback_ml)
    face_cut_subtotal = _number(face_cut_row.get("estimated_cost") if face_cut_row else None)
    if face_cut_subtotal is None:
        face_cut_subtotal = _cost_ml_pass(quantity_ml=face_cut_quantity, pass_count=1, tariff_eur_per_ml_pass=1.5)
    overrides["service.cnc_face"] = _base_operation_override(
        operation_code="CNC_CUT_PLEXIGLAS_3MM",
        operation_kind="cut",
        material_code=PLEXIGLAS_3MM,
        thickness_mm=3.0,
        operation_depth_mm=3.0,
        pass_depth_mm=DEFAULT_PASS_DEPTH_MM,
        pass_count=1,
        tariff_basis="ml_pass",
        tariff_eur_per_ml_pass=1.5,
        tariff_source=OWNER_CONFIRMED_PLEXIGLAS_CUT_BASELINE,
        subtotal=face_cut_subtotal,
        quantity_ml=face_cut_quantity,
        status="MATCHED",
        warnings=[],
        extra={"quantity": face_cut_quantity, "unit": "ml" if face_cut_quantity is not None else None},
    )

    face_flat_quantity = _number(face_flat_recess_row.get("quantity") if face_flat_recess_row else None)
    if face_flat_quantity is None:
        face_flat_quantity = _number(face_flat_recess_quantity_fallback_ml)
    face_flat_subtotal = _number(face_flat_recess_row.get("estimated_cost") if face_flat_recess_row else None)
    if face_flat_subtotal is None:
        face_flat_subtotal = _cost_ml_pass(quantity_ml=face_flat_quantity, pass_count=1, tariff_eur_per_ml_pass=1.5)
    overrides["service.cnc_face_bevel"] = _base_operation_override(
        operation_code="CNC_FLAT_RECESS_PLEXIGLAS_GLUE_SEAT",
        operation_kind="flat_recess",
        material_code=PLEXIGLAS_3MM,
        thickness_mm=3.0,
        operation_depth_mm=1.0,
        pass_depth_mm=DEFAULT_PASS_DEPTH_MM,
        pass_count=1,
        tariff_basis="ml_pass",
        tariff_eur_per_ml_pass=1.5,
        tariff_source=OWNER_CONFIRMED_PLEXIGLAS_GUIDE_CHANNEL_BASELINE,
        subtotal=face_flat_subtotal,
        quantity_ml=face_flat_quantity,
        status="MATCHED",
        warnings=[
            "LEGACY_LABEL_SANFREN_RENAMED_TO_CANAL_PLAT_GHIDAJ",
            "GUIDE_CHANNEL_DEPTH_FORM_FIELD_PENDING",
        ],
        extra={
            "quantity": face_flat_quantity,
            "unit": "ml" if face_flat_quantity is not None else None,
            "operation_semantics": ["flat_recess", "guide_channel", "glue_seat", "flat_channel"],
            "legacy_labels": ["bevel", "sanfren"],
            "legacy_label": "Sanfren CNC fata Plexiglas",
            "canonical_label": "Canal plat ghidaj fata Plexiglas",
            "not_v_cut": True,
            "future_form_field_key": "guide_channel_depth_mm",
            "future_form_field_default_mm": 1.0,
            "future_form_field_aliases": ["flat_recess_depth_mm"],
            "future_admin_registry_required": True,
        },
    )

    back_cut_quantity = _number(back_cut_row.get("quantity") if back_cut_row else None)
    if back_cut_quantity is None:
        back_cut_quantity = _number(back_cut_quantity_fallback_ml)
    back_cut_subtotal = _number(back_cut_row.get("estimated_cost") if back_cut_row else None)
    if back_cut_subtotal is None:
        back_cut_subtotal = _cost_ml_pass(quantity_ml=back_cut_quantity, pass_count=5, tariff_eur_per_ml_pass=1.5)
    overrides["service.cnc_back"] = _base_operation_override(
        operation_code="CNC_CUT_FOREX_10MM",
        operation_kind="cut",
        material_code=FOREX_10MM,
        thickness_mm=10.0,
        operation_depth_mm=10.0,
        pass_depth_mm=DEFAULT_PASS_DEPTH_MM,
        pass_count=5,
        tariff_basis="ml_pass",
        tariff_eur_per_ml_pass=1.5,
        tariff_source="owner_contract_confirmed_forex_baseline",
        subtotal=back_cut_subtotal,
        quantity_ml=back_cut_quantity,
        status="MATCHED",
        warnings=["FOREX_BACK_ROW_AGGREGATES_CUT_AND_FLAT_RECESS_TRACE"],
        extra={
            "quantity": back_cut_quantity,
            "unit": "ml" if back_cut_quantity is not None else None,
            "cut_passes": 3,
            "flat_recess_passes": 2,
            "total_effective_passes": 5,
            "owner_pass_override": True,
            "operation_semantics": ["cut", "flat_recess", "back_seat"],
            "trace_breakdown": [
                {
                    "operation_code": "CNC_CUT_FOREX_10MM",
                    "operation_kind": "cut",
                    "operation_depth_mm": 10.0,
                    "pass_count": 3,
                    "tariff_basis": "ml_pass",
                    "tariff_eur_per_ml_pass": 1.5,
                },
                {
                    "operation_code": "CNC_FLAT_RECESS_FOREX_BACK_SEAT",
                    "operation_kind": "flat_recess",
                    "operation_depth_mm": 7.0,
                    "pass_count": 2,
                    "tariff_basis": "ml_pass",
                    "tariff_eur_per_ml_pass": 1.5,
                },
            ],
        },
    )
    return overrides