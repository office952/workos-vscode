"""Product process contract — resolved graph schemas (pure; no DB)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

CantFinish = Literal["standard", "vinyl", "ral"]
SupportType = Literal["none", "metal_bars", "alucobond_cased"]
ScrewFinish = Literal["NATURAL", "PAINTED_TO_MATCH_CANT"]
ServiceCorner = Literal[
    "TOP_LEFT",
    "TOP_RIGHT",
    "BOTTOM_LEFT",
    "BOTTOM_RIGHT",
    "MANUAL_CONFIRMED",
]


class ProductProcessResolveInput(BaseModel):
    """Confirmed job configuration for the process resolver (fixture or ProductDefinition-shaped)."""

    product_template_code: str = "TPL-VOLUMETRIC-LETTERS_v2"
    contract_version: str = "product_process/volumetric_letters/v1"
    active_components: list[str] = Field(default_factory=list)
    cant_finish: CantFinish = "standard"
    support_type: SupportType = "none"
    screw_finish: ScrewFinish | None = "NATURAL"
    power_supply_service_corner: ServiceCorner | None = None
    mains_cable_length_m: float | None = None
    template_selected: bool = False
    illuminated: bool = True
    geometry_confirmed: bool = True
    led_layout_confirmed: bool = True
    # D3: when segmented electrical authority is CONFIRMED+complete, legacy single-panel
    # When True, confirmed multi-panel segmented assembly owns electrical/service decisions;
    # power_supply_service_corner is not required for alucobond_cased.
    segmented_electrical_authority_complete: bool = False
    geometry: dict[str, Any] = Field(default_factory=dict)
    # Adversarial / test injection hooks (never used in production paths)
    inject_cycle_edge: tuple[str, str] | None = None
    inject_missing_producer_state: str | None = None
    force_include_processes: list[str] = Field(default_factory=list)


class ResolvedProcessRule(BaseModel):
    process_code: str
    name: str
    source_component: str | None = None
    source_interface: str | None = None
    requires_states: list[str] = Field(default_factory=list)
    produces_states: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    material_roles: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    sequence_hint: int | None = None
    parallel_group: str | None = None
    active_reason: str | None = None
    contract_version: str | None = None
    priced_operation: str | None = None
    mini_module_code: str | None = None


class ResolvedMaterialRequirement(BaseModel):
    material_role: str
    source_process: str | None = None
    source_component: str | None = None
    source_interface: str | None = None
    optional: bool = False


class ResolverIssue(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ResolvedProductProcessGraph(BaseModel):
    contract_version: str
    catalog_version: str
    product_template_code: str
    active_component_codes: list[str] = Field(default_factory=list)
    active_interface_codes: list[str] = Field(default_factory=list)
    process_rules: list[ResolvedProcessRule] = Field(default_factory=list)
    process_order: list[str] = Field(default_factory=list)
    material_roles: list[ResolvedMaterialRequirement] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    produced_states: list[str] = Field(default_factory=list)
    parallel_groups: dict[str, list[str]] = Field(default_factory=dict)
    config_echo: dict[str, Any] = Field(default_factory=dict)
    warnings: list[ResolverIssue] = Field(default_factory=list)
    blockers: list[ResolverIssue] = Field(default_factory=list)
    component_contract_hash: str | None = None
    interface_contract_hash: str | None = None
    process_graph_hash: str | None = None
    graph_hash: str | None = None
    readiness: Literal["ready", "blocked", "degraded"] = "ready"
