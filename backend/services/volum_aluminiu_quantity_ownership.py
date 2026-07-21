"""Quantity ownership for TPL-VOLUM-ALUMINIU_v1 / modelare_cant.

Confirmed return_cant perimeter owns component separate-calc qty.
Parent quote_geometry remains evidence / product-total fallback — never silent for separate calc.
"""

from __future__ import annotations

from typing import Any, Mapping

from services.volum_aluminiu_component_contract import (
    BOM_COMPONENT_ID,
    CANONICAL_PERIMETER_UNIT,
    COMMERCIAL_BASIS_SYNONYM,
    COMMERCIAL_LINE_CODE,
    COMMERCIAL_RULE_CODE,
    INTERNAL_RULE_CODE,
    MINI_MODULE_CODE,
    PRICING_COMPONENT_CODE,
    TEMPLATE_CODE,
    extract_return_cant_instances,
    instance_has_confirmed_perimeter,
    round_perimeter_m,
)


def sum_confirmed_perimeter_m(instances: Mapping[str, Any] | None) -> tuple[float | None, list[str]]:
    """Sum confirmed perimeters across return_cant instances. Fail closed if any unconfirmed."""
    rows = instances or {}
    if not rows:
        return None, ["RETURN_CANT_INSTANCE_MISSING"]

    total = 0.0
    blockers: list[str] = []
    for key, inst in rows.items():
        if not isinstance(inst, Mapping):
            blockers.append(f"RETURN_CANT_INSTANCE_INVALID:{key}")
            continue
        if not instance_has_confirmed_perimeter(inst):
            blockers.append(f"RETURN_CANT_UNCONFIRMED:{key}")
            continue
        geometry = inst.get("geometry") if isinstance(inst.get("geometry"), Mapping) else {}
        total += float(geometry["confirmed_perimeter_m"])

    if blockers:
        return None, blockers
    if total <= 0:
        return None, ["RETURN_CANT_PERIMETER_NON_POSITIVE"]
    return round_perimeter_m(total), []


def resolve_component_quantity_from_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Component-owned qty resolver for separate calc — no parent unconfirmed fallback."""
    instances = extract_return_cant_instances(payload)
    qty_m, blockers = sum_confirmed_perimeter_m(instances)
    evidence = None
    if isinstance(payload, Mapping):
        geom = payload.get("quote_geometry")
        if isinstance(geom, Mapping):
            try:
                evidence = float(geom.get("letter_perimeter_m"))  # type: ignore[arg-type]
                if evidence <= 0:
                    evidence = None
            except (TypeError, ValueError):
                evidence = None

    return {
        "schema": "volum_aluminiu_component_quantity_v1",
        "template_code": TEMPLATE_CODE,
        "mini_module_code": MINI_MODULE_CODE,
        "unit": CANONICAL_PERIMETER_UNIT,
        "commercial_basis_synonym": COMMERCIAL_BASIS_SYNONYM,
        "quantity_m": qty_m,
        "quantity_ml": qty_m,  # synonym — same magnitude
        "source": "product_truth.components.return_cant.confirmed_perimeter_m"
        if qty_m is not None
        else None,
        "evidence_perimeter_m": evidence,
        "evidence_drives_calc": False,
        "parent_unconfirmed_fallback_used": False,
        "blockers": blockers,
        "ok": qty_m is not None and not blockers,
    }


def build_derived_quantities(
    *,
    quantity_m: float,
    depth_mm: int | None,
    finish_type: str | None,
) -> dict[str, Any]:
    """Component-owned derived qty map (no EP materialization)."""
    derived: dict[str, Any] = {
        "return_profile_linear_meter": quantity_m,
        "return_profile_linear_ml": quantity_m,
        "depth_mm": depth_mm,
    }
    # Wrap/paint area formulas are depth-sensitive on child PT; surface intent only here.
    if depth_mm is not None and finish_type:
        token = finish_type.strip().lower()
        if token in {"oracal_651", "oracal_641", "oracal_wrapped", "oracal", "vinyl", "colantat"}:
            derived["return_wrap_linear_meter"] = quantity_m
            derived["return_wrap_note"] = "area formula remains child material formula_id return_wrap_area"
        if token in {"ral_paint", "vopsit_ral", "ral", "painted", "paint"}:
            derived["return_paint_linear_meter"] = quantity_m
            derived["return_paint_note"] = "consumption formula remains child formula_id return_paint_consumption"
    return derived


def build_quantity_and_ops_ownership_view() -> dict[str, Any]:
    return {
        "quantity_ownership": {
            "primary_input": "confirmed_perimeter_m",
            "unit": CANONICAL_PERIMETER_UNIT,
            "commercial_basis": COMMERCIAL_BASIS_SYNONYM,
            "resolver": "resolve_component_quantity_from_payload",
            "parent_dependency": {
                "field": "quote_geometry.letter_perimeter_m",
                "role": "evidence_only",
                "may_drive_separate_calc": False,
            },
            "remaining_parent_deps": [
                "letter_group / layer mapping for instance keys",
                "product-total VL CPP may still consume quote_geometry until activation GO",
            ],
            "dual_id": {
                "bom_component_id": BOM_COMPONENT_ID,
                "pricing_component_code": PRICING_COMPONENT_CODE,
            },
        },
        "materials_ops_ownership": {
            "owner_template": TEMPLATE_CODE,
            "bom_component_id": BOM_COMPONENT_ID,
            "materials": [
                "MAT-PROFIL-LATERAL-LITERE-30MM|60MM|80MM|100MM → return_profile_linear_meter",
                "MAT-ORACAL-651 → return_wrap_area (finish-gated)",
                "MAT-VOPSEA-RAL* → return_paint_consumption (finish-gated)",
                "MAT-ADEZIV-CANT-LITERE → return_profile_adhesive",
            ],
            "operations": [
                "RETURN_PROFILE_MACHINE_FORMING → return_profile_machine_forming",
                "RETURN_PROFILE_FACE_BONDING → return_profile_face_bonding (Aggregate modelare_cant)",
                "PAINTING → return_painting_linear_meter (finish-gated)",
            ],
            "aggregate_provenance": "linked_module",
            "commercial_ref": {
                "line_code": COMMERCIAL_LINE_CODE,
                "rule_code": COMMERCIAL_RULE_CODE,
                "basis": COMMERCIAL_BASIS_SYNONYM,
            },
            "internal_cost_ref": {
                "rule_code": INTERNAL_RULE_CODE,
                "basis": COMMERCIAL_BASIS_SYNONYM,
            },
            "execution_materialization": False,
        },
    }
