"""Read-only Mini-module Contract Registry endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from dependencies.auth import get_current_user
from schemas.mini_module_registry import MiniModuleContract, MiniModuleRegistryResponse
from services.mini_module_registry_service import (
    MiniModuleRegistryService,
    get_mini_module_registry_service,
)
from services.template_architecture_scope import require_canonical_template_code

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-mini-modules"],
    dependencies=[Depends(get_current_user)],
)


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


def _service() -> MiniModuleRegistryService:
    return get_mini_module_registry_service()


@router.get("/mini-modules", response_model=MiniModuleRegistryResponse)
async def list_mini_modules() -> MiniModuleRegistryResponse:
    """Return all registered mini-module operational contracts (read-only)."""
    return _service().list_all()


@router.get("/mini-modules/by-template/{template_code}", response_model=MiniModuleRegistryResponse)
async def get_mini_modules_by_template(template_code: str) -> MiniModuleRegistryResponse:
    """Return mini-modules applicable to a product template_code."""
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
                canonical_template_code=identity.canonical_template_code,
                resolution_type=identity.resolution_type,
                legacy_alias_used=identity.legacy_alias_used,
                resolution_source=identity.resolution_source,
            ),
        )
    return _service().get_by_template(identity.canonical_template_code)


@router.get("/mini-modules/{module_code}", response_model=MiniModuleContract)
async def get_mini_module(module_code: str) -> MiniModuleContract:
    """Return one mini-module contract by module_code."""
    module = _service().get_by_code(module_code)
    if module is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope("module_not_found", module_code=module_code),
        )
    return module
