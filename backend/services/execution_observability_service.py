"""
ExecutionObservabilityService — WorkOS Observability v1.

STRICTLY READ-ONLY.

Canonical invariants (non-negotiable):
  - This service NEVER writes to Orders, ExecutionPlan, ExecutionReality.
  - It does NOT call the cost engine, quote orchestrator, or product
    system service.
  - It does NOT read product templates or material rates.
  - It ONLY reads: DivergenceService report + ExecutionObservationConfig.
  - Missing data surfaces explicitly as `UNCONFIRMED`. No silent fallback.

Public API:
  - ObservabilityStatus enum: "OK" | "WARNING" | "CRITICAL" | "UNCONFIRMED"
  - ObservationReport dataclass (plain DTO, no persistence).
  - ExecutionObservabilityService(db).observe(order_id) -> ObservationReport

Classification algorithm (v1):
  1. If config.is_active is False            -> UNCONFIRMED (reason=config_inactive)
  2. If divergence lacks plan OR reality     -> UNCONFIRMED (reason=plan_missing / reality_missing)
  3. If divergence.delta / plan / reality is None -> UNCONFIRMED (reason=data_incomplete)
  4. Compute delta_minutes = |reality - plan|
     Compute delta_pct     = delta_minutes / plan * 100  (plan == 0 handled below)
  5. If delta_minutes >= critical_minutes OR delta_pct >= critical_pct -> CRITICAL
  6. Elif delta_minutes >= warning_minutes OR delta_pct >= warning_pct -> WARNING
  7. Else -> OK

Notes:
  - plan == 0 and reality == 0 -> delta = 0 -> OK (no work, no divergence).
  - plan == 0 and reality > 0  -> delta_pct is undefined; minutes thresholds
    still apply. If minutes thresholds don't trip, we still escalate to
    WARNING because any real work against a zero plan is a surprise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_observation_config import ExecutionObservationConfig
from services.divergence_service import DivergenceService


STATUS_OK = "OK"
STATUS_WARNING = "WARNING"
STATUS_CRITICAL = "CRITICAL"
STATUS_UNCONFIRMED = "UNCONFIRMED"


@dataclass
class ObservationReport:
    order_id: int
    order_code: str
    status: str
    reasons: List[str] = field(default_factory=list)

    has_order: bool = False
    has_plan: bool = False
    has_reality: bool = False

    plan_total_estimated_minutes: Optional[float] = None
    reality_total_actual_minutes: Optional[float] = None
    delta_minutes: Optional[float] = None
    delta_pct: Optional[float] = None

    thresholds: Dict[str, Any] = field(default_factory=dict)

    observed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "order_code": self.order_code,
            "status": self.status,
            "reasons": list(self.reasons),
            "has_order": self.has_order,
            "has_plan": self.has_plan,
            "has_reality": self.has_reality,
            "plan_total_estimated_minutes": self.plan_total_estimated_minutes,
            "reality_total_actual_minutes": self.reality_total_actual_minutes,
            "delta_minutes": self.delta_minutes,
            "delta_pct": self.delta_pct,
            "thresholds": dict(self.thresholds),
            "observed_at": self.observed_at,
        }


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionObservabilityService:
    """Observes Execution Layer. Read-only. No persistence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _load_active_config(self) -> Optional[ExecutionObservationConfig]:
        """Load the active config row (lowest id) if any exists.

        Returns the row when found; returns ``None`` when no config row
        is present at all. This is a pure SELECT. No mutation. No
        creation of defaults here — creating defaults belongs to the
        CRUD router, not observability.
        """
        stmt = select(ExecutionObservationConfig).order_by(
            ExecutionObservationConfig.id.asc()
        )
        res = await self.db.execute(stmt)
        rows = list(res.scalars().all())
        if not rows:
            return None
        # Prefer the first active; else first row overall.
        for r in rows:
            if r.is_active:
                return r
        return rows[0]

    @staticmethod
    def _thresholds_dict(cfg: Optional[ExecutionObservationConfig]) -> Dict[str, Any]:
        if cfg is None:
            return {
                "warning_time_delta_pct": None,
                "critical_time_delta_pct": None,
                "warning_time_delta_minutes": None,
                "critical_time_delta_minutes": None,
                "is_active": False,
                "source": "default_missing",
            }
        return {
            "warning_time_delta_pct": cfg.warning_time_delta_pct,
            "critical_time_delta_pct": cfg.critical_time_delta_pct,
            "warning_time_delta_minutes": cfg.warning_time_delta_minutes,
            "critical_time_delta_minutes": cfg.critical_time_delta_minutes,
            "is_active": cfg.is_active,
            "source": "db",
        }

    async def observe(self, order_id: int) -> ObservationReport:
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError("order_id_invalid")

        divergence = await DivergenceService(self.db).compare(order_id)
        cfg = await self._load_active_config()
        thresholds = self._thresholds_dict(cfg)

        report = ObservationReport(
            order_id=order_id,
            order_code=divergence.order_code,
            status=STATUS_UNCONFIRMED,
            has_order=divergence.has_order,
            has_plan=divergence.has_plan,
            has_reality=divergence.has_reality,
            plan_total_estimated_minutes=divergence.plan_total_estimated_minutes,
            reality_total_actual_minutes=divergence.reality_total_actual_minutes,
            thresholds=thresholds,
            observed_at=_iso_now(),
        )

        # 1. No config / inactive config -> UNCONFIRMED.
        if cfg is None:
            report.reasons.append("config_missing")
            return report
        if not cfg.is_active:
            report.reasons.append("config_inactive")
            return report

        # 2. Missing order/plan/reality -> UNCONFIRMED.
        if not divergence.has_order:
            report.reasons.append("order_missing")
            return report
        if not divergence.has_plan:
            report.reasons.append("plan_missing")
            return report
        if not divergence.has_reality:
            report.reasons.append("reality_missing")
            return report

        plan_mins = divergence.plan_total_estimated_minutes
        real_mins = divergence.reality_total_actual_minutes
        if plan_mins is None or real_mins is None:
            report.reasons.append("data_incomplete")
            return report

        # 3. Classification.
        delta_minutes = round(abs(real_mins - plan_mins), 4)
        report.delta_minutes = delta_minutes

        delta_pct: Optional[float]
        if plan_mins > 0:
            delta_pct = round((delta_minutes / plan_mins) * 100.0, 4)
        else:
            delta_pct = None
        report.delta_pct = delta_pct

        warn_m = cfg.warning_time_delta_minutes
        crit_m = cfg.critical_time_delta_minutes
        warn_p = cfg.warning_time_delta_pct
        crit_p = cfg.critical_time_delta_pct

        is_critical = False
        is_warning = False

        if delta_minutes >= crit_m:
            is_critical = True
            report.reasons.append("minutes_over_critical")
        if delta_pct is not None and delta_pct >= crit_p:
            is_critical = True
            report.reasons.append("pct_over_critical")

        if not is_critical:
            if delta_minutes >= warn_m:
                is_warning = True
                report.reasons.append("minutes_over_warning")
            if delta_pct is not None and delta_pct >= warn_p:
                is_warning = True
                report.reasons.append("pct_over_warning")

        # Edge case: plan_mins == 0 and reality > 0 and minutes thresholds
        # did not fire. Still a surprise — escalate to WARNING with explicit
        # reason so nothing silently classifies as OK.
        if not is_critical and not is_warning:
            if plan_mins == 0 and real_mins > 0:
                is_warning = True
                report.reasons.append("work_against_zero_plan")

        if is_critical:
            report.status = STATUS_CRITICAL
        elif is_warning:
            report.status = STATUS_WARNING
        else:
            report.status = STATUS_OK
            report.reasons.append("within_thresholds")

        return report