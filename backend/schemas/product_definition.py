"""Read-only ProductDefinition preview schema (Step 6) — no pricing, no DB persistence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

PRODUCT_DEFINITION_PREVIEW_VERSION = "1.0.0"
COMPOSITION_GRAPH_VERSION = "1.0.0"

ReadinessStatus = Literal["ready", "partial", "blocked"]
CompositionMode = Literal["none", "single_child", "mounting_chain", "standalone_root", "template_only"]
SolutionStatus = Literal["confirmed", "blocked"]
CompositionCompatibilityStatus = Literal["compatible", "blocked", "partial"]
CompositionRelationType = Literal[
    "required_module",
    "optional_addon",
    "visual_mounting_support",
    "structural_dependency",
]
CompositionNodeRole = Literal[
    "root_product",
    "mounting_panel",
    "premount_structure",
    "volum_aluminum",
    "other",
]
CompositionActivationSource = Literal[
    "canonical_mounting_solution",
    "legacy_mounting_system",
    "composition_pilot",
    "template_registry",
    "none",
]
SourcePayloadType = Literal["template_only", "workspace_payload"]
ModulePreviewState = Literal[
    "always_on",
    "active",
    "inactive",
    "pending",
    "conditional_active",
    "future_reserved",
]


class ProductDefinitionSourceContext(BaseModel):
    template_code: str
    workspace_id: str | None = None
    quote_id: str | None = None
    source_payload_type: SourcePayloadType = "template_only"


class ProductDefinitionModuleRef(BaseModel):
    module_code: str
    module_name: str
    activation_kind: str
    state: ModulePreviewState
    activation_reason: str | None = None
    missing_fields: list[str] = Field(default_factory=list)


class ProductDefinitionComponentRole(BaseModel):
    component_id: str
    label_ro: str | None = None
    role: str | None = None
    mini_module_code: str | None = None
    module_active: bool = True
    provenance: str = "missing"
    source_template_code: str | None = None


class ProductDefinitionMaterialRole(BaseModel):
    material_code: str
    label: str | None = None
    unit: str | None = None
    component_ref: str | None = None
    mini_module_code: str | None = None
    module_active: bool = True
    provenance: str = "missing"


class ProductDefinitionOperationRole(BaseModel):
    operation_code: str
    label: str | None = None
    workcenter: str | None = None
    component_ref: str | None = None
    mini_module_code: str | None = None
    module_active: bool = True
    is_geometry_gate: bool = False
    is_priced: bool = True
    provenance: str = "missing"


class ProductDefinitionValidation(BaseModel):
    readiness_status: ReadinessStatus = "partial"
    missing_required_fields: list[str] = Field(default_factory=list)
    invalid_combinations: list[str] = Field(default_factory=list)
    unresolved_warnings: list[str] = Field(default_factory=list)


class ProductDefinitionProvenanceEntry(BaseModel):
    key: str
    source: str
    detail: str


class CompositionProvenanceEntry(BaseModel):
    key: str
    source: str
    detail: str


class CompositionNode(BaseModel):
    node_id: str
    template_code: str
    module_code: str
    module_role: str
    node_role: CompositionNodeRole
    parent_node_id: str | None = None
    activation_source: CompositionActivationSource
    included_in_graph: bool = True
    inherited_inputs: dict[str, Any] = Field(default_factory=dict)
    locally_owned_inputs: dict[str, Any] = Field(default_factory=dict)
    unresolved_inputs: list[str] = Field(default_factory=list)
    compatibility_status: CompositionCompatibilityStatus = "compatible"
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    provenance: list[CompositionProvenanceEntry] = Field(default_factory=list)


class CompositionEdge(BaseModel):
    edge_id: str
    parent_template_code: str
    parent_node_id: str
    child_template_code: str
    child_node_id: str
    module_code: str
    module_role: str
    child_role: CompositionNodeRole
    relation_type: CompositionRelationType
    dependency_role: str | None = None
    included_in_graph: bool = True
    activation_source: CompositionActivationSource
    inherited_inputs: dict[str, Any] = Field(default_factory=dict)
    locally_owned_inputs: dict[str, Any] = Field(default_factory=dict)
    unresolved_inputs: list[str] = Field(default_factory=list)
    compatibility_status: CompositionCompatibilityStatus = "compatible"
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    provenance: list[CompositionProvenanceEntry] = Field(default_factory=list)


class CompositionGraphHeader(BaseModel):
    composed_graph_version: str = COMPOSITION_GRAPH_VERSION
    composition_mode: CompositionMode = "none"
    root_template_code: str
    selected_solution_id: str | None = None
    solution_status: SolutionStatus = "confirmed"
    solution_reason_codes: list[str] = Field(default_factory=list)
    compatibility_status: CompositionCompatibilityStatus = "compatible"
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    provenance: list[CompositionProvenanceEntry] = Field(default_factory=list)
    active_module_codes: list[str] = Field(default_factory=list)


class ProductDefinitionComposition(CompositionGraphHeader):
    """Frozen composed-graph contract — authoritative mounting child identity."""

    nodes: list[CompositionNode] = Field(default_factory=list)
    edges: list[CompositionEdge] = Field(default_factory=list)
    frozen_mounting_solution: dict[str, Any] | None = None


class ProductDefinitionResourceHints(BaseModel):
    """Future operational routing — not active execution in Step 6."""

    scope: Literal["future_resource_hint"] = "future_resource_hint"
    pricing_source: list[str] = Field(default_factory=list)
    inventory_source: list[str] = Field(default_factory=list)
    required_machine_type: list[str] = Field(default_factory=list)
    required_employee_roles: list[str] = Field(default_factory=list)
    employee_availability_dependency: list[str] = Field(default_factory=list)
    attendance_capacity_dependency: list[str] = Field(default_factory=list)
    subcontractable: list[str] = Field(default_factory=list)
    external_partner_fallback: list[str] = Field(default_factory=list)
    machine_failure_fallback: list[str] = Field(default_factory=list)
    execution_routing_notes: list[str] = Field(default_factory=list)


class ProductDefinitionPreview(BaseModel):
    """Canonical read-only ProductDefinition preview — Step 6."""

    preview_version: str = PRODUCT_DEFINITION_PREVIEW_VERSION
    template_code: str
    business_name_ro: str | None = None
    source_context: ProductDefinitionSourceContext
    selected_modules: list[ProductDefinitionModuleRef] = Field(default_factory=list)
    optional_modules: list[ProductDefinitionModuleRef] = Field(default_factory=list)
    inactive_modules: list[ProductDefinitionModuleRef] = Field(default_factory=list)
    components: list[ProductDefinitionComponentRole] = Field(default_factory=list)
    material_roles: list[ProductDefinitionMaterialRole] = Field(default_factory=list)
    operation_roles: list[ProductDefinitionOperationRole] = Field(default_factory=list)
    linked_template_runtime_segments: dict[str, Any] | None = None
    canonical_values: dict[str, Any] = Field(default_factory=dict)
    geometry_inputs: dict[str, Any] = Field(default_factory=dict)
    validation: ProductDefinitionValidation = Field(default_factory=ProductDefinitionValidation)
    provenance: list[ProductDefinitionProvenanceEntry] = Field(default_factory=list)
    resource_hints: ProductDefinitionResourceHints | None = None
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    composition: ProductDefinitionComposition | None = None
    # Typed Product Truth job provenance (mirrors provenance entry product_truth_job_revision).
    product_truth_job_revision: int | None = None
    product_truth_content_hash: str | None = None
    product_truth_status: str | None = None
