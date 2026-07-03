import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.quotes import Quotes

logger = logging.getLogger(__name__)


# ------------------ Service Layer ------------------
class QuotesService:
    """Service layer for Quotes operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Optional[Quotes]:
        """Create a new quotes"""
        try:
            obj = Quotes(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created quotes with id: {obj.id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating quotes: {str(e)}")
            raise

    async def get_by_id(self, obj_id: int) -> Optional[Quotes]:
        """Get quotes by ID"""
        try:
            query = select(Quotes).where(Quotes.id == obj_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching quotes {obj_id}: {str(e)}")
            raise

    async def get_list(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of quotess"""
        try:
            query = select(Quotes)
            count_query = select(func.count(Quotes.id))
            
            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(Quotes, field):
                        query = query.where(getattr(Quotes, field) == value)
                        count_query = count_query.where(getattr(Quotes, field) == value)
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith('-'):
                    field_name = sort[1:]
                    if hasattr(Quotes, field_name):
                        query = query.order_by(getattr(Quotes, field_name).desc())
                else:
                    if hasattr(Quotes, sort):
                        query = query.order_by(getattr(Quotes, sort))
            else:
                query = query.order_by(Quotes.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching quotes list: {str(e)}")
            raise

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> Optional[Quotes]:
        """Update quotes"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Quotes {obj_id} not found for update")
                return None
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated quotes {obj_id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating quotes {obj_id}: {str(e)}")
            raise

    async def delete(self, obj_id: int) -> bool:
        """Delete quotes"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Quotes {obj_id} not found for deletion")
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted quotes {obj_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting quotes {obj_id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[Quotes]:
        """Get quotes by any field"""
        try:
            if not hasattr(Quotes, field_name):
                raise ValueError(f"Field {field_name} does not exist on Quotes")
            result = await self.db.execute(
                select(Quotes).where(getattr(Quotes, field_name) == field_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching quotes by {field_name}: {str(e)}")
            raise

    async def list_by_field(
        self, field_name: str, field_value: Any, skip: int = 0, limit: int = 20
    ) -> List[Quotes]:
        """Get list of quotess filtered by field"""
        try:
            if not hasattr(Quotes, field_name):
                raise ValueError(f"Field {field_name} does not exist on Quotes")
            result = await self.db.execute(
                select(Quotes)
                .where(getattr(Quotes, field_name) == field_value)
                .offset(skip)
                .limit(limit)
                .order_by(Quotes.id.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching quotess by {field_name}: {str(e)}")
            raise