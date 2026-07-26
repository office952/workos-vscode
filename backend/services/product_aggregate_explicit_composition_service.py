"""Compile ProductAggregate from explicit ProductDefinition composition graph."""

from __future__ import annotations

from typing import Any

from schemas.product_aggregate import (
    ProductAggregate,
    ProductAggregateComponent,
    ProductAggregateCompositionEdge,
    ProductAggregateCompositionGraph,
    ProductAggregateCompositionNode,
    ProductAggregateConflict,
    ProductAggregateMaterial,
    ProductAggregateModule,
    ProductAggregateModules,
    ProductAggregateOperation,
    ProductAggregateProvenanceSummary,
)
from schemas.product_definition import CompositionEdge, CompositionNode, ProductDefinitionComposition, ProductDefinitionPreview

WARNING_EXPLICIT_GRAPH_APPLIED = "EXPLICIT_COMPOSITION_GRAPH_APPLIED"
WARNING_UPSTREAM_TRUTH_MISSING = "UPSTREAM_TRUTH_MISSING"
CONFLICT_COMPOSITION_BLOCKED = "COMPOSITION_GRAPH_BLOCKED"
CONFLICT_CHILD_AGGREGATE_MISSING = "COMPOSITION_CHILD_AGGREGATE_MISSING"


def _included_nodes(composition: ProductDefinitionComposition) -> list[CompositionNode]:
    return [node for node in composition.nodes if node.included_in_graph]


def _included_edges(composition: ProductDefinitionComposition) -> list[CompositionEdge]:
    return [edge for edge in composition.edges if edge.included_in_graph]


def explicit_child_template_codes(composition: ProductDefinitionComposition) -> list[str]:
    root = composition.root_template_code
    codes = [
        node.template_code
        for node in _included_nodes(composition)
        if node.node_role != "root_product" and node.template_code != root
    ]
    return sorted(dict.fromkeys(codes))


def _registry_child_codes(aggregate: ProductAggregate) -> set[str]:
    return {
        module.child_template_code
        for module in [*aggregate.modules.required, *aggregate.modules.optional]
        if module.child_template_code
    }


def _to_graph_node(node: CompositionNode) -> ProductAggregateCompositionNode:
    return ProductAggregateCompositionNode(
        node_id=node.node_id,
        template_code=node.template_code,
        node_role=node.node_role,
        module_code=node.module_code,
        module_role=node.module_role,
        parent_node_id=node.parent_node_id,
        activation_source=node.activation_source,
        inherited_inputs=dict(node.inherited_inputs),
        locally_owned_inputs=dict(node.locally_owned_inputs),
        unresolved_inputs=list(node.unresolved_inputs),
        blockers=list(node.blockers),
        warnings=list(node.warnings),
    )


def _to_graph_edge(edge: CompositionEdge) -> ProductAggregateCompositionEdge:
    return ProductAggregateCompositionEdge(
        edge_id=edge.edge_id,
        parent_template_code=edge.parent_template_code,
        parent_node_id=edge.parent_node_id,
        child_template_code=edge.child_template_code,
        child_node_id=edge.child_node_id,
        child_role=edge.child_role,
        relation_type=edge.relation_type,
        dependency_role=edge.dependency_role,
        inherited_inputs=dict(edge.inherited_inputs),
        locally_owned_inputs=dict(edge.locally_owned_inputs),
        blockers=list(edge.blockers),
    )


def _build_composition_graph(
    composition: ProductDefinitionComposition,
) -> ProductAggregateCompositionGraph:
    return ProductAggregateCompositionGraph(
        composed_graph_version=composition.composed_graph_version,
        composition_mode=composition.composition_mode,
        root_template_code=composition.root_template_code,
        solution_status=composition.solution_status,
        compatibility_status=composition.compatibility_status,
        blockers=list(composition.blockers),
        warnings=list(composition.warnings),
        active_child_template_codes=explicit_child_template_codes(composition),
        nodes=[_to_graph_node(node) for node in _included_nodes(composition)],
        edges=[_to_graph_edge(edge) for edge in _included_edges(composition)],
        frozen_mounting_solution=(
            dict(composition.frozen_mounting_solution)
            if isinstance(composition.frozen_mounting_solution, dict)
            else None
        ),
    )


def _runtime_mini_module_for_child(
    *,
    source_template_code: str,
    composition_module_code: str | None,
) -> str | None:
    """Map composition child → runtime mini_module_code (not composition role)."""
    from data.mini_module_registry_volumetric_v2 import CHILD_TEMPLATE_TO_MODULE

    return CHILD_TEMPLATE_TO_MODULE.get(source_template_code) or composition_module_code


def _namespace_component(
    component: ProductAggregateComponent,
    *,
    node: CompositionNode,
) -> ProductAggregateComponent:
    component_ref = component.component_id
    if "::" not in component_ref:
        component_ref = f"{node.node_id}::{component.component_id}"
    return component.model_copy(
        update={
            "component_id": component_ref,
            "role": node.node_role,
            "source_template_code": node.template_code,
            "mini_module_code": _runtime_mini_module_for_child(
                source_template_code=node.template_code,
                composition_module_code=node.module_code,
            ),
            "provenance": "linked_module",
            "status": "present",
            "materials": [],
            "operations": [],
        }
    )


def _namespace_material(
    material: ProductAggregateMaterial,
    *,
    node_id: str,
    source_template_code: str,
    mini_module_code: str | None,
) -> ProductAggregateMaterial:
    component_ref = material.component_ref or node_id
    if "::" not in str(component_ref):
        component_ref = f"{node_id}::{component_ref}"
    return material.model_copy(
        update={
            "component_ref": component_ref,
            "source_template_code": source_template_code,
            "mini_module_code": _runtime_mini_module_for_child(
                source_template_code=source_template_code,
                composition_module_code=mini_module_code,
            ),
            "provenance": "linked_module",
            "status": "present",
        }
    )


def _namespace_operation(
    operation: ProductAggregateOperation,
    *,
    node_id: str,
    source_template_code: str,
    mini_module_code: str | None,
) -> ProductAggregateOperation:
    component_ref = operation.component_ref or node_id
    if "::" not in str(component_ref):
        component_ref = f"{node_id}::{component_ref}"
    return operation.model_copy(
        update={
            "component_ref": component_ref,
            "source_template_code": source_template_code,
            "mini_module_code": _runtime_mini_module_for_child(
                source_template_code=source_template_code,
                composition_module_code=mini_module_code,
            ),
            "provenance": "linked_module",
            "status": "present",
        }
    )


def _filter_modules(
    modules: list[ProductAggregateModule],
    *,
    active_child_codes: set[str],
) -> list[ProductAggregateModule]:
    filtered: list[ProductAggregateModule] = []
    for module in modules:
        if module.child_template_code not in active_child_codes:
            continue
        filtered.append(module.model_copy(update={"active": True}))
    return filtered


def _upstream_truth_conflicts(pd: ProductDefinitionPreview) -> list[ProductAggregateConflict]:
    conflicts: list[ProductAggregateConflict] = []
    missing = list(pd.validation.missing_required_fields or [])
    if "volum_aluminum_module_template_code" in missing:
        composition = pd.composition
        volum_in_graph = any(
            node.node_role == "volum_aluminum"
            for node in (composition.nodes if composition else [])
            if node.included_in_graph
        )
        if not volum_in_graph:
            conflicts.append(
                ProductAggregateConflict(
                    code=WARNING_UPSTREAM_TRUTH_MISSING,
                    severity="warning",
                    message=(
                        "Intake has not persisted volum_aluminum_module_template_code; "
                        "explicit composition graph omits volum_aluminum child."
                    ),
                    field="volum_aluminum_module_template_code",
                    details={"owner": "intake", "graph_child_omitted": True},
                )
            )
    return conflicts


def apply_explicit_composition_graph(
    *,
    pd: ProductDefinitionPreview,
    base_aggregate: ProductAggregate,
    child_aggregates_by_template: dict[str, ProductAggregate],
) -> ProductAggregate:
    """Filter and compile aggregate structure from ProductDefinition composition graph."""
    composition = pd.composition
    if composition is None:
        return base_aggregate

    graph = _build_composition_graph(composition)
    active_child_codes = set(graph.active_child_template_codes)
    registry_child_codes = _registry_child_codes(base_aggregate)
    stripped_child_codes = sorted(registry_child_codes - active_child_codes)

    canonical_values = dict(pd.canonical_values or {})
    if canonical_values:
        enriched_nodes: list[ProductAggregateCompositionNode] = []
        for node in graph.nodes:
            if node.node_role != "root_product":
                enriched_nodes.append(node)
                continue
            merged_inputs = dict(node.inherited_inputs)
            for key in (
                "face_finish_type",
                "return_finish_type",
                "return_depth_mm",
                "backing_mode",
                "width_mm",
                "height_mm",
                "letter_face_area_m2",
            ):
                if key in canonical_values and canonical_values[key] is not None:
                    merged_inputs[key] = canonical_values[key]
            enriched_nodes.append(node.model_copy(update={"inherited_inputs": merged_inputs}))
        graph = graph.model_copy(update={"nodes": enriched_nodes})

    conflicts: list[ProductAggregateConflict] = list(base_aggregate.conflicts)
    warnings: list[ProductAggregateConflict] = list(base_aggregate.warnings)

    if composition.solution_status == "blocked" or composition.blockers:
        conflicts.append(
            ProductAggregateConflict(
                code=CONFLICT_COMPOSITION_BLOCKED,
                severity="error",
                message="ProductDefinition composition graph is blocked.",
                details={
                    "blockers": list(composition.blockers),
                    "solution_status": composition.solution_status,
                },
            )
        )

    conflicts.extend(_upstream_truth_conflicts(pd))

    components = list(base_aggregate.components)
    materials = [
        item
        for item in base_aggregate.materials
        if item.provenance == "parent" or item.source_template_code not in registry_child_codes
    ]
    operations = [
        item
        for item in base_aggregate.operations
        if item.provenance == "parent" or item.source_template_code not in registry_child_codes
    ]

    for node in _included_nodes(composition):
        if node.node_role == "root_product":
            continue
        child_aggregate = child_aggregates_by_template.get(node.template_code)
        if child_aggregate is None:
            conflicts.append(
                ProductAggregateConflict(
                    code=CONFLICT_CHILD_AGGREGATE_MISSING,
                    severity="error",
                    message=f"Missing child aggregate for graph node {node.node_id}.",
                    field=node.template_code,
                    details={"node_id": node.node_id, "node_role": node.node_role},
                )
            )
            continue

        components.extend(
            _namespace_component(component, node=node)
            for component in child_aggregate.components
        )
        materials.extend(
            _namespace_material(
                material,
                node_id=node.node_id,
                source_template_code=node.template_code,
                mini_module_code=node.module_code,
            )
            for material in child_aggregate.materials
        )
        operations.extend(
            _namespace_operation(
                operation,
                node_id=node.node_id,
                source_template_code=node.template_code,
                mini_module_code=node.module_code,
            )
            for operation in child_aggregate.operations
        )

    modules = ProductAggregateModules(
        required=_filter_modules(base_aggregate.modules.required, active_child_codes=active_child_codes),
        optional=_filter_modules(base_aggregate.modules.optional, active_child_codes=active_child_codes),
    )

    warnings.append(
        ProductAggregateConflict(
            code=WARNING_EXPLICIT_GRAPH_APPLIED,
            severity="info",
            message=(
                "ProductAggregate compiled from explicit ProductDefinition composition graph "
                "without registry trigger re-inference."
            ),
            details={
                "composition_mode": composition.composition_mode,
                "active_child_template_codes": graph.active_child_template_codes,
                "stripped_registry_child_codes": stripped_child_codes,
                "node_count": len(graph.nodes),
                "edge_count": len(graph.edges),
            },
        )
    )

    provenance_summary = ProductAggregateProvenanceSummary(
        parent=dict(base_aggregate.provenance_summary.parent),
        dossier=dict(base_aggregate.provenance_summary.dossier),
        linked_modules={
            **dict(base_aggregate.provenance_summary.linked_modules),
            "explicit_graph_children": len(active_child_codes),
            "stripped_registry_children": len(stripped_child_codes),
        },
        aggregate_totals={
            "components": len(components),
            "materials": len(materials),
            "operations": len(operations),
            "composition_nodes": len(graph.nodes),
            "composition_edges": len(graph.edges),
        },
        product_truth_job_revision=base_aggregate.provenance_summary.product_truth_job_revision,
        product_truth_content_hash=base_aggregate.provenance_summary.product_truth_content_hash,
        product_truth_status=base_aggregate.provenance_summary.product_truth_status,
    )

    return base_aggregate.model_copy(
        update={
            "modules": modules,
            "components": components,
            "materials": materials,
            "operations": operations,
            "conflicts": conflicts,
            "warnings": warnings,
            "composition_graph": graph,
            "provenance_summary": provenance_summary,
        }
    )
