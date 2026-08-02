"""Profitability Actual Read Model V1 — honest composition of frozen + actual truths.

READ-ONLY. Never invents labor money. Missing ≠ 0.
Does not mutate Order, Plan, Reality, Inventory, HR, or Pricing.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.orders import Orders
from schemas.order_snapshot_v2 import OrderSnapshotV2
from services.controlled_task_session_service import build_execution_actuals_read_model


REASON_PLANNING_MINUTES_MISSING = "planning_minutes_source_missing"
REASON_ACTUAL_MATERIAL_COST_MISSING = "actual_material_cost_missing"
REASON_EMPLOYEE_COST_POLICY_MISSING = "employee_cost_policy_missing"
REASON_JOB_NOT_CLOSED = "job_not_closed"
REASON_ACTUAL_TASK_COVERAGE_INCOMPLETE = "actual_task_coverage_incomplete"
REASON_ACCEPTED_COMMERCIAL_MISSING = "accepted_commercial_snapshot_missing"
REASON_ESTIMATED_INTERNAL_INCOMPLETE = "estimated_internal_cost_incomplete"
REASON_ACTUAL_TOTAL_COST_INCOMPLETE = "actual_total_cost_incomplete"

PROVENANCE = "profitability_actual_read_model_v1"


class OrderNotFoundError(LookupError):
    pass


def _unavailable(reason: str) -> dict[str, Any]:
    return {"value": None, "available": False, "reason": reason}


def _available(value: Any, *, provenance: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"value": value, "available": True, "reason": None}
    if provenance:
        out["provenance"] = provenance
    return out


class ProfitabilityActualReadModelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _load_order(self, order_id: int) -> Orders:
        row = (
            await self.db.execute(select(Orders).where(Orders.id == order_id))
        ).scalar_one_or_none()
        if row is None:
            raise OrderNotFoundError(str(order_id))
        return row

    @staticmethod
    def _parse_snapshot_dict(order: Orders) -> dict[str, Any] | None:
        """Extract frozen commercial/EIC fields without requiring full schema validate."""
        raw = getattr(order, "snapshot_v2_json", None)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return None
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        # Prefer full validate when possible (provenance), else dict extract.
        try:
            snap = OrderSnapshotV2.model_validate(data)
            return {
                "accepted_commercial_total": snap.accepted_commercial_total,
                "accepted_currency": snap.accepted_currency,
                "estimated_internal_total": snap.estimated_internal_total,
                "estimated_internal_cost_snapshot": (
                    snap.estimated_internal_cost_snapshot.model_dump()
                    if snap.estimated_internal_cost_snapshot is not None
                    else None
                ),
                "validated": True,
            }
        except (TypeError, ValueError):
            if data.get("accepted_commercial_total") is None:
                return None
            eic = data.get("estimated_internal_cost_snapshot")
            return {
                "accepted_commercial_total": data.get("accepted_commercial_total"),
                "accepted_currency": data.get("accepted_currency"),
                "estimated_internal_total": data.get("estimated_internal_total"),
                "estimated_internal_cost_snapshot": eic if isinstance(eic, dict) else None,
                "validated": False,
            }

    async def build(self, order_id: int) -> dict[str, Any]:
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError("order_id_invalid")

        order = await self._load_order(order_id)
        snapshot = self._parse_snapshot_dict(order)
        unavailable_reasons: list[str] = []

        # --- Commercial truth (frozen only) ---
        if snapshot is not None:
            commercial = {
                "accepted_revenue": _available(
                    float(snapshot["accepted_commercial_total"]),
                    provenance="order_snapshot_v2.accepted_commercial_total",
                ),
                "currency": _available(
                    snapshot.get("accepted_currency"),
                    provenance="order_snapshot_v2.accepted_currency",
                ),
                "snapshot_present": True,
                "revenue_source": "order_snapshot_v2",
            }
        else:
            unavailable_reasons.append(REASON_ACCEPTED_COMMERCIAL_MISSING)
            commercial = {
                "accepted_revenue": _unavailable(REASON_ACCEPTED_COMMERCIAL_MISSING),
                "currency": _unavailable(REASON_ACCEPTED_COMMERCIAL_MISSING),
                "snapshot_present": False,
                "revenue_source": "missing",
            }

        # --- Estimated internal ---
        est_total = snapshot.get("estimated_internal_total") if snapshot else None
        eic_snap = (
            snapshot.get("estimated_internal_cost_snapshot") if snapshot else None
        )
        if est_total is None:
            unavailable_reasons.append(REASON_ESTIMATED_INTERNAL_INCOMPLETE)
            estimated = {
                "estimated_total_cost": _unavailable(REASON_ESTIMATED_INTERNAL_INCOMPLETE),
                "estimated_material_cost": _unavailable(REASON_ESTIMATED_INTERNAL_INCOMPLETE),
                "estimated_operation_cost": _unavailable(REASON_ESTIMATED_INTERNAL_INCOMPLETE),
                "snapshot": eic_snap,
                "completeness": "incomplete",
                "provenance": "order_snapshot_v2.estimated_internal_cost_snapshot"
                if eic_snap
                else None,
            }
        else:
            mat = eic_snap.get("estimated_material_cost") if eic_snap else None
            op = eic_snap.get("estimated_operation_cost") if eic_snap else None
            estimated = {
                "estimated_total_cost": _available(
                    float(est_total),
                    provenance="order_snapshot_v2.estimated_internal_total",
                ),
                "estimated_material_cost": (
                    _available(mat, provenance="eic.estimated_material_cost")
                    if mat is not None
                    else _unavailable(REASON_ESTIMATED_INTERNAL_INCOMPLETE)
                ),
                "estimated_operation_cost": (
                    _available(op, provenance="eic.estimated_operation_cost")
                    if op is not None
                    else _unavailable(REASON_ESTIMATED_INTERNAL_INCOMPLETE)
                ),
                "snapshot": eic_snap,
                "completeness": "present",
                "provenance": "order_snapshot_v2",
            }

        # --- Actual operational (ExecutionActuals) ---
        try:
            actuals_rm = await build_execution_actuals_read_model(self.db, order_id=order_id)
        except Exception:
            actuals_rm = {
                "status": "unavailable",
                "tasks": [],
                "reality_total_actual_time_minutes": 0.0,
            }

        tasks = list(actuals_rm.get("tasks") or [])
        total_minutes = float(actuals_rm.get("reality_total_actual_time_minutes") or 0.0)
        session_count = sum(int(t.get("session_count") or 0) for t in tasks)
        active_any = any(bool(t.get("active_session")) for t in tasks)
        tasks_with_actual = [t for t in tasks if int(t.get("session_count") or 0) > 0]
        coverage_ratio = (
            len(tasks_with_actual) / len(tasks) if tasks else 0.0
        )
        employees: list[dict[str, Any]] = []
        first_start = None
        last_end = None
        for t in tasks:
            if t.get("first_started_at") and (
                first_start is None or t["first_started_at"] < first_start
            ):
                first_start = t["first_started_at"]
            if t.get("last_ended_at") and (
                last_end is None or t["last_ended_at"] > last_end
            ):
                last_end = t["last_ended_at"]
            if t.get("assigned_employee_id") is not None:
                employees.append(
                    {
                        "employee_id": t.get("assigned_employee_id"),
                        "task_id": t.get("task_id"),
                    }
                )

        planned_present = any(t.get("planned_minutes") is not None for t in tasks)
        duration_variance: dict[str, Any]
        if not planned_present:
            duration_variance = _unavailable(REASON_PLANNING_MINUTES_MISSING)
            if REASON_PLANNING_MINUTES_MISSING not in unavailable_reasons:
                unavailable_reasons.append(REASON_PLANNING_MINUTES_MISSING)
        else:
            # Only when both sides exist per-task; aggregate skip for honesty
            duration_variance = _unavailable(REASON_PLANNING_MINUTES_MISSING)

        if coverage_ratio < 1.0 or active_any or not tasks:
            unavailable_reasons.append(REASON_ACTUAL_TASK_COVERAGE_INCOMPLETE)
            unavailable_reasons.append(REASON_JOB_NOT_CLOSED)

        operational = {
            "session_count": session_count,
            "actual_duration_minutes": _available(
                total_minutes,
                provenance="execution_reality.total_actual_time_minutes",
            ),
            "employees_involved": employees,
            "first_started_at": first_start,
            "last_ended_at": last_end,
            "task_coverage": {
                "operational_task_count": len(tasks),
                "tasks_with_sessions": len(tasks_with_actual),
                "ratio": round(coverage_ratio, 4),
                "active_session_open": active_any,
            },
            "duration_variance_minutes": duration_variance,
            "tasks": tasks,
            "provenance": "controlled_task_session / execution_actuals_rm",
        }

        # --- Actual cost truth — NEVER invent labor ---
        unavailable_reasons.append(REASON_EMPLOYEE_COST_POLICY_MISSING)
        unavailable_reasons.append(REASON_ACTUAL_MATERIAL_COST_MISSING)
        unavailable_reasons.append(REASON_ACTUAL_TOTAL_COST_INCOMPLETE)

        actual_cost = {
            "actual_material_cost": _unavailable(REASON_ACTUAL_MATERIAL_COST_MISSING),
            "labor_actual_cost": _unavailable(REASON_EMPLOYEE_COST_POLICY_MISSING),
            "other_actual_cost": _unavailable(REASON_ACTUAL_TOTAL_COST_INCOMPLETE),
            "actual_total_cost": _unavailable(REASON_ACTUAL_TOTAL_COST_INCOMPLETE),
            "employee_cost_policy": "missing_owner_decision",
            "note": (
                "Actual minutes are operational truth. Monetary labor cost requires "
                "a separate Owner-approved employee cost policy. Do not use "
                "workcenter rate_per_hour, cost_lunar_firma÷hours, or commercial tariffs."
            ),
        }

        # --- Profitability result ---
        est_margin: dict[str, Any]
        if (
            commercial["accepted_revenue"]["available"]
            and estimated["estimated_total_cost"]["available"]
        ):
            revenue = float(commercial["accepted_revenue"]["value"])
            cost = float(estimated["estimated_total_cost"]["value"])
            amount = round(revenue - cost, 4)
            pct = round((amount / revenue) * 100.0, 4) if revenue > 0 else None
            est_margin = {
                "amount": _available(amount, provenance="commercial - estimated_internal"),
                "percent": _available(pct) if pct is not None else _unavailable(
                    REASON_ESTIMATED_INTERNAL_INCOMPLETE
                ),
            }
        else:
            est_margin = {
                "amount": _unavailable(REASON_ESTIMATED_INTERNAL_INCOMPLETE),
                "percent": _unavailable(REASON_ESTIMATED_INTERNAL_INCOMPLETE),
            }

        actual_margin = {
            "amount": _unavailable(REASON_ACTUAL_TOTAL_COST_INCOMPLETE),
            "percent": _unavailable(REASON_ACTUAL_TOTAL_COST_INCOMPLETE),
            "label_forbidden": "Profit real",
            "explanation": (
                "Actual margin stays unavailable until actual material cost and "
                "Owner-approved labor cost policy are both present and the job is closed."
            ),
        }

        # Deduplicate reasons preserving order
        seen: set[str] = set()
        reasons_unique: list[str] = []
        for r in unavailable_reasons:
            if r not in seen:
                seen.add(r)
                reasons_unique.append(r)

        return {
            "status": "ok",
            "order_id": order_id,
            "model_version": PROVENANCE,
            "commercial_truth": commercial,
            "estimated_internal_truth": estimated,
            "actual_operational_truth": operational,
            "actual_cost_truth": actual_cost,
            "profitability_result": {
                "estimated_margin": est_margin,
                "actual_margin": actual_margin,
                "unavailable_reasons": reasons_unique,
                "completeness": "partial_operational_only",
                "provenance": PROVENANCE,
            },
            "access": {
                "audience": ["admin", "manager"],
                "operator_sees_margins": False,
                "hr_cost_exposed": False,
            },
            "mutated": {
                "commercial_snapshot": False,
                "assignment": False,
                "sessions": False,
                "inventory": False,
                "pricing": False,
                "hr": False,
            },
        }
