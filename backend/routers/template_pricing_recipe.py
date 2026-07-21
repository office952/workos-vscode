"""Read-only Template Pricing Studio recipe endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.template_pricing_recipe import TemplatePricingRecipeResponse
from services.template_architecture_scope import require_canonical_template_code
from services.template_pricing_recipe_service import TemplatePricingRecipeService

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-template-pricing"],
    dependencies=[Depends(get_current_user)],
)


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.get(
    "/templates/{template_code}/pricing",
    response_model=TemplatePricingRecipeResponse,
)
async def get_template_pricing_recipe(
    template_code: str,
    workspace_id: str | None = Query(
        default=None,
        description="Optional workspace id reserved for future payload-aware preview",
    ),
    db: AsyncSession = Depends(get_db),
) -> TemplatePricingRecipeResponse:
    """Compose template recipe + catalog resolution. Read-only; no rate invention."""
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
                canonical_template_code=identity.canonical_template_code,
                resolution_type=identity.resolution_type,
            ),
        )

    canonical = identity.canonical_template_code
    service = TemplatePricingRecipeService(db)
    recipe = await service.build_recipe(canonical, workspace_id=workspace_id)
    if recipe is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "template_pricing_recipe_not_found",
                template_code=template_code,
            ),
        )
    return recipe
