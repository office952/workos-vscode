"""ProfitabilityAnalysis read-only response schema (Step 10.2)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ProfitabilityStatus = Literal[
    "estimated_only",
    "actuals_partial",
    "actuals_available",
    "missing_snapshot",
    "unsupported_legacy_order",
]

RevenueSource = Literal[
    "order_snapshot_v2",
    "order.total_amount",
    "missing",
]


class ProfitabilityVariance(BaseModel):
    """Estimated vs actual variance — partial fields null in MVP."""

    cost_delta: float | None = None
    minutes_delta: float | None = None


class ProfitabilityAnalysisResponse(BaseModel):
    """Read-only profitability analysis for a single order."""

    order_id: int
    order_code: str
    snapshot_version: int | None = None
    has_snapshot_v2: bool
    revenue_source: RevenueSource
    accepted_commercial_total: float | None = None
    accepted_currency: str | None = None
    estimated_internal_total: float | None = None
    has_execution_reality: bool
    actual_total_cost: float | None = None
    actual_labor_minutes: float | None = None
    actual_materials_total: float | None = None
    estimated_margin_amount: float | None = None
    estimated_margin_percent: float | None = None
    actual_margin_amount: float | None = None
    actual_margin_percent: float | None = None
    variance_estimated_vs_actual: ProfitabilityVariance | None = None
    profitability_status: ProfitabilityStatus
    warnings: list[str] = Field(default_factory=list)
    retroactive_change_allowed: bool = False
    write_back_performed: bool = False
