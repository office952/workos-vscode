"""Graph-to-cost structural projection contract (Wave 3 / D-010)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

GRAPH_COST_PROJECTION_VERSION = "1.0.0"

StructuralAuthority = Literal[
    "composition_graph",
    "legacy_module_states",
    "offer_scope_subset",
]


class GraphCostProjectionNode(BaseModel):
    node_id: str
    template_code: str
    node_role: str
    module_code: str
    module_role: str
    parent_node_id: str | None = None
    activation_source: str | None = None
    inherited_inputs: dict[str, Any] = Field(default_factory=dict)
    locally_owned_inputs: dict[str, Any] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)


class GraphCostProjectionEdge(BaseModel):
    edge_id: str
    parent_node_id: str
    child_node_id: str
    child_role: str
    relation_type: str
    dependency_role: str | None = None


class GraphCostProjection(BaseModel):
    """Canonical workspace structural scope for 7B/7H/7G module activation."""

    projection_version: str = GRAPH_COST_PROJECTION_VERSION
    structural_authority: StructuralAuthority = "composition_graph"
    template_code: str
    workspace_id: str | None = None
    composed_graph_version: str | None = None
    composition_mode: str | None = None
    root_template_code: str
    active_child_template_codes: list[str] = Field(default_factory=list)
    active_mini_module_codes: list[str] = Field(default_factory=list)
    root_mini_module_codes: list[str] = Field(default_factory=list)
    graph_structural_module_codes: list[str] = Field(default_factory=list)
    nodes: list[GraphCostProjectionNode] = Field(default_factory=list)
    edges: list[GraphCostProjectionEdge] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    compatibility_note: str | None = None
    compiler: str = "product_aggregate_graph_cost_projection"
