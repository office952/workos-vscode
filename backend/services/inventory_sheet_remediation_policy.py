from __future__ import annotations

from dataclasses import dataclass, field

from schemas.inventory import (
    InventorySheetAuditIssueCode,
    InventorySheetRemediationCategory,
)
from services.inventory_sheet_quality_audit import (
    InventorySheetQualityAuditItem,
    InventorySheetQualityAuditReport,
)


@dataclass(frozen=True)
class InventorySheetRemediationPolicy:
    issue_code: InventorySheetAuditIssueCode
    remediation_category: InventorySheetRemediationCategory
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    requires_operator_input: bool = True
    requires_admin_confirmation: bool = True
    recommended_next_step: str = ""
    future_automation_eligible: bool = False


@dataclass(frozen=True)
class InventorySheetRemediationPlanItem:
    material_id: str
    material_name: str | None
    issue_code: InventorySheetAuditIssueCode
    remediation_category: InventorySheetRemediationCategory
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    requires_operator_input: bool = True
    requires_admin_confirmation: bool = True
    recommended_next_step: str = ""
    future_automation_eligible: bool = False
    would_block_intake_assist: bool = True


@dataclass(frozen=True)
class InventorySheetRemediationPlanSummary:
    total_items: int = 0
    manual_only_count: int = 0
    assisted_manual_count: int = 0
    future_bulk_safe_count: int = 0
    not_repairable_without_domain_decision_count: int = 0


@dataclass(frozen=True)
class InventorySheetRemediationPlanReport:
    items: list[InventorySheetRemediationPlanItem] = field(default_factory=list)
    summary: InventorySheetRemediationPlanSummary = field(
        default_factory=InventorySheetRemediationPlanSummary
    )


_POLICY_BY_ISSUE: dict[InventorySheetAuditIssueCode, InventorySheetRemediationPolicy] = {
    "missing_required_field": InventorySheetRemediationPolicy(
        issue_code="missing_required_field",
        remediation_category="manual_only",
        allowed_actions=[
            "open_material_edit_form",
            "set_required_identity_fields",
            "set_material_status",
            "rerun_audit",
        ],
        forbidden_actions=[
            "auto_fill_required_fields",
            "bulk_fix",
            "silent_normalization",
        ],
        requires_operator_input=True,
        requires_admin_confirmation=True,
        recommended_next_step=(
            "Open material edit form and enter verified required fields "
            "(code/name/status) from source-of-truth documents."
        ),
        future_automation_eligible=False,
    ),
    "missing_configuration": InventorySheetRemediationPolicy(
        issue_code="missing_configuration",
        remediation_category="assisted_manual",
        allowed_actions=[
            "open_material_edit_form",
            "set_sheet_dimensions",
            "set_sheet_unit",
            "rerun_audit",
        ],
        forbidden_actions=[
            "auto_fill_dimensions",
            "bulk_fix",
            "default_sheet_size",
        ],
        requires_operator_input=True,
        requires_admin_confirmation=True,
        recommended_next_step=(
            "Collect verified sheet format data from supplier label/spec and "
            "enter sheet_width, sheet_height, and sheet_unit manually."
        ),
        future_automation_eligible=False,
    ),
    "invalid_unit": InventorySheetRemediationPolicy(
        issue_code="invalid_unit",
        remediation_category="assisted_manual",
        allowed_actions=[
            "open_material_edit_form",
            "map_unit_to_supported_value",
            "record_mapping_reason",
            "rerun_audit",
        ],
        forbidden_actions=[
            "auto_correct_unit_without_mapping_table",
            "bulk_fix_without_approval",
            "silent_normalization",
        ],
        requires_operator_input=True,
        requires_admin_confirmation=True,
        recommended_next_step=(
            "Map unit to canonical supported unit only when source documents "
            "confirm the conversion."
        ),
        future_automation_eligible=True,
    ),
    "invalid_dimensions": InventorySheetRemediationPolicy(
        issue_code="invalid_dimensions",
        remediation_category="manual_only",
        allowed_actions=[
            "open_material_edit_form",
            "set_positive_sheet_dimensions",
            "set_positive_usable_dimensions",
            "rerun_audit",
        ],
        forbidden_actions=[
            "auto_fill_dimensions",
            "bulk_fix",
            "silent_normalization",
        ],
        requires_operator_input=True,
        requires_admin_confirmation=True,
        recommended_next_step=(
            "Validate physical dimensions and enter positive numeric values "
            "for sheet and usable dimensions."
        ),
        future_automation_eligible=False,
    ),
    "partial_payload": InventorySheetRemediationPolicy(
        issue_code="partial_payload",
        remediation_category="assisted_manual",
        allowed_actions=[
            "open_material_edit_form",
            "align_usable_with_sheet_dimensions",
            "set_null_usable_when_unknown",
            "rerun_audit",
        ],
        forbidden_actions=[
            "auto_shrink_dimensions",
            "bulk_fix",
            "silent_normalization",
        ],
        requires_operator_input=True,
        requires_admin_confirmation=True,
        recommended_next_step=(
            "Resolve dimension conflict by confirming usable limits against "
            "verified sheet dimensions."
        ),
        future_automation_eligible=False,
    ),
    "unexpected_shape": InventorySheetRemediationPolicy(
        issue_code="unexpected_shape",
        remediation_category="not_repairable_without_domain_decision",
        allowed_actions=[
            "open_data_governance_incident",
            "triage_schema_drift",
            "rerun_audit_after_fix_plan",
        ],
        forbidden_actions=[
            "auto_repair",
            "bulk_fix",
            "silent_normalization",
        ],
        requires_operator_input=True,
        requires_admin_confirmation=True,
        recommended_next_step=(
            "Escalate to domain/data governance owner for root-cause analysis "
            "before any data correction."
        ),
        future_automation_eligible=False,
    ),
}


def get_remediation_policy_for_issue(
    issue_code: InventorySheetAuditIssueCode,
) -> InventorySheetRemediationPolicy:
    return _POLICY_BY_ISSUE[issue_code]


def build_remediation_plan_for_audit_item(
    item: InventorySheetQualityAuditItem,
) -> InventorySheetRemediationPlanItem | None:
    # Only invalid items with issue_code require remediation planning.
    if item.status != "invalid" or item.issue_code is None:
        return None

    policy = get_remediation_policy_for_issue(item.issue_code)
    return InventorySheetRemediationPlanItem(
        material_id=item.material_id,
        material_name=item.material_name,
        issue_code=item.issue_code,
        remediation_category=policy.remediation_category,
        allowed_actions=list(policy.allowed_actions),
        forbidden_actions=list(policy.forbidden_actions),
        requires_operator_input=policy.requires_operator_input,
        requires_admin_confirmation=policy.requires_admin_confirmation,
        recommended_next_step=policy.recommended_next_step,
        future_automation_eligible=policy.future_automation_eligible,
        would_block_intake_assist=item.would_block_intake_assist,
    )


def build_remediation_plan_for_report(
    audit_report: InventorySheetQualityAuditReport,
) -> InventorySheetRemediationPlanReport:
    items: list[InventorySheetRemediationPlanItem] = []

    for audit_item in audit_report.items:
        plan_item = build_remediation_plan_for_audit_item(audit_item)
        if plan_item is not None:
            items.append(plan_item)

    summary = InventorySheetRemediationPlanSummary(
        total_items=len(items),
        manual_only_count=sum(
            1 for item in items if item.remediation_category == "manual_only"
        ),
        assisted_manual_count=sum(
            1 for item in items if item.remediation_category == "assisted_manual"
        ),
        future_bulk_safe_count=sum(
            1 for item in items if item.remediation_category == "future_bulk_safe"
        ),
        not_repairable_without_domain_decision_count=sum(
            1
            for item in items
            if item.remediation_category
            == "not_repairable_without_domain_decision"
        ),
    )

    return InventorySheetRemediationPlanReport(items=items, summary=summary)
