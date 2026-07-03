"""Dual Quote Snapshot V2 schema (Step 8 MVP).

Freezes CommercialPriceProposal (7G) and EstimatedInternalCost (7H) side-by-side.
Never merges commercial and internal totals into a single universal price.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.commercial_price_proposal import CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.product_aggregate import ProductAggregate
from schemas.product_definition import ProductDefinitionPreview

QUOTE_SNAPSHOT_V2_VERSION = "1.0.0"
QUOTE_SNAPSHOT_V2_SOURCE = "quote_snapshot_v2"

QuoteSnapshotReadiness = Literal[
    "ready_for_owner_review",
    "partial_with_owner_decisions",
    "blocked_missing_commercial",
    "blocked_missing_internal",
    "blocked_snapshot_conflict",
    "blocked_forbidden_path",
    "blocked_schema_missing",
]

QuoteSnapshotPersistStatus = Literal["not_persisted", "persisted", "blocked"]


class QuoteSnapshotOwnerDecision(BaseModel):
    code: str
    label: str
    source: Literal["commercial_price_proposal", "estimated_internal_cost"]
    module_code: str | None = None
    detail: str | None = None


class QuoteSnapshotBlocker(BaseModel):
    code: str
    message: str
    source: Literal["commercial_price_proposal", "estimated_internal_cost"]
    module_code: str | None = None
    material_code: str | None = None


class QuoteSnapshotProvenanceEntry(BaseModel):
    key: str
    source: str
    detail: str


class QuoteSnapshotV2(BaseModel):
    """Dual quote snapshot — commercial and internal sides kept separate."""

    snapshot_version: str = QUOTE_SNAPSHOT_V2_VERSION
    snapshot_id: str | None = None
    snapshot_code: str | None = None
    quote_id: str | None = None
    workspace_id: str | None = None
    template_code: str
    product_definition_snapshot: ProductDefinitionPreview | None = None
    product_aggregate_snapshot: ProductAggregate | None = None
    commercial_price_proposal_snapshot: CommercialPriceProposalPreview
    estimated_internal_cost_snapshot: EstimatedInternalCostPreview
    owner_decisions_snapshot: list[QuoteSnapshotOwnerDecision] = Field(default_factory=list)
    warnings_snapshot: list[str] = Field(default_factory=list)
    blockers_snapshot: list[QuoteSnapshotBlocker] = Field(default_factory=list)
    readiness: QuoteSnapshotReadiness = "partial_with_owner_decisions"
    frozen_at: str | None = None
    frozen_by: str | None = None
    version: int = 1
    provenance: list[QuoteSnapshotProvenanceEntry] = Field(default_factory=list)
    persist_status: QuoteSnapshotPersistStatus = "not_persisted"
    notes: list[str] = Field(default_factory=list)
    input_summary: dict[str, Any] = Field(default_factory=dict)
