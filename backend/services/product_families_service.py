"""Product Families Registry service.

Provides CRUD operations for the canonical product families registry and a
matcher that maps a family_id to a product_template with explicit status.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_families import Product_families
from models.product_templates import Product_templates

logger = logging.getLogger(__name__)


class Product_familiesService:
    """CRUD service for product_families."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Product_families:
        obj = Product_families(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_by_id(self, obj_id: int) -> Optional[Product_families]:
        result = await self.db.execute(
            select(Product_families).where(Product_families.id == obj_id)
        )
        return result.scalar_one_or_none()

    async def get_by_family_id(self, family_id: str) -> Optional[Product_families]:
        result = await self.db.execute(
            select(Product_families).where(Product_families.family_id == family_id)
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        skip: int = 0,
        limit: int = 100,
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = select(Product_families)
        count_query = select(func.count(Product_families.id))
        if query_dict:
            for field, value in query_dict.items():
                if hasattr(Product_families, field):
                    query = query.where(getattr(Product_families, field) == value)
                    count_query = count_query.where(
                        getattr(Product_families, field) == value
                    )
        total = (await self.db.execute(count_query)).scalar()
        if sort:
            field_name = sort.lstrip("-")
            if hasattr(Product_families, field_name):
                col = getattr(Product_families, field_name)
                query = query.order_by(col.desc() if sort.startswith("-") else col)
        else:
            query = query.order_by(Product_families.family_id.asc())
        result = await self.db.execute(query.offset(skip).limit(limit))
        items = result.scalars().all()
        return {"items": items, "total": total, "skip": skip, "limit": limit}

    async def update(
        self, obj_id: int, update_data: Dict[str, Any]
    ) -> Optional[Product_families]:
        obj = await self.get_by_id(obj_id)
        if not obj:
            return None
        for key, value in update_data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj_id: int) -> bool:
        obj = await self.get_by_id(obj_id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True


async def find_template_by_family(
    db: AsyncSession, family_id: str
) -> Dict[str, Any]:
    """Canonical matcher: resolve a family_id to a product_template.

    Returns a dict with one of three statuses:
      - "ok":         a unique template was resolved (via default_template_id
                      or a single active template with that family_id).
      - "not_found":  family_id does not exist or no templates match.
      - "ambiguous":  multiple active templates match and no default is set.
    """
    if not family_id:
        return {
            "status": "not_found",
            "template": None,
            "candidates": [],
            "message": "family_id is required",
        }

    family_row = (
        await db.execute(
            select(Product_families).where(Product_families.family_id == family_id)
        )
    ).scalar_one_or_none()

    if not family_row:
        return {
            "status": "not_found",
            "template": None,
            "candidates": [],
            "message": f"Product family '{family_id}' not found in registry",
        }

    # 1. Explicit default template wins.
    if family_row.default_template_id:
        tpl = (
            await db.execute(
                select(Product_templates).where(
                    Product_templates.id == family_row.default_template_id
                )
            )
        ).scalar_one_or_none()
        if tpl:
            return {
                "status": "ok",
                "template": tpl,
                "candidates": [tpl],
                "message": "Resolved via default_template_id",
            }

    # 2. Match by family_id on template.
    tpl_rows = (
        await db.execute(
            select(Product_templates).where(
                Product_templates.family_id == family_id,
                (Product_templates.active.is_(True)) | (Product_templates.active.is_(None)),
            )
        )
    ).scalars().all()

    if len(tpl_rows) == 0:
        return {
            "status": "not_found",
            "template": None,
            "candidates": [],
            "message": f"No active templates found for family '{family_id}'",
        }
    if len(tpl_rows) == 1:
        return {
            "status": "ok",
            "template": tpl_rows[0],
            "candidates": tpl_rows,
            "message": "Resolved via unique family_id match",
        }
    return {
        "status": "ambiguous",
        "template": None,
        "candidates": tpl_rows,
        "message": (
            f"Multiple active templates ({len(tpl_rows)}) match family "
            f"'{family_id}' and no default_template_id is set"
        ),
    }


async def validate_family_id(db: AsyncSession, family_id: Optional[str]) -> bool:
    """Return True if family_id exists and is active, else False."""
    if not family_id:
        return False
    row = (
        await db.execute(
            select(Product_families).where(
                Product_families.family_id == family_id,
                Product_families.active.is_(True),
            )
        )
    ).scalar_one_or_none()
    return row is not None