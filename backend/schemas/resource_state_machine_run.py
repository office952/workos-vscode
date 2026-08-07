"""Resource State — MACHINE_RUN command contracts (CREATE + lifecycle + participants)."""

from __future__ import annotations

from datetime import datetime
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
MachineRunOperation = Literal[
    "CREATE_MACHINE_RUN",
    "CONFIRM_MACHINE_RUN",
    "RELEASE_MACHINE_RUN",
    "CANCEL_MACHINE_RUN",
    "RESCHEDULE_MACHINE_RUN",
    "ADD_MACHINE_RUN_PARTICIPANT",
    "REMOVE_MACHINE_RUN_PARTICIPANT",
]
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


class ConfirmMachineRunCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(
        default="machine_run_confirm", min_length=1, max_length=64
    )
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class ReleaseMachineRunCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(
        default="machine_run_release", min_length=1, max_length=64
    )
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class CancelMachineRunCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(
        default="machine_run_cancel", min_length=1, max_length=64
    )
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class RescheduleMachineRunCommand(BaseModel):
    reservation_start: datetime
    reservation_end: datetime
    timezone: str = Field(..., min_length=1, max_length=64)
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(
        default="machine_run_reschedule", min_length=1, max_length=64
    )
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class AddMachineRunParticipantCommand(BaseModel):
    execution_plan_id: int = Field(..., gt=0)
    task_key: str = Field(..., min_length=1, max_length=512)
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(
        default="machine_run_add_participant", min_length=1, max_length=64
    )
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class RemoveMachineRunParticipantCommand(BaseModel):
    execution_plan_id: int = Field(..., gt=0)
    task_key: str = Field(..., min_length=1, max_length=512)
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(
        default="machine_run_remove_participant", min_length=1, max_length=64
    )
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class MachineRunParticipantResult(BaseModel):
    execution_plan_id: int
    task_key: str
    order_id: int
    status: ParticipantStatus


class CreateMachineRunResult(BaseModel):
    """Shared response for CREATE, lifecycle, RESCHEDULE, and participant commands."""

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
    previous_status: MachineRunStatus | None = None
    previous_version: int | None = None
    affected_participant: MachineRunParticipantResult | None = None
