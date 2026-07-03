from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from services.commercial_markup_policy_service import (
    COMMERCIAL_MARKUP_POLICY_CONFIG,
    CommercialMarkupPolicyValidationError,
    dry_run_commercial_markup,
    list_commercial_markup_policies,
)


router = APIRouter(
    prefix="/api/admin/commercial-markup-policies",
    tags=["admin_commercial_markup_policies"],
    dependencies=[Depends(get_current_user)],
)


class CommercialMarkupDryRunBody(BaseModel):
    material_code: str = Field(..., min_length=1)
    quantity: float = Field(1.0, gt=0)


@router.get("/config")
async def get_commercial_markup_policy_config(
    _user: Dict[str, Any] = Depends(require_permission("inventory.view")),
) -> Dict[str, Any]:
    return COMMERCIAL_MARKUP_POLICY_CONFIG


@router.get("")
async def get_commercial_markup_policies(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(require_permission("inventory.view")),
) -> List[Dict[str, Any]]:
    return await list_commercial_markup_policies(db, status_filter=status)


@router.post("/dry-run")
async def run_commercial_markup_dry_run(
    body: CommercialMarkupDryRunBody,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(require_permission("inventory.view")),
) -> Dict[str, Any]:
    try:
        return await dry_run_commercial_markup(
            db,
            material_code=body.material_code,
            quantity=body.quantity,
        )
    except CommercialMarkupPolicyValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))