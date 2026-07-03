"""ExecutionPlan V2 materialization audit schema (Step 9 audit-only)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.execution_plan_v2 import READINESS_GATE_TASK_TYPE

MaterializationAuditStatus = Literal[
    "blocked_needs_owner_go",
    "already_materialized_in_envelope",
    "dry_run_blocked",
    "dry_run_ready_with_warnings",
]

DryRunMaterializationStatus = Literal[
    "blocked",
    "ready_with_warnings",
    "ready",
    "already_materialized",
]


class MaterializableTaskCandidatePreview(BaseModel):
    task_key: str
    label: str | None = None
    canonical_task_type: str | None = None
    source_operation_code: str | None = None
    sequence_index: int | None = None
    operational_status_preview: str = "pending"
    estimated_minutes: float | None = None
    warnings: list[str] = Field(default_factory=list)


class NonOperationalItemPreview(BaseModel):
    task_name: str
    task_type: str
    reason: str
    excluded_from: str = "planned_tasks_and_materialization"


class MaterializationAuditGuards(BaseModel):
    mode: str = "audit_only"
    creates_execution_tasks: bool = False
    creates_sessions: bool = False
    writes_database: bool = False
    uses_cost_engine: bool = False
    uses_price_endpoint: bool = False
    uses_quote_orchestrator: bool = False
    employee_mobile_scope: bool = False
    post_materialize_allowed: bool = False


class ExecutionPlanV2MaterializationAudit(BaseModel):
    """Read-only audit of V2 plan → operational_tasks mapping — never persists."""

    mode: Literal["audit_only"] = "audit_only"
    order_id: int
    order_code: str | None = None
    execution_plan_id: int
    source_quote_snapshot_v2_id: int | None = None
    source_snapshot_code: str | None = None
    plan_source: str | None = None
    template_code: str | None = None
    materialization_status: MaterializationAuditStatus
    dry_run_status: DryRunMaterializationStatus
    planned_task_count: int = 0
    operation_count: int = 0
    operational_tasks_in_envelope_count: int = 0
    materializable_task_candidates: list[MaterializableTaskCandidatePreview] = Field(
        default_factory=list
    )
    non_operational_items: list[NonOperationalItemPreview] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    activation_hash_preview: str | None = None
    guards: MaterializationAuditGuards = Field(default_factory=MaterializationAuditGuards)
    contract_notes: list[str] = Field(default_factory=list)
    message: str | None = None
    input_summary: dict[str, Any] = Field(default_factory=dict)
