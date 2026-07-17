"""Project Product Aggregate composition_graph into cost-domain structural scope."""

from __future__ import annotations

from typing import Any

from data.mini_module_registry_volumetric_v2 import CHILD_TEMPLATE_TO_MODULE
from schemas.graph_cost_projection import (
    GRAPH_COST_PROJECTION_VERSION,
    GraphCostProjection,
    GraphCostProjectionEdge,
    GraphCostProjectionNode,
)
from schemas.product_aggregate import ProductAggregate, ProductAggregateCompositionGraph
from schemas.product_definition import ProductDefinitionPreview
from services.offer_scope_resolver_service import merge_scope_payload

TD_W3_GRAPH_COST_LEGACY_COMPAT = "TD-W3-GRAPH-COST-001"

BAR_MOUNTING = frozenset({"steel_bars", "aluminum_bars"})
GATE_ONLY_MODULES = frozenset({"geometry_svg"})
FUTURE_MODULES = frozenset({"electrica_logo"})

GRAPH_STRUCTURAL_ROLES = frozenset({"mounting_panel", "premount_structure", "volum_aluminum"})


def _module_is_cost_active(state: str) -> bool:
    return state in ("always_on", "active", "conditional_active")


def _root_mini_modules_from_pd(
    pd: ProductDefinitionPreview,
    quote_input: dict[str, Any] | None = None,
) -> set[str]:
    """Root letter modules from PD states — excludes graph-owned structural modules."""
    active: set[str] = set()
    seen: set[str] = set()
    all_mods = list(pd.selected_modules) + list(pd.optional_modules) + list(pd.inactive_modules)
    for mod in all_mods:
        if mod.module_code in seen:
            continue
        seen.add(mod.module_code)
        code = mod.module_code
        if code in FUTURE_MODULES or code in GATE_ONLY_MODULES:
            continue
        if code in ("structura_suport", "modelare_cant"):
            continue
        if code == "finisaje":
            active.add(code)
            continue
        if code == "sistem_led":
            if mod.state in ("active", "conditional_active"):
                active.add(code)
            continue
        if mod.activation_kind in ("always_on", "required_module"):
            active.add(code)
            continue
        if _module_is_cost_active(mod.state):
            active.add(code)

    if quote_input:
        finish = quote_input.get("finish_setup") if isinstance(quote_input.get("finish_setup"), dict) else {}
        merged_finish = dict(finish)
        for key in (
            "mounting_system",
            "lighting_system_type",
            "illuminated",
            "return_depth_mm",
            "return_finish_type",
            "selected_psu_watts",
            "led_module_count",
        ):
            if key in quote_input and key not in merged_finish:
                merged_finish[key] = quote_input[key]

        illuminated = merged_finish.get("illuminated")
        is_lit = illuminated is True or str(illuminated).lower() in ("true", "1", "yes")
        lighting = merged_finish.get("lighting_system_type")
        if is_lit and lighting and str(lighting).strip().lower() not in ("", "none"):
            active.add("sistem_led")
        elif not is_lit:
            active.discard("sistem_led")

    return active


def _graph_structural_modules(graph: ProductAggregateCompositionGraph) -> set[str]:
    modules: set[str] = set()
    for node in graph.nodes:
        if node.node_role == "volum_aluminum":
            modules.add(CHILD_TEMPLATE_TO_MODULE.get(node.template_code, "modelare_cant"))
        elif node.node_role in ("mounting_panel", "premount_structure"):
            modules.add(CHILD_TEMPLATE_TO_MODULE.get(node.template_code, "structura_suport"))
    return modules


def _graph_blockers(graph: ProductAggregateCompositionGraph, pd: ProductDefinitionPreview) -> list[str]:
    blockers = list(graph.blockers)
    for conflict in pd.validation.missing_required_fields or []:
        if conflict == "volum_aluminum_module_template_code":
            blockers.append("UPSTREAM_TRUTH_MISSING:volum_aluminum_module_template_code")
    for conflict in aggregate_upstream_blockers(pd):
        if conflict not in blockers:
            blockers.append(conflict)
    return sorted(set(blockers))


def aggregate_upstream_blockers(pd: ProductDefinitionPreview) -> list[str]:
    del pd
    return []


def _projection_nodes(graph: ProductAggregateCompositionGraph) -> list[GraphCostProjectionNode]:
    return [
        GraphCostProjectionNode(
            node_id=node.node_id,
            template_code=node.template_code,
            node_role=node.node_role,
            module_code=node.module_code,
            module_role=node.module_role,
            parent_node_id=node.parent_node_id,
            activation_source=node.activation_source,
            inherited_inputs=dict(node.inherited_inputs or {}),
            locally_owned_inputs=dict(node.locally_owned_inputs or {}),
            blockers=list(node.blockers or []),
        )
        for node in graph.nodes
    ]


def _projection_edges(graph: ProductAggregateCompositionGraph) -> list[GraphCostProjectionEdge]:
    return [
        GraphCostProjectionEdge(
            edge_id=edge.edge_id,
            parent_node_id=edge.parent_node_id,
            child_node_id=edge.child_node_id,
            child_role=edge.child_role,
            relation_type=edge.relation_type,
            dependency_role=edge.dependency_role,
        )
        for edge in graph.edges
    ]


def build_graph_cost_projection(
    *,
    pd: ProductDefinitionPreview,
    aggregate: ProductAggregate,
    quote_input: dict[str, Any] | None = None,
) -> GraphCostProjection | None:
    graph = aggregate.composition_graph
    if graph is None or pd.source_context.source_payload_type != "workspace_payload":
        return None

    root_modules = _root_mini_modules_from_pd(pd, quote_input)
    structural_modules = _graph_structural_modules(graph)
    active = sorted(root_modules | structural_modules)

    return GraphCostProjection(
        projection_version=GRAPH_COST_PROJECTION_VERSION,
        structural_authority="composition_graph",
        template_code=pd.template_code,
        workspace_id=pd.source_context.workspace_id,
        composed_graph_version=graph.composed_graph_version,
        composition_mode=graph.composition_mode,
        root_template_code=graph.root_template_code,
        active_child_template_codes=list(graph.active_child_template_codes),
        active_mini_module_codes=active,
        root_mini_module_codes=sorted(root_modules),
        graph_structural_module_codes=sorted(structural_modules),
        nodes=_projection_nodes(graph),
        edges=_projection_edges(graph),
        blockers=_graph_blockers(graph, pd),
        warnings=[w.message for w in aggregate.warnings if w.code == "EXPLICIT_COMPOSITION_GRAPH_APPLIED"][:1],
        compatibility_note=(
            f"{TD_W3_GRAPH_COST_LEGACY_COMPAT}: legacy mounting_system/support_type cannot override graph structural scope."
        ),
    )


def resolve_cost_active_modules(
    *,
    pd: ProductDefinitionPreview,
    aggregate: ProductAggregate | None = None,
    quote_input: dict[str, Any] | None = None,
) -> tuple[set[str], GraphCostProjection | None]:
    """Resolve mini_module_codes for cost filtering on workspace graph path or legacy fallback."""
    if aggregate is None or aggregate.composition_graph is None:
        return set(), None
    if pd.source_context.source_payload_type != "workspace_payload":
        return set(), None

    projection = build_graph_cost_projection(pd=pd, aggregate=aggregate, quote_input=quote_input)
    if projection is None:
        return set(), None

    active = set(projection.active_mini_module_codes)
    structural_modules = set(projection.graph_structural_module_codes)

    payload = merge_scope_payload({}, quote_input)
    # Sold modules are the authority for component_subset — do not intersect with
    # full-template PD always_on set (that caused RETURN-only empty / FACE pollution).
    from services.active_scope_resolver_service import compile_active_scope

    scope_result = compile_active_scope(
        template_code=pd.template_code,
        payload=payload,
        quote_input=quote_input,
    )
    if not scope_result.use_legacy_full_product:
        if scope_result.errors:
            return set(), projection
        commercial = scope_result.commercial_set()
        # Keep graph structural modules that are also commercially sold (e.g. modelare_cant).
        active = commercial | (structural_modules & commercial)
        projection = projection.model_copy(
            update={
                "structural_authority": "offer_scope_subset",
                "active_mini_module_codes": sorted(active),
            }
        )

    return active, projection


def allowed_cost_template_codes(projection: GraphCostProjection) -> set[str]:
    allowed = {projection.root_template_code}
    allowed.update(projection.active_child_template_codes)
    return allowed
