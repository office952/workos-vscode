import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory_materials import Inventory_materials
from services.inventory_sheet_format import validate_sheet_format_payload

logger = logging.getLogger(__name__)

STOCK_CURRENT_UPDATE_ERROR = "stock_current_update_requires_stock_movement"


# ------------------ Service Layer ------------------
class Inventory_materialsService:
    """Service layer for Inventory_materials operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Optional[Inventory_materials]:
        """Create a new inventory_materials"""
        try:
            validate_sheet_format_payload(data)
            obj = Inventory_materials(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created inventory_materials with id: {obj.id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating inventory_materials: {str(e)}")
            raise

    async def get_by_id(self, obj_id: int) -> Optional[Inventory_materials]:
        """Get inventory_materials by ID"""
        try:
            query = select(Inventory_materials).where(Inventory_materials.id == obj_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching inventory_materials {obj_id}: {str(e)}")
            raise

    async def get_list(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of inventory_materialss"""
        try:
            query = select(Inventory_materials)
            count_query = select(func.count(Inventory_materials.id))
            
            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(Inventory_materials, field):
                        query = query.where(getattr(Inventory_materials, field) == value)
                        count_query = count_query.where(getattr(Inventory_materials, field) == value)
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith('-'):
                    field_name = sort[1:]
                    if hasattr(Inventory_materials, field_name):
                        query = query.order_by(getattr(Inventory_materials, field_name).desc())
                else:
                    if hasattr(Inventory_materials, sort):
                        query = query.order_by(getattr(Inventory_materials, sort))
            else:
                query = query.order_by(Inventory_materials.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching inventory_materials list: {str(e)}")
            raise

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> Optional[Inventory_materials]:
        """Update inventory_materials"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Inventory_materials {obj_id} not found for update")
                return None

            if "stock_current" in update_data and update_data["stock_current"] is not None:
                existing_stock = obj.stock_current
                incoming_stock = update_data["stock_current"]
                if existing_stock != incoming_stock:
                    raise ValueError(STOCK_CURRENT_UPDATE_ERROR)

            merged = {
                "sheet_format_type": obj.sheet_format_type,
                "sheet_width": obj.sheet_width,
                "sheet_height": obj.sheet_height,
                "sheet_unit": obj.sheet_unit,
                "sheet_thickness": obj.sheet_thickness,
                "sheet_thickness_unit": obj.sheet_thickness_unit,
                "usable_width": obj.usable_width,
                "usable_height": obj.usable_height,
                "format_source": obj.format_source,
                "format_verified": obj.format_verified,
                "format_notes": obj.format_notes,
            }
            merged.update(update_data)
            validate_sheet_format_payload(merged)

            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated inventory_materials {obj_id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating inventory_materials {obj_id}: {str(e)}")
            raise

    async def delete(self, obj_id: int) -> bool:
        """Delete inventory_materials"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Inventory_materials {obj_id} not found for deletion")
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted inventory_materials {obj_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting inventory_materials {obj_id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[Inventory_materials]:
        """Get inventory_materials by any field"""
        try:
            if not hasattr(Inventory_materials, field_name):
                raise ValueError(f"Field {field_name} does not exist on Inventory_materials")
            result = await self.db.execute(
                select(Inventory_materials).where(getattr(Inventory_materials, field_name) == field_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching inventory_materials by {field_name}: {str(e)}")
            raise

    async def list_by_field(
        self, field_name: str, field_value: Any, skip: int = 0, limit: int = 20
    ) -> List[Inventory_materials]:
        """Get list of inventory_materialss filtered by field"""
        try:
            if not hasattr(Inventory_materials, field_name):
                raise ValueError(f"Field {field_name} does not exist on Inventory_materials")
            result = await self.db.execute(
                select(Inventory_materials)
                .where(getattr(Inventory_materials, field_name) == field_value)
                .offset(skip)
                .limit(limit)
                .order_by(Inventory_materials.id.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching inventory_materialss by {field_name}: {str(e)}")
            raise