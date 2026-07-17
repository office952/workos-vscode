"""Frozen Active Scope contract for Quote/Order snapshots (Letters Slice 1).

Embeds compiled ActiveScopeResult. No DB migration — JSON blob fields only.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.active_scope import ACTIVE_SCOPE_CONTRACT_VERSION, ACTIVE_SCOPE_RESOLVER_VERSION, ActiveScopeResult
from schemas.offer_scope import OFFER_SCOPE_CONTRACT_VERSION

ACTIVE_SCOPE_SNAPSHOT_VERSION_V1 = "active_scope_snapshot/v1"
ACTIVE_SCOPE_SNAPSHOT_VERSION_V2 = "active_scope_snapshot/v2"
# Writers emit v2 (precise responsibilities). Readers accept v1 + v2.
ACTIVE_SCOPE_SNAPSHOT_VERSION = ACTIVE_SCOPE_SNAPSHOT_VERSION_V2
KNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSIONS = frozenset(
    {ACTIVE_SCOPE_SNAPSHOT_VERSION_V1, ACTIVE_SCOPE_SNAPSHOT_VERSION_V2}
)

ActiveScopeCompatibilityMode = Literal["enriched", "legacy_scope_fallback"]


class QuoteSnapshotActiveScope(BaseModel):
    """Enriched freeze of compiled active scope — workspace provenance only."""

    active_scope_snapshot_version: str = ACTIVE_SCOPE_SNAPSHOT_VERSION
    compatibility_mode: ActiveScopeCompatibilityMode = "enriched"
    source_workspace_id: str | None = None
    source_template_code: str
    source_offer_scope_version: str = OFFER_SCOPE_CONTRACT_VERSION
    active_scope_contract_version: str = ACTIVE_SCOPE_CONTRACT_VERSION
    resolver_version: str = ACTIVE_SCOPE_RESOLVER_VERSION
    compiled_at: str | None = None
    compiled: ActiveScopeResult
    warnings: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ACTIVE_SCOPE_SNAPSHOT_VERSION",
    "KNOWN_ACTIVE_SCOPE_SNAPSHOT_VERSIONS",
    "ActiveScopeCompatibilityMode",
    "QuoteSnapshotActiveScope",
]
