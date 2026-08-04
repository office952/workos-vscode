"""Read-only consistency between embedded assignee and transition history."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional, Sequence

from sqlalchemy import text
from sqlalchemy.engine import Connection


STATUS_NO_CURRENT_ASSIGNMENT_NO_HISTORY = "NO_CURRENT_ASSIGNMENT_NO_HISTORY"
STATUS_CURRENT_ASSIGNMENT_WITH_BACKFILLED_HISTORY = (
    "CURRENT_ASSIGNMENT_WITH_BACKFILLED_HISTORY"
)
STATUS_CURRENT_STATE_MATCHES_LATEST_TRANSITION = (
    "CURRENT_STATE_MATCHES_LATEST_TRANSITION"
)
STATUS_CURRENT_STATE_MISMATCH = "CURRENT_STATE_MISMATCH"
STATUS_MULTIPLE_INITIAL_BACKFILLS = "MULTIPLE_INITIAL_BACKFILLS"
STATUS_MALFORMED_TRANSITION_SEQUENCE = "MALFORMED_TRANSITION_SEQUENCE"
STATUS_UNKNOWN = "UNKNOWN"

SOURCE_LEGACY_EMBEDDED_BACKFILL = "LEGACY_EMBEDDED_BACKFILL"


@dataclass
class TaskConsistencyResult:
    execution_plan_id: int
    order_id: int
    task_key: str
    embedded_assigned_employee_id: Optional[int]
    latest_transition_id: Optional[str]
    latest_transition_type: Optional[str]
    latest_new_employee_id: Optional[int]
    transition_count: int
    legacy_backfill_count: int
    status: str
    detail: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyReport:
    tasks: list[TaskConsistencyResult] = field(default_factory=list)
    match_count: int = 0
    mismatch_count: int = 0
    fail_closed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "match_count": self.match_count,
            "mismatch_count": self.mismatch_count,
            "fail_closed": self.fail_closed,
        }


def _parse_ops(tasks_json: Any) -> list[dict[str, Any]]:
    if isinstance(tasks_json, (bytes, bytearray)):
        tasks_json = tasks_json.decode("utf-8")
    if isinstance(tasks_json, str):
        data = json.loads(tasks_json)
    else:
        data = tasks_json
    if isinstance(data, list):
        return []
    if not isinstance(data, dict):
        return []
    ops = data.get("operational_tasks") or []
    return ops if isinstance(ops, list) else []


def evaluate_task_consistency(
    *,
    execution_plan_id: int,
    order_id: int,
    task_key: str,
    embedded_assigned_employee_id: Optional[int],
    transitions: Sequence[Mapping[str, Any]],
) -> TaskConsistencyResult:
    """transitions must be ordered by id ASC (canonical)."""
    ordered = list(transitions)
    legacy_count = sum(
        1
        for t in ordered
        if (t.get("source") == SOURCE_LEGACY_EMBEDDED_BACKFILL)
        and (t.get("transition_type") == "ASSIGN")
    )
    latest = ordered[-1] if ordered else None
    latest_new = latest.get("new_employee_id") if latest else None
    latest_type = latest.get("transition_type") if latest else None
    latest_tid = latest.get("transition_id") if latest else None

    if legacy_count > 1:
        return TaskConsistencyResult(
            execution_plan_id=execution_plan_id,
            order_id=order_id,
            task_key=task_key,
            embedded_assigned_employee_id=embedded_assigned_employee_id,
            latest_transition_id=latest_tid,
            latest_transition_type=latest_type,
            latest_new_employee_id=latest_new,
            transition_count=len(ordered),
            legacy_backfill_count=legacy_count,
            status=STATUS_MULTIPLE_INITIAL_BACKFILLS,
            detail="more_than_one_legacy_embedded_backfill_assign",
        )

    if not ordered and embedded_assigned_employee_id is None:
        return TaskConsistencyResult(
            execution_plan_id=execution_plan_id,
            order_id=order_id,
            task_key=task_key,
            embedded_assigned_employee_id=None,
            latest_transition_id=None,
            latest_transition_type=None,
            latest_new_employee_id=None,
            transition_count=0,
            legacy_backfill_count=0,
            status=STATUS_NO_CURRENT_ASSIGNMENT_NO_HISTORY,
        )

    if not ordered and embedded_assigned_employee_id is not None:
        return TaskConsistencyResult(
            execution_plan_id=execution_plan_id,
            order_id=order_id,
            task_key=task_key,
            embedded_assigned_employee_id=embedded_assigned_employee_id,
            latest_transition_id=None,
            latest_transition_type=None,
            latest_new_employee_id=None,
            transition_count=0,
            legacy_backfill_count=0,
            status=STATUS_CURRENT_STATE_MISMATCH,
            detail="embedded_assignment_without_transition_history",
        )

    # Validate sequence shape lightly (ASSIGN first when history starts from null).
    first = ordered[0]
    if first.get("transition_type") not in ("ASSIGN", "REASSIGN", "UNASSIGN"):
        return TaskConsistencyResult(
            execution_plan_id=execution_plan_id,
            order_id=order_id,
            task_key=task_key,
            embedded_assigned_employee_id=embedded_assigned_employee_id,
            latest_transition_id=latest_tid,
            latest_transition_type=latest_type,
            latest_new_employee_id=latest_new,
            transition_count=len(ordered),
            legacy_backfill_count=legacy_count,
            status=STATUS_MALFORMED_TRANSITION_SEQUENCE,
            detail="invalid_transition_type",
        )

    if latest_new != embedded_assigned_employee_id:
        return TaskConsistencyResult(
            execution_plan_id=execution_plan_id,
            order_id=order_id,
            task_key=task_key,
            embedded_assigned_employee_id=embedded_assigned_employee_id,
            latest_transition_id=latest_tid,
            latest_transition_type=latest_type,
            latest_new_employee_id=latest_new,
            transition_count=len(ordered),
            legacy_backfill_count=legacy_count,
            status=STATUS_CURRENT_STATE_MISMATCH,
            detail="ASSIGNMENT_TRANSITION_STATE_MISMATCH",
        )

    if (
        embedded_assigned_employee_id is not None
        and legacy_count == 1
        and len(ordered) == 1
    ):
        status = STATUS_CURRENT_ASSIGNMENT_WITH_BACKFILLED_HISTORY
    else:
        status = STATUS_CURRENT_STATE_MATCHES_LATEST_TRANSITION

    return TaskConsistencyResult(
        execution_plan_id=execution_plan_id,
        order_id=order_id,
        task_key=task_key,
        embedded_assigned_employee_id=embedded_assigned_employee_id,
        latest_transition_id=latest_tid,
        latest_transition_type=latest_type,
        latest_new_employee_id=latest_new,
        transition_count=len(ordered),
        legacy_backfill_count=legacy_count,
        status=status,
    )


def verify_plan_consistency(
    connection: Connection,
    *,
    execution_plan_id: Optional[int] = None,
) -> ConsistencyReport:
    """Read-only verifier. Never repairs."""
    report = ConsistencyReport()
    if execution_plan_id is None:
        plans = connection.execute(
            text(
                "SELECT id, order_id, tasks_json FROM execution_plan ORDER BY id"
            )
        ).fetchall()
    else:
        plans = connection.execute(
            text(
                "SELECT id, order_id, tasks_json FROM execution_plan "
                "WHERE id = :pid"
            ),
            {"pid": execution_plan_id},
        ).fetchall()

    for plan in plans:
        plan_id = int(plan._mapping["id"])
        order_id = int(plan._mapping["order_id"])
        ops = _parse_ops(plan._mapping["tasks_json"])
        transitions = connection.execute(
            text(
                """
                SELECT id, transition_id, task_key, transition_type,
                       new_employee_id, source
                FROM execution_task_assignment_transitions
                WHERE execution_plan_id = :pid
                ORDER BY id ASC
                """
            ),
            {"pid": plan_id},
        ).fetchall()
        by_task: dict[str, list[dict[str, Any]]] = {}
        for tr in transitions:
            key = str(tr._mapping["task_key"])
            by_task.setdefault(key, []).append(dict(tr._mapping))

        seen_keys: set[str] = set()
        for task in ops:
            if not isinstance(task, dict):
                continue
            task_key = task.get("task_id") or task.get("id")
            if not isinstance(task_key, str):
                continue
            seen_keys.add(task_key)
            ae = task.get("assigned_employee_id")
            if ae is not None and not isinstance(ae, int):
                result = TaskConsistencyResult(
                    execution_plan_id=plan_id,
                    order_id=order_id,
                    task_key=task_key,
                    embedded_assigned_employee_id=None,
                    latest_transition_id=None,
                    latest_transition_type=None,
                    latest_new_employee_id=None,
                    transition_count=len(by_task.get(task_key, [])),
                    legacy_backfill_count=0,
                    status=STATUS_UNKNOWN,
                    detail="embedded_assigned_employee_id_not_int",
                )
            else:
                result = evaluate_task_consistency(
                    execution_plan_id=plan_id,
                    order_id=order_id,
                    task_key=task_key,
                    embedded_assigned_employee_id=ae if isinstance(ae, int) else None,
                    transitions=by_task.get(task_key, []),
                )
            report.tasks.append(result)

        # Transitions for task keys no longer in operational_tasks
        for task_key, trs in by_task.items():
            if task_key in seen_keys:
                continue
            result = evaluate_task_consistency(
                execution_plan_id=plan_id,
                order_id=order_id,
                task_key=task_key,
                embedded_assigned_employee_id=None,
                transitions=trs,
            )
            if result.status == STATUS_NO_CURRENT_ASSIGNMENT_NO_HISTORY:
                result = TaskConsistencyResult(
                    execution_plan_id=plan_id,
                    order_id=order_id,
                    task_key=task_key,
                    embedded_assigned_employee_id=None,
                    latest_transition_id=result.latest_transition_id,
                    latest_transition_type=result.latest_transition_type,
                    latest_new_employee_id=result.latest_new_employee_id,
                    transition_count=result.transition_count,
                    legacy_backfill_count=result.legacy_backfill_count,
                    status=STATUS_MALFORMED_TRANSITION_SEQUENCE,
                    detail="orphan_transition_without_operational_task",
                )
            report.tasks.append(result)

    mismatch_statuses = {
        STATUS_CURRENT_STATE_MISMATCH,
        STATUS_MULTIPLE_INITIAL_BACKFILLS,
        STATUS_MALFORMED_TRANSITION_SEQUENCE,
        STATUS_UNKNOWN,
    }
    for task in report.tasks:
        if task.status in (
            STATUS_CURRENT_STATE_MATCHES_LATEST_TRANSITION,
            STATUS_CURRENT_ASSIGNMENT_WITH_BACKFILLED_HISTORY,
            STATUS_NO_CURRENT_ASSIGNMENT_NO_HISTORY,
        ):
            report.match_count += 1
        elif task.status in mismatch_statuses:
            report.mismatch_count += 1
    report.fail_closed = report.mismatch_count > 0
    return report
