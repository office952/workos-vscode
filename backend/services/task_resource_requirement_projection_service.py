"""Read-only Task Resource Requirement projection.

Surfaces known / derived / unknown demand fields from ExecutionPlan
operational_tasks without mutating tasks_json or writing resource commitments.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.execution_plan import ExecutionPlan
from schemas.task_resource_requirement_projection import (
    FieldProvenance,
    PlanResourceRequirementProjection,
    PlanResourceRequirementSummary,
    ResourceModeHint,
    ResourceRequirementsStatus,
    TaskResourceRequirementProjection,
)
from services.execution_plan_task_parser import operational_tasks_only
from services.operational_catalog import OPERATIONAL_WORKCENTERS

# Soft family → mode hint (Owner realignment). HYBRID has no safe hint.
_HYBRID_WORKCENTERS: frozenset[str] = frozenset(
    {"WC_METAL_FAB", "WC_VINYL_APPLICATION"}
)
_MACHINE_BOUND_WORKCENTERS: frozenset[str] = frozenset(
    {
        "WC_CNC_ROUTING",
        "WC_LETTER_FORMING",
        "WC_LASER_CUTTING",
        "WC_CUT",
        "WC_PRINT",
        "WC_LAMINATE",
    }
)
_MANUAL_WORKSPACE_WORKCENTERS: frozenset[str] = frozenset(
    {"WC_ASSEMBLY", "WC_LED_ASSEMBLY"}
)
_PERSON_DRIVEN_WORKCENTERS: frozenset[str] = frozenset({"WC_PREPRESS"})
_FIELD_WORKCENTERS: frozenset[str] = frozenset({"WC_FIELD_INSTALLATION"})

# Demand fields from the readonly contract that are not yet on tasks.
_LATER_DEMAND_FIELDS: tuple[str, ...] = (
    "resource_mode",
    "required_people_min",
    "workspace_class",
    "machine_capability_code",
    "batch_eligible",
)

_WC_LABELS: dict[str, str] = {
    str(w.get("workcenter_code") or ""): str(w.get("label_ro") or "")
    for w in OPERATIONAL_WORKCENTERS
    if w.get("workcenter_code")
}


class TaskResourceRequirementPlanNotFoundError(LookupError):
    """execution_plan row missing."""


class TaskResourceRequirementTaskNotFoundError(LookupError):
    """task_key not present in operational_tasks[]."""


def _task_key_of(task: dict[str, Any]) -> str:
    return str(
        task.get("task_id")
        or task.get("deterministic_task_key")
        or task.get("task_key")
        or ""
    ).strip()


def _workcenter_of(task: dict[str, Any]) -> str | None:
    mr = task.get("machine_requirement")
    if isinstance(mr, dict):
        wc = mr.get("workcenter") or mr.get("workcenter_code")
        if wc is not None and str(wc).strip():
            return str(wc).strip()
    wc = task.get("workcenter") or task.get("workcenter_code")
    if wc is not None and str(wc).strip():
        return str(wc).strip()
    return None


def _operation_code_of(task: dict[str, Any]) -> str | None:
    for key in ("source_operation_code", "process_id", "operation_code"):
        val = task.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def soft_resource_mode_hint(workcenter_code: str | None) -> ResourceModeHint:
    """Non-authoritative hint. HYBRID → UNKNOWN. Never invent from operation name."""
    wc = (workcenter_code or "").strip()
    if not wc:
        return "UNKNOWN"
    if wc in _HYBRID_WORKCENTERS:
        return "UNKNOWN"
    if wc in _MACHINE_BOUND_WORKCENTERS:
        return "MACHINE_BOUND"
    if wc in _MANUAL_WORKSPACE_WORKCENTERS:
        return "MANUAL_WORKSPACE"
    if wc in _PERSON_DRIVEN_WORKCENTERS:
        return "PERSON_DRIVEN"
    if wc in _FIELD_WORKCENTERS:
        return "FIELD"
    return "UNKNOWN"


def _classify_status(
    *,
    task_key: str,
    workcenter_code: str | None,
    duration_known: bool,
    duration_source_known: bool,
    mode_hint: ResourceModeHint,
) -> ResourceRequirementsStatus:
    if not task_key:
        return "UNKNOWN"
    # Soft NOT_APPLICABLE reserved; shop volumetric tasks always need some resource story.
    if not workcenter_code and not duration_known:
        return "UNKNOWN"
    safe_mode = mode_hint != "UNKNOWN"
    if (
        workcenter_code
        and duration_known
        and duration_source_known
        and safe_mode
    ):
        return "KNOWN_MINIMAL"
    if workcenter_code or duration_known or safe_mode:
        return "PARTIAL"
    return "UNKNOWN"


def project_task_resource_requirements(
    task: dict[str, Any],
    *,
    execution_plan_id: int,
) -> TaskResourceRequirementProjection:
    """Pure projection for one operational task dict."""
    task_key = _task_key_of(task)
    operation_code = _operation_code_of(task)
    workcenter_code = _workcenter_of(task)
    workcenter_label = _WC_LABELS.get(workcenter_code or "") or None

    raw_minutes = task.get("estimated_time_minutes")
    if raw_minutes is None:
        raw_minutes = task.get("estimated_minutes")
    estimated: float | None
    if raw_minutes is None:
        estimated = None
    else:
        try:
            estimated = float(raw_minutes)
        except (TypeError, ValueError):
            estimated = None

    planning_source = task.get("planning_minutes_source")
    if planning_source is not None:
        planning_source = str(planning_source).strip() or None

    mode_hint = soft_resource_mode_hint(workcenter_code)
    duration_known = estimated is not None
    duration_source_known = planning_source is not None

    status = _classify_status(
        task_key=task_key,
        workcenter_code=workcenter_code,
        duration_known=duration_known,
        duration_source_known=duration_source_known,
        mode_hint=mode_hint,
    )

    known: list[str] = []
    unknown: list[str] = []
    derived: list[str] = []
    provenance: list[FieldProvenance] = []

    if task_key:
        known.append("task_key")
        provenance.append(
            FieldProvenance(
                field="task_key",
                source="EXECUTION_PLAN_SNAPSHOT",
                derived=False,
                confidence="CONFIRMED",
            )
        )
    else:
        unknown.append("task_key")

    if operation_code:
        known.append("operation_code")
        provenance.append(
            FieldProvenance(
                field="operation_code",
                source="EXECUTION_PLAN_SNAPSHOT",
                derived=False,
                confidence="CONFIRMED",
            )
        )
    else:
        unknown.append("operation_code")

    if workcenter_code:
        known.append("workcenter_code")
        provenance.append(
            FieldProvenance(
                field="workcenter_code",
                source="EXECUTION_PLAN_SNAPSHOT",
                derived=False,
                confidence="CONFIRMED",
            )
        )
        if workcenter_label:
            known.append("workcenter_label")
            provenance.append(
                FieldProvenance(
                    field="workcenter_label",
                    source="WORKCENTER_REGISTRY",
                    derived=True,
                    confidence="SAFE_DERIVATION",
                )
            )
            derived.append("workcenter_label")
    else:
        unknown.append("workcenter_code")

    if duration_known:
        known.append("estimated_time_minutes")
        provenance.append(
            FieldProvenance(
                field="estimated_time_minutes",
                source="EXECUTION_PLAN_SNAPSHOT",
                derived=False,
                confidence="CONFIRMED",
            )
        )
    else:
        unknown.append("estimated_time_minutes")

    if duration_source_known:
        known.append("planning_minutes_source")
        provenance.append(
            FieldProvenance(
                field="planning_minutes_source",
                source="EXECUTION_PLAN_SNAPSHOT",
                derived=False,
                confidence="CONFIRMED",
            )
        )
    else:
        unknown.append("planning_minutes_source")

    if mode_hint != "UNKNOWN":
        derived.append("resource_mode_hint")
        provenance.append(
            FieldProvenance(
                field="resource_mode_hint",
                source="LEGACY_INFERENCE",
                derived=True,
                confidence="SAFE_DERIVATION",
            )
        )
    else:
        provenance.append(
            FieldProvenance(
                field="resource_mode_hint",
                source="UNKNOWN",
                derived=True,
                confidence="UNKNOWN",
            )
        )

    for field in _LATER_DEMAND_FIELDS:
        if field not in unknown:
            unknown.append(field)

    # Stable ordering for lists
    known = sorted(set(known))
    unknown = sorted(set(unknown))
    derived = sorted(set(derived))

    return TaskResourceRequirementProjection(
        execution_plan_id=execution_plan_id,
        task_key=task_key,
        operation_code=operation_code,
        workcenter_code=workcenter_code,
        workcenter_label=workcenter_label,
        estimated_time_minutes=estimated,
        planning_minutes_source=planning_source,
        resource_requirements_status=status,
        resource_mode_hint=mode_hint,
        known_fields=known,
        unknown_fields=unknown,
        derived_fields=derived,
        source_provenance=provenance,
    )


def _summarize(
    tasks: list[TaskResourceRequirementProjection],
) -> PlanResourceRequirementSummary:
    summary = PlanResourceRequirementSummary(total_tasks=len(tasks))
    for t in tasks:
        if t.resource_requirements_status == "KNOWN_MINIMAL":
            summary.known_minimal += 1
        elif t.resource_requirements_status == "PARTIAL":
            summary.partial += 1
        elif t.resource_requirements_status == "NOT_APPLICABLE":
            summary.not_applicable += 1
        else:
            summary.unknown += 1
        if t.estimated_time_minutes is not None:
            summary.duration_known += 1
        else:
            summary.duration_unknown += 1
        if t.resource_mode_hint != "UNKNOWN":
            summary.safe_mode_hint += 1
        if (t.workcenter_code or "") in _HYBRID_WORKCENTERS:
            summary.hybrid_unknown_mode += 1
    return summary


async def project_plan_resource_requirements(
    db: AsyncSession,
    *,
    plan_id: int,
    task_key: str | None = None,
) -> PlanResourceRequirementProjection:
    """Load plan operational_tasks and project resource requirements (read-only)."""
    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.id == plan_id))
    ).scalar_one_or_none()
    if plan is None:
        raise TaskResourceRequirementPlanNotFoundError("execution_plan_not_found")

    try:
        ops = operational_tasks_only(plan.tasks_json)
    except Exception as exc:
        raise TaskResourceRequirementTaskNotFoundError(
            "tasks_json_unreadable"
        ) from exc

    # Stable ordering by sequence then task_key
    def _sort_key(t: dict[str, Any]) -> tuple[int, str]:
        seq = t.get("sequence_index")
        try:
            seq_i = int(seq) if seq is not None else 10**9
        except (TypeError, ValueError):
            seq_i = 10**9
        return (seq_i, _task_key_of(t))

    ordered = sorted(ops, key=_sort_key)
    projections = [
        project_task_resource_requirements(t, execution_plan_id=plan_id)
        for t in ordered
        if _task_key_of(t)
    ]

    filter_key = (task_key or "").strip()
    if filter_key:
        projections = [p for p in projections if p.task_key == filter_key]
        if not projections:
            raise TaskResourceRequirementTaskNotFoundError(
                "task_key_not_in_operational_tasks"
            )

    return PlanResourceRequirementProjection(
        execution_plan_id=plan_id,
        order_id=plan.order_id,
        summary=_summarize(projections),
        tasks=projections,
    )
