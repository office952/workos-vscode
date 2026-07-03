"""Router for Product Blueprint Dossier CRUD.

Phase A — Product Blueprint Dossier Foundation.
Phase B — Hardening (delete policy, status transitions, version increment,
          semantic validation, owner enforcement).

Provides CRUD endpoints for the product_blueprint_dossier table.
Follows the same patterns as product_templates and product_families routers.

This router does NOT calculate cost, create offers, create orders,
create tasks, modify stock, or rewrite snapshots.
"""

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
from services.product_blueprint_dossier_service import (
    ALLOWED_DOSSIER_STATUSES,
    ProductBlueprintDossierService,
    validate_completion_state_json,
    validate_json_fields,
    validate_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/product-blueprint-dossiers",
    tags=["product_blueprint_dossier"],
    dependencies=[Depends(get_current_user)],
)


# ---------- Pydantic Schemas ----------
class DossierCreateData(BaseModel):
    """Create schema for product blueprint dossier."""

    template_id: int
    template_code: str
    dossier_version: int = 1
    status: str = "draft"
    sections_json: Optional[str] = None
    variants_json: Optional[str] = None
    layers_json: Optional[str] = None
    task_rules_json: Optional[str] = None
    time_assumptions_json: Optional[str] = None
    costengine_mapping_json: Optional[str] = None
    quote_readiness_json: Optional[str] = None
    output_blocks_json: Optional[str] = None
    visual_prompt_blocks_json: Optional[str] = None
    production_notes_json: Optional[str] = None
    qc_checkpoints_json: Optional[str] = None
    risks_json: Optional[str] = None
    completion_state_json: Optional[str] = None
    owner_role: Optional[str] = None
    reviewer_role: Optional[str] = None


class DossierUpdateData(BaseModel):
    """Update schema (partial updates allowed)."""

    template_code: Optional[str] = None
    dossier_version: Optional[int] = None
    status: Optional[str] = None
    sections_json: Optional[str] = None
    variants_json: Optional[str] = None
    layers_json: Optional[str] = None
    task_rules_json: Optional[str] = None
    time_assumptions_json: Optional[str] = None
    costengine_mapping_json: Optional[str] = None
    quote_readiness_json: Optional[str] = None
    output_blocks_json: Optional[str] = None
    visual_prompt_blocks_json: Optional[str] = None
    production_notes_json: Optional[str] = None
    qc_checkpoints_json: Optional[str] = None
    risks_json: Optional[str] = None
    completion_state_json: Optional[str] = None
    owner_role: Optional[str] = None
    reviewer_role: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class DossierResponse(BaseModel):
    """Response schema."""

    id: int
    template_id: int
    template_code: str
    dossier_version: int
    status: str
    sections_json: Optional[str] = None
    variants_json: Optional[str] = None
    layers_json: Optional[str] = None
    task_rules_json: Optional[str] = None
    time_assumptions_json: Optional[str] = None
    costengine_mapping_json: Optional[str] = None
    quote_readiness_json: Optional[str] = None
    output_blocks_json: Optional[str] = None
    visual_prompt_blocks_json: Optional[str] = None
    production_notes_json: Optional[str] = None
    qc_checkpoints_json: Optional[str] = None
    risks_json: Optional[str] = None
    completion_state_json: Optional[str] = None
    owner_role: Optional[str] = None
    reviewer_role: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DossierListResponse(BaseModel):
    """List response schema."""

    items: List[DossierResponse]
    total: int
    skip: int
    limit: int


# ---------- Validation helpers ----------
def _validate_create_payload(data: dict) -> None:
    """Run all validations on create payload. Raises HTTPException on failure."""
    # template_id is required
    if not data.get("template_id"):
        raise HTTPException(status_code=422, detail="template_id is required")

    # template_code is required
    if not data.get("template_code"):
        raise HTTPException(status_code=422, detail="template_code is required")

    # status must be in allowed set
    status_err = validate_status(data.get("status"))
    if status_err:
        raise HTTPException(status_code=422, detail=status_err)

    # JSON fields must be valid JSON
    json_errors = validate_json_fields(data)
    if json_errors:
        raise HTTPException(status_code=422, detail=json_errors)

    # completion_state_json section states must be valid
    cs_err = validate_completion_state_json(data)
    if cs_err:
        raise HTTPException(status_code=422, detail=cs_err)


def _validate_update_payload(data: dict) -> None:
    """Run all validations on update payload. Raises HTTPException on failure."""
    # status must be in allowed set (if provided)
    if "status" in data and data["status"] is not None:
        status_err = validate_status(data["status"])
        if status_err:
            raise HTTPException(status_code=422, detail=status_err)

    # JSON fields must be valid JSON
    json_errors = validate_json_fields(data)
    if json_errors:
        raise HTTPException(status_code=422, detail=json_errors)

    # completion_state_json section states must be valid
    cs_err = validate_completion_state_json(data)
    if cs_err:
        raise HTTPException(status_code=422, detail=cs_err)


# ---------- Routes ----------
@router.get("", response_model=DossierListResponse)
async def list_dossiers(
    query: Optional[str] = Query(None, description="Query conditions (JSON string)"),
    sort: Optional[str] = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    db: AsyncSession = Depends(get_db),
):
    """List product blueprint dossiers with filtering, sorting, and pagination."""
    service = ProductBlueprintDossierService(db)
    query_dict = None
    if query:
        try:
            query_dict = json.loads(query)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid query JSON format")
    return await service.get_list(skip=skip, limit=limit, query_dict=query_dict, sort=sort)


@router.get("/by-template/{template_id}", response_model=DossierResponse)
async def get_dossier_by_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get dossier by template_id (unique — at most one dossier per template)."""
    service = ProductBlueprintDossierService(db)
    result = await service.get_by_template_id(template_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No dossier found for template_id {template_id}",
        )
    return result


@router.get("/{id}", response_model=DossierResponse)
async def get_dossier(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single dossier by ID."""
    service = ProductBlueprintDossierService(db)
    result = await service.get_by_id(id)
    if not result:
        raise HTTPException(status_code=404, detail="Dossier not found")
    return result


@router.post("", response_model=DossierResponse, status_code=201)
async def create_dossier(
    data: DossierCreateData,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("dossier.create")),
):
    """Create a new product blueprint dossier.

    Validates:
      - template_id is required and must reference an existing product_template
      - template_code is required
      - status must be in allowed set
      - JSON fields must contain valid JSON
      - completion_state_json section states must be valid
      - Semantic JSON validation progressive per status
      - Uniqueness: one dossier per template_id
    """
    payload = data.model_dump()
    _validate_create_payload(payload)

    service = ProductBlueprintDossierService(db)

    # Check uniqueness: one dossier per template_id
    existing = await service.get_by_template_id(data.template_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A dossier already exists for template_id {data.template_id} (dossier id: {existing.id})",
        )

    try:
        user_role = getattr(current_user, "role", None)
        result = await service.create(payload, user_role=user_role)
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create dossier")
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating dossier: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{id}", response_model=DossierResponse)
async def update_dossier(
    id: int,
    data: DossierUpdateData,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("dossier.update")),
):
    """Update an existing dossier (partial updates allowed).

    Enforces:
      - Status transition rules (hardening decision §10)
      - Version auto-increment on approval transition (§9)
      - Version decrement blocked (§9)
      - Semantic JSON validation progressive per status (§13)
      - Owner enforcement on writes (§14)
    """
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    _validate_update_payload(update_dict)

    service = ProductBlueprintDossierService(db)
    try:
        user_role = getattr(current_user, "role", None)
        result = await service.update(id, update_dict, user_role=user_role)
        if not result:
            raise HTTPException(status_code=404, detail="Dossier not found")
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        error_msg = str(e)
        # Use 409 for status transition errors only, 422 for all other validation errors
        if error_msg.startswith("Status transition from"):
            raise HTTPException(status_code=409, detail=error_msg)
        raise HTTPException(status_code=422, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dossier {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{id}")
async def delete_dossier(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("dossier.delete")),
):
    """Delete a single dossier by ID.

    Enforces delete policy (hardening decision §7):
      - Hard delete allowed ONLY for status 'draft' or 'deprecated'
      - Returns 409 for 'needs_review', 'approved', 'blocked'
      - Owner enforcement on delete (§14)
    """
    service = ProductBlueprintDossierService(db)
    try:
        user_role = getattr(current_user, "role", None)
        success = await service.delete(id, user_role=user_role)
        if not success:
            raise HTTPException(status_code=404, detail="Dossier not found")
        return {"message": "Dossier deleted successfully", "id": id}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dossier {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")