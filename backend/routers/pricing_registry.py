"""Pricing Registry — template-driven quote pricing aggregation (read-only)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.pricing_registry_service import PricingRegistryService

router = APIRouter(
    prefix="/api/v1/pricing",
    tags=["pricing_registry"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/registry")
async def get_pricing_registry(
    template_code: Optional[str] = Query(
        None, description="Filter to items used by this template (or Product 001 alias)"
    ),
    include_all_inventory: bool = Query(
        False,
        description="Debug/admin: include all inventory materials, not only template-used",
    ),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.view")),
) -> Dict[str, Any]:
    """Unified template-driven Pricing Registry for quote calculation."""
    service = PricingRegistryService(db)
    return await service.build_registry(
        template_filter=template_code,
        include_all_inventory=include_all_inventory,
    )
