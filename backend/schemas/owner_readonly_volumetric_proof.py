"""Owner read-only Product / Price / Tasking proof — projection only, no new tasking."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

PROOF_VERSION = "owner_readonly_volumetric_v1"


class OwnerProofSafety(BaseModel):
    no_write: bool = True
    no_snapshot_persist: bool = True
    no_execution_plan_write: bool = True
    no_task_materialization: bool = True
    no_new_tasking_system: bool = True
    resolver_is_not_task_engine: bool = True
    money_authority: Literal["cpp_live_materials"] = "cpp_live_materials"
    process_authority: Literal["modular_resolver"] = "modular_resolver"
    tasking_authority: Literal["existing_task_rules"] = "existing_task_rules"


class OwnerProofIntakeSelection(BaseModel):
    support_source: str | None = None
    mounting_system: str | None = None
    mounting_solution_template: str | None = None
    return_finish_type: str | None = None
    mains_cable_length_m: float | None = None
    power_supply_service_corner: str | None = None
    service_screw_finish: str | None = None
    mounting_template_enabled: bool | None = None
    lighting_system_type: str | None = None


class OwnerProofProductDefinitionSlice(BaseModel):
    template_code: str
    canonical_values: dict[str, Any] = Field(default_factory=dict)
    readiness_status: str | None = None
    missing_required_fields: list[str] = Field(default_factory=list)


class OwnerProofProcessNode(BaseModel):
    process_code: str
    depends_on_process_ids: list[str] = Field(default_factory=list)
    sequence: int | None = None
    component_ref: str | None = None


class OwnerProofProcessGraph(BaseModel):
    process_graph_source: str | None = None
    process_graph_hash: str | None = None
    process_contract_version: str | None = None
    process_count: int = 0
    edge_count: int = 0
    processes: list[OwnerProofProcessNode] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class OwnerProofTaskRulesProjection(BaseModel):
    """Projection of Aggregate.task_contract into existing task_rules — not a new graph."""

    authority: Literal["existing_task_rules"] = "existing_task_rules"
    process_graph_source: str | None = None
    rule_count: int = 0
    task_names: list[str] = Field(default_factory=list)
    depends_on_preserved: bool = True
    notes: list[str] = Field(default_factory=list)


class OwnerProofWireSupplyLine(BaseModel):
    present: bool = False
    material_code: str | None = None
    material_key: str | None = None
    quantity: float | None = None
    unit: str | None = None
    quantity_source: str | None = None
    quantity_basis: str | None = None
    unit_price: float | None = None
    estimated_cost: float | None = None
    price_source: str | None = None


class OwnerProofLiveMaterials(BaseModel):
    wire_supply: OwnerProofWireSupplyLine = Field(default_factory=OwnerProofWireSupplyLine)
    cable_channel_commercial_guarded: bool = False
    consumable_keys: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)


class OwnerProofExecutionPreview4C(BaseModel):
    present: bool = False
    no_write: bool = True
    candidate_count: int = 0
    edge_count: int = 0
    process_depends_on_edges: int = 0
    sequence_fallback_edges: int = 0
    sample_dependencies: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class OwnerProofVerificationPath(BaseModel):
    intake_ui: str
    product_system_ui: str
    proof_api: str
    aggregate_api: str
    logical_list_api: str
    execution_preview_api: str


class OwnerReadonlyVolumetricProof(BaseModel):
    proof_version: str = PROOF_VERSION
    template_code: str
    workspace_id: str
    safety: OwnerProofSafety = Field(default_factory=OwnerProofSafety)
    intake_selection: OwnerProofIntakeSelection = Field(default_factory=OwnerProofIntakeSelection)
    product_definition: OwnerProofProductDefinitionSlice
    process_graph: OwnerProofProcessGraph = Field(default_factory=OwnerProofProcessGraph)
    task_rules_projection: OwnerProofTaskRulesProjection = Field(
        default_factory=OwnerProofTaskRulesProjection
    )
    live_materials: OwnerProofLiveMaterials = Field(default_factory=OwnerProofLiveMaterials)
    execution_preview_4c: OwnerProofExecutionPreview4C = Field(
        default_factory=OwnerProofExecutionPreview4C
    )
    guards: list[str] = Field(default_factory=list)
    verification_path: OwnerProofVerificationPath
    chain_ok: bool = False
    notes: list[str] = Field(default_factory=list)
