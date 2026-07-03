"""Manager/admin review dependency — separate from employee self app."""

from __future__ import annotations

from dataclasses import dataclass

from dependencies.auth import get_current_user
from dependencies.permissions import resolve_effective_role
from fastapi import Depends, HTTPException, status
from schemas.auth import UserResponse

EMPLOYEE_REQUEST_REVIEWER_ROLES = frozenset({"admin", "manager"})


@dataclass(frozen=True)
class EmployeeRequestReviewerContext:
    user: UserResponse
    role: str


async def require_employee_request_reviewer(
    current_user: UserResponse = Depends(get_current_user),
) -> EmployeeRequestReviewerContext:
    """
    Restrict request review routes to admin/manager.

    Does not resolve employee identity — review is not self-app access.
    """
    effective_role = resolve_effective_role(current_user.role)
    if effective_role not in EMPLOYEE_REQUEST_REVIEWER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "employee_request_reviewer_required",
                "role": effective_role,
                "message": "Request review requires role 'admin' or 'manager'.",
            },
        )
    return EmployeeRequestReviewerContext(user=current_user, role=effective_role)
