"""
BUILD 9 — Quote Output Composition Preview Router.

Endpoints:
  GET /api/v1/entities/quotes/{quote_id}/output-composition-preview
    Returns the read-only output composition preview DTO.

  GET /api/v1/entities/quotes/{quote_id}/output-composition-preview/export
    Returns the composition preview as downloadable HTML.

Auth: follows existing project pattern (get_current_user dependency).

Rules:
  - Read-only — no persist, no mutation
  - No Quote creation/modification
  - No Order creation/modification
  - No ProductTemplate mutation
  - No BlueprintDossier mutation
  - No CostEngine formula calculation
  - No document snapshot created
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from services.quote_output_composition_service import QuoteOutputCompositionService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/quotes",
    tags=["quote-output-composition"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/{quote_id}/output-composition-preview")
async def get_output_composition_preview(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get the read-only output composition preview for a quote.

    Combines output blocks rendering with quote commercial data.
    Does NOT persist, mutate, or create any entities.
    """
    service = QuoteOutputCompositionService(db)
    result = await service.compose_preview(quote_id)

    dto = result.to_dict()

    if "quote_not_found" in dto.get("blockers", []):
        raise HTTPException(status_code=404, detail="Quote not found")

    return dto


@router.get("/{quote_id}/output-composition-preview/export", response_class=HTMLResponse)
async def export_output_composition_preview(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export the output composition preview as downloadable HTML.

    PREVIEW ONLY — not saved, not sent, not an accepted order snapshot.
    """
    service = QuoteOutputCompositionService(db)
    result = await service.compose_preview(quote_id)

    dto = result.to_dict()

    if "quote_not_found" in dto.get("blockers", []):
        raise HTTPException(status_code=404, detail="Quote not found")

    html_content = service.render_composition_html(dto)
    quote_code = dto.get("quote_code", "unknown")

    return HTMLResponse(
        content=html_content,
        headers={
            "Content-Disposition": f'attachment; filename="output_composition_preview_{quote_code}.html"',
        },
    )