"""Step 7C — bridge Aggregate Cost BOM → Cost Engine v2 hierarchical input.

Read-only transformation: aggregate-expanded BOM lines become the structural
source for `build_execution_layers_from_components`, replacing parent-only
`comp_flat_legacy` for volumetric v2 pricing.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from data.mini_module_registry_volumetric_v2 import DOSSIER_COMPONENT_TO_MODULE, PILOT_TEMPLATE
from schemas.aggregate_cost_bom import AggregateExpandedCostBom
from schemas.product_aggregate import ProductAggregate
from services.pricing_registry_service import V6_ALIGNED_TEMPLATE_CODES

logger = logging.getLogger(__name__)

MODULE_TO_DOSSIER: dict[str, str] = {v: k for k, v in DOSSIER_COMPONENT_TO_MODULE.items()}

BLOCKING_PRICING_BLOCKERS = frozenset(
    {
        "MISSING_FROM_INVENTORY",
        "MISSING_PRICE",
        "VARIANT_REQUIRED",
        "EXTERNAL_PRICE_REQUIRED",
    }
)


@dataclass
class TemplateRowIndex:
    materials: dict[str, dict[str, Any]] = field(default_factory=dict)
    operations: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class AggregatePriceContext:
    template_code: str
    aggregate: ProductAggregate
    aggregate_cost_bom: AggregateExpandedCostBom
    template_rows: TemplateRowIndex


def is_aggregate_cost_template(template_code: str | None) -> bool:
    code = str(template_code or "").strip()
    if code in V6_ALIGNED_TEMPLATE_CODES:
        return True
    return code == PILOT_TEMPLATE


def _parse_json_field(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return None


def _material_code(row: dict[str, Any]) -> str | None:
    code = row.get("material_code") or row.get("materialCode")
    return str(code).strip() if code else None


def _operation_code(row: dict[str, Any]) -> str | None:
    code = row.get("code") or row.get("operation_code") or row.get("operation_id")
    return str(code).strip() if code else None


def _ingest_template_rows(
    index: TemplateRowIndex,
    *,
    materials: list[Any],
    operations: list[Any],
) -> None:
    for row in materials or []:
        if not isinstance(row, dict):
            continue
        code = _material_code(row)
        if code:
            index.materials[code] = dict(row)
    for row in operations or []:
        if not isinstance(row, dict):
            continue
        code = _operation_code(row)
        if code:
            index.operations[code] = dict(row)


async def load_template_row_index(db, aggregate: ProductAggregate) -> TemplateRowIndex:
    from sqlalchemy import select

    from models.product_templates import Product_templates

    index = TemplateRowIndex()
    codes = {aggregate.template_code}
    for mod in aggregate.modules.required + aggregate.modules.optional:
        codes.add(mod.child_template_code)

    rows = (
        await db.execute(
            select(Product_templates).where(Product_templates.template_code.in_(sorted(codes)))
        )
    ).scalars().all()
    for tpl in rows:
        _ingest_template_rows(
            index,
            materials=_parse_json_field(tpl.required_materials_json) or [],
            operations=_parse_json_field(tpl.operations_json) or [],
        )
        components = _parse_json_field(tpl.components_json) or []
        if isinstance(components, list):
            for comp in components:
                if not isinstance(comp, dict):
                    continue
                _ingest_template_rows(
                    index,
                    materials=list(comp.get("materials") or []),
                    operations=list(comp.get("operations") or []),
                )
    return index


async def prepare_aggregate_price_context(
    db,
    template_code: str,
    *,
    workspace_id: str | None = None,
    quote_input: dict[str, Any] | None = None,
) -> AggregatePriceContext | None:
    if not is_aggregate_cost_template(template_code):
        return None

    from services.aggregate_cost_bom_adapter import AggregateCostBomBuilderService
    from services.product_aggregate_service import ProductAggregateService

    builder = AggregateCostBomBuilderService(db)
    aggregate_svc = ProductAggregateService(db)

    bom = await builder.build_preview(
        template_code,
        workspace_id=workspace_id,
        quote_input=quote_input,
    )
    aggregate = await aggregate_svc.build(template_code)
    if bom is None or aggregate is None:
        return None

    template_rows = await load_template_row_index(db, aggregate)
    return AggregatePriceContext(
        template_code=template_code,
        aggregate=aggregate,
        aggregate_cost_bom=bom,
        template_rows=template_rows,
    )


def collect_aggregate_pricing_blockers(bom: AggregateExpandedCostBom) -> list[str]:
    reasons: list[str] = []
    if bom.bom_status == "blocked":
        reasons.append("aggregate_bom:blocked")
    for mp in bom.missing_pricing:
        reasons.append(
            f"aggregate_bom:missing_pricing:{mp.item_type}:{mp.code}:{mp.reason}"
        )
    for pb in bom.pricing_blockers:
        if pb.blocker_code in BLOCKING_PRICING_BLOCKERS:
            reasons.append(f"aggregate_bom:{pb.blocker_code}:{pb.code}")
    for warning in bom.warnings:
        if "ACTIVE_MODULE_NO_COST_LINES" in warning:
            reasons.append(f"aggregate_bom:{warning}")
    if bom.missing_geometry:
        for key in bom.missing_geometry:
            if any(
                critical in key
                for critical in (
                    "selected_psu_watts",
                    "return_depth_mm",
                    "letter_face_area_m2",
                    "letter_perimeter_m",
                )
            ):
                reasons.append(f"aggregate_bom:missing_geometry:{key}")
    return sorted(set(reasons))


def _resolve_component_id(
    *,
    component_ref: str | None,
    mini_module_code: str | None,
    costable_components: dict[str, Any],
) -> str:
    if component_ref and component_ref in costable_components:
        return component_ref
    if mini_module_code:
        dossier = MODULE_TO_DOSSIER.get(mini_module_code)
        if dossier and dossier in costable_components:
            return dossier
    if component_ref:
        return component_ref
    if mini_module_code:
        return f"mod_{mini_module_code}"
    return "comp_aggregate_modular"


def _material_engine_row(
    mat: Any,
    *,
    resolved_code: str,
    template_rows: TemplateRowIndex,
) -> dict[str, Any]:
    base = template_rows.materials.get(resolved_code) or template_rows.materials.get(
        getattr(mat, "material_code", resolved_code)
    )
    if base:
        row = dict(base)
        row["material_code"] = resolved_code
        row["materialCode"] = resolved_code
        component_ref = getattr(mat, "component_ref", None)
        if component_ref:
            row["component_ref"] = component_ref
        row["_aggregate_provenance"] = getattr(mat, "provenance", None)
        row["_mini_module_code"] = getattr(mat, "mini_module_code", None)
        return row
    formula_id = getattr(mat, "formula_id", None)
    return {
        "material_code": resolved_code,
        "materialCode": resolved_code,
        "name": getattr(mat, "label", None) or resolved_code,
        "unit": getattr(mat, "unit", None) or "buc",
        "quantity": 0,
        "calculation_type": "formula_based" if formula_id else "static",
        "formula_id": formula_id,
        "component_ref": getattr(mat, "component_ref", None),
        "_aggregate_provenance": getattr(mat, "provenance", None),
        "_mini_module_code": getattr(mat, "mini_module_code", None),
    }


def _operation_engine_row(
    op: Any,
    *,
    template_rows: TemplateRowIndex,
) -> dict[str, Any]:
    base = template_rows.operations.get(op.operation_code)
    if base:
        row = dict(base)
        row["code"] = op.operation_code
        if op.workcenter:
            row["workcenter"] = op.workcenter
        if op.component_ref:
            row["component_ref"] = op.component_ref
        row["_aggregate_provenance"] = op.provenance
        row["_mini_module_code"] = op.mini_module_code
        return row
    return {
        "code": op.operation_code,
        "name": op.label or op.operation_code,
        "workcenter": op.workcenter,
        "calculation_type": "formula_based" if op.formula_id else "static",
        "formula_id": op.formula_id,
        "component_ref": op.component_ref,
        "_aggregate_provenance": op.provenance,
        "_mini_module_code": op.mini_module_code,
    }


def build_synthetic_hierarchical_template(
    ctx: AggregatePriceContext,
) -> dict[str, Any]:
    bom = ctx.aggregate_cost_bom
    components: dict[str, dict[str, Any]] = {}

    for comp in bom.costable_components:
        components[comp.component_id] = {
            "component_id": comp.component_id,
            "type": comp.role or "MODULAR",
            "name": comp.label_ro or comp.component_id,
            "materials": [],
            "operations": [],
            "_provenance": comp.provenance,
            "_mini_module_code": comp.mini_module_code,
        }

    op_index = {
        (op.operation_code, op.component_ref, op.mini_module_code): op
        for op in ctx.aggregate.operations
    }
    mat_index = {
        (m.material_code, m.component_ref, m.mini_module_code): m
        for m in ctx.aggregate.materials
    }

    for mat in bom.costable_materials:
        resolved = mat.resolved_material_code or mat.material_code
        comp_id = _resolve_component_id(
            component_ref=mat.component_ref,
            mini_module_code=mat.mini_module_code,
            costable_components=components,
        )
        if comp_id not in components:
            components[comp_id] = {
                "component_id": comp_id,
                "type": "MODULAR",
                "name": comp_id,
                "materials": [],
                "operations": [],
            }
        agg_mat = mat_index.get((mat.material_code, mat.component_ref, mat.mini_module_code))
        if not agg_mat:
            for key, candidate in mat_index.items():
                if key[0] == mat.material_code or key[0] == resolved:
                    agg_mat = candidate
                    break
        engine_row = _material_engine_row(
            agg_mat or mat,
            resolved_code=resolved,
            template_rows=ctx.template_rows,
        )
        components[comp_id]["materials"].append(engine_row)

    for op in bom.costable_operations:
        comp_id = _resolve_component_id(
            component_ref=op.component_ref,
            mini_module_code=op.mini_module_code,
            costable_components=components,
        )
        if comp_id not in components:
            components[comp_id] = {
                "component_id": comp_id,
                "type": "MODULAR",
                "name": comp_id,
                "materials": [],
                "operations": [],
            }
        agg_op = op_index.get((op.operation_code, op.component_ref, op.mini_module_code))
        if not agg_op:
            for key, candidate in op_index.items():
                if key[0] == op.operation_code:
                    agg_op = candidate
                    break
        components[comp_id]["operations"].append(
            _operation_engine_row(agg_op or op, template_rows=ctx.template_rows)
        )

    return {
        "template_code": ctx.template_code,
        "components_json": list(components.values()),
        "operations_json": [],
        "required_materials_json": [],
        "_aggregate_expanded_source": True,
    }


def costable_line_keys(bom: AggregateExpandedCostBom) -> set[str]:
    keys: set[str] = set()
    for mat in bom.costable_materials:
        keys.add(f"material:{mat.resolved_material_code or mat.material_code}")
    for op in bom.costable_operations:
        keys.add(f"operation:{op.operation_code}")
    return keys
