"""Operator/admin visibility for employee task clarification requests."""

from __future__ import annotations

from typing import List, Optional

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from routers.employee_mobile_tasks import TaskClarificationResponse
from schemas.auth import UserResponse
from services.task_clarification_request_service import (
    list_clarification_requests,
    resolve_clarification_request,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/api/v1/operator",
    tags=["operator-clarifications"],
    dependencies=[Depends(get_current_user)],
)


class ClarificationResolveBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


@router.get(
    "/clarification-requests",
    response_model=List[TaskClarificationResponse],
    dependencies=[Depends(require_permission("execution.clarification_list"))],
)
async def get_clarification_requests(
    status: Optional[str] = Query(default="open"),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_clarification_requests(db, status=status)
    return [TaskClarificationResponse(**row) for row in rows]


@router.patch(
    "/clarification-requests/{request_id}/resolve",
    response_model=TaskClarificationResponse,
    dependencies=[Depends(require_permission("execution.clarification_resolve"))],
)
async def patch_resolve_clarification_request(
    request_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await resolve_clarification_request(
        db,
        request_id=request_id,
        resolved_by_user_id=current_user.id,
    )
    return TaskClarificationResponse(**row)
