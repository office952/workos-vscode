"""Company Calendar + productive hours (Cost Intern, not client tariff)."""

from __future__ import annotations

from datetime import date

import pytest
from models.employees import Employees
from services.company_calendar import (
    WORK_HOURS_PER_DAY,
    count_company_workdays_in_month,
    is_company_workday,
    is_public_holiday,
    standard_productive_hours_for_month,
)
from services.employee_attendance_service import create_attendance_event
from services.employee_productive_hours import (
    compute_employee_productive_hours,
    compute_productive_hours_by_employee,
    productive_hours_from_parts,
)
from services.cost_engine_config import CostEngineConfigService
from services.employees import is_valid_for_cost_engine


def test_ro_holidays_factual_2026():
    assert is_public_holiday(date(2026, 1, 1))
    assert is_public_holiday(date(2026, 4, 13))  # Easter Monday
    assert is_public_holiday(date(2026, 6, 1))  # Children's Day / Pentecost Monday
    assert not is_public_holiday(date(2026, 7, 15))


def test_june_2026_excludes_holiday_monday():
    # June 1 2026 is Monday holiday → not a company workday
    assert not is_company_workday(date(2026, 6, 1))
    assert is_company_workday(date(2026, 6, 2))
    # 22 Mon–Fri minus June 1 holiday = 21 company workdays
    assert count_company_workdays_in_month(2026, 6) == 21
    assert standard_productive_hours_for_month(2026, 6) == 21 * WORK_HOURS_PER_DAY


def test_july_2026_no_holidays_on_weekdays():
    # July 2026: 23 Mon–Fri, no RO public holidays mid-month
    assert count_company_workdays_in_month(2026, 7) == 23
    assert standard_productive_hours_for_month(2026, 7) == 184.0


def test_productive_hours_from_parts():
    assert productive_hours_from_parts(21, 0) == 168.0
    assert productive_hours_from_parts(21, 5) == 128.0
    assert productive_hours_from_parts(5, 10) == 0.0


def test_is_valid_for_cost_engine_hours_not_required():
    assert is_valid_for_cost_engine(
        {
            "employee_type": "productive",
            "status": "active",
            "cost_lunar_firma": 7000,
            "ore_productive_luna": None,
        }
    )
    assert not is_valid_for_cost_engine(
        {
            "employee_type": "productive",
            "status": "active",
            "cost_lunar_firma": None,
            "ore_productive_luna": 140,
        }
    )


@pytest.mark.asyncio
async def test_approved_leave_deducted_planned_ignored(db_session):
    emp = Employees(
        name="Calin",
        status="active",
        employee_type="productive",
        cost_lunar_firma=8500,
    )
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)

    # Planned leave — must NOT reduce CostEngine capacity hours
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-07-06",
            "end_date": "2026-07-10",
            "event_type": "leave",
            "event_status": "planned",
        },
    )
    # Approved leave — Mon–Wed 3 company workdays
    await create_attendance_event(
        db_session,
        {
            "employee_id": emp.id,
            "start_date": "2026-07-13",
            "end_date": "2026-07-15",
            "event_type": "leave",
            "event_status": "approved",
        },
    )

    detail = await compute_employee_productive_hours(
        db_session, emp.id, year=2026, month=7
    )
    assert detail["company_workdays"] == 23
    assert detail["approved_leave_days"] == 3
    assert detail["ore_productive_luna"] == 20 * WORK_HOURS_PER_DAY

    by_id = await compute_productive_hours_by_employee(
        db_session, [emp.id], year=2026, month=7
    )
    assert by_id[emp.id] == 160.0


@pytest.mark.asyncio
async def test_cost_engine_uses_calendar_hours_without_stored_field(db_session):
    # Isolate: deactivate any leftover productive rows from sibling tests.
    from sqlalchemy import select, update

    await db_session.execute(
        update(Employees).values(status="inactive")
    )
    await db_session.commit()

    emp = Employees(
        name="Florin CNC Calendar",
        status="active",
        employee_type="productive",
        cost_lunar_firma=8000,
        ore_productive_luna=None,
    )
    db_session.add(emp)
    await db_session.commit()

    cfg = await CostEngineConfigService(db_session).compute_base_config(
        year=2026, month=7
    )
    assert cfg["valid"] is True
    assert cfg["total_productive_hours_month"] == 184.0
    assert cfg["productive_hours_source"] == "company_calendar_minus_approved_leave"
    assert abs(cfg["average_labour_hour_cost"] - (8000 / 184.0)) < 0.01
    assert not any("employee_invalid" in w for w in cfg["warnings"])
    # sanity: only one active productive remains
    active = (
        await db_session.execute(
            select(Employees).where(
                Employees.status == "active",
                Employees.employee_type == "productive",
            )
        )
    ).scalars().all()
    assert len(active) == 1
