"""Router for Product Families Registry."""

import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.product_families_service import (
    Product_familiesService,
    find_template_by_family,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/product-families",
    tags=["product_families"],
    dependencies=[Depends(get_current_user)],
)


class ProductFamilyData(BaseModel):
    family_id: str
    label: str
    category: Optional[str] = None
    active: bool = True
    default_template_id: Optional[int] = None
    description: Optional[str] = None


class ProductFamilyUpdateData(BaseModel):
    family_id: Optional[str] = None
    label: Optional[str] = None
    category: Optional[str] = None
    active: Optional[bool] = None
    default_template_id: Optional[int] = None
    description: Optional[str] = None


class ProductFamilyResponse(BaseModel):
    id: int
    family_id: str
    label: str
    category: Optional[str] = None
    active: bool
    default_template_id: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductFamilyListResponse(BaseModel):
    items: List[ProductFamilyResponse]
    total: int
    skip: int
    limit: int


@router.get("", response_model=ProductFamilyListResponse)
async def list_product_families(
    query: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    service = Product_familiesService(db)
    query_dict = None
    if query:
        try:
            query_dict = json.loads(query)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid query JSON")
    return await service.get_list(
        skip=skip, limit=limit, query_dict=query_dict, sort=sort
    )


@router.get("/by-family-id/{family_id}", response_model=ProductFamilyResponse)
async def get_by_family_id(family_id: str, db: AsyncSession = Depends(get_db)):
    service = Product_familiesService(db)
    obj = await service.get_by_family_id(family_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Product family not found")
    return obj


@router.get("/{family_id}/resolve-template")
async def resolve_template(family_id: str, db: AsyncSession = Depends(get_db)):
    """Resolve a family_id to its canonical product_template.

    Returns {status, template, candidates, message}.
    """
    result = await find_template_by_family(db, family_id)
    tpl = result.get("template")
    candidates = result.get("candidates") or []
    return {
        "status": result["status"],
        "message": result["message"],
        "template": {
            "id": tpl.id,
            "template_code": tpl.template_code,
            "family_id": tpl.family_id,
            "family_name": tpl.family_name,
        }
        if tpl
        else None,
        "candidates": [
            {
                "id": c.id,
                "template_code": c.template_code,
                "family_id": c.family_id,
                "family_name": c.family_name,
            }
            for c in candidates
        ],
    }


@router.get("/{id}", response_model=ProductFamilyResponse)
async def get_product_family(id: int, db: AsyncSession = Depends(get_db)):
    service = Product_familiesService(db)
    obj = await service.get_by_id(id)
    if not obj:
        raise HTTPException(status_code=404, detail="Product family not found")
    return obj


@router.post("", response_model=ProductFamilyResponse, status_code=201)
async def create_product_family(
    data: ProductFamilyData, db: AsyncSession = Depends(get_db), _user: UserResponse = Depends(require_permission("product_family.create"))
):
    service = Product_familiesService(db)
    # Uniqueness check
    if await service.get_by_family_id(data.family_id):
        raise HTTPException(
            status_code=400,
            detail=f"Product family '{data.family_id}' already exists",
        )
    return await service.create(data.model_dump())


@router.put("/{id}", response_model=ProductFamilyResponse)
async def update_product_family(
    id: int,
    data: ProductFamilyUpdateData,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("product_family.update")),
):
    service = Product_familiesService(db)
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    obj = await service.update(id, update_dict)
    if not obj:
        raise HTTPException(status_code=404, detail="Product family not found")
    return obj


@router.delete("/{id}")
async def delete_product_family(id: int, db: AsyncSession = Depends(get_db), _user: UserResponse = Depends(require_permission("product_family.delete"))):
    service = Product_familiesService(db)
    ok = await service.delete(id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product family not found")
    return {"message": "Product family deleted", "id": id}