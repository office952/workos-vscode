"""Employees service — thin CRUD + derived helpers for CostEngine inputs.

No cost formula that belongs to CostEngine lives here. The only derived
value we expose is `cost_ora_calculat`, which is an algebraic identity on
a single row (`cost_lunar_firma / ore_productive_luna`), not a company-wide
aggregate. Monthly productive hours are calculated by
`services.employee_productive_hours` (Company Calendar − approved leave,
clipped to employment interval). Company-wide aggregates live in
`services.cost_engine_config.CostEngineConfigService.compute_base_config`.

Lifecycle: never hard-delete. Resignations → end_date + ended/inactive.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models.employees import Employees
from services.employee_lifecycle import (
    TERMINAL_STATUSES,
    employment_workdays_in_month,
    is_assignable,
    to_date,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


VALID_STATUSES = {"active", "on_leave", "sick", "training", "inactive", "ended"}
VALID_TYPES = {"productive", "indirect", "administrative", "management"}


def compute_cost_ora_calculat(cost_lunar_firma: Optional[float], ore_productive_luna: Optional[float]) -> Optional[float]:
    """Per-row derived value. None if inputs insufficient — no silent fallback."""
    if cost_lunar_firma is None or ore_productive_luna is None:
        return None
    try:
        hours = float(ore_productive_luna)
        cost = float(cost_lunar_firma)
    except (TypeError, ValueError):
        return None
    if hours <= 0:
        return None
    return round(cost / hours, 4)


def is_valid_for_cost_engine(row: "Employees | dict") -> bool:
    """Productive contributors need cost_lunar_firma > 0.

    Productive hours come from Company Calendar − approved leave
    (`employee_productive_hours`), clipped to employment dates;
    stored `ore_productive_luna` is not required.
    Non-assignable / terminal employees are never CostEngine blockers.
    """
    if isinstance(row, dict):
        emp_type = row.get("employee_type")
        status = row.get("status")
        cost = row.get("cost_lunar_firma")
    else:
        emp_type = row.employee_type
        status = row.status
        cost = row.cost_lunar_firma

    if emp_type != "productive":
        return True  # non-productive employees are never a blocker for labour-rate calc
    if status in TERMINAL_STATUSES or status != "active":
        return True  # only ACTIVE productive employees need to be valid
    if cost is None:
        return False
    try:
        if float(cost) <= 0:
            return False
    except (TypeError, ValueError):
        return False
    return True


def _normalize_list_field(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return json.dumps(list(value), ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)


def _sanitize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    clean = dict(data)
    if "skills" in clean:
        clean["skills"] = _normalize_list_field(clean["skills"])
    if "machines" in clean:
        clean["machines"] = _normalize_list_field(clean["machines"])
    if "status" in clean and clean["status"] is not None and clean["status"] not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{clean['status']}'. Allowed: {sorted(VALID_STATUSES)}")
    if "employee_type" in clean and clean["employee_type"] is not None and clean["employee_type"] not in VALID_TYPES:
        raise ValueError(f"Invalid employee_type '{clean['employee_type']}'. Allowed: {sorted(VALID_TYPES)}")
    if "monthly_internal_pay_amount" in clean and clean["monthly_internal_pay_amount"] is not None:
        try:
            pay = float(clean["monthly_internal_pay_amount"])
        except (TypeError, ValueError):
            raise ValueError("monthly_internal_pay_amount must be a number")
        if pay < 0:
            raise ValueError("monthly_internal_pay_amount must be >= 0")
        clean["monthly_internal_pay_amount"] = pay
    start = to_date(clean.get("data_angajare")) if "data_angajare" in clean else None
    end = to_date(clean.get("end_date")) if "end_date" in clean else None
    if start is not None and end is not None and end < start:
        raise ValueError("end_date must be on or after data_angajare (start_date)")
    # Resignations: setting end_date without terminal status → mark ended
    if end is not None and clean.get("status") is None:
        pass
    if clean.get("status") in TERMINAL_STATUSES and clean.get("end_date") is None and "end_date" in clean:
        # explicit null end_date with terminal status is allowed (capacity helper infers)
        pass
    return clean


class EmployeesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Employees:
        payload = _sanitize_payload(data)
        if not payload.get("status"):
            payload["status"] = "active"
        obj = Employees(**payload)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_by_id(self, obj_id: int) -> Optional[Employees]:
        result = await self.db.execute(select(Employees).where(Employees.id == obj_id))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        skip: int = 0,
        limit: int = 500,
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        q = select(Employees)
        cq = select(func.count(Employees.id))
        if query_dict:
            for field, value in query_dict.items():
                if hasattr(Employees, field):
                    q = q.where(getattr(Employees, field) == value)
                    cq = cq.where(getattr(Employees, field) == value)
        total = (await self.db.execute(cq)).scalar()

        if sort:
            desc = sort.startswith("-")
            field_name = sort[1:] if desc else sort
            if hasattr(Employees, field_name):
                col = getattr(Employees, field_name)
                q = q.order_by(col.desc() if desc else col)
        else:
            q = q.order_by(Employees.id.asc())

        result = await self.db.execute(q.offset(skip).limit(limit))
        items = result.scalars().all()
        return {"items": items, "total": total, "skip": skip, "limit": limit}

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> Optional[Employees]:
        obj = await self.get_by_id(obj_id)
        if not obj:
            return None
        payload = _sanitize_payload(update_data)
        # When setting terminal status without end_date, stamp end_date now.
        new_status = payload.get("status")
        if new_status in TERMINAL_STATUSES and payload.get("end_date") is None and obj.end_date is None:
            payload["end_date"] = datetime.now(timezone.utc)
        for k, v in payload.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        start = to_date(obj.data_angajare)
        end = to_date(obj.end_date)
        if start is not None and end is not None and end < start:
            raise ValueError("end_date must be on or after data_angajare (start_date)")
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def end_employment(
        self,
        obj_id: int,
        *,
        end_date: Optional[datetime] = None,
        status: str = "ended",
    ) -> Optional[Employees]:
        """Soft-end: set end_date + terminal status. Never hard-delete."""
        if status not in TERMINAL_STATUSES:
            raise ValueError(f"end status must be one of {sorted(TERMINAL_STATUSES)}")
        obj = await self.get_by_id(obj_id)
        if not obj:
            return None
        obj.status = status
        obj.end_date = end_date or datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj_id: int) -> bool:
        """Deprecated hard path — soft-ends instead (Owner: never hard-delete)."""
        obj = await self.end_employment(obj_id, status="ended")
        return obj is not None

    async def get_active_productive(self) -> List[Employees]:
        """ACTIVE PRODUCTIVE employees still inside employment interval today.

        Used for assignment-adjacent lists. CostEngine month aggregation uses
        `get_productive_contributors_for_month` (effective-date based).
        """
        result = await self.db.execute(
            select(Employees).where(
                Employees.employee_type == "productive",
                Employees.status == "active",
            )
        )
        today = datetime.now(timezone.utc).date()
        return [e for e in result.scalars().all() if is_assignable(e, today)]

    async def get_productive_contributors_for_month(
        self, year: int, month: int
    ) -> List[Employees]:
        """Productive employees with ≥1 employment workday in the target month."""
        result = await self.db.execute(
            select(Employees).where(Employees.employee_type == "productive")
        )
        out: List[Employees] = []
        for emp in result.scalars().all():
            if employment_workdays_in_month(emp, year, month):
                out.append(emp)
        return out
