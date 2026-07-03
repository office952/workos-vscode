"""
BUILD 10 — Quote Output Snapshot Candidate Router.

Endpoints for creating, listing, managing lifecycle, and exporting
quote output snapshot candidates.

Rules:
  - No Quote mutation
  - No Order mutation
  - No Order snapshot creation
  - No CostEngine formula change
  - No email/send
  - No final contract generation
  - Snapshot is internal audit document only
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.quote_output_snapshot_service import QuoteOutputSnapshotService
from services.quote_output_snapshot_governance_service import QuoteOutputSnapshotGovernanceService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/quotes",
    tags=["quote-output-snapshots"],
    dependencies=[Depends(get_current_user)],
)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CreateSnapshotRequest(BaseModel):
    source: str = "quote_output_composition_preview"
    notes: Optional[str] = None
    initial_status: str = "draft"


class ActionRequest(BaseModel):
    reason: Optional[str] = None


class SupersedeRequest(BaseModel):
    new_snapshot_id: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/{quote_id}/output-snapshots")
async def create_output_snapshot(
    quote_id: int,
    request: CreateSnapshotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("quote_output_snapshot.manage")),
):
    """Create a new quote output snapshot candidate from composition preview.

    Does NOT mutate Quote, Order, or any existing entity.
    """
    service = QuoteOutputSnapshotService(db)
    result = await service.create_snapshot(
        quote_id,
        notes=request.notes,
        initial_status=request.initial_status,
        created_by=current_user.email or current_user.id,
    )

    if "error" in result:
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])

    return result


@router.get("/{quote_id}/output-snapshots")
async def list_output_snapshots(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List all output snapshot candidates for a quote."""
    service = QuoteOutputSnapshotService(db)
    return await service.list_snapshots(quote_id)


@router.get("/{quote_id}/output-snapshots/{snapshot_id}")
async def get_output_snapshot(
    quote_id: int,
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single output snapshot candidate."""
    service = QuoteOutputSnapshotService(db)
    result = await service.get_snapshot(quote_id, snapshot_id)
    if not result:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return result


@router.post("/{quote_id}/output-snapshots/{snapshot_id}/submit-review")
async def submit_snapshot_for_review(
    quote_id: int,
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("quote_output_snapshot.manage")),
):
    """Submit snapshot for review: draft -> needs_review."""
    service = QuoteOutputSnapshotService(db)
    result = await service.submit_for_review(
        quote_id, snapshot_id, user=current_user.email or current_user.id
    )
    if "error" in result:
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.post("/{quote_id}/output-snapshots/{snapshot_id}/approve")
async def approve_snapshot(
    quote_id: int,
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("quote_output_snapshot.manage")),
):
    """Approve snapshot for quote output: draft/needs_review -> approved_for_quote_output.

    Approval does NOT send to client, create Order, or change Quote status.
    """
    service = QuoteOutputSnapshotService(db)
    result = await service.approve(
        quote_id, snapshot_id, user=current_user.email or current_user.id
    )
    if "error" in result:
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.post("/{quote_id}/output-snapshots/{snapshot_id}/archive")
async def archive_snapshot(
    quote_id: int,
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("quote_output_snapshot.manage")),
):
    """Archive snapshot: draft/needs_review/approved -> archived."""
    service = QuoteOutputSnapshotService(db)
    result = await service.archive(
        quote_id, snapshot_id, user=current_user.email or current_user.id
    )
    if "error" in result:
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.post("/{quote_id}/output-snapshots/{snapshot_id}/reject")
async def reject_snapshot(
    quote_id: int,
    snapshot_id: int,
    request: ActionRequest = ActionRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("quote_output_snapshot.manage")),
):
    """Reject snapshot: draft/needs_review -> rejected."""
    service = QuoteOutputSnapshotService(db)
    result = await service.reject(
        quote_id, snapshot_id,
        user=current_user.email or current_user.id,
        reason=request.reason,
    )
    if "error" in result:
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


@router.get("/{quote_id}/output-snapshots/{snapshot_id}/export", response_class=HTMLResponse)
async def export_snapshot_html(
    quote_id: int,
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export saved snapshot as HTML.

    Exports from SAVED content, not live preview.
    Does NOT create Quote, Order, or any entity.
    """
    service = QuoteOutputSnapshotService(db)
    html = await service.export_html(quote_id, snapshot_id)
    if not html:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    # Get snapshot for filename
    snapshot_data = await service.get_snapshot(quote_id, snapshot_id)
    snapshot_code = snapshot_data.get("snapshot_code", "unknown") if snapshot_data else "unknown"

    return HTMLResponse(
        content=html,
        headers={
            "Content-Disposition": f'attachment; filename="snapshot_{snapshot_code}.html"',
        },
    )


@router.post("/{quote_id}/output-snapshots/{snapshot_id}/supersede")
async def supersede_snapshot(
    quote_id: int,
    snapshot_id: int,
    request: SupersedeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(require_permission("quote_output_snapshot.manage")),
):
    """Explicitly supersede a snapshot with a newer one."""
    service = QuoteOutputSnapshotService(db)
    result = await service.supersede(
        quote_id, snapshot_id,
        new_snapshot_id=request.new_snapshot_id,
        user=current_user.email or current_user.id,
    )
    if "error" in result:
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# BUILD 11 — Governance / Eligibility Endpoint
# ---------------------------------------------------------------------------

@router.get("/{quote_id}/output-snapshots/governance/eligibility")
async def get_snapshot_eligibility(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Evaluate output snapshot eligibility for a quote.

    READ-ONLY governance endpoint.
    Does NOT mutate Quote, Order, or any entity.
    Does NOT create Order snapshot.
    Does NOT send anything to client.
    Does NOT change any status.

    Returns eligibility status:
      eligible — one approved snapshot, no blockers, source metadata present
      blocked — approved snapshot has blockers or missing content
      needs_review — multiple approved snapshots (conflict) or pending review
      missing — no approved snapshot exists
    """
    service = QuoteOutputSnapshotGovernanceService(db)
    return await service.evaluate_eligibility(quote_id)