"""Resolve operational employee identity from authenticated user — self-only boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status
from models.employees import Employees
from schemas.auth import UserResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

MOBILE_ELIGIBLE_STATUSES = frozenset({"active"})


@dataclass(frozen=True)
class ResolvedEmployee:
    """Minimal employee projection safe for employee-mobile context."""

    id: int
    name: str
    status: str
    role: Optional[str]
    department: Optional[str]
    user_id: str


async def resolve_employee_for_user(
    db: AsyncSession,
    current_user: UserResponse,
) -> ResolvedEmployee:
    """
    Resolve exactly one active employee row linked via employees.user_id.

    Never accepts client-supplied employee_id.
    """
    user_id = (current_user.id or "").strip()
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "employee_link_missing",
                "message": "Authenticated user has no id for employee resolution.",
            },
        )

    result = await db.execute(
        select(Employees).where(Employees.user_id == user_id).order_by(Employees.id.asc())
    )
    rows = list(result.scalars().all())

    if len(rows) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "employee_link_missing",
                "message": "No employee record linked to this user.",
            },
        )

    if len(rows) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "employee_link_ambiguous",
                "message": "Multiple employee records linked to this user.",
            },
        )

    row = rows[0]
    if row.status not in MOBILE_ELIGIBLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "employee_not_active",
                "message": f"Employee status '{row.status}' is not eligible for mobile self access.",
            },
        )

    return ResolvedEmployee(
        id=row.id,
        name=row.name,
        status=row.status,
        role=row.role,
        department=row.department,
        user_id=user_id,
    )
