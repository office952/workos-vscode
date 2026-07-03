"""Execution plan operational readiness evaluation (Step 9.3.4.c).

Pure/read-only classification of whether an order's execution plan has
materialized operational tasks ready for backend consumers. No DB writes,
no sessions, no ExecutionReality, no Employee Mobile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException
from models.execution_plan import ExecutionPlan
from services.execution_plan_task_parser import parse_tasks_json_raw

STATUS_NO_EXECUTION_PLAN = "no_execution_plan"
STATUS_INVALID_TASKS_JSON = "invalid_tasks_json"
STATUS_LEGACY_OPERATIONAL_READY = "legacy_operational_ready"
STATUS_V2_NOT_MATERIALIZED = "v2_not_materialized"
STATUS_V2_OPERATIONAL_READY = "v2_operational_ready"
STATUS_V2_OPERATIONAL_EMPTY = "v2_operational_empty"
STATUS_BLOCKED_TASK_GRAPH = "blocked_task_graph"
STATUS_UNKNOWN_FORMAT = "unknown_format"

BLOCKER_EXECUTION_PLAN_MISSING = "EXECUTION_PLAN_MISSING"
BLOCKER_EXECUTION_PLAN_TASKS_JSON_INVALID = "EXECUTION_PLAN_TASKS_JSON_INVALID"
BLOCKER_OPERATIONAL_TASKS_NOT_MATERIALIZED = "OPERATIONAL_TASKS_NOT_MATERIALIZED"
BLOCKER_OPERATIONAL_TASKS_EMPTY_AFTER_MATERIALIZATION = (
    "OPERATIONAL_TASKS_EMPTY_AFTER_MATERIALIZATION"
)
BLOCKER_OPERATIONAL_TASK_DEPENDENCY_MISSING = "OPERATIONAL_TASK_DEPENDENCY_MISSING"
BLOCKER_OPERATIONAL_READINESS_NOT_READY = "OPERATIONAL_READINESS_NOT_READY"

NEXT_ACTION_GENERATE_EXECUTION_PLAN = "generate_execution_plan"
NEXT_ACTION_MATERIALIZE_V2_OPERATIONAL_TASKS = "materialize_v2_operational_tasks"

PROVENANCE_STEP = "execution_plan_operational_readiness.1"

MUTATION_ALLOWED_STATUSES = frozenset(
    {
        STATUS_LEGACY_OPERATIONAL_READY,
        STATUS_V2_OPERATIONAL_READY,
    }
)


@dataclass
class ExecutionOperationalReadinessResult:
    order_id: int | None
    execution_plan_id: int | None
    format: str
    status: str
    operational_tasks_count: int
    execution_tasks_created: bool | None
    operational_tasks_materialized: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_action: str | None = None
    provenance: list[dict[str, Any]] = field(default_factory=list)


def _provenance_entry(*, format: str, status: str) -> list[dict[str, Any]]:
    return [
        {
            "source": PROVENANCE_STEP,
            "format": format,
            "status": status,
        }
    ]


def _dependency_blockers(operational_tasks: list[dict[str, Any]]) -> list[str]:
    task_ids = {
        str(task.get("task_id")).strip()
        for task in operational_tasks
        if str(task.get("task_id") or "").strip()
    }
    blockers: list[str] = []
    for task in operational_tasks:
        task_id = str(task.get("task_id") or "").strip()
        if not task_id:
            continue
        deps = task.get("depends_on_task_ids")
        if not isinstance(deps, list):
            continue
        for dep in deps:
            dep_id = str(dep).strip()
            if dep_id and dep_id not in task_ids:
                blockers.append(BLOCKER_OPERATIONAL_TASK_DEPENDENCY_MISSING)
                return blockers
    return blockers


def _invalid_json_status(parsed_format: str, parse_errors: list[str]) -> str:
    if parsed_format != "invalid":
        return STATUS_UNKNOWN_FORMAT
    if any("tasks_json_unrecognized_shape" in err for err in parse_errors):
        return STATUS_UNKNOWN_FORMAT
    return STATUS_INVALID_TASKS_JSON


def evaluate_execution_plan_operational_readiness(
    plan: ExecutionPlan | None,
) -> ExecutionOperationalReadinessResult:
    """Classify execution plan operational readiness — read-only, no side effects."""
    if plan is None:
        return ExecutionOperationalReadinessResult(
            order_id=None,
            execution_plan_id=None,
            format="none",
            status=STATUS_NO_EXECUTION_PLAN,
            operational_tasks_count=0,
            execution_tasks_created=None,
            operational_tasks_materialized=False,
            blockers=[BLOCKER_EXECUTION_PLAN_MISSING],
            warnings=[],
            next_action=NEXT_ACTION_GENERATE_EXECUTION_PLAN,
            provenance=_provenance_entry(format="none", status=STATUS_NO_EXECUTION_PLAN),
        )

    parsed = parse_tasks_json_raw(plan.tasks_json)
    operational_tasks = list(parsed.operational_tasks)
    operational_count = len(operational_tasks)
    warnings = list(parsed.parse_errors)

    if parsed.format == "invalid":
        status = _invalid_json_status(parsed.format, parsed.parse_errors)
        blockers = [BLOCKER_EXECUTION_PLAN_TASKS_JSON_INVALID]
        if status == STATUS_UNKNOWN_FORMAT:
            blockers = []
        return ExecutionOperationalReadinessResult(
            order_id=plan.order_id,
            execution_plan_id=plan.id,
            format=parsed.format,
            status=status,
            operational_tasks_count=0,
            execution_tasks_created=None,
            operational_tasks_materialized=False,
            blockers=blockers,
            warnings=warnings,
            next_action=None,
            provenance=_provenance_entry(format=parsed.format, status=status),
        )

    if parsed.format == "legacy_list":
        materialized = operational_count > 0
        return ExecutionOperationalReadinessResult(
            order_id=plan.order_id,
            execution_plan_id=plan.id,
            format=parsed.format,
            status=STATUS_LEGACY_OPERATIONAL_READY,
            operational_tasks_count=operational_count,
            execution_tasks_created=None,
            operational_tasks_materialized=materialized,
            blockers=[],
            warnings=warnings,
            next_action=None,
            provenance=_provenance_entry(
                format=parsed.format,
                status=STATUS_LEGACY_OPERATIONAL_READY,
            ),
        )

    if parsed.format == "v2_envelope":
        envelope = parsed.envelope or {}
        execution_tasks_created = bool(envelope.get("execution_tasks_created"))

        if execution_tasks_created and operational_count == 0:
            return ExecutionOperationalReadinessResult(
                order_id=plan.order_id,
                execution_plan_id=plan.id,
                format=parsed.format,
                status=STATUS_V2_OPERATIONAL_EMPTY,
                operational_tasks_count=0,
                execution_tasks_created=True,
                operational_tasks_materialized=False,
                blockers=[BLOCKER_OPERATIONAL_TASKS_EMPTY_AFTER_MATERIALIZATION],
                warnings=warnings,
                next_action=None,
                provenance=_provenance_entry(
                    format=parsed.format,
                    status=STATUS_V2_OPERATIONAL_EMPTY,
                ),
            )

        if operational_count == 0:
            return ExecutionOperationalReadinessResult(
                order_id=plan.order_id,
                execution_plan_id=plan.id,
                format=parsed.format,
                status=STATUS_V2_NOT_MATERIALIZED,
                operational_tasks_count=0,
                execution_tasks_created=execution_tasks_created,
                operational_tasks_materialized=False,
                blockers=[BLOCKER_OPERATIONAL_TASKS_NOT_MATERIALIZED],
                warnings=warnings,
                next_action=NEXT_ACTION_MATERIALIZE_V2_OPERATIONAL_TASKS,
                provenance=_provenance_entry(
                    format=parsed.format,
                    status=STATUS_V2_NOT_MATERIALIZED,
                ),
            )

        dep_blockers = _dependency_blockers(operational_tasks)
        if dep_blockers:
            return ExecutionOperationalReadinessResult(
                order_id=plan.order_id,
                execution_plan_id=plan.id,
                format=parsed.format,
                status=STATUS_BLOCKED_TASK_GRAPH,
                operational_tasks_count=operational_count,
                execution_tasks_created=execution_tasks_created,
                operational_tasks_materialized=True,
                blockers=dep_blockers,
                warnings=warnings,
                next_action=None,
                provenance=_provenance_entry(
                    format=parsed.format,
                    status=STATUS_BLOCKED_TASK_GRAPH,
                ),
            )

        return ExecutionOperationalReadinessResult(
            order_id=plan.order_id,
            execution_plan_id=plan.id,
            format=parsed.format,
            status=STATUS_V2_OPERATIONAL_READY,
            operational_tasks_count=operational_count,
            execution_tasks_created=execution_tasks_created,
            operational_tasks_materialized=True,
            blockers=[],
            warnings=warnings,
            next_action=None,
            provenance=_provenance_entry(
                format=parsed.format,
                status=STATUS_V2_OPERATIONAL_READY,
            ),
        )

    return ExecutionOperationalReadinessResult(
        order_id=plan.order_id,
        execution_plan_id=plan.id,
        format=parsed.format,
        status=STATUS_UNKNOWN_FORMAT,
        operational_tasks_count=operational_count,
        execution_tasks_created=None,
        operational_tasks_materialized=False,
        blockers=[],
        warnings=warnings,
        next_action=None,
        provenance=_provenance_entry(format=parsed.format, status=STATUS_UNKNOWN_FORMAT),
    )


def readiness_result_to_api_fields(
    result: ExecutionOperationalReadinessResult,
) -> dict[str, Any]:
    """Map readiness result to optional execution plan API payload fields."""
    return {
        "operational_readiness_status": result.status,
        "operational_tasks_count": result.operational_tasks_count,
        "operational_readiness_blockers": list(result.blockers),
        "operational_readiness_next_action": result.next_action,
        "operational_tasks_materialized": result.operational_tasks_materialized,
    }


def operational_readiness_block_message(result: ExecutionOperationalReadinessResult) -> str:
    if result.status == STATUS_V2_NOT_MATERIALIZED:
        return "Operational tasks are not materialized for this V2 execution plan."
    if result.status == STATUS_V2_OPERATIONAL_EMPTY:
        return "Operational tasks are empty after materialization."
    if result.status == STATUS_BLOCKED_TASK_GRAPH:
        return "Operational task dependency graph is blocked."
    if result.status == STATUS_INVALID_TASKS_JSON:
        return "Execution plan tasks_json is invalid."
    if result.status == STATUS_UNKNOWN_FORMAT:
        return "Execution plan tasks_json has an unrecognized format."
    if result.status == STATUS_NO_EXECUTION_PLAN:
        return "Execution plan is missing for this order."
    return "Operational readiness is not satisfied for this execution plan."


def operational_readiness_blocked_http_exception(
    result: ExecutionOperationalReadinessResult,
) -> HTTPException:
    blockers = list(result.blockers)
    if not blockers:
        blockers = [BLOCKER_OPERATIONAL_READINESS_NOT_READY]
    return HTTPException(
        status_code=422,
        detail={
            "error": "operational_readiness_blocked",
            "operational_readiness_status": result.status,
            "blockers": blockers,
            "next_action": result.next_action,
            "message": operational_readiness_block_message(result),
        },
    )


def assert_operational_mutation_allowed(
    plan: ExecutionPlan | None,
) -> ExecutionOperationalReadinessResult:
    """Raise HTTP 404/422 when plan-level operational readiness blocks mutation."""
    result = evaluate_execution_plan_operational_readiness(plan)
    if result.status == STATUS_NO_EXECUTION_PLAN:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "plan_not_found",
                "operational_readiness_status": result.status,
                "blockers": list(result.blockers),
                "next_action": result.next_action,
                "message": operational_readiness_block_message(result),
            },
        )
    if result.status not in MUTATION_ALLOWED_STATUSES:
        raise operational_readiness_blocked_http_exception(result)
    return result
