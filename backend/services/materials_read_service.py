"""
M22 — Materials Registry Read Service.

Read-only service that queries the `materials` table created by M22 DB execution.

Safety guarantees:
  - No DB writes. No mutations. No side effects.
  - Idempotent: same input + same DB state → same output.
  - Gated by `settings.registry_materials_live` at the caller level.

Forbidden:
  - No INSERT / UPDATE / DELETE.
  - No cost calculations (Cost Engine boundary — BLK-18).
  - No stock mutations (Inventory/OC boundary).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MaterialsReadService:
    """Read-only access to public.materials (M22 registry)."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_code(self, material_code: str) -> Optional[Dict[str, Any]]:
        """Fetch a single material by its unique code.

        Returns None if not found. Never writes.
        """
        sql = text(
            "SELECT id, code, name, description, category, unit, "
            "stock_available, minimum_stock, is_active, created_at, updated_at "
            "FROM materials WHERE code = :code LIMIT 1"
        )
        result = await self._db.execute(sql, {"code": material_code})
        row = result.mappings().first()
        if not row:
            return None
        return dict(row)

    async def exists(self, material_code: str) -> bool:
        """Check if a material code exists in the registry."""
        sql = text("SELECT 1 FROM materials WHERE code = :code LIMIT 1")
        result = await self._db.execute(sql, {"code": material_code})
        return result.scalar() is not None

    async def is_active(self, material_code: str) -> Optional[bool]:
        """Check if a material is active. Returns None if not found."""
        sql = text(
            "SELECT is_active FROM materials WHERE code = :code LIMIT 1"
        )
        result = await self._db.execute(sql, {"code": material_code})
        row = result.scalar()
        if row is None:
            return None
        return bool(row)

    async def material_available(self, material_code: str) -> Dict[str, Any]:
        """Check material readiness: exists, is_active, has stock > 0.

        Returns a dict with:
          - found: bool
          - active: bool (False if not found)
          - has_stock: bool (False if not found or stock_available <= 0)
          - material: dict or None

        This method does NOT enforce cost validation (BLK-18 boundary).
        """
        material = await self.get_by_code(material_code)
        if material is None:
            return {
                "found": False,
                "active": False,
                "has_stock": False,
                "material": None,
            }
        is_active = bool(material.get("is_active", False))
        stock = float(material.get("stock_available", 0))
        return {
            "found": True,
            "active": is_active,
            "has_stock": stock > 0,
            "material": material,
        }

    async def check_readiness(self) -> Dict[str, Any]:
        """Check if the materials registry is ready (table exists, has data).

        Returns:
          - ready: bool
          - row_count: int
          - active_count: int
        """
        try:
            count_sql = text("SELECT COUNT(*) FROM materials")
            active_sql = text("SELECT COUNT(*) FROM materials WHERE is_active = true")
            total = int((await self._db.execute(count_sql)).scalar() or 0)
            active = int((await self._db.execute(active_sql)).scalar() or 0)
            return {
                "ready": total > 0,
                "row_count": total,
                "active_count": active,
            }
        except Exception as exc:
            logger.warning("Materials registry readiness check failed: %s", exc)
            return {
                "ready": False,
                "row_count": 0,
                "active_count": 0,
            }

    async def list_all_codes(self, active_only: bool = True) -> List[str]:
        """Return all material codes (optionally only active ones)."""
        if active_only:
            sql = text(
                "SELECT code FROM materials WHERE is_active = true ORDER BY code ASC"
            )
        else:
            sql = text("SELECT code FROM materials ORDER BY code ASC")
        result = await self._db.execute(sql)
        return [row[0] for row in result.all()]