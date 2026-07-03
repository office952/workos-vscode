from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


InventorySheetAuditStatus = Literal["all", "valid", "not_applicable", "invalid"]
InventorySheetAuditItemStatus = Literal["valid", "not_applicable", "invalid"]
InventorySheetAuditIssueCode = Literal[
    "missing_required_field",
    "missing_configuration",
    "invalid_unit",
    "invalid_dimensions",
    "partial_payload",
    "unexpected_shape",
]
InventorySheetRemediationCategory = Literal[
    "manual_only",
    "assisted_manual",
    "future_bulk_safe",
    "not_repairable_without_domain_decision",
]
InventorySheetRemediationOperationStatus = Literal["applied", "failed"]


class InventorySheetFormatContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["none", "sheet", "roll", "linear", "piece", "unknown"]
    width: float | None = None
    height: float | None = None
    unit: Literal["mm", "cm", "m", "unknown"] = "unknown"
    usable_width: float | None = None
    usable_height: float | None = None
    thickness: float | None = None
    thickness_unit: Literal["mm", "cm", "m", "unknown"] = "unknown"
    verified: bool = False
    source: Literal["manual", "supplier", "imported", "unknown"] = "unknown"


class InventorySheetAssistItemContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_id: str
    material_name: str
    category: str
    status: Literal["active", "missing_price", "needs_owner_input", "unknown"]
    unit: Literal["sqm", "pcs", "ml", "sheet", "unknown"]
    sheet_format: InventorySheetFormatContract
    fit_status: Literal["fits", "fits_rotated", "does_not_fit", "unknown"] = "unknown"
    fit_reason: str
    warnings: list[str] = Field(default_factory=list)
    requires_review: bool = True


class InventorySheetPayloadContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["backend"] = "backend"
    assist_available: bool
    items: list[InventorySheetAssistItemContract] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    contract_version: str = "2026-05-15"


class InventorySheetQualityByIssueCode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    missing_required_field: int = 0
    missing_configuration: int = 0
    invalid_unit: int = 0
    invalid_dimensions: int = 0
    partial_payload: int = 0
    unexpected_shape: int = 0


class InventorySheetQualityAuditSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_records_checked: int = 0
    valid_count: int = 0
    not_applicable_count: int = 0
    invalid_count: int = 0
    would_block_intake_assist_count: int = 0
    by_issue_code: InventorySheetQualityByIssueCode = Field(
        default_factory=InventorySheetQualityByIssueCode
    )


class InventorySheetQualityAuditFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: InventorySheetAuditStatus = "all"
    issue_code: InventorySheetAuditIssueCode | None = None
    would_block_intake_assist: bool | None = None
    limit: int = 100
    offset: int = 0


class InventorySheetQualityAuditItemContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_id: str
    material_name: str | None = None
    material_code: str | None = None
    category: str | None = None
    status: InventorySheetAuditItemStatus
    issue_code: InventorySheetAuditIssueCode | None = None
    message: str
    recommended_action: str | None = None
    would_block_intake_assist: bool = False


class InventorySheetQualityAuditResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["backend"] = "backend"
    report_type: Literal["inventory_sheet_quality_audit"] = (
        "inventory_sheet_quality_audit"
    )
    generated_at: str
    summary: InventorySheetQualityAuditSummary
    filters: InventorySheetQualityAuditFilters
    items: list[InventorySheetQualityAuditItemContract] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class InventorySheetRemediationPlanItemContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_id: str
    material_name: str | None = None
    issue_code: InventorySheetAuditIssueCode
    remediation_category: InventorySheetRemediationCategory
    allowed_actions: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    requires_operator_input: bool = True
    requires_admin_confirmation: bool = True
    recommended_next_step: str
    future_automation_eligible: bool = False
    would_block_intake_assist: bool = True


class InventorySheetRemediationPlanSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_items: int = 0
    manual_only_count: int = 0
    assisted_manual_count: int = 0
    future_bulk_safe_count: int = 0
    not_repairable_without_domain_decision_count: int = 0


class InventorySheetRemediationPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["backend"] = "backend"
    report_type: Literal["inventory_sheet_remediation_plan"] = (
        "inventory_sheet_remediation_plan"
    )
    generated_at: str
    summary: InventorySheetRemediationPlanSummary
    items: list[InventorySheetRemediationPlanItemContract] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=lambda: [
        "This plan is read-only and does not modify inventory data."
    ])


class InventorySheetRemediationProposedValues(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sheet_format_type: Literal["none", "sheet", "roll", "linear", "piece", "unknown"] | None = None
    sheet_width: float | None = None
    sheet_height: float | None = None
    sheet_unit: Literal["mm", "cm", "m", "unknown"] | None = None
    sheet_thickness: float | None = None
    sheet_thickness_unit: Literal["mm", "cm", "m", "unknown"] | None = None
    usable_width: float | None = None
    usable_height: float | None = None
    format_source: Literal["manual", "supplier", "imported", "unknown"] | None = None
    format_verified: bool | None = None
    format_notes: str | None = None


class InventorySheetRemediationExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_code: InventorySheetAuditIssueCode
    proposed_values: InventorySheetRemediationProposedValues
    reason: str | None = None
    confirm: bool = False


class InventorySheetRemediationExecutionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sheet_format: dict[str, Any]
    audit_status: InventorySheetAuditItemStatus
    issue_code: InventorySheetAuditIssueCode | None = None


class InventorySheetRemediationExecutionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["backend"] = "backend"
    operation: Literal["inventory_sheet_remediation"] = "inventory_sheet_remediation"
    status: Literal["applied"] = "applied"
    material_id: str
    issue_code: InventorySheetAuditIssueCode
    before: InventorySheetRemediationExecutionSnapshot
    after: InventorySheetRemediationExecutionSnapshot
    audit_event_id: str
    warnings: list[str] = Field(default_factory=list)


class InventorySheetRemediationAuditTrailByIssueCode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    missing_required_field: int = 0
    missing_configuration: int = 0
    invalid_unit: int = 0
    invalid_dimensions: int = 0
    partial_payload: int = 0
    unexpected_shape: int = 0


class InventorySheetRemediationAuditTrailByStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    applied: int = 0
    failed: int = 0


class InventorySheetRemediationAuditTrailSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_events: int = 0
    returned_events: int = 0
    by_issue_code: InventorySheetRemediationAuditTrailByIssueCode = Field(
        default_factory=InventorySheetRemediationAuditTrailByIssueCode
    )
    by_status: InventorySheetRemediationAuditTrailByStatus = Field(
        default_factory=InventorySheetRemediationAuditTrailByStatus
    )


class InventorySheetRemediationAuditTrailFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_id: str | None = None
    issue_code: InventorySheetAuditIssueCode | None = None
    changed_by: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    operation_status: InventorySheetRemediationOperationStatus | None = None
    limit: int = 100
    offset: int = 0


class InventorySheetRemediationAuditTrailEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_event_id: str
    material_id: str
    issue_code: InventorySheetAuditIssueCode
    reason: str
    changed_by: str | None = None
    changed_at: str
    source: str
    operation_status: InventorySheetRemediationOperationStatus
    old_values: dict[str, Any]
    new_values: dict[str, Any]
    validation_result_before: dict[str, Any]
    validation_result_after: dict[str, Any]


class InventorySheetRemediationAuditTrailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["backend"] = "backend"
    report_type: Literal["inventory_sheet_remediation_audit_trail"] = (
        "inventory_sheet_remediation_audit_trail"
    )
    generated_at: str
    summary: InventorySheetRemediationAuditTrailSummary
    filters: InventorySheetRemediationAuditTrailFilters
    events: list[InventorySheetRemediationAuditTrailEvent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
