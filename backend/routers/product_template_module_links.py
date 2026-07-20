import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from services.product_template_module_links_service import ProductTemplateModuleLinksService


router = APIRouter(
    prefix="/api/v1/entities/product-template-module-links",
    tags=["product_template_module_links"],
    dependencies=[Depends(get_current_user)],
)


class ProductTemplateModuleLinkData(BaseModel):
    parent_template_id: int
    parent_template_code: str
    module_template_id: int
    module_template_code: str
    relation_type: str = "optional_addon"
    trigger_field: str
    trigger_value_json: str
    input_mapping_json: str
    default_values_json: Optional[str] = None
    pricing_mode: str = "separate_quote_line"
    execution_mode: str = "linked_child_work"
    active: bool = True
    notes: Optional[str] = None
    # Component-contract edge fields (no ComponentTemplate table).
    usage_mode: Optional[str] = None
    instance_schema_id: Optional[str] = None


class ProductTemplateModuleLinkUpdateData(BaseModel):
    relation_type: Optional[str] = None
    trigger_field: Optional[str] = None
    trigger_value_json: Optional[str] = None
    input_mapping_json: Optional[str] = None
    default_values_json: Optional[str] = None
    pricing_mode: Optional[str] = None
    execution_mode: Optional[str] = None
    active: Optional[bool] = None
    notes: Optional[str] = None
    usage_mode: Optional[str] = None
    instance_schema_id: Optional[str] = None


class ProductTemplateModuleLinkResponse(BaseModel):
    id: int
    parent_template_id: int
    parent_template_code: str
    module_template_id: int
    module_template_code: str
    relation_type: str
    trigger_field: str
    trigger_value_json: str
    input_mapping_json: str
    default_values_json: Optional[str] = None
    pricing_mode: str
    execution_mode: str
    active: bool
    notes: Optional[str] = None
    usage_mode: Optional[str] = None
    instance_schema_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductTemplateModuleLinkListResponse(BaseModel):
    items: List[ProductTemplateModuleLinkResponse]
    total: int
    skip: int
    limit: int


def _validate_json_string(value: Optional[str], field: str, required: bool = True) -> None:
    if value is None:
        if required:
            raise HTTPException(status_code=422, detail=f"{field} is required")
        return
    try:
        json.loads(value)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail=f"{field} must be valid JSON")


@router.get("", response_model=ProductTemplateModuleLinkListResponse)
async def list_product_template_module_links(
    query: Optional[str] = Query(None, description="Query conditions (JSON string)"),
    sort: Optional[str] = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
):
    query_dict = None
    if query:
        try:
            query_dict = json.loads(query)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid query JSON format")
    service = ProductTemplateModuleLinksService(db)
    return await service.get_list(skip=skip, limit=limit, query_dict=query_dict, sort=sort)


@router.get("/{id}", response_model=ProductTemplateModuleLinkResponse)
async def get_product_template_module_link(id: int, db: AsyncSession = Depends(get_db)):
    service = ProductTemplateModuleLinksService(db)
    result = await service.get_by_id(id)
    if result is None:
        raise HTTPException(status_code=404, detail="Product template module link not found")
    return result


@router.post("", response_model=ProductTemplateModuleLinkResponse, status_code=201)
async def create_product_template_module_link(
    data: ProductTemplateModuleLinkData,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("product_template.update")),
):
    payload = data.model_dump()
    _validate_json_string(payload.get("trigger_value_json"), "trigger_value_json")
    _validate_json_string(payload.get("input_mapping_json"), "input_mapping_json")
    _validate_json_string(payload.get("default_values_json"), "default_values_json", required=False)
    service = ProductTemplateModuleLinksService(db)
    return await service.create(payload)


@router.put("/{id}", response_model=ProductTemplateModuleLinkResponse)
async def update_product_template_module_link(
    id: int,
    data: ProductTemplateModuleLinkUpdateData,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("product_template.update")),
):
    payload = data.model_dump(exclude_unset=True)
    if "trigger_value_json" in payload:
        _validate_json_string(payload.get("trigger_value_json"), "trigger_value_json")
    if "input_mapping_json" in payload:
        _validate_json_string(payload.get("input_mapping_json"), "input_mapping_json")
    if "default_values_json" in payload:
        _validate_json_string(payload.get("default_values_json"), "default_values_json", required=False)
    service = ProductTemplateModuleLinksService(db)
    result = await service.update(id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="Product template module link not found")
    return result