"""Build 4C — Execution preview projected from frozen modular graph (read-only)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.frozen_modular_graph import (
    FrozenGraphAssertionResult,
    FrozenGraphComponentHashes,
    FrozenModularGraphPreview,
)

EXECUTION_PREVIEW_FROM_FROZEN_VERSION = "execution_preview_from_frozen/v1"
SOURCE_AUTHORITY_FROZEN_SNAPSHOT_V2 = "frozen_snapshot_v2"

PreviewReadiness = Literal[
    "ready",
    "blocked",
    "degraded",
    "legacy_compatible",
    "checksum_invalid",
    "scope_invalid",
    "provenance_incomplete",
    "unsupported_v1",
]


class ExecutionPreviewSource(BaseModel):
    snapshot_kind: str = "unknown"
    snapshot_version: str | None = None
    frozen_graph_hash: str | None = None
    order_id: int | None = None
    legacy_mode: bool = False
    compatibility_adapter: str = EXECUTION_PREVIEW_FROM_FROZEN_VERSION
    source_authority: str = SOURCE_AUTHORITY_FROZEN_SNAPSHOT_V2


class ExecutionPreviewCandidate(BaseModel):
    preview_candidate_key: str
    source_operation_code: str | None = None
    task_rule_code: str | None = None
    task_name: str
    owner_module: str | None = None
    interface_owner: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    role_hints: list[str] = Field(default_factory=list)
    machine_hints: list[str] = Field(default_factory=list)
    material_requirements: list[str] = Field(default_factory=list)
    readiness: str = "projected"
    provenance: str | None = None
    sequence: int | None = None


class ExecutionPreviewDependencyEdge(BaseModel):
    from_candidate_key: str
    to_candidate_key: str
    provenance: str = "sequence_order"


class ExecutionPreviewDependencyGraph(BaseModel):
    edges: list[ExecutionPreviewDependencyEdge] = Field(default_factory=list)
    topological_order: list[str] = Field(default_factory=list)
    cycle_detected: bool = False
    unresolved: list[str] = Field(default_factory=list)


class ExecutionPreviewMaterialRequirement(BaseModel):
    material_code: str
    unit: str | None = None
    owner_module: str | None = None
    interface_provenance: bool = False
    optional: bool = False
    readiness_state: str = "frozen_requirement"
    attached_candidate_keys: list[str] = Field(default_factory=list)


class ExecutionPreviewCommercialReference(BaseModel):
    cpp_fingerprint: list[dict[str, Any]] = Field(default_factory=list)
    cpp_line_count: int = 0
    net_total: float | None = None
    gross_total: float | None = None
    no_reprice: bool = True


class ExecutionPreviewSafety(BaseModel):
    preview_only: bool = True
    no_persistence: bool = True
    no_materialization: bool = True
    no_live_recompile: bool = True
    no_write: bool = True


class ExecutionPreviewFromFrozen(BaseModel):
    """Read-only execution projection over FrozenModularGraphPreview / OrderSnapshotV2."""

    preview_version: str = EXECUTION_PREVIEW_FROM_FROZEN_VERSION
    readiness: PreviewReadiness = "ready"
    source: ExecutionPreviewSource
    frozen_graph: FrozenModularGraphPreview
    hashes: FrozenGraphComponentHashes
    task_candidates: list[ExecutionPreviewCandidate] = Field(default_factory=list)
    dependency_graph: ExecutionPreviewDependencyGraph = Field(
        default_factory=ExecutionPreviewDependencyGraph
    )
    material_requirements: list[ExecutionPreviewMaterialRequirement] = Field(
        default_factory=list
    )
    commercial_reference: ExecutionPreviewCommercialReference = Field(
        default_factory=ExecutionPreviewCommercialReference
    )
    assertions: list[FrozenGraphAssertionResult] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    preview_fingerprint: str | None = None
    safety: ExecutionPreviewSafety = Field(default_factory=ExecutionPreviewSafety)
    message: str | None = None
