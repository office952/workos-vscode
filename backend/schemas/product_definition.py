"""Read-only ProductDefinition preview schema (Step 6) — no pricing, no DB persistence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

PRODUCT_DEFINITION_PREVIEW_VERSION = "1.0.0"

ReadinessStatus = Literal["ready", "partial", "blocked"]
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
