"""Canonical operator execution task truth read model (W6-T01)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.execution_owner_decision_release import PRODUCTION_RELEASE_POLICY
from schemas.execution_plan_v2_frozen_task_identity import FROZEN_TASK_IDENTITY_VERSION

OPERATOR_TASK_TRUTH_VERSION = "operator_task_truth/v1"
PRODUCTION_RELEASE_SCOPE = "ORDER_SCOPE"

ReadinessAuthority = Literal[
    "FROZEN_ORDER_SNAPSHOT_V2",
    "LEGACY_ORDER_INPUT",
    "LEGACY_READ_MODEL_EXPLICIT",
    "BLOCKED_MISSING_ORDER_SNAPSHOT_V2",
]

IdentitySource = Literal[
    "frozen_task_identity/v1",
    "legacy_plan_task",
    "not_proven",
]


class TaskIdentityTruth(BaseModel):
    task_id: str
    deterministic_task_key: str | None = None
    display_label: str
    identity_classification: str | None = None
    source_graph_node_id: str | None = None
    source_component_instance_id: str | None = None
    component_role: str | None = None
    component_label: str | None = None
    component_template_code: str | None = None
    source_operation_code: str | None = None
    source_task_rule_code: str | None = None
    parent_graph_node_id: str | None = None
    task_scope: str | None = None
    logo_segment_key: str | None = None
    identity_source: IdentitySource = "not_proven"


class TaskRuntimeTruth(BaseModel):
    current_status: str
    assigned_employee_id: int | None = None
    assigned_employee_name: str | None = None
    is_startable: bool = False
    is_completeable: bool = False
    is_blocked: bool = False
    readiness_status: str | None = None
    readiness_label: str | None = None
    readiness_reasons: list[dict[str, Any]] = Field(default_factory=list)
    blocking_reasons: list[dict[str, Any]] = Field(default_factory=list)
    blocking_task_ids: list[str] = Field(default_factory=list)
    blocking_tasks: list[dict[str, Any]] = Field(default_factory=list)
    production_release_blocked: bool = False
    production_release_status: str
    production_release_scope: str = PRODUCTION_RELEASE_SCOPE
    blocking_owner_decision_codes: list[str] = Field(default_factory=list)
    last_started_at: str | None = None
    last_ended_at: str | None = None


class TaskAuthorityTruth(BaseModel):
    frozen_source: str | None = None
    operational_source: str = "execution_reality"
    readiness_source: str = "task_readiness_service"
    production_release_source: str = "execution_owner_decision_production_release_service"
    legacy_fallback_active: bool = False


class OperatorTaskTruthTask(BaseModel):
    identity: TaskIdentityTruth
    runtime: TaskRuntimeTruth
    authority: TaskAuthorityTruth


class OwnerDecisionSummaryItem(BaseModel):
    code: str
    label: str
    category: str
    blocking: bool
    frozen_status: str = "present"
    operational_status: str
    scope: str = "order"
    required_action: str | None = None
    acknowledgement_sufficient: bool = False
    requires_resolution: bool = False
    can_resolve: bool = False
    resolved_at: str | None = None
    resolved_by_user_name: str | None = None
    has_resolution_note: bool = False


class RoleCapabilities(BaseModel):
    can_resolve_owner_decisions: bool = False
    can_view_internal_cost: bool = False
    can_view_owner_decision_notes: bool = False


class InternalCostSummary(BaseModel):
    visibility: Literal["available", "restricted"]
    status: str | None = None
    estimated_total_internal_cost: float | None = None
    accepted_commercial_total: float | None = None
    execution_blocked: bool | None = None


class OperatorTaskTruthResponse(BaseModel):
    contract_version: str = OPERATOR_TASK_TRUTH_VERSION
    order_id: int
    order_code: str | None = None
    execution_plan_id: int | None = None
    order_snapshot_v2_id: int | None = None
    quote_snapshot_v2_id: int | None = None
    task_identity_version: str | None = None
    readiness_authority: ReadinessAuthority
    production_release_policy: str = PRODUCTION_RELEASE_POLICY
    production_release_status: str
    production_release_blocked: bool
    owner_decisions_summary: list[OwnerDecisionSummaryItem] = Field(default_factory=list)
    role_capabilities: RoleCapabilities
    internal_cost_summary: InternalCostSummary | None = None
    tasks: list[OperatorTaskTruthTask] = Field(default_factory=list)
    generated_at: str
    legacy_order: bool = False


# Re-export for schema tests
CANONICAL_FROZEN_IDENTITY_FIELDS = (
    "contract_version",
    "deterministic_task_key",
    "source_graph_node_id",
    "source_component_role",
    "source_template_code",
    "source_component_instance_id",
    "source_segment_key",
    "source_operation_code",
    "source_task_rule_code",
    "parent_graph_node_id",
    "operation_scope",
    "identity_classification",
    "task_rule_origin",
)

DEFAULT_TASK_IDENTITY_VERSION = FROZEN_TASK_IDENTITY_VERSION
