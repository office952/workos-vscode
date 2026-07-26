"""WorkOS Truth Metadata — shared reference models and path safety (W0-B1)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.truth_metadata.enums import (
    TRUTH_METADATA_VERSION,
    AuthorityType,
    EvidenceType,
    FIGMA_APPROVED_STATUSES,
    FigmaApprovalStatus,
    FigmaDriftType,
    FigmaFlowStatus,
)

_TRANSLATION_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
_UNSAFE_PATH_PARTS = ("..",)


def normalize_repo_path(path: str) -> str:
    """Normalize a repo-relative path; reject traversal and absolute escapes."""
    if not path or not str(path).strip():
        raise ValueError("path must be non-empty")
    raw = str(path).strip().replace("\\", "/")
    if "\x00" in raw:
        raise ValueError("path must not contain null bytes")
    if raw.startswith("/") or (len(raw) >= 2 and raw[1] == ":"):
        raise ValueError("path must be repo-relative (no absolute paths)")
    parts = [p for p in raw.split("/") if p not in ("", ".")]
    if any(p in _UNSAFE_PATH_PARTS for p in parts):
        raise ValueError("path traversal is not allowed")
    if any(p.startswith("~") for p in parts):
        raise ValueError("home-relative path segments are not allowed")
    return "/".join(parts)


def validate_translation_key(key: str | None) -> str | None:
    if key is None:
        return None
    if not _TRANSLATION_KEY_RE.match(key):
        raise ValueError(
            "translation_key must be dotted snake_case with at least two segments "
            "(e.g. system_map.title)"
        )
    return key


class DisplayMetadata(BaseModel):
    """Romanian-first display fields (UI projection; not business SoT)."""

    model_config = ConfigDict(extra="forbid")

    display_label_ro: str = Field(min_length=1)
    technical_alias: str | None = None
    translation_key: str | None = None
    description_ro: str | None = None

    @field_validator("translation_key")
    @classmethod
    def _translation_key(cls, value: str | None) -> str | None:
        return validate_translation_key(value)


class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1)
    evidence_type: EvidenceType
    reference: str = Field(min_length=1, description="Path, URL, symbol, or check id")
    captured_at: datetime | None = None
    note: str | None = None
    is_test_fixture: bool = False

    @field_validator("reference")
    @classmethod
    def _safe_ref(cls, value: str) -> str:
        if value.startswith(("http://", "https://")):
            return value
        if "/" in value or "\\" in value:
            return normalize_repo_path(value)
        if ".." in value:
            raise ValueError("evidence reference must not contain '..'")
        return value


class AuthorityReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authority_type: AuthorityType
    authority_reference: str = Field(min_length=1)
    authority_rank: int = Field(ge=0, le=1000)

    @field_validator("authority_reference")
    @classmethod
    def _safe_auth_ref(cls, value: str) -> str:
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith(("od:", "OD-", "OD_")) or "/" not in value and "\\" not in value:
            if ".." in value:
                raise ValueError("authority_reference must not contain '..'")
            return value
        return normalize_repo_path(value)


class FigmaReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    figma_file_key: str = Field(min_length=1)
    figma_file_name: str | None = None
    figma_page_name: str | None = None
    figma_node_id: str = Field(min_length=1)
    figma_flow_name: str | None = None
    figma_flow_status: FigmaFlowStatus = FigmaFlowStatus.NOT_FOUND
    figma_approval_status: FigmaApprovalStatus = FigmaApprovalStatus.UNKNOWN
    figma_last_reviewed_at: datetime | None = None
    runtime_route: str | None = None
    runtime_component: str | None = None
    drift_type: FigmaDriftType = FigmaDriftType.NONE
    drift_description: str | None = None
    owner_decision_required: bool = False
    supersedes_node_id: str | None = None
    superseded_by_node_id: str | None = None

    @model_validator(mode="after")
    def _approval_consistency(self) -> FigmaReference:
        if self.drift_type != FigmaDriftType.NONE and not (self.drift_description or "").strip():
            raise ValueError("drift_description is required when drift_type is not NONE")
        if self.supersedes_node_id and self.supersedes_node_id == self.figma_node_id:
            raise ValueError("supersedes_node_id must not equal figma_node_id")
        if self.superseded_by_node_id and self.superseded_by_node_id == self.figma_node_id:
            raise ValueError("superseded_by_node_id must not equal figma_node_id")
        return self

    def is_approved_for_authority(self) -> bool:
        return self.figma_approval_status in FIGMA_APPROVED_STATUSES


def assert_figma_may_back_figma_approved(ref: FigmaReference) -> None:
    if not ref.is_approved_for_authority():
        raise ValueError(
            "Figma node without APPROVED / APPROVED_WITH_NOTES cannot back FIGMA_APPROVED authority"
        )


class VersionedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata_version: str = Field(default=TRUTH_METADATA_VERSION)

    @field_validator("metadata_version")
    @classmethod
    def _version(cls, value: str) -> str:
        if value != TRUTH_METADATA_VERSION:
            raise ValueError(
                f"unsupported metadata_version: {value!r}; expected {TRUTH_METADATA_VERSION!r}"
            )
        return value


def fixture_banner() -> dict[str, Any]:
    return {
        "fixture_class": "TEST_FIXTURE",
        "canonicality": "NOT_CANONICAL_TRUTH",
    }
