"""Dual Quote Snapshot V2 schema (Step 8 MVP).

Freezes CommercialPriceProposal (7G) and EstimatedInternalCost (7H) side-by-side.
Never merges commercial and internal totals into a single universal price.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.commercial_price_proposal import CommercialPriceProposalPreview
from schemas.estimated_internal_cost import EstimatedInternalCostPreview
from schemas.offer_scope import OFFER_SCOPE_CONTRACT_VERSION, OfferScopeMode
from schemas.product_aggregate import ProductAggregate
from schemas.product_definition import ProductDefinitionPreview

QUOTE_SNAPSHOT_V2_VERSION = "1.0.0"
QUOTE_SNAPSHOT_V2_SOURCE = "quote_snapshot_v2"
COMPONENT_SCOPE_VERSION = "quote_component_scope/v1"

ComponentScopeClassification = Literal["sold", "calc_only", "linked_neutral", "unspecified"]

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


class QuoteSnapshotOfferScope(BaseModel):
    contract_version: str = OFFER_SCOPE_CONTRACT_VERSION
    mode: OfferScopeMode = "full_product"
    sold_modules: list[str] = Field(default_factory=list)
    resolved_runtime_sold_modules: list[str] = Field(default_factory=list)
    use_legacy: bool = True
    resolver_contract_version: str = OFFER_SCOPE_CONTRACT_VERSION
    validation_errors: list[str] = Field(default_factory=list)


class QuoteSnapshotComponentInstance(BaseModel):
    instance_id: str
    canonical_component_code: str | None = None
    runtime_module_code: str | None = None
    source_template_code: str
    segment_key: str | None = None
    classification: ComponentScopeClassification = "unspecified"


class QuoteSnapshotGeometryInput(BaseModel):
    quote_geometry: dict[str, Any] = Field(default_factory=dict)
    svg_source: dict[str, Any] = Field(default_factory=dict)
    analysis_ready: bool | None = None
    workspace_payload_hash: str | None = None


class FrozenComponentScope(BaseModel):
    """Reusable frozen component-scope payload for both snapshot paths."""

    product_aggregate: ProductAggregate | None = None
    offer_scope_snapshot: QuoteSnapshotOfferScope
    component_instances: list[QuoteSnapshotComponentInstance] = Field(default_factory=list)
    geometry_input_snapshot: QuoteSnapshotGeometryInput | None = None
    scope_warnings: list[str] = Field(default_factory=list)


class QuoteSnapshotV2(BaseModel):
    """Dual quote snapshot — commercial and internal sides kept separate."""

    snapshot_version: str = QUOTE_SNAPSHOT_V2_VERSION
    snapshot_id: str | None = None
    snapshot_code: str | None = None
    quote_id: str | None = None
    workspace_id: str | None = None
    template_code: str
    component_scope_version: str | None = None
    offer_scope_snapshot: QuoteSnapshotOfferScope | None = None
    component_instances: list[QuoteSnapshotComponentInstance] = Field(default_factory=list)
    geometry_input_snapshot: QuoteSnapshotGeometryInput | None = None
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
