"""Employee lifecycle foundation — hire/end dates, soft-end, capacity clip."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from models.employees import Employees
from services.company_calendar import WORK_HOURS_PER_DAY
from services.employee_lifecycle import (
    employment_workdays_in_month,
    is_assignable,
    is_employed_on,
)
from services.employee_productive_hours import compute_employee_productive_hours
from services.employees import EmployeesService, VALID_STATUSES


def test_valid_statuses_include_ended():
    assert "ended" in VALID_STATUSES
    assert "inactive" in VALID_STATUSES


def test_employment_interval_and_assignable():
    emp = {
        "status": "active",
        "data_angajare": "2026-07-10",
        "end_date": "2026-07-20",
    }
    assert is_employed_on(emp, date(2026, 7, 15))
    assert not is_employed_on(emp, date(2026, 7, 9))
    assert not is_employed_on(emp, date(2026, 7, 21))
    assert is_assignable(emp, date(2026, 7, 15))
    assert not is_assignable({**emp, "status": "ended"}, date(2026, 7, 15))
    assert not is_assignable(emp, date(2026, 7, 25))


def test_july_employment_clip_workdays():
    # Hired mid-July 2026 (Fri 10), ends Fri 17 → Mon–Fri 10,13,14,15,16,17 = 6 workdays
    emp = {
        "status": "active",
        "data_angajare": date(2026, 7, 10),
        "end_date": date(2026, 7, 17),
    }
    days = employment_workdays_in_month(emp, 2026, 7)
    assert len(days) == 6
    assert days[0] == date(2026, 7, 10)
    assert days[-1] == date(2026, 7, 17)


@pytest.mark.asyncio
async def test_productive_hours_clipped_to_employment(db_session):
    emp = Employees(
        name="Hire Mid Month",
        status="active",
        employee_type="productive",
        cost_lunar_firma=8000,
        data_angajare=datetime(2026, 7, 10, tzinfo=timezone.utc),
        end_date=datetime(2026, 7, 17, tzinfo=timezone.utc),
    )
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)

    detail = await compute_employee_productive_hours(
        db_session, emp.id, year=2026, month=7
    )
    assert detail["company_workdays"] == 6
    assert detail["ore_productive_luna"] == 6 * WORK_HOURS_PER_DAY
    assert "employment" in detail["source"]


@pytest.mark.asyncio
async def test_soft_end_never_hard_deletes(db_session):
    emp = Employees(
        name="To End",
        status="active",
        employee_type="productive",
        cost_lunar_firma=7000,
        data_angajare=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    emp_id = emp.id

    svc = EmployeesService(db_session)
    ended = await svc.end_employment(emp_id, status="ended")
    assert ended is not None
    assert ended.status == "ended"
    assert ended.end_date is not None

    # Row still exists — not hard-deleted
    still = await svc.get_by_id(emp_id)
    assert still is not None
    assert still.status == "ended"
    assert not is_assignable(still, date.today())

    # delete() path is soft-end too
    emp2 = Employees(
        name="Soft Delete Path",
        status="active",
        employee_type="productive",
        cost_lunar_firma=7000,
    )
    db_session.add(emp2)
    await db_session.commit()
    await db_session.refresh(emp2)
    ok = await svc.delete(emp2.id)
    assert ok is True
    row = await svc.get_by_id(emp2.id)
    assert row is not None
    assert row.status == "ended"
