"""PRODUCT_PRICE_BREAKDOWN_V1 — read-model over CPP + EIC + recipe (no second calculator)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

PRODUCT_PRICE_BREAKDOWN_VERSION = "1.0.0"

LineGroup = Literal[
    "material",
    "machine",
    "labor",
    "service",
    "ai_decision",
    "adjustment",
    "commercial",
    "internal",
]

SourceType = Literal[
    "market",
    "catalog",
    "owner",
    "AI_DECISION",
    "measured",
    "legacy",
    "documented_commercial",
    "inventory",
    "unknown",
]


class PriceBreakdownLine(BaseModel):
    line_id: str
    line_group: LineGroup
    resource_code: str
    display_name: str
    quantity_key: Optional[str] = None
    formula_display: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    base_value: Optional[float] = None
    currency: Optional[str] = None
    source_type: SourceType = "unknown"
    source_id: Optional[str] = None
    minimum: Optional[float] = None
    waste: Optional[float] = None
    adjustment: Optional[float] = None
    internal_cost: Optional[float] = None
    commercial_value: Optional[float] = None
    cpp_line: Optional[str] = None
    eic_rule: Optional[str] = None
    configurable: bool = False
    warning: Optional[str] = None
    confidence: Optional[str] = None
    rationale_ro: Optional[str] = None
    ai_decision_id: Optional[str] = None
    # MATERIAL_MARKET_PRICE_REGISTRY_V1 — additive purchase provenance
    material_source_type: Optional[str] = None
    material_supplier: Optional[str] = None
    material_freshness: Optional[str] = None
    material_effective_from: Optional[str] = None
    material_normalization_formula: Optional[str] = None
    material_normalized_unit: Optional[str] = None
    material_normalized_price: Optional[float] = None
    material_canonical: Optional[bool] = None


class PriceBreakdownGroupTotal(BaseModel):
    line_group: LineGroup
    line_count: int = 0
    internal_subtotal: Optional[float] = None
    commercial_subtotal: Optional[float] = None
    currency: Optional[str] = None


class PriceBreakdownTotals(BaseModel):
    material_internal: Optional[float] = None
    machine_internal: Optional[float] = None
    labor_internal: Optional[float] = None
    service_internal: Optional[float] = None
    consumables_internal: Optional[float] = None
    overhead_internal: Optional[float] = None
    ai_contribution_note_ro: Optional[str] = None
    internal_total: Optional[float] = None
    commercial_subtotal: Optional[float] = None
    commercial_total: Optional[float] = None
    currency: str = "RON"
    cpp_total_matches: bool = False
    eic_total_matches: bool = False
    no_duplicate_commercial_codes: bool = True
    no_duplicate_internal_codes: bool = True


class PriceBreakdownCalibrationHook(BaseModel):
    """Secondary time/calibration metadata — not required for totals."""

    line_code: Optional[str] = None
    estimated_minutes: Optional[float] = None
    purpose: Optional[str] = None
    excluded_from_total: bool = True
    note_ro: str = "Timpul este evidență secundară pentru calibrare, nu baza de cost."


class ProductPriceBreakdownResponse(BaseModel):
    schema_version: str = PRODUCT_PRICE_BREAKDOWN_VERSION
    template_code: str
    configuration_id: str
    fixture_id: Optional[str] = None
    currency: str = "RON"
    ownership_note_ro: str = (
        "Linia de referință a laboratorului: Cost producție (EIC). "
        "Preț comercial (CPP) rămâne vizibil pentru reconciliere, nu ca ofertă. "
        "Desfășurătorul nu recalculează. Materialele folosesc cost achiziție. "
        "Manopera folosește driveri fizici. Timpul e secundar. "
        "Fără adaos / ofertă / comandă în finish line."
    )
    publication_status: Optional[str] = None
    operational_readiness: Optional[str] = None
    uses_ai_defaults: bool = False
    configuration_summary: dict[str, Any] = Field(default_factory=dict)
    lines: list[PriceBreakdownLine] = Field(default_factory=list)
    group_totals: list[PriceBreakdownGroupTotal] = Field(default_factory=list)
    totals: PriceBreakdownTotals = Field(default_factory=PriceBreakdownTotals)
    ai_decisions: list[dict[str, Any]] = Field(default_factory=list)
    calibration_hooks: list[PriceBreakdownCalibrationHook] = Field(default_factory=list)
    cpp_status: Optional[str] = None
    eic_status: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    eic_provenance: list[dict[str, Any]] = Field(default_factory=list)
    cpp_provenance: list[dict[str, Any]] = Field(default_factory=list)
    acm_treatments_blocked: Optional[bool] = None
