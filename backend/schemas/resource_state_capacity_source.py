"""Capacity Stage 1 — workcenter capacity source command contracts."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

OverAllocationPolicy = Literal["WARN_ONLY", "HARD_BLOCK", "ALLOW_WITH_REASON"]
CapacitySourceLabel = Literal["OWNER_CONFIGURED", "SYSTEM_DERIVED", "AI_DECISION"]
CapacitySourceStatus = Literal["ACTIVE", "DISABLED", "SUPERSEDED"]
CapacitySourceOperation = Literal[
    "CREATE_WORKCENTER_CAPACITY",
    "ADJUST_WORKCENTER_CAPACITY",
    "DISABLE_WORKCENTER_CAPACITY",
    "SUPERSEDE_WORKCENTER_CAPACITY",
]


class CreateWorkcenterCapacityCommand(BaseModel):
    workcenter_code: str = Field(..., min_length=1, max_length=128)
    bucket_date: date
    timezone: str = Field(..., min_length=1, max_length=64)
    available_minutes: int = Field(..., ge=0)
    over_allocation_policy: OverAllocationPolicy = "WARN_ONLY"
    source_label: CapacitySourceLabel = "OWNER_CONFIGURED"
    source_explanation: str | None = Field(default=None, max_length=500)
    source_execution_truth: bool = True
    expected_version: int = Field(default=0, ge=0)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(
        default="capacity_source_create", min_length=1, max_length=64
    )
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class AdjustWorkcenterCapacityCommand(BaseModel):
    available_minutes: int = Field(..., ge=0)
    over_allocation_policy: OverAllocationPolicy | None = None
    source_label: CapacitySourceLabel | None = None
    source_explanation: str | None = Field(default=None, max_length=500)
    source_execution_truth: bool | None = None
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class DisableWorkcenterCapacityCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class SupersedeWorkcenterCapacityCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    replacement_idempotency_key: str = Field(..., min_length=8, max_length=36)
    available_minutes: int = Field(..., ge=0)
    over_allocation_policy: OverAllocationPolicy = "WARN_ONLY"
    source_label: CapacitySourceLabel = "OWNER_CONFIGURED"
    source_explanation: str | None = Field(default=None, max_length=500)
    source_execution_truth: bool = True
    timezone: str | None = Field(default=None, max_length=64)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class WorkcenterCapacitySourceResult(BaseModel):
    source_id: int
    workcenter_code: str
    bucket_date: date
    bucket_start: datetime
    bucket_end: datetime
    timezone: str
    available_minutes: int
    over_allocation_policy: OverAllocationPolicy
    source_label: CapacitySourceLabel
    source_execution_truth: bool
    status: CapacitySourceStatus
    version: int
    operation: CapacitySourceOperation
    transition_id: str
    previous_status: CapacitySourceStatus | None = None
    previous_version: int | None = None
    already_applied: bool = False
    replacement_source_id: int | None = None
    replacement_transition_id: str | None = None
