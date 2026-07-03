"""Read-only Mini-module Contract Registry schema — operational product flow contract."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

REGISTRY_VERSION = "1.0.0"

OperationalStatus = Literal[
    "ACTIVE_OPERATIONAL",
    "READONLY_EXPLANATORY",
    "FUTURE_RESERVED_STEP_5",
    "FUTURE_RESERVED_STEP_6",
    "FUTURE_RESERVED_STEP_7",
    "FUTURE_RESERVED_STEP_8",
    "FUTURE_RESERVED_STEP_9",
    "DEAD_PIECE_REMOVE_OR_APPROVE",
]

ModuleType = Literal[
    "linked_child_template",
    "dossier_component",
    "parent_template",
    "derived_process",
]


class OperationalDestination(BaseModel):
    """Every field/component/material/operation must declare where it flows."""

    intake_source: list[str] = Field(default_factory=list)
    product_definition_keys: list[str] = Field(default_factory=list)
    product_aggregate_display: list[str] = Field(default_factory=list)
    cost_engine_use: list[str] = Field(default_factory=list)
    quote_snapshot_use: list[str] = Field(default_factory=list)
    order_snapshot_use: list[str] = Field(default_factory=list)
    task_preview_use: list[str] = Field(default_factory=list)


class MiniModuleActivationRule(BaseModel):
    rule_type: str
    trigger_field: str | None = None
    trigger_value: Any = None
    description: str


class MiniModuleCompatibilityRule(BaseModel):
    rule_type: str
    description: str
    details: dict[str, Any] = Field(default_factory=dict)


class MiniModuleConflict(BaseModel):
    code: str
    severity: Literal["info", "warning", "error"] = "warning"
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class MiniModuleContract(BaseModel):
    """Operational contract for one mini-module."""

    module_code: str
    module_name: str
    module_version: str = "1.0.0"
    module_type: ModuleType
    child_template_code: str | None = None
    dossier_component_id: str | None = None
    applies_to_template_codes: list[str] = Field(default_factory=list)
    produced_component_roles: list[str] = Field(default_factory=list)
    required_material_roles: list[str] = Field(default_factory=list)
    required_operation_roles: list[str] = Field(default_factory=list)
    consumed_form_fields: list[str] = Field(default_factory=list)
    product_definition_outputs: list[str] = Field(default_factory=list)
    aggregate_outputs: list[str] = Field(default_factory=list)
    cost_engine_inputs: list[str] = Field(default_factory=list)
    quote_snapshot_outputs: list[str] = Field(default_factory=list)
    order_snapshot_outputs: list[str] = Field(default_factory=list)
    task_preview_outputs: list[str] = Field(default_factory=list)
    activation_rules: list[MiniModuleActivationRule] = Field(default_factory=list)
    compatibility_rules: list[MiniModuleCompatibilityRule] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    conflicts: list[MiniModuleConflict] = Field(default_factory=list)
    operational_status: OperationalStatus
    roadmap_owner_step: int
    operational_destination: OperationalDestination = Field(default_factory=OperationalDestination)
    warnings: list[str] = Field(default_factory=list)


class MiniModuleRegistrySummary(BaseModel):
    registry_version: str = REGISTRY_VERSION
    template_code: str | None = None
    total_modules: int = 0
    active_operational_count: int = 0
    future_reserved_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class MiniModuleRegistryResponse(BaseModel):
    summary: MiniModuleRegistrySummary
    modules: list[MiniModuleContract] = Field(default_factory=list)


class MiniModuleRegistryRef(BaseModel):
    """Lightweight reference for ProductAggregate metadata."""

    module_code: str
    operational_status: OperationalStatus
    child_template_code: str | None = None
    dossier_component_id: str | None = None
