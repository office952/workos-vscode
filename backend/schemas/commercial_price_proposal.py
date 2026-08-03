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
    # Commercial product ownership (F7F) — letters and the ACM panel are separate products.
    commercial_product_key: str | None = None
    # F7H — publication honesty for configurable rates (never invent Owner-final status).
    rate_publication_status: Literal["owner_confirmed", "provisional", "unpublished"] | None = None


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


class CommercialCurrencyBucket(BaseModel):
    """One honest per-currency subtotal. Currencies are never fused without an explicit rate."""

    currency: str
    subtotal: float


class CommercialProductSubtotal(BaseModel):
    product_key: str
    label: str
    line_codes: list[str] = Field(default_factory=list)
    subtotals_by_currency: list[CommercialCurrencyBucket] = Field(default_factory=list)
    blocked: bool = False
    blocker_codes: list[str] = Field(default_factory=list)
    # Lines that carry no price yet because an Owner decision is pending. They do not block the
    # offer, but any subtotal that omits them is partial and must be labelled as such.
    pending_line_codes: list[str] = Field(default_factory=list)


class CommercialProductBreakdown(BaseModel):
    """F7F Step 3 contract: per-product subtotals plus one honest complete offer total.

    `complete_offer_total` is emitted only when every priced line resolves to a single
    currency and no product is blocked. Mixed currencies are never summed: there is no
    automatic EUR->RON conversion, no live FX and no default rate in this engine.
    """

    products: list[CommercialProductSubtotal] = Field(default_factory=list)
    subtotals_by_currency: list[CommercialCurrencyBucket] = Field(default_factory=list)
    currency_mix_detected: bool = False
    # F7H scoped presentation currency (EUR for volumetric+ACM pilot; never a global default).
    presentation_currency: str | None = None
    complete_offer_total: float | None = None
    complete_offer_total_currency: str | None = None
    complete_offer_total_unavailable_reason: str | None = None
    complete_offer_total_is_partial: bool = False
    pending_line_codes: list[str] = Field(default_factory=list)
    tax_status: Literal["tax_exclusive"] = "tax_exclusive"
    vat_policy_source: str | None = None
    vat_rate_percent: float | None = None


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
    # F7F: per-product subtotals + honest complete offer total. `subtotal_commercial` /
    # `commercial_total` above stay as the pre-F7F fused figure for backwards compatibility;
    # operator-facing surfaces must read `commercial_product_breakdown`.
    commercial_product_breakdown: CommercialProductBreakdown | None = None
