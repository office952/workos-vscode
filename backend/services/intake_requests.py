import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.intake_requests import Intake_requests

logger = logging.getLogger(__name__)


# ------------------ Service Layer ------------------
class Intake_requestsService:
    """Service layer for Intake_requests operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Optional[Intake_requests]:
        """Create a new intake_requests"""
        try:
            obj = Intake_requests(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created intake_requests with id: {obj.id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating intake_requests: {str(e)}")
            raise

    async def get_by_id(self, obj_id: int) -> Optional[Intake_requests]:
        """Get intake_requests by ID"""
        try:
            query = select(Intake_requests).where(Intake_requests.id == obj_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching intake_requests {obj_id}: {str(e)}")
            raise

    async def get_list(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of intake_requestss"""
        try:
            query = select(Intake_requests)
            count_query = select(func.count(Intake_requests.id))
            
            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(Intake_requests, field):
                        query = query.where(getattr(Intake_requests, field) == value)
                        count_query = count_query.where(getattr(Intake_requests, field) == value)
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith('-'):
                    field_name = sort[1:]
                    if hasattr(Intake_requests, field_name):
                        query = query.order_by(getattr(Intake_requests, field_name).desc())
                else:
                    if hasattr(Intake_requests, sort):
                        query = query.order_by(getattr(Intake_requests, sort))
            else:
                query = query.order_by(Intake_requests.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching intake_requests list: {str(e)}")
            raise

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> Optional[Intake_requests]:
        """Update intake_requests"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Intake_requests {obj_id} not found for update")
                return None
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated intake_requests {obj_id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating intake_requests {obj_id}: {str(e)}")
            raise

    async def delete(self, obj_id: int) -> bool:
        """Delete intake_requests"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Intake_requests {obj_id} not found for deletion")
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted intake_requests {obj_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting intake_requests {obj_id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[Intake_requests]:
        """Get intake_requests by any field"""
        try:
            if not hasattr(Intake_requests, field_name):
                raise ValueError(f"Field {field_name} does not exist on Intake_requests")
            result = await self.db.execute(
                select(Intake_requests).where(getattr(Intake_requests, field_name) == field_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching intake_requests by {field_name}: {str(e)}")
            raise

    async def list_by_field(
        self, field_name: str, field_value: Any, skip: int = 0, limit: int = 20
    ) -> List[Intake_requests]:
        """Get list of intake_requestss filtered by field"""
        try:
            if not hasattr(Intake_requests, field_name):
                raise ValueError(f"Field {field_name} does not exist on Intake_requests")
            result = await self.db.execute(
                select(Intake_requests)
                .where(getattr(Intake_requests, field_name) == field_value)
                .offset(skip)
                .limit(limit)
                .order_by(Intake_requests.id.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching intake_requestss by {field_name}: {str(e)}")
            raise