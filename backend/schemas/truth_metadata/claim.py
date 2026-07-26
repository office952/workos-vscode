"""WorkOS Truth Metadata — TruthClaim model and validation rules (W0-B1)."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from schemas.truth_metadata.enums import (
    CANONICAL_AUTHORITY_RANK_FLOOR,
    CANONICAL_AUTHORITY_TYPES,
    RUNTIME_AUTHORITY_RANK_CEILING,
    AuthorityType,
    ClaimStatus,
    ClaimType,
    DriftStatus,
    OwnerType,
    SubjectType,
    VisibilityClass,
)
from schemas.truth_metadata.references import (
    AuthorityReference,
    DisplayMetadata,
    EvidenceReference,
    FigmaReference,
    VersionedModel,
    assert_figma_may_back_figma_approved,
    normalize_repo_path,
    validate_translation_key,
)


class TruthClaim(VersionedModel):
    """Controlled assertion about WorkOS truth. Projection metadata — not UI SoT."""

    claim_id: str = Field(min_length=1)
    subject_type: SubjectType
    subject_id: str = Field(min_length=1)
    claim_type: ClaimType
    claim_text: str = Field(min_length=1)
    display_label_ro: str = Field(min_length=1)
    technical_alias: str | None = None
    translation_key: str | None = None
    description_ro: str | None = None
    authority: AuthorityReference
    owner_type: OwnerType
    owner_reference: str | None = None
    status: ClaimStatus
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    last_validated_at: datetime | None = None
    validated_against: str | None = None
    evidence_refs: list[EvidenceReference] = Field(default_factory=list)
    document_path: str | None = None
    code_refs: list[str] = Field(default_factory=list)
    runtime_refs: list[str] = Field(default_factory=list)
    test_refs: list[str] = Field(default_factory=list)
    figma_refs: list[FigmaReference] = Field(default_factory=list)
    related_systems: list[str] = Field(default_factory=list)
    related_pages: list[str] = Field(default_factory=list)
    related_contracts: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    superseded_by: str | None = None
    drift_status: DriftStatus = DriftStatus.NOT_VALIDATED
    drift_reason: str | None = None
    owner_decision_required: bool = False
    visibility_class: VisibilityClass
    is_test_fixture: bool = False
    fixture_class: str | None = Field(
        default=None,
        description="Must be TEST_FIXTURE when is_test_fixture is true",
    )
    canonicality: str | None = Field(
        default=None,
        description="Must be NOT_CANONICAL_TRUTH for fixtures",
    )

    @field_validator("translation_key")
    @classmethod
    def _tk(cls, value: str | None) -> str | None:
        return validate_translation_key(value)

    @field_validator("document_path")
    @classmethod
    def _doc_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_repo_path(value)

    @model_validator(mode="after")
    def _validate_claim_rules(self) -> TruthClaim:
        auth = self.authority

        # Runtime evidence cannot hold canonical architecture authority rank.
        if auth.authority_type == AuthorityType.RUNTIME_EVIDENCE:
            if auth.authority_rank >= CANONICAL_AUTHORITY_RANK_FLOOR:
                raise ValueError(
                    "RUNTIME_EVIDENCE must not use canonical authority_rank "
                    f"(>={CANONICAL_AUTHORITY_RANK_FLOOR})"
                )
            if auth.authority_rank > RUNTIME_AUTHORITY_RANK_CEILING:
                raise ValueError(
                    "RUNTIME_EVIDENCE authority_rank must be "
                    f"<={RUNTIME_AUTHORITY_RANK_CEILING}"
                )

        # FIGMA_APPROVED authority requires an approved figma ref.
        if auth.authority_type == AuthorityType.FIGMA_APPROVED:
            if not self.figma_refs:
                raise ValueError("FIGMA_APPROVED authority requires at least one figma_ref")
            for ref in self.figma_refs:
                assert_figma_may_back_figma_approved(ref)

        # Owner rules for canonical authorities on CURRENT* claims.
        if (
            self.status in (ClaimStatus.CURRENT, ClaimStatus.CURRENT_WITH_GUARDS)
            and auth.authority_type in CANONICAL_AUTHORITY_TYPES
        ):
            if self.owner_type == OwnerType.UNASSIGNED:
                raise ValueError(
                    "canonical CURRENT claims require owner_type other than UNASSIGNED"
                )
            if not (self.owner_reference or "").strip():
                raise ValueError("canonical CURRENT claims require owner_reference")

        # Validation date required for CURRENT.
        if self.status == ClaimStatus.CURRENT and self.last_validated_at is None:
            raise ValueError("CURRENT claims require last_validated_at")

        # Evidence required for CURRENT / CURRENT_WITH_GUARDS.
        if self.status in (ClaimStatus.CURRENT, ClaimStatus.CURRENT_WITH_GUARDS):
            if not self.evidence_refs:
                raise ValueError("CURRENT/CURRENT_WITH_GUARDS claims require evidence_refs")

        # Supersession coherence.
        if self.claim_id in self.supersedes:
            raise ValueError("claim cannot supersede itself")
        if self.superseded_by and self.superseded_by == self.claim_id:
            raise ValueError("claim cannot be superseded_by itself")

        # valid_until >= valid_from
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until must be >= valid_from")

        # Drift reason when not ALIGNED / NOT_VALIDATED
        if self.drift_status not in (DriftStatus.ALIGNED, DriftStatus.NOT_VALIDATED):
            if not (self.drift_reason or "").strip():
                raise ValueError("drift_reason is required when drift_status is not ALIGNED/NOT_VALIDATED")

        # Fixture markers
        if self.is_test_fixture:
            if self.fixture_class != "TEST_FIXTURE":
                raise ValueError("test fixtures must set fixture_class=TEST_FIXTURE")
            if self.canonicality != "NOT_CANONICAL_TRUTH":
                raise ValueError("test fixtures must set canonicality=NOT_CANONICAL_TRUTH")

        # Authority reference always required (embedded in AuthorityReference)
        if not auth.authority_reference.strip():
            raise ValueError("authority_reference is required")

        return self

    def to_display_metadata(self) -> DisplayMetadata:
        return DisplayMetadata(
            display_label_ro=self.display_label_ro,
            technical_alias=self.technical_alias,
            translation_key=self.translation_key,
            description_ro=self.description_ro,
        )
