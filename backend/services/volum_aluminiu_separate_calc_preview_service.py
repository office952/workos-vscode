"""Read-only separate calculation preview for TPL-VOLUM-ALUMINIU_v1.

Uses existing commercial/internal rule definitions (ml). No PT/Quote/Order/EP persist.
Does not require template activation.
"""

from __future__ import annotations

import copy
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from data.commercial_rules_volumetric_v2 import RULES_BY_TEMPLATE as COMMERCIAL_RULES_BY_TEMPLATE
from data.internal_cost_rules_volumetric_v2 import RULES_BY_TEMPLATE as INTERNAL_RULES_BY_TEMPLATE
from schemas.volum_aluminiu_separate_calc_preview import (
    VolumAluminiuSeparateCalcPreviewRequest,
    VolumAluminiuSeparateCalcPreviewResponse,
)
from services.return_cant_product_truth_bridge import build_return_cant_runtime_product_truth
from services.volum_aluminiu_component_contract import (
    CANONICAL_PERIMETER_UNIT,
    COMMERCIAL_BASIS_SYNONYM,
    COMMERCIAL_LINE_CODE,
    COMMERCIAL_RULE_CODE,
    INTERNAL_RULE_CODE,
    MINI_MODULE_CODE,
    PARENT_TEMPLATE_CODE,
    TEMPLATE_CODE,
    build_input_contract_view,
    evaluate_separate_calculation_readiness,
    extract_return_cant_instances,
)
from services.volum_aluminiu_quantity_ownership import (
    build_derived_quantities,
    build_quantity_and_ops_ownership_view,
    resolve_component_quantity_from_payload,
)


def _hydrate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    working = copy.deepcopy(payload or {})
    subtree = build_return_cant_runtime_product_truth(working)
    product_truth = working.setdefault("product_truth", {})
    if not isinstance(product_truth, dict):
        product_truth = {}
        working["product_truth"] = product_truth
    components = product_truth.setdefault("components", {})
    if not isinstance(components, dict):
        components = {}
        product_truth["components"] = components
    components["return_cant"] = subtree["components"]["return_cant"]
    return working


def _primary_depth_and_finish(instances: dict[str, Any]) -> tuple[int | None, str | None]:
    depth: int | None = None
    finish: str | None = None
    for inst in instances.values():
        if not isinstance(inst, dict):
            continue
        profile = inst.get("material_profile") if isinstance(inst.get("material_profile"), dict) else {}
        width = profile.get("width_mm")
        if isinstance(width, int):
            depth = width
        elif width is not None:
            try:
                depth = int(width)
            except (TypeError, ValueError):
                pass
        variant = inst.get("finish_variant") if isinstance(inst.get("finish_variant"), dict) else {}
        finish = str(variant.get("type") or finish or "") or None
    return depth, finish


def _commercial_slice(*, quantity_ml: float, currency: str) -> dict[str, Any]:
    rules = COMMERCIAL_RULES_BY_TEMPLATE.get(PARENT_TEMPLATE_CODE) or ()
    rule = None
    for item in rules:
        if getattr(item, "line_code", None) == COMMERCIAL_LINE_CODE:
            rule = item
            break
    if rule is None:
        return {
            "ok": False,
            "error": "commercial_rule_missing",
            "line_code": COMMERCIAL_LINE_CODE,
            "basis": COMMERCIAL_BASIS_SYNONYM,
        }
    unit_price = getattr(rule, "documented_unit_price", None)
    line_total = None
    if unit_price is not None:
        try:
            line_total = round(float(unit_price) * float(quantity_ml), 4)
        except (TypeError, ValueError):
            line_total = None
    return {
        "ok": True,
        "line_code": rule.line_code,
        "label": rule.label,
        "module_code": rule.module_code,
        "component_code": rule.component_code,
        "pricing_rule_code": rule.pricing_rule_code,
        "basis_type": rule.basis_type,
        "unit": rule.unit,
        "quantity": quantity_ml,
        "quantity_source": "confirmed_perimeter_m",
        "unit_price": unit_price,
        "currency": getattr(rule, "documented_unit_price_currency", None) or currency,
        "line_total": line_total,
        "anti_hourly": True,
        "warnings": list(getattr(rule, "warnings", ()) or ()),
        "note": "Read-only rule projection; no Pricing Registry redesign; no quote persist",
    }


def _internal_cost_slice(*, quantity_ml: float) -> dict[str, Any]:
    pack = INTERNAL_RULES_BY_TEMPLATE.get(PARENT_TEMPLATE_CODE) or {}
    rules = pack.get("operations") or ()
    rule = None
    for item in rules:
        if getattr(item, "rule_code", None) == INTERNAL_RULE_CODE:
            rule = item
            break
    if rule is None:
        return {
            "ok": False,
            "error": "internal_rule_missing",
            "rule_code": INTERNAL_RULE_CODE,
            "basis": COMMERCIAL_BASIS_SYNONYM,
        }
    unit_cost = getattr(rule, "internal_unit_cost", None)
    line_total = None
    if unit_cost is not None:
        try:
            line_total = round(float(unit_cost) * float(quantity_ml), 4)
        except (TypeError, ValueError):
            line_total = None
    return {
        "ok": True,
        "line_code": rule.line_code,
        "label": rule.label,
        "module_code": rule.module_code,
        "component_code": rule.component_code,
        "rule_code": rule.rule_code,
        "basis_type": rule.basis_type,
        "unit": rule.unit,
        "quantity": quantity_ml,
        "quantity_source": "confirmed_perimeter_m",
        "unit_cost": unit_cost,
        "line_total": line_total,
        "anti_hourly": True,
        "warnings": list(getattr(rule, "warnings", ()) or ()),
        "note": "Read-only internal cost projection; no EP materialization",
    }


class VolumAluminiuSeparateCalcPreviewService:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db  # reserved; preview is payload-driven and does not require writes

    def build_preview(
        self,
        template_code: str,
        body: VolumAluminiuSeparateCalcPreviewRequest,
    ) -> VolumAluminiuSeparateCalcPreviewResponse:
        code = (template_code or "").strip()
        if code != TEMPLATE_CODE:
            return VolumAluminiuSeparateCalcPreviewResponse(
                template_code=code,
                mini_module_code=MINI_MODULE_CODE,
                separate_calculation="FAIL",
                blockers=["TEMPLATE_NOT_VOLUM_ALUMINIU"],
                warnings=[],
                input_contract=build_input_contract_view(),
            )

        hydrated = _hydrate_payload(body.payload)
        instances = extract_return_cant_instances(hydrated)
        readiness = evaluate_separate_calculation_readiness(instances)
        quantity = resolve_component_quantity_from_payload(hydrated)
        ownership = build_quantity_and_ops_ownership_view()

        depth, finish = _primary_depth_and_finish(instances)
        derived: dict[str, Any] = {}
        commercial = None
        internal = None
        blockers = list(quantity.get("blockers") or [])
        for reason in readiness.get("reasons") or []:
            if reason not in blockers:
                blockers.append(reason)

        if quantity.get("ok") and quantity.get("quantity_m") is not None:
            derived = build_derived_quantities(
                quantity_m=float(quantity["quantity_m"]),
                depth_mm=depth,
                finish_type=finish,
            )
            if body.include_commercial_line:
                commercial = _commercial_slice(
                    quantity_ml=float(quantity["quantity_ml"]),
                    currency=body.currency,
                )
            if body.include_internal_cost_line:
                internal = _internal_cost_slice(quantity_ml=float(quantity["quantity_ml"]))

        unit_trace = [
            {
                "stage": "evidence",
                "field": "quote_geometry.letter_perimeter_m",
                "unit": CANONICAL_PERIMETER_UNIT,
                "conversion_owner": "observe_only",
            },
            {
                "stage": "product_truth",
                "field": "confirmed_perimeter_m",
                "unit": CANONICAL_PERIMETER_UNIT,
                "conversion_owner": "operator_confirm",
            },
            {
                "stage": "component_qty",
                "field": "return_profile_linear_meter",
                "unit": CANONICAL_PERIMETER_UNIT,
                "conversion_owner": "component",
            },
            {
                "stage": "commercial",
                "field": COMMERCIAL_RULE_CODE,
                "unit": COMMERCIAL_BASIS_SYNONYM,
                "conversion_owner": "synonym_1ml_eq_1m",
            },
            {
                "stage": "internal_cost",
                "field": INTERNAL_RULE_CODE,
                "unit": COMMERCIAL_BASIS_SYNONYM,
                "conversion_owner": "synonym_1ml_eq_1m",
            },
        ]

        return VolumAluminiuSeparateCalcPreviewResponse(
            template_code=TEMPLATE_CODE,
            mini_module_code=MINI_MODULE_CODE,
            persist=False,
            activation_required=False,
            publication_blocked=True,
            separate_calculation=str(readiness.get("separate_calculation") or "FAIL"),
            readiness=readiness,
            quantity=quantity,
            derived_quantities=derived,
            instances=instances,
            materials_ops_ownership=ownership["materials_ops_ownership"],
            commercial=commercial,
            internal_cost=internal,
            unit_trace=unit_trace,
            remaining_parent_deps=list(
                ownership["quantity_ownership"].get("remaining_parent_deps") or []
            ),
            blockers=blockers,
            warnings=[
                "publication_and_activation_remain_blocked",
                "identity_aliases_mapped_via_IDENTITY_MAP",
                "quote_geometry_controlled_bridge_or_legacy_fallback",
            ],
            input_contract=build_input_contract_view(),
        )
