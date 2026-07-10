"""Read-only ProductAggregate endpoint."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.product_aggregate import ProductAggregate
from services.product_aggregate_service import ProductAggregateService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-aggregate"],
    dependencies=[Depends(get_current_user)],
)


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.get("/aggregate/{template_code}", response_model=ProductAggregate)
async def get_product_aggregate(
    template_code: str,
    workspace_id: str | None = Query(default=None, description="Optional Intake V6 workspace for composed aggregate"),
    db: AsyncSession = Depends(get_db),
) -> ProductAggregate:
    """
    Build and return a read-only ProductAggregate for the given template_code.

    Merges parent template row, blueprint dossier, and linked child modules.
    When workspace_id is provided, composes confirmed linked logo segments from
    ProductDefinition preview without re-resolving bindings independently.
    Does not mutate DB. Returns warnings/conflicts in body when parent is minimal.
    """
    service = ProductAggregateService(db)
    if workspace_id:
        aggregate = await service.build_for_workspace(template_code, workspace_id)
    else:
        aggregate = await service.build(template_code)
    if aggregate is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope("template_not_found", template_code=template_code),
        )
    return aggregate
