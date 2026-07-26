from __future__ import annotations

from typing import Any

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


class SvgBindableComponent(BaseModel):
    """Product System authority: Component Template may receive SVG geometry."""

    component_template_code: str
    process_component_code: str | None = None
    owner_label: str
    accepted_geometry_roles: list[str] = Field(default_factory=list)
    accepted_face_treatment_codes: list[str] = Field(default_factory=list)
    selection_mode: str
    cardinality: str
    required: bool = False
    available: bool = True
    active: bool = False
    active_by_default: bool = False
    technical_role: str | None = None
    guards: list[str] = Field(default_factory=list)
    product_definition_targets: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    svg_binding: dict[str, Any] = Field(default_factory=dict)


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
    svg_bindable_components: list[SvgBindableComponent] = Field(default_factory=list)
    shared_component_contracts: list[SharedVolumetricComponentSummary] = Field(default_factory=list)
    capabilities: ProductSystemTemplateCapabilities | None = None
    readiness: ProductSystemTemplateReadiness | None = None
    # Publication lifecycle (active=true is never sufficient for published).
    publication_status: str | None = None
    publication_legacy_unspecified: bool = True
    publication_offerability_gate: str | None = None
    active_is_not_published: bool = True


class ProductTemplateAvailabilityResponse(BaseModel):
    items: list[ProductTemplateAvailabilityItem] = Field(default_factory=list)
    total: int = 0
    offerable_count: int = 0
    runtime_module_count: int = 0
