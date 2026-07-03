"""Tests for monthly_internal_pay_amount on employees — separate from cost_lunar_firma."""

from __future__ import annotations

import pytest
from models.employees import Employees
from routers.employees import _serialize
from services.employees import EmployeesService


@pytest.mark.asyncio
async def test_create_employee_with_internal_pay_amount(db_session):
    svc = EmployeesService(db_session)
    row = await svc.create(
        {
            "name": "Andrei Goghi",
            "status": "active",
            "employee_type": "productive",
            "cost_lunar_firma": 8500.0,
            "ore_productive_luna": 160.0,
            "monthly_internal_pay_amount": 4000.0,
        }
    )
    assert row.cost_lunar_firma == 8500.0
    assert row.monthly_internal_pay_amount == 4000.0


@pytest.mark.asyncio
async def test_update_internal_pay_without_changing_company_cost(db_session):
    svc = EmployeesService(db_session)
    row = await svc.create(
        {
            "name": "Test Worker",
            "status": "active",
            "employee_type": "productive",
            "cost_lunar_firma": 7000.0,
            "ore_productive_luna": 140.0,
            "monthly_internal_pay_amount": 3500.0,
        }
    )
    updated = await svc.update(
        row.id,
        {"monthly_internal_pay_amount": 4200.0},
    )
    assert updated is not None
    assert updated.monthly_internal_pay_amount == 4200.0
    assert updated.cost_lunar_firma == 7000.0


@pytest.mark.asyncio
async def test_negative_internal_pay_amount_rejected(db_session):
    svc = EmployeesService(db_session)
    with pytest.raises(ValueError, match="monthly_internal_pay_amount"):
        await svc.create(
            {
                "name": "Bad Pay",
                "status": "active",
                "employee_type": "productive",
                "monthly_internal_pay_amount": -100,
            }
        )


def test_serialize_maps_salary_amount_to_company_cost_not_internal_pay():
    row = Employees(
        id=1,
        name="Andrei",
        status="active",
        employee_type="productive",
        cost_lunar_firma=8500.0,
        monthly_internal_pay_amount=4000.0,
        ore_productive_luna=160.0,
    )
    payload = _serialize(row)
    assert payload.cost_lunar_firma == 8500.0
    assert payload.monthly_internal_pay_amount == 4000.0
    assert payload.salary_amount == 8500.0
    assert payload.salary_amount != payload.monthly_internal_pay_amount
