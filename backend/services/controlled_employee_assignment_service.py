"""Canonical controlled employee assignment — Wave 6 hardened command.

Single mutation contract for operational task assignment:

* DEC-015 eligibility revalidated inside the plan lock
* Compare-and-set on embedded ``assigned_employee_id``
* No caller-controlled validation bypass
* No silent reassignment / last-write-wins
* Audit evidence embedded in the same ``tasks_json`` write (no schema change)

Does not create sessions/actuals. Does not activate Employee Mobile.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone
from typing import Any, Optional
from weakref import WeakValueDictionary

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from services.employee_eligibility_read_model_service import (
    build_employee_eligibility_read_model,
)
from services.employee_lifecycle import is_assignable
from services.execution_plan_operational_readiness_service import (
    assert_operational_mutation_allowed,
)
from services.execution_plan_task_parser import (
    ParsedExecutionPlanTasks,
    load_operational_tasks_from_plan_json,
    serialize_operational_tasks_to_plan_json,
)

CONTROLLED_ASSIGNMENT_SOURCE = "controlled_ops_graph_assign_v1"
CANONICAL_ASSIGNMENT_SOURCE = "canonical_controlled_assign_v1"

OUTCOME_ASSIGNED = "assigned"
OUTCOME_ALREADY_SAME = "already_assigned_to_same_employee"

# Plan-scoped process lock (complements SELECT FOR UPDATE on the plan row).
_plan_assign_locks: "WeakValueDictionary[int, asyncio.Lock]" = WeakValueDictionary()


def _plan_assignment_lock(order_id: int) -> asyncio.Lock:
    lock = _plan_assign_locks.get(order_id)
    if lock is None:
        lock = asyncio.Lock()
        _plan_assign_locks[order_id] = lock
    return lock


def _reality_has_active_session(raw: str | None, task_id: str) -> bool:
    import json

    if not raw:
        return False
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return False
    if not isinstance(parsed, list):
        return False
    for item in parsed:
        if not isinstance(item, dict):
            continue
        if str(item.get("task_id")) != task_id:
            continue
        if item.get("started_at") and not item.get("ended_at"):
            return True
    return False


def _reality_task_lookup(raw: Optional[str]) -> dict[str, dict]:
    import json

    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    if not isinstance(parsed, list):
        return {}
    return {
        str(item.get("task_id")): item
        for item in parsed
        if isinstance(item, dict) and item.get("task_id")
    }


def _normalize_employee_id(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _load_plan_operational_tasks(raw: str) -> tuple[list[dict[str, Any]], ParsedExecutionPlanTasks]:
    tasks, parsed = load_operational_tasks_from_plan_json(raw)
    if parsed.format == "invalid":
        raise HTTPException(
            status_code=422,
            detail={"error": "tasks_json_invalid", "message": ";".join(parsed.parse_errors)},
        )
    return tasks, parsed


def _eligibility_task_row(eligibility: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    for row in eligibility.get("tasks") or []:
        if str(row.get("task_key") or "") == task_id:
            return row
    return None


def _raise_eligibility_failure(task_row: dict[str, Any]) -> None:
    status = str(task_row.get("eligibility_status") or "")
    blockers = list(task_row.get("blockers") or [])
    status_to_error = {
        "blocked_missing_workcenter": "blocked_missing_workcenter",
        "blocked_ambiguous_workcenter": "blocked_ambiguous_workcenter",
        "blocked_missing_requirements": "blocked_missing_requirements",
        "blocked_no_matching_employee": "blocked_no_matching_employee",
        "not_required": "blocked_missing_requirements",
    }
    if status in status_to_error:
        raise HTTPException(
            status_code=422,
            detail={
                "error": status_to_error[status],
                "eligibility_status": status,
                "blockers": blockers,
            },
        )
    if status not in {"ready", "ready_with_warnings"}:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "employee_not_eligible",
                "eligibility_status": status,
                "blockers": blockers,
            },
        )


async def assign_operational_task_controlled(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    assigned_employee_id: int,
    actor_user_id: str | None = None,
    allow_reassign: bool = False,
) -> dict[str, Any]:
    """Canonical assignment command (Wave 6).

    ``allow_reassign`` is accepted only for signature compatibility with older
    internal callers and is **ignored** — silent reassignment is forbidden.
    """
    del allow_reassign  # DEC-ASSIGN-03/07: SILENT_REASSIGNMENT = FORBIDDEN

    if not isinstance(order_id, int) or order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    tid = (task_id or "").strip()
    if not tid:
        raise HTTPException(status_code=422, detail={"error": "invalid_task_identity"})
    if not isinstance(assigned_employee_id, int) or assigned_employee_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "assigned_employee_id_invalid"})

    # Fast pre-checks (not sufficient alone — revalidated inside the lock).
    order = (
        await db.execute(select(Orders).where(Orders.id == order_id))
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})

    emp = (
        await db.execute(select(Employees).where(Employees.id == assigned_employee_id))
    ).scalar_one_or_none()
    if emp is None:
        raise HTTPException(status_code=404, detail={"error": "employee_not_found"})
    if not is_assignable(emp, date.today()):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "inactive_employee",
                "status": emp.status,
                "end_date": emp.end_date.isoformat() if emp.end_date else None,
            },
        )

    async with _plan_assignment_lock(order_id):
        plan = (
            await db.execute(
                select(ExecutionPlan)
                .where(ExecutionPlan.order_id == order_id)
                .order_by(ExecutionPlan.id.desc())
                .limit(1)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if plan is None:
            raise HTTPException(status_code=404, detail={"error": "plan_not_found"})
        if int(plan.order_id) != int(order_id):
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "plan_mismatch",
                    "message": "Execution plan does not belong to the requested order.",
                },
            )

        assert_operational_mutation_allowed(plan)

        # Re-read employee under the same transactional boundary.
        emp = (
            await db.execute(select(Employees).where(Employees.id == assigned_employee_id))
        ).scalar_one_or_none()
        if emp is None:
            raise HTTPException(status_code=404, detail={"error": "employee_not_found"})
        if not is_assignable(emp, date.today()):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "inactive_employee",
                    "status": emp.status,
                    "end_date": emp.end_date.isoformat() if emp.end_date else None,
                },
            )

        # DEC-015 eligibility revalidation inside lock (not a pre-lock-only check).
        eligibility = await build_employee_eligibility_read_model(db, order_id)
        if eligibility.get("status") == "blocked_not_materialized":
            raise HTTPException(
                status_code=422,
                detail={"error": "task_not_materialized"},
            )
        if eligibility.get("status") == "plan_not_found":
            raise HTTPException(status_code=404, detail={"error": "plan_not_found"})

        task_row = _eligibility_task_row(eligibility, tid)
        if task_row is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "task_not_found",
                    "message": "Task absent from operational_tasks[].",
                },
            )

        _raise_eligibility_failure(task_row)

        eligible_ids = {
            int(e["employee_id"])
            for e in (task_row.get("eligible_employees") or [])
            if e.get("employee_id") is not None
        }
        if int(assigned_employee_id) not in eligible_ids:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "employee_not_eligible",
                    "message": "Employee is not in current eligibility candidates for this task.",
                    "eligible_employee_ids": sorted(eligible_ids),
                },
            )

        reality = (
            await db.execute(
                select(ExecutionReality).where(ExecutionReality.order_id == order_id)
            )
        ).scalar_one_or_none()
        if reality and _reality_has_active_session(reality.tasks_json, tid):
            raise HTTPException(
                status_code=409,
                detail={"error": "task_session_already_active"},
            )

        reality_lookup = _reality_task_lookup(reality.tasks_json if reality else None)
        tasks, parsed = _load_plan_operational_tasks(plan.tasks_json)

        updated_task: Optional[dict[str, Any]] = None
        outcome = OUTCOME_ASSIGNED
        for entry in tasks:
            if not isinstance(entry, dict):
                continue
            if str(entry.get("task_id")) != tid:
                continue

            rt = reality_lookup.get(tid, {})
            if rt.get("ended_at"):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "stale_task_state",
                        "message": "Task completed — assignment mutation forbidden.",
                        "reason": "task_already_completed",
                    },
                )

            existing_assignee = _normalize_employee_id(entry.get("assigned_employee_id"))
            if existing_assignee is not None and existing_assignee != assigned_employee_id:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "already_assigned_to_different_employee",
                        "message": "Task already assigned to another employee.",
                        "current_assigned_employee_id": existing_assignee,
                    },
                )

            if existing_assignee == assigned_employee_id:
                # Idempotent retry: no mutation, no duplicate audit write.
                outcome = OUTCOME_ALREADY_SAME
                updated_task = dict(entry)
                break

            # CAS: unassigned → assign once (same JSON document rewrite under plan lock).
            entry["assigned_employee_id"] = assigned_employee_id
            entry["assignment_updated_at"] = datetime.now(timezone.utc).isoformat()
            entry["assignment_source"] = CANONICAL_ASSIGNMENT_SOURCE
            if actor_user_id:
                entry["assignment_actor_user_id"] = str(actor_user_id)
            updated_task = dict(entry)
            break

        if updated_task is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "task_not_found",
                    "message": "Task absent from plan operational tasks after lock re-read.",
                },
            )

        if outcome == OUTCOME_ASSIGNED:
            # Persistence + embedded audit evidence are the same write.
            plan.tasks_json = serialize_operational_tasks_to_plan_json(parsed, tasks)
            try:
                await db.commit()
            except Exception:
                await db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail={"error": "assignment_persist_failed"},
                ) from None
            await db.refresh(plan)
            # Fail closed if audit fields did not land with the assignment.
            persisted_tasks, _ = _load_plan_operational_tasks(plan.tasks_json)
            persisted = next(
                (
                    t
                    for t in persisted_tasks
                    if isinstance(t, dict) and str(t.get("task_id")) == tid
                ),
                None,
            )
            if (
                persisted is None
                or _normalize_employee_id(persisted.get("assigned_employee_id"))
                != assigned_employee_id
                or not persisted.get("assignment_updated_at")
                or persisted.get("assignment_source") != CANONICAL_ASSIGNMENT_SOURCE
            ):
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "assignment_audit_inconsistent",
                        "message": "Assignment persistence missing required audit evidence.",
                    },
                )
            updated_task = dict(persisted)

        status = str(task_row.get("eligibility_status") or "")
        # Operational application log — safe IDs only (no name/email/JWT/tasks_json/pricing).
        logger.info(
            "assignment_command event=%s outcome=%s order_id=%s plan_id=%s "
            "task_id=%s employee_id=%s actor_user_id=%s eligibility_status=%s "
            "retry_or_conflict=%s",
            (
                "ASSIGNMENT_IDEMPOTENT_RETRY"
                if outcome == OUTCOME_ALREADY_SAME
                else "ASSIGNMENT_SUCCEEDED"
            ),
            outcome,
            order_id,
            plan.id,
            tid,
            assigned_employee_id,
            actor_user_id,
            status,
            "idempotent" if outcome == OUTCOME_ALREADY_SAME else "first_assign",
        )
        return {
            "plan_id": plan.id,
            "order_id": plan.order_id,
            "order_code": plan.order_code,
            "task_id": tid,
            "assigned_employee_id": assigned_employee_id,
            "assigned_employee_name": emp.name,
            "task": updated_task,
            "assignment_outcome": outcome,
            "already_assigned": outcome == OUTCOME_ALREADY_SAME,
            "controlled": True,
            "eligibility_status": status,
            "eligible_employee_count": int(task_row.get("eligible_employee_count") or 0),
            "requirement_version": task_row.get("requirement_version"),
            "actor_user_id": actor_user_id,
            "sessions_created": 0,
            "actuals_created": 0,
            "authorization_scope": {
                "permission": "execution.task_assign",
                "order_id": order_id,
                "plan_id": plan.id,
                "task_id": tid,
                "employee_context": "active_assignable_plus_dec015_eligibility",
                "tenant_model": "none_in_system",
            },
        }
