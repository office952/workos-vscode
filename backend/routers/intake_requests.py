import json
import logging
from typing import Any, Dict, List, Optional

from datetime import datetime, date

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.intake_requests import Intake_requestsService
from services.work_intake_svg_upload_service import WorkIntakeSvgUploadService
from services.work_intake_artwork_print_upload_service import WorkIntakeArtworkPrintUploadService
from services.work_intake_work_file_service import WorkIntakeWorkFileService
from services.product_families_service import validate_family_id
from validators.intake_product_spec import validate_intake_product_spec
from validators.intake_site_audit import site_audit_to_storage, validate_intake_site_audit
from validators.status_lifecycle import validate_status, validate_transition

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/intake_requests",
    tags=["intake_requests"],
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


def _product_spec_to_storage(spec: Any) -> Optional[str]:
    """Normalize and JSON-encode product_spec_json for DB storage."""
    normalized = validate_intake_product_spec(spec)
    if normalized is None:
        return None
    return json.dumps(normalized, ensure_ascii=False)


def _site_audit_to_storage(spec: Any) -> Optional[str]:
    normalized = validate_intake_site_audit(spec)
    if normalized is None:
        return None
    return site_audit_to_storage(normalized)


def _prepare_intake_write_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize product_spec_json and pass through other intake fields."""
    out = dict(data)
    if "product_spec_json" in out:
        out["product_spec_json"] = _product_spec_to_storage(out["product_spec_json"])
    if "site_audit_json" in out:
        out["site_audit_json"] = _site_audit_to_storage(out["site_audit_json"])
    return out


# ---------- Pydantic Schemas ----------
class Intake_requestsData(BaseModel):
    """Entity data schema (for create/update)"""
    code: str
    client_id: int = None
    client_name: str
    contact_person: str = None
    channel: str = None
    product_family: str
    description: str = None
    dimensions: str = None
    quantity: int = None
    status: str
    assigned_to: str = None
    notes: str = None
    priority: str = None
    delivery_type: str = None
    product_spec_json: Optional[Dict[str, Any]] = None
    confirmed_template_code: Optional[str] = None
    confirmed_template_name: Optional[str] = None
    site_audit_json: Optional[Dict[str, Any]] = None


class Intake_requestsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    code: Optional[str] = None
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    contact_person: Optional[str] = None
    channel: Optional[str] = None
    product_family: Optional[str] = None
    description: Optional[str] = None
    dimensions: Optional[str] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[str] = None
    delivery_type: Optional[str] = None
    product_spec_json: Optional[Dict[str, Any]] = None
    confirmed_template_code: Optional[str] = None
    confirmed_template_name: Optional[str] = None
    site_audit_json: Optional[Dict[str, Any]] = None


class Intake_requestsResponse(BaseModel):
    """Entity response schema"""
    id: int
    code: str
    client_id: Optional[int] = None
    client_name: str
    contact_person: Optional[str] = None
    channel: Optional[str] = None
    product_family: str
    description: Optional[str] = None
    dimensions: Optional[str] = None
    quantity: Optional[int] = None
    status: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[str] = None
    delivery_type: Optional[str] = None
    product_spec_json: Optional[Dict[str, Any]] = None
    confirmed_template_code: Optional[str] = None
    confirmed_template_name: Optional[str] = None
    site_audit_json: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("site_audit_json", mode="before")
    @classmethod
    def _parse_site_audit_json(cls, value: Any) -> Optional[Dict[str, Any]]:
        if value is None or value == "":
            return None
        if isinstance(value, dict):
            return validate_intake_site_audit(value)
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return None
            return validate_intake_site_audit(parsed) if isinstance(parsed, dict) else None
        return None

    @field_validator("product_spec_json", mode="before")
    @classmethod
    def _parse_product_spec_json(cls, value: Any) -> Optional[Dict[str, Any]]:
        if value is None or value == "":
            return None
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return None
            return parsed if isinstance(parsed, dict) else None
        return None

    class Config:
        from_attributes = True


class Intake_requestsListResponse(BaseModel):
    """List response schema"""
    items: List[Intake_requestsResponse]
    total: int
    skip: int
    limit: int


class Intake_requestsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[Intake_requestsData]


class Intake_requestsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: Intake_requestsUpdateData


class Intake_requestsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[Intake_requestsBatchUpdateItem]


class Intake_requestsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=Intake_requestsListResponse)
async def query_intake_requestss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query intake_requestss with filtering, sorting, and pagination"""
    logger.debug(f"Querying intake_requestss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = Intake_requestsService(db)
    try:
        query_dict = _parse_query_or_400(query)
        
        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
        )
        logger.debug(f"Found {result['total']} intake_requestss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying intake_requestss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=Intake_requestsListResponse)
async def query_intake_requestss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query intake_requestss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying intake_requestss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = Intake_requestsService(db)
    try:
        query_dict = _parse_query_or_400(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} intake_requestss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying intake_requestss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/by-code/{intake_code}/svg-upload-and-analyze")
async def svg_upload_and_analyze_by_code(
    intake_code: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("intake.update")),
) -> dict:
    """Upload an SVG for an intake request (by public code), analyze, and persist vector_* fields."""
    service = WorkIntakeSvgUploadService(db)
    result = await service.upload_and_analyze(intake_code=intake_code, upload=file)
    if not result.get("ok"):
        code = result.get("code", "invalid_svg")
        status_code = 404 if code == "intake_not_found" else 400
        raise HTTPException(status_code=status_code, detail=result)
    return result


@router.post("/by-code/{intake_code}/artwork-print-upload")
async def artwork_print_upload_by_code(
    intake_code: str,
    layer_id: str = Query(..., description="Artwork layer id from svgArtworkLayersPending"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("intake.update")),
) -> dict:
    """Upload a print/production file for a policromie artwork layer assignment."""
    service = WorkIntakeArtworkPrintUploadService(db)
    result = await service.upload(intake_code=intake_code, layer_id=layer_id, upload=file)
    if not result.get("ok"):
        code = result.get("code", "invalid_file")
        status_code = 404 if code == "intake_not_found" else 400
        raise HTTPException(status_code=status_code, detail=result)
    return result


@router.post("/by-code/{intake_code}/work-file-upload")
async def work_file_upload_by_code(
    intake_code: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: UserResponse = Depends(require_permission("intake.update")),
) -> dict:
    """Upload a production master work file for an intake request."""
    service = WorkIntakeWorkFileService(db)
    uploaded_by = user.name or user.email
    result = await service.upload(
        intake_code=intake_code,
        upload=file,
        uploaded_by=uploaded_by,
    )
    if not result.get("ok"):
        code = result.get("code", "invalid_file")
        status_code = 404 if code == "intake_not_found" else 400
        raise HTTPException(status_code=status_code, detail=result)
    return result


@router.get("/by-code/{intake_code}/work-files/{file_id}/download")
async def work_file_download_by_code(
    intake_code: str,
    file_id: str,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("intake.update")),
):
    """Download a production work file attached to an intake request."""
    service = WorkIntakeWorkFileService(db)
    result = await service.download(intake_code=intake_code, file_id=file_id)
    if isinstance(result, dict) and not result.get("ok", True):
        code = result.get("code", "invalid_request")
        status_code = 404 if code == "intake_not_found" else 400
        raise HTTPException(status_code=status_code, detail=result)
    return result


@router.get("/{id}", response_model=Intake_requestsResponse)
async def get_intake_requests(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single intake_requests by ID"""
    logger.debug(f"Fetching intake_requests with id: {id}, fields={fields}")
    
    service = Intake_requestsService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Intake_requests with id {id} not found")
            raise HTTPException(status_code=404, detail="Intake_requests not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching intake_requests {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=Intake_requestsResponse, status_code=201)
async def create_intake_requests(
    data: Intake_requestsData,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("intake.create")),
):
    """Create a new intake_requests"""
    logger.debug(f"Creating new intake_requests with data: {data}")
    
    # Validate family_id against registry if provided
    if data.product_family:
        is_valid = await validate_family_id(db, data.product_family)
        if not is_valid:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid product_family/family_id '{data.product_family}': not found in Product Families Registry or inactive",
            )
    service = Intake_requestsService(db)
    try:
        payload = _prepare_intake_write_payload(data.model_dump())
        if payload.get("status") is not None:
            validate_status("intake_requests", payload["status"])
        result = await service.create(payload)
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create intake_requests")
        
        logger.info(f"Intake_requests created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating intake_requests: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating intake_requests: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[Intake_requestsResponse], status_code=201)
async def create_intake_requestss_batch(
    request: Intake_requestsBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("intake.create")),
):
    """Create multiple intake_requestss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} intake_requestss")
    
    service = Intake_requestsService(db)
    results = []
    
    try:
        for item_data in request.items:
            payload = _prepare_intake_write_payload(item_data.model_dump())
            result = await service.create(payload)
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} intake_requestss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[Intake_requestsResponse])
async def update_intake_requestss_batch(
    request: Intake_requestsBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("intake.update")),
):
    """Update multiple intake_requestss in a single request"""
    logger.debug(f"Batch updating {len(request.items)} intake_requestss")
    
    service = Intake_requestsService(db)
    results = []
    
    try:
        for item in request.items:
            raw = item.updates.model_dump(exclude_unset=True)
            try:
                update_dict = _prepare_intake_write_payload(raw)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            update_dict = {
                k: v for k, v in update_dict.items()
                if v is not None or k == "product_spec_json"
            }
            result = await service.update(item.id, update_dict)
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} intake_requestss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=Intake_requestsResponse)
async def update_intake_requests(
    id: int,
    data: Intake_requestsUpdateData,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("intake.update")),
):
    """Update an existing intake_requests"""
    logger.debug(f"Updating intake_requests {id} with data: {data}")

    # Validate family_id against Product Families Registry if provided in update
    if data.product_family is not None:
        is_valid = await validate_family_id(db, data.product_family)
        if not is_valid:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid product_family/family_id '{data.product_family}': not found in Product Families Registry or inactive",
            )

    service = Intake_requestsService(db)
    try:
        existing = await service.get_by_id(id)
        if not existing:
            logger.warning(f"Intake_requests with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Intake_requests not found")

        raw = data.model_dump(exclude_unset=True)
        if "status" in raw and raw["status"] is not None:
            validate_transition("intake_requests", existing.status, raw["status"])

        update_dict = _prepare_intake_write_payload(raw)
        update_dict = {
            k: v for k, v in update_dict.items()
            if v is not None or k in ("product_spec_json", "site_audit_json")
        }
        result = await service.update(id, update_dict)
        if not result:
            logger.warning(f"Intake_requests with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Intake_requests not found")
        
        logger.info(f"Intake_requests {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating intake_requests {id}: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating intake_requests {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_intake_requestss_batch(
    request: Intake_requestsBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("intake.delete")),
):
    """Delete multiple intake_requestss by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} intake_requestss")
    
    service = Intake_requestsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} intake_requestss successfully")
        return {"message": f"Successfully deleted {deleted_count} intake_requestss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_intake_requests(
    id: int,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("intake.delete")),
):
    """Delete a single intake_requests by ID"""
    logger.debug(f"Deleting intake_requests with id: {id}")
    
    service = Intake_requestsService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Intake_requests with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Intake_requests not found")
        
        logger.info(f"Intake_requests {id} deleted successfully")
        return {"message": "Intake_requests deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting intake_requests {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")