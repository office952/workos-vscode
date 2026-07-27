"""Employees service — thin CRUD + derived helpers for CostEngine inputs.

No cost formula that belongs to CostEngine lives here. The only derived
value we expose is `cost_ora_calculat`, which is an algebraic identity on
a single row (`cost_lunar_firma / ore_productive_luna`), not a company-wide
aggregate. Monthly productive hours are calculated by
`services.employee_productive_hours` (Company Calendar − approved leave).
Company-wide aggregates live in
`services.cost_engine_config.CostEngineConfigService.compute_base_config`.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from models.employees import Employees
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


VALID_STATUSES = {"active", "on_leave", "sick", "training", "inactive"}
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
    """Active productive employees need cost_lunar_firma > 0.

    Productive hours come from Company Calendar − approved leave
    (`employee_productive_hours`); stored `ore_productive_luna` is not required.
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
    if status != "active":
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
    return clean


class EmployeesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Employees:
        payload = _sanitize_payload(data)
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
        for k, v in payload.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj_id: int) -> bool:
        obj = await self.get_by_id(obj_id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True

    async def get_active_productive(self) -> List[Employees]:
        """Return ACTIVE PRODUCTIVE employees — the only ones eligible for
        contributing to the average labour hour cost."""
        result = await self.db.execute(
            select(Employees).where(
                Employees.employee_type == "productive",
                Employees.status == "active",
            )
        )
        return list(result.scalars().all())