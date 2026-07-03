import json
import logging
from typing import List, Optional

from datetime import datetime, date

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from services.product_templates import Product_templatesService
from services.product_families_service import validate_family_id
from services.product_template_contract import (
    TemplateContractError,
    validate_hierarchical_payload,
)

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/product_templates",
    tags=["product_templates"],
    dependencies=[Depends(get_current_user)],
)


# ---------- Pydantic Schemas ----------
class Product_templatesData(BaseModel):
    """Entity data schema (for create/update)"""
    template_code: str
    family_id: str = None
    family_name: str
    description: str = None
    components_json: str = None
    operations_json: str = None
    required_materials_json: str = None
    estimated_hours: float = None
    base_labor_rate: float = None
    base_margin_pct: float = None
    active: bool = None
    notes: str = None


class Product_templatesUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    template_code: Optional[str] = None
    family_id: Optional[str] = None
    family_name: Optional[str] = None
    description: Optional[str] = None
    components_json: Optional[str] = None
    operations_json: Optional[str] = None
    required_materials_json: Optional[str] = None
    estimated_hours: Optional[float] = None
    base_labor_rate: Optional[float] = None
    base_margin_pct: Optional[float] = None
    active: Optional[bool] = None
    notes: Optional[str] = None


class Product_templatesResponse(BaseModel):
    """Entity response schema"""
    id: int
    template_code: str
    family_id: Optional[str] = None
    family_name: str
    description: Optional[str] = None
    components_json: Optional[str] = None
    operations_json: Optional[str] = None
    required_materials_json: Optional[str] = None
    estimated_hours: Optional[float] = None
    base_labor_rate: Optional[float] = None
    base_margin_pct: Optional[float] = None
    active: Optional[bool] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Product_templatesListResponse(BaseModel):
    """List response schema"""
    items: List[Product_templatesResponse]
    total: int
    skip: int
    limit: int


class Product_templatesBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Product_templatesData]


class Product_templatesBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Product_templatesUpdateData


class Product_templatesBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Product_templatesBatchUpdateItem]


class Product_templatesBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Product_templatesListResponse)
async def query_product_templatess(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query product_templatess with filtering, sorting, and pagination"""
    logger.debug(f"Querying product_templatess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Product_templatesService(db)
    try:
        # Parse query JSON if provided
        query_dict = None
        if query:
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid query JSON format")
        
        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
        )
        logger.debug(f"Found {result['total']} product_templatess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying product_templatess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Product_templatesListResponse)
async def query_product_templatess_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query product_templatess with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying product_templatess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Product_templatesService(db)
    try:
        # Parse query JSON if provided
        query_dict = None
        if query:
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid query JSON format")

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} product_templatess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying product_templatess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=Product_templatesResponse)
async def get_product_templates(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single product_templates by ID"""
    logger.debug(f"Fetching product_templates with id: {id}, fields={fields}")
    
    service = Product_templatesService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Product_templates with id {id} not found")
            raise HTTPException(status_code=404, detail="Product_templates not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product_templates {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Product_templatesResponse, status_code=201)
async def create_product_templates(
    data: Product_templatesData,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("product_template.create")),
):
    """Create a new product_templates.

    Sprint #27 — Strict Contract Hardening:
      - Validates the hierarchical shape of components_json + operations_json
        + required_materials_json at the router boundary.
      - Returns HTTP 422 with precise field-level errors on any violation.
      - Normalizes the JSON fields (re-emits canonical flat mirrors derived
        from the hierarchical shape) before persistence.
    """
    logger.debug(f"Creating new product_templates with data: {data}")

    # Validate family_id against Product Families Registry if provided
    if data.family_id:
        is_valid = await validate_family_id(db, data.family_id)
        if not is_valid:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid family_id '{data.family_id}': not found in Product Families Registry or inactive",
            )

    # Sprint #27 — strict contract validation on CREATE.
    payload = data.model_dump()
    try:
        normalized = validate_hierarchical_payload(
            components_json=payload.get("components_json"),
            operations_json=payload.get("operations_json"),
            required_materials_json=payload.get("required_materials_json"),
        )
    except TemplateContractError as exc:
        logger.info(
            "Rejecting product_templates create — contract violation: %s", exc.errors
        )
        raise HTTPException(status_code=422, detail=exc.errors)
    payload.update(normalized)

    service = Product_templatesService(db)
    try:
        result = await service.create(payload)
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create product_templates")

        logger.info(f"Product_templates created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating product_templates: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating product_templates: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Product_templatesResponse], status_code=201)
async def create_product_templatess_batch(
    request: Product_templatesBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("product_template.create")),
):
    """Create multiple product_templatess in a single request"""
    logger.debug(f"Batch creating {len(request.items)} product_templatess")
    
    service = Product_templatesService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump())
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} product_templatess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Product_templatesResponse])
async def update_product_templatess_batch(
    request: Product_templatesBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("product_template.update")),
):
    """Update multiple product_templatess in a single request"""
    logger.debug(f"Batch updating {len(request.items)} product_templatess")
    
    service = Product_templatesService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict)
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} product_templatess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Product_templatesResponse)
async def update_product_templates(
    id: int,
    data: Product_templatesUpdateData,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("product_template.update")),
):
    """Update an existing product_templates.

    Sprint #27 — Strict Contract Hardening:
      - If the update payload includes ANY of the three JSON fields
        (components_json / operations_json / required_materials_json), then
        ALL THREE must be present and jointly valid. Partial updates of the
        template shape are disallowed because the flat mirrors are derived
        from components_json.
      - Validation errors return HTTP 422 with precise field-level errors.
    """
    logger.debug(f"Updating product_templates {id} with data: {data}")

    # Validate family_id against Product Families Registry if provided in update
    if data.family_id is not None:
        is_valid = await validate_family_id(db, data.family_id)
        if not is_valid:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid family_id '{data.family_id}': not found in Product Families Registry or inactive",
            )

    # Sprint #27 — strict contract validation on UPDATE (all-or-nothing on
    # the three JSON fields).
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    shape_keys = {"components_json", "operations_json", "required_materials_json"}
    touched_shape = shape_keys & set(update_dict.keys())
    if touched_shape:
        missing = shape_keys - set(update_dict.keys())
        if missing:
            raise HTTPException(
                status_code=422,
                detail=[
                    {
                        "path": key,
                        "code": "SHAPE_PARTIAL_UPDATE_FORBIDDEN",
                        "detail": (
                            "components_json / operations_json / required_materials_json "
                            "must be updated together; missing: "
                            + ", ".join(sorted(missing))
                        ),
                    }
                    for key in sorted(missing)
                ],
            )
        try:
            normalized = validate_hierarchical_payload(
                components_json=update_dict.get("components_json"),
                operations_json=update_dict.get("operations_json"),
                required_materials_json=update_dict.get("required_materials_json"),
            )
        except TemplateContractError as exc:
            logger.info(
                "Rejecting product_templates update — contract violation: %s",
                exc.errors,
            )
            raise HTTPException(status_code=422, detail=exc.errors)
        update_dict.update(normalized)

    service = Product_templatesService(db)
    try:
        result = await service.update(id, update_dict)
        if not result:
            logger.warning(f"Product_templates with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Product_templates not found")

        logger.info(f"Product_templates {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating product_templates {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating product_templates {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_product_templatess_batch(
    request: Product_templatesBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("product_template.delete")),
):
    """Delete multiple product_templatess by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} product_templatess")
    
    service = Product_templatesService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} product_templatess successfully")
        return {"message": f"Successfully deleted {deleted_count} product_templatess", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_product_templates(
    id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("product_template.delete")),
):
    """Delete a single product_templates by ID"""
    logger.debug(f"Deleting product_templates with id: {id}")
    
    service = Product_templatesService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Product_templates with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Product_templates not found")
        
        logger.info(f"Product_templates {id} deleted successfully")
        return {"message": "Product_templates deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product_templates {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")