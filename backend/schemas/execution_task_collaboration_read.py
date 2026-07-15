"""Read-only execution task collaboration projection (FLEX-01).

Option B: optional principal from assigned_employee_id; actual workers from sessions.
No participant persistence; no write semantics.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

EXECUTION_TASK_COLLABORATION_READ_VERSION = "execution_task_collaboration_read/v1"

PrincipalSource = Literal[
    "execution_plan",
    "employee_claim",
    "manager_assign",
    "start_from_available",
    "unknown",
]

CollaborationCapability = Literal[
    "CURRENTLY_INDIVIDUAL_UI",
    "BACKEND_MULTI_SESSION_CAPABLE",
]


class OptionalPrincipalRead(BaseModel):
    """Optional coordinator hint from execution plan — not proof of work started."""

    optional_principal_employee_id: int | None = None
    optional_principal_employee_name: str | None = None
    optional_principal_source: PrincipalSource = "execution_plan"
    principal_has_started: bool = False


class WorkerSessionRead(BaseModel):
    session_id: str
    employee_id: int | None = None
    employee_name: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    duration_minutes: float | None = None
    is_active: bool = False
    session_status: str | None = None
    session_role: str | None = None
    session_type: str | None = None
    completed_by_employee_id: int | None = None


class ActualWorkerRead(BaseModel):
    """Worker derived from at least one session — not a persisted participant."""

    employee_id: int
    employee_name: str | None = None
    session_count: int = 0
    active_session_count: int = 0
    has_active_session: bool = False
    individual_work_time_minutes: float = 0.0
    worker_sessions: list[WorkerSessionRead] = Field(default_factory=list)
    is_optional_principal: bool = False


class TaskCollaborationRead(BaseModel):
    task_id: str
    display_name: str | None = None
    optional_principal: OptionalPrincipalRead
    actual_workers: list[ActualWorkerRead] = Field(default_factory=list)
    active_workers: list[ActualWorkerRead] = Field(default_factory=list)
    completed_session_workers: list[ActualWorkerRead] = Field(default_factory=list)
    has_multiple_actual_workers: bool = False
    aggregate_session_time_minutes: float = 0.0
    all_sessions_closed: bool = False
    active_sessions_count: int = 0
    total_sessions_count: int = 0
    operation_status: str
    operation_status_display: str | None = None
    operation_completed: bool = False
    derived_session_status: str
    collaboration_capability: CollaborationCapability = "BACKEND_MULTI_SESSION_CAPABLE"
    ui_collaboration_capability: CollaborationCapability = "CURRENTLY_INDIVIDUAL_UI"


class OrderTaskCollaborationReadResponse(BaseModel):
    contract_version: str = EXECUTION_TASK_COLLABORATION_READ_VERSION
    order_id: int
    order_code: str | None = None
    execution_plan_id: int | None = None
    tasks: list[TaskCollaborationRead] = Field(default_factory=list)
    generated_at: str
    read_model_notes: list[str] = Field(default_factory=list)
