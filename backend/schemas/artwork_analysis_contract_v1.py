"""Minimal extensible Artwork Analysis Contract v1 (consume-only).

WorkOS validates and reviews external desktop analysis payloads.
It does not parse SVG/DWG/DXF and does not write Product Truth from this module.
Transport for delivery of the payload is TBD.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

ARTWORK_ANALYSIS_CONTRACT_VERSION = "artwork_analysis_contract_v1"

SUPPORTED_ARTWORK_ANALYSIS_CONTRACT_VERSIONS: frozenset[str] = frozenset(
    {ARTWORK_ANALYSIS_CONTRACT_VERSION}
)

ObservationStatus = Literal["observed", "proposed", "confirmed"]
BindingStatus = Literal["proposed", "confirmed"]
SourceFileKind = Literal["svg", "dwg", "dxf", "other", "unknown"]


class ArtworkAnalysisProvenanceV1(BaseModel):
    """Minimum provenance for audit and Snapshot reference."""

    analysis_id: str = Field(min_length=1)
    analysis_version: str = Field(min_length=1)
    source_file_name: Optional[str] = None
    source_file_hash: Optional[str] = None
    source_file_kind: SourceFileKind = "unknown"
    producer_app: Optional[str] = None
    producer_app_version: Optional[str] = None
    produced_at: Optional[str] = None
    source_entity_ids: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class ArtworkAnalysisEntityV1(BaseModel):
    entity_id: str = Field(min_length=1)
    kind: Optional[str] = None
    label: Optional[str] = None
    status: ObservationStatus = "observed"
    attributes: dict[str, Any] = Field(default_factory=dict)


class ArtworkAnalysisGroupV1(BaseModel):
    group_id: str = Field(min_length=1)
    member_entity_ids: list[str] = Field(default_factory=list)
    label: Optional[str] = None
    status: ObservationStatus = "observed"
    attributes: dict[str, Any] = Field(default_factory=dict)


class ArtworkAnalysisMeasurementV1(BaseModel):
    measurement_id: str = Field(min_length=1)
    entity_id: Optional[str] = None
    metric: str = Field(min_length=1)
    value: float
    unit: Optional[str] = None
    status: ObservationStatus = "observed"


class ArtworkAnalysisObservationV1(BaseModel):
    observation_id: str = Field(min_length=1)
    code: Optional[str] = None
    message: str = Field(min_length=1)
    status: ObservationStatus = "observed"
    related_entity_ids: list[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ArtworkAnalysisSuggestedBindingV1(BaseModel):
    """Suggested component/product bindings — always proposed until operator confirms."""

    binding_id: str = Field(min_length=1)
    target_role: Optional[str] = None
    entity_ids: list[str] = Field(default_factory=list)
    status: BindingStatus = "proposed"
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    rationale: Optional[str] = None

    @field_validator("status")
    @classmethod
    def reject_inbound_confirmed(cls, value: BindingStatus) -> BindingStatus:
        if value == "confirmed":
            raise ValueError(
                "suggested_bindings must start as proposed; "
                "confirmed status is reserved for operator Product Truth confirmation"
            )
        return value


class ArtworkAnalysisContractV1(BaseModel):
    """Lean external analysis payload — extensible via attributes/extra only."""

    artwork_analysis_contract_version: str = Field(min_length=1)
    provenance: ArtworkAnalysisProvenanceV1
    entities: list[ArtworkAnalysisEntityV1] = Field(default_factory=list)
    groups: list[ArtworkAnalysisGroupV1] = Field(default_factory=list)
    measurements: list[ArtworkAnalysisMeasurementV1] = Field(default_factory=list)
    observations: list[ArtworkAnalysisObservationV1] = Field(default_factory=list)
    suggested_bindings: list[ArtworkAnalysisSuggestedBindingV1] = Field(
        default_factory=list
    )
    confidence_summary: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    extensions: dict[str, Any] = Field(default_factory=dict)

    @field_validator("artwork_analysis_contract_version")
    @classmethod
    def reject_unknown_contract_version(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if normalized not in SUPPORTED_ARTWORK_ANALYSIS_CONTRACT_VERSIONS:
            raise ValueError(
                f"unsupported artwork_analysis_contract_version: {value!r}; "
                f"supported={sorted(SUPPORTED_ARTWORK_ANALYSIS_CONTRACT_VERSIONS)}"
            )
        return normalized

    @model_validator(mode="after")
    def require_source_identity(self) -> ArtworkAnalysisContractV1:
        hash_ok = bool(str(self.provenance.source_file_hash or "").strip())
        name_ok = bool(str(self.provenance.source_file_name or "").strip())
        if not hash_ok and not name_ok:
            raise ValueError(
                "provenance requires source_file_hash or source_file_name"
            )
        return self


class ArtworkAnalysisReviewSurfaceV1(BaseModel):
    """UI review surface contract — read-only presentation shape."""

    analysis_id: str
    contract_version: str
    source_file_name: Optional[str] = None
    source_file_hash: Optional[str] = None
    entity_count: int = 0
    group_count: int = 0
    measurement_count: int = 0
    observation_count: int = 0
    suggested_binding_count: int = 0
    unconfirmed_observation_count: int = 0
    all_bindings_proposed: bool = True
    product_truth_writable_from_adapter: bool = False
    transport: Literal["tbd"] = "tbd"
    notes: list[str] = Field(default_factory=list)


class ArtworkAnalysisAdapterResultV1(BaseModel):
    """Consume-only adapter output — never includes a Product Truth write."""

    ok: bool
    write_performed: bool = False
    product_truth_written: bool = False
    contract: Optional[ArtworkAnalysisContractV1] = None
    review_surface: Optional[ArtworkAnalysisReviewSurfaceV1] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
