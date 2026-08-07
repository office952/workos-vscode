"""MACHINE_RUN operator read contracts (list + detail)."""

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
ReservationStatus = Literal[
    "HELD", "RESERVED", "CANCELLED", "RELEASED", "SUPERSEDED"
]
ParticipantStatus = Literal["ACTIVE", "REMOVED"]


class MachineRunMachineProjection(BaseModel):
    machine_id: int
    machine_code: str
    name: str
    is_active: bool
    is_available: bool
    operational_status: str | None = None
    capabilities: list[str] = Field(default_factory=list)


class MachineRunReservationProjection(BaseModel):
    reservation_id: int
    status: ReservationStatus
    version: int
    machine_id: int
    reservation_start: datetime
    reservation_end: datetime
    timezone: str


class MachineRunParticipantRead(BaseModel):
    participant_id: int
    status: ParticipantStatus
    execution_plan_id: int
    task_key: str
    order_id: int
    operation_code: str | None = None
    workcenter: str | None = None
    machine_capability_code: str | None = None
    batch_eligible: bool | None = None
    added_at: datetime | None = None
    added_by: str | None = None
    removed_at: datetime | None = None
    removed_by: str | None = None


class MachineRunListItem(BaseModel):
    machine_run_id: int
    status: MachineRunStatus
    version: int
    machine_id: int
    machine_code: str | None = None
    machine_name: str | None = None
    reservation_id: int
    reservation_status: ReservationStatus
    reservation_version: int
    reservation_start: datetime
    reservation_end: datetime
    timezone: str
    active_participant_count: int
    total_participant_count: int
    execution_plan_ids: list[int] = Field(default_factory=list)
    order_ids: list[int] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MachineRunListResult(BaseModel):
    items: list[MachineRunListItem]
    count: int


class MachineRunDetail(BaseModel):
    machine_run_id: int
    status: MachineRunStatus
    version: int
    timezone: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    actual_runtime_seconds: int | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    machine: MachineRunMachineProjection
    reservation: MachineRunReservationProjection
    participants: list[MachineRunParticipantRead]
    execution_plan_ids: list[int] = Field(default_factory=list)
    order_ids: list[int] = Field(default_factory=list)
    active_participant_count: int
    total_participant_count: int
