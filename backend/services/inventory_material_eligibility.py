from __future__ import annotations

from typing import Optional


def is_stock_operational_material(status: Optional[str]) -> bool:
    """Return True when a material status is stock-operational."""
    return status in (None, "active")
