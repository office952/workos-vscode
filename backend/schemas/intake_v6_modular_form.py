"""Intake V6 modular form contract schema — derived from mini-module registry (read-only)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

FORM_CONTRACT_VERSION = "1.2.0-generic-renderer-pilot"

SupportedFieldType = Literal[
    "text",
    "number",
    "integer",
    "boolean",
    "select",
    "multiselect",
    "readonly",
]

VisibilityKind = Literal["always", "equals", "not_equals", "in_set", "truthy", "falsy"]

OperationalStatus = Literal[
    "ACTIVE_OPERATIONAL",
    "READONLY_EXPLANATORY",
    "FUTURE_RESERVED_STEP_6",
    "FUTURE_RESERVED_STEP_7",
    "FUTURE_RESERVED_STEP_8",
    "FUTURE_RESERVED_STEP_9",
    "DEAD_PIECE_REMOVE_OR_APPROVE",
]

FieldRole = Literal[
    "module_activation",
    "module_configuration",
    "geometry_input",
    "product_definition_key",
    "derived_quote_input",
    "readonly_computed",
]

ActivationKind = Literal["always_on", "required_module", "optional_addon", "conditional_gate"]


class IntakeFormOption(BaseModel):
    """One selectable value for generic select/multiselect rendering."""

    value: str
    label_ro: str


class IntakeVisibilityRule(BaseModel):
    """Bounded visibility rule — no arbitrary expressions."""

    kind: VisibilityKind = "always"
    workspace_path: str | None = None
    value: Any = None
    values: list[Any] | None = None


class IntakeFormFieldBinding(BaseModel):
    """One Intake V6 field with operational destination."""

    canonical_key: str
    workspace_path: str
    label_ro: str | None = None
    required: bool = False
    field_type: str | None = None
    unit: str | None = None
    option_values: list[str] | None = None
    options: list[IntakeFormOption] | None = None
    visibility_rule: str | None = None
    visibility: IntakeVisibilityRule | None = None
    min_value: float | None = None
    max_value: float | None = None
    read_only: bool = False
    display_mode: str | None = None
    decision: str | None = None
    consumers: list[str] = Field(default_factory=list)
    field_role: FieldRole = "module_configuration"
    module_codes: list[str] = Field(default_factory=list)
    operational_status: OperationalStatus = "ACTIVE_OPERATIONAL"
    product_definition_keys: list[str] = Field(default_factory=list)
    aggregate_trace: list[str] = Field(default_factory=list)
    cost_engine_step: str | None = None
    derived_from: str | None = None
    derivation_rule: str | None = None
    notes: list[str] = Field(default_factory=list)


class IntakeRenderSection(BaseModel):
    """Ordered UI section for generic Intake contract rendering."""

    section_key: str
    title_ro: str
    order: int
    description_ro: str | None = None
    module_codes: list[str] = Field(default_factory=list)
    field_keys: list[str] = Field(default_factory=list)
    visibility: IntakeVisibilityRule | None = None
    pilot_role: str | None = None


class IntakeModuleFormSection(BaseModel):
    """Form-facing view of one mini-module."""

    module_code: str
    module_name: str
    operational_status: OperationalStatus
    activation_kind: ActivationKind
    intake_trigger_fields: list[str] = Field(default_factory=list)
    consumed_form_fields: list[str] = Field(default_factory=list)
    required_form_fields: list[str] = Field(default_factory=list)
    optional_form_fields: list[str] = Field(default_factory=list)
    product_definition_outputs: list[str] = Field(default_factory=list)
    valid_when: list[str] = Field(default_factory=list)
    invalid_when: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TriggerFieldAlignment(BaseModel):
    """Documents module-link trigger vs Intake canonical field — no warning suppression."""

    module_code: str
    module_link_trigger_field: str
    canonical_intake_field: str
    derived_quote_input_key: str | None = None
    derivation_rule: str | None = None
    warning_code: str = "TRIGGER_FIELD_MISMATCH"
    backwards_compatible: bool = True
    resolution_owner_step: int = 5
    notes: list[str] = Field(default_factory=list)


class IntakeV6ModularFormContractSummary(BaseModel):
    contract_version: str = FORM_CONTRACT_VERSION
    template_code: str
    registry_version: str
    active_module_count: int = 0
    field_binding_count: int = 0
    # Full form runtime authority is not claimed for Letters yet.
    # When true, runtime_authority_scope must describe the bounded surface.
    runtime_authority: bool = False
    runtime_authority_scope: str | None = None
    warnings: list[str] = Field(default_factory=list)


class IntakeV6ModularFormContract(BaseModel):
    """GET contract for Intake V6 modular form alignment."""

    summary: IntakeV6ModularFormContractSummary
    modules: list[IntakeModuleFormSection] = Field(default_factory=list)
    field_bindings: list[IntakeFormFieldBinding] = Field(default_factory=list)
    render_sections: list[IntakeRenderSection] = Field(default_factory=list)
    writable_workspace_paths: list[str] = Field(default_factory=list)
    form_system_backbone: dict[str, Any] | None = None
    trigger_alignments: list[TriggerFieldAlignment] = Field(default_factory=list)
    valid_combinations: list[str] = Field(default_factory=list)
    invalid_combinations: list[str] = Field(default_factory=list)
    orphan_fields_audit: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
