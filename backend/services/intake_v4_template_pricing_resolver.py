"""Resolve material unit costs from inventory_materials DB, falling back to legacy constants.

Called by material breakdown, RAL paint, vinyl catalog, and consumable services
so they no longer rely on hardcoded Python constants for pricing.

Pattern: load once per request via `load_template_material_prices(db)`,
then pass the dict to individual service functions.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from services.inventory_materials_admin_service import load_material_cost_dict

logger = logging.getLogger(__name__)

# Legacy fallback constants — used ONLY when DB row is missing or inactive.
_FALLBACK_PRICES: Dict[str, float] = {
    # Vinyl materials (EUR/m²)
    "MAT-ORACAL-651": 9.0,
    "MAT-VINYL-PRINT": 1.5,
    "MAT-VINYL-PRINT-LAMINATED": 10.0,
    # RAL paint (EUR/tub)
    "MAT-VOPSEA-RAL": 10.0,
    # Print / lamination service (EUR/m²)
    "SVC-PRINT-SERVICE": 8.5,
    "SVC-LAMINATION-SERVICE": 5.0,
    # Consumables (RON)
    "MAT-CONSUMABILE-MONTAJ": 5.0,
}

# Exchange rate fallback
FALLBACK_EUR_RATE_RON = 5.1


async def load_template_material_prices(
    db: Optional[AsyncSession] = None,
) -> Dict[str, float]:
    """Load active material prices from inventory_materials DB.

    Returns {material_code: unit_cost} for all active rows.
    Callers should use `resolve_price()` to get a price with fallback.
    """
    try:
        return await load_material_cost_dict(db)
    except Exception:
        logger.warning("Failed to load material prices from DB, using fallbacks", exc_info=True)
        return {}


def resolve_price(
    prices: Dict[str, float],
    code: str,
    fallback: float | None = None,
) -> float | None:
    """Get price for material code: DB first, then explicit fallback, then legacy constant."""
    if code in prices:
        return prices[code]
    if fallback is not None:
        return fallback
    return _FALLBACK_PRICES.get(code)


def resolve_price_or_zero(
    prices: Dict[str, float],
    code: str,
    fallback: float = 0.0,
) -> float:
    """Get price for material code, never None."""
    return resolve_price(prices, code, fallback) or 0.0
