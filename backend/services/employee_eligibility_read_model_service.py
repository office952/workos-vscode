"""Employee Eligibility Read Model (DEC-015) — read-only, fail-closed, no assignment.

Uses:
  - frozen operational_tasks[] (workcenter, process_id, warnings)
  - current Employee Registry + explicit skill/WC/operation authorizations
  - ORR required_skill_codes / authorization_mode via OperationalRegistryService

Never writes. Never assigns. Never uses User role, labels, or \"all active\" fallback.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.employees import Employees
from models.execution_plan import ExecutionPlan
from services.operational_registry_service import OperationalRegistryService

REQUIREMENT_SOURCE = "operation_resource_requirements+employee_authorizations"
REQUIREMENT_VERSION = "eligibility-rm/v1"

EligibilityStatus = str  # ready | ready_with_warnings | blocked_* | not_required


def _parse_envelope(tasks_json: str | None) -> dict[str, Any]:
    if not tasks_json:
        return {}
    try:
        data = json.loads(tasks_json)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _task_workcenter(task: dict[str, Any]) -> str | None:
    wc = task.get("workcenter")
    if wc:
        return str(wc).strip() or None
    mr = task.get("machine_requirement")
    if isinstance(mr, dict) and mr.get("workcenter"):
        return str(mr["workcenter"]).strip() or None
    mt = task.get("machine_type")
    if mt:
        return str(mt).strip() or None
    return None


def _task_resolution_status(task: dict[str, Any]) -> str | None:
    mr = task.get("machine_requirement")
    if isinstance(mr, dict):
        status = mr.get("resolution_status")
        if status:
            return str(status)
    warnings = task.get("warnings") or []
    if "WORKCENTER_NOT_REQUIRED" in warnings:
        return "not_required"
    if "WORKCENTER_MAPPING_AMBIGUOUS" in warnings:
        return "ambiguous"
    if "WORKCENTER_MAPPING_SOURCE_MISSING" in warnings:
        return "source_missing"
    return None


def _operation_code(task: dict[str, Any]) -> str:
    return str(
        task.get("source_operation_code")
        or task.get("process_id")
        or ""
    ).strip()


async def build_employee_eligibility_read_model(
    db: AsyncSession,
    order_id: int,
) -> dict[str, Any]:
    """Pure read model over materialized operational_tasks[]. Zero writes."""
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        return {
            "mode": "employee_eligibility_read_model",
            "order_id": order_id,
            "status": "plan_not_found",
            "tasks": [],
            "side_effects": "none",
        }

    envelope = _parse_envelope(plan.tasks_json)
    # Gate B: operational_tasks only — never fall back to planned_tasks[].
    ops = envelope.get("operational_tasks")
    if not isinstance(ops, list):
        ops = []

    if not ops:
        return {
            "mode": "employee_eligibility_read_model",
            "order_id": order_id,
            "execution_plan_id": plan.id,
            "status": "blocked_not_materialized",
            "requirement_source": REQUIREMENT_SOURCE,
            "requirement_version": REQUIREMENT_VERSION,
            "operational_task_count": 0,
            "tasks": [],
            "side_effects": "none",
            "notes": ["Eligibility requires materialized operational_tasks[]."],
        }

    registry = OperationalRegistryService(db)
    # Prefetch active employees + authorizations once (avoid N+1).
    active_emps = (
        await db.execute(
            select(Employees)
            .where(Employees.status == "active")
            .order_by(Employees.name.asc(), Employees.id.asc())
        )
    ).scalars().all()
    auth_by_emp: dict[int, dict[str, list[str]]] = {}
    for emp in active_emps:
        auth_by_emp[int(emp.id)] = await registry.get_employee_authorizations(int(emp.id))

    # Cache ORR resolution + explicit OEA per registry operation code.
    mapping_cache: dict[str, dict[str, Any] | None] = {}
    explicit_cache: dict[str, set[int]] = {}

    async def _mapping_for(op_code: str) -> dict[str, Any] | None:
        key = op_code.lower()
        if key not in mapping_cache:
            mapping_cache[key] = await registry.resolve_operation_mapping(op_code)
        return mapping_cache[key]

    async def _explicit_ids(registry_code: str) -> set[int]:
        if registry_code not in explicit_cache:
            explicit_cache[registry_code] = set(
                await registry.get_operation_employee_ids(registry_code)
            )
        return explicit_cache[registry_code]

    task_rows: list[dict[str, Any]] = []
    for task in ops:
        if not isinstance(task, dict):
            continue
        task_key = str(task.get("task_id") or task.get("source_task_key") or "").strip()
        op_code = _operation_code(task)
        frozen_wc = _task_workcenter(task)
        wc_status = _task_resolution_status(task)
        warnings = list(task.get("warnings") or [])
        minutes = task.get("estimated_time_minutes")
        if minutes is None:
            minutes = task.get("estimated_minutes")

        blockers: list[str] = []
        row_warnings: list[str] = []
        if minutes is None:
            row_warnings.append("planning_minutes_source_missing")

        identity_ok = bool(task_key) and bool(op_code)
        if not identity_ok:
            blockers.append("unstable_task_identity")

        if wc_status == "not_required" or "WORKCENTER_NOT_REQUIRED" in warnings:
            status: EligibilityStatus = "not_required"
            task_rows.append(
                {
                    "task_key": task_key,
                    "canonical_task_type": task.get("process_type")
                    or task.get("canonical_task_type"),
                    "source_operation_code": op_code,
                    "workcenter_code": frozen_wc,
                    "requirement_source": REQUIREMENT_SOURCE,
                    "requirement_version": REQUIREMENT_VERSION,
                    "eligibility_status": status,
                    "eligible_employee_count": 0,
                    "eligible_employees": [],
                    "blockers": [],
                    "warnings": row_warnings,
                }
            )
            continue

        if wc_status == "ambiguous" or "WORKCENTER_MAPPING_AMBIGUOUS" in warnings:
            blockers.append("workcenter_ambiguous")
            status = "blocked_ambiguous_workcenter"
            task_rows.append(
                {
                    "task_key": task_key,
                    "canonical_task_type": task.get("process_type")
                    or task.get("canonical_task_type"),
                    "source_operation_code": op_code,
                    "workcenter_code": frozen_wc,
                    "requirement_source": REQUIREMENT_SOURCE,
                    "requirement_version": REQUIREMENT_VERSION,
                    "eligibility_status": status,
                    "eligible_employee_count": 0,
                    "eligible_employees": [],
                    "blockers": blockers,
                    "warnings": row_warnings,
                }
            )
            continue

        if not frozen_wc:
            blockers.append("workcenter_missing")
            status = "blocked_missing_workcenter"
            task_rows.append(
                {
                    "task_key": task_key,
                    "canonical_task_type": task.get("process_type")
                    or task.get("canonical_task_type"),
                    "source_operation_code": op_code,
                    "workcenter_code": None,
                    "requirement_source": REQUIREMENT_SOURCE,
                    "requirement_version": REQUIREMENT_VERSION,
                    "eligibility_status": status,
                    "eligible_employee_count": 0,
                    "eligible_employees": [],
                    "blockers": blockers,
                    "warnings": row_warnings,
                }
            )
            continue

        mapping = await _mapping_for(op_code) if op_code else None
        if mapping is None:
            blockers.append("missing_operation_requirements")
            status = "blocked_missing_requirements"
            task_rows.append(
                {
                    "task_key": task_key,
                    "canonical_task_type": task.get("process_type")
                    or task.get("canonical_task_type"),
                    "source_operation_code": op_code,
                    "workcenter_code": frozen_wc,
                    "requirement_source": REQUIREMENT_SOURCE,
                    "requirement_version": REQUIREMENT_VERSION,
                    "eligibility_status": status,
                    "eligible_employee_count": 0,
                    "eligible_employees": [],
                    "blockers": blockers,
                    "warnings": row_warnings,
                }
            )
            continue

        registry_code = str(mapping.get("operation_code") or "").strip()
        mode = (mapping.get("authorization_mode") or "hybrid").lower()
        required_skills = [
            str(s).strip() for s in (mapping.get("required_skill_codes") or []) if str(s).strip()
        ]
        allowed_wcs = [
            str(c).strip()
            for c in (mapping.get("allowed_workcenter_codes") or [])
            if str(c).strip()
        ]
        # Frozen WC must be among ORR allow-list when ORR has WC constraints
        # (current registry). Fail-closed if frozen WC not authorized by ORR.
        if allowed_wcs and frozen_wc not in allowed_wcs:
            # Historical freeze can diverge after ORR correction — still evaluate
            # against frozen WC + employee WC auth, but warn.
            row_warnings.append(
                f"frozen_workcenter_not_in_current_orr_allowlist:{frozen_wc}"
            )

        explicit_ids = await _explicit_ids(registry_code)
        eligible: list[dict[str, Any]] = []

        for emp in active_emps:
            emp_id = int(emp.id)
            auth = auth_by_emp[emp_id]
            emp_skills = set(auth.get("skill_codes") or [])
            emp_wcs = set(auth.get("workcenter_codes") or [])

            # Explicit frozen workcenter authorization required (not label guess).
            if frozen_wc not in emp_wcs:
                continue

            skill_ok = (not required_skills) or bool(set(required_skills) & emp_skills)
            # Match ORR hybrid rules for skills/resources using registry helper,
            # but force frozen WC (already checked above).
            mapping_for_match = {
                **mapping,
                "allowed_workcenter_codes": [frozen_wc],
            }
            rule_match = registry._employee_matches_mapping_rules(
                auth, mapping_for_match, machine_type=None
            )

            if mode == "explicit":
                is_eligible = emp_id in explicit_ids
            elif mode == "skill":
                is_eligible = rule_match and skill_ok
            else:
                if explicit_ids:
                    is_eligible = emp_id in explicit_ids or rule_match
                else:
                    is_eligible = rule_match

            if not is_eligible:
                continue

            matched_skills = sorted(set(required_skills) & emp_skills)
            provenance = [
                f"employee_workcenter_authorizations:{frozen_wc}",
                f"operation_resource_requirements:{registry_code}",
                f"authorization_mode:{mode}",
            ]
            if matched_skills:
                provenance.append(
                    "employee_skill_authorizations:" + ",".join(matched_skills)
                )
            if emp_id in explicit_ids:
                provenance.append(
                    f"operation_employee_authorizations:{registry_code}"
                )

            eligible.append(
                {
                    "employee_id": emp_id,
                    "display_name": emp.name,
                    "active_status": emp.status,
                    "matched_operation_capability": registry_code,
                    "matched_skills": matched_skills,
                    "matched_workcenter": frozen_wc,
                    "match_provenance": provenance,
                    "availability_status": "not_evaluated",
                }
            )

        # Deterministic order: name then id (already from query); re-sort for safety.
        eligible.sort(key=lambda e: (e["display_name"] or "", e["employee_id"]))

        if blockers:
            status = "blocked_missing_requirements"
        elif not eligible:
            status = "blocked_no_matching_employee"
            blockers.append("no_matching_employee")
        elif row_warnings:
            status = "ready_with_warnings"
        else:
            status = "ready"

        task_rows.append(
            {
                "task_key": task_key,
                "canonical_task_type": task.get("process_type")
                or task.get("canonical_task_type"),
                "source_operation_code": op_code,
                "workcenter_code": frozen_wc,
                "requirement_source": REQUIREMENT_SOURCE,
                "requirement_version": REQUIREMENT_VERSION,
                "authorization_mode": mode,
                "required_skill_codes": required_skills,
                "registry_operation_code": registry_code,
                "eligibility_status": status,
                "eligible_employee_count": len(eligible),
                "eligible_employees": eligible,
                "blockers": blockers,
                "warnings": row_warnings,
            }
        )

    ready_n = sum(1 for t in task_rows if t["eligibility_status"] in {"ready", "ready_with_warnings"})
    blocked_n = sum(1 for t in task_rows if str(t["eligibility_status"]).startswith("blocked_"))

    return {
        "mode": "employee_eligibility_read_model",
        "order_id": order_id,
        "execution_plan_id": plan.id,
        "status": "ok",
        "requirement_source": REQUIREMENT_SOURCE,
        "requirement_version": REQUIREMENT_VERSION,
        "operational_task_count": len(task_rows),
        "ready_or_warning_count": ready_n,
        "blocked_count": blocked_n,
        "tasks": task_rows,
        "side_effects": "none",
        "notes": [
            "Read-only. Does not assign, claim, start, or create sessions/actuals.",
            "Employee ≠ User. Matching uses explicit authorizations only.",
            "Planning minutes missing → warning only, not a blocker.",
            "Availability/calendar is not evaluated (availability_status=not_evaluated).",
        ],
    }
