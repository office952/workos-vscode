"""CommercialPriceProposal read-only preview schema (Step 7G)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

COMMERCIAL_PRICE_PROPOSAL_PREVIEW_VERSION = "1.0.0"
COMMERCIAL_PRICE_PROPOSAL_SOURCE = "commercial_price_proposal"

CommercialProposalStatus = Literal["ready", "partial", "blocked"]
CommercialBasisType = Literal[
    "m2",
    "ml",
    "piece",
    "letter",
    "set",
    "fixed",
    "minimum",
    "complexity",
    "unknown",
]


class CommercialPriceLine(BaseModel):
    code: str
    label: str
    module_code: str | None = None
    component_code: str | None = None
    basis_type: CommercialBasisType
    quantity: float | int | None = None
    unit: str | None = None
    commercial_unit_price: float | None = None
    subtotal: float | None = None
    pricing_rule_code: str
    source: str
    owner_decision_required: bool = False
    warnings: list[str] = Field(default_factory=list)
    # Linked-child provenance (logo segments under letters root). Optional for letter lines.
    segment_key: str | None = None
    layer_identity: str | None = None
    linked_template_code: str | None = None
    # Registry reuse provenance (mapping to existing workcenter_rates / Pricing Registry).
    registry_pricing_code: str | None = None
    source_currency: str | None = None
    cpp_currency: str | None = None
    currency_conversion_rate: float | None = None
    currency_conversion_source: str | None = None


class CommercialMinimumApplied(BaseModel):
    code: str
    label: str
    detail: str | None = None


class CommercialComplexityAdjustment(BaseModel):
    code: str
    label: str
    multiplier: float | None = None
    detail: str | None = None


class CommercialOwnerDecision(BaseModel):
    code: str
    label: str
    module_code: str | None = None
    detail: str | None = None


class CommercialBlocker(BaseModel):
    code: str
    message: str
    module_code: str | None = None


class CommercialProvenanceEntry(BaseModel):
    key: str
    source: str
    detail: str


class CommercialPriceProposalPreview(BaseModel):
    preview_version: str = COMMERCIAL_PRICE_PROPOSAL_PREVIEW_VERSION
    template_code: str
    source: str = COMMERCIAL_PRICE_PROPOSAL_SOURCE
    status: CommercialProposalStatus = "partial"
    commercial_price_lines: list[CommercialPriceLine] = Field(default_factory=list)
    subtotal_commercial: float | None = None
    commercial_total: float | None = None
    currency: str = "RON"
    minimums_applied: list[CommercialMinimumApplied] = Field(default_factory=list)
    complexity_adjustments: list[CommercialComplexityAdjustment] = Field(default_factory=list)
    unknown_owner_decisions: list[CommercialOwnerDecision] = Field(default_factory=list)
    commercial_blockers: list[CommercialBlocker] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    forbidden_hourly_usage_detected: list[str] = Field(default_factory=list)
    provenance: list[CommercialProvenanceEntry] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"
    quote_ready_for_commercial_review: bool = False
    notes: list[str] = Field(default_factory=list)
    input_summary: dict[str, Any] = Field(default_factory=dict)
