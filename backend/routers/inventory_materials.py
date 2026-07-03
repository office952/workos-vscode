import json
import logging
from typing import Any, Dict, List, Optional

from datetime import datetime, date

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from services.inventory_materials import Inventory_materialsService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/inventory_materials",
    tags=["inventory_materials"],
    dependencies=[Depends(get_current_user)],
)

SUPPORTED_QUERY_OPERATORS = ["$eq"]


def _parse_query_or_400(raw_query: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw_query:
        return None
    try:
        parsed = json.loads(raw_query)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid query JSON format")

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_query_shape",
                "message": "Query must be a JSON object",
            },
        )

    for _field, value in parsed.items():
        if isinstance(value, dict):
            operator = next(
                (k for k in value.keys() if isinstance(k, str) and k.startswith("$")),
                "object_value",
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "unsupported_query_operator",
                    "operator": operator,
                    "supported_operators": SUPPORTED_QUERY_OPERATORS,
                },
            )

    return parsed


# ---------- Pydantic Schemas ----------
class Inventory_materialsData(BaseModel):
    """Entity data schema (for create/update)"""
    code: str
    name: str
    category: str = None
    unit: str
    stock_current: float = None
    stock_min: float = None
    stock_max: float = None
    unit_cost: float = None
    currency: str = None
    vat_percent: float = None
    valid_from: datetime = None
    supplier: str = None
    supplier_id: int = None
    source_name: str = None
    source_url: str = None
    source_checked_at: datetime = None
    source_notes: str = None
    last_restocked: str = None
    consumption_rate: float = None
    location: str = None
    sheet_format_type: str = None
    sheet_width: float = None
    sheet_height: float = None
    sheet_unit: str = None
    sheet_thickness: float = None
    sheet_thickness_unit: str = None
    usable_width: float = None
    usable_height: float = None
    format_source: str = None
    format_verified: bool = None
    format_notes: str = None


class Inventory_materialsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    stock_current: Optional[float] = None
    stock_min: Optional[float] = None
    stock_max: Optional[float] = None
    unit_cost: Optional[float] = None
    currency: Optional[str] = None
    vat_percent: Optional[float] = None
    valid_from: Optional[datetime] = None
    supplier: Optional[str] = None
    supplier_id: Optional[int] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_checked_at: Optional[datetime] = None
    source_notes: Optional[str] = None
    last_restocked: Optional[str] = None
    consumption_rate: Optional[float] = None
    location: Optional[str] = None
    sheet_format_type: Optional[str] = None
    sheet_width: Optional[float] = None
    sheet_height: Optional[float] = None
    sheet_unit: Optional[str] = None
    sheet_thickness: Optional[float] = None
    sheet_thickness_unit: Optional[str] = None
    usable_width: Optional[float] = None
    usable_height: Optional[float] = None
    format_source: Optional[str] = None
    format_verified: Optional[bool] = None
    format_notes: Optional[str] = None


class Inventory_materialsResponse(BaseModel):
    """Entity response schema"""
    id: int
    code: str
    name: str
    category: Optional[str] = None
    unit: str
    stock_current: Optional[float] = None
    stock_min: Optional[float] = None
    stock_max: Optional[float] = None
    unit_cost: Optional[float] = None
    currency: Optional[str] = None
    vat_percent: Optional[float] = None
    valid_from: Optional[datetime] = None
    supplier: Optional[str] = None
    supplier_id: Optional[int] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_checked_at: Optional[datetime] = None
    source_notes: Optional[str] = None
    last_restocked: Optional[str] = None
    consumption_rate: Optional[float] = None
    location: Optional[str] = None
    sheet_format_type: Optional[str] = None
    sheet_width: Optional[float] = None
    sheet_height: Optional[float] = None
    sheet_unit: Optional[str] = None
    sheet_thickness: Optional[float] = None
    sheet_thickness_unit: Optional[str] = None
    usable_width: Optional[float] = None
    usable_height: Optional[float] = None
    format_source: Optional[str] = None
    format_verified: Optional[bool] = None
    format_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Inventory_materialsListResponse(BaseModel):
    """List response schema"""
    items: List[Inventory_materialsResponse]
    total: int
    skip: int
    limit: int


class Inventory_materialsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Inventory_materialsData]


class Inventory_materialsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Inventory_materialsUpdateData


class Inventory_materialsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Inventory_materialsBatchUpdateItem]


class Inventory_materialsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Inventory_materialsListResponse)
async def query_inventory_materialss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query inventory_materialss with filtering, sorting, and pagination"""
    logger.debug(f"Querying inventory_materialss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Inventory_materialsService(db)
    try:
        query_dict = _parse_query_or_400(query)
        
        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
        )
        logger.debug(f"Found {result['total']} inventory_materialss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying inventory_materialss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Inventory_materialsListResponse)
async def query_inventory_materialss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query inventory_materialss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying inventory_materialss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Inventory_materialsService(db)
    try:
        query_dict = _parse_query_or_400(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} inventory_materialss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying inventory_materialss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Inventory_materialsResponse)
async def get_inventory_materials(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single inventory_materials by ID"""
    logger.debug(f"Fetching inventory_materials with id: {id}, fields={fields}")
    
    service = Inventory_materialsService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Inventory_materials with id {id} not found")
            raise HTTPException(status_code=404, detail="Inventory_materials not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching inventory_materials {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Inventory_materialsResponse, status_code=201)
async def create_inventory_materials(
    data: Inventory_materialsData,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("inventory.create")),
):
    """Create a new inventory_materials"""
    logger.debug(f"Creating new inventory_materials with data: {data}")
    
    service = Inventory_materialsService(db)
    try:
        result = await service.create(data.model_dump())
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create inventory_materials")
        
        logger.info(f"Inventory_materials created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating inventory_materials: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating inventory_materials: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Inventory_materialsResponse], status_code=201)
async def create_inventory_materialss_batch(
    request: Inventory_materialsBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("inventory.create")),
):
    """Create multiple inventory_materialss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} inventory_materialss")
    
    service = Inventory_materialsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump())
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} inventory_materialss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Inventory_materialsResponse])
async def update_inventory_materialss_batch(
    request: Inventory_materialsBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("inventory.update")),
):
    """Update multiple inventory_materialss in a single request"""
    logger.debug(f"Batch updating {len(request.items)} inventory_materialss")
    
    service = Inventory_materialsService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict)
            if result:
                results.append(result)

        logger.info(f"Batch updated {len(results)} inventory_materialss successfully")
        return results
    except ValueError as e:
        await db.rollback()
        logger.error(f"Validation error in batch update: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Inventory_materialsResponse)
async def update_inventory_materials(
    id: int,
    data: Inventory_materialsUpdateData,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("inventory.update")),
):
    """Update an existing inventory_materials"""
    logger.debug(f"Updating inventory_materials {id} with data: {data}")

    service = Inventory_materialsService(db)
    try:
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        result = await service.update(id, update_dict)
        if not result:
            logger.warning(f"Inventory_materials with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Inventory_materials not found")
        
        logger.info(f"Inventory_materials {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating inventory_materials {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating inventory_materials {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_inventory_materialss_batch(
    request: Inventory_materialsBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("inventory.delete")),
):
    """Delete multiple inventory_materialss by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} inventory_materialss")
    
    service = Inventory_materialsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} inventory_materialss successfully")
        return {"message": f"Successfully deleted {deleted_count} inventory_materialss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_inventory_materials(
    id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("inventory.delete")),
):
    """Delete a single inventory_materials by ID"""
    logger.debug(f"Deleting inventory_materials with id: {id}")
    
    service = Inventory_materialsService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Inventory_materials with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Inventory_materials not found")
        
        logger.info(f"Inventory_materials {id} deleted successfully")
        return {"message": "Inventory_materials deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting inventory_materials {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")