"""Read-only employee payment situation for tranșe 15/30 — not fiscal payroll."""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from models.employee_payment_record import EmployeePaymentRecord
from models.employees import Employees
from services.employee_attendance_service import get_attendance_month_summary
from services.employee_balance_service import get_employee_balance_summary
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

VALID_SLOTS = frozenset({"15", "30"})
PAYMENT_STATUSES_ACTIVE = frozenset({"confirmed", "draft"})


def _month_bounds(year: int, month: int) -> Tuple[date, date]:
    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _slot_period(year: int, month: int, slot: str) -> Tuple[date, date]:
    month_start, month_end = _month_bounds(year, month)
    if slot == "15":
        return month_start, date(year, month, min(15, month_end.day))
    if slot == "30":
        start_day = min(16, month_end.day)
        return date(year, month, start_day), month_end
    raise ValueError("slot must be 15 or 30")


def _round_amount(value: float) -> float:
    return round(float(value), 2)


def _slot_status(expected: float, paid: float, missing_base: bool) -> str:
    if missing_base:
        return "missing_base"
    if expected <= 0:
        return "unpaid"
    remaining = max(0.0, expected - paid)
    if remaining <= 0:
        return "paid"
    if paid > 0:
        return "partial"
    return "unpaid"


def _attendance_label(att_row: Optional[Dict[str, Any]]) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    if att_row is None:
        return "Lipsă pontaj", ["attendance_summary_unavailable"]
    planned = int(att_row.get("planned_event_count") or 0)
    present = int(att_row.get("present_days") or 0)
    standard = int(att_row.get("standard_work_days") or 0)
    if planned > 0:
        warnings.append("attendance_planned_events")
        return "Incomplet — evenimente planificate", warnings
    if present < standard:
        warnings.append("attendance_incomplete")
        return f"Incomplet — {standard - present} zile", warnings
    return f"OK — {present}/{standard} zile", warnings


def _advances_label(balance_row: Optional[Dict[str, Any]]) -> Tuple[str, float, List[str]]:
    if balance_row is None:
        return "Sold 0 RON", 0.0, []
    active_balance = float(balance_row.get("active_balance") or 0)
    count = int(balance_row.get("transaction_count") or 0)
    if count == 0 or active_balance <= 0:
        return "Sold 0 RON", 0.0, []
    return f"Sold activ {_round_amount(active_balance)} RON ({count} poz.)", active_balance, []


def _record_to_history(row: EmployeePaymentRecord) -> Dict[str, Any]:
    return {
        "id": row.id,
        "amount_paid": _round_amount(row.amount_paid),
        "payment_date": row.payment_date.isoformat(),
        "status": row.status,
        "notes": row.notes,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "cancelled": row.status == "cancelled",
    }


async def get_employee_payment_situation(db: AsyncSession, year: int, month: int) -> Dict[str, Any]:
    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")

    attendance_summary = await get_attendance_month_summary(db, year, month)
    attendance_by_id = {
        row["employee_id"]: row for row in attendance_summary.get("employees", [])
    }

    balance_summary = await get_employee_balance_summary(db)
    balance_by_id = {
        row["employee_id"]: row for row in balance_summary.get("employees", [])
    }

    payments_result = await db.execute(
        select(EmployeePaymentRecord).where(
            EmployeePaymentRecord.year == year,
            EmployeePaymentRecord.month == month,
        )
    )
    all_payments = list(payments_result.scalars().all())
    payments_by_employee_slot: Dict[Tuple[int, str], List[EmployeePaymentRecord]] = {}
    for p in all_payments:
        payments_by_employee_slot.setdefault((p.employee_id, p.slot), []).append(p)

    employees_result = await db.execute(
        select(Employees).where(Employees.status == "active").order_by(Employees.name.asc())
    )
    employees = list(employees_result.scalars().all())

    employee_rows: List[Dict[str, Any]] = []
    summary_expected = 0.0
    summary_paid = 0.0
    unpaid_count = 0
    partial_count = 0
    paid_count = 0

    for emp in employees:
        salary_monthly = emp.cost_lunar_firma
        missing_base = salary_monthly is None or float(salary_monthly) <= 0
        currency = emp.salary_currency or "RON"
        warnings: List[str] = []
        if missing_base:
            warnings.append("missing_profile_salary")

        att_label, att_warnings = _attendance_label(attendance_by_id.get(emp.id))
        warnings.extend(att_warnings)

        adv_label, suggested_deduction, adv_warnings = _advances_label(balance_by_id.get(emp.id))
        if suggested_deduction > 0:
            warnings.append("advances_suggested_deduction_info_only")

        slots: Dict[str, Any] = {}
        monthly_expected = 0.0
        monthly_paid = 0.0

        for slot in ("15", "30"):
            period_start, period_end = _slot_period(year, month, slot)
            expected = 0.0
            if not missing_base:
                expected = _round_amount(float(salary_monthly) / 2.0)

            slot_payments = payments_by_employee_slot.get((emp.id, slot), [])
            paid = _round_amount(
                sum(
                    float(p.amount_paid)
                    for p in slot_payments
                    if p.status in PAYMENT_STATUSES_ACTIVE
                )
            )
            remaining = _round_amount(max(0.0, expected - paid))
            status = _slot_status(expected, paid, missing_base)

            history = sorted(
                [_record_to_history(p) for p in slot_payments],
                key=lambda h: (h["payment_date"], h["id"]),
                reverse=True,
            )

            slot_warnings = list(warnings)
            if not missing_base and att_warnings:
                slot_warnings.append("attendance_adjustment_deferred")

            slots[slot] = {
                "slot": slot,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "expected_amount": expected,
                "paid_amount": paid,
                "remaining_amount": remaining,
                "status": status,
                "breakdown": {
                    "base_amount": expected,
                    "attendance_adjustment": 0.0,
                    "overtime_amount": 0.0,
                    "advances_debts_deduction": 0.0,
                    "existing_payments": paid,
                    "suggested_deduction": _round_amount(suggested_deduction) if suggested_deduction > 0 else 0.0,
                },
                "warnings": slot_warnings,
                "history": history,
            }

            monthly_expected += expected
            monthly_paid += paid

            if not missing_base and expected > 0:
                if status == "unpaid":
                    unpaid_count += 1
                elif status == "partial":
                    partial_count += 1
                elif status == "paid":
                    paid_count += 1

        monthly_remaining = _round_amount(max(0.0, monthly_expected - monthly_paid))
        summary_expected += monthly_expected
        summary_paid += monthly_paid

        employee_rows.append(
            {
                "employee_id": emp.id,
                "employee_name": emp.name,
                "salary_monthly": float(salary_monthly) if not missing_base else None,
                "salary_amount": float(salary_monthly) if not missing_base else None,
                "monthly_internal_pay_amount": emp.monthly_internal_pay_amount,
                "currency": currency,
                "base_source": "employee_profile_salary",
                "warnings": warnings,
                "attendance_label": att_label,
                "advances_debts_label": adv_label,
                "monthly_expected_amount": _round_amount(monthly_expected),
                "monthly_paid_amount": _round_amount(monthly_paid),
                "monthly_remaining_amount": monthly_remaining,
                "missing_pay_base": missing_base,
                "slots": slots,
            }
        )

    summary_remaining = _round_amount(max(0.0, summary_expected - summary_paid))

    return {
        "year": year,
        "month": month,
        "currency": balance_summary.get("currency", "RON"),
        "summary": {
            "expected_total": _round_amount(summary_expected),
            "paid_total": _round_amount(summary_paid),
            "remaining_total": summary_remaining,
            "unpaid_count": unpaid_count,
            "partial_count": partial_count,
            "paid_count": paid_count,
        },
        "employees": employee_rows,
    }
