"""Template Lifecycle Control System V1 — derived read models (no parallel registry)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

LifecycleStageCode = Literal[
    "PRODUCT_FAMILY",
    "PRODUCT_TEMPLATE",
    "COMPONENT_TEMPLATES",
    "INTERFACE_CONTRACTS",
    "INTAKE_AVAILABILITY",
    "INTAKE_STEP_1",
    "INTAKE_STEP_2",
    "FINISH_SETUP",
    "PRODUCT_DEFINITION",
    "PRODUCT_AGGREGATE",
    "CPP",
    "OFFER",
    "ORDER_SNAPSHOT",
    "TASK_RULES_PROJECTION",
    "TASK_MATERIALIZATION",
    "EXECUTION",
    "RUNTIME_PROOF",
]

LifecycleStatus = Literal[
    "NOT_APPLICABLE",
    "NOT_STARTED",
    "DISCOVERED",
    "CONFIGURED",
    "WIRED",
    "VALIDATED",
    "PREVIEW_ONLY",
    "OWNER_GATE_REQUIRED",
    "BLOCKED",
    "PASS",
    "DEPRECATED",
]

LifecycleIssueSeverity = Literal["blocking", "warning", "diagnostic"]


class LifecycleIssue(BaseModel):
    code: str
    severity: LifecycleIssueSeverity = "blocking"
    message: str
    evidence: list[str] = Field(default_factory=list)


class LifecycleStageResult(BaseModel):
    stage: LifecycleStageCode
    owner_label: str
    authority: str
    required: bool = True
    status: LifecycleStatus
    evidence: list[str] = Field(default_factory=list)
    warnings: list[LifecycleIssue] = Field(default_factory=list)
    blockers: list[LifecycleIssue] = Field(default_factory=list)
    owner_gate: str | None = None
    affected_files: list[str] = Field(default_factory=list)
    affected_tests: list[str] = Field(default_factory=list)
    runtime_proof: list[str] = Field(default_factory=list)


class LifecycleOwnerGate(BaseModel):
    code: str
    label: str
    status: LifecycleStatus
    reason: str
    stage: LifecycleStageCode | None = None


class LifecycleLegacyConflict(BaseModel):
    code: str
    classification: Literal[
        "read_only_compatibility",
        "migration_required",
        "forbidden_for_new_data",
        "dead_candidate",
        "owner_decision_required",
    ]
    message: str
    evidence: list[str] = Field(default_factory=list)


class LifecycleImpactSummary(BaseModel):
    changed: str
    affected_product_templates: list[str] = Field(default_factory=list)
    affected_intake: list[str] = Field(default_factory=list)
    affected_product_definition: list[str] = Field(default_factory=list)
    affected_product_aggregate: list[str] = Field(default_factory=list)
    cpp: list[str] = Field(default_factory=list)
    tasking: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class TemplateLifecycleReadiness(BaseModel):
    """Derived projection — Product System remains authority."""

    schema_version: str = "template_lifecycle_control_v1"
    template_code: str
    version: str | None = None
    family_id: str | None = None
    family_name: str | None = None
    template_status: str
    lifecycle_status: LifecycleStatus
    readiness_score: int = Field(ge=0, le=100)
    activation_eligible: bool = False
    stages: list[LifecycleStageResult] = Field(default_factory=list)
    owner_gates: list[LifecycleOwnerGate] = Field(default_factory=list)
    impact_summary: LifecycleImpactSummary | None = None
    legacy_conflicts: list[LifecycleLegacyConflict] = Field(default_factory=list)
    stage_counts: dict[str, int] = Field(default_factory=dict)
    derived_from: list[str] = Field(default_factory=list)


class TemplateLifecycleImpactResponse(BaseModel):
    schema_version: str = "template_lifecycle_impact_v1"
    template_code: str
    reverse_dependencies: dict[str, list[str]] = Field(default_factory=dict)
    impact: LifecycleImpactSummary


class TemplateLifecycleValidateItem(BaseModel):
    template_code: str
    lifecycle_status: LifecycleStatus
    readiness_score: int
    activation_eligible: bool
    blocking_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)


class TemplateLifecycleValidateResponse(BaseModel):
    schema_version: str = "template_lifecycle_validate_v1"
    ok: bool
    checked: int
    failed: int
    items: list[TemplateLifecycleValidateItem] = Field(default_factory=list)
    fail_reasons: list[str] = Field(default_factory=list)


class TemplateLifecycleInspectResponse(BaseModel):
    readiness: TemplateLifecycleReadiness
    impact: TemplateLifecycleImpactResponse
    raw_context: dict[str, Any] = Field(default_factory=dict)
