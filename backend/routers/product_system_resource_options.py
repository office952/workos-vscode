"""Read-only Shared Technical Resource Options endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from dependencies.auth import get_current_user
from schemas.structural_resource_options import (
    ComponentAcceptedOptions,
    StructuralMaterialOption,
    StructuralProfileOption,
    StructuralResourceOptionsResponse,
)
from services.structural_resource_options_service import (
    StructuralResourceOptionsService,
    get_structural_resource_options_service,
)
from services.template_architecture_scope import require_canonical_template_code

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["product-system-resource-options"],
    dependencies=[Depends(get_current_user)],
)


def _svc() -> StructuralResourceOptionsService:
    return get_structural_resource_options_service()


def _error(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.get("/resource-options", response_model=StructuralResourceOptionsResponse)
async def get_resource_options() -> StructuralResourceOptionsResponse:
    return _svc().snapshot()


@router.get("/resource-options/structural-materials", response_model=list[StructuralMaterialOption])
async def list_structural_materials() -> list[StructuralMaterialOption]:
    return _svc().list_materials()


@router.get("/resource-options/structural-profiles", response_model=list[StructuralProfileOption])
async def list_structural_profiles() -> list[StructuralProfileOption]:
    return _svc().list_profiles()


@router.get(
    "/resource-options/by-component/{template_code}",
    response_model=ComponentAcceptedOptions,
)
async def resource_options_by_component(template_code: str) -> ComponentAcceptedOptions:
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
            ),
        )
    accepted = _svc().accepted_for_component(identity.canonical_template_code)
    if accepted is None:
        raise HTTPException(
            status_code=404,
            detail=_error("component_resource_options_not_found", template_code=identity.canonical_template_code),
        )
    return accepted


@router.get(
    "/resource-options/by-component/{template_code}/profiles",
    response_model=list[StructuralProfileOption],
)
async def profiles_by_component(
    template_code: str,
    material_code: str | None = Query(default=None),
) -> list[StructuralProfileOption]:
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
            ),
        )
    return _svc().profiles_for_component(
        identity.canonical_template_code, material_code=material_code
    )
