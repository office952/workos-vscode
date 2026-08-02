"""Operational Resource Readiness (F7C) read model — ORR allow-list ∩ machines registry.

Uses:
  - frozen ``operational_tasks[]`` (workcenter, source_operation_code, warnings)
  - ``OperationalRegistryService.resolve_operation_mapping`` (ORR direct/alias resolution)
  - ``machines`` registry rows for the resolved ``allowed_resource_codes``
  - ``data.operational_workcenters`` for canonical workcenter identity

Never writes. Never assigns ``machine_code``. Never reopens DEC-009. Never invents a
formal ``machine_required|optional`` enum — ``resource_requirement_mode`` is derived
strictly from what ORR + machines registry already say.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.operational_workcenters import workcenter_registry_status
from models.execution_plan import ExecutionPlan
from models.operational_registry import MachineRegistry
from schemas.operational_resource_readiness import (
    CompatibleMachineCandidate,
    OperationalResourceReadinessResult,
    OperationalTaskResourceReadiness,
    ResourceRequirementMode,
)
from services.operational_registry_service import OperationalRegistryService

MACHINE_LIKE_KINDS = frozenset({"machine", "tool"})


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


def _operation_code(task: dict[str, Any]) -> str:
    return str(task.get("source_operation_code") or task.get("process_id") or "").strip()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


async def _load_machines_by_code(
    db: AsyncSession, codes: list[str]
) -> dict[str, MachineRegistry]:
    if not codes:
        return {}
    rows = (
        await db.execute(select(MachineRegistry).where(MachineRegistry.machine_code.in_(codes)))
    ).scalars().all()
    return {str(r.machine_code): r for r in rows}


def _candidate_from_row(
    row: MachineRegistry, *, is_default: bool
) -> CompatibleMachineCandidate:
    return CompatibleMachineCandidate(
        resource_code=row.machine_code,
        name=row.name,
        resource_kind=row.resource_kind or "machine",
        workcenter_code=row.workcenter_code,
        is_active=bool(row.is_active),
        is_available=bool(row.is_available),
        operational_status=row.operational_status,
        is_default=is_default,
    )


def _blocked_row(
    *,
    task_key: str | None,
    display_name: str | None,
    op_code: str,
    canonical_task_type: str | None,
    workcenter_code: str | None,
    wc_status: str,
    mode: ResourceRequirementMode,
    status: str,
    minutes: float | None,
    blockers: list[str],
    warnings: list[str],
    authorization_mode: str | None = None,
    registry_operation_code: str | None = None,
    allowed_resource_codes: list[str] | None = None,
    default_resource_code: str | None = None,
) -> OperationalTaskResourceReadiness:
    return OperationalTaskResourceReadiness(
        task_key=task_key,
        display_name=display_name,
        source_operation_code=op_code or None,
        canonical_task_type=canonical_task_type,
        workcenter_code=workcenter_code,
        workcenter_registry_status=wc_status,  # type: ignore[arg-type]
        resource_requirement_mode=mode,
        authorization_mode=authorization_mode,
        registry_operation_code=registry_operation_code,
        allowed_resource_codes=allowed_resource_codes or [],
        default_resource_code=default_resource_code,
        estimated_minutes=minutes,
        status=status,  # type: ignore[arg-type]
        blockers=blockers,
        warnings=warnings,
    )


async def build_operational_resource_readiness(
    db: AsyncSession,
    order_id: int,
) -> OperationalResourceReadinessResult:
    """Pure read model over materialized ``operational_tasks[]``. Zero writes."""
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one_or_none()
    if plan is None:
        return OperationalResourceReadinessResult(
            order_id=order_id,
            status="plan_not_found",
            notes=["No execution plan exists for this order."],
        )

    envelope = _parse_envelope(plan.tasks_json)
    # Operational source only — never fall back to planned_tasks[] (Faza rule).
    ops = envelope.get("operational_tasks")
    if not isinstance(ops, list):
        ops = []

    if not ops:
        return OperationalResourceReadinessResult(
            order_id=order_id,
            execution_plan_id=plan.id,
            status="blocked_not_materialized",
            notes=["Resource readiness requires materialized operational_tasks[]."],
        )

    registry = OperationalRegistryService(db)
    mapping_cache: dict[str, dict[str, Any] | None] = {}

    async def _mapping_for(op_code: str) -> dict[str, Any] | None:
        key = op_code.lower()
        if key not in mapping_cache:
            mapping_cache[key] = await registry.resolve_operation_mapping(op_code)
        return mapping_cache[key]

    task_op_codes = sorted(
        {_operation_code(t) for t in ops if isinstance(t, dict) and _operation_code(t)}
    )
    for op_code in task_op_codes:
        await _mapping_for(op_code)

    # Batch-load every machine referenced by any resolved ORR mapping — avoid N+1.
    all_resource_codes: set[str] = set()
    for mapping in mapping_cache.values():
        if not mapping:
            continue
        all_resource_codes.update(mapping.get("allowed_resource_codes") or [])
        default = mapping.get("default_resource_code")
        if default:
            all_resource_codes.add(str(default))
    machines_by_code = await _load_machines_by_code(db, sorted(all_resource_codes))

    task_rows: list[OperationalTaskResourceReadiness] = []
    for task in ops:
        if not isinstance(task, dict):
            continue
        task_key = str(task.get("task_id") or task.get("source_task_key") or "").strip() or None
        op_code = _operation_code(task)
        frozen_wc = _task_workcenter(task)
        minutes = task.get("estimated_time_minutes")
        if minutes is None:
            minutes = task.get("estimated_minutes")
        display_name = task.get("display_name") or task.get("name")
        canonical_task_type = task.get("process_type") or task.get("canonical_task_type")

        warnings: list[str] = []
        if minutes is None:
            warnings.append("PLANNING_MINUTES_SOURCE_MISSING")

        wc_status = workcenter_registry_status(frozen_wc)
        if wc_status == "non_canonical":
            # WC_CNC must never be silently treated as WC_CNC_ROUTING — warn only.
            warnings.append(f"WORKCENTER_NON_CANONICAL:{frozen_wc}")
        elif wc_status == "missing":
            # Unknown code — flagged, never guessed into a canonical mapping.
            warnings.append(f"WORKCENTER_UNKNOWN:{frozen_wc}")

        if wc_status == "empty":
            task_rows.append(
                _blocked_row(
                    task_key=task_key,
                    display_name=display_name,
                    op_code=op_code,
                    canonical_task_type=canonical_task_type,
                    workcenter_code=None,
                    wc_status="empty",
                    mode="unknown_resource_policy",
                    status="missing_workcenter",
                    minutes=minutes,
                    blockers=["workcenter_missing"],
                    warnings=warnings,
                )
            )
            continue

        mapping = await _mapping_for(op_code) if op_code else None
        if mapping is None:
            task_rows.append(
                _blocked_row(
                    task_key=task_key,
                    display_name=display_name,
                    op_code=op_code,
                    canonical_task_type=canonical_task_type,
                    workcenter_code=frozen_wc,
                    wc_status=wc_status,
                    mode="unknown_resource_policy",
                    status="unknown_resource_policy",
                    minutes=minutes,
                    blockers=["orr_mapping_missing"],
                    warnings=warnings,
                )
            )
            continue

        registry_code = str(mapping.get("operation_code") or "").strip() or None
        authorization_mode = mapping.get("authorization_mode")
        allowed_wcs = _dedupe(
            [str(c).strip() for c in (mapping.get("allowed_workcenter_codes") or []) if str(c).strip()]
        )
        allowed_resources = _dedupe(
            [str(c).strip() for c in (mapping.get("allowed_resource_codes") or []) if str(c).strip()]
        )
        default_resource = mapping.get("default_resource_code")
        default_resource = str(default_resource).strip() if default_resource else None

        if len(allowed_wcs) > 1:
            task_rows.append(
                _blocked_row(
                    task_key=task_key,
                    display_name=display_name,
                    op_code=op_code,
                    canonical_task_type=canonical_task_type,
                    workcenter_code=frozen_wc,
                    wc_status=wc_status,
                    mode="unknown_resource_policy",
                    status="ambiguous_mapping",
                    minutes=minutes,
                    blockers=["workcenter_mapping_ambiguous"],
                    warnings=warnings,
                    authorization_mode=authorization_mode,
                    registry_operation_code=registry_code,
                    allowed_resource_codes=allowed_resources,
                    default_resource_code=default_resource,
                )
            )
            continue

        if allowed_wcs and frozen_wc and frozen_wc not in allowed_wcs:
            # Historical freeze can diverge from a later ORR correction — evaluate
            # against the frozen WC but surface the drift, never silently patch it.
            warnings.append(f"FROZEN_WORKCENTER_NOT_IN_ORR_ALLOWLIST:{frozen_wc}")

        found_kinds = {
            (machines_by_code[c].resource_kind or "machine")
            for c in allowed_resources
            if c in machines_by_code
        }
        missing_codes = [c for c in allowed_resources if c not in machines_by_code]
        if missing_codes:
            warnings.append(f"ORR_RESOURCE_CODE_NOT_IN_REGISTRY:{','.join(missing_codes)}")

        if not allowed_resources:
            mode: ResourceRequirementMode = "workcenter_only"
        elif not found_kinds:
            # ORR declares resource codes, but none exist in the machines registry —
            # cannot honestly confirm kind, so we do not guess "workcenter_only".
            mode = "unknown_resource_policy"
        elif found_kinds <= {"work_area"}:
            mode = "workcenter_only"
        else:
            mode = "orr_allowlist"

        machine_candidates = [
            _candidate_from_row(machines_by_code[c], is_default=(c == default_resource))
            for c in allowed_resources
            if c in machines_by_code
            and (machines_by_code[c].resource_kind or "machine") in MACHINE_LIKE_KINDS
            and machines_by_code[c].is_active
        ]
        work_area_candidates = [
            _candidate_from_row(machines_by_code[c], is_default=(c == default_resource))
            for c in allowed_resources
            if c in machines_by_code
            and (machines_by_code[c].resource_kind or "machine") == "work_area"
            and machines_by_code[c].is_active
        ]

        blockers: list[str] = []
        if mode == "workcenter_only":
            status = "workcenter_only"
        elif mode == "unknown_resource_policy":
            status = "unknown_resource_policy"
            blockers.append("orr_resource_codes_unregistered")
        else:  # orr_allowlist
            if machine_candidates:
                status = "ready_with_warnings" if warnings else "ready"
            elif default_resource and default_resource in machines_by_code and not bool(
                machines_by_code[default_resource].is_active
            ):
                status = "machine_unavailable"
                blockers.append("default_resource_inactive")
            else:
                status = "machine_required_but_none_compatible"
                blockers.append("no_compatible_machine_registered")

        task_rows.append(
            OperationalTaskResourceReadiness(
                task_key=task_key,
                display_name=display_name,
                source_operation_code=op_code or None,
                canonical_task_type=canonical_task_type,
                workcenter_code=frozen_wc,
                workcenter_registry_status=wc_status,  # type: ignore[arg-type]
                resource_requirement_mode=mode,
                authorization_mode=authorization_mode,
                registry_operation_code=registry_code,
                allowed_resource_codes=allowed_resources,
                default_resource_code=default_resource,
                compatible_machine_candidates=machine_candidates,
                work_area_candidates=work_area_candidates,
                estimated_minutes=minutes,
                status=status,  # type: ignore[arg-type]
                blockers=blockers,
                warnings=warnings,
            )
        )

    ready_n = sum(1 for t in task_rows if t.status == "ready")
    warning_n = sum(
        1 for t in task_rows if t.status in {"ready_with_warnings", "workcenter_only"}
    )
    blocked_n = sum(
        1
        for t in task_rows
        if t.status
        in {
            "missing_workcenter",
            "unknown_resource_policy",
            "machine_required_but_none_compatible",
            "machine_optional_no_candidate",
            "machine_unavailable",
            "maintenance_conflict",
            "ambiguous_mapping",
        }
    )

    return OperationalResourceReadinessResult(
        order_id=order_id,
        execution_plan_id=plan.id,
        status="ok",
        operational_task_count=len(task_rows),
        ready_count=ready_n,
        warning_count=warning_n,
        blocked_count=blocked_n,
        tasks=task_rows,
        notes=[
            "Read-only. Does not assign machine_code, does not create sessions/assignments.",
            "resource_requirement_mode is derived from ORR truth only — no formal "
            "machine_required|optional|workcenter_only enum exists in the registry "
            "(Owner decision pending).",
            "Planning minutes missing is a capacity warning, not a commercial blocker.",
            "workcenter_only means every ORR-allowed resource is work_area-kind — "
            "absence of a machine candidate is expected, not a gap.",
        ],
    )
