"""MACHINE_RUN candidate discovery + task→active-run lookup read contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MachineRunStatus = Literal[
    "HELD",
    "RESERVED",
    "RUNNING",
    "COMPLETED",
    "CANCELLED",
    "RELEASED",
    "SUPERSEDED",
]
ReservationStatus = Literal[
    "HELD", "RESERVED", "CANCELLED", "RELEASED", "SUPERSEDED"
]


class MachineRunCandidateTask(BaseModel):
    execution_plan_id: int
    task_key: str
    order_id: int
    operation_code: str | None = None
    workcenter: str | None = None
    resource_mode: str
    machine_capability_code: str
    batch_eligible: bool
    task_label: str | None = None


class MachineRunCandidateListResult(BaseModel):
    """Eligible tasks for CREATE (machine_id) or ADD (machine_run_id) context."""

    context: Literal["create", "add"]
    machine_id: int
    machine_run_id: int | None = None
    machine_code: str | None = None
    machine_name: str | None = None
    required_capability: str | None = None
    mutation_allowed: bool = True
    reason_code: str | None = None
    message: str | None = None
    items: list[MachineRunCandidateTask] = Field(default_factory=list)
    count: int = 0


class ActiveMachineRunByTask(BaseModel):
    machine_run_id: int
    status: MachineRunStatus
    machine_id: int
    machine_code: str | None = None
    machine_name: str | None = None
    reservation_status: ReservationStatus
    execution_plan_id: int
    task_key: str
    order_id: int
    participant_status: Literal["ACTIVE"] = "ACTIVE"


class ActiveMachineRunByTaskResult(BaseModel):
    """Nullable membership — empty membership when task has no active run."""

    membership: ActiveMachineRunByTask | None = None
