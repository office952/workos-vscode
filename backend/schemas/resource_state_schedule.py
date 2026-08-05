"""Resource State R9 — scheduling writer command contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ScheduleInitialStatus = Literal["DRAFT", "PLANNED"]
ScheduleStatus = Literal[
    "DRAFT", "PLANNED", "CONFIRMED", "CANCELLED", "SUPERSEDED"
]
ScheduleOperation = Literal[
    "CREATE_SCHEDULE",
    "RESCHEDULE",
    "CONFIRM_SCHEDULE",
    "CANCEL_SCHEDULE",
    "SUPERSEDE_SCHEDULE",
]


class CreateScheduleCommand(BaseModel):
    execution_plan_id: int = Field(..., gt=0)
    task_key: str = Field(..., min_length=1, max_length=512)
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str = Field(..., min_length=1, max_length=64)
    initial_status: ScheduleInitialStatus = "DRAFT"
    workcenter_code: str | None = Field(default=None, max_length=128)
    expected_version: int = Field(default=0, ge=0)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(default="schedule_create", min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class RescheduleCommand(BaseModel):
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str | None = Field(default=None, max_length=64)
    workcenter_code: str | None = Field(default=None, max_length=128)
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class ConfirmScheduleCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(default="schedule_confirm", min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class CancelScheduleCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class SupersedeScheduleCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(
        ...,
        min_length=8,
        max_length=36,
        description="Idempotency key for SUPERSEDE transition on the prior row.",
    )
    replacement_idempotency_key: str = Field(
        ...,
        min_length=8,
        max_length=36,
        description="Idempotency key for CREATE of the replacement row.",
    )
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str = Field(..., min_length=1, max_length=64)
    initial_status: ScheduleInitialStatus = "PLANNED"
    workcenter_code: str | None = Field(default=None, max_length=128)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class ScheduleCommandResult(BaseModel):
    schedule_id: int
    execution_plan_id: int
    task_key: str
    status: ScheduleStatus
    version: int
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str
    operation: ScheduleOperation
    transition_id: str
    previous_status: ScheduleStatus | None = None
    previous_version: int | None = None
    already_applied: bool = False
    replacement_schedule_id: int | None = None
    replacement_transition_id: str | None = None
