from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_admin_user
from schemas.inventory import (
    InventorySheetAuditIssueCode,
    InventorySheetAuditStatus,
    InventorySheetQualityAuditFilters,
    InventorySheetQualityAuditItemContract,
    InventorySheetQualityAuditResponse,
    InventorySheetQualityAuditSummary,
    InventorySheetQualityByIssueCode,
)
from services.inventory_sheet_quality_audit import audit_inventory_sheet_quality
from services.inventory_sheet_export_service import (
    export_sheet_quality_audit_csv,
    export_sheet_quality_audit_json,
)

router = APIRouter(
    prefix="/api/v1/admin/inventory",
    tags=["admin_inventory_sheet_quality"],
    dependencies=[Depends(get_admin_user)],
)


def _build_issue_code_summary(items: list[InventorySheetQualityAuditItemContract]) -> InventorySheetQualityByIssueCode:
    summary = InventorySheetQualityByIssueCode()
    for item in items:
        if item.issue_code == "missing_required_field":
            summary.missing_required_field += 1
        elif item.issue_code == "missing_configuration":
            summary.missing_configuration += 1
        elif item.issue_code == "invalid_unit":
            summary.invalid_unit += 1
        elif item.issue_code == "invalid_dimensions":
            summary.invalid_dimensions += 1
        elif item.issue_code == "partial_payload":
            summary.partial_payload += 1
        elif item.issue_code == "unexpected_shape":
            summary.unexpected_shape += 1
    return summary


@router.get(
    "/sheet-quality-audit",
    response_model=InventorySheetQualityAuditResponse,
)
async def get_inventory_sheet_quality_audit(
    status: InventorySheetAuditStatus = Query(default="all"),
    issue_code: InventorySheetAuditIssueCode | None = Query(default=None),
    would_block_intake_assist: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> InventorySheetQualityAuditResponse:
    return await _build_quality_audit_response(
        db=db,
        status=status,
        issue_code=issue_code,
        would_block_intake_assist=would_block_intake_assist,
        limit=limit,
        offset=offset,
    )


async def _build_quality_audit_response(
    *,
    db: AsyncSession,
    status: InventorySheetAuditStatus,
    issue_code: InventorySheetAuditIssueCode | None,
    would_block_intake_assist: bool | None,
    limit: int,
    offset: int,
) -> InventorySheetQualityAuditResponse:
    report = await audit_inventory_sheet_quality(db)

    all_items = [
        InventorySheetQualityAuditItemContract(
            material_id=item.material_id,
            material_name=item.material_name,
            material_code=item.material_id,
            category=item.category,
            status=item.status,
            issue_code=item.issue_code,
            message=item.message,
            recommended_action=None if item.recommended_action == "N/A" else item.recommended_action,
            would_block_intake_assist=item.would_block_intake_assist,
        )
        for item in report.items
    ]

    filtered_items = all_items
    if status != "all":
        filtered_items = [item for item in filtered_items if item.status == status]
    if issue_code is not None:
        filtered_items = [item for item in filtered_items if item.issue_code == issue_code]
    if would_block_intake_assist is not None:
        filtered_items = [
            item
            for item in filtered_items
            if item.would_block_intake_assist == would_block_intake_assist
        ]

    paginated_items = filtered_items[offset : offset + limit]

    summary = InventorySheetQualityAuditSummary(
        total_records_checked=report.total_records_checked,
        valid_count=report.valid_count,
        not_applicable_count=report.not_applicable_count,
        invalid_count=report.invalid_count,
        would_block_intake_assist_count=sum(1 for item in all_items if item.would_block_intake_assist),
        by_issue_code=_build_issue_code_summary(all_items),
    )

    return InventorySheetQualityAuditResponse(
        source="backend",
        report_type="inventory_sheet_quality_audit",
        generated_at=datetime.now(timezone.utc).isoformat(),
        summary=summary,
        filters=InventorySheetQualityAuditFilters(
            status=status,
            issue_code=issue_code,
            would_block_intake_assist=would_block_intake_assist,
            limit=limit,
            offset=offset,
        ),
        items=paginated_items,
        warnings=[],
    )


@router.get("/sheet-quality-audit/export")
async def export_inventory_sheet_quality_audit(
    format: Literal["csv", "json"] = Query(default="csv"),
    status: InventorySheetAuditStatus = Query(default="all"),
    issue_code: InventorySheetAuditIssueCode | None = Query(default=None),
    would_block_intake_assist: bool | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    report = await _build_quality_audit_response(
        db=db,
        status=status,
        issue_code=issue_code,
        would_block_intake_assist=would_block_intake_assist,
        limit=limit,
        offset=offset,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if format == "csv":
        filename = f"inventory_sheet_quality_audit_{timestamp}.csv"
        csv_content = export_sheet_quality_audit_csv(report)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    filename = f"inventory_sheet_quality_audit_{timestamp}.json"
    payload = export_sheet_quality_audit_json(report)
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
