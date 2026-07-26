"""WorkOS Truth Metadata — document, system, page, edge, drift (W0-B1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from schemas.truth_metadata.enums import (
    DocumentAuthority,
    DocumentCategory,
    DriftStatus,
    EdgeRelationshipType,
    OwnerType,
    PageRole,
    VisibilityClass,
)
from schemas.truth_metadata.references import (
    DisplayMetadata,
    EvidenceReference,
    FigmaReference,
    VersionedModel,
    normalize_repo_path,
)


class DocumentReference(VersionedModel):
    """Document identity + relationships. Path allowlist membership ≠ canonical authority."""

    document_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    path: str = Field(min_length=1)
    category: DocumentCategory
    authority: DocumentAuthority
    status: DocumentAuthority
    owner: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_validated_at: datetime | None = None
    supersedes: list[str] = Field(default_factory=list)
    superseded_by: str | None = None
    systems: list[str] = Field(default_factory=list)
    pages: list[str] = Field(default_factory=list)
    routes: list[str] = Field(default_factory=list)
    contracts: list[str] = Field(default_factory=list)
    figma_refs: list[FigmaReference] = Field(default_factory=list)
    code_refs: list[str] = Field(default_factory=list)
    api_refs: list[str] = Field(default_factory=list)
    test_refs: list[str] = Field(default_factory=list)
    qa_refs: list[str] = Field(default_factory=list)
    worklog_refs: list[str] = Field(default_factory=list)
    runtime_refs: list[str] = Field(default_factory=list)
    drift_status: DriftStatus = DriftStatus.NOT_VALIDATED
    visibility_class: VisibilityClass
    display: DisplayMetadata | None = None
    is_test_fixture: bool = False
    fixture_class: str | None = None
    canonicality: str | None = None

    @field_validator("path")
    @classmethod
    def _path(cls, value: str) -> str:
        return normalize_repo_path(value)

    @model_validator(mode="after")
    def _supersession(self) -> DocumentReference:
        if self.document_id in self.supersedes:
            raise ValueError("document cannot supersede itself")
        if self.superseded_by and self.superseded_by == self.document_id:
            raise ValueError("document cannot be superseded_by itself")
        if self.is_test_fixture:
            if self.fixture_class != "TEST_FIXTURE":
                raise ValueError("test fixtures must set fixture_class=TEST_FIXTURE")
            if self.canonicality != "NOT_CANONICAL_TRUTH":
                raise ValueError("test fixtures must set canonicality=NOT_CANONICAL_TRUTH")
        return self


class SystemNode(VersionedModel):
    system_id: str = Field(min_length=1)
    display: DisplayMetadata
    role_summary: str | None = None
    owner_type: OwnerType = OwnerType.UNASSIGNED
    owner_reference: str | None = None
    authority_reference: str | None = None
    status: str = Field(description="System operational status vocabulary (string for B1 extensibility)")
    routes: list[str] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[EvidenceReference] = Field(default_factory=list)
    last_validated_at: datetime | None = None
    # Separated from architecture status — never promote runtime into architecture.
    runtime_status: str | None = None
    runtime_status_source: str | None = Field(
        default=None,
        description="Label for runtime check source; null if unavailable",
    )
    visibility_class: VisibilityClass = VisibilityClass.ADMIN_ONLY
    is_test_fixture: bool = False


class PageNode(VersionedModel):
    page_id: str = Field(min_length=1)
    route: str = Field(min_length=1)
    component_reference: str | None = None
    system_id: str = Field(min_length=1)
    role: PageRole
    display: DisplayMetadata
    reads: list[str] = Field(default_factory=list)
    writes: list[str] = Field(default_factory=list)
    upstream: list[str] = Field(default_factory=list)
    downstream: list[str] = Field(default_factory=list)
    figma_refs: list[FigmaReference] = Field(default_factory=list)
    document_ids: list[str] = Field(default_factory=list)
    status: str
    drift_status: DriftStatus = DriftStatus.NOT_VALIDATED
    drift_reason: str | None = None
    visibility_class: VisibilityClass = VisibilityClass.ADMIN_ONLY
    last_validated_at: datetime | None = None
    is_test_fixture: bool = False

    @model_validator(mode="after")
    def _drift(self) -> PageNode:
        if self.drift_status not in (DriftStatus.ALIGNED, DriftStatus.NOT_VALIDATED):
            if not (self.drift_reason or "").strip():
                raise ValueError("drift_reason is required when drift_status is not ALIGNED/NOT_VALIDATED")
        return self


class TypedEdge(VersionedModel):
    edge_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    relationship_type: EdgeRelationshipType
    contract_id: str | None = None
    trigger: str | None = None
    identity: str | None = None
    allowed_data: list[str] = Field(default_factory=list)
    forbidden_data: list[str] = Field(default_factory=list)
    freeze_rule: str | None = None
    authority_reference: str | None = None
    status: str = "UNKNOWN"
    evidence_refs: list[EvidenceReference] = Field(default_factory=list)
    last_validated_at: datetime | None = None
    display: DisplayMetadata | None = None
    visibility_class: VisibilityClass = VisibilityClass.ADMIN_ONLY
    is_test_fixture: bool = False


class DriftRecord(VersionedModel):
    drift_id: str = Field(min_length=1)
    subject_type: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    drift_status: DriftStatus
    drift_reason: str = Field(min_length=1)
    sources_compared: list[str] = Field(default_factory=list)
    owner_decision_required: bool = False
    evidence_refs: list[EvidenceReference] = Field(default_factory=list)
    visibility_class: VisibilityClass = VisibilityClass.INTERNAL_TECHNICAL
    is_test_fixture: bool = False

    @model_validator(mode="after")
    def _aligned_ok(self) -> DriftRecord:
        if self.drift_status == DriftStatus.ALIGNED:
            raise ValueError("DriftRecord must not use ALIGNED; omit record or use claim.drift_status")
        return self
