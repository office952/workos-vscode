"""Schemas for PRODUCT_SYSTEM_REFERENCE_COMPLETE."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

CompletionVerdict = Literal["PASS", "NOT_COMPLETE"]
AxisComplete = Literal["yes", "no", "accepted_limitation"]
FreezeReadiness = Literal[
    "READY_FOR_DOCUMENTATION_HANDOFF",
    "NOT_READY",
]


class CompletionMatrixRow(BaseModel):
    axis: str
    required_verdict: str
    actual_verdict: str
    required_for_reference: bool = True
    complete: AxisComplete = "no"
    limitation: Optional[str] = None
    deferred_to_adv: bool = False
    runtime_proof: Optional[str] = None
    test_proof: Optional[str] = None
    screenshot_proof: Optional[str] = None
    documentation_input: Optional[str] = None
    freeze_input: Optional[str] = None
    blocker: Optional[str] = None
    final_action: Optional[str] = None
    confidence: Literal["high", "medium", "low"] = "high"
    accepted_build: Optional[str] = None
    accepted_commit: Optional[str] = None


class DocumentationHandoffDocInput(BaseModel):
    doc_id: str
    canonical_facts: list[str] = Field(default_factory=list)
    source_code: list[str] = Field(default_factory=list)
    source_api: list[str] = Field(default_factory=list)
    fixture: Optional[str] = None
    accepted_screenshot: Optional[str] = None
    accepted_build: Optional[str] = None
    accepted_commit: Optional[str] = None
    limitations: list[str] = Field(default_factory=list)
    do_not_transfer: list[str] = Field(default_factory=list)
    open_workflow_adv_decision: Optional[str] = None


class ProductSystemReferenceCompleteResponse(BaseModel):
    contract_version: str
    name: str
    overall_verdict: CompletionVerdict
    freeze_readiness: FreezeReadiness
    production_cost_authority: str = "EIC_production_cost"
    cpp_role: str = "reconciliation_only"
    accepted_build_chain: list[dict[str, str]] = Field(default_factory=list)
    completion_matrix: list[CompletionMatrixRow] = Field(default_factory=list)
    accepted_limitations: list[dict[str, str]] = Field(default_factory=list)
    do_not_transfer: list[str] = Field(default_factory=list)
    just_in_time_catalog_rule: dict[str, Any] = Field(default_factory=dict)
    operational_process_contract: dict[str, Any] = Field(default_factory=dict)
    ui_mode_distinction: dict[str, Any] = Field(default_factory=dict)
    dev_mode_contract: dict[str, Any] = Field(default_factory=dict)
    freeze_governance_contract: dict[str, Any] = Field(default_factory=dict)
    live_proof: dict[str, Any] = Field(default_factory=dict)
    documentation_handoff: list[DocumentationHandoffDocInput] = Field(default_factory=list)
    compound_engineering_map: list[dict[str, Any]] = Field(default_factory=list)
    executive_truth_ro: str = ""
    warnings: list[str] = Field(default_factory=list)
