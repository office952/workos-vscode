"""Documentation index response models (W0-B2) — wraps W0-B1 DocumentReference."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from schemas.truth_metadata import (
    TRUTH_METADATA_VERSION,
    DocumentReference,
    DriftStatus,
    VisibilityClass,
)
from schemas.truth_metadata.references import DisplayMetadata

DOCUMENTATION_INDEX_VERSION = "workos_documentation_index/v1"


class DocumentationFreshness(BaseModel):
    """Dates are informational. filesystem_mtime is never proof of validity."""

    model_config = ConfigDict(extra="forbid")

    filesystem_mtime: datetime | None = None
    git_last_changed_at: datetime | None = None
    last_validated_at: datetime | None = None
    validation_status: str = Field(
        description="VALIDATED | UNKNOWN | STALE_HINT — not architectural invalidity"
    )


class DocumentationIndexListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    title: str
    path: str
    category: str
    authority: str
    status: str
    visibility_class: VisibilityClass
    last_validated_at: datetime | None = None
    drift_status: DriftStatus
    related_systems: list[str] = Field(default_factory=list)
    related_pages: list[str] = Field(default_factory=list)
    display: DisplayMetadata | None = None
    technical_id: str = Field(description="Stable technical document_id — never replaced by display label")
    metadata_version: str = TRUTH_METADATA_VERSION
    index_version: str = DOCUMENTATION_INDEX_VERSION


class DocumentationIndexDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document: DocumentReference
    technical_id: str
    reason_for_inclusion: str | None = None
    freshness: DocumentationFreshness
    file_exists: bool
    content_markdown: str | None = None
    index_version: str = DOCUMENTATION_INDEX_VERSION


class DocumentationIndexListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index_version: str = DOCUMENTATION_INDEX_VERSION
    metadata_version: str = TRUTH_METADATA_VERSION
    count: int
    items: list[DocumentationIndexListItem]
    notes: list[str] = Field(
        default_factory=lambda: [
            "Read-only projection. Path membership is not canonical authority.",
            "No Documentation Center UI in W0-B2.",
        ]
    )


def document_to_list_item(doc: DocumentReference) -> DocumentationIndexListItem:
    return DocumentationIndexListItem(
        document_id=doc.document_id,
        title=doc.title,
        path=doc.path,
        category=str(doc.category),
        authority=str(doc.authority),
        status=str(doc.status),
        visibility_class=doc.visibility_class,
        last_validated_at=doc.last_validated_at,
        drift_status=doc.drift_status,
        related_systems=list(doc.systems),
        related_pages=list(doc.pages),
        display=doc.display,
        technical_id=doc.document_id,
        metadata_version=doc.metadata_version,
    )


def dump_safe_public_dict(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")
