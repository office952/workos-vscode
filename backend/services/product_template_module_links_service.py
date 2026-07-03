import logging
from typing import Any, Dict, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_template_module_links import ProductTemplateModuleLink

logger = logging.getLogger(__name__)


class ProductTemplateModuleLinksService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(
        self,
        skip: int = 0,
        limit: int = 500,
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = select(ProductTemplateModuleLink)
        count_query = select(func.count(ProductTemplateModuleLink.id))

        if query_dict:
            for field, value in query_dict.items():
                if hasattr(ProductTemplateModuleLink, field):
                    query = query.where(getattr(ProductTemplateModuleLink, field) == value)
                    count_query = count_query.where(getattr(ProductTemplateModuleLink, field) == value)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        if sort:
            field_name = sort[1:] if sort.startswith("-") else sort
            if hasattr(ProductTemplateModuleLink, field_name):
                col = getattr(ProductTemplateModuleLink, field_name)
                query = query.order_by(col.desc() if sort.startswith("-") else col)
        else:
            query = query.order_by(ProductTemplateModuleLink.id.desc())

        result = await self.db.execute(query.offset(skip).limit(limit))
        return {"items": result.scalars().all(), "total": total, "skip": skip, "limit": limit}

    async def get_by_id(self, link_id: int) -> Optional[ProductTemplateModuleLink]:
        result = await self.db.execute(
            select(ProductTemplateModuleLink).where(ProductTemplateModuleLink.id == link_id)
        )
        return result.scalar_one_or_none()

    async def get_existing(
        self,
        parent_template_code: str,
        module_template_code: str,
        trigger_field: str,
    ) -> Optional[ProductTemplateModuleLink]:
        result = await self.db.execute(
            select(ProductTemplateModuleLink).where(
                and_(
                    ProductTemplateModuleLink.parent_template_code == parent_template_code,
                    ProductTemplateModuleLink.module_template_code == module_template_code,
                    ProductTemplateModuleLink.trigger_field == trigger_field,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, data: Dict[str, Any]) -> ProductTemplateModuleLink:
        obj = ProductTemplateModuleLink(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info("Created product template module link id=%s", obj.id)
        return obj

    async def update(self, link_id: int, data: Dict[str, Any]) -> Optional[ProductTemplateModuleLink]:
        obj = await self.get_by_id(link_id)
        if obj is None:
            return None
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        logger.info("Updated product template module link id=%s", obj.id)
        return obj

    async def upsert_by_contract(self, data: Dict[str, Any]) -> tuple[ProductTemplateModuleLink, str]:
        existing = await self.get_existing(
            str(data["parent_template_code"]),
            str(data["module_template_code"]),
            str(data["trigger_field"]),
        )
        if existing is None:
            return await self.create(data), "created"
        updated = await self.update(existing.id, data)
        return updated or existing, "updated"