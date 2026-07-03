"""Manager team read-only workspace — admin/manager guard, server-side team scope."""

from __future__ import annotations

from dataclasses import dataclass

from dependencies.auth import get_current_user
from dependencies.permissions import resolve_effective_role
from fastapi import Depends, HTTPException, status
from schemas.auth import UserResponse
from services.employee_manager_team_service import (
    MANAGER_TEAM_READER_ROLES,
    ManagerTeamScope,
    resolve_manager_team_scope,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db


@dataclass(frozen=True)
class ManagerTeamReaderContext:
    user: UserResponse
    role: str
    scope: ManagerTeamScope


async def require_manager_team_reader(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> ManagerTeamReaderContext:
    effective_role = resolve_effective_role(current_user.role)
    if effective_role not in MANAGER_TEAM_READER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "manager_team_reader_required",
                "role": effective_role,
                "message": "Manager team workspace requires role 'admin' or 'manager'.",
            },
        )
    scope = await resolve_manager_team_scope(db, current_user, effective_role)
    return ManagerTeamReaderContext(
        user=current_user,
        role=effective_role,
        scope=scope,
    )
