import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.orders import Orders

logger = logging.getLogger(__name__)


# ------------------ Service Layer ------------------
class OrdersService:
    """Service layer for Orders operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Optional[Orders]:
        """Create a new orders"""
        try:
            obj = Orders(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created orders with id: {obj.id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating orders: {str(e)}")
            raise

    async def get_by_id(self, obj_id: int) -> Optional[Orders]:
        """Get orders by ID"""
        try:
            query = select(Orders).where(Orders.id == obj_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching orders {obj_id}: {str(e)}")
            raise

    async def get_list(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of orderss"""
        try:
            query = select(Orders)
            count_query = select(func.count(Orders.id))
            
            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(Orders, field):
                        query = query.where(getattr(Orders, field) == value)
                        count_query = count_query.where(getattr(Orders, field) == value)
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith('-'):
                    field_name = sort[1:]
                    if hasattr(Orders, field_name):
                        query = query.order_by(getattr(Orders, field_name).desc())
                else:
                    if hasattr(Orders, sort):
                        query = query.order_by(getattr(Orders, sort))
            else:
                query = query.order_by(Orders.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching orders list: {str(e)}")
            raise

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> Optional[Orders]:
        """Update orders"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Orders {obj_id} not found for update")
                return None
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated orders {obj_id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating orders {obj_id}: {str(e)}")
            raise

    async def delete(self, obj_id: int) -> bool:
        """Delete orders"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Orders {obj_id} not found for deletion")
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted orders {obj_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting orders {obj_id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[Orders]:
        """Get orders by any field"""
        try:
            if not hasattr(Orders, field_name):
                raise ValueError(f"Field {field_name} does not exist on Orders")
            result = await self.db.execute(
                select(Orders).where(getattr(Orders, field_name) == field_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching orders by {field_name}: {str(e)}")
            raise

    async def list_by_field(
        self, field_name: str, field_value: Any, skip: int = 0, limit: int = 20
    ) -> List[Orders]:
        """Get list of orderss filtered by field"""
        try:
            if not hasattr(Orders, field_name):
                raise ValueError(f"Field {field_name} does not exist on Orders")
            result = await self.db.execute(
                select(Orders)
                .where(getattr(Orders, field_name) == field_value)
                .offset(skip)
                .limit(limit)
                .order_by(Orders.id.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching orderss by {field_name}: {str(e)}")
            raise