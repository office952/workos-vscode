"""Resource State R9 — machine reservation writer command contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ReservationStatus = Literal[
    "HELD", "RESERVED", "CANCELLED", "RELEASED", "SUPERSEDED"
]
ReservationOperation = Literal[
    "CREATE_RESERVATION",
    "CONFIRM_RESERVATION",
    "RELEASE_RESERVATION",
    "CANCEL_RESERVATION",
    "SUPERSEDE_RESERVATION",
]


class CreateReservationCommand(BaseModel):
    execution_plan_id: int = Field(..., gt=0)
    task_key: str = Field(..., min_length=1, max_length=512)
    machine_id: int = Field(..., gt=0)
    reservation_start: datetime
    reservation_end: datetime
    timezone: str = Field(..., min_length=1, max_length=64)
    expected_version: int = Field(default=0, ge=0)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(
        default="reservation_create", min_length=1, max_length=64
    )
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class ConfirmReservationCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(
        default="reservation_confirm", min_length=1, max_length=64
    )
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class ReleaseReservationCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class CancelReservationCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class SupersedeReservationCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    replacement_idempotency_key: str = Field(..., min_length=8, max_length=36)
    machine_id: int | None = Field(default=None, gt=0)
    reservation_start: datetime
    reservation_end: datetime
    timezone: str = Field(..., min_length=1, max_length=64)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class ReservationCommandResult(BaseModel):
    reservation_id: int
    execution_plan_id: int
    task_key: str
    machine_id: int
    status: ReservationStatus
    version: int
    reservation_start: datetime
    reservation_end: datetime
    timezone: str
    operation: ReservationOperation
    transition_id: str
    previous_status: ReservationStatus | None = None
    previous_version: int | None = None
    already_applied: bool = False
    replacement_reservation_id: int | None = None
    replacement_transition_id: str | None = None
