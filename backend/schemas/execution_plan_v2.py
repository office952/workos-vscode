"""ExecutionPlan V2 preview schema (Step 9.3.2) — read-only, not persisted."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.quote_snapshot_v2 import QuoteSnapshotProvenanceEntry

EXECUTION_PLAN_V2_SOURCE = "order_snapshot_v2"
EXECUTION_PLAN_V2_PLAN_SOURCE = "order_snapshot_v2"
EXECUTION_PLAN_V2_PERSIST_STATUS = "not_persisted"
EXECUTION_PLAN_V2_TASKS_JSON_PLAN_VERSION = "v2.preview_to_plan.1"
PLANNING_MINUTES_WARNING = "PLANNING_MINUTES_SOURCE_REQUIRED"
TOTAL_ESTIMATED_TIME_SOURCE_NOT_AVAILABLE = "not_available_in_v2_preview"
READINESS_GATE_TASK_TYPE = "READINESS_GATE"
READINESS_GATE_EXCLUDED_WARNING = "READINESS_GATE_RULES_EXCLUDED_FROM_V2_PREVIEW"

ExecutionPlanV2PersistStatus = Literal["persisted", "already_exists", "blocked"]

ExecutionPlanV2PreviewStatus = Literal[
    "ready_for_owner_review",
    "partial_missing_planning_minutes",
    "partial_missing_optional_requirements",
    "blocked_missing_order_snapshot_v2",
    "blocked_missing_product_definition",
    "blocked_missing_product_aggregate",
    "blocked_missing_task_rules",
    "blocked_unknown_task_type",
    "blocked_snapshot_hash_mismatch",
    "blocked_forbidden_source",
    "blocked_legacy_order",
    "blocked_order_not_found",
    "blocked_missing_quote_snapshot_v2_id",
]

IGNORED_PRICING_SOURCES: list[str] = [
    "commercial_price_proposal_snapshot",
    "estimated_internal_cost_snapshot",
    "order.total_amount",
    "quote.grand_total",
    "quotes.line_items",
    "orders.snapshot_line_items",
    "cost_result",
    "workcenter_rates",
]


class PlannedTaskMaterialInput(BaseModel):
    material_code: str
    label: str | None = None
    unit: str | None = None
    component_ref: str | None = None


class PlannedTaskMachineRequirement(BaseModel):
    workcenter: str | None = None
    machine_type: str | None = None


class PlannedTaskEmployeeRoleRequirement(BaseModel):
    role_code: str | None = None


class PlannedTaskExternalServiceRequirement(BaseModel):
    service_code: str | None = None
    label: str | None = None


class PlannedTaskPreview(BaseModel):
    task_key: str
    label: str
    canonical_task_type: str
    source_module_code: str | None = None
    source_component_code: str | None = None
    source_operation_code: str | None = None
    source_task_rule_code: str | None = None
    sequence_index: int | None = None
    depends_on_task_keys: list[str] = Field(default_factory=list)
    material_inputs: list[PlannedTaskMaterialInput] = Field(default_factory=list)
    machine_requirement: PlannedTaskMachineRequirement | None = None
    employee_role_requirement: PlannedTaskEmployeeRoleRequirement | None = None
    external_service_requirement: PlannedTaskExternalServiceRequirement | None = None
    estimated_minutes: float | None = None
    planning_minutes_source: str | None = None
    warnings: list[str] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)


class PlannedOperationPreview(BaseModel):
    operation_code: str
    label: str | None = None
    workcenter: str | None = None
    component_ref: str | None = None
    sequence_index: int | None = None
    source_template_code: str | None = None
    priced: bool = True
    provenance: list[str] = Field(default_factory=list)


class PlannedTaskDependency(BaseModel):
    task_key: str
    depends_on_task_key: str


class MaterialReadinessInput(BaseModel):
    material_code: str
    label: str | None = None
    unit: str | None = None
    status: str = "unknown"


class MachineRequirementSummary(BaseModel):
    workcenter: str | None = None
    operation_codes: list[str] = Field(default_factory=list)


class EmployeeRoleRequirementSummary(BaseModel):
    role_code: str
    task_keys: list[str] = Field(default_factory=list)


class ExternalServiceRequirementSummary(BaseModel):
    service_code: str
    label: str | None = None
    task_keys: list[str] = Field(default_factory=list)


READINESS_GATE_TASK_TYPE = "READINESS_GATE"
READINESS_GATE_EXCLUDED_WARNING = "READINESS_GATE_RULES_EXCLUDED_FROM_V2_PREVIEW"


class ExecutionPlanV2Preview(BaseModel):
    """Read-only execution plan preview from OrderSnapshotV2 — never persisted."""

    status: ExecutionPlanV2PreviewStatus
    order_id: int | None = None
    order_code: str | None = None
    quote_id: int | None = None
    quote_snapshot_v2_id: int | None = None
    template_code: str | None = None
    source: str = EXECUTION_PLAN_V2_SOURCE
    source_snapshot_code: str | None = None
    source_content_hash: str | None = None
    source_order_snapshot_version: str | None = None
    order_snapshot_hash: str | None = None
    planned_operations: list[PlannedOperationPreview] = Field(default_factory=list)
    planned_tasks: list[PlannedTaskPreview] = Field(default_factory=list)
    dependencies: list[PlannedTaskDependency] = Field(default_factory=list)
    material_readiness_inputs: list[MaterialReadinessInput] = Field(default_factory=list)
    machine_requirements: list[MachineRequirementSummary] = Field(default_factory=list)
    employee_role_requirements: list[EmployeeRoleRequirementSummary] = Field(default_factory=list)
    external_service_requirements: list[ExternalServiceRequirementSummary] = Field(
        default_factory=list
    )
    ignored_pricing_sources: list[str] = Field(default_factory=lambda: list(IGNORED_PRICING_SOURCES))
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    provenance: list[QuoteSnapshotProvenanceEntry] = Field(default_factory=list)
    execution_plan_created: bool = False
    execution_tasks_created: bool = False
    persist_status: str = EXECUTION_PLAN_V2_PERSIST_STATUS
    no_write: bool = True
    message: str | None = None
    input_summary: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlanV2PersistResult(BaseModel):
    """Result of persisting ExecutionPlan V2 from validated preview — no task sessions."""

    status: ExecutionPlanV2PersistStatus
    persist_status: ExecutionPlanV2PersistStatus | None = None
    execution_plan_id: int | None = None
    order_id: int
    order_code: str | None = None
    quote_id: int | None = None
    quote_snapshot_v2_id: int | None = None
    template_code: str | None = None
    plan_source: str = EXECUTION_PLAN_V2_PLAN_SOURCE
    source_snapshot_code: str | None = None
    source_content_hash: str | None = None
    source_order_snapshot_version: str | None = None
    order_snapshot_hash: str | None = None
    preview_status: ExecutionPlanV2PreviewStatus | None = None
    total_estimated_time_minutes: float | None = None
    total_estimated_time_source: str | None = None
    execution_plan_created: bool = True
    execution_tasks_created: bool = False
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    provenance: list[QuoteSnapshotProvenanceEntry] = Field(default_factory=list)
    message: str | None = None
    input_summary: dict[str, Any] = Field(default_factory=dict)
