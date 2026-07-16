"""Collaboration help request API schemas — Phase 2."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

HELP_STATUS_OPEN = "OPEN"
HELP_STATUS_CANCELLED = "CANCELLED"
HELP_STATUS_DECLINED = "DECLINED"
HELP_STATUS_CLOSED = "CLOSED"

HelpStatus = Literal["OPEN", "CANCELLED", "DECLINED", "CLOSED"]


class HelpRequestCreateBody(BaseModel):
    """Create OPEN help — targeted_employee_id null = broadcast."""

    targeted_employee_id: int | None = None
    reason: str | None = Field(default=None, max_length=512)
    competence_hint: str | None = Field(default=None, max_length=128)


class HelpRequestRead(BaseModel):
    help_request_id: int
    order_id: int
    task_id: str
    requested_by_employee_id: int
    targeted_employee_id: int | None = None
    status: HelpStatus
    reason: str | None = None
    competence_hint: str | None = None
    created_at: str
    updated_at: str
    closed_at: str | None = None
    is_broadcast: bool = True


class HelpActionResponse(BaseModel):
    status: str = "ok"
    action: Literal["create", "accept", "decline", "cancel", "close"]
    help_request: HelpRequestRead
    membership_already_active: bool = False
    membership_reactivated: bool = False
    membership_id: int | None = None


class HelpRequestListResponse(BaseModel):
    order_id: int
    task_id: str | None = None
    help_requests: list[HelpRequestRead] = Field(default_factory=list)


class ManagerAddMembershipBody(BaseModel):
    """Operator invite — HELPER membership without help request."""

    employee_id: int
