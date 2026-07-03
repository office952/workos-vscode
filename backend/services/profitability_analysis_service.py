"""
ProfitabilityAnalysisService — Step 10.2 read-only order profitability.

READ-ONLY. NEVER MUTATES Order, Quote, ExecutionReality, or sessions.
Does NOT import CostEngine, QuoteOrchestrator, or /price paths.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.profitability_analysis import (
    ProfitabilityAnalysisResponse,
    ProfitabilityStatus,
    ProfitabilityVariance,
    RevenueSource,
)

WARNING_BATCH_PUT_WATCH = "order_mutability_guard_batch_watch"
WARNING_EXECUTION_REALITY_MISSING = "execution_reality_missing"
WARNING_ESTIMATED_INTERNAL_MISSING = "estimated_internal_total_missing"
WARNING_ACTUAL_COSTING_NOT_AVAILABLE = "actual_costing_not_available"
WARNING_LEGACY_WITHOUT_V2 = "legacy_order_without_snapshot_v2"
WARNING_ACTUAL_MATERIAL_COST_MISSING = "actual_material_cost_missing"
WARNING_HR_LABOR_COST_MISSING = "hr_labor_cost_missing"


class OrderNotFoundError(LookupError):
    """Raised when order_id does not exist."""


class ProfitabilityAnalysisService:
    """Build read-only profitability analysis from frozen order + actuals."""

    def __init__(self, db: AsyncSession):
        self.db = db

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
    def _margin_amount(commercial: float | None, cost: float | None) -> float | None:
        if commercial is None or cost is None:
            return None
        return round(commercial - cost, 4)

    @staticmethod
    def _margin_percent(commercial: float | None, margin_amount: float | None) -> float | None:
        if commercial is None or margin_amount is None or commercial <= 0:
            return None
        return round((margin_amount / commercial) * 100.0, 4)

    @staticmethod
    def _materials_observation_count(reality: ExecutionReality | None) -> int:
        if reality is None:
            return 0
        raw = reality.materials_json
        if not raw:
            return 0
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return 0
        if not isinstance(data, list):
            return 0
        return len([item for item in data if isinstance(item, dict)])

    async def analyze_order(self, order_id: int) -> ProfitabilityAnalysisResponse:
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError("order_id_invalid")

        order = await self._load_order(order_id)
        if order is None:
            raise OrderNotFoundError(f"order_not_found:{order_id}")

        snapshot_v2 = self._parse_snapshot_v2(order)
        has_snapshot_v2 = snapshot_v2 is not None
        warnings: list[str] = [WARNING_BATCH_PUT_WATCH]

        revenue_source: RevenueSource
        accepted_commercial_total: float | None
        accepted_currency: str | None = None
        estimated_internal_total: float | None = None

        if snapshot_v2 is not None:
            revenue_source = "order_snapshot_v2"
            accepted_commercial_total = snapshot_v2.accepted_commercial_total
            accepted_currency = snapshot_v2.accepted_currency
            estimated_internal_total = snapshot_v2.estimated_internal_total
            if estimated_internal_total is None:
                warnings.append(WARNING_ESTIMATED_INTERNAL_MISSING)
        elif order.total_amount is not None:
            revenue_source = "order.total_amount"
            accepted_commercial_total = float(order.total_amount)
            warnings.append(WARNING_LEGACY_WITHOUT_V2)
        else:
            revenue_source = "missing"
            accepted_commercial_total = None

        plan = await self._load_plan(order_id)
        reality = await self._load_reality(order_id)
        has_execution_reality = reality is not None

        actual_labor_minutes: float | None = None
        if reality is not None:
            actual_labor_minutes = float(reality.total_actual_time_minutes)
            if self._materials_observation_count(reality) > 0:
                warnings.append(WARNING_ACTUAL_MATERIAL_COST_MISSING)
        else:
            warnings.append(WARNING_EXECUTION_REALITY_MISSING)

        actual_total_cost: float | None = None
        actual_materials_total: float | None = None
        warnings.append(WARNING_ACTUAL_COSTING_NOT_AVAILABLE)
        warnings.append(WARNING_HR_LABOR_COST_MISSING)

        estimated_margin_amount = self._margin_amount(
            accepted_commercial_total, estimated_internal_total
        )
        estimated_margin_percent = self._margin_percent(
            accepted_commercial_total, estimated_margin_amount
        )

        actual_margin_amount: float | None = None
        actual_margin_percent: float | None = None

        minutes_delta: float | None = None
        if plan is not None and actual_labor_minutes is not None:
            plan_minutes = float(plan.total_estimated_time_minutes)
            minutes_delta = round(actual_labor_minutes - plan_minutes, 4)

        variance = ProfitabilityVariance(
            cost_delta=None,
            minutes_delta=minutes_delta,
        )

        profitability_status = self._resolve_status(
            has_snapshot_v2=has_snapshot_v2,
            revenue_source=revenue_source,
            has_execution_reality=has_execution_reality,
            actual_total_cost=actual_total_cost,
        )

        return ProfitabilityAnalysisResponse(
            order_id=order.id,
            order_code=order.code,
            snapshot_version=getattr(order, "snapshot_version", None),
            has_snapshot_v2=has_snapshot_v2,
            revenue_source=revenue_source,
            accepted_commercial_total=accepted_commercial_total,
            accepted_currency=accepted_currency,
            estimated_internal_total=estimated_internal_total,
            has_execution_reality=has_execution_reality,
            actual_total_cost=actual_total_cost,
            actual_labor_minutes=actual_labor_minutes,
            actual_materials_total=actual_materials_total,
            estimated_margin_amount=estimated_margin_amount,
            estimated_margin_percent=estimated_margin_percent,
            actual_margin_amount=actual_margin_amount,
            actual_margin_percent=actual_margin_percent,
            variance_estimated_vs_actual=variance,
            profitability_status=profitability_status,
            warnings=sorted(set(warnings)),
            retroactive_change_allowed=False,
            write_back_performed=False,
        )

    @staticmethod
    def _resolve_status(
        *,
        has_snapshot_v2: bool,
        revenue_source: RevenueSource,
        has_execution_reality: bool,
        actual_total_cost: float | None,
    ) -> ProfitabilityStatus:
        if revenue_source == "missing" and not has_snapshot_v2:
            return "missing_snapshot"
        if revenue_source == "order.total_amount" and not has_snapshot_v2:
            return "unsupported_legacy_order"
        if has_execution_reality:
            if actual_total_cost is not None:
                return "actuals_available"
            return "actuals_partial"
        return "estimated_only"
