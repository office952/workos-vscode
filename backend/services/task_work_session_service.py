"""Work session model helpers for execution_reality.tasks_json — multi-participant tasks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

ROLE_PRIMARY = "primary"
ROLE_HELPER = "helper"
SESSION_TYPE_WORK = "work"
SESSION_TYPE_ASSIST = "assist"
SESSION_STATUS_IN_PROGRESS = "in_progress"
SESSION_STATUS_ENDED = "ended"
SESSION_STATUS_COMPLETED = "completed"
SESSION_STATUS_BLOCKED = "blocked"


def new_session_id() -> str:
    return f"ws-{uuid.uuid4().hex[:12]}"


def _parse_dt(raw: Any) -> Optional[datetime]:
    if raw is None:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def sessions_for_task(tasks: List[Dict[str, Any]], task_id: str) -> List[Dict[str, Any]]:
    return [
        entry
        for entry in tasks
        if isinstance(entry, dict) and str(entry.get("task_id") or "") == task_id
    ]


def ensure_session_id(entry: Dict[str, Any]) -> str:
    existing = str(entry.get("session_id") or "").strip()
    if existing:
        return existing
    task_id = str(entry.get("task_id") or "task")
    employee_id = entry.get("employee_id") or "0"
    started = str(entry.get("started_at") or "legacy")
    return f"legacy-{task_id}-{employee_id}-{started}"


def is_session_active(entry: Dict[str, Any]) -> bool:
    if entry.get("ended_at"):
        return False
    return bool(entry.get("started_at"))


def compute_duration_minutes(started_at: str, ended_at: str) -> int:
    start = _parse_dt(started_at)
    end = _parse_dt(ended_at)
    if start is None or end is None or end < start:
        return 0
    return max(0, int(round((end - start).total_seconds() / 60.0)))


def _session_runtime_status(entry: Dict[str, Any]) -> str:
    if not is_session_active(entry):
        return "done" if entry.get("ended_at") else "assigned"
    if entry.get("blocked_at") and not entry.get("unblocked_at"):
        return "blocked"
    if entry.get("paused_at") and not entry.get("resumed_at"):
        return "paused"
    return "in_progress"


def derive_task_status_from_sessions(sessions: List[Dict[str, Any]]) -> str:
    """Global task status — done only when no active sessions remain."""
    if not sessions:
        return "assigned"

    active_sessions = [entry for entry in sessions if is_session_active(entry)]
    if not active_sessions:
        if any(entry.get("ended_at") for entry in sessions):
            return "done"
        return "assigned"

    for entry in active_sessions:
        if entry.get("paused_at") and not entry.get("resumed_at"):
            return "paused"

    for entry in active_sessions:
        if entry.get("blocked_at") and not entry.get("unblocked_at"):
            return "blocked"

    return "in_progress"


def derive_task_status_for_employee(
    sessions: List[Dict[str, Any]],
    employee_id: int,
) -> str:
    """Self-only mobile view — prefer the authenticated employee's active session."""
    my_active = active_session_for_employee(sessions, employee_id)
    if my_active:
        return _session_runtime_status(my_active)

    for entry in sessions:
        try:
            entry_employee = int(entry.get("employee_id") or 0)
        except (TypeError, ValueError):
            continue
        if entry_employee != employee_id:
            continue
        if entry.get("ended_at") and entry.get("completed_by_employee_id"):
            return "done"

    return derive_task_status_from_sessions(sessions)


def merge_reality_fields_for_task(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Legacy-compatible merged view for a task (latest active, else latest closed)."""
    if not sessions:
        return {}
    active = [entry for entry in sessions if is_session_active(entry)]
    if active:
        return max(active, key=lambda item: str(item.get("started_at") or ""))
    closed = [entry for entry in sessions if entry.get("ended_at")]
    if closed:
        return max(closed, key=lambda item: str(item.get("ended_at") or ""))
    return sessions[-1]


def active_session_for_employee(
    sessions: List[Dict[str, Any]],
    employee_id: int,
) -> Optional[Dict[str, Any]]:
    for entry in sessions:
        try:
            entry_employee = int(entry.get("employee_id") or 0)
        except (TypeError, ValueError):
            continue
        if entry_employee == employee_id and is_session_active(entry):
            return entry
    return None


def has_active_session_for_employee(
    tasks: List[Dict[str, Any]],
    *,
    task_id: str,
    employee_id: int,
) -> bool:
    return active_session_for_employee(sessions_for_task(tasks, task_id), employee_id) is not None


def build_work_session_observation(
    *,
    task_id: str,
    employee_id: int,
    employee_name: str,
    started_at_iso: str,
    role: str = ROLE_PRIMARY,
    session_type: str = SESSION_TYPE_WORK,
    source: str = "employee_mobile",
    notes: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    observation: Dict[str, Any] = {
        "session_id": new_session_id(),
        "task_id": task_id,
        "employee_id": employee_id,
        "employee_name": employee_name,
        "role": role,
        "session_type": session_type,
        "started_at": started_at_iso,
        "ended_at": None,
        "duration_minutes": None,
        "status": SESSION_STATUS_IN_PROGRESS,
        "source": source,
    }
    if notes:
        observation["notes"] = notes
    if extra:
        for key, value in extra.items():
            if value is not None:
                observation[key] = value
    return observation


def close_work_session(
    entry: Dict[str, Any],
    *,
    ended_at_iso: str,
    status: str,
    completion_fields: Optional[Dict[str, Any]] = None,
) -> None:
    started_at = entry.get("started_at")
    if started_at:
        entry["duration_minutes"] = compute_duration_minutes(str(started_at), ended_at_iso)
    entry["ended_at"] = ended_at_iso
    entry["status"] = status
    if completion_fields:
        for key, value in completion_fields.items():
            if value is not None:
                entry[key] = value


def aggregate_task_work_metrics(
    sessions: List[Dict[str, Any]],
    *,
    employee_names: Optional[Dict[int, str]] = None,
) -> Dict[str, Any]:
    active_workers: List[Dict[str, Any]] = []
    participant_ids: set[int] = set()
    total_logged = 0.0
    last_worked_at: Optional[str] = None

    for entry in sessions:
        employee_id_raw = entry.get("employee_id")
        try:
            employee_id = int(employee_id_raw) if employee_id_raw is not None else None
        except (TypeError, ValueError):
            employee_id = None

        if employee_id is not None and employee_id > 0:
            participant_ids.add(employee_id)

        ended_at = entry.get("ended_at")
        if ended_at:
            duration = entry.get("duration_minutes")
            if duration is None and entry.get("started_at"):
                duration = compute_duration_minutes(str(entry["started_at"]), str(ended_at))
            if duration:
                total_logged += float(duration)
            if last_worked_at is None or str(ended_at) > last_worked_at:
                last_worked_at = str(ended_at)

        if is_session_active(entry) and entry.get("started_at"):
            name = str(entry.get("employee_name") or "").strip()
            if not name and employee_id is not None and employee_names:
                name = employee_names.get(employee_id, "")
            active_workers.append(
                {
                    "employee_id": employee_id,
                    "employee_name": name,
                    "role": str(entry.get("role") or ROLE_PRIMARY),
                    "session_type": str(entry.get("session_type") or SESSION_TYPE_WORK),
                    "started_at": entry.get("started_at"),
                    "session_id": ensure_session_id(entry),
                }
            )

    return {
        "active_workers": active_workers,
        "participants_count": len(participant_ids),
        "work_sessions_count": len(sessions),
        "total_logged_minutes": round(total_logged, 2),
        "last_worked_at": last_worked_at,
    }


def employee_safe_helper_count(
    active_workers: List[Dict[str, Any]],
    *,
    viewer_employee_id: int,
) -> int:
    others = 0
    for worker in active_workers:
        try:
            worker_id = int(worker.get("employee_id") or 0)
        except (TypeError, ValueError):
            continue
        if worker_id > 0 and worker_id != viewer_employee_id:
            others += 1
    return others
