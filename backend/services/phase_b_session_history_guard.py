"""Phase B session / execution-history fail-closed guard.

Owner policy: ANY_SESSION_OR_EXECUTION_HISTORY_BLOCKS.

Canonical sources in this repo (factual):
- ``execution_reality.tasks_json`` — controlled sessions live here (no separate Session ORM)
- ``actual_labor_cost_lines`` — frozen labor actuals keyed by order_id + task_id

Not task-linked (documented NOT_APPLICABLE for this guard):
- ``employee_attendance_events`` / attendance effects (employee-day, not task)

Query failure → fail closed (treat as history present).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.actual_cost_policy import ActualLaborCostLine
from models.execution_reality import ExecutionReality

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SessionHistoryProbe:
    has_history: bool
    sources: tuple[str, ...]
    detail: Optional[str] = None
    fail_closed_error: bool = False


def _reality_task_entries(raw: Optional[str], task_id: str) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        raise ValueError("execution_reality_tasks_json_unreadable")
    if not isinstance(parsed, list):
        raise ValueError("execution_reality_tasks_json_not_list")
    out: list[dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            # Inconsistent row → fail closed at caller
            raise ValueError("execution_reality_entry_not_object")
        if str(item.get("task_id") or "") == task_id:
            out.append(item)
    return out


def reality_entry_counts_as_history(entry: dict[str, Any]) -> bool:
    """Any reality row for the task is history — including null started_at.

    Presence of the task entry itself is execution evidence. Also treat
    session_id / ended_at / duration / employee_id markers as history.
    """
    if entry.get("started_at"):
        return True
    if entry.get("ended_at"):
        return True
    if entry.get("session_id"):
        return True
    if entry.get("stopped_at") or entry.get("completed_at"):
        return True
    # Row exists for this task_id even with null timestamps → historical evidence.
    return True


async def probe_task_execution_history(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
) -> SessionHistoryProbe:
    """Return whether any canonical execution history exists for the task."""
    sources: list[str] = []
    tid = (task_id or "").strip()
    if not tid:
        return SessionHistoryProbe(
            has_history=True,
            sources=("invalid_task_identity",),
            detail="empty_task_id",
            fail_closed_error=True,
        )

    try:
        reality = (
            await db.execute(
                select(ExecutionReality).where(ExecutionReality.order_id == order_id)
            )
        ).scalar_one_or_none()
        if reality is not None:
            try:
                entries = _reality_task_entries(reality.tasks_json, tid)
            except ValueError as exc:
                return SessionHistoryProbe(
                    has_history=True,
                    sources=("execution_reality_inconsistent",),
                    detail=str(exc),
                    fail_closed_error=True,
                )
            for entry in entries:
                if reality_entry_counts_as_history(entry):
                    sources.append("execution_reality")
                    break

        actual_count = (
            await db.execute(
                select(ActualLaborCostLine.id)
                .where(
                    ActualLaborCostLine.order_id == order_id,
                    ActualLaborCostLine.task_id == tid,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if actual_count is not None:
            sources.append("actual_labor_cost_lines")

        # Sanity probe: ensure DB connection still readable (fail closed on error).
        await db.execute(text("SELECT 1"))

    except Exception as exc:  # noqa: BLE001 — fail closed
        logger.warning(
            "session_history_probe_failed order_id=%s task_id=%s err=%s",
            order_id,
            tid,
            type(exc).__name__,
        )
        return SessionHistoryProbe(
            has_history=True,
            sources=("probe_query_failure",),
            detail=type(exc).__name__,
            fail_closed_error=True,
        )

    # Attendance is not task-scoped in this repo — documented NOT_APPLICABLE.
    return SessionHistoryProbe(
        has_history=bool(sources),
        sources=tuple(sources),
        detail=None if sources else "no_history",
    )
