"""
Phase 6 — ProductSystem Execution Preview endpoint (S27).

Read-only endpoint:
  GET /api/v1/product_system/preview/{order_id}

Returns a ProductSystemExecutionPreview envelope.
No writes. No mutations. Pure read-only.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from data_models.execution_preview import ProductSystemExecutionPreview
from services.product_system_execution_output_service import (
    OrderNotFoundError,
    ProductSystemExecutionPreviewService,
    TemplateCodeNotFoundError,
)
from services.product_system_linkage_validator import (
    TemplateInactiveError,
    TemplateNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product_system",
    tags=["product-system-preview"],
    dependencies=[Depends(get_current_user)],
)


def _error_envelope(error: str, **kwargs: Any) -> Dict[str, Any]:
    body: Dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.get("/preview/{order_id}", response_model=ProductSystemExecutionPreview)
async def get_execution_preview(
    order_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ProductSystemExecutionPreview:
    """
    Generate the execution preview envelope for a given order.

    Returns a ProductSystemExecutionPreview with generated_operations,
    generated_task_requirements, missing_links, blockers, warnings, and trace_source.

    No writes. No mutations. Pure read-only.
    """
    service = ProductSystemExecutionPreviewService(db)

    try:
        result = await service.preview_for_execution(order_id)
    except OrderNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope("order_not_found", order_id=order_id),
        )
    except TemplateCodeNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "template_not_found", template_code=exc.template_code
            ),
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "template_not_found", template_id=exc.template_id
            ),
        )
    except TemplateInactiveError as exc:
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "template_inactive",
                template_id=exc.template_id,
                template_code=exc.template_code,
            ),
        )
    except Exception as exc:
        logger.error(
            "Unexpected error generating preview for order %d: %s",
            order_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=_error_envelope(
                "internal_error",
                message="Preview service encountered an unexpected error",
            ),
        )

    return result