"""Post-job truth read contract — plan vs reality + profitability coverage (V1)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

DataPresence = Literal[
    "present",
    "missing",
    "not_captured",
    "not_applicable",
    "excluded",
    "still_active",
    "zero",
    "partial",
    "complete",
]

CostCoverageStatus = Literal[
    "COMPLETE",
    "PARTIAL",
    "INCOMPLETE",
    "NOT_AVAILABLE",
]

ProfitabilityTruthStatus = Literal[
    "COMPLETE",
    "PARTIAL",
    "INCOMPLETE",
    "NOT_AVAILABLE",
]


class PresenceValue(BaseModel):
    """Scalar with explicit presence so missing is never confused with zero."""

    value: float | int | str | bool | None = None
    presence: DataPresence
    unit: str | None = None
    source: str | None = None
    note: str | None = None


class PostJobBaseline(BaseModel):
    revenue_net: PresenceValue
    planned_internal_cost: PresenceValue
    currency: str | None = None
    revenue_source: str
    has_snapshot_v2: bool
    snapshot_version: int | None = None


class LaborSessionRow(BaseModel):
    session_id: str
    task_id: str | None = None
    employee_id: int | None = None
    employee_name: str | None = None
    role: str | None = None
    session_type: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    actual_minutes: float | None = None
    status: str
    completeness: DataPresence


class LaborActuals(BaseModel):
    closed_minutes_total: PresenceValue
    open_session_count: int = 0
    session_count: int = 0
    planned_minutes_total: PresenceValue
    variance_minutes: PresenceValue
    sessions: list[LaborSessionRow] = Field(default_factory=list)
    monetary_cost: PresenceValue
    completeness: DataPresence


class MaterialActualLine(BaseModel):
    material_id: int | None = None
    material_name: str | None = None
    material_code: str | None = None
    task_id: str | None = None
    planned_quantity: PresenceValue
    actual_deducted_quantity: PresenceValue
    unit: str | None = None
    planned_internal_cost: PresenceValue
    actual_known_internal_cost: PresenceValue
    quantity_variance: PresenceValue
    cost_variance: PresenceValue
    valuation_method: str | None = None
    source: str
    movement_id: int | None = None
    performed_at: str | None = None
    completeness: DataPresence


class MaterialActuals(BaseModel):
    lines: list[MaterialActualLine] = Field(default_factory=list)
    observed_row_count: int = 0
    deducted_movement_count: int = 0
    known_actual_cost_total: PresenceValue
    valuation_method: str | None = None
    completeness: DataPresence


class MachineActualItem(BaseModel):
    task_id: str | None = None
    planned_machine_id: str | None = None
    planned_machine_type: str | None = None
    status: DataPresence
    note: str | None = None


class MachineActuals(BaseModel):
    items: list[MachineActualItem] = Field(default_factory=list)
    completeness: DataPresence
    note: str | None = None


class QuantityActuals(BaseModel):
    tasks_planned: PresenceValue
    tasks_completed: PresenceValue
    progress_percent: PresenceValue
    completed_quantity: PresenceValue
    completeness: DataPresence


class ReconciliationVariance(BaseModel):
    dimension: str
    planned_value: float | int | str | None = None
    actual_value: float | int | str | None = None
    absolute_variance: float | None = None
    percentage_variance: float | None = None
    unit: str | None = None
    source: str
    status: DataPresence
    explanation_code: str
    data_completeness: DataPresence


ReconciliationOpState = Literal[
    "matched",
    "partial",
    "missing_actual",
    "variance",
]


class OperationReconciliationRow(BaseModel):
    task_id: str
    task_name: str | None = None
    planned_status: str | None = None
    actual_status: str | None = None
    planned_minutes: PresenceValue
    actual_minutes: PresenceValue
    variance_minutes: PresenceValue
    planned_quantity: PresenceValue
    actual_quantity: PresenceValue
    quantity_variance: PresenceValue
    reconciliation_state: ReconciliationOpState
    completeness: DataPresence


class ReconciliationSummary(BaseModel):
    """Compact operation reconciliation counts for operator UI."""

    matched_count: int = 0
    partial_count: int = 0
    missing_actual_count: int = 0
    variance_count: int = 0
    operations_total: int = 0


class ReconciliationBlock(BaseModel):
    variances: list[ReconciliationVariance] = Field(default_factory=list)
    operations: list[OperationReconciliationRow] = Field(default_factory=list)
    summary: ReconciliationSummary = Field(default_factory=ReconciliationSummary)


class ProfitabilityCoverage(BaseModel):
    revenue_net: PresenceValue
    planned_internal_cost: PresenceValue
    known_actual_cost: PresenceValue
    known_actual_margin: PresenceValue
    known_actual_margin_percent: PresenceValue
    cost_coverage_status: CostCoverageStatus
    profitability_status: ProfitabilityTruthStatus
    included_cost_components: list[str] = Field(default_factory=list)
    excluded_cost_components: list[str] = Field(default_factory=list)
    missing_actual_components: list[str] = Field(default_factory=list)
    wording: list[str] = Field(default_factory=list)
    false_final_profit_forbidden: bool = True


class MissingDataItem(BaseModel):
    code: str
    dimension: str
    message: str
    blocking_for_complete_profitability: bool = True


class PostJobTruthResponse(BaseModel):
    """Cohesive read model for /execution/:orderId post-job truth."""

    contract_version: Literal["post_job_truth_v1"] = "post_job_truth_v1"
    order_id: int
    order_code: str
    baseline: PostJobBaseline
    labor: LaborActuals
    materials: MaterialActuals
    machines: MachineActuals
    quantity: QuantityActuals
    reconciliation: ReconciliationBlock
    profitability: ProfitabilityCoverage
    missing_data: list[MissingDataItem] = Field(default_factory=list)
    sources: dict[str, Any] = Field(default_factory=dict)
    retroactive_change_allowed: bool = False
    write_back_performed: bool = False
