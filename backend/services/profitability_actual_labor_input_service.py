"""Profitability Actual Labor Input — factual closed-session provenance (minutes only).

Derives from Execution Reality sessions written by controlled_task_session_service.
No monetary rates. No new persistence. No MachineRun double-count.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.execution_plan_task_parser import (
    operational_tasks_only,
    parse_tasks_json_raw,
)
from services.task_work_session_service import (
    compute_duration_minutes,
    is_session_active,
)

LABOR_INPUT_CONTRACT = "profitability_actual_labor_input/v1"
DURATION_SOURCE = "ended_at_minus_started_at"
CANONICAL_DURATION_UNIT = "minutes"
# Minutes use existing compute_duration_minutes: int(round(total_seconds / 60)).
# Python round uses banker's rounding (half-to-even): 30s → 0 min, 90s → 2 min.
ROUNDING_RULE = "python_round_half_to_even_seconds_over_60_to_int_minutes"


def _normalize_employee_id(raw: Any) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _parse_reality_tasks(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    import json

    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _duration_seconds(started_at: str, ended_at: str) -> int | None:
    from datetime import datetime

    try:
        start = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(ended_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    if end < start:
        return None
    return max(0, int((end - start).total_seconds()))


def _assert_operational_materialized(plan: ExecutionPlan) -> None:
    parsed = parse_tasks_json_raw(plan.tasks_json)
    if parsed.format == "v2_envelope" and parsed.operational_tasks:
        return
    if parsed.format == "legacy_list" and parsed.operational_tasks:
        return
    raise HTTPException(status_code=422, detail={"error": "v2_not_materialized"})


async def build_profitability_actual_labor_input(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str | None = None,
) -> dict[str, Any]:
    """Canonical factual labor input for Profitability (time provenance only).

    CLOSED sessions contribute to finals. ACTIVE sessions are listed but excluded
    from totals. Employee-minutes sum across concurrent employees (no wall-clock
    dedupe). MachineRun runtime is never included.
    """
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "plan_not_found"})
    _assert_operational_materialized(plan)

    reality = (
        await db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
    ).scalar_one_or_none()
    sessions_all = _parse_reality_tasks(reality.tasks_json if reality else None)

    closed_sessions: list[dict[str, Any]] = []
    active_sessions: list[dict[str, Any]] = []
    invalid_sessions: list[dict[str, Any]] = []
    by_task: dict[str, dict[str, Any]] = {}
    by_employee_task: dict[tuple[int, str], dict[str, Any]] = {}

    ops = [
        t
        for t in operational_tasks_only(plan.tasks_json)
        if isinstance(t, dict) and (not task_id or str(t.get("task_id") or "") == task_id)
    ]
    op_ids = {str(t.get("task_id") or "") for t in ops}

    for task in ops:
        tid = str(task.get("task_id") or "")
        by_task[tid] = {
            "task_id": tid,
            "workcenter": task.get("workcenter"),
            "planned_minutes": task.get("estimated_time_minutes"),
            "closed_session_count": 0,
            "active_session_count": 0,
            "total_employee_minutes": 0,
            "total_employee_seconds": 0,
        }

    for entry in sessions_all:
        if not isinstance(entry, dict):
            continue
        tid = str(entry.get("task_id") or "")
        if task_id and tid != task_id:
            continue
        if tid not in op_ids:
            # Orphan reality row not on operational plan — fail closed (exclude).
            invalid_sessions.append(
                {
                    "session_id": entry.get("session_id"),
                    "task_id": tid,
                    "reason": "task_not_on_operational_plan",
                }
            )
            continue

        emp_id = _normalize_employee_id(entry.get("employee_id"))
        started = str(entry.get("started_at") or "")
        ended = str(entry.get("ended_at") or "") if entry.get("ended_at") else ""
        sid = str(entry.get("session_id") or "").strip() or None

        if is_session_active(entry):
            active_sessions.append(
                {
                    "session_id": sid,
                    "task_id": tid,
                    "employee_id": emp_id,
                    "started_at": started or None,
                    "status": "active",
                    "contribution": "not_final",
                }
            )
            if tid in by_task:
                by_task[tid]["active_session_count"] += 1
            continue

        if not ended or not started:
            invalid_sessions.append(
                {
                    "session_id": sid,
                    "task_id": tid,
                    "reason": "missing_timestamps",
                }
            )
            continue
        if emp_id is None:
            invalid_sessions.append(
                {
                    "session_id": sid,
                    "task_id": tid,
                    "reason": "missing_employee",
                }
            )
            continue

        seconds = _duration_seconds(started, ended)
        if seconds is None:
            invalid_sessions.append(
                {
                    "session_id": sid,
                    "task_id": tid,
                    "employee_id": emp_id,
                    "reason": "ended_before_started_or_unparseable",
                }
            )
            continue

        minutes = entry.get("duration_minutes")
        if minutes is None:
            minutes = compute_duration_minutes(started, ended)
        try:
            minutes_i = int(minutes)
        except (TypeError, ValueError):
            minutes_i = compute_duration_minutes(started, ended)

        rec = {
            "session_id": sid,
            "order_id": order_id,
            "execution_plan_id": plan.id,
            "task_id": tid,
            "employee_id": emp_id,
            "started_at": started,
            "ended_at": ended,
            "actual_duration_seconds": seconds,
            "actual_duration_minutes": minutes_i,
            "status": str(entry.get("status") or "ended"),
            "role": entry.get("role"),
            "session_type": entry.get("session_type"),
            "source": entry.get("source"),
            "workcenter": by_task.get(tid, {}).get("workcenter"),
            "contribution": "final_closed",
            "duration_source": DURATION_SOURCE,
        }
        closed_sessions.append(rec)
        by_task[tid]["closed_session_count"] += 1
        by_task[tid]["total_employee_minutes"] += minutes_i
        by_task[tid]["total_employee_seconds"] += seconds
        key = (emp_id, tid)
        if key not in by_employee_task:
            by_employee_task[key] = {
                "employee_id": emp_id,
                "task_id": tid,
                "session_count": 0,
                "total_employee_minutes": 0,
                "total_employee_seconds": 0,
            }
        by_employee_task[key]["session_count"] += 1
        by_employee_task[key]["total_employee_minutes"] += minutes_i
        by_employee_task[key]["total_employee_seconds"] += seconds

    total_minutes = sum(int(s["actual_duration_minutes"]) for s in closed_sessions)
    total_seconds = sum(int(s["actual_duration_seconds"]) for s in closed_sessions)

    return {
        "contract": LABOR_INPUT_CONTRACT,
        "status": "ok",
        "order_id": order_id,
        "execution_plan_id": plan.id,
        "write_authority": "controlled_task_session_service",
        "duration_source": DURATION_SOURCE,
        "canonical_duration_unit": CANONICAL_DURATION_UNIT,
        "rounding_rule": ROUNDING_RULE,
        "closed_sessions": closed_sessions,
        "active_sessions": active_sessions,
        "invalid_sessions": invalid_sessions,
        "by_employee_task": list(by_employee_task.values()),
        "by_task": list(by_task.values()),
        "totals": {
            "closed_session_count": len(closed_sessions),
            "active_session_count": len(active_sessions),
            "invalid_session_count": len(invalid_sessions),
            "total_employee_minutes": total_minutes,
            "total_employee_seconds": total_seconds,
        },
        "machine_run_included": False,
        "planned_minutes_mutated": False,
        "monetary_rates_included": False,
        "commercial_mutated": False,
    }
