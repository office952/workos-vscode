"""Create/cancel internal employee payment records — no side effects on payroll/balances."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

from models.employee_payment_record import EmployeePaymentRecord
from models.employees import Employees
from sqlalchemy.ext.asyncio import AsyncSession

VALID_SLOTS = frozenset({"15", "30"})
RECORD_STATUSES = frozenset({"draft", "confirmed", "cancelled"})


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
        raise ValueError("amount_paid must be a number")
    if amount <= 0:
        raise ValueError("amount_paid must be greater than 0")
    return round(amount, 2)


def _record_to_dict(row: EmployeePaymentRecord, employee_name: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": row.id,
        "employee_id": row.employee_id,
        "employee_name": employee_name,
        "year": row.year,
        "month": row.month,
        "slot": row.slot,
        "amount_paid": float(row.amount_paid),
        "payment_date": row.payment_date.isoformat(),
        "status": row.status,
        "notes": row.notes,
        "source": row.source,
        "cancelled_at": row.cancelled_at,
        "cancelled_reason": row.cancelled_reason,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


async def create_employee_payment_record(db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
    employee_id = int(payload["employee_id"])
    emp = await db.get(Employees, employee_id)
    if emp is None:
        raise ValueError(f"employee_id {employee_id} not found")

    profile_salary = emp.cost_lunar_firma
    if profile_salary is None or float(profile_salary) <= 0:
        raise ValueError(
            "employee profile salary (cost_lunar_firma) is required to record payments"
        )

    year = int(payload["year"])
    month = int(payload["month"])
    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")

    slot = str(payload.get("slot", "")).strip()
    if slot not in VALID_SLOTS:
        raise ValueError("slot must be 15 or 30")

    amount_paid = _parse_amount(payload.get("amount_paid"))
    payment_date = _parse_date(payload.get("payment_date"), "payment_date")
    notes = payload.get("notes")
    source = (payload.get("source") or "manual").strip() or "manual"
    status = (payload.get("status") or "confirmed").strip().lower()
    if status not in RECORD_STATUSES:
        raise ValueError("status must be draft, confirmed, or cancelled")

    row = EmployeePaymentRecord(
        employee_id=employee_id,
        year=year,
        month=month,
        slot=slot,
        amount_paid=amount_paid,
        payment_date=payment_date,
        status=status,
        notes=notes,
        source=source,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _record_to_dict(row, emp.name)


async def cancel_employee_payment_record(
    db: AsyncSession,
    record_id: int,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    row = await db.get(EmployeePaymentRecord, record_id)
    if row is None:
        raise ValueError(f"payment record {record_id} not found")
    if row.status == "cancelled":
        return _record_to_dict(row, None)

    row.status = "cancelled"
    row.cancelled_at = datetime.now()
    row.cancelled_reason = (reason or "").strip() or None
    row.updated_at = datetime.now()
    await db.commit()
    emp = await db.get(Employees, row.employee_id)
    await db.refresh(row)
    return _record_to_dict(row, emp.name if emp else None)
