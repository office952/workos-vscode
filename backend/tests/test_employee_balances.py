"""Tests for internal employee balance ledger."""

from __future__ import annotations

import pytest
from models.employees import Employees
from services.employee_balance_service import (
    cancel_employee_balance_transaction,
    create_employee_balance_transaction,
    delete_employee_balance_transaction,
    get_employee_balance_summary,
    list_employee_balance_transactions,
)


async def _seed_active(db_session, name: str = "Andrei Goghi") -> Employees:
    emp = Employees(name=name, status="active", employee_type="productive")
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


def _summary_row(summary: dict, employee_id: int) -> dict:
    return next(r for r in summary["employees"] if r["employee_id"] == employee_id)


@pytest.mark.asyncio
async def test_create_advance_increases_active_balance(db_session):
    emp = await _seed_active(db_session)
    await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp.id,
            "transaction_date": "2026-06-11",
            "transaction_type": "advance",
            "amount": 500,
            "currency": "RON",
            "notes": "Avans",
        },
    )
    row = _summary_row(await get_employee_balance_summary(db_session), emp.id)
    assert row["active_balance"] == 500
    assert row["advance_total"] == 500
    assert row["transaction_count"] == 1


@pytest.mark.asyncio
async def test_create_loan_increases_active_balance(db_session):
    emp = await _seed_active(db_session)
    await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp.id,
            "transaction_date": "2026-06-11",
            "transaction_type": "loan",
            "amount": 300,
        },
    )
    row = _summary_row(await get_employee_balance_summary(db_session), emp.id)
    assert row["active_balance"] == 300
    assert row["loan_total"] == 300


@pytest.mark.asyncio
async def test_create_retention_increases_active_balance(db_session):
    emp = await _seed_active(db_session)
    await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp.id,
            "transaction_date": "2026-06-11",
            "transaction_type": "retention",
            "amount": 200,
        },
    )
    row = _summary_row(await get_employee_balance_summary(db_session), emp.id)
    assert row["active_balance"] == 200
    assert row["retention_total"] == 200


@pytest.mark.asyncio
async def test_repayment_decreases_active_balance(db_session):
    emp = await _seed_active(db_session)
    await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp.id,
            "transaction_date": "2026-06-10",
            "transaction_type": "advance",
            "amount": 500,
        },
    )
    await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp.id,
            "transaction_date": "2026-06-11",
            "transaction_type": "repayment",
            "amount": 200,
        },
    )
    row = _summary_row(await get_employee_balance_summary(db_session), emp.id)
    assert row["active_balance"] == 300
    assert row["repayment_total"] == 200


@pytest.mark.asyncio
async def test_compensation_decreases_active_balance(db_session):
    emp = await _seed_active(db_session)
    await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp.id,
            "transaction_date": "2026-06-10",
            "transaction_type": "loan",
            "amount": 400,
        },
    )
    await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp.id,
            "transaction_date": "2026-06-11",
            "transaction_type": "compensation",
            "amount": 150,
        },
    )
    row = _summary_row(await get_employee_balance_summary(db_session), emp.id)
    assert row["active_balance"] == 250
    assert row["compensation_total"] == 150


@pytest.mark.asyncio
async def test_cancelled_transaction_does_not_affect_summary(db_session):
    emp = await _seed_active(db_session)
    created = await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp.id,
            "transaction_date": "2026-06-11",
            "transaction_type": "advance",
            "amount": 500,
        },
    )
    await cancel_employee_balance_transaction(db_session, created["id"])
    row = _summary_row(await get_employee_balance_summary(db_session), emp.id)
    assert row["active_balance"] == 0
    assert row["transaction_count"] == 0


@pytest.mark.asyncio
async def test_adjustment_without_notes_rejected(db_session):
    emp = await _seed_active(db_session)
    with pytest.raises(ValueError, match="notes"):
        await create_employee_balance_transaction(
            db_session,
            {
                "employee_id": emp.id,
                "transaction_date": "2026-06-11",
                "transaction_type": "adjustment",
                "amount": 50,
            },
        )


@pytest.mark.asyncio
async def test_amount_zero_or_negative_rejected(db_session):
    emp = await _seed_active(db_session)
    with pytest.raises(ValueError, match="amount"):
        await create_employee_balance_transaction(
            db_session,
            {
                "employee_id": emp.id,
                "transaction_date": "2026-06-11",
                "transaction_type": "advance",
                "amount": 0,
            },
        )


@pytest.mark.asyncio
async def test_invalid_employee_rejected(db_session):
    with pytest.raises(ValueError, match="not found"):
        await create_employee_balance_transaction(
            db_session,
            {
                "employee_id": 99999,
                "transaction_date": "2026-06-11",
                "transaction_type": "advance",
                "amount": 100,
            },
        )


@pytest.mark.asyncio
async def test_summary_includes_active_employees_with_zero_balance(db_session):
    emp = await _seed_active(db_session)
    summary = await get_employee_balance_summary(db_session)
    row = _summary_row(summary, emp.id)
    assert row["active_balance"] == 0
    assert row["transaction_count"] == 0


@pytest.mark.asyncio
async def test_cancel_endpoint_sets_cancelled(db_session):
    emp = await _seed_active(db_session)
    created = await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp.id,
            "transaction_date": "2026-06-11",
            "transaction_type": "advance",
            "amount": 100,
        },
    )
    cancelled = await cancel_employee_balance_transaction(db_session, created["id"])
    assert cancelled["status"] == "cancelled"


@pytest.mark.asyncio
async def test_list_filters_by_employee_and_type(db_session):
    emp1 = await _seed_active(db_session, "A")
    emp2 = await _seed_active(db_session, "B")
    await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp1.id,
            "transaction_date": "2026-06-11",
            "transaction_type": "advance",
            "amount": 100,
        },
    )
    await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp2.id,
            "transaction_date": "2026-06-11",
            "transaction_type": "loan",
            "amount": 200,
        },
    )
    rows = await list_employee_balance_transactions(
        db_session, employee_id=emp1.id, transaction_type="advance"
    )
    assert len(rows) == 1
    assert rows[0]["employee_id"] == emp1.id
    assert rows[0]["transaction_type"] == "advance"


@pytest.mark.asyncio
async def test_delete_removes_transaction(db_session):
    emp = await _seed_active(db_session)
    created = await create_employee_balance_transaction(
        db_session,
        {
            "employee_id": emp.id,
            "transaction_date": "2026-06-11",
            "transaction_type": "advance",
            "amount": 100,
        },
    )
    await delete_employee_balance_transaction(db_session, created["id"])
    row = _summary_row(await get_employee_balance_summary(db_session), emp.id)
    assert row["active_balance"] == 0
