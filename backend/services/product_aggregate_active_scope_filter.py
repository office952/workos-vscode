"""Filter ProductAggregate to compiled active scope before downstream consumers."""

from __future__ import annotations

from typing import Any

from data.mini_module_registry_volumetric_v2 import (
    CHILD_TEMPLATE_TO_MODULE,
    DOSSIER_COMPONENT_TO_MODULE,
)
from schemas.active_scope import ActiveScopeResult
from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateComponent,
    ProductAggregateMaterial,
    ProductAggregateOperation,
    ProductAggregateTaskContract,
    ProductAggregateTaskRule,
)
from schemas.product_definition import ProductDefinitionPreview
from services.active_scope_resolver_service import (
    COMPOSITION_ONLY_EXECUTION_OPS,
    compile_active_scope,
)

GEOMETRY_GATE_OPERATIONS = frozenset({"svg_geometry_analysis"})

# Reverse map — identity rows for modules that have no parent components_json rows.
MODULE_TO_DOSSIER_COMPONENT: dict[str, str] = {
    module: component_id for component_id, module in DOSSIER_COMPONENT_TO_MODULE.items()
}

DOSSIER_COMPONENT_LABELS: dict[str, str] = {
    "comp_face_litere": "VIZUAL FAȚĂ",
    "comp_lateral_litere": "VOLUM ALUMINIU",
    "comp_spate_litere": "CAPAC SPATE",
    "comp_led_litere": "SISTEM LED",
    "comp_finisaj_litere": "FINISAJ",
}


def _module_for_component(comp: ProductAggregateComponent) -> str | None:
    if comp.mini_module_code:
        return comp.mini_module_code
    if comp.source_template_code:
        mapped = CHILD_TEMPLATE_TO_MODULE.get(comp.source_template_code)
        if mapped:
            return mapped
    return DOSSIER_COMPONENT_TO_MODULE.get(comp.component_id)


def _module_for_material(mat: ProductAggregateMaterial) -> str | None:
    if mat.mini_module_code:
        return mat.mini_module_code
    if mat.source_template_code:
        mapped = CHILD_TEMPLATE_TO_MODULE.get(mat.source_template_code)
        if mapped:
            return mapped
    if mat.component_ref:
        mapped = DOSSIER_COMPONENT_TO_MODULE.get(mat.component_ref)
        if mapped:
            return mapped
    return DOSSIER_COMPONENT_TO_MODULE.get(mat.component_ref or "")


def _module_for_operation(op: ProductAggregateOperation) -> str | None:
    if op.mini_module_code:
        return op.mini_module_code
    if op.operation_code in GEOMETRY_GATE_OPERATIONS:
        return "geometry_svg"
    if op.source_template_code:
        mapped = CHILD_TEMPLATE_TO_MODULE.get(op.source_template_code)
        if mapped:
            return mapped
    if op.component_ref:
        # Namespaced refs: "comp_x::node" — map base id when present.
        base = (op.component_ref or "").split("::", 1)[0]
        mapped = DOSSIER_COMPONENT_TO_MODULE.get(base) or DOSSIER_COMPONENT_TO_MODULE.get(
            op.component_ref
        )
        if mapped:
            return mapped
    return None


def _active_from_pd(pd: ProductDefinitionPreview) -> set[str]:
    active: set[str] = set()
    for mod in pd.selected_modules:
        if mod.state in ("always_on", "active", "conditional_active"):
            active.add(mod.module_code)
    return active


def resolve_scope_for_aggregate(
    *,
    pd: ProductDefinitionPreview,
    payload: dict[str, Any] | None = None,
    quote_input: dict[str, Any] | None = None,
) -> ActiveScopeResult:
    return compile_active_scope(
        template_code=pd.template_code,
        payload=payload or {},
        quote_input=quote_input or payload,
    )


def enrich_identity_components_for_modules(
    aggregate: ProductAggregate,
    modules: set[str],
) -> ProductAggregate:
    """Ensure sold/active modules have identity component rows (dossier map).

    Parent Letters templates may ship with empty components_json; linked children cover
    return aluminum only. FACE/BACK/LED/FINISH need identity rows for BOM/snapshot scope.
    """
    present_mods = {_module_for_component(c) for c in aggregate.components}
    extras: list[ProductAggregateComponent] = []
    for mod in sorted(modules):
        if mod in present_mods or mod == "geometry_svg":
            continue
        component_id = MODULE_TO_DOSSIER_COMPONENT.get(mod)
        if not component_id:
            continue
        extras.append(
            ProductAggregateComponent(
                component_id=component_id,
                label_ro=DOSSIER_COMPONENT_LABELS.get(component_id),
                role=mod,
                mini_module_code=mod,
                provenance="dossier",
                source_template_code=aggregate.template_code,
                status="present",
            )
        )
    # Geometry calc prerequisite — identity only (not a sold commercial module).
    if "geometry_svg" in modules and "geometry_svg" not in present_mods:
        extras.append(
            ProductAggregateComponent(
                component_id="comp_geometry_svg_gate",
                label_ro="Geometry / SVG",
                role="geometry_svg",
                mini_module_code="geometry_svg",
                provenance="dossier",
                source_template_code=aggregate.template_code,
                status="present",
            )
        )
    if not extras:
        return aggregate
    return aggregate.model_copy(update={"components": list(aggregate.components) + extras})


def filter_aggregate_by_active_scope(
    aggregate: ProductAggregate,
    *,
    pd: ProductDefinitionPreview,
    scope: ActiveScopeResult | None = None,
    payload: dict[str, Any] | None = None,
) -> ProductAggregate:
    """Emit only selected-scope graph rows for component_subset; enrich full product identity."""
    scope = scope or resolve_scope_for_aggregate(pd=pd, payload=payload)
    if scope.use_legacy_full_product or scope.errors:
        # Full product: keep graph, add missing dossier identity rows for PD-active modules.
        legacy_mods = _active_from_pd(pd) or set(MODULE_TO_DOSSIER_COMPONENT.keys())
        return enrich_identity_components_for_modules(aggregate, legacy_mods | {"geometry_svg"})

    allowed = scope.active_set()
    sold_set = set(scope.sold_module_codes)
    composition_excluded = set(scope.composition_excluded_operations) | set(
        COMPOSITION_ONLY_EXECUTION_OPS
        if sold_set == {"RETURN-CANT"}
        or ("RETURN-CANT" in sold_set and "FACE" not in sold_set)
        else ()
    )
    composition_excluded_materials = {
        str(code).strip().upper()
        for code in (scope.composition_excluded_materials or [])
        if str(code).strip()
    } | {
        str(code).strip().lower()
        for code in (scope.composition_excluded_materials or [])
        if str(code).strip()
    }

    components: list[ProductAggregateComponent] = []
    for comp in aggregate.components:
        mod = _module_for_component(comp)
        if mod is None or mod in allowed:
            if mod is None and allowed:
                # Unmapped parent rows are not automatically active in subset mode.
                continue
            if mod is None:
                continue
            tagged = comp if comp.mini_module_code else comp.model_copy(update={"mini_module_code": mod})
            components.append(tagged)

    materials: list[ProductAggregateMaterial] = []
    for mat in aggregate.materials:
        mat_code = str(mat.material_code or "").strip()
        if mat_code and (
            mat_code.upper() in composition_excluded_materials
            or mat_code.lower() in composition_excluded_materials
        ):
            continue
        mod = _module_for_material(mat)
        if mod is None:
            continue
        if mod not in allowed:
            continue
        tagged = mat if mat.mini_module_code else mat.model_copy(update={"mini_module_code": mod})
        materials.append(tagged)

    operations: list[ProductAggregateOperation] = []
    for op in aggregate.operations:
        # Composition-only ops excluded even when parent module is sold.
        if op.operation_code in composition_excluded:
            continue
        priced = str(getattr(op, "priced_operation", "") or "")
        if priced in composition_excluded:
            continue
        mod = _module_for_operation(op)
        if mod is None:
            continue
        if mod not in allowed:
            continue
        # Bonding ops historically tagged asamblare — exclude unless FACE+CANT interface.
        if (
            "FACE" not in sold_set
            and "RETURN-CANT" in sold_set
            and (op.mini_module_code == "asamblare" or "bonding" in (op.operation_code or "").lower())
        ):
            continue
        tagged = op if op.mini_module_code else op.model_copy(update={"mini_module_code": mod})
        operations.append(tagged)

    task_contract = aggregate.task_contract
    if task_contract is not None and task_contract.task_rules:
        kept_rules: list[ProductAggregateTaskRule] = []
        for rule in task_contract.task_rules:
            priced = str(getattr(rule, "priced_operation", "") or "")
            if priced in composition_excluded:
                continue
            mod = getattr(rule, "mini_module_code", None) or None
            if mod and mod not in allowed and priced != "vector_prep":
                # vector_prep maps to geometry — allow when geometry_svg active
                if not (priced == "vector_prep" and "geometry_svg" in allowed):
                    continue
            if priced == "vector_prep" and "geometry_svg" not in allowed:
                continue
            if mod is None and priced == "vector_prep" and "geometry_svg" in allowed:
                kept_rules.append(rule)
                continue
            if mod is None:
                # Unscoped dossier rules drop in subset mode.
                continue
            if mod in allowed or (priced == "vector_prep" and "geometry_svg" in allowed):
                kept_rules.append(rule)
        task_contract = ProductAggregateTaskContract(
            task_rules=kept_rules,
            notes=list(task_contract.notes)
            + [
                f"ACTIVE_SCOPE_SELECTED_GRAPH mode={scope.mode} "
                f"sold={scope.sold_module_codes} modules={sorted(allowed)}"
            ],
        )

    scoped = aggregate.model_copy(
        update={
            "components": components,
            "materials": materials,
            "operations": operations,
            "task_contract": task_contract,
        }
    )
    return enrich_identity_components_for_modules(scoped, allowed)


def pd_active_module_codes(pd: ProductDefinitionPreview) -> set[str]:
    return _active_from_pd(pd)
