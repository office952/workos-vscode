"""Resource State R6 — read-only evaluation contracts.

Evaluation states (CLEAR/ACTIVE/UNKNOWN/NOT_CONFIGURED) are derived at read
time. Configuration status ACTIVE/DISABLED is a separate persisted concept.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ResourceDomain = Literal[
    "SCHEDULING", "MACHINE_RESERVATION", "CAPACITY_ALLOCATION"
]
DomainEvaluationState = Literal["CLEAR", "ACTIVE", "UNKNOWN", "NOT_CONFIGURED"]
AggregateEvaluationState = Literal[
    "CLEAR",
    "BLOCKED_ACTIVE",
    "BLOCKED_UNKNOWN",
    "BLOCKED_NOT_CONFIGURED",
]


class DomainResourceStateResult(BaseModel):
    domain: ResourceDomain
    state: DomainEvaluationState
    configured: bool
    configuration_id: int | None = None
    configuration_version: int | None = None
    source_record_ids: list[int] = Field(default_factory=list)
    reason_code: str
    evaluated_at: datetime


class TaskResourceStateResult(BaseModel):
    plan_id: int
    order_id: int | None = None
    task_key: str
    scheduling: DomainResourceStateResult
    machine_reservation: DomainResourceStateResult
    capacity_allocation: DomainResourceStateResult
    aggregate: AggregateEvaluationState
    aggregate_reason_code: str
    evaluated_at: datetime
