"""Monthly productive hours from Company Calendar − approved leave.

Owner rule: ore_productive_luna must NOT be entered manually per employee.
Formula: company workdays × 8 − approved leave days (on company workdays) × 8,
clipped to each employee's employment interval (data_angajare / end_date).
HR/Pontaj = internal cost & availability — never client tariff.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Set

from models.employee_attendance_event import EmployeeAttendanceEvent
from models.employees import Employees
from services.company_calendar import (
    WORK_HOURS_PER_DAY,
    company_workdays_in_month,
    company_workdays_in_range,
    count_company_workdays_in_month,
    holidays_in_month,
    month_bounds,
    standard_productive_hours_for_month,
)
from services.employee_lifecycle import employment_workdays_in_month
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Owner: approved leave deducted. Confirmed is treated as approved-for-capacity.
APPROVED_LEAVE_STATUSES = frozenset({"approved", "confirmed"})


def _leave_days_on_workdays(
    events: Iterable[EmployeeAttendanceEvent],
    workdays: Set[date],
) -> Set[date]:
    deducted: Set[date] = set()
    for ev in events:
        if ev.event_type != "leave":
            continue
        if ev.event_status not in APPROVED_LEAVE_STATUSES:
            continue
        for day in company_workdays_in_range(ev.start_date, ev.end_date):
            if day in workdays:
                deducted.add(day)
    return deducted


def productive_hours_from_parts(
    company_workdays: int,
    approved_leave_days: int,
) -> float:
    net_days = max(0, int(company_workdays) - int(approved_leave_days))
    return float(net_days) * WORK_HOURS_PER_DAY


async def load_approved_leave_events(
    db: AsyncSession,
    *,
    year: int,
    month: int,
    employee_ids: Optional[Iterable[int]] = None,
) -> List[EmployeeAttendanceEvent]:
    month_start, month_end = month_bounds(year, month)
    stmt = select(EmployeeAttendanceEvent).where(
        EmployeeAttendanceEvent.event_type == "leave",
        EmployeeAttendanceEvent.event_status.in_(tuple(APPROVED_LEAVE_STATUSES)),
        EmployeeAttendanceEvent.start_date <= month_end,
        EmployeeAttendanceEvent.end_date >= month_start,
    )
    if employee_ids is not None:
        ids = list(employee_ids)
        if not ids:
            return []
        stmt = stmt.where(EmployeeAttendanceEvent.employee_id.in_(ids))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _load_employees_map(
    db: AsyncSession, employee_ids: Iterable[int]
) -> Dict[int, Employees]:
    ids = list(employee_ids)
    if not ids:
        return {}
    result = await db.execute(select(Employees).where(Employees.id.in_(ids)))
    return {e.id: e for e in result.scalars().all()}


async def compute_employee_productive_hours(
    db: AsyncSession,
    employee_id: int,
    *,
    year: int,
    month: int,
) -> Dict[str, Any]:
    """Calculate productive hours for one employee in a calendar month."""
    emp_map = await _load_employees_map(db, [employee_id])
    emp = emp_map.get(employee_id)
    if emp is None:
        workdays = company_workdays_in_month(year, month)
    else:
        workdays = employment_workdays_in_month(emp, year, month)
    workday_set = set(workdays)
    events = await load_approved_leave_events(
        db, year=year, month=month, employee_ids=[employee_id]
    )
    leave_days = _leave_days_on_workdays(events, workday_set)
    hours = productive_hours_from_parts(len(workdays), len(leave_days))
    return {
        "employee_id": employee_id,
        "year": year,
        "month": month,
        "company_workdays": len(workdays),
        "public_holidays_in_month": [d.isoformat() for d in holidays_in_month(year, month)],
        "approved_leave_days": len(leave_days),
        "approved_leave_dates": [d.isoformat() for d in sorted(leave_days)],
        "hours_per_day": WORK_HOURS_PER_DAY,
        "ore_productive_luna": hours,
        "source": "company_calendar_minus_approved_leave_clipped_employment",
        "employment_clipped": emp is not None,
    }


async def compute_productive_hours_by_employee(
    db: AsyncSession,
    employee_ids: Iterable[int],
    *,
    year: int,
    month: int,
) -> Dict[int, float]:
    """Batch productive hours for CostEngine aggregation (employment-clipped)."""
    ids = list(employee_ids)
    if not ids:
        return {}

    emp_map = await _load_employees_map(db, ids)
    events = await load_approved_leave_events(
        db, year=year, month=month, employee_ids=ids
    )
    by_emp: Dict[int, List[EmployeeAttendanceEvent]] = {}
    for ev in events:
        by_emp.setdefault(ev.employee_id, []).append(ev)

    out: Dict[int, float] = {}
    for emp_id in ids:
        emp = emp_map.get(emp_id)
        if emp is None:
            workdays = company_workdays_in_month(year, month)
        else:
            workdays = employment_workdays_in_month(emp, year, month)
        workday_set = set(workdays)
        leave_days = _leave_days_on_workdays(by_emp.get(emp_id, []), workday_set)
        out[emp_id] = productive_hours_from_parts(len(workdays), len(leave_days))
    return out


def calendar_baseline_hours(year: int, month: int) -> float:
    """Hours before leave — useful for read-only UI when leave fetch is unavailable."""
    return standard_productive_hours_for_month(year, month)


def company_workday_count(year: int, month: int) -> int:
    return count_company_workdays_in_month(year, month)
