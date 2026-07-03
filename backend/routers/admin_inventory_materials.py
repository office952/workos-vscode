"""Admin router for the Inventory Materials registry (Sprint #20.5).

Mirrors the Sprint #20 `admin_workcenter_rates` router contract but
targets `inventory_materials` rows. All endpoints operate on the
canonical `code` field (not numeric `id`).

Endpoints (prefix `/api/admin/inventory-materials`):
  - GET    /                 -> list all rows (ordered by `code`).
  - GET    /{code}            -> fetch one row by canonical code.
  - PATCH  /{code}            -> update unit_cost / status / supplier / name.

All mutations validate the canonical invariant:
`status == "active"` requires `unit_cost` to be a positive number.
Violations return HTTP 400.

This router is intentionally minimal — it does NOT duplicate the
generic `/api/v1/entities/inventory_materials` CRUD (by id) used by
the rest of the app. It only exists to drive registry-completion
workflows (Sprint #20.5 price fill + future admin UI).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.inventory_materials_admin_service import (
    InventoryMaterialValidationError,
    get_inventory_material_price_history,
    get_inventory_material_by_code,
    get_inventory_material_source_review_audit,
    preview_category_cleanup,
    list_inventory_materials_admin,
    patch_inventory_material_by_code,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/inventory-materials",
    tags=["admin_inventory_materials"],
    dependencies=[Depends(get_current_user)],
)


INTELLIGENCE_POLICY: Dict[str, Any] = {
    "canonical_categories": [
        "Placi",
        "Profile metalice",
        "Parti electrice",
        "Folii",
        "Consumabile",
    ],
    "recommended_subcategories": {
        "Profile metalice": [
            "Otel / teava rectangulara",
            "Otel / teava rotunda",
            "Otel / cornier",
            "Otel / platbanda",
            "Aluminiu / profil litera volumetrica",
            "Aluminiu / profil caseta luminoasa",
            "Aluminiu / profil rama",
            "Aluminiu / profil sistem textil/banner",
        ],
        "Folii": [
            "Oracal 651",
            "Oracal 641",
            "Oracal 8500 translucent",
            "Printabil",
            "Laminare",
        ],
        "Placi": [
            "ACM / Alucobond / Dibond",
            "Plexiglas",
            "Forex",
            "HIPS / alte placi",
        ],
        "Parti electrice": [
            "LED modules",
            "surse alimentare",
            "cabluri / conectori",
        ],
        "Consumabile": [
            "adezivi",
            "suruburi / prinderi",
            "distantieri / kit montaj",
            "consumabile generale",
        ],
    },
    "required_pricing_fields": ["unit", "unit_cost", "currency", "vat_percent", "valid_from"],
    "price_governed_fields": ["unit_cost", "currency", "vat_percent", "valid_from"],
    "source_review_policy": {
        "statuses": ["missing", "needs_review", "reviewed", "stale", "accepted_override"],
        "accepted_override_requires_notes": True,
    },
    "product_system_gate_rules": {
        "requires_ready_for_pricing": True,
        "requires_active_status": True,
        "rejects_archived": True,
        "requires_category_normalized": True,
        "requires_unit": True,
        "requires_source_review_ok": True,
        "informational_only": True,
    },
    "stale_source_days": 90,
    "warnings": [
        "Material Registry unit_cost remains acquisition/production cost.",
        "Commercial markup policy is a separate layer.",
        "ProductSystem gate is informational and does not activate Product 001.",
    ],
    "category_policy": {
        "accepted": [
            "Placi",
            "Profile metalice",
            "Parti electrice",
            "Folii",
            "Consumabile",
        ],
        "recommended_subcategories": {
            "Profile metalice": [
                "Otel / teava rectangulara",
                "Otel / teava rotunda",
                "Otel / cornier",
                "Otel / platbanda",
                "Aluminiu / profil litera volumetrica",
                "Aluminiu / profil caseta luminoasa",
                "Aluminiu / profil rama",
                "Aluminiu / profil sistem textil/banner",
            ],
            "Folii": [
                "Oracal 651",
                "Oracal 641",
                "Oracal 8500 translucent",
                "Printabil",
                "Laminare",
            ],
            "Placi": [
                "ACM / Alucobond / Dibond",
                "Plexiglas",
                "Forex",
                "HIPS / alte placi",
            ],
            "Parti electrice": [
                "LED modules",
                "surse alimentare",
                "cabluri / conectori",
            ],
            "Consumabile": [
                "adezivi",
                "suruburi / prinderi",
                "distantieri / kit montaj",
                "servicii interne",
            ],
        },
    },
    "source_review": {
        "stale_after_days": 90,
        "override_token": "source_review:accepted",
    },
    "productsystem_gate": {
        "informational_only": True,
        "activates_product_001": False,
        "connects_cost_engine": False,
    },
}


class InventoryMaterialPatchBody(BaseModel):
    unit_cost: Optional[float] = None
    currency: Optional[str] = None
    vat_percent: Optional[float] = None
    valid_from: Optional[datetime] = None
    status: Optional[str] = None
    supplier: Optional[str] = None
    supplier_id: Optional[int] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_checked_at: Optional[datetime] = None
    source_notes: Optional[str] = None
    source_review_status: Optional[str] = None
    source_reviewed_at: Optional[datetime] = None
    source_reviewed_by: Optional[str] = None
    name: Optional[str] = None
    subcategory: Optional[str] = None
    change_reason: Optional[str] = None
    snapshot_source: Optional[str] = "admin_patch"
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


@router.get("")
async def list_materials(
    status: Optional[str] = Query(
        None, description="Optional status filter, e.g. 'missing_price' or 'active'."
    ),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.view")),
) -> List[Dict[str, Any]]:
    """Return every inventory material row sorted by code."""
    return await list_inventory_materials_admin(db, status_filter=status)


@router.get("/policy")
async def get_intelligence_policy(
    _user: UserResponse = Depends(require_permission("inventory.view")),
) -> Dict[str, Any]:
    """Return static intelligence policy hints for frontend governance UX."""
    return INTELLIGENCE_POLICY


@router.get("/{code}")
async def get_material(
    code: str,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.view")),
) -> Dict[str, Any]:
    row = await get_inventory_material_by_code(db, code)
    if row is None:
        raise HTTPException(
            status_code=404, detail=f"inventory_material '{code}' not found"
        )
    return row


@router.get("/{code}/price-history")
async def get_material_price_history_by_code(
    code: str,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.view")),
) -> List[Dict[str, Any]]:
    material = await get_inventory_material_by_code(db, code)
    if material is None:
        raise HTTPException(
            status_code=404, detail=f"inventory_material '{code}' not found"
        )
    return await get_inventory_material_price_history(db, code=code, limit=limit)


@router.get("/{code}/source-review-audit")
async def get_material_source_review_audit(
    code: str,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.view")),
) -> List[Dict[str, Any]]:
    material = await get_inventory_material_by_code(db, code)
    if material is None:
        raise HTTPException(
            status_code=404, detail=f"inventory_material '{code}' not found"
        )
    return await get_inventory_material_source_review_audit(db, code=code, limit=limit)


@router.get("/price-history/by-id/{material_id}")
async def get_material_price_history_by_id(
    material_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.view")),
) -> List[Dict[str, Any]]:
    return await get_inventory_material_price_history(
        db,
        material_id=material_id,
        limit=limit,
    )


@router.get("/category-cleanup/preview")
async def get_category_cleanup_preview(
    limit: int = Query(500, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.view")),
) -> List[Dict[str, Any]]:
    return await preview_category_cleanup(db, limit=limit)


@router.patch("/{code}")
async def patch_material(
    code: str,
    body: InventoryMaterialPatchBody,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("inventory.update")),
) -> Dict[str, Any]:
    model_fields_set = getattr(body, "model_fields_set", None)
    if model_fields_set is None:
        model_fields_set = getattr(body, "__fields_set__", set())
    provided_fields = set(model_fields_set)

    try:
        row = await patch_inventory_material_by_code(
            db,
            code,
            unit_cost=body.unit_cost,
            currency=body.currency,
            vat_percent=body.vat_percent,
            valid_from=body.valid_from,
            status=body.status,
            supplier=body.supplier,
            supplier_id=body.supplier_id,
            source_name=body.source_name,
            source_url=body.source_url,
            source_checked_at=body.source_checked_at,
            source_notes=body.source_notes,
            source_review_status=body.source_review_status,
            source_reviewed_at=body.source_reviewed_at,
            source_reviewed_by=body.source_reviewed_by,
            name=body.name,
            subcategory=body.subcategory,
            change_reason=body.change_reason,
            changed_by=str(_user.id),
            snapshot_source=body.snapshot_source,
            sheet_format_type=body.sheet_format_type,
            sheet_width=body.sheet_width,
            sheet_height=body.sheet_height,
            sheet_unit=body.sheet_unit,
            sheet_thickness=body.sheet_thickness,
            sheet_thickness_unit=body.sheet_thickness_unit,
            usable_width=body.usable_width,
            usable_height=body.usable_height,
            format_source=body.format_source,
            format_verified=body.format_verified,
            format_notes=body.format_notes,
            provided_fields=provided_fields,
        )
    except InventoryMaterialValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if row is None:
        raise HTTPException(
            status_code=404, detail=f"inventory_material '{code}' not found"
        )
    return row