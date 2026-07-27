"""Internal employee attendance — default present schedule + exception events."""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set

from models.employee_attendance_event import EmployeeAttendanceEvent
from models.employees import Employees
from services.company_calendar import (
    WORK_HOURS_PER_DAY,
    WORKING_WEEKDAYS,
    is_company_workday,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_WORK_HOURS_PER_DAY = WORK_HOURS_PER_DAY
DEFAULT_WORKING_WEEKDAYS: Set[int] = set(WORKING_WEEKDAYS)

EVENT_TYPES = frozenset({"absent", "leave", "sick", "partial", "overtime", "correction"})
EVENT_STATUSES = frozenset({"planned", "approved", "confirmed", "cancelled"})
SUMMARY_STATUSES = frozenset({"planned", "approved", "confirmed"})
FULL_DAY_TYPES = frozenset({"absent", "leave", "sick"})
RANGE_TYPES = frozenset({"absent", "leave", "sick"})
SINGLE_DAY_TYPES = frozenset({"partial", "overtime", "correction"})

_MIN_HOURS = 0.0
_MAX_HOURS = 24.0
_MIN_DELTA = -24.0
_MAX_DELTA = 24.0


def is_working_weekday(day: date) -> bool:
    """Mon–Fri and not a RO legal holiday (Company Calendar)."""
    return is_company_workday(day)


def count_standard_work_days(start_date: date, end_date: date) -> int:
    return len(working_days_in_range(start_date, end_date))


def working_days_in_range(start_date: date, end_date: date) -> List[date]:
    days: List[date] = []
    current = start_date
    while current <= end_date:
        if is_working_weekday(current):
            days.append(current)
        current = date.fromordinal(current.toordinal() + 1)
    return days


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _parse_date(value: Any, field_name: str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError(f"{field_name} must be a valid date")


def validate_event_type(event_type: str) -> str:
    normalized = (event_type or "").strip().lower()
    if normalized not in EVENT_TYPES:
        raise ValueError(f"event_type must be one of: {', '.join(sorted(EVENT_TYPES))}")
    return normalized


def validate_event_status(event_status: str) -> str:
    normalized = (event_status or "").strip().lower()
    if normalized not in EVENT_STATUSES:
        raise ValueError(f"event_status must be one of: {', '.join(sorted(EVENT_STATUSES))}")
    return normalized


def _parse_optional_float(value: Any, field_name: str) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number")


def _validate_hours_range(value: float, field_name: str, min_v: float, max_v: float) -> float:
    if value < min_v or value > max_v:
        raise ValueError(f"{field_name} must be between {min_v} and {max_v}")
    return value


def _ranges_overlap(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    return a_start <= b_end and b_start <= a_end


def _event_to_dict(row: EmployeeAttendanceEvent, employee_name: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "start_date": row.start_date.isoformat(),
        "end_date": row.end_date.isoformat(),
        "event_type": row.event_type,
        "event_status": row.event_status,
        "hours_override": float(row.hours_override) if row.hours_override is not None else None,
        "hours_delta": float(row.hours_delta) if row.hours_delta is not None else None,
        "notes": row.notes,
        "source": row.source,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "employee_name": employee_name,
    }


def _calendar_days_for_event(ev: EmployeeAttendanceEvent, clip_start: date, clip_end: date) -> List[date]:
    """Days this event applies to within [clip_start, clip_end] for summary."""
    if ev.event_status == "cancelled":
        return []
    s = max(ev.start_date, clip_start)
    e = min(ev.end_date, clip_end)
    if s > e:
        return []

    if ev.event_type in SINGLE_DAY_TYPES:
        if ev.start_date < clip_start or ev.start_date > clip_end:
            return []
        return [ev.start_date]

    return working_days_in_range(s, e)


def _full_day_days_for_event(ev: EmployeeAttendanceEvent, clip_start: date, clip_end: date) -> Set[date]:
    if ev.event_type not in FULL_DAY_TYPES or ev.event_status == "cancelled":
        return set()
    return set(_calendar_days_for_event(ev, clip_start, clip_end))


def _apply_day_to_summary(
    event_type: str,
    day: date,
    hours_override: Optional[float],
    hours_delta: Optional[float],
    state: Dict[str, float],
) -> None:
    working = is_working_weekday(day)

    if event_type == "absent" and working:
        state["absent_days"] += 1
        state["present_days"] -= 1
        state["total_hours"] -= DEFAULT_WORK_HOURS_PER_DAY
    elif event_type == "leave" and working:
        state["leave_days"] += 1
        state["present_days"] -= 1
        state["total_hours"] -= DEFAULT_WORK_HOURS_PER_DAY
    elif event_type == "sick" and working:
        state["sick_days"] += 1
        state["present_days"] -= 1
        state["total_hours"] -= DEFAULT_WORK_HOURS_PER_DAY
    elif event_type == "partial" and working:
        override = hours_override if hours_override is not None else 0.0
        state["partial_days"] += 1
        state["present_days"] -= 1
        state["total_hours"] -= (DEFAULT_WORK_HOURS_PER_DAY - override)
    elif event_type == "overtime":
        delta = hours_delta if hours_delta is not None else 0.0
        state["overtime_hours"] += delta
        state["total_hours"] += delta
    elif event_type == "correction":
        if hours_override is not None:
            if working:
                state["total_hours"] += (hours_override - DEFAULT_WORK_HOURS_PER_DAY)
            else:
                state["total_hours"] += hours_override
        if hours_delta is not None:
            state["total_hours"] += hours_delta


def validate_event_payload(
    event_type: str,
    start_date: date,
    end_date: date,
    event_status: str,
    hours_override: Optional[float],
    hours_delta: Optional[float],
    notes: Optional[str],
) -> tuple[str, date, date, str, Optional[float], Optional[float], Optional[str]]:
    et = validate_event_type(event_type)
    es = validate_event_status(event_status)

    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    if et in SINGLE_DAY_TYPES and start_date != end_date:
        raise ValueError(f"{et} events must be single-day (start_date must equal end_date)")

    if et in RANGE_TYPES:
        wd = working_days_in_range(start_date, end_date)
        if not wd:
            raise ValueError(f"{et} range must include at least one standard working weekday")

    if et == "partial":
        if not is_working_weekday(start_date):
            raise ValueError("partial events are only allowed on standard working weekdays")
        if hours_override is None:
            raise ValueError("partial events require hours_override")
        hours_override = _validate_hours_range(hours_override, "hours_override", _MIN_HOURS, _MAX_HOURS)
        hours_delta = None
    elif et == "overtime":
        if hours_delta is None:
            raise ValueError("overtime events require hours_delta")
        hours_delta = _validate_hours_range(hours_delta, "hours_delta", _MIN_DELTA, _MAX_DELTA)
        if hours_delta <= 0:
            raise ValueError("overtime events require hours_delta > 0")
        hours_override = None
    elif et == "correction":
        note_text = (notes or "").strip()
        if not note_text:
            raise ValueError("correction events require notes")
        if hours_override is None and hours_delta is None:
            raise ValueError("correction events require hours_override or hours_delta")
        if hours_override is not None:
            hours_override = _validate_hours_range(hours_override, "hours_override", _MIN_HOURS, _MAX_HOURS)
        if hours_delta is not None:
            hours_delta = _validate_hours_range(hours_delta, "hours_delta", _MIN_DELTA, _MAX_DELTA)
    else:
        hours_override = None
        hours_delta = None

    return et, start_date, end_date, es, hours_override, hours_delta, notes


async def _load_overlapping_events(
    db: AsyncSession,
    employee_id: int,
    start_date: date,
    end_date: date,
    exclude_id: Optional[int] = None,
) -> List[EmployeeAttendanceEvent]:
    stmt = select(EmployeeAttendanceEvent).where(
        EmployeeAttendanceEvent.employee_id == employee_id,
        EmployeeAttendanceEvent.event_status != "cancelled",
        EmployeeAttendanceEvent.start_date <= end_date,
        EmployeeAttendanceEvent.end_date >= start_date,
    )
    if exclude_id is not None:
        stmt = stmt.where(EmployeeAttendanceEvent.id != exclude_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _validate_conflicts(
    db: AsyncSession,
    employee_id: int,
    event_type: str,
    event_status: str,
    start_date: date,
    end_date: date,
    hours_override: Optional[float],
    exclude_id: Optional[int] = None,
) -> None:
    if event_status == "cancelled":
        return

    existing = await _load_overlapping_events(db, employee_id, start_date, end_date, exclude_id)
    new_full_days = (
        set(working_days_in_range(start_date, end_date)) if event_type in FULL_DAY_TYPES else set()
    )

    for ev in existing:
        clip_start = min(start_date, ev.start_date)
        clip_end = max(end_date, ev.end_date)
        ev_full = _full_day_days_for_event(ev, clip_start, clip_end)

        if event_type in FULL_DAY_TYPES and new_full_days.intersection(ev_full):
            raise ValueError(
                f"conflicting full-day event ({ev.event_type}) already covers a day in this range"
            )

        if event_type == "partial":
            if start_date in ev_full:
                raise ValueError("cannot add partial on a day with absent/leave/sick")
            if ev.event_type == "partial" and ev.start_date == start_date:
                raise ValueError("partial event already exists on this day")

        if event_type in FULL_DAY_TYPES:
            for d in new_full_days:
                if ev.event_type == "partial" and ev.start_date == d:
                    raise ValueError("partial event already exists on a day in this range")

    if event_type == "correction" and hours_override is not None:
        day_existing = await _load_overlapping_events(
            db, employee_id, start_date, start_date, exclude_id
        )
        for ev in day_existing:
            if ev.event_type != "overtime":
                raise ValueError(
                    "correction with hours_override cannot overlap other events on the same day"
                )


async def list_attendance_events(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    employee_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")
    stmt = (
        select(EmployeeAttendanceEvent, Employees.name)
        .join(Employees, Employees.id == EmployeeAttendanceEvent.employee_id)
        .where(
            EmployeeAttendanceEvent.start_date <= end_date,
            EmployeeAttendanceEvent.end_date >= start_date,
        )
        .order_by(EmployeeAttendanceEvent.start_date.asc(), EmployeeAttendanceEvent.id.asc())
    )
    if employee_id is not None:
        stmt = stmt.where(EmployeeAttendanceEvent.employee_id == employee_id)
    result = await db.execute(stmt)
    return [_event_to_dict(row, name) for row, name in result.all()]


async def create_attendance_event(db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
    employee_id = int(payload["employee_id"])
    start_date = _parse_date(payload.get("start_date"), "start_date")
    end_date_raw = payload.get("end_date")
    end_date = _parse_date(end_date_raw, "end_date") if end_date_raw is not None else start_date

    emp = await db.get(Employees, employee_id)
    if emp is None:
        raise ValueError(f"employee_id {employee_id} not found")

    hours_override = _parse_optional_float(payload.get("hours_override"), "hours_override")
    hours_delta = _parse_optional_float(payload.get("hours_delta"), "hours_delta")
    notes = payload.get("notes")
    source = (payload.get("source") or "manual").strip() or "manual"
    event_status = validate_event_status(str(payload.get("event_status") or "confirmed"))

    event_type, start_date, end_date, event_status, hours_override, hours_delta, notes = validate_event_payload(
        str(payload.get("event_type", "")),
        start_date,
        end_date,
        event_status,
        hours_override,
        hours_delta,
        notes,
    )

    await _validate_conflicts(
        db, employee_id, event_type, event_status, start_date, end_date, hours_override
    )

    row = EmployeeAttendanceEvent(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        event_status=event_status,
        hours_override=hours_override,
        hours_delta=hours_delta,
        notes=notes,
        source=source,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _event_to_dict(row, emp.name)


async def update_attendance_event(
    db: AsyncSession,
    event_id: int,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    row = await db.get(EmployeeAttendanceEvent, event_id)
    if row is None:
        raise ValueError(f"attendance event {event_id} not found")

    start_date = row.start_date
    if payload.get("start_date") is not None:
        start_date = _parse_date(payload["start_date"], "start_date")

    end_date = row.end_date
    if payload.get("end_date") is not None:
        end_date = _parse_date(payload["end_date"], "end_date")
    elif payload.get("start_date") is not None and payload.get("end_date") is None:
        if row.event_type in SINGLE_DAY_TYPES:
            end_date = start_date

    event_type = row.event_type
    if payload.get("event_type") is not None:
        event_type = validate_event_type(str(payload["event_type"]))

    event_status = row.event_status
    if payload.get("event_status") is not None:
        event_status = validate_event_status(str(payload["event_status"]))

    hours_override = row.hours_override
    if "hours_override" in payload:
        hours_override = _parse_optional_float(payload.get("hours_override"), "hours_override")

    hours_delta = row.hours_delta
    if "hours_delta" in payload:
        hours_delta = _parse_optional_float(payload.get("hours_delta"), "hours_delta")

    notes = row.notes
    if "notes" in payload:
        notes = payload.get("notes")

    event_type, start_date, end_date, event_status, hours_override, hours_delta, notes = validate_event_payload(
        event_type,
        start_date,
        end_date,
        event_status,
        hours_override,
        hours_delta,
        notes,
    )

    await _validate_conflicts(
        db,
        row.employee_id,
        event_type,
        event_status,
        start_date,
        end_date,
        hours_override,
        exclude_id=event_id,
    )

    row.start_date = start_date
    row.end_date = end_date
    row.event_type = event_type
    row.event_status = event_status
    row.hours_override = hours_override
    row.hours_delta = hours_delta
    row.notes = notes
    row.updated_at = datetime.now()

    emp = await db.get(Employees, row.employee_id)
    await db.commit()
    await db.refresh(row)
    return _event_to_dict(row, emp.name if emp else None)


async def delete_attendance_event(db: AsyncSession, event_id: int) -> None:
    row = await db.get(EmployeeAttendanceEvent, event_id)
    if row is None:
        raise ValueError(f"attendance event {event_id} not found")
    await db.delete(row)
    await db.commit()


async def get_attendance_month_summary(db: AsyncSession, year: int, month: int) -> Dict[str, Any]:
    month_start, month_end = _month_bounds(year, month)
    standard_work_days = count_standard_work_days(month_start, month_end)
    standard_hours = standard_work_days * DEFAULT_WORK_HOURS_PER_DAY

    employees_result = await db.execute(
        select(Employees).where(Employees.status == "active").order_by(Employees.name.asc())
    )
    active_employees = employees_result.scalars().all()

    events_result = await db.execute(
        select(EmployeeAttendanceEvent)
        .where(
            EmployeeAttendanceEvent.start_date <= month_end,
            EmployeeAttendanceEvent.end_date >= month_start,
        )
        .order_by(EmployeeAttendanceEvent.start_date.asc(), EmployeeAttendanceEvent.id.asc())
    )
    all_events = events_result.scalars().all()
    events_by_employee: Dict[int, List[EmployeeAttendanceEvent]] = {}
    for ev in all_events:
        events_by_employee.setdefault(ev.employee_id, []).append(ev)

    employee_rows: List[Dict[str, Any]] = []
    for emp in active_employees:
        events = events_by_employee.get(emp.id, [])
        state: Dict[str, float] = {
            "present_days": float(standard_work_days),
            "absent_days": 0.0,
            "leave_days": 0.0,
            "sick_days": 0.0,
            "partial_days": 0.0,
            "overtime_hours": 0.0,
            "total_hours": float(standard_hours),
        }
        status_counts = {"planned": 0, "approved": 0, "confirmed": 0, "cancelled": 0}
        active_event_count = 0

        for ev in events:
            status_counts[ev.event_status] = status_counts.get(ev.event_status, 0) + 1
            if ev.event_status not in SUMMARY_STATUSES:
                continue
            if _ranges_overlap(ev.start_date, ev.end_date, month_start, month_end):
                active_event_count += 1

            if ev.event_type in SINGLE_DAY_TYPES:
                days = _calendar_days_for_event(ev, month_start, month_end)
                for day in days:
                    _apply_day_to_summary(
                        ev.event_type, day, ev.hours_override, ev.hours_delta, state
                    )
            else:
                for day in _calendar_days_for_event(ev, month_start, month_end):
                    _apply_day_to_summary(
                        ev.event_type, day, ev.hours_override, ev.hours_delta, state
                    )

        employee_rows.append(
            {
                "employee_id": emp.id,
                "employee_name": emp.name,
                "standard_work_days": standard_work_days,
                "standard_hours": standard_hours,
                "present_days": int(state["present_days"]),
                "absent_days": int(state["absent_days"]),
                "leave_days": int(state["leave_days"]),
                "sick_days": int(state["sick_days"]),
                "partial_days": int(state["partial_days"]),
                "overtime_hours": float(state["overtime_hours"]),
                "total_hours": float(state["total_hours"]),
                "event_count": active_event_count,
                "planned_event_count": status_counts.get("planned", 0),
                "approved_event_count": status_counts.get("approved", 0),
                "confirmed_event_count": status_counts.get("confirmed", 0),
                "cancelled_event_count": status_counts.get("cancelled", 0),
            }
        )

    return {
        "year": year,
        "month": month,
        "standard_work_hours_per_day": DEFAULT_WORK_HOURS_PER_DAY,
        "employees": employee_rows,
    }
