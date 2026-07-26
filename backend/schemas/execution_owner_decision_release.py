"""Execution owner-decision production release gate schemas (Wave 5 / W5-T01)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PRODUCTION_RELEASE_POLICY = "ORDER_AND_PLAN_ALLOWED_TASK_START_BLOCKED"

ReleaseStatus = Literal[
    "RELEASE_ALLOWED",
    "RELEASE_BLOCKED_OWNER_DECISIONS",
    "RELEASE_BLOCKED_MISSING_RUNTIME_RESOLUTION",
    "RELEASE_BLOCKED_POLICY_ERROR",
    "NOT_PROVEN",
]

OwnerDecisionOperationalStatus = Literal[
    "unresolved",
    "acknowledged",
    "resolved",
    "waived",
]

FrozenDecisionClassification = Literal[
    "production_blocking",
    "nonblocking_internal_analysis",
    "unclassified",
]


class OwnerDecisionReleaseBlocker(BaseModel):
    code: str
    label: str
    scope: str = "order"
    required_action: str
    acknowledgement_sufficient: bool = False
    requires_resolution: bool = True
    operational_status: OwnerDecisionOperationalStatus = "unresolved"
    frozen_classification: FrozenDecisionClassification = "production_blocking"


class ProductionReleaseEvaluation(BaseModel):
    release_status: ReleaseStatus
    policy: str = PRODUCTION_RELEASE_POLICY
    order_id: int | None = None
    blockers: list[OwnerDecisionReleaseBlocker] = Field(default_factory=list)
    frozen_decision_codes: list[str] = Field(default_factory=list)
    nonblocking_decision_codes: list[str] = Field(default_factory=list)
    message: str | None = None


class OwnerDecisionResolutionRequest(BaseModel):
    status: OwnerDecisionOperationalStatus
    note: str = Field(min_length=3, max_length=2000)


class OwnerDecisionResolutionResult(BaseModel):
    order_id: int
    code: str
    operational_status: OwnerDecisionOperationalStatus
    release_status: ReleaseStatus
    idempotent: bool = False
    audit_event_id: str | None = None
