"""Phase A — synthetic ASSIGN backfill from embedded operational_tasks[].

Does not mutate tasks_json / assigned_employee_id / plan.updated_at.
Idempotent via deterministic transition_id (UUID5).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from models.execution_task_assignment_transition import (
    SOURCE_LEGACY_EMBEDDED_BACKFILL,
)
from sqlalchemy import text
from sqlalchemy.engine import Connection


BACKFILL_REASON_CODE = "INITIAL_ASSIGNMENT_BACKFILL"
BACKFILL_TRANSITION_NAMESPACE = uuid.UUID("6b0f3e2a-8c1d-4f5a-9e7b-2d4c8a1f0b3e")
BACKFILL_ID_PREFIX = "workos:execution_task_assignment_transition:legacy_embedded_backfill:v1"


@dataclass(frozen=True)
class EmbeddedAssignmentCandidate:
    execution_plan_id: int
    order_id: int
    task_key: str
    assigned_employee_id: int
    assignment_actor_user_id: Optional[str]
    assignment_updated_at: Optional[str]
    assignment_source: Optional[str]
    plan_updated_at: Optional[str]
    plan_created_at: Optional[str]


@dataclass
class AssignmentInventoryReport:
    plans_scanned: int = 0
    operational_tasks_scanned: int = 0
    current_assignments_found: int = 0
    malformed_assignment_states: int = 0
    expected_transition_rows: int = 0
    candidates: list[EmbeddedAssignmentCandidate] = field(default_factory=list)
    malformed: list[dict[str, Any]] = field(default_factory=list)
    known_fixture_notes: list[str] = field(default_factory=list)


@dataclass
class BackfillReport:
    inserted: int = 0
    skipped_existing: int = 0
    candidates: int = 0
    errors: list[str] = field(default_factory=list)
    inserted_transition_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def deterministic_legacy_backfill_transition_id(
    *,
    execution_plan_id: int,
    task_key: str,
    assigned_employee_id: int,
    assignment_updated_at: Optional[str],
) -> str:
    """Stable UUID5 so re-running backfill cannot insert duplicates."""
    ts = (assignment_updated_at or "").strip()
    material = (
        f"{BACKFILL_ID_PREFIX}:{execution_plan_id}:{task_key}:"
        f"{assigned_employee_id}:{ts}"
    )
    return str(uuid.uuid5(BACKFILL_TRANSITION_NAMESPACE, material))


def _parse_tasks_payload(raw: Any) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    if raw is None:
        return None, "tasks_json_null"
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return None, f"tasks_json_invalid_json:{exc}"
    else:
        data = raw
    if isinstance(data, list):
        # Legacy array shape — not V2 operational_tasks; ignore for Phase A backfill.
        return {"operational_tasks": [], "_legacy_array": True}, None
    if not isinstance(data, dict):
        return None, "tasks_json_not_object"
    return data, None


def inventory_embedded_assignments(
    plan_rows: Sequence[Mapping[str, Any]],
) -> AssignmentInventoryReport:
    """Scan plan rows; only operational_tasks[] with non-null assigned_employee_id."""
    report = AssignmentInventoryReport()
    report.plans_scanned = len(plan_rows)
    for row in plan_rows:
        plan_id = int(row["id"])
        order_id = int(row["order_id"])
        payload, err = _parse_tasks_payload(row.get("tasks_json"))
        if err or payload is None:
            report.malformed_assignment_states += 1
            report.malformed.append(
                {"execution_plan_id": plan_id, "order_id": order_id, "error": err}
            )
            continue
        ops = payload.get("operational_tasks") or []
        if not isinstance(ops, list):
            report.malformed_assignment_states += 1
            report.malformed.append(
                {
                    "execution_plan_id": plan_id,
                    "order_id": order_id,
                    "error": "operational_tasks_not_list",
                }
            )
            continue
        report.operational_tasks_scanned += len(ops)
        for task in ops:
            if not isinstance(task, dict):
                report.malformed_assignment_states += 1
                report.malformed.append(
                    {
                        "execution_plan_id": plan_id,
                        "order_id": order_id,
                        "error": "task_not_object",
                    }
                )
                continue
            ae = task.get("assigned_employee_id")
            if ae is None:
                continue
            task_key = task.get("task_id") or task.get("id")
            if not isinstance(task_key, str) or not task_key.strip():
                report.malformed_assignment_states += 1
                report.malformed.append(
                    {
                        "execution_plan_id": plan_id,
                        "order_id": order_id,
                        "error": "missing_task_key",
                        "assigned_employee_id": ae,
                    }
                )
                continue
            if not isinstance(ae, int):
                report.malformed_assignment_states += 1
                report.malformed.append(
                    {
                        "execution_plan_id": plan_id,
                        "order_id": order_id,
                        "task_key": task_key,
                        "error": "assigned_employee_id_not_int",
                        "assigned_employee_id": ae,
                    }
                )
                continue
            report.candidates.append(
                EmbeddedAssignmentCandidate(
                    execution_plan_id=plan_id,
                    order_id=order_id,
                    task_key=task_key,
                    assigned_employee_id=ae,
                    assignment_actor_user_id=_optional_str(
                        task.get("assignment_actor_user_id")
                    ),
                    assignment_updated_at=_optional_str(
                        task.get("assignment_updated_at")
                    ),
                    assignment_source=_optional_str(task.get("assignment_source")),
                    plan_updated_at=_optional_str(row.get("updated_at")),
                    plan_created_at=_optional_str(row.get("created_at")),
                )
            )
    report.current_assignments_found = len(report.candidates)
    report.expected_transition_rows = len(report.candidates)
    report.known_fixture_notes = [
        "880750/23 Wave 7 canonical_controlled_assign_v1 LED→7",
        "973019/21 golden-pilot controlled_ops_graph_assign_v1 (Wave 3 noted historical)",
        "23099/4 and 23150/5 historical Mobile/operator lab assignments",
    ]
    return report


def _optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    text_value = str(value).strip()
    return text_value or None


def _resolve_created_at(candidate: EmbeddedAssignmentCandidate) -> datetime:
    for raw in (
        candidate.assignment_updated_at,
        candidate.plan_updated_at,
        candidate.plan_created_at,
    ):
        parsed = _parse_datetime(raw)
        if parsed is not None:
            return parsed
    raise ValueError(
        f"no_available_timestamp plan={candidate.execution_plan_id} "
        f"task={candidate.task_key}"
    )


def _parse_datetime(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    text_value = raw.strip()
    if text_value.endswith("Z"):
        text_value = text_value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text_value)
    except ValueError:
        # SQLite may store "YYYY-MM-DD HH:MM:SS.ffffff"
        try:
            return datetime.fromisoformat(text_value.replace(" ", "T"))
        except ValueError:
            return None


def build_backfill_row(candidate: EmbeddedAssignmentCandidate) -> dict[str, Any]:
    created_at = _resolve_created_at(candidate)
    transition_id = deterministic_legacy_backfill_transition_id(
        execution_plan_id=candidate.execution_plan_id,
        task_key=candidate.task_key,
        assigned_employee_id=candidate.assigned_employee_id,
        assignment_updated_at=candidate.assignment_updated_at,
    )
    metadata: dict[str, Any] = {}
    if candidate.assignment_source:
        metadata["embedded_assignment_source"] = candidate.assignment_source
    return {
        "transition_id": transition_id,
        "execution_plan_id": candidate.execution_plan_id,
        "order_id": candidate.order_id,
        "task_key": candidate.task_key,
        "transition_type": "ASSIGN",
        "previous_employee_id": None,
        "new_employee_id": candidate.assigned_employee_id,
        "actor_user_id": candidate.assignment_actor_user_id,
        "actor_role": None,
        "reason_code": BACKFILL_REASON_CODE,
        "reason_note": None,
        "task_state_at_transition": None,
        "eligibility_decision_code": None,
        "eligibility_provenance": None,
        "request_id": None,
        "correlation_id": None,
        "expected_current_employee_id": None,
        "source": SOURCE_LEGACY_EMBEDDED_BACKFILL,
        "command_version": "phase_a_backfill_v1",
        "metadata_json": json.dumps(metadata, separators=(",", ":")) if metadata else None,
        "created_at": created_at,
    }


def load_plan_rows(connection: Connection) -> list[dict[str, Any]]:
    result = connection.execute(
        text(
            "SELECT id, order_id, tasks_json, updated_at, created_at "
            "FROM execution_plan ORDER BY id"
        )
    )
    return [dict(row._mapping) for row in result]


def run_legacy_embedded_backfill(connection: Connection) -> BackfillReport:
    """Insert synthetic ASSIGN rows; skip when transition_id already present."""
    report = BackfillReport()
    inventory = inventory_embedded_assignments(load_plan_rows(connection))
    if inventory.malformed_assignment_states:
        report.errors.append(
            f"malformed_assignment_states={inventory.malformed_assignment_states}"
        )
        report.errors.extend(
            json.dumps(item, sort_keys=True) for item in inventory.malformed[:20]
        )
        return report

    report.candidates = inventory.expected_transition_rows
    for candidate in inventory.candidates:
        row = build_backfill_row(candidate)
        existing = connection.execute(
            text(
                "SELECT id FROM execution_task_assignment_transitions "
                "WHERE transition_id = :transition_id"
            ),
            {"transition_id": row["transition_id"]},
        ).fetchone()
        if existing is not None:
            report.skipped_existing += 1
            continue
        connection.execute(
            text(
                """
                INSERT INTO execution_task_assignment_transitions (
                    transition_id, execution_plan_id, order_id, task_key,
                    transition_type, previous_employee_id, new_employee_id,
                    actor_user_id, actor_role, reason_code, reason_note,
                    task_state_at_transition, eligibility_decision_code,
                    eligibility_provenance, request_id, correlation_id,
                    expected_current_employee_id, source, command_version,
                    metadata_json, created_at
                ) VALUES (
                    :transition_id, :execution_plan_id, :order_id, :task_key,
                    :transition_type, :previous_employee_id, :new_employee_id,
                    :actor_user_id, :actor_role, :reason_code, :reason_note,
                    :task_state_at_transition, :eligibility_decision_code,
                    :eligibility_provenance, :request_id, :correlation_id,
                    :expected_current_employee_id, :source, :command_version,
                    :metadata_json, :created_at
                )
                """
            ),
            row,
        )
        report.inserted += 1
        report.inserted_transition_ids.append(row["transition_id"])
    return report
