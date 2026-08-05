"""Capacity Stage 1 — capacity allocation writer command contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CapacityStatus = Literal[
    "HELD", "ALLOCATED", "RELEASED", "CANCELLED", "SUPERSEDED"
]
CapacityInitialStatus = Literal["HELD", "ALLOCATED"]
CapacityOperation = Literal[
    "CREATE_ALLOCATION",
    "ADJUST_ALLOCATION",
    "RELEASE_ALLOCATION",
    "CANCEL_ALLOCATION",
    "SUPERSEDE_ALLOCATION",
]
WorkloadSource = Literal[
    "OWNER_CONFIGURED",
    "PRODUCT_AGGREGATE_DERIVED",
    "OPERATION_CONTRACT",
    "AI_DECISION",
    "MANUAL_MANAGER_ESTIMATE",
]


class CreateAllocationCommand(BaseModel):
    execution_plan_id: int = Field(..., gt=0)
    task_key: str = Field(..., min_length=1, max_length=512)
    workcenter_code: str = Field(..., min_length=1, max_length=128)
    bucket_start: datetime
    bucket_end: datetime
    timezone: str = Field(..., min_length=1, max_length=64)
    quantity_minutes: int = Field(..., gt=0)
    workload_source: WorkloadSource
    workload_source_reference: str | None = Field(default=None, max_length=255)
    workload_explanation: str | None = Field(default=None, max_length=500)
    initial_status: CapacityInitialStatus = "ALLOCATED"
    expected_source_version: int | None = Field(
        default=None,
        ge=1,
        description="Optional CAS against workcenter capacity source version.",
    )
    expected_version: int = Field(default=0, ge=0)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(
        default="capacity_allocate", min_length=1, max_length=64
    )
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class AdjustAllocationCommand(BaseModel):
    quantity_minutes: int | None = Field(default=None, gt=0)
    bucket_start: datetime | None = None
    bucket_end: datetime | None = None
    timezone: str | None = Field(default=None, max_length=64)
    workload_source: WorkloadSource | None = None
    workload_source_reference: str | None = Field(default=None, max_length=255)
    workload_explanation: str | None = Field(default=None, max_length=500)
    expected_source_version: int | None = Field(default=None, ge=1)
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class ReleaseAllocationCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class CancelAllocationCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class SupersedeAllocationCommand(BaseModel):
    expected_version: int = Field(..., ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=36)
    replacement_idempotency_key: str = Field(..., min_length=8, max_length=36)
    workcenter_code: str = Field(..., min_length=1, max_length=128)
    bucket_start: datetime
    bucket_end: datetime
    timezone: str = Field(..., min_length=1, max_length=64)
    quantity_minutes: int = Field(..., gt=0)
    workload_source: WorkloadSource
    workload_source_reference: str | None = Field(default=None, max_length=255)
    workload_explanation: str | None = Field(default=None, max_length=500)
    initial_status: CapacityInitialStatus = "ALLOCATED"
    expected_source_version: int | None = Field(default=None, ge=1)
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_note: str | None = Field(default=None, max_length=500)
    correlation_id: str | None = Field(default=None, max_length=64)


class OverAllocationDetail(BaseModel):
    over_allocated: bool
    available_minutes: int
    allocated_before: int
    requested_minutes: int
    allocated_after: int
    excess_minutes: int
    workcenter_code: str
    bucket_start: datetime
    bucket_end: datetime
    policy: Literal["WARN_ONLY", "HARD_BLOCK", "ALLOW_WITH_REASON"]
    reason_code: str | None = None


class AllocationCommandResult(BaseModel):
    allocation_id: int
    execution_plan_id: int
    task_key: str
    workcenter_code: str
    status: CapacityStatus
    version: int
    quantity_minutes: int
    unit: Literal["minutes"] = "minutes"
    bucket_start: datetime
    bucket_end: datetime
    timezone: str
    workload_source: WorkloadSource | None = None
    operation: CapacityOperation
    transition_id: str
    previous_status: CapacityStatus | None = None
    previous_version: int | None = None
    already_applied: bool = False
    over_allocation: OverAllocationDetail | None = None
    replacement_allocation_id: int | None = None
    replacement_transition_id: str | None = None
