"""Schemas for ConfirmJobProductTruth — job-level Product Truth revision."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


JobConfirmationState = Literal["unconfirmed", "confirmed", "stale_after_edit"]


class ConfirmJobProductTruthRequest(BaseModel):
    expected_revision: int = Field(ge=0, description="0 for first confirm; else current revision")
    expected_draft_hash: Optional[str] = Field(
        default=None,
        description="Optional optimistic concurrency guard against draft payload hash",
    )
    expected_content_hash: Optional[str] = Field(
        default=None,
        description="Optional guard when re-confirming / correcting an existing revision",
    )
    root_template_code: Optional[str] = None
    correction_reason: Optional[str] = None


class JobRevisionMetadataView(BaseModel):
    revision: int
    content_hash: str
    confirmation_state: str
    confirmed_at: Optional[str] = None
    confirmed_by: Optional[str] = None
    expected_draft_hash: Optional[str] = None
    root_template_code: Optional[str] = None
    root_template_version: Optional[str] = None
    contract_version: str = "job_revision_v1"
    source: str = "confirm_job_product_truth"
    provenance: dict[str, Any] = Field(default_factory=dict)


class ConfirmJobProductTruthResponse(BaseModel):
    workspace_id: str
    workspace_code: Optional[str] = None
    write_performed: bool
    idempotent_noop: bool
    product_truth_path: str = "payload_json.product_truth.confirmed_snapshot_v1"
    metadata: JobRevisionMetadataView
    pinned_bag_keys: list[str] = Field(default_factory=list)
    draft_hash: str
    previous_revision: Optional[int] = None
    audit_entry: Optional[dict[str, Any]] = None


class JobProductTruthStatusResponse(BaseModel):
    workspace_id: str
    has_job_revision: bool
    metadata: Optional[JobRevisionMetadataView] = None
    draft_hash: str
    is_stale: bool = False
    commercial_freeze_allowed: bool = False
