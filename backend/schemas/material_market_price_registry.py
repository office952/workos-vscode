"""MATERIAL_MARKET_PRICE_REGISTRY_V1 — read-model over Inventory purchase truth."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

MATERIAL_MARKET_PRICE_REGISTRY_VERSION = "1.0.0"

SourceType = Literal[
    "MEASURED_LANDED_COST",
    "PURCHASE_INVOICE",
    "SUPPLIER_OFFER",
    "OWNER_CONFIRMED",
    "SUPPLIER_CATALOG",
    "TEMPORARY_AI_FALLBACK",
    "LEGACY",
    "MISSING",
]

FreshnessStatus = Literal[
    "CURRENT",
    "REVIEW_SOON",
    "STALE",
    "EXPIRED",
    "UNKNOWN_DATE",
]


class MaterialPriceNormalization(BaseModel):
    raw_unit: Optional[str] = None
    raw_price: Optional[float] = None
    currency: Optional[str] = None
    normalized_unit: Optional[str] = None
    normalized_price: Optional[float] = None
    sheet_width_mm: Optional[float] = None
    sheet_height_mm: Optional[float] = None
    sheet_area_m2: Optional[float] = None
    formula_display: Optional[str] = None
    conversion_applied: bool = False
    note_ro: Optional[str] = None


class MaterialPriceHistoryPoint(BaseModel):
    history_id: int
    unit_cost: Optional[float] = None
    currency: Optional[str] = None
    vat_percent: Optional[float] = None
    valid_from: Optional[str] = None
    changed_at: Optional[str] = None
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None
    snapshot_source: Optional[str] = None


class MaterialMarketPriceRecord(BaseModel):
    material_code: str
    display_name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    variant: Optional[str] = None
    inventory_status: Optional[str] = None
    stock_current: Optional[float] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    supplier_sku: Optional[str] = None
    source_type: SourceType = "MISSING"
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_date: Optional[str] = None
    source_notes: Optional[str] = None
    source_review_status: Optional[str] = None
    effective_from: Optional[str] = None
    raw_unit: Optional[str] = None
    raw_price: Optional[float] = None
    currency: Optional[str] = None
    vat_percent: Optional[float] = None
    vat_included: bool = False
    landed_cost: Optional[float] = None
    normalization: MaterialPriceNormalization = Field(
        default_factory=MaterialPriceNormalization
    )
    preferred: bool = True
    freshness: FreshnessStatus = "UNKNOWN_DATE"
    freshness_policy_ro: Optional[str] = None
    confidence: Literal["high", "medium", "low"] = "medium"
    temporary_ai_fallback: bool = False
    canonical: bool = True
    blocker: Optional[str] = None
    warning: Optional[str] = None
    active_templates: list[str] = Field(default_factory=list)
    history: list[MaterialPriceHistoryPoint] = Field(default_factory=list)
    inventory_href: str = ""
    pricing_href: str = "/inventory/pricing"


class MaterialMarketPriceSummary(BaseModel):
    total: int = 0
    priced: int = 0
    missing: int = 0
    stale: int = 0
    review_soon: int = 0
    unknown_date: int = 0
    with_supplier: int = 0
    active_template_critical_missing: int = 0
    temporary_ai_fallback: int = 0


class MaterialMarketPriceRegistryResponse(BaseModel):
    schema_version: str = MATERIAL_MARKET_PRICE_REGISTRY_VERSION
    ownership_note_ro: str = (
        "Inventory deține identitatea materialului. "
        "Pricing expune sursa de achiziție și normalizarea. "
        "AI nu este autoritate finală pentru preț material."
    )
    source_precedence: list[str] = Field(default_factory=list)
    freshness_policy: dict[str, Any] = Field(default_factory=dict)
    summary: MaterialMarketPriceSummary = Field(
        default_factory=MaterialMarketPriceSummary
    )
    items: list[MaterialMarketPriceRecord] = Field(default_factory=list)
    critical_missing: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
