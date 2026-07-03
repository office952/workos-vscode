"""Tests for live employee payment situation + recording."""

from __future__ import annotations

import pytest
from models.employees import Employees
from services.employee_payment_record_service import (
    cancel_employee_payment_record,
    create_employee_payment_record,
)
from services.employee_payment_situation_service import get_employee_payment_situation


async def _seed_employee(
    db_session,
    name: str,
    cost_lunar_firma: float | None = 8500.0,
    monthly_internal_pay_amount: float | None = None,
) -> Employees:
    emp = Employees(
        name=name,
        status="active",
        employee_type="productive",
        cost_lunar_firma=cost_lunar_firma,
        monthly_internal_pay_amount=monthly_internal_pay_amount,
        ore_productive_luna=160.0,
    )
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


def _employee_row(situation: dict, employee_id: int) -> dict:
    return next(e for e in situation["employees"] if e["employee_id"] == employee_id)


@pytest.mark.asyncio
async def test_situation_uses_profile_salary_halves(db_session):
    emp = await _seed_employee(db_session, "Andrei Goghi", 8000.0, 4000.0)
    situation = await get_employee_payment_situation(db_session, 2026, 6)
    row = _employee_row(situation, emp.id)
    assert row["salary_monthly"] == 8000.0
    assert row["salary_amount"] == 8000.0
    assert row["base_source"] == "employee_profile_salary"
    assert row["slots"]["15"]["expected_amount"] == 4000.0
    assert row["slots"]["30"]["expected_amount"] == 4000.0
    assert row["monthly_expected_amount"] == 8000.0


@pytest.mark.asyncio
async def test_chirila_7000_internal_null_slot_expected_3500(db_session):
    emp = await _seed_employee(db_session, "Chirila Cristian", 7000.0, None)
    situation = await get_employee_payment_situation(db_session, 2026, 6)
    row = _employee_row(situation, emp.id)
    assert row["missing_pay_base"] is False
    assert row["slots"]["15"]["expected_amount"] == 3500.0
    assert row["slots"]["30"]["expected_amount"] == 3500.0


@pytest.mark.asyncio
async def test_cost_lunar_firma_wins_over_monthly_internal_pay_amount(db_session):
    emp = await _seed_employee(db_session, "Split Base", 8000.0, 4000.0)
    situation = await get_employee_payment_situation(db_session, 2026, 6)
    row = _employee_row(situation, emp.id)
    assert row["slots"]["15"]["expected_amount"] == 4000.0
    assert row["slots"]["30"]["expected_amount"] == 4000.0


@pytest.mark.asyncio
async def test_missing_profile_salary_when_cost_lunar_null_or_zero(db_session):
    emp_null = await _seed_employee(db_session, "No Salary", None, 5000.0)
    emp_zero = await _seed_employee(db_session, "Zero Salary", 0.0, 5000.0)
    situation = await get_employee_payment_situation(db_session, 2026, 6)
    row_null = _employee_row(situation, emp_null.id)
    row_zero = _employee_row(situation, emp_zero.id)
    assert row_null["missing_pay_base"] is True
    assert "missing_profile_salary" in row_null["warnings"]
    assert row_null["slots"]["15"]["expected_amount"] == 0.0
    assert row_zero["missing_pay_base"] is True
    assert row_zero["slots"]["15"]["expected_amount"] == 0.0


@pytest.mark.asyncio
async def test_create_payment_allowed_when_profile_salary_positive(db_session):
    emp = await _seed_employee(db_session, "Pay OK", 7000.0, None)
    created = await create_employee_payment_record(
        db_session,
        {
            "employee_id": emp.id,
            "year": 2026,
            "month": 6,
            "slot": "15",
            "amount_paid": 500,
            "payment_date": "2026-06-11",
        },
    )
    assert created["amount_paid"] == 500.0


@pytest.mark.asyncio
async def test_create_payment_rejected_without_profile_salary(db_session):
    emp = await _seed_employee(db_session, "Pay Blocked", None, 4000.0)
    with pytest.raises(ValueError, match="profile salary"):
        await create_employee_payment_record(
            db_session,
            {
                "employee_id": emp.id,
                "year": 2026,
                "month": 6,
                "slot": "15",
                "amount_paid": 100,
                "payment_date": "2026-06-11",
            },
        )


@pytest.mark.asyncio
async def test_create_payment_partial_then_full_status(db_session):
    emp = await _seed_employee(db_session, "Pay Test", 8000.0)
    await create_employee_payment_record(
        db_session,
        {
            "employee_id": emp.id,
            "year": 2026,
            "month": 6,
            "slot": "15",
            "amount_paid": 500,
            "payment_date": "2026-06-11",
        },
    )
    situation = await get_employee_payment_situation(db_session, 2026, 6)
    slot15 = _employee_row(situation, emp.id)["slots"]["15"]
    assert slot15["paid_amount"] == 500.0
    assert slot15["remaining_amount"] == 3500.0
    assert slot15["status"] == "partial"

    await create_employee_payment_record(
        db_session,
        {
            "employee_id": emp.id,
            "year": 2026,
            "month": 6,
            "slot": "15",
            "amount_paid": 3500,
            "payment_date": "2026-06-12",
        },
    )
    situation = await get_employee_payment_situation(db_session, 2026, 6)
    slot15 = _employee_row(situation, emp.id)["slots"]["15"]
    assert slot15["paid_amount"] == 4000.0
    assert slot15["remaining_amount"] == 0.0
    assert slot15["status"] == "paid"


@pytest.mark.asyncio
async def test_cancelled_payment_not_counted_as_paid(db_session):
    emp = await _seed_employee(db_session, "Cancel Test", 8000.0)
    created = await create_employee_payment_record(
        db_session,
        {
            "employee_id": emp.id,
            "year": 2026,
            "month": 6,
            "slot": "15",
            "amount_paid": 800,
            "payment_date": "2026-06-11",
        },
    )
    await cancel_employee_payment_record(db_session, created["id"], "test")
    situation = await get_employee_payment_situation(db_session, 2026, 6)
    slot15 = _employee_row(situation, emp.id)["slots"]["15"]
    assert slot15["paid_amount"] == 0.0
    assert len(slot15["history"]) == 1
    assert slot15["history"][0]["cancelled"] is True


@pytest.mark.asyncio
async def test_situation_does_not_mutate_employee_fields(db_session):
    emp = await _seed_employee(db_session, "Stable", 8000.0, 4000.0)
    await get_employee_payment_situation(db_session, 2026, 6)
    refreshed = await db_session.get(Employees, emp.id)
    assert refreshed.monthly_internal_pay_amount == 4000.0
    assert refreshed.cost_lunar_firma == 8000.0


@pytest.mark.asyncio
async def test_employee_without_salary_still_listed(db_session):
    emp = await _seed_employee(db_session, "No Base", None)
    situation = await get_employee_payment_situation(db_session, 2026, 6)
    ids = [e["employee_id"] for e in situation["employees"]]
    assert emp.id in ids
