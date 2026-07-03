"""
DivergenceService — WorkOS Execution Layer v1.

READ-ONLY. NEVER MUTATES ANYTHING.

Canonical rules:
  - No `.commit()`, no `.add(...)`, no `.update(...)`, no `insert(...)`,
    no `delete(...)`.
  - Compares three independent artifacts:
       Order (the "sold" / locked truth)         ← orders table
       ExecutionPlan (the "planned" / estimated) ← execution_plan table
       ExecutionReality (the "actual")           ← execution_reality table
  - Returns a plain DTO. Callers do whatever they want with it.
  - Missing pieces are reported explicitly, never masked.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from services.execution_plan_task_parser import parse_tasks_json_raw


@dataclass
class DivergenceReport:
    order_id: int
    order_code: str
    has_order: bool
    has_plan: bool
    has_reality: bool

    sold_total_amount: Optional[float] = None

    plan_total_estimated_minutes: Optional[float] = None
    reality_total_actual_minutes: Optional[float] = None

    delta_estimated_vs_actual_minutes: Optional[float] = None
    per_task: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "order_code": self.order_code,
            "has_order": self.has_order,
            "has_plan": self.has_plan,
            "has_reality": self.has_reality,
            "sold_total_amount": self.sold_total_amount,
            "plan_total_estimated_minutes": self.plan_total_estimated_minutes,
            "reality_total_actual_minutes": self.reality_total_actual_minutes,
            "delta_estimated_vs_actual_minutes": self.delta_estimated_vs_actual_minutes,
            "per_task": list(self.per_task),
            "notes": list(self.notes),
        }


class DivergenceService:
    """Compares Order / Plan / Reality. READ ONLY."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _load_order(self, order_id: int) -> Optional[Orders]:
        stmt = select(Orders).where(Orders.id == order_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def _load_plan(self, order_id: int) -> Optional[ExecutionPlan]:
        stmt = select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        res = await self.db.execute(stmt)
        # If multiple rows ever exist (future revisions), pick the newest id.
        rows = list(res.scalars().all())
        if not rows:
            return None
        return sorted(rows, key=lambda r: r.id)[-1]

    async def _load_reality(self, order_id: int) -> Optional[ExecutionReality]:
        stmt = select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    def _parse_plan_tasks(plan: ExecutionPlan) -> List[Dict[str, Any]]:
        if plan.tasks_json is None or plan.tasks_json == "":
            return []
        parsed = parse_tasks_json_raw(plan.tasks_json)
        return list(parsed.operational_tasks)

    @staticmethod
    def _parse_reality_tasks(reality: ExecutionReality) -> List[Dict[str, Any]]:
        if reality.tasks_json is None or reality.tasks_json == "":
            return []
        try:
            data = json.loads(reality.tasks_json)
        except (TypeError, ValueError):
            return []
        if not isinstance(data, list):
            return []
        return [t for t in data if isinstance(t, dict)]

    async def compare(self, order_id: int) -> DivergenceReport:
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError("order_id_invalid")

        order = await self._load_order(order_id)
        plan = await self._load_plan(order_id)
        reality = await self._load_reality(order_id)

        report = DivergenceReport(
            order_id=order_id,
            order_code=order.code if order is not None else "",
            has_order=order is not None,
            has_plan=plan is not None,
            has_reality=reality is not None,
        )

        if order is None:
            report.notes.append("order_not_found")
        else:
            if order.total_amount is None:
                report.notes.append("order_total_amount_missing")
            else:
                report.sold_total_amount = float(order.total_amount)

        if plan is None:
            report.notes.append("plan_not_generated")
        else:
            report.plan_total_estimated_minutes = float(plan.total_estimated_time_minutes)

        if reality is None:
            report.notes.append("reality_not_recorded")
        else:
            report.reality_total_actual_minutes = float(reality.total_actual_time_minutes)

        if (
            report.plan_total_estimated_minutes is not None
            and report.reality_total_actual_minutes is not None
        ):
            report.delta_estimated_vs_actual_minutes = round(
                report.reality_total_actual_minutes - report.plan_total_estimated_minutes,
                2,
            )

        if plan is not None and reality is not None:
            plan_tasks = self._parse_plan_tasks(plan)
            reality_tasks = self._parse_reality_tasks(reality)
            reality_by_id: Dict[str, Dict[str, Any]] = {}
            for rt in reality_tasks:
                tid = rt.get("task_id")
                if not isinstance(tid, str):
                    continue
                # If a task_id repeats in reality, sum durations.
                reality_by_id.setdefault(tid, {"actual_minutes": 0.0})
                try:
                    from datetime import datetime

                    s_raw = rt.get("started_at")
                    e_raw = rt.get("ended_at")
                    if s_raw and e_raw:
                        s = datetime.fromisoformat(str(s_raw).replace("Z", "+00:00"))
                        e = datetime.fromisoformat(str(e_raw).replace("Z", "+00:00"))
                        delta = (e - s).total_seconds() / 60.0
                        if delta > 0:
                            reality_by_id[tid]["actual_minutes"] += delta
                except ValueError:
                    continue

            per_task: List[Dict[str, Any]] = []
            for pt in plan_tasks:
                tid = pt.get("task_id")
                est = pt.get("estimated_time_minutes")
                try:
                    est_f = float(est) if est is not None else None
                except (TypeError, ValueError):
                    est_f = None
                actual_minutes = None
                if isinstance(tid, str) and tid in reality_by_id:
                    actual_minutes = round(reality_by_id[tid]["actual_minutes"], 2)
                delta = None
                if est_f is not None and actual_minutes is not None:
                    delta = round(actual_minutes - est_f, 2)
                per_task.append(
                    {
                        "task_id": tid,
                        "name": pt.get("name"),
                        "estimated_minutes": est_f,
                        "actual_minutes": actual_minutes,
                        "delta_minutes": delta,
                    }
                )
            # Tasks recorded in reality but not in plan are reported as orphans.
            plan_ids = {
                pt.get("task_id") for pt in plan_tasks if isinstance(pt.get("task_id"), str)
            }
            for tid, rv in reality_by_id.items():
                if tid in plan_ids:
                    continue
                per_task.append(
                    {
                        "task_id": tid,
                        "name": None,
                        "estimated_minutes": None,
                        "actual_minutes": round(rv["actual_minutes"], 2),
                        "delta_minutes": None,
                        "orphan": True,
                    }
                )
            report.per_task = per_task

        return report