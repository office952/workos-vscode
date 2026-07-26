"""Collaboration membership API schemas — HELPER join/leave (Phase 1)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MEMBERSHIP_ROLE_HELPER = "helper"
MEMBERSHIP_STATUS_ACTIVE = "active"
MEMBERSHIP_STATUS_INACTIVE = "inactive"

JoinSource = Literal["self_join", "manager_add", "help_accept"]
MembershipStatus = Literal["active", "inactive"]
MembershipRole = Literal["helper"]


class HelperMembershipRead(BaseModel):
    """Persisted HELPER membership — authorization intent, not work proof."""

    employee_id: int
    employee_name: str | None = None
    status: MembershipStatus
    role: MembershipRole = MEMBERSHIP_ROLE_HELPER
    joined_at: str
    left_at: str | None = None
    join_source: str | None = None
    membership_id: int | None = None


class MembershipActionResponse(BaseModel):
    status: str = "ok"
    action: Literal["join", "leave"]
    order_id: int
    task_id: str
    employee_id: int
    membership: HelperMembershipRead
    already_joined: bool = False
    already_left: bool = False
    reactivated: bool = False


class TaskMembershipListResponse(BaseModel):
    order_id: int
    task_id: str
    memberships: list[HelperMembershipRead] = Field(default_factory=list)
    active_count: int = 0
