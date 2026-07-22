"""MATERIAL_MARKET_PRICE_REGISTRY_V1 — read-only material purchase truth."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.material_market_price_registry import (
    MaterialMarketPriceRecord,
    MaterialMarketPriceRegistryResponse,
)
from services.material_market_price_registry_service import (
    MaterialMarketPriceRegistryService,
)

router = APIRouter(
    prefix="/api/v1/pricing",
    tags=["pricing-material-market-price-registry"],
    dependencies=[Depends(get_current_user)],
)


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.get(
    "/material-market-prices",
    response_model=MaterialMarketPriceRegistryResponse,
)
async def get_material_market_prices(
    include_history: bool = Query(default=True),
    active_templates_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> MaterialMarketPriceRegistryResponse:
    """Inventory purchase/market price registry — no invented prices."""
    return await MaterialMarketPriceRegistryService(db).build_registry(
        include_history=include_history,
        active_templates_only=active_templates_only,
    )


@router.get(
    "/material-market-prices/{material_code}",
    response_model=MaterialMarketPriceRecord,
)
async def get_material_market_price(
    material_code: str,
    db: AsyncSession = Depends(get_db),
) -> MaterialMarketPriceRecord:
    row = await MaterialMarketPriceRegistryService(db).get_material(material_code)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "material_market_price_not_found",
                material_code=material_code,
            ),
        )
    return row
