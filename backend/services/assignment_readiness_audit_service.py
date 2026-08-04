"""Finalization Wave 5 — Assignment Readiness Audit (read-only).

Composes Wave 4 eligibility + current embedded assignment state + known
command-contract inventory. Never calls assign_plan_task / never writes.
ASSIGNMENT_AUTHORIZED remains False until a separate Owner GO.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.employee_eligibility_read_model_service import (
    build_employee_eligibility_read_model,
)
from services.employee_lifecycle import is_assignable
from services.execution_plan_task_parser import load_operational_tasks_from_plan_json
from services.operational_resource_readiness_service import (
    build_operational_resource_readiness,
)

AUDIT_MODE = "assignment_readiness_audit"
AUDIT_VERSION = "assignment-readiness/v1"

COMMAND_ROUTE = "PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/assign"
COMMAND_SERVICE_CONTROLLED = "assign_operational_task_controlled"
COMMAND_SERVICE_PERSIST = "assign_plan_task"
COMMAND_PERMISSION = "execution.task_assign"

OWNER_GO_BLOCKER = "OWNER_GO_FOR_REAL_ASSIGNMENT_NOT_GRANTED"


def _parse_envelope(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _normalize_emp_id(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _reality_has_active_session(raw: str | None, task_id: str) -> bool:
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


def evaluate_candidate_for_future_assignment(
    *,
    eligibility_task: dict[str, Any] | None,
    plan_task: dict[str, Any] | None,
    candidate_employee_id: int | None,
    employee: Employees | None,
    active_session: bool,
) -> dict[str, Any]:
    """Pure candidate validation mirror of controlled assign preconditions.

    Does not persist. Even VALID_CANDIDATE_FOR_FUTURE_ASSIGNMENT does not
    authorize execution of the assignment command under Wave 5.
    """
    reasons: list[str] = []
    if candidate_employee_id is None:
        return {
            "evaluation_status": "CANDIDATE_NOT_REQUESTED",
            "assignment_authorized": False,
            "authorization_blocker": OWNER_GO_BLOCKER,
            "reasons": ["No candidate_employee_id supplied for hypothetical evaluation."],
        }
    if plan_task is None:
        return {
            "evaluation_status": "TASK_NOT_OPERATIONAL",
            "assignment_authorized": False,
            "authorization_blocker": OWNER_GO_BLOCKER,
            "reasons": ["Task absent from operational_tasks[]."],
        }
    if eligibility_task is None:
        return {
            "evaluation_status": "TASK_NOT_OPERATIONAL",
            "assignment_authorized": False,
            "authorization_blocker": OWNER_GO_BLOCKER,
            "reasons": ["Task absent from eligibility read model (operational_tasks[] only)."],
        }
    if employee is None:
        return {
            "evaluation_status": "CANDIDATE_NOT_FOUND",
            "assignment_authorized": False,
            "authorization_blocker": OWNER_GO_BLOCKER,
            "reasons": [f"Employee id={candidate_employee_id} not found."],
        }
    if not is_assignable(employee, date.today()):
        return {
            "evaluation_status": "CANDIDATE_INACTIVE",
            "assignment_authorized": False,
            "authorization_blocker": OWNER_GO_BLOCKER,
            "reasons": [
                f"Employee status={getattr(employee, 'status', None)} is not assignable.",
            ],
        }

    existing = _normalize_emp_id(plan_task.get("assigned_employee_id"))
    if existing is not None and existing != int(candidate_employee_id):
        return {
            "evaluation_status": "TASK_ALREADY_ASSIGNED",
            "assignment_authorized": False,
            "authorization_blocker": OWNER_GO_BLOCKER,
            "reasons": [f"Task already assigned to employee_id={existing}."],
            "current_assigned_employee_id": existing,
        }
    if existing == int(candidate_employee_id):
        reasons.append("Same employee already embedded on task (idempotent no-op path).")

    if active_session:
        return {
            "evaluation_status": "COMMAND_NOT_AUTHORIZED",
            "assignment_authorized": False,
            "authorization_blocker": OWNER_GO_BLOCKER,
            "reasons": ["Active session blocks controlled assign (409 task_session_already_active)."],
        }

    status = str(eligibility_task.get("eligibility_status") or "")
    blockers = list(eligibility_task.get("blockers") or [])
    if status in {
        "blocked_missing_workcenter",
        "blocked_ambiguous_workcenter",
        "blocked_missing_requirements",
        "not_required",
    }:
        return {
            "evaluation_status": "ELIGIBILITY_REQUIREMENTS_NOT_CONFIGURED"
            if status in {"blocked_missing_requirements", "not_required"}
            else "NOT_ELIGIBLE",
            "assignment_authorized": False,
            "authorization_blocker": OWNER_GO_BLOCKER,
            "eligibility_status": status,
            "reasons": blockers or [status],
        }
    if status == "blocked_no_matching_employee":
        return {
            "evaluation_status": "NOT_ELIGIBLE",
            "assignment_authorized": False,
            "authorization_blocker": OWNER_GO_BLOCKER,
            "eligibility_status": status,
            "reasons": blockers or ["no_matching_employee"],
        }
    if status not in {"ready", "ready_with_warnings"}:
        return {
            "evaluation_status": "ELIGIBILITY_UNKNOWN",
            "assignment_authorized": False,
            "authorization_blocker": OWNER_GO_BLOCKER,
            "eligibility_status": status,
            "reasons": blockers or [f"Unhandled eligibility_status={status}"],
        }

    eligible_ids = {
        int(e["employee_id"])
        for e in (eligibility_task.get("eligible_employees") or [])
        if e.get("employee_id") is not None
    }
    if int(candidate_employee_id) not in eligible_ids:
        return {
            "evaluation_status": "NOT_ELIGIBLE",
            "assignment_authorized": False,
            "authorization_blocker": OWNER_GO_BLOCKER,
            "eligibility_status": status,
            "reasons": [
                "Employee is not in current eligibility candidates for this task.",
            ],
            "eligible_employee_ids": sorted(eligible_ids),
        }

    return {
        "evaluation_status": "VALID_CANDIDATE_FOR_FUTURE_ASSIGNMENT",
        "assignment_authorized": False,
        "authorization_blocker": OWNER_GO_BLOCKER,
        "eligibility_status": status,
        "reasons": reasons
        + [
            "Candidate passes known controlled-assign technical preconditions.",
            "Wave 5 does not authorize executing the assignment command.",
        ],
        "eligible_employee_ids": sorted(eligible_ids),
        "semantics": {
            "ELIGIBLE_CANDIDATE": True,
            "SELECTED_CANDIDATE": False,
            "ASSIGNABLE_REQUEST": False,
            "VALIDATED_ASSIGNMENT_COMMAND": False,
            "PERSISTED_ASSIGNMENT": existing == int(candidate_employee_id),
            "AUTHORIZED_TO_START": False,
            "AVAILABLE_NOW": False,
        },
    }


def _command_contract_inventory() -> dict[str, Any]:
    return {
        "canonical_route": COMMAND_ROUTE,
        "request_schema": {
            "assigned_employee_id": "int (required)",
            "controlled": "optional legacy; false → 422 forbidden (Wave 6)",
            "allow_reassign": "optional legacy; true → 422 forbidden (Wave 6)",
        },
        "frontend_may_send_only": [
            "order_id (path)",
            "task_id / task_key (path)",
            "assigned_employee_id",
        ],
        "frontend_must_not_send_as_truth": [
            "eligibility result",
            "role/skill requirements",
            "workcenter override",
            "task body",
            "machine capability result",
            "eligible=true",
            "admin_override",
            "estimated_minutes",
        ],
        "server_rebuilds": [
            "order existence",
            "order → latest ExecutionPlan under FOR UPDATE",
            "task from operational_tasks[] only",
            "frozen workcenter from task",
            "DEC-015 eligibility inside plan lock",
            "employee assignable lifecycle (inside lock)",
            "existing assigned_employee_id CAS",
            "active session conflict",
            "operational readiness mutation gate",
            "embedded assignment audit fields in same JSON write",
        ],
        "controlled_service": COMMAND_SERVICE_CONTROLLED,
        "persist_service": "inlined in assign_operational_task_controlled (Wave 6); assign_plan_task = BLOCKED_LEGACY",
        "permission": COMMAND_PERMISSION,
        "persistence": "embedded assigned_employee_id on operational task in tasks_json (no separate assignment table)",
        "legacy_bypass": {
            "path": "public controlled=false / allow_reassign=true rejected; assign_plan_task raises direct_assign_blocked",
            "classification": "BLOCKED_LEGACY",
            "mobile_claim_start_from_available": "BLOCKED_LEGACY / FROZEN_FINAL_FINAL",
        },
        "idempotency": {
            "status": "IDEMPOTENCY_VERIFIED_FOR_EMBEDDED_MODEL",
            "same_employee_noop": True,
            "different_employee_conflict": True,
            "idempotency_key": False,
            "unique_constraint": False,
            "optimistic_version": False,
            "in_process_lock": True,
            "select_for_update": True,
            "notes": [
                "State CAS on assigned_employee_id under plan lock.",
                "asyncio.Lock is process-local; DB FOR UPDATE covers same-DB writers.",
                "No client idempotency key (DEC-ASSIGN-03).",
                "Cluster/multi-node safety not claimed.",
            ],
        },
        "transactionality": {
            "status": "TRANSACTIONALITY_VERIFIED_WITHIN_DOCUMENTED_BOUNDARY",
            "unit": "single ExecutionPlan.tasks_json rewrite including embedded audit + commit",
            "separate_assignment_row": False,
            "audit_model": "embedded assignment_source/updated_at/actor_user_id in same write",
            "partial_state_risk": "No separate audit table; success requires audit fields present after commit",
            "rollback_helper": "clear_plan_task_assignment retained but Mobile paths frozen",
        },
        "concurrency": {
            "status": "CONCURRENCY_VERIFIED_WITHIN_DOCUMENTED_BOUNDARY",
            "protections": [
                "per-order asyncio.Lock (plan-scoped)",
                "SELECT FOR UPDATE on plan row",
                "eligibility + state revalidation inside lock",
                "409 already_assigned_to_different_employee (no overwrite)",
            ],
            "gaps": [
                "process-local asyncio.Lock is not cluster-wide",
                "no client expected plan/task version token",
            ],
        },
        "candidate_selection_policy": "MANUAL_FUTURE_OWNER_DECISION",
        "auto_assignment": "NOT_AUTHORIZED",
        "machine_assignment_coupled": False,
    }


def _protections() -> dict[str, Any]:
    return {
        "confirmed": [
            "canonical path always revalidates DEC-015 eligibility inside plan lock",
            "public controlled=false / allow_reassign=true rejected",
            "direct assign_plan_task blocked",
            "Mobile claim/start_from_available frozen",
            "operational_tasks[] only (no planned_tasks fallback)",
            "employee lifecycle is_assignable check inside lock",
            "active session blocks controlled assign",
            "permission execution.task_assign required",
            "order + plan + task + DEC-015 employee context scoped",
            "same-employee idempotent; different-employee conflict",
            "embedded audit evidence required on successful assign",
        ],
        "missing_or_partial": [
            "no multi-tenant org model in system (strongest scope = order/plan/task/DEC-015)",
            "no client idempotency key / unique assignment constraint",
            "no expected version / ETag concurrency token",
            "in-process lock not cluster-safe (DB FOR UPDATE is the cross-connection boundary)",
            "Availability/pontaj not evaluated (correct; must stay not_evaluated)",
        ],
        "wave5_authorization": {
            "assignment_authorized": False,
            "reason": OWNER_GO_BLOCKER,
        },
    }


async def build_assignment_readiness_audit(
    db: AsyncSession,
    order_id: int,
    *,
    candidate_employee_id: int | None = None,
    task_key: str | None = None,
) -> dict[str, Any]:
    """Read-only assignment readiness audit. Zero writes. Zero command execution."""
    wave5_boundary = {
        "assignment_authorized": False,
        "assignment_command_executable": False,
        "machine_assignable": False,
        "schedulable": False,
        "sessions_authorized": False,
        "capacity_allocation": "not_started",
        "evaluation_mode": "read_only_audit",
        "authorization_blocker": OWNER_GO_BLOCKER,
    }

    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        return {
            "mode": AUDIT_MODE,
            "audit_version": AUDIT_VERSION,
            "order_id": order_id,
            "status": "plan_not_found",
            "side_effects": "none",
            "wave5_boundary": wave5_boundary,
            "command_contract": _command_contract_inventory(),
            "protections": _protections(),
            "tasks": [],
            "notes": ["No ExecutionPlan for order — assignment readiness unavailable."],
        }

    envelope = _parse_envelope(plan.tasks_json)
    ops = envelope.get("operational_tasks")
    if not isinstance(ops, list):
        ops = []

    eligibility = await build_employee_eligibility_read_model(db, order_id)
    resources = await build_operational_resource_readiness(db, order_id)

    if not ops:
        return {
            "mode": AUDIT_MODE,
            "audit_version": AUDIT_VERSION,
            "order_id": order_id,
            "execution_plan_id": plan.id,
            "status": "blocked_not_materialized",
            "side_effects": "none",
            "wave5_boundary": wave5_boundary,
            "command_contract": _command_contract_inventory(),
            "protections": _protections(),
            "operational_task_count": 0,
            "employee_assignment_count": 0,
            "machine_assignment_count": 0,
            "eligibility_status": eligibility.get("status"),
            "resource_readiness_status": getattr(resources, "status", None),
            "scheduling": "HOLD",
            "capacity_allocation": "not_started",
            "tasks": [],
            "notes": [
                "Assignment readiness requires materialized operational_tasks[].",
                "Planned tasks / planned operations are not assignment sources.",
            ],
        }

    plan_tasks, _parsed = load_operational_tasks_from_plan_json(plan.tasks_json)
    plan_by_id = {
        str(t.get("task_id") or "").strip(): t
        for t in plan_tasks
        if isinstance(t, dict) and str(t.get("task_id") or "").strip()
    }

    elig_by_key = {
        str(t.get("task_key") or "").strip(): t
        for t in (eligibility.get("tasks") or [])
        if isinstance(t, dict) and str(t.get("task_key") or "").strip()
    }
    res_by_key = {
        str(getattr(t, "task_key", None) or "").strip(): t
        for t in (getattr(resources, "tasks", None) or [])
        if str(getattr(t, "task_key", None) or "").strip()
    }

    reality = (
        await db.execute(select(ExecutionReality).where(ExecutionReality.order_id == order_id))
    ).scalar_one_or_none()
    reality_raw = reality.tasks_json if reality else None

    task_rows: list[dict[str, Any]] = []
    assigned_count = 0
    for op in ops:
        if not isinstance(op, dict):
            continue
        tid = str(op.get("task_id") or op.get("source_task_key") or "").strip()
        if not tid:
            continue
        plan_task = plan_by_id.get(tid) or op
        elig = elig_by_key.get(tid)
        res = res_by_key.get(tid)
        assignee = _normalize_emp_id(plan_task.get("assigned_employee_id"))
        if assignee is not None:
            assigned_count += 1
        minutes = plan_task.get("estimated_time_minutes")
        if minutes is None:
            minutes = plan_task.get("estimated_minutes")
        warnings = list(plan_task.get("warnings") or [])
        if minutes is None and "PLANNING_MINUTES_SOURCE_REQUIRED" not in warnings:
            # Preserve Wave 3 honesty if warning string differs in envelope.
            for w in warnings:
                if "PLANNING_MINUTES" in str(w).upper():
                    break
            else:
                warnings = warnings + ["PLANNING_MINUTES_SOURCE_REQUIRED"]

        machine_candidates = 0
        if res is not None:
            machine_candidates = len(getattr(res, "compatible_machine_candidates", None) or [])

        task_rows.append(
            {
                "task_key": tid,
                "canonical_task_type": plan_task.get("canonical_task_type")
                or (elig or {}).get("canonical_task_type"),
                "source_operation_code": plan_task.get("source_operation_code")
                or (elig or {}).get("source_operation_code"),
                "frozen_workcenter": plan_task.get("workcenter_code")
                or (elig or {}).get("workcenter_code"),
                "estimated_minutes": minutes,
                "warnings": warnings,
                "eligibility_status": (elig or {}).get("eligibility_status"),
                "eligible_employee_count": int((elig or {}).get("eligible_employee_count") or 0),
                "eligible_employees": [
                    {
                        "employee_id": e.get("employee_id"),
                        "display_name": e.get("display_name"),
                        "match_provenance": e.get("match_provenance"),
                        "availability_status": e.get("availability_status", "not_evaluated"),
                    }
                    for e in ((elig or {}).get("eligible_employees") or [])
                    if isinstance(e, dict)
                ],
                "eligibility_blockers": list((elig or {}).get("blockers") or []),
                "current_assignment": {
                    "status": "assigned" if assignee is not None else "unassigned",
                    "assigned_employee_id": assignee,
                    "assignment_source": plan_task.get("assignment_source"),
                },
                "machine_capability_ref": {
                    "status": getattr(res, "status", None) if res is not None else "unavailable",
                    "capable_machine_candidate_count": machine_candidates,
                    "semantics": {
                        "CAPABLE_MACHINE": machine_candidates > 0,
                        "SELECTED_MACHINE": False,
                        "ASSIGNED_MACHINE": False,
                        "RESERVED_MACHINE": False,
                        "AVAILABLE_MACHINE": False,
                    },
                },
                "active_session": _reality_has_active_session(reality_raw, tid),
                "future_assign_preconditions": {
                    "task_operational": True,
                    "eligibility_ready": (elig or {}).get("eligibility_status")
                    in {"ready", "ready_with_warnings"},
                    "has_eligible_candidate": int((elig or {}).get("eligible_employee_count") or 0)
                    > 0,
                    "currently_unassigned": assignee is None,
                    "no_active_session": not _reality_has_active_session(reality_raw, tid),
                    "minutes_configured": minutes is not None,
                    "schedulable": False,
                    "assignment_authorized": False,
                },
                "readiness_notes": [
                    "ELIGIBLE_CANDIDATE ≠ SELECTED_CANDIDATE ≠ PERSISTED_ASSIGNMENT",
                    "CAPABLE_MACHINE ≠ ASSIGNED_MACHINE ≠ RESERVED_MACHINE",
                    "MATERIALIZED + ELIGIBLE ≠ ASSIGNED ≠ SCHEDULABLE ≠ AUTHORIZED_TO_START",
                ],
            }
        )

    hypothetical: dict[str, Any] | None = None
    requested_task = (task_key or "").strip() or None
    if candidate_employee_id is not None or requested_task is not None:
        emp = None
        if candidate_employee_id is not None:
            emp = (
                await db.execute(
                    select(Employees).where(Employees.id == int(candidate_employee_id))
                )
            ).scalar_one_or_none()
        elig_task = elig_by_key.get(requested_task) if requested_task else None
        plan_task = plan_by_id.get(requested_task) if requested_task else None
        if requested_task is None:
            hypothetical = {
                "evaluation_status": "TASK_NOT_OPERATIONAL",
                "assignment_authorized": False,
                "authorization_blocker": OWNER_GO_BLOCKER,
                "reasons": ["task_key required for hypothetical candidate evaluation."],
            }
        else:
            hypothetical = evaluate_candidate_for_future_assignment(
                eligibility_task=elig_task,
                plan_task=plan_task,
                candidate_employee_id=candidate_employee_id,
                employee=emp,
                active_session=_reality_has_active_session(reality_raw, requested_task),
            )
            hypothetical["task_key"] = requested_task
            hypothetical["candidate_employee_id"] = candidate_employee_id

    return {
        "mode": AUDIT_MODE,
        "audit_version": AUDIT_VERSION,
        "order_id": order_id,
        "execution_plan_id": plan.id,
        "status": "ok",
        "side_effects": "none",
        "wave5_boundary": wave5_boundary,
        "command_contract": _command_contract_inventory(),
        "protections": _protections(),
        "operational_task_count": len(task_rows),
        "employee_assignment_count": assigned_count,
        "machine_assignment_count": 0,
        "session_count_active": sum(1 for t in task_rows if t.get("active_session")),
        "eligibility_envelope_status": eligibility.get("status"),
        "resource_readiness_status": getattr(resources, "status", None),
        "execution_tasks_created": bool(envelope.get("execution_tasks_created")),
        "scheduling": "HOLD",
        "capacity_allocation": "not_started",
        "tasks": task_rows,
        "hypothetical_candidate_evaluation": hypothetical,
        "notes": [
            "Read-only audit. Does not assign employees, teams, machines, or reserve capacity.",
            "Does not execute PATCH assign. Does not start sessions.",
            "Candidate selection policy remains MANUAL_FUTURE_OWNER_DECISION.",
            OWNER_GO_BLOCKER,
        ],
    }
