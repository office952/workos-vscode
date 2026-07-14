"""Product Definition composed-graph contract V1 — frozen mounting resolution, Cases A–D."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from schemas.product_definition import (
    COMPOSITION_GRAPH_VERSION,
    CompositionEdge,
    CompositionGraphHeader,
    CompositionNode,
    CompositionProvenanceEntry,
    ProductDefinitionComposition,
)
from services.mounting_solution_service import (
    ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES,
    METAL_PREMOUNT_TEMPLATE_CODE,
    build_linked_module_input_from_solution,
    hydrate_mounting_solution_from_legacy,
    legacy_mounting_system_from_solution,
    normalize_solution_configuration,
    read_mounting_solution,
    resolve_effective_mounting_solution,
)
from services.mounting_scope_service import is_mounting_preparation_active, normalize_mounting_scope

ROOT_TEMPLATE_VOLUMETRIC = "TPL-VOLUMETRIC-LETTERS_v2"
VOLUM_ALUMINUM_TEMPLATE_CODE = "TPL-VOLUM-ALUMINIU_v1"
STRUCTURA_SUPORT_MODULE_CODE = "structura_suport"
PRODUCT_DEFINITION_COMPOSITION_PILOT_KEY = "product_definition_composition"

CompositionMode = Literal["none", "single_child", "mounting_chain", "standalone_root", "template_only"]
SolutionStatus = Literal["confirmed", "blocked"]
CompatibilityStatus = Literal["compatible", "blocked", "partial"]
RelationType = Literal[
    "required_module",
    "optional_addon",
    "visual_mounting_support",
    "structural_dependency",
]
NodeRole = Literal["root_product", "mounting_panel", "premount_structure", "volum_aluminum", "other"]
ActivationSource = Literal[
    "canonical_mounting_solution",
    "legacy_mounting_system",
    "composition_pilot",
    "template_registry",
    "none",
]

# Stable blocker reason codes
BLOCKER_UNKNOWN_CHILD_TEMPLATE = "UNKNOWN_CHILD_TEMPLATE"
BLOCKER_INCOMPATIBLE_CHILD_RELATION = "INCOMPATIBLE_CHILD_RELATION"
BLOCKER_MISSING_ACM_DIMENSIONS = "MISSING_ACM_DIMENSIONS"
BLOCKER_MISSING_PREMOUNT_INPUTS = "MISSING_PREMOUNT_INPUTS"
BLOCKER_MOUNTING_SCOPE_INACTIVE = "MOUNTING_SCOPE_INACTIVE"
BLOCKER_REQUIRED_VOLUM_AL_MISSING = "REQUIRED_VOLUM_AL_MISSING"
BLOCKER_AMBIGUOUS_STRUCTURA_SUPORT = "AMBIGUOUS_STRUCTURA_SUPORT"
BLOCKER_CHILD_OUTPUT_INCOMPLETE = "CHILD_OUTPUT_INCOMPLETE"
BLOCKER_DUPLICATE_ROLE_ASSIGNMENT = "DUPLICATE_ROLE_ASSIGNMENT"
BLOCKER_INCOMPATIBLE_MOUNTING_CHAIN = "INCOMPATIBLE_MOUNTING_CHAIN"
BLOCKER_MISSING_STRUCTURAL_SUPPORT_INPUTS = "MISSING_STRUCTURAL_SUPPORT_INPUTS"
BLOCKER_MISSING_ACM_TO_PREMOUNT_EDGE = "MISSING_ACM_TO_PREMOUNT_EDGE"
BLOCKER_AMBIGUOUS_SUPPORT_HIERARCHY = "AMBIGUOUS_SUPPORT_HIERARCHY"

# Stable warning reason codes
WARN_LEGACY_MOUNTING_SYSTEM_FALLBACK = "LEGACY_MOUNTING_SYSTEM_FALLBACK"
WARN_OPERATOR_OVERRIDE_USED = "OPERATOR_OVERRIDE_USED"
WARN_OPTIONAL_INPUT_MISSING = "OPTIONAL_INPUT_MISSING"
WARN_ALTERNATIVE_SOLUTION_AVAILABLE = "ALTERNATIVE_SOLUTION_AVAILABLE"
WARN_PREMOUNT_FORM_CONTRACT_INCOMPLETE = "PREMOUNT_FORM_CONTRACT_INCOMPLETE"
WARN_DEAD_LINK_TRIGGER_METADATA = "DEAD_LINK_TRIGGER_METADATA"
WARN_TRIGGER_FIELD_MISMATCH = "TRIGGER_FIELD_MISMATCH"
WARN_INTAKE_COMPOSITION_MODE_LIMITED = "INTAKE_COMPOSITION_MODE_LIMITED"

CHILD_ROLE_BY_TEMPLATE: dict[str, NodeRole] = {
    ACM_BOXED_MOUNTING_TEMPLATE_CODE: "mounting_panel",
    METAL_PREMOUNT_TEMPLATE_CODE: "premount_structure",
    VOLUM_ALUMINUM_TEMPLATE_CODE: "volum_aluminum",
}

RELATION_BY_CHILD_ROLE: dict[str, RelationType] = {
    "mounting_panel": "visual_mounting_support",
    "premount_structure": "structural_dependency",
    "volum_aluminum": "required_module",
}


@dataclass(frozen=True)
class FrozenMountingResolution:
    """Single frozen mounting resolution per Product Definition build."""

    mounting_scope: str
    prep_active: bool
    resolved_solution: dict[str, Any] | None
    canonical_solution: dict[str, Any] | None
    legacy_fallback_used: bool
    activation_source: ActivationSource
    selected_solution_id: str | None
    pilot_request: dict[str, Any] | None


def _read_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _coerce_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _node_id(template_code: str, node_role: str) -> str:
    return f"node:{node_role}:{template_code}"


def _edge_id(parent_template: str, child_template: str, relation_type: str) -> str:
    return f"edge:{parent_template}->{child_template}:{relation_type}"


def _read_pilot_request(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, Mapping):
        return None
    pilot = payload.get(PRODUCT_DEFINITION_COMPOSITION_PILOT_KEY)
    if not isinstance(pilot, dict):
        finish = payload.get("finish_setup")
        if isinstance(finish, dict):
            pilot = finish.get(PRODUCT_DEFINITION_COMPOSITION_PILOT_KEY)
    return dict(pilot) if isinstance(pilot, dict) else None


def freeze_mounting_resolution(
    *,
    finish: Mapping[str, Any] | None,
    payload: Mapping[str, Any] | None = None,
) -> FrozenMountingResolution:
    """Resolve mounting truth once — canonical first, legacy fallback second."""
    setup = finish if isinstance(finish, Mapping) else {}
    scope = normalize_mounting_scope(setup.get("mounting_scope"), setup=setup)
    prep_active = is_mounting_preparation_active(setup)
    canonical = read_mounting_solution(setup)
    legacy_fallback_used = False
    activation_source: ActivationSource = "none"
    resolved: dict[str, Any] | None = None

    if canonical:
        template_code = _read_string(canonical.get("template_code"))
        if template_code:
            resolved = {
                "template_code": template_code,
                "configuration": normalize_solution_configuration(
                    template_code,
                    canonical.get("configuration"),
                ),
            }
            activation_source = "canonical_mounting_solution"
    else:
        hydrated = hydrate_mounting_solution_from_legacy(setup)
        if hydrated:
            template_code = _read_string(hydrated.get("template_code"))
            if template_code:
                resolved = {
                    "template_code": template_code,
                    "configuration": normalize_solution_configuration(
                        template_code,
                        hydrated.get("configuration"),
                    ),
                }
                legacy_fallback_used = True
                activation_source = "legacy_mounting_system"

    selected_id = _read_string(resolved.get("template_code")) if resolved else None
    pilot = _read_pilot_request(payload)

    return FrozenMountingResolution(
        mounting_scope=scope,
        prep_active=prep_active,
        resolved_solution=resolved,
        canonical_solution=canonical,
        legacy_fallback_used=legacy_fallback_used,
        activation_source=activation_source,
        selected_solution_id=selected_id,
        pilot_request=pilot,
    )


def _volum_aluminum_code(finish: Mapping[str, Any]) -> str | None:
    return _read_string(finish.get("volum_aluminum_module_template_code"))


def _quote_input_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    quote_geometry = _coerce_dict(payload.get("quote_geometry"))
    client = _coerce_dict(payload.get("client"))
    merged: dict[str, Any] = {}
    for key in ("width_mm", "height_mm", "depth_mm", "letter_count", "letter_perimeter_m", "letter_face_area_m2"):
        if key in quote_geometry and quote_geometry[key] is not None:
            merged[key] = quote_geometry[key]
        elif key in client and client[key] is not None:
            merged[key] = client[key]
    return merged


def _build_node(
    *,
    template_code: str,
    module_code: str,
    module_role: str,
    node_role: NodeRole,
    parent_node_id: str | None,
    activation_source: ActivationSource,
    included: bool,
    inherited_inputs: dict[str, Any],
    local_inputs: dict[str, Any],
    unresolved_inputs: list[str],
    blockers: list[str],
    warnings: list[str],
) -> CompositionNode:
    compat: CompatibilityStatus = "blocked" if blockers else ("partial" if unresolved_inputs else "compatible")
    return CompositionNode(
        node_id=_node_id(template_code, node_role),
        template_code=template_code,
        module_code=module_code,
        module_role=module_role,
        node_role=node_role,
        parent_node_id=parent_node_id,
        activation_source=activation_source,
        included_in_graph=included,
        inherited_inputs=inherited_inputs,
        locally_owned_inputs=local_inputs,
        unresolved_inputs=unresolved_inputs,
        compatibility_status=compat,
        blockers=blockers,
        warnings=warnings,
        provenance=[
            CompositionProvenanceEntry(
                key="activation_source",
                source="product_definition_composition_contract",
                detail=activation_source,
            )
        ],
    )


def _build_edge(
    *,
    parent_template_code: str,
    parent_node_id: str,
    child_template_code: str,
    child_node_id: str,
    module_code: str,
    module_role: str,
    child_role: NodeRole,
    relation_type: RelationType,
    dependency_role: str | None,
    activation_source: ActivationSource,
    included: bool,
    inherited_inputs: dict[str, Any],
    local_inputs: dict[str, Any],
    unresolved_inputs: list[str],
    blockers: list[str],
    warnings: list[str],
) -> CompositionEdge:
    compat: CompatibilityStatus = "blocked" if blockers else ("partial" if unresolved_inputs else "compatible")
    return CompositionEdge(
        edge_id=_edge_id(parent_template_code, child_template_code, relation_type),
        parent_template_code=parent_template_code,
        parent_node_id=parent_node_id,
        child_template_code=child_template_code,
        child_node_id=child_node_id,
        module_code=module_code,
        module_role=module_role,
        child_role=child_role,
        relation_type=relation_type,
        dependency_role=dependency_role,
        included_in_graph=included,
        activation_source=activation_source,
        inherited_inputs=inherited_inputs,
        locally_owned_inputs=local_inputs,
        unresolved_inputs=unresolved_inputs,
        compatibility_status=compat,
        blockers=blockers,
        warnings=warnings,
        provenance=[
            CompositionProvenanceEntry(
                key="relation_type",
                source="product_definition_composition_contract",
                detail=relation_type,
            )
        ],
    )


def _acm_dimension_blockers(config: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    for key in ("panel_width_mm", "panel_height_mm"):
        try:
            if float(config.get(key) or 0) <= 0:
                blockers.append(BLOCKER_MISSING_ACM_DIMENSIONS)
                break
        except (TypeError, ValueError):
            blockers.append(BLOCKER_MISSING_ACM_DIMENSIONS)
            break
    return blockers


def _premount_input_blockers(config: Mapping[str, Any], quote_input: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    unresolved: list[str] = []
    if not config.get("mounting_bar_profile"):
        unresolved.append("mounting_bar_profile")
    if not config.get("bar_count"):
        unresolved.append("bar_count")
    if quote_input.get("width_mm") is None:
        unresolved.append("width_mm")
    if unresolved:
        blockers.append(BLOCKER_MISSING_PREMOUNT_INPUTS)
    return blockers, unresolved


def build_product_definition_composition(
    *,
    root_template_code: str,
    payload: Mapping[str, Any] | None,
    source_payload_type: str,
    standalone_root: bool = False,
) -> ProductDefinitionComposition:
    """Build composed graph from frozen mounting resolution — Cases A–D."""
    payload_map = dict(payload) if isinstance(payload, Mapping) else {}
    finish = _coerce_dict(payload_map.get("finish_setup"))
    frozen = freeze_mounting_resolution(finish=finish, payload=payload_map)
    quote_input = _quote_input_from_payload(payload_map)

    blockers: list[str] = []
    warnings: list[str] = []
    alternatives: list[str] = []
    nodes: list[CompositionNode] = []
    edges: list[CompositionEdge] = []
    active_module_codes: list[str] = []

    if standalone_root:
        root_node = _build_node(
            template_code=root_template_code,
            module_code=STRUCTURA_SUPORT_MODULE_CODE,
            module_role="mounting_support",
            node_role="root_product",
            parent_node_id=None,
            activation_source="template_registry",
            included=True,
            inherited_inputs={},
            local_inputs={},
            unresolved_inputs=[],
            blockers=[],
            warnings=[],
        )
        return ProductDefinitionComposition(
            composed_graph_version=COMPOSITION_GRAPH_VERSION,
            composition_mode="standalone_root",
            root_template_code=root_template_code,
            selected_solution_id=root_template_code,
            solution_status="confirmed",
            solution_reason_codes=[],
            compatibility_status="compatible",
            blockers=[],
            warnings=[],
            alternatives=[],
            provenance=[
                CompositionProvenanceEntry(
                    key="standalone_root",
                    source="product_definition_composition_contract",
                    detail="boxed_acm_mounting_standalone_root_v1",
                )
            ],
            active_module_codes=[STRUCTURA_SUPORT_MODULE_CODE],
            nodes=[root_node],
            edges=[],
            frozen_mounting_solution=None,
        )

    if source_payload_type != "workspace_payload":
        composition_mode: CompositionMode = "template_only"
        solution_status: SolutionStatus = "confirmed"
    else:
        composition_mode = "none"
        solution_status = "confirmed"

    root_node_id = _node_id(root_template_code, "root_product")
    root_node = _build_node(
        template_code=root_template_code,
        module_code="root",
        module_role="root_product",
        node_role="root_product",
        parent_node_id=None,
        activation_source="template_registry",
        included=True,
        inherited_inputs={},
        local_inputs=quote_input,
        unresolved_inputs=[],
        blockers=[],
        warnings=[],
    )
    nodes.append(root_node)

    volum_code = _volum_aluminum_code(finish)
    volum_active = bool(volum_code)
    if volum_active and volum_code:
        volum_node = _build_node(
            template_code=volum_code,
            module_code="volum_aluminum",
            module_role="volum_aluminum",
            node_role="volum_aluminum",
            parent_node_id=root_node_id,
            activation_source="template_registry",
            included=True,
            inherited_inputs={k: quote_input[k] for k in quote_input if k in ("width_mm", "height_mm", "depth_mm")},
            local_inputs={"volum_aluminum_module_template_code": volum_code},
            unresolved_inputs=[],
            blockers=[],
            warnings=[],
        )
        nodes.append(volum_node)
        edges.append(
            _build_edge(
                parent_template_code=root_template_code,
                parent_node_id=root_node_id,
                child_template_code=volum_code,
                child_node_id=volum_node.node_id,
                module_code="volum_aluminum",
                module_role="volum_aluminum",
                child_role="volum_aluminum",
                relation_type="required_module",
                dependency_role=None,
                activation_source="template_registry",
                included=True,
                inherited_inputs=volum_node.inherited_inputs,
                local_inputs=volum_node.locally_owned_inputs,
                unresolved_inputs=[],
                blockers=[],
                warnings=[],
            )
        )
        active_module_codes.append("volum_aluminum")

    solution = frozen.resolved_solution
    pilot = frozen.pilot_request or {}
    pilot_mode = _read_string(pilot.get("composition_mode"))
    supporting_codes = [
        _read_string(code)
        for code in (pilot.get("supporting_template_codes") or [])
        if _read_string(code)
    ]

    if frozen.legacy_fallback_used:
        warnings.append(WARN_LEGACY_MOUNTING_SYSTEM_FALLBACK)

    if solution and not frozen.prep_active:
        blockers.append(BLOCKER_MOUNTING_SCOPE_INACTIVE)

    primary_template = _read_string(solution.get("template_code")) if solution else None
    if primary_template and primary_template not in ALLOWED_MOUNTING_SOLUTION_TEMPLATE_CODES:
        blockers.append(BLOCKER_UNKNOWN_CHILD_TEMPLATE)

    # Generic structura active without child identity — handled after graph build when legacy signal has no child node.

    chain_requested = pilot_mode == "mounting_chain"
    premount_in_supporting = METAL_PREMOUNT_TEMPLATE_CODE in supporting_codes
    acm_primary = primary_template == ACM_BOXED_MOUNTING_TEMPLATE_CODE
    premount_primary = primary_template == METAL_PREMOUNT_TEMPLATE_CODE

    if chain_requested and not (acm_primary and premount_in_supporting):
        warnings.append(WARN_INTAKE_COMPOSITION_MODE_LIMITED)

    if chain_requested and acm_primary and not premount_in_supporting:
        blockers.append(BLOCKER_MISSING_ACM_TO_PREMOUNT_EDGE)

    if chain_requested and premount_primary and ACM_BOXED_MOUNTING_TEMPLATE_CODE in supporting_codes:
        blockers.append(BLOCKER_AMBIGUOUS_SUPPORT_HIERARCHY)

    mounting_system = _read_string(finish.get("mounting_system"))
    legacy_support_signal = mounting_system in {"steel_bars", "aluminum_bars", "acm_panel"}
    duplicate_roles: dict[str, str] = {}
    child_specs: list[tuple[str, ActivationSource, dict[str, Any]]] = []

    if solution and frozen.prep_active and primary_template:
        config = _coerce_dict(solution.get("configuration"))
        module_input = build_linked_module_input_from_solution(
            solution=solution,
            quote_input=quote_input,
            defaults=None,
        )
        child_role = CHILD_ROLE_BY_TEMPLATE.get(primary_template, "other")
        if child_role in duplicate_roles:
            blockers.append(BLOCKER_DUPLICATE_ROLE_ASSIGNMENT)
        else:
            duplicate_roles[child_role] = primary_template
        child_specs.append((primary_template, frozen.activation_source, module_input))

        if chain_requested and acm_primary and premount_in_supporting:
            premount_config = normalize_solution_configuration(
                METAL_PREMOUNT_TEMPLATE_CODE,
                pilot.get("premount_configuration"),
            )
            premount_solution = {
                "template_code": METAL_PREMOUNT_TEMPLATE_CODE,
                "configuration": premount_config,
            }
            premount_input = build_linked_module_input_from_solution(
                solution=premount_solution,
                quote_input=quote_input,
                defaults=None,
            )
            if "premount_structure" in duplicate_roles:
                blockers.append(BLOCKER_DUPLICATE_ROLE_ASSIGNMENT)
            else:
                duplicate_roles["premount_structure"] = METAL_PREMOUNT_TEMPLATE_CODE
            child_specs.append(
                (METAL_PREMOUNT_TEMPLATE_CODE, "composition_pilot", premount_input),
            )

    # Pilot-only duplicate role injection for tests
    if pilot.get("_force_duplicate_role"):
        blockers.append(BLOCKER_DUPLICATE_ROLE_ASSIGNMENT)

    parent_for_child = root_template_code
    parent_node_for_child = root_node_id
    prior_mounting_panel_id: str | None = None

    for idx, (child_template, activation_source, module_input) in enumerate(child_specs):
        child_role = CHILD_ROLE_BY_TEMPLATE.get(child_template, "other")
        relation = RELATION_BY_CHILD_ROLE.get(child_role, "optional_addon")
        dependency_role = "supports_acm_assembly" if (
            child_role == "premount_structure" and prior_mounting_panel_id is not None
        ) else None

        node_blockers: list[str] = []
        node_warnings: list[str] = []
        unresolved: list[str] = []

        if child_template == ACM_BOXED_MOUNTING_TEMPLATE_CODE:
            node_blockers.extend(_acm_dimension_blockers(module_input))
        if child_template == METAL_PREMOUNT_TEMPLATE_CODE:
            premount_blockers, unresolved = _premount_input_blockers(module_input, quote_input)
            node_blockers.extend(premount_blockers)
            if pilot_mode == "mounting_chain":
                node_warnings.append(WARN_PREMOUNT_FORM_CONTRACT_INCOMPLETE)

        edge_parent_template = parent_for_child
        edge_parent_node = parent_node_for_child
        if child_role == "premount_structure" and prior_mounting_panel_id:
            edge_parent_template = ACM_BOXED_MOUNTING_TEMPLATE_CODE
            edge_parent_node = prior_mounting_panel_id

        child_node = _build_node(
            template_code=child_template,
            module_code=STRUCTURA_SUPORT_MODULE_CODE,
            module_role="mounting_support",
            node_role=child_role,
            parent_node_id=edge_parent_node,
            activation_source=activation_source,
            included=True,
            inherited_inputs={k: v for k, v in module_input.items() if k in quote_input},
            local_inputs={k: v for k, v in module_input.items() if k not in quote_input},
            unresolved_inputs=unresolved,
            blockers=node_blockers,
            warnings=node_warnings,
        )
        nodes.append(child_node)

        edge_blockers = list(node_blockers)
        if chain_requested and child_role == "premount_structure" and not prior_mounting_panel_id:
            edge_blockers.append(BLOCKER_MISSING_ACM_TO_PREMOUNT_EDGE)

        edges.append(
            _build_edge(
                parent_template_code=edge_parent_template,
                parent_node_id=edge_parent_node,
                child_template_code=child_template,
                child_node_id=child_node.node_id,
                module_code=STRUCTURA_SUPORT_MODULE_CODE,
                module_role="mounting_support",
                child_role=child_role,
                relation_type=relation,
                dependency_role=dependency_role,
                activation_source=activation_source,
                included=True,
                inherited_inputs=child_node.inherited_inputs,
                local_inputs=child_node.locally_owned_inputs,
                unresolved_inputs=unresolved,
                blockers=edge_blockers,
                warnings=node_warnings,
            )
        )
        active_module_codes.append(STRUCTURA_SUPORT_MODULE_CODE)

        if child_role == "mounting_panel":
            prior_mounting_panel_id = child_node.node_id
            parent_for_child = child_template
            parent_node_for_child = child_node.node_id

    if legacy_support_signal and not any(
        n.included_in_graph and n.node_role in ("mounting_panel", "premount_structure") for n in nodes
    ):
        blockers.append(BLOCKER_AMBIGUOUS_STRUCTURA_SUPORT)

    if chain_requested and acm_primary and premount_in_supporting:
        has_acm_premount_edge = any(
            e.child_template_code == METAL_PREMOUNT_TEMPLATE_CODE
            and e.parent_template_code == ACM_BOXED_MOUNTING_TEMPLATE_CODE
            and e.relation_type == "structural_dependency"
            for e in edges
        )
        if not has_acm_premount_edge and BLOCKER_MISSING_ACM_TO_PREMOUNT_EDGE not in blockers:
            blockers.append(BLOCKER_MISSING_ACM_TO_PREMOUNT_EDGE)
        composition_mode = "mounting_chain"
    elif child_specs:
        composition_mode = "single_child"
    elif volum_active:
        composition_mode = "single_child"
    elif source_payload_type != "workspace_payload":
        composition_mode = "template_only"
    else:
        composition_mode = "none"

    all_blockers = sorted(set(blockers + [b for n in nodes for b in n.blockers] + [b for e in edges for b in e.blockers]))
    all_warnings = sorted(set(warnings + [w for n in nodes for w in n.warnings] + [w for e in edges for w in e.warnings]))

    if BLOCKER_DUPLICATE_ROLE_ASSIGNMENT in all_blockers:
        solution_status = "blocked"
    elif all_blockers:
        solution_status = "blocked"
    else:
        solution_status = "confirmed"

    compat: CompatibilityStatus = "blocked" if all_blockers else ("partial" if all_warnings else "compatible")

    reason_codes: list[str] = []
    if primary_template:
        reason_codes.append(f"primary_child:{primary_template}")
    if chain_requested:
        reason_codes.append("composition_pilot:mounting_chain")
    if frozen.legacy_fallback_used:
        reason_codes.append("legacy_mounting_system_hydrated")

    frozen_solution_export = None
    if solution:
        frozen_solution_export = {
            "template_code": solution.get("template_code"),
            "configuration": dict(solution.get("configuration") or {}),
            "activation_source": frozen.activation_source,
            "legacy_fallback_used": frozen.legacy_fallback_used,
        }

    return ProductDefinitionComposition(
        composed_graph_version=COMPOSITION_GRAPH_VERSION,
        composition_mode=composition_mode,
        root_template_code=root_template_code,
        selected_solution_id=frozen.selected_solution_id,
        solution_status=solution_status,
        solution_reason_codes=reason_codes,
        compatibility_status=compat,
        blockers=all_blockers,
        warnings=all_warnings,
        alternatives=alternatives,
        provenance=[
            CompositionProvenanceEntry(
                key="frozen_mounting_resolution",
                source="mounting_solution_service",
                detail=f"prep_active={frozen.prep_active} scope={frozen.mounting_scope}",
            ),
            CompositionProvenanceEntry(
                key="mounting_solution",
                source=frozen.activation_source,
                detail=_read_string(primary_template) or "none",
            ),
        ],
        active_module_codes=sorted(set(active_module_codes)),
        nodes=nodes,
        edges=sorted(edges, key=lambda e: (e.parent_template_code, e.child_template_code, e.relation_type)),
        frozen_mounting_solution=frozen_solution_export,
    )


def structura_suport_active_from_composition(composition: ProductDefinitionComposition | None) -> bool:
    if composition is None:
        return False
    return any(
        n.included_in_graph
        and n.node_role in ("mounting_panel", "premount_structure")
        for n in composition.nodes
    )


def metal_support_required_from_composition(
    composition: ProductDefinitionComposition | None,
    *,
    finish: Mapping[str, Any] | None,
) -> bool | None:
    if composition and structura_suport_active_from_composition(composition):
        return True
    if isinstance(finish, Mapping) and is_mounting_preparation_active(finish):
        solution = resolve_effective_mounting_solution(finish)
        if solution and legacy_mounting_system_from_solution(solution):
            return True
    return None
