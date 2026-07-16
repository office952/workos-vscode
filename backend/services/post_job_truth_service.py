"""
PostJobTruthService — cohesive post-job actuals + reconciliation + profitability coverage.

READ-ONLY. Never mutates Order, Quote, ExecutionPlan, ExecutionReality, sessions,
or inventory. Does not import CostEngine / QuoteOrchestrator / /price.

Labor money is intentionally excluded (G2). Material money uses inventory catalog
unit_cost labeled as valuation method — never silent current-price invention without label.
Machine actual usage is not captured in runtime → not_captured.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.inventory_materials import Inventory_materials
from models.orders import Orders
from models.stock_movements import StockMovement
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.post_job_truth import (
    ReconciliationOpState,
    ReconciliationSummary,
    LaborActuals,
    LaborSessionRow,
    MachineActualItem,
    MachineActuals,
    MaterialActualLine,
    MaterialActuals,
    MissingDataItem,
    OperationReconciliationRow,
    PostJobBaseline,
    PostJobTruthResponse,
    PresenceValue,
    ProfitabilityCoverage,
    QuantityActuals,
    ReconciliationBlock,
    ReconciliationVariance,
)
from services.execution_plan_task_parser import parse_tasks_json_raw
from services.task_work_session_service import (
    aggregate_task_work_metrics,
    compute_duration_minutes,
    derive_task_status_from_sessions,
    ensure_session_id,
    is_session_active,
    sessions_for_task,
)


class OrderNotFoundError(LookupError):
    """Raised when order_id does not exist."""


VALUATION_INVENTORY_CATALOG_UNIT_COST = "inventory_materials.unit_cost_at_read"


class PostJobTruthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_for_order(self, order_id: int) -> PostJobTruthResponse:
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError("order_id_invalid")

        order = await self._load_order(order_id)
        if order is None:
            raise OrderNotFoundError(f"order_not_found:{order_id}")

        snapshot_v2 = self._parse_snapshot_v2(order)
        plan = await self._load_plan(order_id)
        reality = await self._load_reality(order_id)
        movements = await self._load_consumption_movements(order_id)

        baseline = self._build_baseline(order, snapshot_v2)
        labor = self._build_labor(plan, reality)
        materials = await self._build_materials(reality, movements, snapshot_v2)
        machines = self._build_machines(plan)
        quantity = self._build_quantity(plan, reality)
        reconciliation = self._build_reconciliation(
            baseline=baseline,
            labor=labor,
            materials=materials,
            machines=machines,
            quantity=quantity,
            plan=plan,
            reality=reality,
        )
        profitability, missing = self._build_profitability(
            baseline=baseline,
            labor=labor,
            materials=materials,
            machines=machines,
            quantity=quantity,
            has_reality=reality is not None,
        )

        return PostJobTruthResponse(
            order_id=order.id,
            order_code=order.code,
            baseline=baseline,
            labor=labor,
            materials=materials,
            machines=machines,
            quantity=quantity,
            reconciliation=reconciliation,
            profitability=profitability,
            missing_data=missing,
            sources={
                "revenue": baseline.revenue_source,
                "planned_cost": "order_snapshot_v2.estimated_internal_total"
                if snapshot_v2 is not None
                else "missing",
                "labor_minutes": "execution_reality.tasks_json_sessions",
                "material_actuals": "stock_movements.consumption",
                "material_valuation": materials.valuation_method,
                "machine_usage": "not_captured_in_runtime",
                "quantity": "task_completion_from_sessions",
            },
            retroactive_change_allowed=False,
            write_back_performed=False,
        )

    async def _load_order(self, order_id: int) -> Orders | None:
        result = await self.db.execute(select(Orders).where(Orders.id == order_id))
        return result.scalar_one_or_none()

    async def _load_plan(self, order_id: int) -> ExecutionPlan | None:
        result = await self.db.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
        rows = list(result.scalars().all())
        if not rows:
            return None
        return sorted(rows, key=lambda row: row.id)[-1]

    async def _load_reality(self, order_id: int) -> ExecutionReality | None:
        result = await self.db.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def _load_consumption_movements(self, order_id: int) -> list[StockMovement]:
        result = await self.db.execute(
            select(StockMovement)
            .where(StockMovement.order_id == order_id)
            .where(StockMovement.movement_type == "consumption")
            .order_by(StockMovement.performed_at.asc(), StockMovement.id.asc())
        )
        consumptions = list(result.scalars().all())
        if not consumptions:
            return []

        reversal_keys = [f"reversal:{m.id}" for m in consumptions]
        reversed_ids: set[int] = set()
        rev_result = await self.db.execute(
            select(StockMovement.idempotency_key).where(
                StockMovement.idempotency_key.in_(reversal_keys)
            )
        )
        for key in rev_result.scalars().all():
            if isinstance(key, str) and key.startswith("reversal:"):
                try:
                    reversed_ids.add(int(key.split(":", 1)[1]))
                except (TypeError, ValueError):
                    continue
        return [m for m in consumptions if m.id not in reversed_ids]

    @staticmethod
    def _parse_snapshot_v2(order: Orders) -> OrderSnapshotV2 | None:
        raw = getattr(order, "snapshot_v2_json", None)
        if raw is None:
            return None
        if isinstance(raw, str):
            if not raw.strip():
                return None
            try:
                return OrderSnapshotV2.model_validate_json(raw)
            except (TypeError, ValueError):
                return None
        return None

    @staticmethod
    def _pv(
        value: float | int | str | bool | None,
        presence: str,
        *,
        unit: str | None = None,
        source: str | None = None,
        note: str | None = None,
    ) -> PresenceValue:
        return PresenceValue(
            value=value,
            presence=presence,  # type: ignore[arg-type]
            unit=unit,
            source=source,
            note=note,
        )

    def _build_baseline(
        self, order: Orders, snapshot_v2: OrderSnapshotV2 | None
    ) -> PostJobBaseline:
        if snapshot_v2 is not None:
            revenue = snapshot_v2.accepted_commercial_total
            currency = snapshot_v2.accepted_currency
            planned = snapshot_v2.estimated_internal_total
            return PostJobBaseline(
                revenue_net=self._pv(
                    revenue,
                    "present" if revenue is not None else "missing",
                    unit=currency,
                    source="order_snapshot_v2.accepted_commercial_total",
                ),
                planned_internal_cost=self._pv(
                    planned,
                    "present" if planned is not None else "missing",
                    unit=currency,
                    source="order_snapshot_v2.estimated_internal_total",
                ),
                currency=currency,
                revenue_source="order_snapshot_v2",
                has_snapshot_v2=True,
                snapshot_version=getattr(order, "snapshot_version", None),
            )

        if order.total_amount is not None:
            return PostJobBaseline(
                revenue_net=self._pv(
                    float(order.total_amount),
                    "present",
                    source="order.total_amount",
                    note="legacy_without_snapshot_v2",
                ),
                planned_internal_cost=self._pv(
                    None, "missing", note="no_snapshot_v2_estimated_internal"
                ),
                currency=None,
                revenue_source="order.total_amount",
                has_snapshot_v2=False,
                snapshot_version=getattr(order, "snapshot_version", None),
            )

        return PostJobBaseline(
            revenue_net=self._pv(None, "missing"),
            planned_internal_cost=self._pv(None, "missing"),
            currency=None,
            revenue_source="missing",
            has_snapshot_v2=False,
            snapshot_version=getattr(order, "snapshot_version", None),
        )

    def _parse_reality_sessions(self, reality: ExecutionReality | None) -> list[dict[str, Any]]:
        if reality is None or not reality.tasks_json:
            return []
        try:
            data = json.loads(reality.tasks_json)
        except (TypeError, ValueError):
            return []
        if not isinstance(data, list):
            return []
        return [row for row in data if isinstance(row, dict)]

    def _build_labor(
        self, plan: ExecutionPlan | None, reality: ExecutionReality | None
    ) -> LaborActuals:
        planned_minutes: float | None = None
        planned_presence = "missing"
        if plan is not None:
            planned_minutes = float(plan.total_estimated_time_minutes or 0.0)
            # Distinguish unknown vs explicitly zero planned
            if plan.total_estimated_time_minutes is None:
                planned_presence = "missing"
                planned_minutes = None
            else:
                planned_presence = "zero" if planned_minutes == 0.0 else "present"

        sessions_raw = self._parse_reality_sessions(reality)
        if reality is None:
            return LaborActuals(
                closed_minutes_total=self._pv(
                    None, "not_captured", unit="min", source="execution_reality"
                ),
                open_session_count=0,
                session_count=0,
                planned_minutes_total=self._pv(
                    planned_minutes, planned_presence, unit="min", source="execution_plan"
                ),
                variance_minutes=self._pv(None, "missing", unit="min"),
                sessions=[],
                monetary_cost=self._pv(
                    None,
                    "excluded",
                    note="labor_money_out_of_scope_g2",
                    source="hr_rate_not_authorized",
                ),
                completeness="not_captured",
            )

        rows: list[LaborSessionRow] = []
        open_count = 0
        closed_total = 0.0
        for entry in sessions_raw:
            active = is_session_active(entry)
            minutes: float | None = None
            status = "still_active" if active else "ended"
            completeness = "still_active" if active else "complete"
            if active:
                open_count += 1
                minutes = None
            else:
                duration = entry.get("duration_minutes")
                if duration is None and entry.get("started_at") and entry.get("ended_at"):
                    duration = compute_duration_minutes(
                        str(entry["started_at"]), str(entry["ended_at"])
                    )
                if duration is not None:
                    minutes = float(duration)
                    closed_total += minutes
                else:
                    completeness = "partial"

            employee_id = None
            try:
                if entry.get("employee_id") is not None:
                    employee_id = int(entry["employee_id"])
            except (TypeError, ValueError):
                employee_id = None

            rows.append(
                LaborSessionRow(
                    session_id=ensure_session_id(entry),
                    task_id=str(entry.get("task_id") or "") or None,
                    employee_id=employee_id,
                    employee_name=str(entry.get("employee_name") or "") or None,
                    role=str(entry.get("role") or "") or None,
                    session_type=str(entry.get("session_type") or "") or None,
                    started_at=str(entry.get("started_at")) if entry.get("started_at") else None,
                    ended_at=str(entry.get("ended_at")) if entry.get("ended_at") else None,
                    actual_minutes=minutes,
                    status=status,
                    completeness=completeness,  # type: ignore[arg-type]
                )
            )

        # Prefer session aggregation; fall back to reality rollup if sessions empty
        if sessions_raw:
            closed_presence = "zero" if closed_total == 0.0 and open_count == 0 else "present"
            if open_count > 0 and closed_total == 0.0:
                closed_presence = "partial"
            closed_value: float | None = round(closed_total, 4)
        else:
            rollup = reality.total_actual_time_minutes
            if rollup is None:
                closed_value = None
                closed_presence = "missing"
            else:
                closed_value = float(rollup)
                closed_presence = "zero" if closed_value == 0.0 else "present"

        variance_presence = "missing"
        variance_value: float | None = None
        if planned_presence in ("present", "zero") and closed_presence in (
            "present",
            "zero",
            "partial",
        ):
            if planned_minutes is not None and closed_value is not None:
                variance_value = round(closed_value - planned_minutes, 4)
                variance_presence = "present"

        labor_completeness = "complete"
        if open_count > 0:
            labor_completeness = "still_active"
        elif closed_presence in ("missing", "not_captured"):
            labor_completeness = "not_captured"
        elif closed_presence == "partial":
            labor_completeness = "partial"

        return LaborActuals(
            closed_minutes_total=self._pv(
                closed_value,
                closed_presence,
                unit="min",
                source="execution_reality.sessions",
                note="open_sessions_excluded_from_closed_total"
                if open_count > 0
                else None,
            ),
            open_session_count=open_count,
            session_count=len(rows),
            planned_minutes_total=self._pv(
                planned_minutes, planned_presence, unit="min", source="execution_plan"
            ),
            variance_minutes=self._pv(
                variance_value, variance_presence, unit="min", source="reconciliation"
            ),
            sessions=rows,
            monetary_cost=self._pv(
                None,
                "excluded",
                note="labor_money_out_of_scope_g2",
                source="hr_rate_not_authorized",
            ),
            completeness=labor_completeness,  # type: ignore[arg-type]
        )

    async def _build_materials(
        self,
        reality: ExecutionReality | None,
        movements: list[StockMovement],
        snapshot_v2: OrderSnapshotV2 | None,
    ) -> MaterialActuals:
        observed = self._parse_materials(reality)
        planned_by_name = self._planned_material_hints(snapshot_v2)

        material_ids = {m.material_id for m in movements if m.material_id is not None}
        inventory_by_id: dict[int, Inventory_materials] = {}
        if material_ids:
            result = await self.db.execute(
                select(Inventory_materials).where(Inventory_materials.id.in_(material_ids))
            )
            for row in result.scalars().all():
                inventory_by_id[int(row.id)] = row

        lines: list[MaterialActualLine] = []
        known_cost_sum = 0.0
        known_cost_any = False
        valuation_used: str | None = None

        for movement in movements:
            inv = inventory_by_id.get(int(movement.material_id)) if movement.material_id else None
            qty = float(movement.quantity) if movement.quantity is not None else None
            unit_cost = float(inv.unit_cost) if inv is not None and inv.unit_cost is not None else None
            actual_cost: float | None = None
            cost_presence = "missing"
            if qty is not None and unit_cost is not None:
                actual_cost = round(qty * unit_cost, 4)
                cost_presence = "present"
                known_cost_sum += actual_cost
                known_cost_any = True
                valuation_used = VALUATION_INVENTORY_CATALOG_UNIT_COST

            planned_qty = None
            planned_qty_presence = "missing"
            planned_cost = None
            planned_cost_presence = "missing"
            hint_key = (inv.name if inv else None) or None
            if hint_key and hint_key in planned_by_name:
                hint = planned_by_name[hint_key]
                planned_qty = hint.get("quantity")
                planned_qty_presence = "present" if planned_qty is not None else "missing"
                planned_cost = hint.get("internal_cost")
                planned_cost_presence = "present" if planned_cost is not None else "missing"

            qty_var = None
            qty_var_presence = "missing"
            if planned_qty is not None and qty is not None:
                qty_var = round(qty - float(planned_qty), 4)
                qty_var_presence = "present"

            cost_var = None
            cost_var_presence = "missing"
            if planned_cost is not None and actual_cost is not None:
                cost_var = round(actual_cost - float(planned_cost), 4)
                cost_var_presence = "present"

            lines.append(
                MaterialActualLine(
                    material_id=movement.material_id,
                    material_name=inv.name if inv else None,
                    material_code=inv.code if inv else None,
                    task_id=str(movement.task_id) if movement.task_id else None,
                    planned_quantity=self._pv(
                        planned_qty, planned_qty_presence, unit=movement.unit
                    ),
                    actual_deducted_quantity=self._pv(
                        qty,
                        "present" if qty is not None else "missing",
                        unit=movement.unit,
                        source="stock_movements.consumption",
                    ),
                    unit=movement.unit,
                    planned_internal_cost=self._pv(
                        planned_cost, planned_cost_presence, source="snapshot_or_missing"
                    ),
                    actual_known_internal_cost=self._pv(
                        actual_cost,
                        cost_presence,
                        source=VALUATION_INVENTORY_CATALOG_UNIT_COST
                        if cost_presence == "present"
                        else None,
                        note=None
                        if cost_presence == "present"
                        else "unit_cost_unavailable_at_read",
                    ),
                    quantity_variance=self._pv(qty_var, qty_var_presence, unit=movement.unit),
                    cost_variance=self._pv(cost_var, cost_var_presence),
                    valuation_method=VALUATION_INVENTORY_CATALOG_UNIT_COST
                    if cost_presence == "present"
                    else None,
                    source="stock_movements.consumption",
                    movement_id=movement.id,
                    performed_at=movement.performed_at.isoformat()
                    if movement.performed_at
                    else None,
                    completeness="complete" if qty is not None else "partial",  # type: ignore[arg-type]
                )
            )

        # Observed but not deducted → missing actual (not zero)
        deducted_keys = {
            (m.material_id, str(m.task_id or ""), round(float(m.quantity or 0), 4))
            for m in movements
        }
        for idx, mat in enumerate(observed):
            mat_id = mat.get("material_id")
            try:
                mat_id_int = int(mat_id) if mat_id is not None else None
            except (TypeError, ValueError):
                mat_id_int = None
            qty = mat.get("quantity")
            try:
                qty_f = float(qty) if qty is not None else None
            except (TypeError, ValueError):
                qty_f = None
            key = (mat_id_int, str(mat.get("task_id") or ""), round(qty_f or 0, 4))
            if mat_id_int is not None and key in deducted_keys:
                continue
            lines.append(
                MaterialActualLine(
                    material_id=mat_id_int,
                    material_name=str(mat.get("material_name") or "") or None,
                    task_id=str(mat.get("task_id") or "") or None,
                    planned_quantity=self._pv(None, "missing"),
                    actual_deducted_quantity=self._pv(
                        None,
                        "not_captured",
                        unit=str(mat.get("unit") or "") or None,
                        source="execution_reality.materials_json",
                        note="observed_not_deducted",
                    ),
                    unit=str(mat.get("unit") or "") or None,
                    planned_internal_cost=self._pv(None, "missing"),
                    actual_known_internal_cost=self._pv(None, "not_captured"),
                    quantity_variance=self._pv(None, "missing"),
                    cost_variance=self._pv(None, "missing"),
                    source="execution_reality.materials_json",
                    completeness="not_captured",  # type: ignore[arg-type]
                )
            )

        if not movements and not observed:
            completeness = "not_captured"
            known_cost = self._pv(None, "not_captured", source="stock_movements")
        elif movements and known_cost_any:
            completeness = "partial" if any(
                line.actual_known_internal_cost.presence != "present" for line in lines
            ) else "complete"
            # Material cost complete only for valued deductions; labor still missing overall
            known_cost = self._pv(
                round(known_cost_sum, 4),
                "present",
                source=VALUATION_INVENTORY_CATALOG_UNIT_COST,
            )
        elif movements and not known_cost_any:
            completeness = "partial"
            known_cost = self._pv(
                None,
                "missing",
                note="deductions_exist_but_unit_cost_unavailable",
            )
        else:
            completeness = "not_captured"
            known_cost = self._pv(
                None,
                "not_captured",
                note="materials_observed_without_deduction",
            )

        return MaterialActuals(
            lines=lines,
            observed_row_count=len(observed),
            deducted_movement_count=len(movements),
            known_actual_cost_total=known_cost,
            valuation_method=valuation_used,
            completeness=completeness,  # type: ignore[arg-type]
        )

    @staticmethod
    def _parse_materials(reality: ExecutionReality | None) -> list[dict[str, Any]]:
        if reality is None or not reality.materials_json:
            return []
        try:
            data = json.loads(reality.materials_json)
        except (TypeError, ValueError):
            return []
        if not isinstance(data, list):
            return []
        return [row for row in data if isinstance(row, dict)]

    @staticmethod
    def _planned_material_hints(
        snapshot_v2: OrderSnapshotV2 | None,
    ) -> dict[str, dict[str, Any]]:
        """Best-effort planned material hints from EIC snapshot — never treated as actual."""
        hints: dict[str, dict[str, Any]] = {}
        if snapshot_v2 is None:
            return hints
        eic = snapshot_v2.estimated_internal_cost_snapshot
        if eic is None:
            return hints
        materials = list(getattr(eic, "estimated_material_lines", None) or [])
        for line in materials:
            name = getattr(line, "label", None) or getattr(line, "code", None)
            if not name:
                continue
            hints[str(name)] = {
                "quantity": getattr(line, "quantity", None),
                "internal_cost": getattr(line, "subtotal", None),
            }
        return hints

    def _build_machines(self, plan: ExecutionPlan | None) -> MachineActuals:
        items: list[MachineActualItem] = []
        if plan is not None and plan.tasks_json:
            parsed = parse_tasks_json_raw(plan.tasks_json)
            for task in parsed.operational_tasks:
                if not isinstance(task, dict):
                    continue
                machine_id = task.get("required_machine_id") or task.get("machine_id")
                machine_type = task.get("required_machine_type") or task.get("machine_type")
                if machine_id or machine_type:
                    items.append(
                        MachineActualItem(
                            task_id=str(task.get("task_id") or task.get("id") or "") or None,
                            planned_machine_id=str(machine_id) if machine_id else None,
                            planned_machine_type=str(machine_type) if machine_type else None,
                            status="not_captured",
                            note="plan_assigned_only_no_runtime_usage_log",
                        )
                    )
        return MachineActuals(
            items=items,
            completeness="not_captured" if items else "not_applicable",
            note="machine_usage_not_logged_in_execution_reality",
        )

    def _build_quantity(
        self, plan: ExecutionPlan | None, reality: ExecutionReality | None
    ) -> QuantityActuals:
        planned_tasks = 0
        plan_tasks: list[dict[str, Any]] = []
        if plan is not None and plan.tasks_json:
            parsed = parse_tasks_json_raw(plan.tasks_json)
            plan_tasks = list(parsed.operational_tasks)
            planned_tasks = len(plan_tasks)

        sessions = self._parse_reality_sessions(reality)
        completed = 0
        if plan_tasks:
            for task in plan_tasks:
                task_id = str(task.get("task_id") or task.get("id") or "")
                task_sessions = sessions_for_task(sessions, task_id)
                if derive_task_status_from_sessions(task_sessions) == "done":
                    completed += 1
        elif sessions:
            # No plan tasks — derive unique task completion from sessions only
            task_ids = sorted(
                {
                    str(s.get("task_id") or "")
                    for s in sessions
                    if s.get("task_id")
                }
            )
            planned_tasks = len(task_ids)
            for task_id in task_ids:
                if derive_task_status_from_sessions(sessions_for_task(sessions, task_id)) == "done":
                    completed += 1

        if reality is None and plan is None:
            return QuantityActuals(
                tasks_planned=self._pv(None, "missing"),
                tasks_completed=self._pv(None, "not_captured"),
                progress_percent=self._pv(None, "missing", unit="%"),
                completed_quantity=self._pv(
                    None,
                    "not_captured",
                    note="produced_quantity_not_in_domain",
                ),
                completeness="not_captured",
            )

        progress = None
        progress_presence = "missing"
        if planned_tasks > 0:
            progress = round((completed / planned_tasks) * 100.0, 4)
            progress_presence = "present"

        return QuantityActuals(
            tasks_planned=self._pv(
                planned_tasks if planned_tasks else None,
                "present" if planned_tasks else "missing",
                source="execution_plan.operational_tasks",
            ),
            tasks_completed=self._pv(
                completed if reality is not None else None,
                "present" if reality is not None else "not_captured",
                source="execution_reality.sessions_derived_status",
            ),
            progress_percent=self._pv(progress, progress_presence, unit="%"),
            completed_quantity=self._pv(
                None,
                "not_captured",
                note="produced_quantity_field_absent_in_runtime",
            ),
            completeness="partial" if reality is not None else "not_captured",  # type: ignore[arg-type]
        )

    def _build_reconciliation(
        self,
        *,
        baseline: PostJobBaseline,
        labor: LaborActuals,
        materials: MaterialActuals,
        machines: MachineActuals,
        quantity: QuantityActuals,
        plan: ExecutionPlan | None,
        reality: ExecutionReality | None,
    ) -> ReconciliationBlock:
        variances: list[ReconciliationVariance] = []

        def add_var(
            dimension: str,
            planned: float | None,
            actual: float | None,
            *,
            unit: str | None,
            source: str,
            planned_presence: str,
            actual_presence: str,
            explanation_code: str,
        ) -> None:
            abs_var = None
            pct = None
            status = "missing"
            if planned_presence in ("present", "zero") and actual_presence in (
                "present",
                "zero",
                "partial",
            ):
                if planned is not None and actual is not None:
                    abs_var = round(actual - planned, 4)
                    status = "present"
                    if planned != 0:
                        pct = round((abs_var / planned) * 100.0, 4)
                    else:
                        pct = None  # never invent % with zero denominator
            elif actual_presence in ("not_captured", "missing", "excluded"):
                status = actual_presence  # type: ignore[assignment]
            variances.append(
                ReconciliationVariance(
                    dimension=dimension,
                    planned_value=planned,
                    actual_value=actual,
                    absolute_variance=abs_var,
                    percentage_variance=pct,
                    unit=unit,
                    source=source,
                    status=status,  # type: ignore[arg-type]
                    explanation_code=explanation_code,
                    data_completeness=status,  # type: ignore[arg-type]
                )
            )

        add_var(
            "labor_minutes",
            labor.planned_minutes_total.value
            if isinstance(labor.planned_minutes_total.value, (int, float))
            else None,
            labor.closed_minutes_total.value
            if isinstance(labor.closed_minutes_total.value, (int, float))
            else None,
            unit="min",
            source="plan_vs_sessions",
            planned_presence=labor.planned_minutes_total.presence,
            actual_presence=labor.closed_minutes_total.presence,
            explanation_code="minutes_plan_vs_closed_sessions",
        )

        mat_actual = (
            materials.known_actual_cost_total.value
            if isinstance(materials.known_actual_cost_total.value, (int, float))
            else None
        )
        planned_cost = (
            baseline.planned_internal_cost.value
            if isinstance(baseline.planned_internal_cost.value, (int, float))
            else None
        )
        add_var(
            "known_material_cost_vs_planned_internal",
            planned_cost,
            mat_actual,
            unit=baseline.currency,
            source="snapshot_vs_stock_deduction",
            planned_presence=baseline.planned_internal_cost.presence,
            actual_presence=materials.known_actual_cost_total.presence,
            explanation_code="material_known_cost_only_vs_full_planned_internal",
        )

        add_var(
            "task_completion_count",
            quantity.tasks_planned.value
            if isinstance(quantity.tasks_planned.value, (int, float))
            else None,
            quantity.tasks_completed.value
            if isinstance(quantity.tasks_completed.value, (int, float))
            else None,
            unit="tasks",
            source="plan_vs_session_status",
            planned_presence=quantity.tasks_planned.presence,
            actual_presence=quantity.tasks_completed.presence,
            explanation_code="tasks_planned_vs_done",
        )

        operations: list[OperationReconciliationRow] = []
        plan_tasks: list[dict[str, Any]] = []
        if plan is not None and plan.tasks_json:
            plan_tasks = list(parse_tasks_json_raw(plan.tasks_json).operational_tasks)
        sessions = self._parse_reality_sessions(reality)
        qty_not_captured = self._pv(
            None,
            "not_captured",
            note="produced_quantity_field_absent_in_runtime",
        )
        for task in plan_tasks:
            if not isinstance(task, dict):
                continue
            task_id = str(task.get("task_id") or task.get("id") or "")
            if not task_id:
                continue
            task_sessions = sessions_for_task(sessions, task_id)
            metrics = aggregate_task_work_metrics(task_sessions)
            planned_min = task.get("estimated_time_minutes")
            try:
                planned_f = float(planned_min) if planned_min is not None else None
            except (TypeError, ValueError):
                planned_f = None

            has_active = any(is_session_active(s) for s in task_sessions)
            if reality is None or not task_sessions:
                actual_presence = "not_captured"
                actual_f_val: float | None = None
                actual_status: str | None = None if reality is None else "assigned"
            else:
                actual_f_val = float(metrics["total_logged_minutes"])
                if has_active:
                    actual_presence = "partial"
                elif actual_f_val == 0.0:
                    actual_presence = "zero"
                else:
                    actual_presence = "present"
                actual_status = derive_task_status_from_sessions(task_sessions)

            var_val = None
            var_presence = "missing"
            if (
                planned_f is not None
                and actual_f_val is not None
                and actual_presence in ("present", "zero", "partial")
            ):
                var_val = round(actual_f_val - planned_f, 4)
                var_presence = "present"
            elif actual_presence in ("not_captured", "missing", "excluded"):
                var_presence = actual_presence  # type: ignore[assignment]

            recon_state = self._classify_operation_state(
                actual_presence=actual_presence,
                actual_status=actual_status,
                planned_minutes=planned_f,
                actual_minutes=actual_f_val,
                has_active_session=has_active,
            )

            operations.append(
                OperationReconciliationRow(
                    task_id=task_id,
                    task_name=str(task.get("name") or task.get("task_name") or "") or None,
                    planned_status="planned",
                    actual_status=actual_status,
                    planned_minutes=self._pv(
                        planned_f,
                        "present" if planned_f is not None else "missing",
                        unit="min",
                    ),
                    actual_minutes=self._pv(
                        actual_f_val, actual_presence, unit="min", source="sessions"
                    ),
                    variance_minutes=self._pv(var_val, var_presence, unit="min"),
                    planned_quantity=qty_not_captured,
                    actual_quantity=qty_not_captured,
                    quantity_variance=qty_not_captured,
                    reconciliation_state=recon_state,
                    completeness=actual_presence,  # type: ignore[arg-type]
                )
            )

        # Machine variance: planned-only vs not captured
        if machines.items:
            variances.append(
                ReconciliationVariance(
                    dimension="machine_usage",
                    planned_value=len(machines.items),
                    actual_value=None,
                    absolute_variance=None,
                    percentage_variance=None,
                    unit="machines",
                    source="plan_machine_hints",
                    status="not_captured",
                    explanation_code="machine_usage_not_logged",
                    data_completeness="not_captured",
                )
            )

        summary = ReconciliationSummary(
            matched_count=sum(1 for o in operations if o.reconciliation_state == "matched"),
            partial_count=sum(1 for o in operations if o.reconciliation_state == "partial"),
            missing_actual_count=sum(
                1 for o in operations if o.reconciliation_state == "missing_actual"
            ),
            variance_count=sum(1 for o in operations if o.reconciliation_state == "variance"),
            operations_total=len(operations),
        )
        return ReconciliationBlock(
            variances=variances, operations=operations, summary=summary
        )

    def _classify_operation_state(
        self,
        *,
        actual_presence: str,
        actual_status: str | None,
        planned_minutes: float | None,
        actual_minutes: float | None,
        has_active_session: bool,
    ) -> ReconciliationOpState:
        if actual_presence == "not_captured" or actual_status in (None, "assigned"):
            return "missing_actual"
        if has_active_session or actual_status in ("in_progress", "paused", "blocked"):
            return "partial"
        if (
            planned_minutes is not None
            and actual_minutes is not None
            and actual_presence in ("present", "zero", "partial")
            and abs(actual_minutes - planned_minutes) > 1e-6
        ):
            return "variance"
        return "matched"

    def _build_profitability(
        self,
        *,
        baseline: PostJobBaseline,
        labor: LaborActuals,
        materials: MaterialActuals,
        machines: MachineActuals,
        quantity: QuantityActuals,
        has_reality: bool,
    ) -> tuple[ProfitabilityCoverage, list[MissingDataItem]]:
        missing: list[MissingDataItem] = []
        included: list[str] = []
        excluded = ["labor_money", "machine_money"]
        missing_components: list[str] = []

        revenue = baseline.revenue_net
        planned = baseline.planned_internal_cost
        known_mat = materials.known_actual_cost_total

        if known_mat.presence == "present" and isinstance(known_mat.value, (int, float)):
            included.append("materials")
            known_cost_val: float | None = float(known_mat.value)
            known_cost_presence = "present"
        else:
            known_cost_val = None
            known_cost_presence = known_mat.presence
            if materials.deducted_movement_count == 0:
                missing_components.append("materials")
                missing.append(
                    MissingDataItem(
                        code="material_deduction_missing",
                        dimension="materials",
                        message="No stock deduction recorded; material actual cost unknown",
                    )
                )
            else:
                missing_components.append("material_unit_cost")
                missing.append(
                    MissingDataItem(
                        code="material_unit_cost_missing",
                        dimension="materials",
                        message="Deductions exist but inventory unit_cost unavailable",
                    )
                )

        missing_components.append("labor_money")
        missing.append(
            MissingDataItem(
                code="labor_money_excluded",
                dimension="labor",
                message="Labor monetary cost excluded (minutes-only; HR rates not authorized)",
            )
        )
        if machines.completeness == "not_captured":
            missing_components.append("machine_money")
            missing.append(
                MissingDataItem(
                    code="machine_usage_not_captured",
                    dimension="machines",
                    message="Machine/utilaj usage is not logged; machine cost unavailable",
                )
            )
        if quantity.completed_quantity.presence == "not_captured":
            missing.append(
                MissingDataItem(
                    code="produced_quantity_not_captured",
                    dimension="quantity",
                    message="Produced quantity field absent; task completion used instead",
                    blocking_for_complete_profitability=False,
                )
            )
        if labor.open_session_count > 0:
            missing.append(
                MissingDataItem(
                    code="open_work_sessions",
                    dimension="labor",
                    message="Open work sessions remain; closed minutes are incomplete",
                    blocking_for_complete_profitability=True,
                )
            )
        if not has_reality:
            missing.append(
                MissingDataItem(
                    code="execution_reality_missing",
                    dimension="reality",
                    message="Execution reality not recorded",
                )
            )

        margin_val = None
        margin_presence = "missing"
        margin_pct = None
        margin_pct_presence = "missing"
        if (
            revenue.presence == "present"
            and isinstance(revenue.value, (int, float))
            and known_cost_presence == "present"
            and known_cost_val is not None
        ):
            margin_val = round(float(revenue.value) - known_cost_val, 4)
            margin_presence = "present"
            if float(revenue.value) > 0:
                margin_pct = round((margin_val / float(revenue.value)) * 100.0, 4)
                margin_pct_presence = "present"

        # Coverage: never COMPLETE while labor money excluded
        if revenue.presence != "present":
            coverage = "NOT_AVAILABLE"
            profit_status = "NOT_AVAILABLE"
        elif known_cost_presence == "present" and included:
            coverage = "PARTIAL"
            profit_status = "PARTIAL"
        elif has_reality:
            coverage = "INCOMPLETE"
            profit_status = "INCOMPLETE"
        else:
            coverage = "NOT_AVAILABLE"
            profit_status = "NOT_AVAILABLE"

        wording = [
            "Partial profitability — labor monetary cost not included",
            "Cost coverage incomplete until all monetary inputs are known",
            "Do not treat known margin as final profit",
        ]
        if "materials" in included:
            wording.insert(0, "Known actual cost includes materials only")
        if machines.completeness == "not_captured":
            wording.append("Machine cost not available")

        coverage_model = ProfitabilityCoverage(
            revenue_net=revenue,
            planned_internal_cost=planned,
            known_actual_cost=self._pv(
                known_cost_val,
                known_cost_presence,
                unit=baseline.currency,
                source=materials.valuation_method,
            ),
            known_actual_margin=self._pv(
                margin_val,
                margin_presence,
                unit=baseline.currency,
                note="materials_only_known_margin",
            ),
            known_actual_margin_percent=self._pv(
                margin_pct, margin_pct_presence, unit="%", note="materials_only"
            ),
            cost_coverage_status=coverage,  # type: ignore[arg-type]
            profitability_status=profit_status,  # type: ignore[arg-type]
            included_cost_components=included,
            excluded_cost_components=excluded,
            missing_actual_components=sorted(set(missing_components)),
            wording=wording,
            false_final_profit_forbidden=True,
        )
        return coverage_model, missing
