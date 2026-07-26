"""Order Snapshot V2 schema (Step 9.2).

Frozen commercial + internal payload copied from accepted Quote Snapshot V2.
No reprice, no ExecutionPlan at convert time.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.commercial_price_proposal import CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.product_aggregate import ProductAggregate
from schemas.product_definition import ProductDefinitionPreview
from schemas.active_scope_snapshot import QuoteSnapshotActiveScope
from schemas.quote_snapshot_v2 import (
    QuoteSnapshotBlocker,
    QuoteSnapshotComponentInstance,
    QuoteSnapshotGeometryInput,
    QuoteSnapshotOfferScope,
    QuoteSnapshotOwnerDecision,
    QuoteSnapshotProvenanceEntry,
)

ORDER_SNAPSHOT_V2_VERSION = "1.0.0"
ORDER_SNAPSHOT_V2_SOURCE = "order_snapshot_v2"
EXECUTION_PLAN_SOURCE_ORDER_SNAPSHOT_V2 = "order_snapshot_v2"

OrderSnapshotV2ConvertStatus = Literal["converted", "blocked"]


class OrderSnapshotV2(BaseModel):
    """Frozen order snapshot — commercial authority separate from internal estimate."""

    snapshot_version: str = ORDER_SNAPSHOT_V2_VERSION
    snapshot_code: str | None = None
    content_hash: str | None = None
    order_id: int | None = None
    quote_id: int
    quote_snapshot_v2_id: int
    component_scope_version: str | None = None
    offer_scope_snapshot: QuoteSnapshotOfferScope | None = None
    active_scope_snapshot: QuoteSnapshotActiveScope | None = None
    component_instances: list[QuoteSnapshotComponentInstance] = Field(default_factory=list)
    geometry_input_snapshot: QuoteSnapshotGeometryInput | None = None
    product_definition_snapshot: ProductDefinitionPreview | None = None
    product_aggregate_snapshot: ProductAggregate | None = None
    commercial_price_proposal_snapshot: CommercialPriceProposalPreview
    estimated_internal_cost_snapshot: EstimatedInternalCostPreview
    accepted_commercial_total: float
    accepted_currency: str
    estimated_internal_total: float | None = None
    owner_decisions_snapshot: list[QuoteSnapshotOwnerDecision] = Field(default_factory=list)
    warnings_snapshot: list[str] = Field(default_factory=list)
    blockers_snapshot: list[QuoteSnapshotBlocker] = Field(default_factory=list)
    provenance: list[QuoteSnapshotProvenanceEntry] = Field(default_factory=list)
    accepted_at: str | None = None
    accepted_by: str | None = None
    converted_at: str | None = None
    converted_by: str | None = None
    no_reprice_policy: bool = True
    execution_plan_source: str = EXECUTION_PLAN_SOURCE_ORDER_SNAPSHOT_V2
    execution_plan_created: bool = False
    notes: list[str] = Field(default_factory=list)
    input_summary: dict[str, Any] = Field(default_factory=dict)


class OrderSnapshotV2ConvertResult(BaseModel):
    status: OrderSnapshotV2ConvertStatus
    quote_id: int
    quote_code: str | None = None
    order_id: int | None = None
    order_code: str | None = None
    order_status: str | None = None
    quote_snapshot_v2_id: int | None = None
    accepted_commercial_total: float | None = None
    accepted_currency: str | None = None
    estimated_internal_total: float | None = None
    blockers: list[str] = Field(default_factory=list)
    error_code: str | None = None
    message: str | None = None
