"""Product E2E Readiness Check — read-only Product System endpoints.

GET  /api/v1/product-system/e2e-readiness/{template_code}/static
POST /api/v1/product-system/e2e-readiness/{template_code}/runtime-dry-run
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.product_e2e_readiness import (
    ProductE2EReadinessResult,
    ProductE2ERuntimeDryRunRequest,
)
from services.product_e2e_readiness_service import ProductE2EReadinessService
from services.template_architecture_scope import require_canonical_template_code

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-e2e-readiness"],
    dependencies=[Depends(get_current_user)],
)


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.get(
    "/e2e-readiness/{template_code}/static",
    response_model=ProductE2EReadinessResult,
)
async def get_product_e2e_readiness_static(
    template_code: str,
    db: AsyncSession = Depends(get_db),
) -> ProductE2EReadinessResult:
    """Static template-path readiness. No workspace required. No writes."""
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
                canonical_template_code=identity.canonical_template_code,
                resolution_type=identity.resolution_type,
            ),
        )
    service = ProductE2EReadinessService(db)
    return await service.run_static(identity.canonical_template_code)


@router.post(
    "/e2e-readiness/{template_code}/runtime-dry-run",
    response_model=ProductE2EReadinessResult,
)
async def post_product_e2e_readiness_runtime_dry_run(
    template_code: str,
    body: ProductE2ERuntimeDryRunRequest,
    db: AsyncSession = Depends(get_db),
) -> ProductE2EReadinessResult:
    """Runtime dry-run against a workspace. Forces no_write; never confirms/freezes/creates."""
    if body.dry_run is not True:
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "dry_run_required",
                message="Runtime readiness only supports dry_run=true (no writes).",
            ),
        )
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
                canonical_template_code=identity.canonical_template_code,
                resolution_type=identity.resolution_type,
            ),
        )
    service = ProductE2EReadinessService(db)
    return await service.run_runtime_dry_run(
        identity.canonical_template_code,
        workspace_id=body.workspace_id,
        dry_run=True,
    )
