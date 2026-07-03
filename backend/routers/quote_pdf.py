"""
BUILD 15 — Quote PDF Generation Router.

Endpoints (ADDITIVE — does NOT modify existing commercial-document endpoints):
  POST /api/v1/entities/quotes/{quote_id}/pdf/generate
  GET  /api/v1/entities/quotes/{quote_id}/pdf/latest
  GET  /api/v1/entities/quotes/{quote_id}/pdf/archive
  GET  /api/v1/entities/quotes/{quote_id}/pdf/{archive_id}/download

All endpoints are read-only except POST /generate which creates a PDF + archive record.
No mutations to quotes, orders, inventory, or cost engine.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from services.quote_pdf_service import QuotePdfService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/quotes",
    tags=["quote-pdf"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/{quote_id}/pdf/generate", status_code=201)
async def generate_quote_pdf(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("quote.export_pdf")),
):
    """Generate a new PDF from the current quote state.

    Creates a PDF file and stores an archive record with traceability.
    Does NOT modify the quote or any other entity.
    """
    service = QuotePdfService(db)
    generated_by = current_user.get("email") if isinstance(current_user, dict) else None

    result = await service.generate_pdf(quote_id, generated_by=generated_by)

    if "error" in result:
        error = result["error"]
        if error == "quote_not_found":
            raise HTTPException(status_code=404, detail="Quote not found")
        if error == "pdf_generation_failed":
            raise HTTPException(status_code=500, detail="PDF generation failed")
        raise HTTPException(status_code=500, detail=error)

    return result


@router.get("/{quote_id}/pdf/latest")
async def get_latest_pdf(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Download the most recent generated PDF for a quote.

    Returns PDF bytes with Content-Disposition attachment header.
    """
    service = QuotePdfService(db)
    archive = await service.get_latest(quote_id)

    if not archive:
        raise HTTPException(
            status_code=404,
            detail="No PDF generated for this quote",
        )

    pdf_bytes = service.get_pdf_bytes(archive)
    if not pdf_bytes:
        raise HTTPException(
            status_code=404,
            detail="PDF file not found on disk",
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{archive.filename}"',
        },
    )


@router.get("/{quote_id}/pdf/archive")
async def get_pdf_archive(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List all generated PDF documents for a quote (history).

    Returns archive records ordered by newest first.
    """
    service = QuotePdfService(db)
    archives = await service.get_archive_list(quote_id)

    return [
        {
            "id": a.id,
            "quote_id": a.quote_id,
            "quote_code": a.quote_code,
            "quote_version": a.quote_version,
            "filename": a.filename,
            "file_size_bytes": a.file_size_bytes,
            "content_hash": a.content_hash,
            "generated_by": a.generated_by,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in archives
    ]


@router.get("/{quote_id}/pdf/{archive_id}/download")
async def download_archived_pdf(
    quote_id: int,
    archive_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Download a specific archived PDF by its archive ID.

    Validates that the archive belongs to the specified quote_id.
    """
    service = QuotePdfService(db)
    archive = await service.get_archive_by_id(quote_id, archive_id)

    if not archive:
        raise HTTPException(
            status_code=404,
            detail="Archive record not found or does not belong to this quote",
        )

    pdf_bytes = service.get_pdf_bytes(archive)
    if not pdf_bytes:
        raise HTTPException(
            status_code=404,
            detail="PDF file not found on disk",
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{archive.filename}"',
        },
    )