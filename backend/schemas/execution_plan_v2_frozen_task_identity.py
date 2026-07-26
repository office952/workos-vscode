"""Frozen component graph → execution task identity contract (W5-T02)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

FROZEN_TASK_IDENTITY_VERSION = "frozen_task_identity/v1"

OperationScope = Literal[
    "COMPONENT_LOCAL",
    "ROOT_PRODUCT",
    "CROSS_COMPONENT_ASSEMBLY",
    "ORDER_LEVEL",
    "INSTALLATION_SCOPE",
    "INTERNAL_ANALYSIS_ONLY",
    "NOT_PROVEN",
]

IdentityClassification = Literal[
    "FULL_FROZEN_COMPONENT_IDENTITY",
    "TEMPLATE_LEVEL_IDENTITY_ONLY",
    "MODULE_LEVEL_IDENTITY_ONLY",
    "OPERATION_LEVEL_IDENTITY_ONLY",
    "LEGACY_NAME_BASED_IDENTITY",
    "ANONYMOUS_TASK",
    "NOT_PROVEN",
]

TaskRuleOrigin = Literal[
    "dossier_task_rule",
    "composition_graph_operation",
    "linked_segment_task_rule",
]


class FrozenTaskIdentity(BaseModel):
    """Deterministic frozen-graph task identity — never inferred from live Product System."""

    contract_version: str = FROZEN_TASK_IDENTITY_VERSION
    deterministic_task_key: str
    source_graph_node_id: str | None = None
    source_component_role: str | None = None
    source_template_code: str | None = None
    source_component_instance_id: str | None = None
    source_segment_key: str | None = None
    parent_graph_node_id: str | None = None
    source_module_code: str | None = None
    source_operation_code: str | None = None
    source_task_rule_code: str | None = None
    operation_scope: OperationScope = "NOT_PROVEN"
    identity_classification: IdentityClassification = "NOT_PROVEN"
    shared_operation: bool = False
    task_rule_origin: TaskRuleOrigin = "dossier_task_rule"
    provenance: list[str] = Field(default_factory=list)
