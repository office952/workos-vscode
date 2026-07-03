"""
BUILD 9 — Output Blocks Coverage Diagnostics Router.

Endpoint:
  GET /api/v1/product-system/output-blocks/coverage
    Returns coverage diagnostics for output blocks across all product templates.

Auth: follows existing project pattern (get_current_user dependency).
Read-only — no persist, no mutation.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from services.output_blocks_coverage_service import OutputBlocksCoverageService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product-system/output-blocks",
    tags=["output-blocks-coverage"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/coverage")
async def get_output_blocks_coverage(
    db: AsyncSession = Depends(get_db),
):
    """Get output blocks coverage diagnostics.

    Reports which templates have output_blocks_json populated,
    which are partial, and which are missing.

    Read-only — no persist, no mutation.
    """
    service = OutputBlocksCoverageService(db)
    return await service.get_coverage()