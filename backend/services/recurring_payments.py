"""Recurring payments service — CRUD + overhead selector.

Only `status='active'` rows with `include_in_overhead=True` contribute to
`monthly_overhead_cost`. Annual payments are normalized to monthly
(`amount / 12`). Anything else is ignored for the overhead calculation —
this is intentional and must NOT be silently overridden by UI."""
import logging
from typing import Any, Dict, List, Optional

from models.recurring_payments import RecurringPayments
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


VALID_CATEGORIES = {
    "chirie", "utilitati", "leasing", "asigurare", "abonament",
    "servicii", "salarii_indirecte", "alte_costuri",
}
VALID_PERIODICITIES = {"lunar", "anual"}
VALID_STATUSES = {"active", "inactive"}


def monthly_equivalent(row: "RecurringPayments | dict") -> float:
    """Return the monthly-equivalent amount for a payment row.
    Returns 0.0 if the row has no amount or an unsupported periodicity."""
    if isinstance(row, dict):
        amount = row.get("amount")
        periodicity = row.get("periodicity", "lunar")
    else:
        amount = row.amount
        periodicity = row.periodicity

    if amount is None:
        return 0.0
    try:
        amt = float(amount)
    except (TypeError, ValueError):
        return 0.0

    if periodicity == "lunar":
        return amt
    if periodicity == "anual":
        return amt / 12.0
    return 0.0


def _sanitize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    clean = dict(data)
    if "category" in clean and clean["category"] is not None and clean["category"] not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category '{clean['category']}'. Allowed: {sorted(VALID_CATEGORIES)}")
    if "periodicity" in clean and clean["periodicity"] is not None and clean["periodicity"] not in VALID_PERIODICITIES:
        raise ValueError(f"Invalid periodicity '{clean['periodicity']}'. Allowed: {sorted(VALID_PERIODICITIES)}")
    if "status" in clean and clean["status"] is not None and clean["status"] not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{clean['status']}'. Allowed: {sorted(VALID_STATUSES)}")
    return clean


class RecurringPaymentsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> RecurringPayments:
        payload = _sanitize_payload(data)
        obj = RecurringPayments(**payload)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_by_id(self, obj_id: int) -> Optional[RecurringPayments]:
        result = await self.db.execute(select(RecurringPayments).where(RecurringPayments.id == obj_id))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        skip: int = 0,
        limit: int = 500,
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        q = select(RecurringPayments)
        cq = select(func.count(RecurringPayments.id))
        if query_dict:
            for field, value in query_dict.items():
                if hasattr(RecurringPayments, field):
                    q = q.where(getattr(RecurringPayments, field) == value)
                    cq = cq.where(getattr(RecurringPayments, field) == value)
        total = (await self.db.execute(cq)).scalar()

        if sort:
            desc = sort.startswith("-")
            field_name = sort[1:] if desc else sort
            if hasattr(RecurringPayments, field_name):
                col = getattr(RecurringPayments, field_name)
                q = q.order_by(col.desc() if desc else col)
        else:
            q = q.order_by(RecurringPayments.id.asc())

        result = await self.db.execute(q.offset(skip).limit(limit))
        items = result.scalars().all()
        return {"items": items, "total": total, "skip": skip, "limit": limit}

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> Optional[RecurringPayments]:
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

    async def get_overhead_contributors(self) -> List[RecurringPayments]:
        """Active payments flagged as overhead contributors.

        A payment linked to a specific machine AND flagged as machine-cost
        should NOT also be counted here — the canonical rule forbids
        double-counting leasing/utility tied to a specific machine under
        general overhead."""
        result = await self.db.execute(
            select(RecurringPayments).where(
                RecurringPayments.status == "active",
                RecurringPayments.include_in_overhead.is_(True),
            )
        )
        rows = list(result.scalars().all())
        filtered: List[RecurringPayments] = []
        for r in rows:
            if r.linked_machine_id and r.include_in_machine_cost:
                # Skip — will be consumed by per-machine cost in a later iteration.
                continue
            filtered.append(r)
        return filtered