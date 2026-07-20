"""Product Template publication lifecycle contract.

active=true is never sufficient for published / offerable / runtime-ready.
NULL publication_status = legacy unspecified (pre-lifecycle compatibility).
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


PublicationStatus = Literal[
    "DRAFT",
    "VALIDATED",
    "E2E_CHECKED",
    "PUBLISHED",
    "DEPRECATED",
    "ARCHIVED",
]

PublicationAction = Literal[
    "enter_draft",
    "mark_validated",
    "mark_e2e_checked",
    "publish",
    "deprecate",
    "archive",
    "reopen_draft",
]


class ProductTemplatePublicationState(BaseModel):
    template_code: str
    template_id: int
    db_active: bool
    publication_status: Optional[PublicationStatus] = None
    effective_status: str
    legacy_unspecified: bool = False
    publication_version: Optional[int] = None
    last_e2e_verdict: Optional[str] = None
    last_e2e_checked_at: Optional[str] = None
    published_at: Optional[str] = None
    published_by: Optional[str] = None
    offerability_gate: str
    publish_allowed: bool = False
    publish_blockers: list[str] = Field(default_factory=list)
    allowed_actions: list[PublicationAction] = Field(default_factory=list)
    active_is_not_published: bool = True
    contract_version: str = "product_template_publication_v1"


class ProductTemplatePublicationTransitionRequest(BaseModel):
    action: PublicationAction
    actor: Optional[str] = None
    notes: Optional[str] = None
    # When true, publish/e2e_checked re-runs static readiness (default).
    run_readiness: bool = True


class ProductTemplatePublicationTransitionResponse(BaseModel):
    ok: bool
    state: ProductTemplatePublicationState
    readiness_verdict: Optional[str] = None
    readiness_e2e_ready: Optional[bool] = None
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)
