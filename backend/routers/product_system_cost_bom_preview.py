"""Read-only aggregate-expanded cost BOM preview endpoint (Step 7B)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.aggregate_cost_bom import AggregateExpandedCostBom
from services.aggregate_cost_bom_adapter import AggregateCostBomBuilderService
from services.template_architecture_scope import require_canonical_template_code

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-cost-bom"],
    dependencies=[Depends(get_current_user)],
)


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.get("/cost-bom-preview/{template_code}", response_model=AggregateExpandedCostBom)
async def get_cost_bom_preview(
    template_code: str,
    workspace_id: str | None = Query(default=None, description="Optional Intake V6 workspace for payload values"),
    db: AsyncSession = Depends(get_db),
) -> AggregateExpandedCostBom:
    """
    Build read-only aggregate-expanded cost BOM preview.

    Does not calculate final price, persist quotes, or mutate DB.
    """
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
                canonical_template_code=identity.canonical_template_code,
                resolution_type=identity.resolution_type,
                legacy_alias_used=identity.legacy_alias_used,
                resolution_source=identity.resolution_source,
            ),
        )

    canonical = identity.canonical_template_code
    service = AggregateCostBomBuilderService(db)
    preview = await service.build_preview(canonical, workspace_id=workspace_id)
    if preview is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "cost_bom_preview_not_found",
                template_code=template_code,
                workspace_id=workspace_id,
            ),
        )
    return preview
