"""Employee self-service request CRUD — no attendance/payment side effects."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from models.employee_request import EmployeeRequest
from models.employees import Employees
from schemas.auth import UserResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

VALID_REQUEST_TYPES = frozenset(
    {
        "leave",
        "day_off",
        "time_off",
        "advance",
        "attendance_correction",
        "equipment",
        "issue_report",
        "other",
    }
)

DATE_REQUIRED_TYPES = frozenset({"leave", "day_off", "time_off", "attendance_correction"})
AMOUNT_REQUIRED_TYPES = frozenset({"advance"})
CANCELLABLE_STATUSES = frozenset({"draft", "submitted"})
REVIEWABLE_STATUSES = frozenset({"submitted"})
TERMINAL_REVIEW_STATUSES = frozenset({"approved", "rejected", "cancelled"})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_date(value: Any, field: str) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"Invalid {field}: expected ISO date") from exc
    raise ValueError(f"Invalid {field}: expected ISO date string")


def _serialize(row: EmployeeRequest) -> Dict[str, Any]:
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "request_type": row.request_type,
        "status": row.status,
        "title": row.title,
        "description": row.description,
        "start_date": row.start_date.isoformat() if row.start_date else None,
        "end_date": row.end_date.isoformat() if row.end_date else None,
        "amount": row.amount,
        "currency": row.currency,
        "reason": row.reason,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
        "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        "reviewed_by_user_id": row.reviewed_by_user_id,
        "review_note": row.review_note,
    }


def _validate_create_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    request_type = (payload.get("request_type") or "").strip().lower()
    if request_type not in VALID_REQUEST_TYPES:
        raise ValueError(f"Invalid request_type: {request_type}")

    start_date = _parse_date(payload.get("start_date"), "start_date")
    end_date = _parse_date(payload.get("end_date"), "end_date")
    if end_date is None and start_date is not None:
        end_date = start_date
    if start_date and end_date and end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    if request_type in DATE_REQUIRED_TYPES and start_date is None:
        raise ValueError(f"start_date is required for request_type '{request_type}'")

    amount = payload.get("amount")
    currency = (payload.get("currency") or "RON").strip() or "RON"
    if request_type in AMOUNT_REQUIRED_TYPES:
        if amount is None:
            raise ValueError("amount is required for advance requests")
        try:
            amount = float(amount)
        except (TypeError, ValueError) as exc:
            raise ValueError("amount must be a number") from exc
        if amount <= 0:
            raise ValueError("amount must be greater than zero")
    elif amount is not None:
        try:
            amount = float(amount)
        except (TypeError, ValueError) as exc:
            raise ValueError("amount must be a number") from exc

    return {
        "request_type": request_type,
        "title": payload.get("title"),
        "description": payload.get("description"),
        "reason": payload.get("reason"),
        "start_date": start_date,
        "end_date": end_date,
        "amount": amount,
        "currency": currency if amount is not None else (currency if request_type == "advance" else None),
    }


async def create_employee_request(
    db: AsyncSession,
    employee_id: int,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    clean = _validate_create_payload(payload)
    now = _utcnow()
    row = EmployeeRequest(
        employee_id=employee_id,
        request_type=clean["request_type"],
        status="submitted",
        title=clean["title"],
        description=clean["description"],
        reason=clean["reason"],
        start_date=clean["start_date"],
        end_date=clean["end_date"],
        amount=clean["amount"],
        currency=clean["currency"],
        submitted_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _serialize(row)


async def list_employee_requests(db: AsyncSession, employee_id: int) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(EmployeeRequest)
        .where(EmployeeRequest.employee_id == employee_id)
        .order_by(EmployeeRequest.created_at.desc(), EmployeeRequest.id.desc())
    )
    return [_serialize(row) for row in result.scalars().all()]


async def get_employee_request(
    db: AsyncSession,
    employee_id: int,
    request_id: int,
) -> Dict[str, Any]:
    row = await _get_owned_request(db, employee_id, request_id)
    return _serialize(row)


async def cancel_employee_request(
    db: AsyncSession,
    employee_id: int,
    request_id: int,
) -> Dict[str, Any]:
    row = await _get_owned_request(db, employee_id, request_id)
    if row.status not in CANCELLABLE_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "request_not_cancellable",
                "message": f"Request in status '{row.status}' cannot be cancelled.",
            },
        )
    row.status = "cancelled"
    row.updated_at = _utcnow()
    await db.commit()
    await db.refresh(row)
    return _serialize(row)


async def _get_owned_request(
    db: AsyncSession,
    employee_id: int,
    request_id: int,
) -> EmployeeRequest:
    result = await db.execute(
        select(EmployeeRequest).where(
            EmployeeRequest.id == request_id,
            EmployeeRequest.employee_id == employee_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Employee request not found")
    return row


def _serialize_for_review(row: EmployeeRequest, employee: Employees) -> Dict[str, Any]:
    data = _serialize(row)
    data["employee_name"] = employee.name
    data["employee_department"] = employee.department
    data["employee_operational_role"] = employee.role
    data["employee_status"] = employee.status
    return data


async def _get_request_with_employee(
    db: AsyncSession,
    request_id: int,
) -> tuple[EmployeeRequest, Employees]:
    result = await db.execute(
        select(EmployeeRequest, Employees)
        .join(Employees, Employees.id == EmployeeRequest.employee_id)
        .where(EmployeeRequest.id == request_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Employee request not found")
    return row[0], row[1]


async def _active_employee_ids_for_user(db: AsyncSession, user_id: str) -> set[int]:
    if not (user_id or "").strip():
        return set()
    result = await db.execute(
        select(Employees.id).where(
            Employees.user_id == user_id,
            Employees.status == "active",
        )
    )
    return set(result.scalars().all())


async def _linked_employee_ids_for_user(db: AsyncSession, user_id: str) -> set[int]:
    """All employee rows linked to user_id — used for self-review guard regardless of status."""
    if not (user_id or "").strip():
        return set()
    result = await db.execute(select(Employees.id).where(Employees.user_id == user_id))
    return set(result.scalars().all())


async def _assert_not_self_review(
    db: AsyncSession,
    reviewer: UserResponse,
    request_row: EmployeeRequest,
) -> None:
    linked_ids = await _linked_employee_ids_for_user(db, reviewer.id or "")
    if request_row.employee_id in linked_ids:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "self_review_forbidden",
                "message": "Reviewers cannot approve or reject their own employee request.",
            },
        )


def _assert_reviewable_status(row: EmployeeRequest) -> None:
    if row.status in TERMINAL_REVIEW_STATUSES:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "request_not_reviewable",
                "message": f"Request in status '{row.status}' cannot be reviewed.",
            },
        )
    if row.status not in REVIEWABLE_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "request_not_reviewable",
                "message": f"Only submitted requests can be reviewed; got '{row.status}'.",
            },
        )


async def _assert_in_review_scope(
    db: AsyncSession,
    reviewer: UserResponse,
    reviewer_role: str,
    request_row: EmployeeRequest,
) -> None:
    if reviewer_role == "admin":
        return
    from services.employee_manager_team_service import (
        assert_employee_id_in_team_scope,
        resolve_manager_team_scope,
    )

    scope = await resolve_manager_team_scope(db, reviewer, reviewer_role)
    assert_employee_id_in_team_scope(scope, request_row.employee_id)


async def list_employee_requests_for_review(
    db: AsyncSession,
    reviewer: UserResponse,
    reviewer_role: str,
) -> List[Dict[str, Any]]:
    stmt = (
        select(EmployeeRequest, Employees)
        .join(Employees, Employees.id == EmployeeRequest.employee_id)
        .where(EmployeeRequest.status == "submitted")
        .order_by(EmployeeRequest.submitted_at.desc(), EmployeeRequest.id.desc())
    )
    if reviewer_role != "admin":
        from services.employee_manager_team_service import (
            resolve_manager_team_scope,
            team_employee_ids_for_query,
        )

        scope = await resolve_manager_team_scope(db, reviewer, reviewer_role)
        team_ids = team_employee_ids_for_query(scope)
        if team_ids is not None and len(team_ids) == 0:
            return []
        if team_ids is not None:
            stmt = stmt.where(EmployeeRequest.employee_id.in_(team_ids))

    result = await db.execute(stmt)
    return [_serialize_for_review(req, emp) for req, emp in result.all()]


async def get_employee_request_for_review(
    db: AsyncSession,
    request_id: int,
    reviewer: UserResponse,
    reviewer_role: str,
) -> Dict[str, Any]:
    req, emp = await _get_request_with_employee(db, request_id)
    await _assert_in_review_scope(db, reviewer, reviewer_role, req)
    return _serialize_for_review(req, emp)


async def approve_employee_request(
    db: AsyncSession,
    request_id: int,
    reviewer: UserResponse,
    reviewer_role: str,
    review_note: Optional[str] = None,
) -> Dict[str, Any]:
    req, emp = await _get_request_with_employee(db, request_id)
    _assert_reviewable_status(req)
    await _assert_not_self_review(db, reviewer, req)
    await _assert_in_review_scope(db, reviewer, reviewer_role, req)
    now = _utcnow()
    req.status = "approved"
    req.reviewed_at = now
    req.reviewed_by_user_id = reviewer.id
    req.review_note = review_note
    req.updated_at = now
    await db.commit()
    await db.refresh(req)
    return _serialize_for_review(req, emp)


async def reject_employee_request(
    db: AsyncSession,
    request_id: int,
    reviewer: UserResponse,
    reviewer_role: str,
    review_note: Optional[str] = None,
) -> Dict[str, Any]:
    req, emp = await _get_request_with_employee(db, request_id)
    _assert_reviewable_status(req)
    await _assert_not_self_review(db, reviewer, req)
    await _assert_in_review_scope(db, reviewer, reviewer_role, req)
    now = _utcnow()
    req.status = "rejected"
    req.reviewed_at = now
    req.reviewed_by_user_id = reviewer.id
    req.review_note = review_note
    req.updated_at = now
    await db.commit()
    await db.refresh(req)
    return _serialize_for_review(req, emp)
