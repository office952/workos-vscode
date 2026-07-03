"""
Phase 4 — ProductSystem Registry Linkage Validation endpoint (S27).

Read-only endpoint:
  GET /api/v1/product_system/validate/{template_id}

Returns a LinkageValidationResult envelope.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from data_models.linkage_contracts import LinkageValidationResult
from services.product_system_linkage_validator import (
    ProductSystemLinkageValidator,
    TemplateInactiveError,
    TemplateNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product_system",
    tags=["product-system-validation"],
    dependencies=[Depends(get_current_user)],
)


def _error_envelope(error: str, **kwargs: Any) -> Dict[str, Any]:
    body: Dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.get("/validate/{template_id}", response_model=LinkageValidationResult)
async def validate_template_linkage(
    template_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LinkageValidationResult:
    """
    Validate all task_template linkage fields for a given product template.

    Returns a LinkageValidationResult with blockers, warnings, and missing_links.
    No writes. No mutations. Pure read-only validation.
    """
    validator = ProductSystemLinkageValidator(db)

    try:
        result = await validator.validate_template_linkage(template_id)
    except TemplateNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope("template_not_found", template_id=template_id),
        )
    except TemplateInactiveError as exc:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "template_inactive",
                template_id=template_id,
                template_code=exc.template_code,
            ),
        )
    except Exception as exc:
        logger.error(
            "Unexpected error validating template %d: %s", template_id, exc, exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=_error_envelope("internal_error", message="Validation service encountered an unexpected error"),
        )

    return result