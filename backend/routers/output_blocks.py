"""BUILD 27.06 — OutputBlock entity/API contract router.

This router provides backend-owned CRUD + approve endpoints for OutputBlock
definitions. It does not render output, does not mutate quote/order snapshots,
 and does not touch inventory/execution flows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.output_blocks_service import (
    OutputBlocksService,
    OutputBlockPolicyError,
    OutputBlockValidationError,
)
from services.output_block_renderer_service import (
    OutputBlockRendererService,
    OutputBlockPreviewValidationError,
)
from services.output_block_snapshot_service import (
    OutputBlockSnapshotService,
    RenderedOutputSnapshotBlockedError,
    RenderedOutputSnapshotValidationError,
)

router = APIRouter(
    prefix="/api/v1/product-system/output-blocks",
    tags=["product-system-output-blocks-entity"],
    dependencies=[Depends(get_current_user)],
)


class OutputBlockCreateRequest(BaseModel):
    block_id: str
    block_type: str
    title: str
    purpose: Optional[str] = None
    audience: str
    document_type: str
    source_fields: List[str]
    variables: List[Dict[str, Any]]
    template_text: str
    conditions: Union[Dict[str, Any], List[Any]] = Field(default_factory=dict)
    approval_status: str = "draft"
    version: str = "v1"
    owner_role: Optional[str] = None
    reviewer_role: Optional[str] = None
    snapshot_policy: Dict[str, Any] = Field(default_factory=dict)


class OutputBlockUpdateRequest(BaseModel):
    block_type: Optional[str] = None
    title: Optional[str] = None
    purpose: Optional[str] = None
    audience: Optional[str] = None
    document_type: Optional[str] = None
    source_fields: Optional[List[str]] = None
    variables: Optional[List[Dict[str, Any]]] = None
    template_text: Optional[str] = None
    conditions: Optional[Union[Dict[str, Any], List[Any]]] = None
    approval_status: Optional[str] = None
    version: Optional[str] = None
    owner_role: Optional[str] = None
    reviewer_role: Optional[str] = None
    snapshot_policy: Optional[Dict[str, Any]] = None


class OutputBlockApproveRequest(BaseModel):
    reviewer_role: Optional[str] = None


class OutputBlockPreviewRequest(BaseModel):
    block_ids: Optional[List[str]] = None
    block_types: Optional[List[str]] = None
    context: str
    source_payload: Dict[str, Any]


class RenderedOutputBlock(BaseModel):
    block_id: str
    block_type: str
    title: Optional[str] = None
    approval_status: str
    rendered_text: Optional[str] = None
    variables_used: Dict[str, Any] = Field(default_factory=dict)
    source_fields_used: List[str] = Field(default_factory=list)
    skipped: bool = False
    skip_reason: Optional[str] = None
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    blockers: List[Dict[str, Any]] = Field(default_factory=list)


class OutputBlockPreviewResponse(BaseModel):
    preview_only: bool = True
    context: str
    rendered_blocks: List[RenderedOutputBlock] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    blockers: List[Dict[str, Any]] = Field(default_factory=list)


class RenderedOutputBlockSnapshot(BaseModel):
    block_id: str
    block_type: str
    title: Optional[str] = None
    approval_status: str
    block_version: str
    template_text_hash: str
    rendered_text: Optional[str] = None
    variables_used: Dict[str, Any] = Field(default_factory=dict)
    source_fields_used: List[str] = Field(default_factory=list)
    skipped: bool = False
    skip_reason: Optional[str] = None
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    blockers: List[Dict[str, Any]] = Field(default_factory=list)


class OutputBlockSnapshotRequest(BaseModel):
    block_ids: Optional[List[str]] = None
    block_types: Optional[List[str]] = None
    context: str
    source_payload: Dict[str, Any]
    document_type: str
    audience: str
    snapshot_purpose: str
    target_type: Optional[str] = None
    target_id: Optional[Union[int, str]] = None


class OutputBlockSnapshotResponse(BaseModel):
    snapshot_id: int
    snapshot_uid: str
    preview_only: bool = False
    snapshot_status: str
    context: str
    document_type: str
    audience: str
    snapshot_purpose: str
    target_type: Optional[str] = None
    target_id: Optional[Union[int, str]] = None
    rendered_blocks: List[RenderedOutputBlockSnapshot] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    blockers: List[Dict[str, Any]] = Field(default_factory=list)
    source_payload_hash: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None


@router.get("")
async def list_output_blocks(
    block_type: Optional[str] = Query(None),
    audience: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    approval_status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    service = OutputBlocksService(db)
    try:
        return await service.list_blocks(
            block_type=block_type,
            audience=audience,
            document_type=document_type,
            approval_status=approval_status,
            skip=skip,
            limit=limit,
        )
    except OutputBlockValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "output_block_validation_error", "violations": exc.violations},
        )


@router.post("", status_code=201)
async def create_output_block(
    request: OutputBlockCreateRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("product_template.create")),
):
    service = OutputBlocksService(db)
    try:
        return await service.create_block(request.model_dump())
    except OutputBlockValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "output_block_validation_error", "violations": exc.violations},
        )
    except OutputBlockPolicyError as exc:
        raise HTTPException(status_code=409, detail={"error": exc.code, "message": exc.message})


@router.post("/preview", response_model=OutputBlockPreviewResponse)
async def preview_output_blocks(
    request: OutputBlockPreviewRequest,
    db: AsyncSession = Depends(get_db),
):
    service = OutputBlockRendererService(db)
    try:
        return await service.render_output_blocks_preview(
            block_ids=request.block_ids,
            block_types=request.block_types,
            context=request.context,
            source_payload=request.source_payload,
        )
    except OutputBlockPreviewValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "output_block_preview_validation_error",
                "violations": exc.violations,
            },
        )


@router.post("/snapshots", response_model=OutputBlockSnapshotResponse, status_code=201)
async def create_output_block_snapshot(
    request: OutputBlockSnapshotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("output_blocks.snapshot_create")),
):
    service = OutputBlockSnapshotService(db)
    try:
        return await service.create_rendered_output_snapshot(
            context=request.context,
            block_ids=request.block_ids,
            block_types=request.block_types,
            source_payload=request.source_payload,
            document_type=request.document_type,
            audience=request.audience,
            snapshot_purpose=request.snapshot_purpose,
            target_type=request.target_type,
            target_id=request.target_id,
            created_by=current_user.email or current_user.id,
        )
    except RenderedOutputSnapshotValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "rendered_output_snapshot_validation_error",
                "violations": exc.violations,
            },
        )
    except RenderedOutputSnapshotBlockedError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "rendered_output_snapshot_blocked",
                "snapshot": exc.payload,
            },
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"error": str(exc)})


@router.get("/{block_id}")
async def get_output_block(
    block_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = OutputBlocksService(db)
    output_block = await service.get_block(block_id)
    if not output_block:
        raise HTTPException(status_code=404, detail="Output block not found")
    return output_block


@router.patch("/{block_id}")
async def update_output_block(
    block_id: str,
    request: OutputBlockUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("product_template.update")),
):
    service = OutputBlocksService(db)
    payload = {k: v for k, v in request.model_dump().items() if v is not None}
    if not payload:
        raise HTTPException(status_code=422, detail={"error": "empty_update_payload"})

    try:
        output_block = await service.update_block(block_id, payload)
    except OutputBlockValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "output_block_validation_error", "violations": exc.violations},
        )
    except OutputBlockPolicyError as exc:
        raise HTTPException(status_code=409, detail={"error": exc.code, "message": exc.message})

    if not output_block:
        raise HTTPException(status_code=404, detail="Output block not found")
    return output_block


@router.post("/{block_id}/approve")
async def approve_output_block(
    block_id: str,
    request: OutputBlockApproveRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("product_template.update")),
):
    service = OutputBlocksService(db)
    try:
        output_block = await service.approve_block(block_id, reviewer_role=request.reviewer_role)
    except OutputBlockPolicyError as exc:
        raise HTTPException(status_code=409, detail={"error": exc.code, "message": exc.message})

    if not output_block:
        raise HTTPException(status_code=404, detail="Output block not found")
    return output_block