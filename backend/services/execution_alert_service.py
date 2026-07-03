"""
ExecutionAlertService — WorkOS Observability v1.

PURE READ-MODEL. NO PERSISTENCE.

Design decision (locked):
  - v1 of alerts is a **computed read-model**, derived on demand from
    an ObservationReport. We deliberately DO NOT persist alerts in v1.
    Rationale:
      1. Keeps the service trivially read-only (no DB writes anywhere).
      2. Avoids schema churn and alert-dedup/ack logic that belong in v2.
      3. Guarantees no side-effects on Order / Plan / Reality / any table.
      4. Passes the strictest grep-based audit (`commit|add|insert|update|delete`)
         with ZERO hits.
  - v1 of alerts DOES NOT send any external notification (no email, no SMS,
    no webhook). That is explicitly out of scope for Sprint #11.

Alert shape (stable contract):
    {
      "order_id":        int,
      "order_code":      str,
      "severity":        "WARNING" | "CRITICAL",
      "reason":          str,              # short machine code
      "metric":          str,              # e.g. "time_minutes"
      "expected_value":  float | None,     # plan figure
      "actual_value":    float | None,     # reality figure
      "delta":           float | None,     # actual - expected
      "created_at":      ISO-8601 UTC str
    }

Rules:
  - If observation.status is OK or UNCONFIRMED -> empty list.
  - If WARNING or CRITICAL -> exactly one alert per triggering metric.
    In v1 we only classify on `time_minutes`, so at most one alert per order.
  - No writes. No reads of Order / Plan / Reality directly — everything
    comes from the ObservationReport that was passed in.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from services.execution_observability_service import (
    ObservationReport,
    STATUS_CRITICAL,
    STATUS_WARNING,
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionAlertService:
    """Derives alert read-models from an ObservationReport.

    No constructor dependencies. No DB. No I/O.
    """

    def build_alerts(self, observation: ObservationReport) -> List[Dict[str, Any]]:
        if observation is None:
            raise ValueError("observation_required")
        if observation.status not in (STATUS_WARNING, STATUS_CRITICAL):
            return []

        plan = observation.plan_total_estimated_minutes
        actual = observation.reality_total_actual_minutes
        delta: Any = None
        if plan is not None and actual is not None:
            delta = round(actual - plan, 4)

        # Pick the most specific reason; keep the full list too.
        reason_code = self._pick_reason(observation.reasons)

        alert = {
            "order_id": observation.order_id,
            "order_code": observation.order_code,
            "severity": observation.status,
            "reason": reason_code,
            "reasons_all": list(observation.reasons),
            "metric": "time_minutes",
            "expected_value": plan,
            "actual_value": actual,
            "delta": delta,
            "created_at": _iso_now(),
        }
        return [alert]

    @staticmethod
    def _pick_reason(reasons: List[str]) -> str:
        # Prefer critical reasons, then warning reasons, then fallbacks.
        priority = (
            "minutes_over_critical",
            "pct_over_critical",
            "minutes_over_warning",
            "pct_over_warning",
            "work_against_zero_plan",
        )
        for code in priority:
            if code in reasons:
                return code
        return "unclassified"