"""
Foundation Registries — Skills router (read-only, M2).

Implements 2 endpoints per spec__foundation_registries_api.md §7.5–§7.6:

  GET /api/v1/skills
  GET /api/v1/skills/{skill_code}
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from services.foundation_registries import (
    InvalidQueryParamError,
    SkillsReadService,
    is_valid_code,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/skills",
    tags=["foundation-registries"],
    dependencies=[Depends(get_current_user)],
)


class Skill(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: str
    skill_code: str
    skill_name: str
    skill_category: Optional[str] = None
    description: Optional[str] = None
    active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int
    offset: int
    total: int
    has_more: bool


class PaginatedSkills(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: List[Skill]
    pagination: PaginationMeta


_LIST_ALLOWED_PARAMS: frozenset[str] = frozenset(
    {"skill_category", "active", "q", "sort", "limit", "offset"}
)


def _error_detail(code: str, message: str, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {"code": code, "message": message}
    if details:
        body["details"] = details
    if request_id:
        body["request_id"] = request_id
    return body


def _raise(status_code: int, code: str, message: str, *, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None) -> None:
    raise HTTPException(status_code=status_code, detail=_error_detail(code, message, details, request_id))


def _request_id(request: Request) -> Optional[str]:
    return request.headers.get("X-Request-Id")


def _reject_unknown_params(request: Request, allowed: frozenset[str]) -> None:
    extras = [k for k in request.query_params.keys() if k not in allowed]
    if extras:
        _raise(
            400, "INVALID_QUERY_PARAM",
            f"Unknown query parameter(s): {sorted(extras)}.",
            details={"unknown_params": sorted(extras), "allowed_params": sorted(allowed)},
            request_id=_request_id(request),
        )


@router.get("", response_model=PaginatedSkills)
async def list_skills(
    request: Request,
    skill_category: Optional[str] = Query(None),
    active: Optional[bool] = Query(True),
    q: Optional[str] = Query(None, max_length=100),
    sort: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    _reject_unknown_params(request, _LIST_ALLOWED_PARAMS)
    service = SkillsReadService(db)
    try:
        return await service.list(
            skill_category=skill_category,
            active=active,
            q=q,
            sort=sort,
            limit=limit,
            offset=offset,
        )
    except InvalidQueryParamError as e:
        _raise(
            400, "INVALID_QUERY_PARAM", str(e),
            details={"param": e.param, "reason": e.reason},
            request_id=_request_id(request),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing skills: %s", e, exc_info=True)
        _raise(
            500, "INTERNAL_ERROR", "An internal error occurred while listing skills.",
            request_id=_request_id(request),
        )


@router.get("/{skill_code}", response_model=Skill)
async def get_skill(
    skill_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    _reject_unknown_params(request, frozenset())
    if not is_valid_code(skill_code):
        _raise(
            400, "INVALID_SKILL_CODE",
            f"skill_code '{skill_code}' is not a valid canonical code.",
            details={"skill_code": skill_code},
            request_id=_request_id(request),
        )
    service = SkillsReadService(db)
    try:
        skill = await service.get_by_code(skill_code)
    except Exception as e:
        logger.error("Error fetching skill %s: %s", skill_code, e, exc_info=True)
        _raise(
            500, "INTERNAL_ERROR", "An internal error occurred while fetching skill.",
            request_id=_request_id(request),
        )
        return  # pragma: no cover
    if skill is None:
        _raise(
            404, "SKILL_NOT_FOUND",
            f"Skill '{skill_code}' does not exist in the registry.",
            details={"skill_code": skill_code},
            request_id=_request_id(request),
        )
    return skill