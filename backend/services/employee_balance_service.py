"""Internal employee balance ledger — advances, loans, retentions (not fiscal payroll)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from models.employee_balance_transaction import EmployeeBalanceTransaction
from models.employees import Employees
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_CURRENCY = "RON"

TRANSACTION_TYPES = frozenset(
    {"advance", "loan", "retention", "repayment", "compensation", "adjustment"}
)
TRANSACTION_STATUSES = frozenset({"active", "settled", "cancelled"})
INCREASE_TYPES = frozenset({"advance", "loan", "retention", "adjustment"})
DECREASE_TYPES = frozenset({"repayment", "compensation"})


def validate_transaction_type(transaction_type: str) -> str:
    normalized = (transaction_type or "").strip().lower()
    if normalized not in TRANSACTION_TYPES:
        raise ValueError(f"transaction_type must be one of: {', '.join(sorted(TRANSACTION_TYPES))}")
    return normalized


def validate_transaction_status(status: str) -> str:
    normalized = (status or "").strip().lower()
    if normalized not in TRANSACTION_STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(TRANSACTION_STATUSES))}")
    return normalized


def signed_amount(transaction_type: str, amount: float) -> float:
    if transaction_type in INCREASE_TYPES:
        return amount
    if transaction_type in DECREASE_TYPES:
        return -amount
    return 0.0


def _parse_date(value: Any, field_name: str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError(f"{field_name} must be a valid date")


def _parse_amount(value: Any) -> float:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise ValueError("amount must be a number")
    if amount <= 0:
        raise ValueError("amount must be greater than 0")
    return amount


def _transaction_to_dict(row: EmployeeBalanceTransaction, employee_name: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "transaction_date": row.transaction_date.isoformat(),
        "transaction_type": row.transaction_type,
        "amount": float(row.amount),
        "currency": row.currency,
        "status": row.status,
        "notes": row.notes,
        "source": row.source,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "employee_name": employee_name,
        "signed_amount": signed_amount(row.transaction_type, float(row.amount)),
    }


def validate_transaction_payload(
    transaction_type: str,
    amount: float,
    currency: str,
    status: str,
    notes: Optional[str],
) -> tuple[str, float, str, str, Optional[str]]:
    tt = validate_transaction_type(transaction_type)
    st = validate_transaction_status(status)
    amt = _parse_amount(amount)
    cur = (currency or DEFAULT_CURRENCY).strip().upper()
    if not cur:
        raise ValueError("currency must be non-empty")
    if tt == "adjustment" and not (notes or "").strip():
        raise ValueError("adjustment transactions require notes")
    return tt, amt, cur, st, notes


async def list_employee_balance_transactions(
    db: AsyncSession,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    if start_date and end_date and end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    stmt = (
        select(EmployeeBalanceTransaction, Employees.name)
        .join(Employees, Employees.id == EmployeeBalanceTransaction.employee_id)
        .order_by(
            EmployeeBalanceTransaction.transaction_date.desc(),
            EmployeeBalanceTransaction.id.desc(),
        )
    )
    if employee_id is not None:
        stmt = stmt.where(EmployeeBalanceTransaction.employee_id == employee_id)
    if status is not None:
        stmt = stmt.where(EmployeeBalanceTransaction.status == validate_transaction_status(status))
    if transaction_type is not None:
        stmt = stmt.where(
            EmployeeBalanceTransaction.transaction_type == validate_transaction_type(transaction_type)
        )
    if start_date is not None:
        stmt = stmt.where(EmployeeBalanceTransaction.transaction_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(EmployeeBalanceTransaction.transaction_date <= end_date)

    result = await db.execute(stmt)
    return [_transaction_to_dict(row, name) for row, name in result.all()]


async def create_employee_balance_transaction(db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
    employee_id = int(payload["employee_id"])
    emp = await db.get(Employees, employee_id)
    if emp is None:
        raise ValueError(f"employee_id {employee_id} not found")

    transaction_date = _parse_date(payload.get("transaction_date"), "transaction_date")
    notes = payload.get("notes")
    source = (payload.get("source") or "manual").strip() or "manual"
    status = validate_transaction_status(str(payload.get("status") or "active"))

    tt, amount, currency, status, notes = validate_transaction_payload(
        str(payload.get("transaction_type", "")),
        _parse_amount(payload.get("amount")),
        str(payload.get("currency") or DEFAULT_CURRENCY),
        status,
        notes,
    )

    row = EmployeeBalanceTransaction(
        employee_id=employee_id,
        transaction_date=transaction_date,
        transaction_type=tt,
        amount=amount,
        currency=currency,
        status=status,
        notes=notes,
        source=source,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _transaction_to_dict(row, emp.name)


async def update_employee_balance_transaction(
    db: AsyncSession,
    transaction_id: int,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    row = await db.get(EmployeeBalanceTransaction, transaction_id)
    if row is None:
        raise ValueError(f"balance transaction {transaction_id} not found")

    transaction_date = row.transaction_date
    if payload.get("transaction_date") is not None:
        transaction_date = _parse_date(payload["transaction_date"], "transaction_date")

    transaction_type = row.transaction_type
    if payload.get("transaction_type") is not None:
        transaction_type = validate_transaction_type(str(payload["transaction_type"]))

    amount = float(row.amount)
    if payload.get("amount") is not None:
        amount = _parse_amount(payload["amount"])

    currency = row.currency
    if payload.get("currency") is not None:
        currency = str(payload["currency"]).strip().upper()
        if not currency:
            raise ValueError("currency must be non-empty")

    status = row.status
    if payload.get("status") is not None:
        status = validate_transaction_status(str(payload["status"]))

    notes = row.notes
    if "notes" in payload:
        notes = payload.get("notes")

    tt, amount, currency, status, notes = validate_transaction_payload(
        transaction_type, amount, currency, status, notes
    )

    row.transaction_date = transaction_date
    row.transaction_type = tt
    row.amount = amount
    row.currency = currency
    row.status = status
    row.notes = notes
    row.updated_at = datetime.now()

    await db.commit()
    emp = await db.get(Employees, row.employee_id)
    await db.refresh(row)
    return _transaction_to_dict(row, emp.name if emp else None)


async def cancel_employee_balance_transaction(db: AsyncSession, transaction_id: int) -> Dict[str, Any]:
    row = await db.get(EmployeeBalanceTransaction, transaction_id)
    if row is None:
        raise ValueError(f"balance transaction {transaction_id} not found")
    row.status = "cancelled"
    row.updated_at = datetime.now()
    await db.commit()
    emp = await db.get(Employees, row.employee_id)
    await db.refresh(row)
    return _transaction_to_dict(row, emp.name if emp else None)


async def delete_employee_balance_transaction(db: AsyncSession, transaction_id: int) -> None:
    row = await db.get(EmployeeBalanceTransaction, transaction_id)
    if row is None:
        raise ValueError(f"balance transaction {transaction_id} not found")
    await db.delete(row)
    await db.commit()


def _aggregate_row(employee_id: int, employee_name: str) -> Dict[str, Any]:
    return {
        "employee_id": employee_id,
        "employee_name": employee_name,
        "active_balance": 0.0,
        "advance_total": 0.0,
        "loan_total": 0.0,
        "retention_total": 0.0,
        "repayment_total": 0.0,
        "compensation_total": 0.0,
        "transaction_count": 0,
    }


async def get_employee_balance_summary(db: AsyncSession) -> Dict[str, Any]:
    """Summary per active employee — includes zero balances when no transactions."""
    emp_result = await db.execute(
        select(Employees).where(Employees.status == "active").order_by(Employees.name.asc())
    )
    employees = list(emp_result.scalars().all())

    tx_result = await db.execute(select(EmployeeBalanceTransaction))
    transactions = list(tx_result.scalars().all())

    by_employee: Dict[int, Dict[str, Any]] = {
        emp.id: _aggregate_row(emp.id, emp.name or f"Employee {emp.id}") for emp in employees
    }

    for tx in transactions:
        if tx.status == "cancelled":
            continue
        if tx.employee_id not in by_employee:
            continue

        row = by_employee[tx.employee_id]
        row["transaction_count"] += 1
        amount = float(tx.amount)
        signed = signed_amount(tx.transaction_type, amount)
        row["active_balance"] += signed

        if tx.transaction_type == "advance":
            row["advance_total"] += amount
        elif tx.transaction_type == "loan":
            row["loan_total"] += amount
        elif tx.transaction_type == "retention":
            row["retention_total"] += amount
        elif tx.transaction_type == "repayment":
            row["repayment_total"] += amount
        elif tx.transaction_type == "compensation":
            row["compensation_total"] += amount

    employees_summary = list(by_employee.values())
    totals = {
        "active_balance": sum(r["active_balance"] for r in employees_summary),
        "advance_total": sum(r["advance_total"] for r in employees_summary),
        "loan_total": sum(r["loan_total"] for r in employees_summary),
        "retention_total": sum(r["retention_total"] for r in employees_summary),
        "repayment_total": sum(r["repayment_total"] for r in employees_summary),
        "compensation_total": sum(r["compensation_total"] for r in employees_summary),
        "transaction_count": sum(r["transaction_count"] for r in employees_summary),
    }

    return {
        "currency": DEFAULT_CURRENCY,
        "totals": totals,
        "employees": employees_summary,
    }
