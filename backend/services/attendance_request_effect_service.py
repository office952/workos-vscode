"""Generate idempotent attendance effects from approved requests — no auto-apply to pontaj."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from models.attendance_request_effect import AttendanceRequestEffect
from models.employee_attendance_event import EmployeeAttendanceEvent
from models.employee_request import EmployeeRequest
from services.employee_attendance_service import create_attendance_event
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

ATTENDANCE_CAPABLE_REQUEST_TYPES = frozenset(
    {"leave", "day_off", "time_off", "attendance_correction"}
)
SKIPPED_REQUEST_TYPES = frozenset({"advance", "equipment", "issue_report", "other"})

EFFECT_TYPES = frozenset({"leave_range", "day_off", "partial_time_off", "attendance_correction"})
EFFECT_STATUSES = frozenset({"pending", "applied", "conflict", "cancelled"})

REQUEST_TO_EFFECT_TYPE = {
    "leave": "leave_range",
    "day_off": "day_off",
    "time_off": "partial_time_off",
    "attendance_correction": "attendance_correction",
}

CONFLICT_TIME_OFF_HOURS = "time_off_requires_structured_hours"
CONFLICT_CORRECTION_PAYLOAD = "attendance_correction_requires_structured_payload"
CONFLICT_ATTENDANCE_OVERLAP = "attendance_event_overlap"

DEFERRED_APPLY_REQUEST_TYPES = frozenset({"time_off", "attendance_correction"})
APPLY_SUPPORTED_EFFECT_TYPES = frozenset({"leave_range", "day_off"})
ATTENDANCE_EFFECT_SOURCE_PREFIX = "employee_request_effect:"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_date_range(request: EmployeeRequest) -> tuple[Optional[date], Optional[date]]:
    start = request.start_date
    end = request.end_date or request.start_date
    return start, end


def _ranges_overlap(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    return a_start <= b_end and b_start <= a_end


def _serialize(row: AttendanceRequestEffect) -> Dict[str, Any]:
    return {
        "id": row.id,
        "employee_request_id": row.employee_request_id,
        "employee_id": row.employee_id,
        "request_type": row.request_type,
        "effect_type": row.effect_type,
        "status": row.status,
        "date_start": row.date_start.isoformat() if row.date_start else None,
        "date_end": row.date_end.isoformat() if row.date_end else None,
        "hours": row.hours,
        "generated_by_user_id": row.generated_by_user_id,
        "generated_at": row.generated_at.isoformat() if row.generated_at else None,
        "applied_at": row.applied_at.isoformat() if row.applied_at else None,
        "applied_by_user_id": row.applied_by_user_id,
        "source": row.source,
        "notes": row.notes,
        "conflict_reason": row.conflict_reason,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _attendance_source_for_effect(effect_id: int) -> str:
    return f"{ATTENDANCE_EFFECT_SOURCE_PREFIX}{effect_id}"


async def get_attendance_effect_by_id(
    db: AsyncSession,
    effect_id: int,
) -> Optional[AttendanceRequestEffect]:
    return await db.get(AttendanceRequestEffect, effect_id)


async def list_attendance_request_effects(
    db: AsyncSession,
    *,
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    employee_request_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    stmt = select(AttendanceRequestEffect).order_by(
        AttendanceRequestEffect.created_at.desc(),
        AttendanceRequestEffect.id.desc(),
    )
    if status is not None:
        normalized = status.strip().lower()
        if normalized not in EFFECT_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(EFFECT_STATUSES))}")
        stmt = stmt.where(AttendanceRequestEffect.status == normalized)
    if employee_id is not None:
        stmt = stmt.where(AttendanceRequestEffect.employee_id == employee_id)
    if employee_request_id is not None:
        stmt = stmt.where(AttendanceRequestEffect.employee_request_id == employee_request_id)
    result = await db.execute(stmt)
    return [_serialize(row) for row in result.scalars().all()]


async def get_attendance_request_effect_detail(
    db: AsyncSession,
    effect_id: int,
) -> Dict[str, Any]:
    row = await get_attendance_effect_by_id(db, effect_id)
    if row is None:
        raise ValueError(f"attendance effect {effect_id} not found")
    return _serialize(row)


async def get_attendance_effect_for_request(
    db: AsyncSession,
    employee_request_id: int,
) -> Optional[AttendanceRequestEffect]:
    result = await db.execute(
        select(AttendanceRequestEffect).where(
            AttendanceRequestEffect.employee_request_id == employee_request_id
        )
    )
    return result.scalar_one_or_none()


async def list_attendance_effect_generation_candidates(
    db: AsyncSession,
    *,
    employee_id: Optional[int] = None,
    request_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_existing: bool = False,
) -> List[Dict[str, Any]]:
    """Approved attendance-capable requests that may need an effect row."""
    from models.employees import Employees

    stmt = (
        select(EmployeeRequest, Employees, AttendanceRequestEffect)
        .join(Employees, Employees.id == EmployeeRequest.employee_id)
        .outerjoin(
            AttendanceRequestEffect,
            AttendanceRequestEffect.employee_request_id == EmployeeRequest.id,
        )
        .where(
            EmployeeRequest.status == "approved",
            EmployeeRequest.request_type.in_(tuple(sorted(ATTENDANCE_CAPABLE_REQUEST_TYPES))),
        )
        .order_by(EmployeeRequest.reviewed_at.desc(), EmployeeRequest.id.desc())
    )
    if employee_id is not None:
        stmt = stmt.where(EmployeeRequest.employee_id == employee_id)
    if request_type is not None:
        normalized = request_type.strip().lower()
        if normalized not in ATTENDANCE_CAPABLE_REQUEST_TYPES:
            raise ValueError(
                f"request_type must be one of: {', '.join(sorted(ATTENDANCE_CAPABLE_REQUEST_TYPES))}"
            )
        stmt = stmt.where(EmployeeRequest.request_type == normalized)
    if start_date is not None:
        stmt = stmt.where(EmployeeRequest.start_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(EmployeeRequest.end_date <= end_date)

    result = await db.execute(stmt)
    rows: List[Dict[str, Any]] = []
    for req, emp, effect in result.all():
        has_effect = effect is not None
        if not include_existing and has_effect:
            continue
        rows.append(
            {
                "employee_request_id": req.id,
                "employee_id": req.employee_id,
                "employee_name": emp.name,
                "request_type": req.request_type,
                "status": req.status,
                "title": req.title,
                "reason": req.reason,
                "start_date": req.start_date.isoformat() if req.start_date else None,
                "end_date": req.end_date.isoformat() if req.end_date else None,
                "has_effect": has_effect,
                "effect_id": effect.id if effect else None,
                "effect_status": effect.status if effect else None,
            }
        )
    return rows


async def _load_overlapping_attendance_events(
    db: AsyncSession,
    employee_id: int,
    start_date: date,
    end_date: date,
) -> List[EmployeeAttendanceEvent]:
    result = await db.execute(
        select(EmployeeAttendanceEvent).where(
            EmployeeAttendanceEvent.employee_id == employee_id,
            EmployeeAttendanceEvent.event_status != "cancelled",
            EmployeeAttendanceEvent.start_date <= end_date,
            EmployeeAttendanceEvent.end_date >= start_date,
        )
    )
    return list(result.scalars().all())


async def detect_attendance_effect_conflict(
    db: AsyncSession,
    effect: AttendanceRequestEffect,
) -> Optional[str]:
    if effect.status == "conflict" and effect.conflict_reason:
        return effect.conflict_reason

    if effect.request_type == "time_off":
        return CONFLICT_TIME_OFF_HOURS

    if effect.request_type == "attendance_correction":
        return CONFLICT_CORRECTION_PAYLOAD

    if effect.date_start is None or effect.date_end is None:
        return "missing_date_range"

    overlapping = await _load_overlapping_attendance_events(
        db,
        effect.employee_id,
        effect.date_start,
        effect.date_end,
    )
    if overlapping:
        types = ", ".join(sorted({ev.event_type for ev in overlapping}))
        return f"{CONFLICT_ATTENDANCE_OVERLAP}:{types}"

    return None


def _deferred_conflict_for_request_type(request_type: str) -> Optional[str]:
    if request_type == "time_off":
        return CONFLICT_TIME_OFF_HOURS
    if request_type == "attendance_correction":
        return CONFLICT_CORRECTION_PAYLOAD
    return None


async def generate_attendance_effect_for_request(
    db: AsyncSession,
    employee_request: EmployeeRequest,
    generated_by_user_id: str,
) -> Optional[AttendanceRequestEffect]:
    """Create or return existing effect. Returns None when request type skips attendance."""
    if employee_request.status != "approved":
        raise ValueError("Only approved employee requests can generate attendance effects")

    request_type = (employee_request.request_type or "").strip().lower()
    if request_type in SKIPPED_REQUEST_TYPES:
        return None
    if request_type not in ATTENDANCE_CAPABLE_REQUEST_TYPES:
        raise ValueError(f"Unsupported request_type for attendance effects: {request_type}")

    existing = await get_attendance_effect_for_request(db, employee_request.id)
    if existing is not None:
        return existing

    date_start, date_end = _resolve_date_range(employee_request)
    effect_type = REQUEST_TO_EFFECT_TYPE[request_type]
    deferred_reason = _deferred_conflict_for_request_type(request_type)

    status = "pending"
    conflict_reason: Optional[str] = None
    if deferred_reason:
        status = "conflict"
        conflict_reason = deferred_reason
    elif date_start is None:
        status = "conflict"
        conflict_reason = "missing_date_range"
    else:
        overlapping = await _load_overlapping_attendance_events(
            db,
            employee_request.employee_id,
            date_start,
            date_end or date_start,
        )
        if overlapping:
            status = "conflict"
            types = ", ".join(sorted({ev.event_type for ev in overlapping}))
            conflict_reason = f"{CONFLICT_ATTENDANCE_OVERLAP}:{types}"

    now = _utcnow()
    row = AttendanceRequestEffect(
        employee_request_id=employee_request.id,
        employee_id=employee_request.employee_id,
        request_type=request_type,
        effect_type=effect_type,
        status=status,
        date_start=date_start,
        date_end=date_end,
        hours=None,
        generated_by_user_id=generated_by_user_id,
        generated_at=now,
        source="employee_request",
        conflict_reason=conflict_reason,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    try:
        await db.commit()
        await db.refresh(row)
        return row
    except IntegrityError:
        await db.rollback()
        existing_after_race = await get_attendance_effect_for_request(db, employee_request.id)
        if existing_after_race is not None:
            return existing_after_race
        raise


async def _find_applied_attendance_event_for_effect(
    db: AsyncSession,
    effect: AttendanceRequestEffect,
) -> Optional[EmployeeAttendanceEvent]:
    result = await db.execute(
        select(EmployeeAttendanceEvent).where(
            EmployeeAttendanceEvent.employee_id == effect.employee_id,
            EmployeeAttendanceEvent.source == _attendance_source_for_effect(effect.id),
        )
    )
    return result.scalar_one_or_none()


def _attendance_event_type_for_effect(effect: AttendanceRequestEffect) -> str:
    if effect.effect_type == "day_off":
        return "leave"
    if effect.effect_type == "leave_range":
        return "leave"
    raise ValueError(f"apply_unsupported: effect_type {effect.effect_type} is not supported for apply")


async def apply_attendance_request_effect(
    db: AsyncSession,
    effect_id: int,
    applied_by_user_id: str,
) -> Dict[str, Any]:
    """Apply a pending effect to employee_attendance_events — explicit, audited, idempotent."""
    effect = await get_attendance_effect_by_id(db, effect_id)
    if effect is None:
        raise ValueError(f"attendance effect {effect_id} not found")

    if effect.request_type in DEFERRED_APPLY_REQUEST_TYPES:
        raise ValueError(f"apply_unsupported: {effect.request_type} apply is deferred")

    if effect.effect_type not in APPLY_SUPPORTED_EFFECT_TYPES:
        raise ValueError(f"apply_unsupported: effect_type {effect.effect_type} apply is deferred")

    if effect.status == "applied":
        existing_event = await _find_applied_attendance_event_for_effect(db, effect)
        if existing_event is not None:
            return {
                "effect": _serialize(effect),
                "attendance_event_id": existing_event.id,
                "already_applied": True,
            }
        raise ValueError("apply_conflict: effect marked applied but attendance event is missing")

    if effect.status == "cancelled":
        raise ValueError("apply_conflict: cancelled effect cannot be applied")

    if effect.status == "conflict":
        reason = effect.conflict_reason or "effect in conflict"
        raise ValueError(f"apply_conflict: {reason}")

    if effect.status != "pending":
        raise ValueError(f"apply_conflict: unsupported effect status {effect.status}")

    request = await db.get(EmployeeRequest, effect.employee_request_id)
    if request is None:
        raise ValueError(f"employee request {effect.employee_request_id} not found")

    if request.status != "approved":
        raise ValueError(f"apply_conflict: request must be approved (current={request.status})")

    if effect.employee_id != request.employee_id:
        raise ValueError("apply_conflict: effect employee_id does not match request")

    if effect.date_start is None:
        raise ValueError("apply_conflict: effect is missing date_start")

    conflict = await detect_attendance_effect_conflict(db, effect)
    if conflict:
        effect.status = "conflict"
        effect.conflict_reason = conflict
        effect.updated_at = _utcnow()
        await db.commit()
        await db.refresh(effect)
        raise ValueError(f"apply_conflict: {conflict}")

    date_end = effect.date_end or effect.date_start
    event_type = _attendance_event_type_for_effect(effect)
    source = _attendance_source_for_effect(effect.id)

    event_dict = await create_attendance_event(
        db,
        {
            "employee_id": effect.employee_id,
            "start_date": effect.date_start.isoformat(),
            "end_date": date_end.isoformat(),
            "event_type": event_type,
            "event_status": "confirmed",
            "notes": (
                f"Applied from employee request #{effect.employee_request_id} "
                f"(effect #{effect.id})"
            ),
            "source": source,
        },
    )

    now = _utcnow()
    effect.status = "applied"
    effect.applied_at = now
    effect.applied_by_user_id = applied_by_user_id
    effect.updated_at = now
    await db.commit()
    await db.refresh(effect)

    return {
        "effect": _serialize(effect),
        "attendance_event_id": int(event_dict["id"]),
        "attendance_event": event_dict,
        "already_applied": False,
    }


async def cancel_attendance_effect_for_request(
    db: AsyncSession,
    employee_request_id: int,
    reason: Optional[str] = None,
) -> Optional[AttendanceRequestEffect]:
    row = await get_attendance_effect_for_request(db, employee_request_id)
    if row is None:
        return None
    if row.status == "applied":
        raise ValueError("Applied attendance effects cannot be cancelled automatically")
    row.status = "cancelled"
    if reason:
        row.notes = reason
    row.updated_at = _utcnow()
    await db.commit()
    await db.refresh(row)
    return row
