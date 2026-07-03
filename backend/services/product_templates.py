import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_templates import Product_templates

logger = logging.getLogger(__name__)


# ------------------ Service Layer ------------------
class Product_templatesService:
    """Service layer for Product_templates operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Optional[Product_templates]:
        """Create a new product_templates"""
        try:
            obj = Product_templates(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created product_templates with id: {obj.id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating product_templates: {str(e)}")
            raise

    async def get_by_id(self, obj_id: int) -> Optional[Product_templates]:
        """Get product_templates by ID"""
        try:
            query = select(Product_templates).where(Product_templates.id == obj_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching product_templates {obj_id}: {str(e)}")
            raise

    async def get_list(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of product_templatess"""
        try:
            query = select(Product_templates)
            count_query = select(func.count(Product_templates.id))
            
            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(Product_templates, field):
                        query = query.where(getattr(Product_templates, field) == value)
                        count_query = count_query.where(getattr(Product_templates, field) == value)
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith('-'):
                    field_name = sort[1:]
                    if hasattr(Product_templates, field_name):
                        query = query.order_by(getattr(Product_templates, field_name).desc())
                else:
                    if hasattr(Product_templates, sort):
                        query = query.order_by(getattr(Product_templates, sort))
            else:
                query = query.order_by(Product_templates.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching product_templates list: {str(e)}")
            raise

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> Optional[Product_templates]:
        """Update product_templates"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Product_templates {obj_id} not found for update")
                return None
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated product_templates {obj_id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating product_templates {obj_id}: {str(e)}")
            raise

    async def delete(self, obj_id: int) -> bool:
        """Delete product_templates"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Product_templates {obj_id} not found for deletion")
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted product_templates {obj_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting product_templates {obj_id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[Product_templates]:
        """Get product_templates by any field"""
        try:
            if not hasattr(Product_templates, field_name):
                raise ValueError(f"Field {field_name} does not exist on Product_templates")
            result = await self.db.execute(
                select(Product_templates).where(getattr(Product_templates, field_name) == field_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching product_templates by {field_name}: {str(e)}")
            raise

    async def list_by_field(
        self, field_name: str, field_value: Any, skip: int = 0, limit: int = 20
    ) -> List[Product_templates]:
        """Get list of product_templatess filtered by field"""
        try:
            if not hasattr(Product_templates, field_name):
                raise ValueError(f"Field {field_name} does not exist on Product_templates")
            result = await self.db.execute(
                select(Product_templates)
                .where(getattr(Product_templates, field_name) == field_value)
                .offset(skip)
                .limit(limit)
                .order_by(Product_templates.id.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching product_templatess by {field_name}: {str(e)}")
            raise