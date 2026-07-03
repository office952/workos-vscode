"""
Foundation Registries — Roles router (read-only, M2).

Implements 4 endpoints per spec__foundation_registries_api.md §7.1–§7.4:

  GET /api/v1/roles
  GET /api/v1/roles/{role_code}
  GET /api/v1/roles/{role_code}/skills
  GET /api/v1/roles/{role_code}/workcenters

All endpoints are read-only. No mutations are importable from this module.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from services.foundation_registries import (
    InvalidQueryParamError,
    RolesReadService,
    is_valid_code,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/roles",
    tags=["foundation-registries"],
    dependencies=[Depends(get_current_user)],
)


# ---------------------------------------------------------------------------
# Pydantic schemas (inline per codebase convention).
# ---------------------------------------------------------------------------


class Role(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_id: str
    role_code: str
    role_name: str
    role_type: Optional[str] = None
    is_operational: bool
    description: Optional[str] = None
    active: bool
    related_skill_ids: List[str] = Field(default_factory=list)
    related_workcenter_ids: List[str] = Field(default_factory=list)
    skill_count: int
    workcenter_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int
    offset: int
    total: int
    has_more: bool


class PaginatedRoles(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: List[Role]
    pagination: PaginationMeta


class SkillEmbedded(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: str
    skill_code: str
    skill_name: str
    skill_category: Optional[str] = None
    active: bool


class WorkcenterEmbedded(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workcenter_id: str
    workcenter_code: str
    workcenter_name: str
    workcenter_type: Optional[str] = None
    operational_status: Optional[str] = None
    active: bool


class RoleSkillsSemantics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    empty_is_intentional: bool
    administrative_role: bool
    rationale: Optional[str] = None


class RoleSkillsExpanded(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_code: str
    role_id: str
    skills: List[SkillEmbedded]
    skill_count: int
    semantics: RoleSkillsSemantics


class RoleWorkcentersFlags(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temporary_partial: bool
    temporary_partial_rationale: Optional[str] = None


class RoleWorkcentersExpanded(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_code: str
    role_id: str
    workcenters: List[WorkcenterEmbedded]
    workcenter_count: int
    flags: RoleWorkcentersFlags
    semantics: RoleSkillsSemantics


# ---------------------------------------------------------------------------
# Error helpers. Return the canonical ErrorEnvelope shape without leaking
# stack traces.
# ---------------------------------------------------------------------------


_LIST_ALLOWED_PARAMS: frozenset[str] = frozenset(
    {"role_type", "is_operational", "active", "q", "sort", "limit", "offset"}
)
_ROLE_SKILLS_ALLOWED_PARAMS: frozenset[str] = frozenset({"active", "sort"})
_ROLE_WORKCENTERS_ALLOWED_PARAMS: frozenset[str] = frozenset(
    {"active", "operational_status"}
)


def _error_body(
    code: str, message: str, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    if request_id:
        body["error"]["request_id"] = request_id
    return body


def _raise_envelope(status_code: int, code: str, message: str, *, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None) -> None:
    raise HTTPException(status_code=status_code, detail=_error_body(code, message, details, request_id)["error"])


def _request_id(request: Request) -> Optional[str]:
    return request.headers.get("X-Request-Id")


def _reject_unknown_params(request: Request, allowed: frozenset[str]) -> None:
    extras = [k for k in request.query_params.keys() if k not in allowed]
    if extras:
        _raise_envelope(
            400,
            "INVALID_QUERY_PARAM",
            f"Unknown query parameter(s): {sorted(extras)}.",
            details={"unknown_params": sorted(extras), "allowed_params": sorted(allowed)},
            request_id=_request_id(request),
        )


def _validate_role_code(role_code: str, request: Request) -> None:
    if not is_valid_code(role_code):
        _raise_envelope(
            400,
            "INVALID_ROLE_CODE",
            f"role_code '{role_code}' is not a valid canonical code.",
            details={"role_code": role_code},
            request_id=_request_id(request),
        )


# ---------------------------------------------------------------------------
# Routes.
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedRoles)
async def list_roles(
    request: Request,
    role_type: Optional[str] = Query(None, description="Canonical role category filter."),
    is_operational: Optional[bool] = Query(None, description="true=operational only, false=administrative only."),
    active: Optional[bool] = Query(True, description="Filter by active flag. Default true."),
    q: Optional[str] = Query(None, max_length=100, description="Partial match on role_code/role_name."),
    sort: Optional[str] = Query(None, description="Sort field, prefix with '-' for DESC."),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List roles with filtering, sorting, offset pagination."""
    _reject_unknown_params(request, _LIST_ALLOWED_PARAMS)
    service = RolesReadService(db)
    try:
        result = await service.list(
            role_type=role_type,
            is_operational=is_operational,
            active=active,
            q=q,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        return result
    except InvalidQueryParamError as e:
        _raise_envelope(
            400, "INVALID_QUERY_PARAM", str(e),
            details={"param": e.param, "reason": e.reason},
            request_id=_request_id(request),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing roles: %s", e, exc_info=True)
        _raise_envelope(
            500, "INTERNAL_ERROR", "An internal error occurred while listing roles.",
            request_id=_request_id(request),
        )


@router.get("/{role_code}", response_model=Role)
async def get_role(
    role_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return a single role by canonical code."""
    # Single-resource endpoints reject unknown query params too.
    _reject_unknown_params(request, frozenset())
    _validate_role_code(role_code, request)
    service = RolesReadService(db)
    try:
        role = await service.get_by_code(role_code)
    except Exception as e:
        logger.error("Error fetching role %s: %s", role_code, e, exc_info=True)
        _raise_envelope(
            500, "INTERNAL_ERROR", "An internal error occurred while fetching role.",
            request_id=_request_id(request),
        )
        return  # pragma: no cover
    if role is None:
        _raise_envelope(
            404, "ROLE_NOT_FOUND", f"Role '{role_code}' does not exist in the registry.",
            details={"role_code": role_code},
            request_id=_request_id(request),
        )
    return role


@router.get("/{role_code}/skills", response_model=RoleSkillsExpanded)
async def get_role_skills(
    role_code: str,
    request: Request,
    active: Optional[bool] = Query(True),
    sort: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return expanded skills for a role, preserving canonical array order."""
    _reject_unknown_params(request, _ROLE_SKILLS_ALLOWED_PARAMS)
    _validate_role_code(role_code, request)
    service = RolesReadService(db)
    try:
        result = await service.list_role_skills(role_code, active=active, sort=sort)
    except InvalidQueryParamError as e:
        _raise_envelope(
            400, "INVALID_QUERY_PARAM", str(e),
            details={"param": e.param, "reason": e.reason},
            request_id=_request_id(request),
        )
        return  # pragma: no cover
    except Exception as e:
        logger.error("Error expanding skills for %s: %s", role_code, e, exc_info=True)
        _raise_envelope(
            500, "INTERNAL_ERROR", "An internal error occurred while expanding skills.",
            request_id=_request_id(request),
        )
        return  # pragma: no cover
    if result is None:
        _raise_envelope(
            404, "ROLE_NOT_FOUND", f"Role '{role_code}' does not exist in the registry.",
            details={"role_code": role_code},
            request_id=_request_id(request),
        )
    return result


@router.get("/{role_code}/workcenters", response_model=RoleWorkcentersExpanded)
async def get_role_workcenters(
    role_code: str,
    request: Request,
    active: Optional[bool] = Query(True),
    operational_status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return expanded workcenters for a role; carries TEMPORARY_PARTIAL flag."""
    _reject_unknown_params(request, _ROLE_WORKCENTERS_ALLOWED_PARAMS)
    _validate_role_code(role_code, request)
    service = RolesReadService(db)
    try:
        result = await service.list_role_workcenters(
            role_code, active=active, operational_status=operational_status
        )
    except InvalidQueryParamError as e:
        _raise_envelope(
            400, "INVALID_QUERY_PARAM", str(e),
            details={"param": e.param, "reason": e.reason},
            request_id=_request_id(request),
        )
        return  # pragma: no cover
    except Exception as e:
        logger.error("Error expanding workcenters for %s: %s", role_code, e, exc_info=True)
        _raise_envelope(
            500, "INTERNAL_ERROR", "An internal error occurred while expanding workcenters.",
            request_id=_request_id(request),
        )
        return  # pragma: no cover
    if result is None:
        _raise_envelope(
            404, "ROLE_NOT_FOUND", f"Role '{role_code}' does not exist in the registry.",
            details={"role_code": role_code},
            request_id=_request_id(request),
        )
    return result