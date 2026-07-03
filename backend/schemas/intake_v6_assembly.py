"""Read-only Intake V6 assembly preview contracts.

These contracts model a composed product assembly for preview and planning only.
They do not create execution tasks, mutate stock, or persist new DB entities.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AssemblyType = Literal[
    "letters_only",
    "logo_only",
    "letters_logo",
    "letters_on_acp_background",
    "mixed_custom",
]

AssemblyStatus = Literal[
    "draft",
    "needs_input",
    "ready_for_cost",
    "ready_for_task_preview",
]

ComponentType = Literal[
    "volumetric_letters",
    "volumetric_logo",
    "acp_background",
    "metal_structure",
    "forex_backing",
    "lighting",
    "mounting",
]

ComponentSource = Literal[
    "initial_request",
    "svg_detected",
    "operator_added",
    "product_system_required",
]

BindingStatus = Literal["pending", "suggested", "confirmed", "ignored"]
RequiredFieldsStatus = Literal["missing", "partial", "complete"]


class AssemblyDraftChangeLogEntry(BaseModel):
    at: str
    source: str
    event: str
    component_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ComponentInstance(BaseModel):
    component_id: str
    component_type: ComponentType
    template_code: str
    source: ComponentSource
    source_layer_keys: list[str] = Field(default_factory=list)
    binding_status: BindingStatus = "pending"
    required_fields_status: RequiredFieldsStatus = "missing"
    material_roles: list[str] = Field(default_factory=list)
    operation_roles: list[str] = Field(default_factory=list)
    depends_on_component_ids: list[str] = Field(default_factory=list)
    enabled: bool = True


class AssemblyDraft(BaseModel):
    assembly_id: str
    workspace_id: str
    primary_family: str
    assembly_type: AssemblyType
    primary_template_code: str
    component_instances: list[ComponentInstance] = Field(default_factory=list)
    version: int = 1
    change_log: list[AssemblyDraftChangeLogEntry] = Field(default_factory=list)
    status: AssemblyStatus = "draft"


class OperationCandidateMeasure(BaseModel):
    unit: str
    value: float | None = None


class OperationCandidate(BaseModel):
    candidate_id: str
    assembly_id: str
    component_id: str
    source_template_code: str
    source_layer_key: str | None = None
    operation_type: str
    process_type: str
    material_family: str | None = None
    material_code: str | None = None
    thickness_mm: float | None = None
    finish_code: str | None = None
    color_code: str | None = None
    machine_type: str | None = None
    workcenter: str | None = None
    setup_group_key: str | None = None
    dependency_group: str | None = None
    geometry_refs: list[str] = Field(default_factory=list)
    geometry_source: str | None = None
    quantity: OperationCandidateMeasure = Field(
        default_factory=lambda: OperationCandidateMeasure(unit="count", value=None)
    )
    total_area: float | None = None
    total_perimeter: float | None = None
    estimated_time: OperationCandidateMeasure = Field(
        default_factory=lambda: OperationCandidateMeasure(unit="min", value=None)
    )
    consolidation_allowed: bool = False
    separation_reason: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ConsolidatedTask(BaseModel):
    task_id: str
    assembly_id: str
    task_type: str
    process_type: str
    material_code: str | None = None
    thickness_mm: float | None = None
    finish_code: str | None = None
    color_code: str | None = None
    machine_type: str | None = None
    workcenter: str | None = None
    nesting_group_key: str | None = None
    consolidated_from_candidates: list[str] = Field(default_factory=list)
    consolidated_from_components: list[str] = Field(default_factory=list)
    geometry_refs: list[str] = Field(default_factory=list)
    total_quantity: OperationCandidateMeasure | None = None
    total_area: float | None = None
    total_perimeter: float | None = None
    sheet_plan_id: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    qc_rules: list[str] = Field(default_factory=list)
    separation_notes: list[str] = Field(default_factory=list)