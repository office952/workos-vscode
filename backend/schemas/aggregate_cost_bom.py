"""Read-only aggregate-expanded cost BOM preview schema (Step 7B)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.graph_cost_projection import GraphCostProjection

from schemas.product_definition import ProductDefinitionSourceContext

COST_BOM_PREVIEW_VERSION = "1.1.0"

BomStatus = Literal["ready", "partial", "blocked"]
InventoryUsageClassification = Literal[
    "USED_BY_ACTIVE_TEMPLATE",
    "USED_BY_OPTIONAL_MODULE",
    "FUTURE_RESERVED_BY_TEMPLATE",
    "LEGACY_REFERENCED_ONLY",
    "UNUSED_IN_TEMPLATE",
    "MISSING_FROM_INVENTORY",
    "MISSING_PRICE",
]
ProductionMode = Literal[
    "internal_production",
    "external_service_possible",
    "external_service_required",
    "hybrid_internal_external",
    "reseller_product_future",
    "future_reserved",
]
CostLineClassification = Literal[
    "INTERNAL_PRODUCTION",
    "INTERNAL_MATERIAL_EXTERNAL_SERVICE",
    "EXTERNAL_SERVICE",
    "RESELLER_PRODUCT",
    "HYBRID_INTERNAL_EXTERNAL",
    "FUTURE_EXTERNALIZATION_RULE",
]
SkippedReason = Literal[
    "geometry_gate",
    "future_reserved",
    "module_inactive",
    "non_priced_internal",
    "legacy_parent_only",
    "synthetic_component",
]
PricingAvailability = Literal["available", "missing", "variant_required", "not_applicable"]


class CostBomSourceContext(BaseModel):
    template_code: str
    workspace_id: str | None = None
    quote_id: str | None = None
    source_payload_type: str = "template_only"
    uses_parent_bom_as_structural_truth: bool = False
    legacy_parent_bom_note: str | None = None


class CostBomModuleRef(BaseModel):
    module_code: str
    module_name: str | None = None
    state: str
    included_in_cost_bom: bool = False
    exclusion_reason: str | None = None


class CostBomCostableComponent(BaseModel):
    component_id: str
    label_ro: str | None = None
    role: str | None = None
    mini_module_code: str | None = None
    provenance: str
    source_template_code: str | None = None


class CostBomCostableMaterial(BaseModel):
    material_code: str
    resolved_material_code: str | None = None
    label: str | None = None
    unit: str | None = None
    component_ref: str | None = None
    mini_module_code: str | None = None
    provenance: str
    source_template_code: str | None = None
    pricing_source_required: str = "inventory_materials"
    pricing_availability: PricingAvailability = "missing"
    unit_cost: float | None = None
    currency: str | None = None
    required_geometry_keys: list[str] = Field(default_factory=list)


class CostBomCostableOperation(BaseModel):
    operation_code: str
    label: str | None = None
    workcenter: str | None = None
    formula_id: str | None = None
    component_ref: str | None = None
    mini_module_code: str | None = None
    provenance: str
    source_template_code: str | None = None
    pricing_source_required: str = "workcenter_rates"
    pricing_availability: PricingAvailability = "missing"
    required_geometry_keys: list[str] = Field(default_factory=list)
    rate_basis: str | None = None


class CostBomSkippedItem(BaseModel):
    item_type: Literal["component", "material", "operation", "module"]
    item_key: str
    reason: SkippedReason
    detail: str


class CostBomPricingRequirement(BaseModel):
    requirement_code: str
    description: str
    module_codes: list[str] = Field(default_factory=list)
    geometry_keys: list[str] = Field(default_factory=list)
    registry_codes: list[str] = Field(default_factory=list)


class CostBomMissingPricing(BaseModel):
    item_type: Literal["material", "operation", "variant"]
    code: str
    reason: str
    module_code: str | None = None


class CostBomProvenanceEntry(BaseModel):
    key: str
    source: str
    detail: str


class InventoryUsageEntry(BaseModel):
    material_code: str
    resolved_material_code: str | None = None
    classification: InventoryUsageClassification
    module_code: str | None = None
    module_active: bool = False
    in_inventory: bool = False
    has_valid_price: bool = False
    provenance: str | None = None
    owner_step: int | None = None
    notes: str | None = None


class CostBomPricingBlocker(BaseModel):
    blocker_code: str
    item_type: Literal["material", "operation", "variant", "inventory", "external"]
    code: str
    reason: str
    module_code: str | None = None


class ExternalizationRequirement(BaseModel):
    code: str
    label: str
    module_code: str | None = None
    reason: str
    supplier_type: str | None = None
    selected_now: bool = False
    requires_external_price: bool = False
    blocks_pricing_if_selected_without_price: bool = False
    creates_external_task_now: bool = False
    owner_step: int = 9
    production_mode: ProductionMode = "external_service_possible"


class ResellerRequirement(BaseModel):
    product_code: str
    label: str
    purchase_price_required: bool = True
    supplier_required: bool = True
    margin_policy_required: bool = True
    internal_operations_required: bool = False
    status: Literal["future_reserved", "active"] = "future_reserved"
    owner_step: int = 8


class SubcontractableOperation(BaseModel):
    operation_code: str
    label: str | None = None
    module_code: str | None = None
    default_mode: ProductionMode = "internal_production"
    fallback_mode: ProductionMode | None = None
    required_machine_type: str | None = None
    external_partner_fallback: str | None = None
    owner_step: int = 9


class CostLineClassificationEntry(BaseModel):
    item_type: Literal["material", "operation", "component"]
    item_key: str
    classification: CostLineClassification
    production_mode: ProductionMode = "internal_production"
    module_code: str | None = None


class AggregateExpandedCostBom(BaseModel):
    """Read-only cost BOM — aggregate-expanded, not a priced quote."""

    preview_version: str = COST_BOM_PREVIEW_VERSION
    template_code: str
    source_context: CostBomSourceContext
    bom_status: BomStatus = "partial"
    active_modules: list[CostBomModuleRef] = Field(default_factory=list)
    inactive_modules: list[CostBomModuleRef] = Field(default_factory=list)
    costable_components: list[CostBomCostableComponent] = Field(default_factory=list)
    costable_materials: list[CostBomCostableMaterial] = Field(default_factory=list)
    costable_operations: list[CostBomCostableOperation] = Field(default_factory=list)
    skipped_items: list[CostBomSkippedItem] = Field(default_factory=list)
    pricing_requirements: list[CostBomPricingRequirement] = Field(default_factory=list)
    missing_pricing: list[CostBomMissingPricing] = Field(default_factory=list)
    missing_geometry: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    provenance: list[CostBomProvenanceEntry] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    production_mode: ProductionMode = "internal_production"
    inventory_usage: list[InventoryUsageEntry] = Field(default_factory=list)
    missing_inventory_materials: list[str] = Field(default_factory=list)
    unused_inventory_candidates: list[str] = Field(default_factory=list)
    legacy_inventory_references: list[str] = Field(default_factory=list)
    template_required_material_codes: list[str] = Field(default_factory=list)
    template_optional_material_codes: list[str] = Field(default_factory=list)
    pricing_blockers: list[CostBomPricingBlocker] = Field(default_factory=list)
    externalization_requirements: list[ExternalizationRequirement] = Field(default_factory=list)
    reseller_requirements: list[ResellerRequirement] = Field(default_factory=list)
    subcontractable_operations: list[SubcontractableOperation] = Field(default_factory=list)
    cost_line_classification: list[CostLineClassificationEntry] = Field(default_factory=list)
    graph_cost_projection: GraphCostProjection | None = None
