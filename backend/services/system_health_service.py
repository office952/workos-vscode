"""
SystemHealthService — WorkOS Sprint #40.

STRICTLY READ-ONLY. This service NEVER writes to any business table.

Aggregates a handful of lightweight health signals for the operator:

  1. database               — DB connection ping (SELECT 1).
  2. version                — Reuses /api/v1/system/version resolver
                              (Sprint #38), no duplicated logic.
  3. seed_pipeline          — `scripts.seed_sync_all` importable and
                              exposes `run_all_seeds` callable. Never
                              executes any seed.
  4. observation_thresholds — ExecutionObservationConfig has an active
                              row with non-null thresholds (Sprint #37
                              invariant).
  5. execution_anchor_order_14
                            — Sprint #33 canonical anchor: order 14
                              exists, has a plan, has a reality, and its
                              observability status classifies.

Aggregate rules (as specified in Sprint #40):
  - Any check == "fail"               -> aggregate "fail".
  - Else any check in {"warning","unknown"} -> aggregate "warning".
  - Else                              -> aggregate "ok".

Unverifiable signals MUST surface as `status="unknown"` with an explicit
`reason` string. Never fabricate `ok`.
"""

from __future__ import annotations

import importlib
import os
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_observation_config import ExecutionObservationConfig
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from services.execution_observability_service import ExecutionObservabilityService


STATUS_OK = "ok"
STATUS_WARNING = "warning"
STATUS_FAIL = "fail"
STATUS_UNKNOWN = "unknown"
PUBLIC_SERVICE_NAME = "workos"

ANCHOR_ORDER_ID = 14


def _observation_thresholds_required() -> bool:
    raw_flag = os.getenv("WORKOS_REQUIRE_OBSERVATION_THRESHOLDS")
    if raw_flag is not None:
        return raw_flag.strip().lower() in ("1", "true", "yes", "on")
    return True


def _iso_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_check() -> Dict[str, Any]:
    return {"status": STATUS_UNKNOWN, "details": {}}


class SystemHealthService:
    """Pure read-only aggregator of system-level health signals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # 1. Database
    # ------------------------------------------------------------------
    async def _check_database(self) -> Dict[str, Any]:
        check: Dict[str, Any] = _empty_check()
        try:
            res = await self.db.execute(text("SELECT 1"))
            val = res.scalar()
            if val == 1:
                check["status"] = STATUS_OK
                check["details"] = {"ping": "SELECT 1", "result": 1}
            else:
                check["status"] = STATUS_FAIL
                check["details"] = {"reason": "unexpected_ping_result", "result": val}
        except Exception as exc:  # pragma: no cover - defensive
            check["status"] = STATUS_FAIL
            check["details"] = {
                "reason": "db_ping_exception",
                "exception_type": type(exc).__name__,
            }
        return check

    # ------------------------------------------------------------------
    # 2. Version — reuse Sprint #38 resolver
    # ------------------------------------------------------------------
    @staticmethod
    def _check_version() -> Dict[str, Any]:
        check: Dict[str, Any] = _empty_check()
        try:
            # Import lazily so tests can patch the router module cleanly.
            from routers.system import resolve_version_payload

            payload = resolve_version_payload()
            details = {
                "app_name": payload.get("app_name"),
                "release_version": payload.get("release_version"),
                "environment": payload.get("environment"),
                "release_scope": payload.get("release_scope"),
                "source": payload.get("source"),
            }
            check["details"] = details

            # ok requires a resolvable non-unknown source plus concrete payload.
            if details["source"] != "unknown" and (
                details["release_version"] or details["app_name"]
            ):
                check["status"] = STATUS_OK
            elif details["source"] == "unknown":
                check["status"] = STATUS_WARNING
                details["reason"] = "version_source_unknown"
            else:
                check["status"] = STATUS_WARNING
                details["reason"] = "version_partial"
        except Exception as exc:
            check["status"] = STATUS_FAIL
            check["details"] = {
                "reason": "version_resolver_exception",
                "exception_type": type(exc).__name__,
            }
        return check

    # ------------------------------------------------------------------
    # 3. Seed pipeline — import-only, never execute
    # ------------------------------------------------------------------
    @staticmethod
    def _check_seed_pipeline() -> Dict[str, Any]:
        check: Dict[str, Any] = _empty_check()
        try:
            mod = importlib.import_module("scripts.seed_sync_all")
            run_all = getattr(mod, "run_all_seeds", None)
            importable = callable(run_all)
            check["details"] = {
                "seed_sync_all_importable": bool(importable),
                "has_run_all_seeds_callable": bool(importable),
            }
            check["status"] = STATUS_OK if importable else STATUS_FAIL
            if not importable:
                check["details"]["reason"] = "run_all_seeds_not_callable"
        except Exception as exc:
            check["status"] = STATUS_FAIL
            check["details"] = {
                "seed_sync_all_importable": False,
                "reason": "seed_sync_all_import_failed",
                "exception_type": type(exc).__name__,
            }
        return check

    # ------------------------------------------------------------------
    # 4. Observation thresholds (Sprint #37 invariant)
    # ------------------------------------------------------------------
    async def _check_observation_thresholds(self) -> Dict[str, Any]:
        check: Dict[str, Any] = _empty_check()
        try:
            stmt = select(ExecutionObservationConfig).order_by(
                ExecutionObservationConfig.id.asc()
            )
            res = await self.db.execute(stmt)
            rows = list(res.scalars().all())
        except Exception as exc:
            check["status"] = STATUS_FAIL
            check["details"] = {
                "reason": "observation_config_query_failed",
                "exception_type": type(exc).__name__,
            }
            return check

        if not rows:
            required = _observation_thresholds_required()
            check["status"] = STATUS_FAIL if required else STATUS_WARNING
            check["details"] = {
                "reason": "no_observation_config_rows",
                "required": required,
            }
            return check

        # Prefer active row; fall back to first row.
        active = next((r for r in rows if r.is_active), None)
        cfg = active if active is not None else rows[0]

        details = {
            "is_active": bool(cfg.is_active),
            "warning_threshold_pct": cfg.warning_time_delta_pct,
            "critical_threshold_pct": cfg.critical_time_delta_pct,
            "warning_threshold_minutes": cfg.warning_time_delta_minutes,
            "critical_threshold_minutes": cfg.critical_time_delta_minutes,
            "active_row_id": cfg.id,
        }
        check["details"] = details

        missing = [
            k
            for k in (
                "warning_threshold_pct",
                "critical_threshold_pct",
                "warning_threshold_minutes",
                "critical_threshold_minutes",
            )
            if details[k] is None
        ]
        if missing:
            required = _observation_thresholds_required()
            check["status"] = STATUS_FAIL if required else STATUS_WARNING
            details["reason"] = "missing_thresholds"
            details["missing_fields"] = missing
            details["required"] = required
            return check

        if not details["is_active"]:
            check["status"] = STATUS_WARNING
            details["reason"] = "observation_config_inactive"
            return check

        check["status"] = STATUS_OK
        return check

    # ------------------------------------------------------------------
    # 5. Execution anchor order (Sprint #33 invariant)
    # ------------------------------------------------------------------
    async def _check_execution_anchor(self) -> Dict[str, Any]:
        check: Dict[str, Any] = _empty_check()
        details: Dict[str, Any] = {
            "order_id": ANCHOR_ORDER_ID,
            "order_exists": False,
            "has_plan": False,
            "has_reality": False,
            "observability_status": None,
        }
        check["details"] = details

        try:
            order = (
                await self.db.execute(
                    select(Orders).where(Orders.id == ANCHOR_ORDER_ID)
                )
            ).scalar_one_or_none()
        except Exception as exc:
            check["status"] = STATUS_FAIL
            details["reason"] = "order_query_failed"
            details["exception_type"] = type(exc).__name__
            return check

        if order is None:
            check["status"] = STATUS_WARNING
            details["reason"] = "anchor_order_missing"
            return check

        details["order_exists"] = True

        try:
            plan = (
                await self.db.execute(
                    select(ExecutionPlan).where(
                        ExecutionPlan.order_id == ANCHOR_ORDER_ID
                    )
                )
            ).scalar_one_or_none()
            reality = (
                await self.db.execute(
                    select(ExecutionReality).where(
                        ExecutionReality.order_id == ANCHOR_ORDER_ID
                    )
                )
            ).scalar_one_or_none()
        except Exception as exc:
            check["status"] = STATUS_FAIL
            details["reason"] = "plan_or_reality_query_failed"
            details["exception_type"] = type(exc).__name__
            return check

        details["has_plan"] = plan is not None
        details["has_reality"] = reality is not None

        # Observability call is fully non-destructive.
        try:
            report = await ExecutionObservabilityService(self.db).observe(
                ANCHOR_ORDER_ID
            )
            details["observability_status"] = report.status
        except Exception as exc:
            details["observability_status"] = None
            details["observability_error"] = {
                "exception_type": type(exc).__name__,
            }

        if not details["has_plan"] or not details["has_reality"]:
            check["status"] = STATUS_WARNING
            details.setdefault(
                "reason",
                "anchor_incomplete_plan_or_reality_missing",
            )
            return check

        obs_status = details["observability_status"]
        if obs_status == "OK":
            check["status"] = STATUS_OK
        elif obs_status in ("WARNING", "UNCONFIRMED"):
            check["status"] = STATUS_WARNING
            details["reason"] = f"observability_{obs_status.lower()}"
        elif obs_status == "CRITICAL":
            check["status"] = STATUS_FAIL
            details["reason"] = "observability_critical"
        else:
            check["status"] = STATUS_UNKNOWN
            details["reason"] = "observability_status_unknown"

        return check

    # ------------------------------------------------------------------
    # Aggregate
    # ------------------------------------------------------------------
    @staticmethod
    def _aggregate(checks: Dict[str, Dict[str, Any]]) -> str:
        statuses = [c.get("status", STATUS_UNKNOWN) for c in checks.values()]
        if any(s == STATUS_FAIL for s in statuses):
            return STATUS_FAIL
        if any(s in (STATUS_WARNING, STATUS_UNKNOWN) for s in statuses):
            return STATUS_WARNING
        return STATUS_OK

    async def run_diagnostics(self) -> Dict[str, Any]:
        """Execute all checks and return the diagnostics payload."""
        checks: Dict[str, Dict[str, Any]] = {
            "database": await self._check_database(),
            "version": self._check_version(),
            "seed_pipeline": self._check_seed_pipeline(),
            "observation_thresholds": await self._check_observation_thresholds(),
            "execution_anchor_order_14": await self._check_execution_anchor(),
        }
        return {
            "status": self._aggregate(checks),
            "checks": checks,
            "generated_at": _iso_now_utc(),
        }

    async def run_public_health(self) -> Dict[str, Any]:
        """Return a minimal public health response with no sensitive details.

        Public aggregate status is driven by the **database** check only.
        Optional diagnostics probes (e.g. execution_anchor_order_14) must not
        paint the operator chrome as "necesită verificare" while Live DB
        surfaces are healthy. Full check detail remains on /diagnostics.
        """
        diagnostics = await self.run_diagnostics()
        checks = diagnostics.get("checks") or {}
        db_status = (checks.get("database") or {}).get("status", STATUS_UNKNOWN)
        if db_status == STATUS_OK:
            public_status = STATUS_OK
        elif db_status == STATUS_FAIL:
            public_status = STATUS_FAIL
        elif db_status == STATUS_WARNING:
            public_status = STATUS_WARNING
        else:
            public_status = STATUS_UNKNOWN
        return {
            "status": public_status,
            "service": PUBLIC_SERVICE_NAME,
            "generated_at": diagnostics.get("generated_at", _iso_now_utc()),
            # Keep the key for frontend compatibility without exposing internals.
            "checks": {},
        }

    async def run(self) -> Dict[str, Any]:
        """Backward-compatible alias for diagnostics payload."""
        return await self.run_diagnostics()