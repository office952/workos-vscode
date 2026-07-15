"""Read-only execution task collaboration projection (FLEX-01).

Projects optional principal from assigned_employee_id and actual workers from sessions.
Does not write to DB and does not change operational behavior.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from schemas.execution_task_collaboration_read import (
    EXECUTION_TASK_COLLABORATION_READ_VERSION,
    ActualWorkerRead,
    OperationCompletionSource,
    OptionalPrincipalRead,
    OrderTaskCollaborationReadResponse,
    PrincipalSource,
    TaskCollaborationRead,
    WorkerSessionRead,
)
from services.execution_plan_task_parser import operational_tasks_only
from services.material_procurement_status_service import split_reality_task_entries
from services.order_production_blueprint_service import blueprint_status_bucket
from services.task_work_session_service import (
    SESSION_STATUS_COMPLETED,
    SESSION_STATUS_ENDED,
    aggregate_task_work_metrics,
    compute_duration_minutes,
    derive_task_status_from_sessions,
    ensure_session_id,
    is_session_active,
    sessions_for_task,
)

READ_MODEL_NOTES = [
    "optional_principal is assigned_employee_id compatibility — not participation proof",
    "actual_workers are derived only from existing sessions with employee_id",
    "operation_completed uses explicit per-session completion signals only",
    "legacy_or_derived_task_status may show done while operation_completed is false",
    "no invite-before-start, help lifecycle, or quantity progress in FLEX-01",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_employee_id(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _parse_json(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _session_explicitly_completed(entry: dict[str, Any]) -> bool:
    status = str(entry.get("status") or "").strip().lower()
    if status == SESSION_STATUS_COMPLETED:
        return True
    if _normalize_employee_id(entry.get("completed_by_employee_id")) is not None:
        return True
    return False


def _session_stopped_without_completion(entry: dict[str, Any]) -> bool:
    if not entry.get("ended_at"):
        return False
    status = str(entry.get("status") or "").strip().lower()
    if status == SESSION_STATUS_ENDED:
        return True
    if status and status != SESSION_STATUS_COMPLETED:
        return True
    if status == "" and not _session_explicitly_completed(entry):
        return True
    return False


def derive_operation_completion_truth(
    sessions: list[dict[str, Any]],
) -> tuple[bool | None, OperationCompletionSource]:
    """Read-only operation completion — explicit session signals, not legacy derive."""
    if not sessions:
        return False, "no_sessions"

    if any(is_session_active(entry) for entry in sessions if isinstance(entry, dict)):
        return False, "active_sessions_remain"

    closed_sessions = [
        entry for entry in sessions if isinstance(entry, dict) and entry.get("ended_at")
    ]
    if not closed_sessions:
        return False, "no_sessions"

    if len(closed_sessions) != len(sessions):
        return None, "unknown"

    if any(_session_stopped_without_completion(entry) for entry in closed_sessions):
        return False, "session_stop_without_explicit_completion"

    if all(_session_explicitly_completed(entry) for entry in closed_sessions):
        return True, "all_sessions_explicitly_completed"

    return None, "unknown"


def _resolve_principal_source(raw: Any) -> PrincipalSource:
    value = str(raw or "").strip().lower()
    if value == "employee_claim":
        return "employee_claim"
    if value in {"manager_assign", "manager_assignment"}:
        return "manager_assign"
    if value in {"start_from_available", "available_start"}:
        return "start_from_available"
    if value in {"", "execution_plan", "execution"}:
        return "execution_plan"
    return "unknown"


def _session_duration_minutes(entry: dict[str, Any]) -> float:
    ended_at = entry.get("ended_at")
    if not ended_at:
        return 0.0
    duration = entry.get("duration_minutes")
    if duration is not None:
        try:
            return max(0.0, float(duration))
        except (TypeError, ValueError):
            pass
    started_at = entry.get("started_at")
    if started_at:
        return float(compute_duration_minutes(str(started_at), str(ended_at)))
    return 0.0


def _build_worker_session_read(entry: dict[str, Any]) -> WorkerSessionRead:
    employee_id = _normalize_employee_id(entry.get("employee_id"))
    return WorkerSessionRead(
        session_id=ensure_session_id(entry),
        employee_id=employee_id,
        employee_name=str(entry.get("employee_name") or "").strip() or None,
        started_at=entry.get("started_at"),
        ended_at=entry.get("ended_at"),
        duration_minutes=_session_duration_minutes(entry) or None,
        is_active=is_session_active(entry),
        session_status=str(entry.get("status") or "").strip() or None,
        session_role=str(entry.get("role") or "").strip() or None,
        session_type=str(entry.get("session_type") or "").strip() or None,
        completed_by_employee_id=_normalize_employee_id(entry.get("completed_by_employee_id")),
    )


def project_task_collaboration_read(
    *,
    task_id: str,
    plan_task: dict[str, Any],
    sessions: list[dict[str, Any]],
    employee_names: dict[int, str] | None = None,
) -> TaskCollaborationRead:
    """Pure read projection for one operational task (Option B)."""
    names = employee_names or {}
    assigned_employee_id = _normalize_employee_id(plan_task.get("assigned_employee_id"))
    principal_source = _resolve_principal_source(plan_task.get("assignment_source"))

    task_sessions = [
        entry for entry in sessions if isinstance(entry, dict)
    ]
    metrics = aggregate_task_work_metrics(task_sessions, employee_names=names)
    derived_status = derive_task_status_from_sessions(task_sessions)
    status_key, status_display = blueprint_status_bucket(derived_status, assigned_employee_id)

    workers_by_id: dict[int, dict[str, Any]] = {}
    for entry in task_sessions:
        employee_id = _normalize_employee_id(entry.get("employee_id"))
        if employee_id is None:
            continue
        bucket = workers_by_id.setdefault(
            employee_id,
            {
                "employee_id": employee_id,
                "employee_name": str(entry.get("employee_name") or "").strip()
                or names.get(employee_id),
                "sessions": [],
            },
        )
        if not bucket.get("employee_name") and names.get(employee_id):
            bucket["employee_name"] = names[employee_id]
        bucket["sessions"].append(entry)

    actual_workers: list[ActualWorkerRead] = []
    for employee_id in sorted(workers_by_id):
        bucket = workers_by_id[employee_id]
        worker_sessions_raw = sorted(
            bucket["sessions"],
            key=lambda item: str(item.get("started_at") or ""),
        )
        worker_sessions = [_build_worker_session_read(item) for item in worker_sessions_raw]
        active_count = sum(1 for item in worker_sessions if item.is_active)
        individual_minutes = sum(
            float(item.duration_minutes or 0.0) for item in worker_sessions if item.duration_minutes
        )
        actual_workers.append(
            ActualWorkerRead(
                employee_id=employee_id,
                employee_name=bucket.get("employee_name"),
                session_count=len(worker_sessions),
                active_session_count=active_count,
                has_active_session=active_count > 0,
                individual_work_time_minutes=round(individual_minutes, 2),
                worker_sessions=worker_sessions,
                is_optional_principal=assigned_employee_id == employee_id,
            )
        )

    principal_has_started = bool(
        assigned_employee_id is not None
        and assigned_employee_id in workers_by_id
    )
    optional_principal = OptionalPrincipalRead(
        optional_principal_employee_id=assigned_employee_id,
        optional_principal_employee_name=(
            names.get(assigned_employee_id) if assigned_employee_id else None
        ),
        optional_principal_source=principal_source,
        principal_has_started=principal_has_started,
    )

    active_workers = [worker for worker in actual_workers if worker.has_active_session]
    completed_session_workers = [
        worker for worker in actual_workers if not worker.has_active_session
    ]

    all_sessions_closed = (
        len(task_sessions) > 0
        and not any(is_session_active(entry) for entry in task_sessions)
    )

    display_name = (
        plan_task.get("display_name")
        or plan_task.get("name")
        or None
    )

    operation_completed, operation_completion_source = derive_operation_completion_truth(
        task_sessions
    )

    return TaskCollaborationRead(
        task_id=task_id,
        display_name=str(display_name) if display_name else None,
        optional_principal=optional_principal,
        actual_workers=actual_workers,
        active_workers=active_workers,
        completed_session_workers=completed_session_workers,
        has_multiple_actual_workers=len(actual_workers) > 1,
        aggregate_session_time_minutes=float(metrics.get("total_logged_minutes") or 0.0),
        all_sessions_closed=all_sessions_closed,
        active_sessions_count=len(active_workers),
        total_sessions_count=len(task_sessions),
        legacy_or_derived_task_status=status_key,
        operation_status=status_key,
        operation_status_display=status_display,
        operation_completed=operation_completed,
        operation_completion_source=operation_completion_source,
        derived_session_status=derived_status,
        collaboration_capability="BACKEND_MULTI_SESSION_CAPABLE",
        ui_collaboration_capability="CURRENTLY_INDIVIDUAL_UI",
    )


async def build_order_task_collaboration_read(
    db: AsyncSession,
    order_id: int,
) -> OrderTaskCollaborationReadResponse:
    if not isinstance(order_id, int) or order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})

    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "execution_plan_not_found"})

    reality_sql = text(
        "SELECT tasks_json FROM execution_reality WHERE order_id = :oid LIMIT 1"
    )
    reality_row = (await db.execute(reality_sql, {"oid": order_id})).mappings().first()
    raw_reality_tasks = _parse_json(reality_row.get("tasks_json") if reality_row else "[]")
    reality_tasks, _procurement_meta = split_reality_task_entries(raw_reality_tasks)

    employees_sql = text("SELECT id, name FROM employees")
    employee_names: dict[int, str] = {
        int(row[0]): str(row[1])
        for row in (await db.execute(employees_sql)).all()
        if row[0] is not None and row[1]
    }

    reality_sessions_by_task: dict[str, list[dict[str, Any]]] = {}
    for entry in reality_tasks:
        if isinstance(entry, dict):
            key = str(entry.get("task_id") or "")
            if key:
                reality_sessions_by_task.setdefault(key, []).append(entry)

    projections: list[TaskCollaborationRead] = []
    for plan_task in operational_tasks_only(plan.tasks_json):
        if not isinstance(plan_task, dict):
            continue
        task_id = str(plan_task.get("task_id") or "")
        if not task_id:
            continue
        task_sessions = reality_sessions_by_task.get(task_id, [])
        projections.append(
            project_task_collaboration_read(
                task_id=task_id,
                plan_task=plan_task,
                sessions=task_sessions,
                employee_names=employee_names,
            )
        )

    return OrderTaskCollaborationReadResponse(
        contract_version=EXECUTION_TASK_COLLABORATION_READ_VERSION,
        order_id=order_id,
        order_code=str(plan.order_code or "") or None,
        execution_plan_id=int(plan.id) if plan.id is not None else None,
        tasks=projections,
        generated_at=_utc_now_iso(),
        read_model_notes=list(READ_MODEL_NOTES),
    )
