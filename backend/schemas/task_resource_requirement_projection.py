"""Read-only Task Resource Requirement projection contracts.

Informational demand visibility only — not Resource State CLEAR/ACTIVE,
not commitment, not Phase B gates.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ResourceRequirementsStatus = Literal[
    "KNOWN_MINIMAL",
    "PARTIAL",
    "UNKNOWN",
    "NOT_APPLICABLE",
]

ResourceModeHint = Literal[
    "MACHINE_BOUND",
    "MANUAL_WORKSPACE",
    "PERSON_DRIVEN",
    "FIELD",
    "UNKNOWN",
]

ProvenanceSource = Literal[
    "EXECUTION_PLAN_SNAPSHOT",
    "WORKCENTER_REGISTRY",
    "OPERATION_CONTRACT",
    "PRODUCT_AGGREGATE_DERIVED",
    "LEGACY_INFERENCE",
    "UNKNOWN",
]

ConfidenceCategory = Literal["CONFIRMED", "SAFE_DERIVATION", "UNKNOWN"]


class FieldProvenance(BaseModel):
    field: str
    source: ProvenanceSource
    derived: bool = False
    confidence: ConfidenceCategory = "CONFIRMED"


class TaskResourceRequirementProjection(BaseModel):
    execution_plan_id: int
    task_key: str
    operation_code: str | None = None
    workcenter_code: str | None = None
    workcenter_label: str | None = None
    estimated_time_minutes: float | None = None
    planning_minutes_source: str | None = None
    # Authoritative when stamped on EP snapshot; else null (soft hint remains separate).
    resource_mode: ResourceModeHint | None = None
    machine_capability_code: str | None = None
    batch_eligible: bool | None = None
    resource_requirements_status: ResourceRequirementsStatus
    resource_mode_hint: ResourceModeHint
    known_fields: list[str] = Field(default_factory=list)
    unknown_fields: list[str] = Field(default_factory=list)
    derived_fields: list[str] = Field(default_factory=list)
    source_provenance: list[FieldProvenance] = Field(default_factory=list)


class PlanResourceRequirementSummary(BaseModel):
    total_tasks: int
    known_minimal: int = 0
    partial: int = 0
    unknown: int = 0
    not_applicable: int = 0
    duration_known: int = 0
    duration_unknown: int = 0
    safe_mode_hint: int = 0
    hybrid_unknown_mode: int = 0


class PlanResourceRequirementProjection(BaseModel):
    execution_plan_id: int
    order_id: int | None = None
    summary: PlanResourceRequirementSummary
    tasks: list[TaskResourceRequirementProjection] = Field(default_factory=list)
