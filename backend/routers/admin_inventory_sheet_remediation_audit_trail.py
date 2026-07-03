from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_admin_user
from schemas.inventory import (
    InventorySheetAuditIssueCode,
    InventorySheetRemediationAuditTrailResponse,
    InventorySheetRemediationOperationStatus,
)
from services.inventory_sheet_remediation_audit_report import (
    InventorySheetRemediationAuditTrailError,
    get_inventory_sheet_remediation_audit_trail,
)
from services.inventory_sheet_export_service import (
    export_sheet_remediation_audit_trail_csv,
    export_sheet_remediation_audit_trail_json,
)

router = APIRouter(
    prefix="/api/v1/admin/inventory",
    tags=["admin_inventory_sheet_remediation_audit_trail"],
    dependencies=[Depends(get_admin_user)],
)


@router.get(
    "/sheet-remediation-audit-trail",
    response_model=InventorySheetRemediationAuditTrailResponse,
)
async def get_sheet_remediation_audit_trail(
    material_id: str | None = Query(default=None),
    issue_code: InventorySheetAuditIssueCode | None = Query(default=None),
    changed_by: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    operation_status: InventorySheetRemediationOperationStatus | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> InventorySheetRemediationAuditTrailResponse:
    try:
        return await get_inventory_sheet_remediation_audit_trail(
            db=db,
            material_id=material_id,
            issue_code=issue_code,
            changed_by=changed_by,
            date_from=date_from,
            date_to=date_to,
            operation_status=operation_status,
            limit=limit,
            offset=offset,
        )
    except InventorySheetRemediationAuditTrailError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": "inventory_sheet_remediation_audit_trail_error",
                "code": exc.code,
                "field": exc.field,
                "message": exc.message,
            },
        )


@router.get("/sheet-remediation-audit-trail/export")
async def export_sheet_remediation_audit_trail(
    format: Literal["csv", "json"] = Query(default="csv"),
    material_id: str | None = Query(default=None),
    issue_code: InventorySheetAuditIssueCode | None = Query(default=None),
    changed_by: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    operation_status: InventorySheetRemediationOperationStatus | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    try:
        report = await get_inventory_sheet_remediation_audit_trail(
            db=db,
            material_id=material_id,
            issue_code=issue_code,
            changed_by=changed_by,
            date_from=date_from,
            date_to=date_to,
            operation_status=operation_status,
            limit=limit,
            offset=offset,
        )
    except InventorySheetRemediationAuditTrailError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": "inventory_sheet_remediation_audit_trail_error",
                "code": exc.code,
                "field": exc.field,
                "message": exc.message,
            },
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if format == "csv":
        filename = f"inventory_sheet_remediation_audit_trail_{timestamp}.csv"
        csv_content = export_sheet_remediation_audit_trail_csv(report)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    filename = f"inventory_sheet_remediation_audit_trail_{timestamp}.json"
    payload = export_sheet_remediation_audit_trail_json(report)
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
