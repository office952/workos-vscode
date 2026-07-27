"""Employee lifecycle — hire / end dates, assignability, reassignment flags.

HR capacity & internal cost only. Never client tariff / Pricing Registry.
Never hard-delete employees; resignations set end_date + ended/inactive.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.company_calendar import company_workdays_in_month
from services.execution_plan_task_parser import operational_tasks_only
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

TERMINAL_STATUSES = frozenset({"inactive", "ended"})
ASSIGNABLE_STATUS = "active"


def to_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        raw = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(raw).date()
        except ValueError:
            try:
                return date.fromisoformat(raw[:10])
            except ValueError:
                return None
    return None


def employment_interval(emp: "Employees | dict") -> Tuple[Optional[date], Optional[date]]:
    if isinstance(emp, dict):
        start = to_date(emp.get("data_angajare") or emp.get("start_date"))
        end = to_date(emp.get("end_date"))
        status = emp.get("status")
    else:
        start = to_date(getattr(emp, "data_angajare", None))
        end = to_date(getattr(emp, "end_date", None))
        status = getattr(emp, "status", None)
    # Terminal without end_date: no capacity contribution until end_date is set
    # for a partial-month leaver. Historic row links stay; hours stay 0.
    if status in TERMINAL_STATUSES and end is None:
        end = date.min
    return start, end


def is_employed_on(emp: "Employees | dict", on_day: date) -> bool:
    start, end = employment_interval(emp)
    if start is not None and on_day < start:
        return False
    if end is not None and on_day > end:
        return False
    return True


def is_assignable(emp: "Employees | dict", on_day: Optional[date] = None) -> bool:
    """Future assignment eligibility — active + inside employment interval."""
    day = on_day or date.today()
    if isinstance(emp, dict):
        status = emp.get("status")
    else:
        status = emp.status
    if status != ASSIGNABLE_STATUS:
        return False
    return is_employed_on(emp, day)


def employment_workdays_in_month(
    emp: "Employees | dict",
    year: int,
    month: int,
) -> List[date]:
    start, end = employment_interval(emp)
    workdays = company_workdays_in_month(year, month)
    out: List[date] = []
    for day in workdays:
        if start is not None and day < start:
            continue
        if end is not None and day > end:
            continue
        out.append(day)
    return out


def _normalize_employee_id(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _reality_ended_lookup(raw: Optional[str]) -> Dict[str, bool]:
    import json

    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    if not isinstance(parsed, list):
        return {}
    out: Dict[str, bool] = {}
    for item in parsed:
        if not isinstance(item, dict) or not item.get("task_id"):
            continue
        out[str(item["task_id"])] = bool(item.get("ended_at"))
    return out


async def find_open_assignments_needing_reassignment(
    db: AsyncSession,
    *,
    on_day: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Flag open plan tasks whose assignee is no longer assignable after end_date."""
    day = on_day or date.today()
    plans = list(
        (
            await db.execute(select(ExecutionPlan).order_by(ExecutionPlan.id.desc()))
        ).scalars().all()
    )
    if not plans:
        return []

    # Latest plan per order_id
    latest_by_order: Dict[int, ExecutionPlan] = {}
    for plan in plans:
        if plan.order_id not in latest_by_order:
            latest_by_order[plan.order_id] = plan

    emp_ids: set[int] = set()
    plan_tasks: List[Tuple[ExecutionPlan, list]] = []
    for plan in latest_by_order.values():
        tasks = operational_tasks_only(plan.tasks_json)
        plan_tasks.append((plan, tasks))
        for entry in tasks:
            eid = _normalize_employee_id(entry.get("assigned_employee_id"))
            if eid is not None:
                emp_ids.add(eid)

    employees: Dict[int, Employees] = {}
    if emp_ids:
        rows = (
            await db.execute(select(Employees).where(Employees.id.in_(list(emp_ids))))
        ).scalars().all()
        employees = {e.id: e for e in rows}

    realities = (
        await db.execute(
            select(ExecutionReality).where(
                ExecutionReality.order_id.in_(list(latest_by_order.keys()))
            )
        )
    ).scalars().all() if latest_by_order else []
    reality_by_order = {r.order_id: r for r in realities}

    flags: List[Dict[str, Any]] = []
    for plan, tasks in plan_tasks:
        ended = _reality_ended_lookup(
            reality_by_order[plan.order_id].tasks_json
            if plan.order_id in reality_by_order
            else None
        )
        for entry in tasks:
            if not isinstance(entry, dict):
                continue
            task_id = str(entry.get("task_id") or "")
            if not task_id or ended.get(task_id):
                continue
            eid = _normalize_employee_id(entry.get("assigned_employee_id"))
            if eid is None:
                continue
            emp = employees.get(eid)
            if emp is None:
                flags.append(
                    {
                        "order_id": plan.order_id,
                        "order_code": plan.order_code,
                        "plan_id": plan.id,
                        "task_id": task_id,
                        "assigned_employee_id": eid,
                        "assigned_employee_name": entry.get("assigned_employee_name"),
                        "needs_reassignment": True,
                        "reason": "employee_missing",
                    }
                )
                continue
            if is_assignable(emp, day):
                continue
            start, end = employment_interval(emp)
            reason = "employee_not_active"
            if end is not None and day > end:
                reason = "employee_past_end_date"
            elif emp.status in TERMINAL_STATUSES:
                reason = "employee_ended"
            flags.append(
                {
                    "order_id": plan.order_id,
                    "order_code": plan.order_code,
                    "plan_id": plan.id,
                    "task_id": task_id,
                    "assigned_employee_id": eid,
                    "assigned_employee_name": emp.name,
                    "employee_status": emp.status,
                    "end_date": end.isoformat() if end else None,
                    "start_date": start.isoformat() if start else None,
                    "needs_reassignment": True,
                    "reason": reason,
                }
            )
    return flags


async def build_capacity_read_model(
    db: AsyncSession,
    employees: Sequence[Employees],
    *,
    year: int,
    month: int,
    hours_by_id: Dict[int, float],
) -> List[Dict[str, Any]]:
    """Current-month capacity rows — effective-date based, not client pricing."""
    today = date.today()
    rows: List[Dict[str, Any]] = []
    for emp in employees:
        start, end = employment_interval(emp)
        workdays = employment_workdays_in_month(emp, year, month)
        rows.append(
            {
                "employee_id": emp.id,
                "name": emp.name,
                "status": emp.status,
                "employee_type": emp.employee_type,
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "is_assignable": is_assignable(emp, today),
                "employed_workdays_in_month": len(workdays),
                "ore_productive_luna": float(hours_by_id.get(emp.id, 0.0)),
                "source": "company_calendar_minus_approved_leave_clipped_employment",
            }
        )
    return rows
