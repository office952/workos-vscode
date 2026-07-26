"""WorkOS Truth Metadata Contract (W0-B1).

Read-only projection schemas. Canonical documentation remains in Git.
No production claim registry. No write API. No DB migration.
"""

from __future__ import annotations

from schemas.truth_metadata.claim import TruthClaim
from schemas.truth_metadata.entities import (
    DocumentReference,
    DriftRecord,
    PageNode,
    SystemNode,
    TypedEdge,
)
from schemas.truth_metadata.enums import (
    CANONICAL_AUTHORITY_RANK_FLOOR,
    RUNTIME_AUTHORITY_RANK_CEILING,
    TRUTH_METADATA_VERSION,
    AuthorityType,
    ClaimStatus,
    ClaimType,
    DocumentAuthority,
    DocumentCategory,
    DriftStatus,
    EdgeRelationshipType,
    EvidenceType,
    FigmaApprovalStatus,
    FigmaDriftType,
    FigmaFlowStatus,
    OwnerType,
    PageRole,
    SubjectType,
    VisibilityClass,
)
from schemas.truth_metadata.references import (
    AuthorityReference,
    DisplayMetadata,
    EvidenceReference,
    FigmaReference,
    normalize_repo_path,
    validate_translation_key,
)

__all__ = [
    "TRUTH_METADATA_VERSION",
    "CANONICAL_AUTHORITY_RANK_FLOOR",
    "RUNTIME_AUTHORITY_RANK_CEILING",
    "AuthorityType",
    "AuthorityReference",
    "ClaimStatus",
    "ClaimType",
    "DisplayMetadata",
    "DocumentAuthority",
    "DocumentCategory",
    "DocumentReference",
    "DriftRecord",
    "DriftStatus",
    "EdgeRelationshipType",
    "EvidenceReference",
    "EvidenceType",
    "FigmaApprovalStatus",
    "FigmaDriftType",
    "FigmaFlowStatus",
    "FigmaReference",
    "OwnerType",
    "PageNode",
    "PageRole",
    "SubjectType",
    "SystemNode",
    "TruthClaim",
    "TypedEdge",
    "VisibilityClass",
    "normalize_repo_path",
    "validate_translation_key",
]
