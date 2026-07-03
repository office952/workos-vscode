from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_admin_user
from schemas.auth import UserResponse
from schemas.inventory import (
    InventorySheetRemediationExecutionRequest,
    InventorySheetRemediationExecutionResponse,
)
from services.inventory_sheet_remediation_service import (
    InventorySheetRemediationExecutionError,
    apply_inventory_sheet_remediation,
)

router = APIRouter(
    prefix="/api/v1/admin/inventory",
    tags=["admin_inventory_sheet_remediation_execution"],
    dependencies=[Depends(get_admin_user)],
)


@router.patch(
    "/materials/{material_id}/sheet-format-remediation",
    response_model=InventorySheetRemediationExecutionResponse,
)
async def patch_single_material_sheet_remediation(
    material_id: str,
    body: InventorySheetRemediationExecutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_admin_user),
) -> InventorySheetRemediationExecutionResponse:
    try:
        return await apply_inventory_sheet_remediation(
            db=db,
            current_user=current_user,
            material_id=material_id,
            body=body,
        )
    except InventorySheetRemediationExecutionError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": "inventory_sheet_remediation_error",
                "code": exc.code,
                "field": exc.field,
                "message": exc.message,
            },
        )
