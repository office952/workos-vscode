"""Build 4A — Frozen Modular Graph read model over Quote/Order Snapshot V2.

Does not replace V2 persistence. Pure normalization + fingerprints + preview.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

FROZEN_MODULAR_GRAPH_ADAPTER_VERSION = "frozen_modular_graph/v1"
FROZEN_MODULAR_GRAPH_HASH_ALGORITHM = "sha256_hex16"

CompatibilityMode = Literal[
    "modular_v2",
    "legacy_full_product",
    "legacy_v1_line_items",
    "order_v2_frozen",
    "unknown",
]

ScenarioKind = Literal[
    "full_product",
    "face_only",
    "cant_only",
    "face_cant",
    "legacy_full_product",
    "unknown",
]


class FrozenGraphComponentHashes(BaseModel):
    product_definition: str | None = None
    product_aggregate: str | None = None
    cpp: str | None = None
    active_scope: str | None = None
    geometry: str | None = None
    task_contract: str | None = None
    frozen_graph: str


class FrozenGraphIdentity(BaseModel):
    snapshot_version: str | None = None
    product_template_code: str | None = None
    product_definition_version: str | None = None
    aggregate_version: str | None = None
    form_contract_version: str | None = None
    component_scope_version: str | None = None
    adapter_version: str = FROZEN_MODULAR_GRAPH_ADAPTER_VERSION


class FrozenGraphRequest(BaseModel):
    request_mode: str | None = None
    selected_components: list[str] = Field(default_factory=list)
    selected_modules: list[str] = Field(default_factory=list)
    use_legacy: bool = False


class FrozenGraphScope(BaseModel):
    active_components: list[str] = Field(default_factory=list)
    active_modules: list[str] = Field(default_factory=list)
    inactive_modules: list[str] = Field(default_factory=list)
    sold_modules: list[str] = Field(default_factory=list)
    excluded_operations: list[str] = Field(default_factory=list)
    excluded_materials: list[str] = Field(default_factory=list)
    interface_face_cant_active: bool | None = None
    use_legacy_full_product: bool = False


class FrozenGraphGeometry(BaseModel):
    source_file: str | None = None
    workspace_payload_hash: str | None = None
    analysis_ready: bool | None = None
    dimensions: dict[str, Any] = Field(default_factory=dict)
    perimeter: float | None = None
    area: float | None = None


class FrozenGraphCommercial(BaseModel):
    cpp_rule_codes: list[str] = Field(default_factory=list)
    cpp_line_count: int = 0
    currency: str | None = None
    net_total: float | None = None
    gross_total: float | None = None
    line_fingerprint: list[dict[str, Any]] = Field(default_factory=list)


class FrozenTaskCandidatePreview(BaseModel):
    candidate_key: str
    task_name: str
    task_type: str | None = None
    priced_operation: str | None = None
    sequence: int | None = None
    owner_module: str | None = None
    provenance: str | None = None
    trigger_condition: str | None = None
    interface_owner: str | None = None


class FrozenGraphExecutionPreview(BaseModel):
    candidate_count: int = 0
    task_candidates: list[FrozenTaskCandidatePreview] = Field(default_factory=list)
    material_codes: list[str] = Field(default_factory=list)
    operation_codes: list[str] = Field(default_factory=list)
    adhesive_material_count: int = 0
    bonding_operation_count: int = 0
    # Dual validation: semantic (ActiveScope) vs technical (Aggregate outputs).
    semantic_interface_face_cant_active: bool | None = None
    technical_adhesive_present: bool = False
    technical_bonding_present: bool = False
    authority: str = "task_contract.task_rules"


class FrozenGraphCompatibility(BaseModel):
    mode: CompatibilityMode = "unknown"
    scenario: ScenarioKind = "unknown"
    source_snapshot_version: str | None = None
    adapter_version: str = FROZEN_MODULAR_GRAPH_ADAPTER_VERSION
    notes: list[str] = Field(default_factory=list)


class FrozenGraphAssertionResult(BaseModel):
    code: str
    passed: bool
    detail: str | None = None


class FrozenModularGraphPreview(BaseModel):
    """Normalized read model over an existing QuoteSnapshotV2 / OrderSnapshotV2 payload."""

    identity: FrozenGraphIdentity
    request: FrozenGraphRequest
    scope: FrozenGraphScope
    geometry: FrozenGraphGeometry
    commercial: FrozenGraphCommercial
    execution: FrozenGraphExecutionPreview
    compatibility: FrozenGraphCompatibility
    hashes: FrozenGraphComponentHashes
    assertions: list[FrozenGraphAssertionResult] = Field(default_factory=list)
    readiness: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    no_write: bool = True
    hash_algorithm: str = FROZEN_MODULAR_GRAPH_HASH_ALGORITHM
    source_kind: Literal["quote_snapshot_v2", "order_snapshot_v2", "unknown"] = "unknown"
