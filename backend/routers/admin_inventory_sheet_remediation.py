from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_admin_user
from schemas.inventory import (
    InventorySheetRemediationPlanItemContract,
    InventorySheetRemediationPlanResponse,
    InventorySheetRemediationPlanSummary,
)
from services.inventory_sheet_quality_audit import audit_inventory_sheet_quality
from services.inventory_sheet_remediation_policy import (
    build_remediation_plan_for_report,
)

router = APIRouter(
    prefix="/api/v1/admin/inventory",
    tags=["admin_inventory_sheet_remediation"],
    dependencies=[Depends(get_admin_user)],
)


@router.get(
    "/sheet-quality-remediation-plan",
    response_model=InventorySheetRemediationPlanResponse,
)
async def get_inventory_sheet_quality_remediation_plan(
    db: AsyncSession = Depends(get_db),
) -> InventorySheetRemediationPlanResponse:
    audit_report = await audit_inventory_sheet_quality(db)
    plan_report = build_remediation_plan_for_report(audit_report)

    return InventorySheetRemediationPlanResponse(
        source="backend",
        report_type="inventory_sheet_remediation_plan",
        generated_at=datetime.now(timezone.utc).isoformat(),
        summary=InventorySheetRemediationPlanSummary(
            total_items=plan_report.summary.total_items,
            manual_only_count=plan_report.summary.manual_only_count,
            assisted_manual_count=plan_report.summary.assisted_manual_count,
            future_bulk_safe_count=plan_report.summary.future_bulk_safe_count,
            not_repairable_without_domain_decision_count=(
                plan_report.summary.not_repairable_without_domain_decision_count
            ),
        ),
        items=[
            InventorySheetRemediationPlanItemContract(
                material_id=item.material_id,
                material_name=item.material_name,
                issue_code=item.issue_code,
                remediation_category=item.remediation_category,
                allowed_actions=item.allowed_actions,
                forbidden_actions=item.forbidden_actions,
                requires_operator_input=item.requires_operator_input,
                requires_admin_confirmation=item.requires_admin_confirmation,
                recommended_next_step=item.recommended_next_step,
                future_automation_eligible=item.future_automation_eligible,
                would_block_intake_assist=item.would_block_intake_assist,
            )
            for item in plan_report.items
        ],
        warnings=["This plan is read-only and does not modify inventory data."],
    )
