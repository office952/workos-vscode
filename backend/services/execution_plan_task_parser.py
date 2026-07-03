"""Shared execution plan tasks_json parser and V2 operational task materialization (Step 9.3.4.a)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from schemas.execution_plan_v2 import PLANNING_MINUTES_WARNING
from schemas.execution_plan_v2_materialize import (
    OPERATIONAL_TASK_SOURCE,
    OPERATIONAL_STATUS_PENDING,
    V2_LAYER_ID,
)

V2_ENVELOPE_SOURCE = "order_snapshot_v2"


@dataclass
class ParsedExecutionPlanTasks:
    format: str
    operational_tasks: list[dict[str, Any]] = field(default_factory=list)
    envelope: dict[str, Any] | None = None
    planned_tasks: list[dict[str, Any]] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)


def _is_v2_envelope(parsed: Any) -> bool:
    return isinstance(parsed, dict) and parsed.get("source") == V2_ENVELOPE_SOURCE


def parse_tasks_json_raw(raw: str | None) -> ParsedExecutionPlanTasks:
    """Parse execution_plan.tasks_json into operational tasks and envelope metadata."""
    if raw is None or not str(raw).strip():
        return ParsedExecutionPlanTasks(
            format="invalid",
            parse_errors=["tasks_json_empty"],
        )

    try:
        parsed = json.loads(str(raw))
    except (TypeError, ValueError) as exc:
        return ParsedExecutionPlanTasks(
            format="invalid",
            parse_errors=[f"tasks_json_invalid:{exc}"],
        )

    if isinstance(parsed, list):
        operational = [item for item in parsed if isinstance(item, dict)]
        return ParsedExecutionPlanTasks(
            format="legacy_list",
            operational_tasks=operational,
            envelope=None,
            planned_tasks=[],
        )

    if _is_v2_envelope(parsed):
        planned = [
            item for item in (parsed.get("planned_tasks") or []) if isinstance(item, dict)
        ]
        operational_raw = parsed.get("operational_tasks")
        operational: list[dict[str, Any]] = []
        if isinstance(operational_raw, list):
            operational = [item for item in operational_raw if isinstance(item, dict)]
        return ParsedExecutionPlanTasks(
            format="v2_envelope",
            operational_tasks=operational,
            envelope=parsed,
            planned_tasks=planned,
        )

    return ParsedExecutionPlanTasks(
        format="invalid",
        parse_errors=["tasks_json_unrecognized_shape"],
    )


def load_operational_tasks_from_plan_json(
    raw: str | None,
) -> tuple[list[dict[str, Any]], ParsedExecutionPlanTasks]:
    """Return operational task dicts and parse metadata."""
    parsed = parse_tasks_json_raw(raw)
    return list(parsed.operational_tasks), parsed


def operational_tasks_only(raw: str | None) -> list[dict[str, Any]]:
    """Convenience read helper for backend operational consumers."""
    tasks, _parsed = load_operational_tasks_from_plan_json(raw)
    return tasks


def serialize_operational_tasks_to_plan_json(
    parsed: ParsedExecutionPlanTasks,
    operational_tasks: list[dict[str, Any]],
) -> str:
    """Write operational tasks back preserving legacy list or V2 envelope shape."""
    if parsed.format == "legacy_list":
        return json.dumps(operational_tasks, ensure_ascii=False)
    if parsed.format == "v2_envelope" and parsed.envelope is not None:
        envelope = dict(parsed.envelope)
        envelope["operational_tasks"] = operational_tasks
        return json.dumps(envelope, ensure_ascii=False)
    raise ValueError("Cannot serialize operational tasks for invalid execution plan JSON shape")


def compute_activation_hash(envelope: dict[str, Any]) -> str:
    """Stable hash of planning subset used for materialization idempotency audit."""
    canonical = {
        "planned_tasks": envelope.get("planned_tasks") or [],
        "dependencies": envelope.get("dependencies") or [],
        "source_content_hash": envelope.get("source_content_hash"),
    }
    payload = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def _machine_type_from_planned(planned: dict[str, Any]) -> str:
    machine_req = planned.get("machine_requirement")
    if isinstance(machine_req, dict):
        workcenter = machine_req.get("workcenter")
        if workcenter:
            return str(workcenter)
    return ""


def _eligible_role_from_planned(planned: dict[str, Any]) -> str | None:
    role_req = planned.get("employee_role_requirement")
    if isinstance(role_req, dict):
        role_code = role_req.get("role_code")
        if role_code:
            return str(role_code)
    return None


def materialize_operational_tasks_from_v2_envelope(
    envelope: dict[str, Any],
    *,
    execution_plan_id: int,
    order_id: int,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Build flat operational task dicts from V2 planned_tasks — does not persist."""
    warnings: list[str] = []
    blockers: list[str] = []

    planned_tasks = [
        item for item in (envelope.get("planned_tasks") or []) if isinstance(item, dict)
    ]
    if not planned_tasks:
        blockers.append("planned_tasks_empty")
        return [], warnings, blockers

    task_keys: list[str] = []
    for idx, planned in enumerate(planned_tasks):
        task_key = str(planned.get("task_key") or "").strip()
        if not task_key:
            blockers.append(f"missing_task_key:index_{idx}")
            continue
        if task_key in task_keys:
            blockers.append(f"duplicate_task_key:{task_key}")
        task_keys.append(task_key)

    if blockers:
        return [], warnings, blockers

    key_set = set(task_keys)
    for planned in planned_tasks:
        task_key = str(planned.get("task_key")).strip()
        dep_keys = [
            str(key).strip()
            for key in (planned.get("depends_on_task_keys") or [])
            if str(key).strip()
        ]
        for dep_key in dep_keys:
            if dep_key not in key_set:
                blockers.append(f"unresolved_dependency:{task_key}->{dep_key}")

    if blockers:
        return [], warnings, blockers

    operational_tasks: list[dict[str, Any]] = []
    for planned in planned_tasks:
        task_key = str(planned.get("task_key")).strip()
        label = str(planned.get("label") or task_key.replace("_", " ").title())
        technical_name = str(planned.get("source_task_rule_code") or task_key).strip() or task_key

        estimated_raw = planned.get("estimated_minutes")
        task_warnings = list(planned.get("warnings") or [])
        if estimated_raw is None:
            if PLANNING_MINUTES_WARNING not in task_warnings:
                task_warnings.append(PLANNING_MINUTES_WARNING)
            if PLANNING_MINUTES_WARNING not in warnings:
                warnings.append(PLANNING_MINUTES_WARNING)
            estimated_time_minutes = 0.0
        else:
            try:
                estimated_time_minutes = float(estimated_raw)
            except (TypeError, ValueError):
                blockers.append(f"invalid_estimated_minutes:{task_key}")
                continue

        dep_ids = [
            str(key).strip()
            for key in (planned.get("depends_on_task_keys") or [])
            if str(key).strip()
        ]

        provenance = list(planned.get("provenance") or [])
        provenance.append("execution_plan_v2_materialize.1")

        eligible_role = _eligible_role_from_planned(planned)
        operational: dict[str, Any] = {
            "task_id": task_key,
            "source_task_key": task_key,
            "name": label,
            "display_name": label,
            "technical_name": technical_name,
            "process_type": str(planned.get("canonical_task_type") or "").strip(),
            "process_id": str(planned.get("source_operation_code") or "").strip(),
            "machine_type": _machine_type_from_planned(planned),
            "depends_on_task_ids": dep_ids,
            "sequence_index": planned.get("sequence_index"),
            "estimated_time_minutes": estimated_time_minutes,
            "quantity": 1.0,
            "layer_id": V2_LAYER_ID,
            "assigned_employee_id": None,
            "operational_status": OPERATIONAL_STATUS_PENDING,
            "source": OPERATIONAL_TASK_SOURCE,
            "execution_plan_id": execution_plan_id,
            "order_id": order_id,
            "provenance": provenance,
            "source_module_code": planned.get("source_module_code"),
            "source_component_code": planned.get("source_component_code"),
            "material_inputs": planned.get("material_inputs") or [],
            "warnings": task_warnings,
        }
        if eligible_role:
            operational["eligible_role_code"] = eligible_role
            operational["employee_role_requirement"] = planned.get("employee_role_requirement")

        operational_tasks.append(operational)

    if blockers:
        return [], warnings, blockers

    return operational_tasks, warnings, blockers
