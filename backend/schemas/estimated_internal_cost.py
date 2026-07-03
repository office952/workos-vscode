"""EstimatedInternalCost read-only preview schema (Step 7H)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ESTIMATED_INTERNAL_COST_PREVIEW_VERSION = "1.0.0"
ESTIMATED_INTERNAL_COST_SOURCE = "estimated_internal_cost"

InternalCostStatus = Literal["ready", "partial", "blocked"]
InternalLineType = Literal["material", "operation", "consumable", "overhead", "capacity_hint"]
InternalBasisType = Literal[
    "m2",
    "ml",
    "piece",
    "set",
    "fixed",
    "percentage",
    "inventory_unit_cost",
    "unknown",
]
CapacityHintPurpose = Literal["capacity", "sanity_check", "planning_hint"]


class EstimatedInternalCostLine(BaseModel):
    code: str
    label: str
    module_code: str | None = None
    component_code: str | None = None
    line_type: InternalLineType
    basis_type: InternalBasisType
    quantity: float | int | None = None
    unit: str | None = None
    internal_unit_cost: float | None = None
    subtotal: float | None = None
    rule_code: str
    source: str
    owner_decision_required: bool = False
    warnings: list[str] = Field(default_factory=list)


class CapacityHint(BaseModel):
    code: str
    label: str
    estimated_minutes: float | None = None
    source: str
    purpose: CapacityHintPurpose = "capacity"
    excluded_from_total: bool = True


class InternalBlocker(BaseModel):
    code: str
    message: str
    module_code: str | None = None
    material_code: str | None = None


class InternalOwnerDecision(BaseModel):
    code: str
    label: str
    module_code: str | None = None
    detail: str | None = None


class InternalProvenanceEntry(BaseModel):
    key: str
    source: str
    detail: str


class EstimatedInternalCostPreview(BaseModel):
    preview_version: str = ESTIMATED_INTERNAL_COST_PREVIEW_VERSION
    template_code: str
    source: str = ESTIMATED_INTERNAL_COST_SOURCE
    status: InternalCostStatus = "partial"
    estimated_material_lines: list[EstimatedInternalCostLine] = Field(default_factory=list)
    estimated_operation_lines: list[EstimatedInternalCostLine] = Field(default_factory=list)
    estimated_consumable_lines: list[EstimatedInternalCostLine] = Field(default_factory=list)
    estimated_overhead_lines: list[EstimatedInternalCostLine] = Field(default_factory=list)
    capacity_hints: list[CapacityHint] = Field(default_factory=list)
    estimated_material_cost: float | None = None
    estimated_operation_cost: float | None = None
    estimated_consumables_cost: float | None = None
    estimated_overhead_cost: float | None = None
    estimated_total_internal_cost: float | None = None
    currency: str = "RON"
    internal_blockers: list[InternalBlocker] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    unknown_owner_decisions: list[InternalOwnerDecision] = Field(default_factory=list)
    hourly_contamination_detected: list[str] = Field(default_factory=list)
    provenance: list[InternalProvenanceEntry] = Field(default_factory=list)
    completeness: float = 0.0
    confidence: Literal["high", "medium", "low"] = "medium"
    ready_for_quote_snapshot: bool = False
    notes: list[str] = Field(default_factory=list)
    input_summary: dict[str, Any] = Field(default_factory=dict)
