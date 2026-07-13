from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.product_system_template_readiness import (
    ProductSystemTemplateCapabilities,
    ProductSystemTemplateReadiness,
)
from schemas.shared_volumetric_component_contracts import SharedVolumetricComponentSummary


class ProductTemplateCompositionModule(BaseModel):
    role_key: str
    role_label: str
    module_template_code: str
    module_product_system_role: str | None = None
    relation_type: str | None = None
    is_required: bool = True
    sort_order: int = 0
    ui_hint: str | None = None
    status_label: str | None = None


class ProductTemplateAvailabilityItem(BaseModel):
    template_id: int
    template_code: str
    family_id: str | None = None
    family_name: str | None = None
    description: str | None = None
    db_active: bool
    quote_offerable: bool
    runtime_module: bool
    is_parent: bool
    has_modules: bool
    parent_codes: list[str] = Field(default_factory=list)
    module_codes: list[str] = Field(default_factory=list)
    status: str
    status_reason: str
    product_system_role: str
    display_group: str
    importance_rank: int
    owner_decision_required: bool = False
    readiness_reason: str
    ui_label: str
    ui_description: str
    parent_product_codes: list[str] = Field(default_factory=list)
    child_module_codes: list[str] = Field(default_factory=list)
    shared_with_product_codes: list[str] = Field(default_factory=list)
    composition_modules: list[ProductTemplateCompositionModule] = Field(default_factory=list)
    shared_component_contracts: list[SharedVolumetricComponentSummary] = Field(default_factory=list)
    capabilities: ProductSystemTemplateCapabilities | None = None
    readiness: ProductSystemTemplateReadiness | None = None


class ProductTemplateAvailabilityResponse(BaseModel):
    items: list[ProductTemplateAvailabilityItem] = Field(default_factory=list)
    total: int = 0
    offerable_count: int = 0
    runtime_module_count: int = 0
