"""Read-only ProductAggregate schema — modular product flow contract."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.mini_module_registry import MiniModuleRegistryRef, REGISTRY_VERSION as MINI_MODULE_REGISTRY_VERSION

ProvenanceValue = Literal[
    "parent",
    "dossier",
    "linked_module",
    "derived",
    "registry",
    "missing",
    "conflict",
]

SeverityValue = Literal["info", "warning", "error"]

AGGREGATE_VERSION = "1.0.0"

SOURCE_LAYERS: list[str] = [
    "intake_v6_form",
    "product_definition",
    "product_system_parent",
    "product_system_dossier",
    "product_system_linked_modules",
    "cost_engine",
    "quote",
    "order_snapshot",
    "task_preview",
    "execution_plan",
]


class ProductAggregateMaterial(BaseModel):
    material_code: str
    label: str | None = None
    unit: str | None = None
    component_ref: str | None = None
    formula_id: str | None = None
    provenance: ProvenanceValue = "missing"
    source_template_code: str | None = None
    mini_module_code: str | None = None
    status: str = "present"


class ProductAggregateOperation(BaseModel):
    operation_code: str
    label: str | None = None
    workcenter: str | None = None
    component_ref: str | None = None
    formula_id: str | None = None
    priced: bool = True
    provenance: ProvenanceValue = "missing"
    source_template_code: str | None = None
    mini_module_code: str | None = None
    status: str = "present"


class ProductAggregateComponent(BaseModel):
    component_id: str
    label_ro: str | None = None
    role: str | None = None
    mini_module_code: str | None = None
    provenance: ProvenanceValue = "missing"
    source_template_code: str | None = None
    materials: list[ProductAggregateMaterial] = Field(default_factory=list)
    operations: list[ProductAggregateOperation] = Field(default_factory=list)
    status: str = "present"


class ProductAggregateModule(BaseModel):
    module_code: str
    business_name_ro: str | None = None
    child_template_code: str
    child_template_id: int | None = None
    relation_type: str
    trigger_field: str | None = None
    trigger_value: Any = None
    pricing_mode: str | None = None
    execution_mode: str | None = None
    provenance: ProvenanceValue = "linked_module"
    active: bool = True
    notes: str | None = None


class ProductAggregateModules(BaseModel):
    required: list[ProductAggregateModule] = Field(default_factory=list)
    optional: list[ProductAggregateModule] = Field(default_factory=list)


class ProductAggregateFormField(BaseModel):
    canonical_key: str
    label_ro: str | None = None
    workspace_path: str | None = None
    required: bool = False
    provenance: ProvenanceValue = "dossier"
    status: str = "present"


class ProductAggregateFormContract(BaseModel):
    required_quote_input_keys: list[str] = Field(default_factory=list)
    optional_quote_input_keys: list[str] = Field(default_factory=list)
    form_fields: list[ProductAggregateFormField] = Field(default_factory=list)


class ProductAggregateCostContract(BaseModel):
    formula_ids: list[str] = Field(default_factory=list)
    registry_material_codes: list[str] = Field(default_factory=list)
    registry_workcenter_codes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ProductAggregateTaskRule(BaseModel):
    task_name: str
    task_type: str | None = None
    priced_operation: str | None = None
    sequence: int | None = None
    trigger_condition: str | None = None
    provenance: ProvenanceValue = "dossier"
    mini_module_code: str | None = None


class ProductAggregateTaskContract(BaseModel):
    task_rules: list[ProductAggregateTaskRule] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ProductAggregateConflict(BaseModel):
    code: str
    severity: SeverityValue
    message: str
    field: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ProductAggregateProvenanceSummary(BaseModel):
    parent: dict[str, int] = Field(default_factory=dict)
    dossier: dict[str, int] = Field(default_factory=dict)
    linked_modules: dict[str, int] = Field(default_factory=dict)
    aggregate_totals: dict[str, int] = Field(default_factory=dict)


class ProductAggregateMiniModuleRegistrySummary(BaseModel):
    """Read-only references to operational mini-module contracts (Step 4)."""

    registry_version: str = MINI_MODULE_REGISTRY_VERSION
    module_refs: list[MiniModuleRegistryRef] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ProductAggregate(BaseModel):
    aggregate_version: str = AGGREGATE_VERSION
    template_code: str
    template_id: int
    family_id: str | None = None
    family_name: str | None = None
    status: str = "unknown"
    business_name_ro: str | None = None
    source_layers: list[str] = Field(default_factory=lambda: list(SOURCE_LAYERS))
    modules: ProductAggregateModules = Field(default_factory=ProductAggregateModules)
    components: list[ProductAggregateComponent] = Field(default_factory=list)
    materials: list[ProductAggregateMaterial] = Field(default_factory=list)
    operations: list[ProductAggregateOperation] = Field(default_factory=list)
    form_contract: ProductAggregateFormContract = Field(default_factory=ProductAggregateFormContract)
    cost_contract: ProductAggregateCostContract = Field(default_factory=ProductAggregateCostContract)
    task_contract: ProductAggregateTaskContract = Field(default_factory=ProductAggregateTaskContract)
    conflicts: list[ProductAggregateConflict] = Field(default_factory=list)
    warnings: list[ProductAggregateConflict] = Field(default_factory=list)
    provenance_summary: ProductAggregateProvenanceSummary = Field(
        default_factory=ProductAggregateProvenanceSummary
    )
    mini_module_registry: ProductAggregateMiniModuleRegistrySummary | None = None
