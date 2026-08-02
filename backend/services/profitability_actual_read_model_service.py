"""Profitability Actual Read Model V1 — honest composition of frozen + actual truths.

READ-ONLY. Never invents labor money. Missing ≠ 0.
Does not mutate Order, Plan, Reality, Inventory, HR, or Pricing.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.actual_cost_policy import ActualLaborCostLine, ExecutionJobClosure
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from schemas.order_snapshot_v2 import OrderSnapshotV2
from services.actual_cost_policy_runtime_service import (
    ActualCostPolicyRuntimeService,
    REASON_HISTORICAL_COST_NOT_FROZEN,
    REASON_HISTORICAL_POLICY_UNAVAILABLE,
)
from services.controlled_task_session_service import build_execution_actuals_read_model


REASON_PLANNING_MINUTES_MISSING = "planning_minutes_source_missing"
REASON_ACTUAL_MATERIAL_COST_MISSING = "actual_material_cost_missing"
REASON_EMPLOYEE_COST_POLICY_MISSING = "employee_cost_policy_missing"
REASON_JOB_NOT_CLOSED = "job_not_closed"
REASON_EXECUTION_REOPENED = "execution_reopened"
REASON_ACTUAL_TASK_COVERAGE_INCOMPLETE = "actual_task_coverage_incomplete"
REASON_ACCEPTED_COMMERCIAL_MISSING = "accepted_commercial_snapshot_missing"
REASON_ESTIMATED_INTERNAL_INCOMPLETE = "estimated_internal_cost_incomplete"
REASON_ACTUAL_TOTAL_COST_INCOMPLETE = "actual_total_cost_incomplete"
REASON_COST_CATEGORY_REQUIRED_INCOMPLETE = "cost_category_required_incomplete"
REASON_MACHINE_ACTUAL_NOT_CAPTURED = "machine_actual_not_captured"
REASON_MACHINE_POLICY_MISSING = "machine_policy_missing"
REASON_MACHINE_NOT_APPLICABLE = "machine_not_applicable_by_job_profile"
REASON_OTHER_DIRECT_NOT_APPLICABLE = "other_direct_not_declared"
REASON_OTHER_DIRECT_UNCLASSIFIED = "direct_cost_unclassified"
REASON_MATERIAL_MOVEMENT_MISSING = "material_movement_missing"
REASON_MATERIAL_VALUATION_MISSING = "material_valuation_missing"

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

    async def _load_plan_tasks(self, order_id: int) -> list[dict[str, Any]]:
        """Plan tasks may declare machine applicability before usage is captured."""
        plan = (
            await self.db.execute(
                select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
            )
        ).scalar_one_or_none()
        if plan is None or plan.tasks_json in (None, ""):
            return []
        try:
            data = (
                json.loads(plan.tasks_json)
                if isinstance(plan.tasks_json, str)
                else plan.tasks_json
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            return []
        return [t for t in data if isinstance(t, dict)] if isinstance(data, list) else []

    @staticmethod
    def _machine_cost_category(tasks: list[dict[str, Any]]) -> dict[str, Any]:
        """Conditional machine actuals — never invent from WC rate or planned duration."""
        declares_machine = False
        for task in tasks:
            for key in (
                "machine_id",
                "assigned_machine_id",
                "utilaj_id",
                "machine_instance_id",
            ):
                if task.get(key) not in (None, "", 0, "0"):
                    declares_machine = True
                    break
            if task.get("machine_actual_required") is True:
                declares_machine = True
            if declares_machine:
                break
        if not declares_machine:
            return {
                "applicability": "not_applicable",
                "status": "not_applicable",
                "reason": REASON_MACHINE_NOT_APPLICABLE,
                "value": None,
                "available": False,
            }
        # Declared applicable but runtime has no frozen machine usage + dated policy.
        return {
            "applicability": "applicable_optional",
            "status": "unavailable",
            "reason": REASON_MACHINE_ACTUAL_NOT_CAPTURED,
            "secondary_reason": REASON_MACHINE_POLICY_MISSING,
            "value": None,
            "available": False,
        }

    async def _load_actual_cost_facts(
        self, order_id: int
    ) -> tuple[list[ActualLaborCostLine], dict[str, Any], ExecutionJobClosure | None]:
        """Load frozen labor lines, material actual, and job closure (awaited Session API)."""
        labor_result = await self.db.execute(
            select(ActualLaborCostLine).where(ActualLaborCostLine.order_id == order_id)
        )
        labor_lines = list(labor_result.scalars().all())
        material = await ActualCostPolicyRuntimeService(self.db).actual_material_cost(order_id)
        closure_result = await self.db.execute(
            select(ExecutionJobClosure).where(ExecutionJobClosure.order_id == order_id)
        )
        closure = closure_result.scalar_one_or_none()
        return labor_lines, material, closure

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

        # --- Actual cost truth — frozen standard role/skill policies only ---
        labor_lines, material, closure = await self._load_actual_cost_facts(order_id)
        closure_status = closure.status if closure else "open"
        if labor_lines:
            labor = _available(
                round(sum(float(line.labor_cost_amount) for line in labor_lines), 4),
                provenance="actual_labor_cost_lines.standard_role_skill",
            )
            labor["currency"] = labor_lines[0].currency
        else:
            labor = _unavailable(REASON_EMPLOYEE_COST_POLICY_MISSING)
            unavailable_reasons.extend([REASON_EMPLOYEE_COST_POLICY_MISSING, REASON_HISTORICAL_POLICY_UNAVAILABLE, REASON_HISTORICAL_COST_NOT_FROZEN])
        if not material["available"]:
            unavailable_reasons.append(REASON_ACTUAL_MATERIAL_COST_MISSING)
            mat_reason = str(material.get("reason") or "")
            if "valuation" in mat_reason:
                unavailable_reasons.append(REASON_MATERIAL_VALUATION_MISSING)
            elif "movement" in mat_reason or mat_reason.endswith("missing"):
                unavailable_reasons.append(REASON_MATERIAL_MOVEMENT_MISSING)
        closed = closure_status == "closed"
        reopened = closure_status == "reopened"
        if reopened:
            unavailable_reasons.append(REASON_EXECUTION_REOPENED)
        if not closed:
            unavailable_reasons.append(REASON_JOB_NOT_CLOSED)

        plan_tasks = await self._load_plan_tasks(order_id)
        machine_category = self._machine_cost_category([*tasks, *plan_tasks])
        other_direct_category = {
            "applicability": "not_applicable",
            "status": "not_applicable",
            "reason": REASON_OTHER_DIRECT_NOT_APPLICABLE,
            "value": None,
            "available": False,
            "note": (
                "Alte costuri directe necesită fapte clasificate (categorie, sumă, "
                "proveniență, actor). Nu există bucket generic editabil."
            ),
        }
        labor_status = "complete" if labor["available"] else "incomplete"
        material_cost_status = (
            material.get("material_cost_status")
            or ("complete" if material.get("available") else "incomplete")
        )
        material_valuation_status = (
            material.get("material_valuation_status")
            or ("frozen" if material.get("available") else "unavailable")
        )
        cost_categories = {
            "labor": {
                "applicability": "required",
                "status": labor_status,
                "reason": None if labor["available"] else REASON_EMPLOYEE_COST_POLICY_MISSING,
            },
            "material": {
                "applicability": "required",
                "status": material_cost_status,
                "reason": None if material.get("available") else material.get("reason"),
            },
            "machine": machine_category,
            "other_direct": other_direct_category,
            "execution": {
                "status": closure_status,
                "final_margin_available": False,
            },
        }
        # Required categories must be complete. Conditional machine/other_direct that are
        # not_applicable never block. Unavailable optional machine is reported, not zeroed,
        # and does not invent WC-rate actuals.
        applicable_incomplete = [
            key
            for key in ("labor", "material")
            if cost_categories[key].get("status") != "complete"
        ]
        if applicable_incomplete:
            unavailable_reasons.append(REASON_COST_CATEGORY_REQUIRED_INCOMPLETE)
        if (
            machine_category.get("applicability") != "not_applicable"
            and machine_category.get("status") in {"unavailable", "incomplete"}
            and machine_category.get("reason")
        ):
            unavailable_reasons.append(str(machine_category["reason"]))

        complete_actuals = (
            labor["available"]
            and material["available"]
            and closed
            and not applicable_incomplete
        )
        if not complete_actuals:
            unavailable_reasons.append(REASON_ACTUAL_TOTAL_COST_INCOMPLETE)
        cost_categories["execution"]["final_margin_available"] = complete_actuals
        if complete_actuals:
            actual_cost_status = "closed_job_operational_actual"
            actual_margin_status = "closed_job_operational_actual"
        elif labor["available"] or material.get("available"):
            actual_cost_status = "provisional_operational"
            actual_margin_status = "unavailable"
        else:
            actual_cost_status = "unavailable"
            actual_margin_status = "unavailable"
        actual_cost = {
            "actual_material_cost": material,
            "labor_actual_cost": labor,
            "labor_cost_basis": "standard_role_skill",
            "labor_cost_status": labor_status,
            "material_cost_status": material_cost_status,
            "material_valuation_status": material_valuation_status,
            "execution_closure_status": closure_status,
            "actual_cost_status": actual_cost_status,
            "job_closure_status": closure_status,
            "machine_actual_cost": {
                "value": None,
                "available": False,
                "reason": machine_category.get("reason"),
                "status": machine_category.get("status"),
                "applicability": machine_category.get("applicability"),
                "note": (
                    "Cost utilaj condițional. Fără fallback workcenter.rate, "
                    "tarif comercial sau durată planificată ca actual."
                ),
            },
            "other_actual_cost": {
                "value": None,
                "available": False,
                "reason": other_direct_category["reason"],
                "status": other_direct_category["status"],
                "applicability": other_direct_category["applicability"],
            },
            "cost_category_applicability": cost_categories,
            "actual_total_cost": (
                _available(round(float(material["value"]) + float(labor["value"]), 4), provenance="frozen_material + frozen_labor")
                if complete_actuals else _unavailable(REASON_ACTUAL_TOTAL_COST_INCOMPLETE)
            ),
            "note": "Cost intern standard pe rol/competență; fără salariu, tarif de client sau tarif workcenter.",
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

        if complete_actuals and commercial["accepted_revenue"]["available"]:
            actual_total = float(actual_cost["actual_total_cost"]["value"])
            revenue = float(commercial["accepted_revenue"]["value"])
            margin_amount = round(revenue - actual_total, 4)
            actual_margin = {
                "amount": _available(margin_amount, provenance="accepted_commercial - frozen_actual_cost"),
                "percent": _available(round(margin_amount / revenue * 100.0, 4)) if revenue else _unavailable(REASON_ACTUAL_TOTAL_COST_INCOMPLETE),
                "label": "Marjă actuală job închis",
                "provisional": False,
                "actual_margin_status": actual_margin_status,
            }
        else:
            actual_margin = {
                "amount": _unavailable(REASON_ACTUAL_TOTAL_COST_INCOMPLETE),
                "percent": _unavailable(REASON_ACTUAL_TOTAL_COST_INCOMPLETE),
                "label": "Marjă actuală indisponibilă",
                "provisional": True,
                "actual_margin_status": actual_margin_status,
                "explanation": "Necesită cost material și manoperă complete, plus închidere explicită job.",
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
                "completeness": "complete_closed_job" if complete_actuals else "incomplete_or_open_job",
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
