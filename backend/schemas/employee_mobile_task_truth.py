"""Employee Mobile canonical task read model (MOBILE-T01)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.execution_plan_v2_frozen_task_identity import FROZEN_TASK_IDENTITY_VERSION

EMPLOYEE_MOBILE_TASK_TRUTH_VERSION = "employee_mobile_task_truth/v1"

MobileIdentitySource = Literal[
    "frozen_task_identity/v1",
    "legacy_plan_task",
    "not_proven",
]

MobileReadinessAuthority = Literal[
    "FROZEN_ORDER_SNAPSHOT_V2",
    "LEGACY_READ_MODEL_EXPLICIT",
    "BLOCKED_MISSING_ORDER_SNAPSHOT_V2",
]


class EmployeeMobileTaskIdentity(BaseModel):
    task_id: str
    deterministic_task_key: str | None = None
    display_label: str
    component_label: str | None = None
    component_role: str | None = None
    operation_label: str | None = None
    operation_code: str | None = None
    logo_segment_label: str | None = None
    identity_source: MobileIdentitySource = "not_proven"
    identity_classification: str | None = None


class EmployeeMobileTaskAssignment(BaseModel):
    assigned_employee_id: int | None = None
    assigned_employee_name: str | None = None
    is_assigned_to_current_employee: bool = False
    is_available_for_claim: bool = False
    assignment_source: str = "execution_plan"
    can_claim: bool = False


class EmployeeMobileTaskReadiness(BaseModel):
    is_startable: bool = False
    readiness_label: str | None = None
    readiness_status: str | None = None
    readiness_reasons: list[dict[str, Any]] = Field(default_factory=list)
    blocking_task_ids: list[str] = Field(default_factory=list)
    blocking_tasks: list[dict[str, Any]] = Field(default_factory=list)
    material_warning: str | None = None
    dependency_warning: str | None = None
    production_release_blocked: bool = False
    production_blocker_summary: str | None = None
    can_start: bool = False
    can_start_from_available: bool = False
    can_complete: bool = False


class EmployeeMobileTaskAuthority(BaseModel):
    task_identity_version: str | None = None
    readiness_authority: MobileReadinessAuthority = "LEGACY_READ_MODEL_EXPLICIT"
    release_authority: str = "execution_owner_decision_production_release_service"
    legacy_fallback_active: bool = False
    execution_source: str = "execution_plan_v2_operational_tasks"


class EmployeeMobileTruthTask(BaseModel):
    identity: EmployeeMobileTaskIdentity
    assignment: EmployeeMobileTaskAssignment
    readiness: EmployeeMobileTaskReadiness
    authority: EmployeeMobileTaskAuthority
    order_id: int
    order_code: str = ""
    client_label: str = ""
    execution_plan_id: int | None = None
    plan_sequence: int | None = None
    status: str = "assigned"
    started_at: str | None = None
    completed_at: str | None = None
    blocked_at: str | None = None
    blocked_reason: str | None = None
    access_mode: str | None = None
    preview_only: bool = False


class EmployeeMobileTaskTruthSummary(BaseModel):
    total_tasks: int = 0
    assigned_count: int = 0
    available_count: int = 0
    startable_count: int = 0
    blocked_count: int = 0


class EmployeeMobileTaskTruthCapabilities(BaseModel):
    can_claim_available: bool = True
    can_resolve_owner_decisions: bool = False
    can_view_internal_cost: bool = False


class EmployeeMobileTaskTruthResponse(BaseModel):
    contract_version: str = EMPLOYEE_MOBILE_TASK_TRUTH_VERSION
    employee_id: int
    employee_display_name: str = ""
    generated_at: str
    source: str = "employee_mobile_task_truth_service"
    legacy_mode: bool = False
    tasks: list[EmployeeMobileTruthTask] = Field(default_factory=list)
    summary: EmployeeMobileTaskTruthSummary = Field(default_factory=EmployeeMobileTaskTruthSummary)
    capabilities: EmployeeMobileTaskTruthCapabilities = Field(
        default_factory=EmployeeMobileTaskTruthCapabilities
    )
