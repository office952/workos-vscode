"""Schemas for PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from schemas.workflow_adv_analyzer_io_contract_v1 import AnalyzerIoContractDocumentV1

FinishLineVerdict = Literal[
    "PASS",
    "PASS_WITH_WARNINGS",
    "FAIL",
    "IN_PROGRESS",
]

ModularityVerdict = Literal[
    "MODULAR_AND_REUSABLE",
    "MODULAR_WITH_GAPS",
    "PARTIALLY_HARDCODED",
    "STRUCTURALLY_COUPLED",
    "UNSAFE_FOR_HANDOFF",
]

FormSystemVerdict = Literal[
    "CANONICAL_SCHEMA_DRIVEN",
    "USABLE_WITH_TEMPLATE_GAPS",
    "PARTIALLY_HARDCODED",
    "PAGE_SPECIFIC_ONLY",
    "UNSAFE",
]

ScalabilityVerdict = Literal[
    "SCALABLE_REFERENCE",
    "SCALABLE_WITH_KNOWN_LIMITS",
    "NEEDS_MODULARITY_CLOSURE",
    "NEEDS_FORM_SYSTEM_CLOSURE",
    "NOT_READY_FOR_HANDOFF",
]


class FinishLineChecklistItem(BaseModel):
    axis: str
    entity: str
    requirement: str
    status: Literal["ready", "gap", "deferred", "excluded"] = "gap"
    proof: Optional[str] = None
    notes_ro: Optional[str] = None


class FormFieldOwnershipRecord(BaseModel):
    field_id: str
    label: Optional[str] = None
    type: Optional[str] = None
    unit: Optional[str] = None
    required: bool = False
    default: Any = None
    options: list[Any] = Field(default_factory=list)
    visibility_rule: Optional[str] = None
    validation_rule: Optional[str] = None
    owner: Optional[str] = None
    source: str
    destinations: list[str] = Field(default_factory=list)
    affects: list[str] = Field(default_factory=list)
    version: str
    workspace_path: Optional[str] = None
    product_definition_keys: list[str] = Field(default_factory=list)
    child_template_codes: list[str] = Field(default_factory=list)
    quantity_keys: list[str] = Field(default_factory=list)
    cost_lines: list[str] = Field(default_factory=list)
    readiness_keys: list[str] = Field(default_factory=list)
    analyzer_candidate: bool = False
    analyzer_field: Optional[str] = None
    confirmation_required: bool = False
    hardcoded_ui: bool = False
    classification: str = "vl_specific_schema"
    consumers: list[str] = Field(default_factory=list)
    decision: Optional[str] = None


class FormFieldOwnershipMapResponse(BaseModel):
    contract_version: str
    pilot_template: str
    form_system_verdict: FormSystemVerdict
    fields: list[FormFieldOwnershipRecord] = Field(default_factory=list)
    classification_notes: dict[str, str] = Field(default_factory=dict)
    hardcoded_ui_field_ids: list[str] = Field(default_factory=list)
    analyzer_candidate_field_ids: list[str] = Field(default_factory=list)
    reusable_field_ids: list[str] = Field(default_factory=list)


class CriticalMaterialPolicyItem(BaseModel):
    material_code: str
    classification: str
    unit_cost: Optional[float] = None
    currency: Optional[str] = None
    missing_price: bool = True
    templates: list[str] = Field(default_factory=list)
    reason_ro: str
    action: str
    do_not: list[str] = Field(default_factory=list)
    evidence: Optional[str] = None


class CriticalMaterialPolicyResponse(BaseModel):
    contract_version: str
    policy: dict[str, str]
    items: list[CriticalMaterialPolicyItem] = Field(default_factory=list)
    active_template_critical_codes: list[str] = Field(default_factory=list)
    manual_fill_required_codes: list[str] = Field(default_factory=list)
    notes_ro: list[str] = Field(default_factory=list)


class CompoundEngineeringMapRow(BaseModel):
    axis: str
    entity: str
    owner: str
    current_state: str
    reference_requirement: str
    reusable_contract: bool
    template_specific: bool
    hardcoded: bool
    extension_point: str
    input_schema: str
    output_contract: str
    PD_consumer: str
    PT_consumer: str
    quantity_consumer: str
    cost_consumer: str
    analyzer_relevance: str
    handoff_status: Literal["ready", "gap", "do_not_transfer"]
    required_change: str
    proof: str
    risk: Literal["low", "medium", "high"]
    confidence: Literal["high", "medium", "low"]


class FinishLineContractResponse(BaseModel):
    contract_version: str
    finish_line_name: str
    production_cost_equation: str
    production_cost_boundary: dict[str, Any]
    modularity: dict[str, Any]
    modularity_verdict: ModularityVerdict
    form_system_verdict: FormSystemVerdict
    scalability_verdict: ScalabilityVerdict
    authoring_decision: str
    checklist: list[FinishLineChecklistItem] = Field(default_factory=list)
    page_scope: dict[str, list[str]] = Field(default_factory=dict)
    extension_points: list[dict[str, Any]] = Field(default_factory=list)
    template_code_branch_inventory: list[dict[str, Any]] = Field(default_factory=list)
    field_hardcoding_inventory: list[dict[str, Any]] = Field(default_factory=list)
    formula_duplication_inventory: list[dict[str, Any]] = Field(default_factory=list)
    coupling_inventory: list[dict[str, Any]] = Field(default_factory=list)
    compound_engineering_map: list[CompoundEngineeringMapRow] = Field(default_factory=list)
    analyzer_contract: AnalyzerIoContractDocumentV1
    form_field_map_summary: dict[str, Any] = Field(default_factory=dict)
    critical_materials_summary: dict[str, Any] = Field(default_factory=dict)
    overall_verdict: FinishLineVerdict = "IN_PROGRESS"
    warnings: list[str] = Field(default_factory=list)
