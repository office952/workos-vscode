"""Read-only ProductDefinition preview endpoint (Step 6)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.product_definition import ProductDefinitionPreview
from services.product_definition_builder_service import ProductDefinitionBuilderService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-product-definition"],
    dependencies=[Depends(get_current_user)],
)


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.get("/product-definition/{template_code}", response_model=ProductDefinitionPreview)
async def get_product_definition_preview(
    template_code: str,
    workspace_id: str | None = Query(default=None, description="Optional Intake V6 workspace for payload values"),
    db: AsyncSession = Depends(get_db),
) -> ProductDefinitionPreview:
    """
    Build and return a read-only ProductDefinition preview.

    Does not mutate DB, price quotes, or create orders/tasks.
    """
    service = ProductDefinitionBuilderService(db)
    preview = await service.build_preview(template_code, workspace_id=workspace_id)
    if preview is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "product_definition_preview_not_found",
                template_code=template_code,
                workspace_id=workspace_id,
            ),
        )
    return preview
