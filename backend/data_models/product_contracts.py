"""
Canonical contracts (DTOs) for the WorkOS flow:
REQUEST -> PRODUCT DEFINITION -> COST -> OFFER -> ORDER.

RULES (from spec atoms-dev.txt):
  1. ProductSystem defines the product, NOT the cost.
  2. CostEngine calculates the cost, does NOT modify the product.
  3. Quotes orchestrates commercial rules, does NOT contain cost formulas.
  4. Orders creates an immutable snapshot, does NOT recalculate.
  5. Missing data MUST be marked explicitly — no silent fallbacks.

These dataclasses are the single-source-of-truth data shapes exchanged between
ProductSystemService -> CostEngineService -> QuotesOrchestrator -> OrderSnapshotBuilder.
They MUST remain pure data containers (no business logic on them).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

# ---------------------------------------------------------------------------
# PRODUCT DEFINITION
# ---------------------------------------------------------------------------

LayerType = Literal["front", "back", "structure", "lighting", "graphic"]
MaterialUnit = Literal["mm", "sqm", "ml", "pcs"]
ComponentUnit = Literal["pcs", "ml", "sqm"]
ProcessType = Literal["cut", "print", "cnc", "assembly", "wiring"]


@dataclass
class ProductDimensions:
    width_mm: float = 0
    height_mm: float = 0
    depth_mm: float = 0


@dataclass
class ProductMaterial:
    material_id: str = ""
    name: str = ""
    unit: str = "pcs"  # MaterialUnit, but kept as str for JSON-friendliness


@dataclass
class ProductComponent:
    component_id: str = ""
    type: str = ""
    quantity: float = 0
    unit: str = "pcs"  # ComponentUnit


@dataclass
class ProductProcess:
    process_id: str = ""
    type: str = ""  # ProcessType
    machine_type: Optional[str] = None
    estimated_time_minutes: float = 0


@dataclass
class ProductLayer:
    layer_id: str = ""
    layer_type: str = "structure"  # LayerType
    material: ProductMaterial = field(default_factory=ProductMaterial)
    thickness_mm: float = 0
    finish: str = ""
    components: List[ProductComponent] = field(default_factory=list)
    processes: List[ProductProcess] = field(default_factory=list)


@dataclass
class ProductValidationResult:
    is_valid: bool = True
    missing_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ProductDefinition:
    """Canonical blueprint of a product. Produced by ProductSystemService.
    MUST NOT carry any cost figures."""

    product_id: str = ""
    product_type: str = ""
    quantity: int = 1
    dimensions: ProductDimensions = field(default_factory=ProductDimensions)
    layers: List[ProductLayer] = field(default_factory=list)
    validation: ProductValidationResult = field(default_factory=ProductValidationResult)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# COST
# ---------------------------------------------------------------------------

CostLineType = Literal["material", "labour", "machine", "external", "overhead"]


@dataclass
class CostLine:
    type: str = "material"  # CostLineType
    name: str = ""
    quantity: float = 0
    unit: str = ""
    unit_cost: float = 0
    total: float = 0


@dataclass
class CostValidation:
    missing_cost_data: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class PricingContext:
    currency: str = "RON"
    location: str = "RO"
    overhead_profile_id: str = "default"


@dataclass
class CostRequest:
    product_definition: ProductDefinition = field(default_factory=ProductDefinition)
    pricing_context: PricingContext = field(default_factory=PricingContext)


@dataclass
class CostResult:
    """Canonical cost truth. Produced by CostEngineService.
    MUST NOT contain commercial decisions (margin, discount, vat)."""

    is_valid: bool = True
    currency: str = "RON"
    materials_cost: float = 0
    labour_cost: float = 0
    machine_cost: float = 0
    external_cost: float = 0
    overhead_cost: float = 0
    total_cost: float = 0
    estimated_time_minutes: float = 0
    breakdown: List[CostLine] = field(default_factory=list)
    validation: CostValidation = field(default_factory=CostValidation)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# QUOTE / ORDER SNAPSHOTS
# ---------------------------------------------------------------------------

QuoteStatus = Literal["draft", "priced", "blocked"]


@dataclass
class QuotePricing:
    margin_pct: float = 0
    discount_pct: float = 0
    vat_pct: float = 19


@dataclass
class QuotePrice:
    net: float = 0
    gross: float = 0
    final: float = 0


@dataclass
class QuoteCalculationSnapshot:
    """Commercial snapshot. Produced by Quotes orchestrator.
    Does NOT contain cost formulas — only commercial transforms applied on
    top of an existing CostResult.
    
    Includes optional readiness snapshot captured at quote pricing time.
    readiness_result populated by ProductReadinessService.evaluate()."""

    product_definition: ProductDefinition = field(default_factory=ProductDefinition)
    cost_result: CostResult = field(default_factory=CostResult)
    pricing: QuotePricing = field(default_factory=QuotePricing)
    price: QuotePrice = field(default_factory=QuotePrice)
    status: str = "draft"  # QuoteStatus
    blocked_reasons: List[str] = field(default_factory=list)
    template_id: Optional[int] = None  # Product template identity for readiness lookup
    readiness_result: Optional[Dict[str, Any]] = None  # Canonical readiness snapshot from ProductReadinessService

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OrderFinalPrice:
    net: float = 0
    gross: float = 0


@dataclass
class OrderSnapshot:
    """Immutable order snapshot. Produced ONLY from an accepted (priced)
    QuoteCalculationSnapshot. is_locked MUST remain True after creation."""

    order_id: str = ""
    product_definition: ProductDefinition = field(default_factory=ProductDefinition)
    cost_result: CostResult = field(default_factory=CostResult)
    quote_snapshot: QuoteCalculationSnapshot = field(default_factory=QuoteCalculationSnapshot)
    final_price: OrderFinalPrice = field(default_factory=OrderFinalPrice)
    created_at: str = ""
    is_locked: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()