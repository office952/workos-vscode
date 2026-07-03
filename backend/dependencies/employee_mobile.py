"""Employee self-app dependencies — separate from manager review RBAC."""

from __future__ import annotations

from dataclasses import dataclass

from dependencies.auth import get_current_user
from dependencies.permissions import resolve_effective_role
from fastapi import Depends, HTTPException, status
from schemas.auth import UserResponse
from services.employee_mobile_identity import ResolvedEmployee, resolve_employee_for_user
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db

EMPLOYEE_SELF_ACCESS_ROLES = frozenset({"employee_mobile", "manager", "admin"})


@dataclass(frozen=True)
class EmployeeMobileContext:
    """Authenticated user resolved to exactly one active employee (self context)."""

    user: UserResponse
    employee: ResolvedEmployee


async def require_employee_self_user(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> EmployeeMobileContext:
    """
    Employee self-app access: role in EMPLOYEE_SELF_ACCESS_ROLES + linked active employee.

    Role grants zone access; employees.user_id grants identity. Does not grant review rights.
    """
    effective_role = resolve_effective_role(current_user.role)
    if effective_role not in EMPLOYEE_SELF_ACCESS_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "employee_self_role_required",
                "role": effective_role,
                "message": (
                    "Employee self access requires role "
                    f"in {sorted(EMPLOYEE_SELF_ACCESS_ROLES)}."
                ),
            },
        )

    employee = await resolve_employee_for_user(db, current_user)
    return EmployeeMobileContext(user=current_user, employee=employee)


async def require_employee_mobile_self(
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> EmployeeMobileContext:
    """Backward-compatible alias for employee-mobile self routes."""
    return await require_employee_self_user(db=db, current_user=current_user)
