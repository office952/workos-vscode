"""Resource State — CREATE_MACHINE_RUN command contracts (create-only)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MachineRunStatus = Literal["HELD", "RESERVED", "CANCELLED", "RELEASED", "SUPERSEDED"]
MachineRunOperation = Literal["CREATE_MACHINE_RUN"]
ParticipantStatus = Literal["ACTIVE", "REMOVED"]
ReservationStatus = Literal[
    "HELD", "RESERVED", "CANCELLED", "RELEASED", "SUPERSEDED"
]


class MachineRunParticipantRef(BaseModel):
    execution_plan_id: int = Field(..., gt=0)
    task_key: str = Field(..., min_length=1, max_length=512)


class CreateMachineRunCommand(BaseModel):
    machine_id: int = Field(..., gt=0)
    reservation_start: datetime
    reservation_end: datetime
    timezone: str = Field(..., min_length=1, max_length=64)
    participants: list[MachineRunParticipantRef] = Field(..., min_length=1)
    expected_version: int = Field(default=0, ge=0)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(
        default="machine_run_create", min_length=1, max_length=64
    )
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class MachineRunParticipantResult(BaseModel):
    execution_plan_id: int
    task_key: str
    order_id: int
    status: ParticipantStatus


class CreateMachineRunResult(BaseModel):
    machine_run_id: int
    status: MachineRunStatus
    version: int
    reservation_id: int
    reservation_status: ReservationStatus
    reservation_version: int
    machine_id: int
    reservation_start: datetime
    reservation_end: datetime
    timezone: str
    participants: list[MachineRunParticipantResult]
    operation: MachineRunOperation
    transition_id: str
    reservation_transition_id: str
    already_applied: bool = False
