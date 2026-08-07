"""Resource State R6 — read facade: plan/task validation + domain evaluation.

Does NOT wire into Phase B reassignment/unassignment consumers.
"""

from __future__ import annotations

from datetime import datetime, timezone

from models.execution_plan import ExecutionPlan
from schemas.resource_state_read import (
    DomainResourceStateResult,
    TaskResourceStateResult,
)
from services.execution_plan_task_parser import operational_tasks_only
from services.resource_state_read_evaluator import (
    CAPACITY_BLOCKING_STATUSES,
    CAPACITY_KNOWN_STATUSES,
    RESERVATION_BLOCKING_STATUSES,
    RESERVATION_KNOWN_STATUSES,
    SCHEDULE_BLOCKING_STATUSES,
    SCHEDULE_KNOWN_STATUSES,
    aggregate_domain_states,
    evaluate_domain_from_rows,
)
from services.resource_state_read_repository import ResourceStateReadRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ResourceStatePlanNotFoundError(LookupError):
    """execution_plan row missing."""


class ResourceStateTaskNotFoundError(LookupError):
    """task_key not present in plan operational_tasks[]."""


async def evaluate_task_resource_state(
    db: AsyncSession,
    *,
    plan_id: int,
    task_key: str,
) -> TaskResourceStateResult:
    """Canonical R6 read entrypoint."""
    tid = (task_key or "").strip()
    if not tid:
        raise ResourceStateTaskNotFoundError("task_key_blank")

    plan = (
        await db.execute(select(ExecutionPlan).where(ExecutionPlan.id == plan_id))
    ).scalar_one_or_none()
    if plan is None:
        raise ResourceStatePlanNotFoundError("execution_plan_not_found")

    try:
        ops = operational_tasks_only(plan.tasks_json)
    except Exception as exc:  # parser / JSON failures → treat as unknown task identity
        raise ResourceStateTaskNotFoundError("tasks_json_unreadable") from exc

    if not any(str(t.get("task_id") or "") == tid for t in ops):
        raise ResourceStateTaskNotFoundError("task_key_not_in_operational_tasks")

    repo = ResourceStateReadRepository(db)
    now = datetime.now(timezone.utc)

    scheduling = await _evaluate_scheduling(repo, plan_id=plan_id, task_key=tid, now=now)
    reservation = await _evaluate_reservation(
        repo, plan_id=plan_id, task_key=tid, now=now
    )
    capacity = await _evaluate_capacity(repo, plan_id=plan_id, task_key=tid, now=now)

    aggregate, aggregate_reason = aggregate_domain_states(
        [scheduling, reservation, capacity]
    )
    return TaskResourceStateResult(
        plan_id=plan_id,
        order_id=plan.order_id,
        task_key=tid,
        scheduling=scheduling,
        machine_reservation=reservation,
        capacity_allocation=capacity,
        aggregate=aggregate,
        aggregate_reason_code=aggregate_reason,
        evaluated_at=now,
    )


async def _evaluate_scheduling(
    repo: ResourceStateReadRepository,
    *,
    plan_id: int,
    task_key: str,
    now: datetime,
) -> DomainResourceStateResult:
    try:
        config = await repo.get_active_configuration(domain="SCHEDULING")
        rows = await repo.list_schedules_for_task(
            execution_plan_id=plan_id, task_key=task_key
        )
    except Exception:
        return evaluate_domain_from_rows(
            domain="SCHEDULING",
            configuration=None,
            rows=[],
            blocking_statuses=SCHEDULE_BLOCKING_STATUSES,
            known_statuses=SCHEDULE_KNOWN_STATUSES,
            status_getter=lambda r: getattr(r, "status", None),
            id_getter=lambda r: int(getattr(r, "id")),
            evaluated_at=now,
            force_unknown=True,
            unknown_reason="query_failure",
        )
    return evaluate_domain_from_rows(
        domain="SCHEDULING",
        configuration=config,
        rows=rows,
        blocking_statuses=SCHEDULE_BLOCKING_STATUSES,
        known_statuses=SCHEDULE_KNOWN_STATUSES,
        status_getter=lambda r: getattr(r, "status", None),
        id_getter=lambda r: int(getattr(r, "id")),
        evaluated_at=now,
    )


async def _evaluate_reservation(
    repo: ResourceStateReadRepository,
    *,
    plan_id: int,
    task_key: str,
    now: datetime,
) -> DomainResourceStateResult:
    try:
        config = await repo.get_active_configuration(domain="MACHINE_RESERVATION")
        rows = await repo.list_reservations_visible_to_task(
            execution_plan_id=plan_id, task_key=task_key
        )
    except Exception:
        return evaluate_domain_from_rows(
            domain="MACHINE_RESERVATION",
            configuration=None,
            rows=[],
            blocking_statuses=RESERVATION_BLOCKING_STATUSES,
            known_statuses=RESERVATION_KNOWN_STATUSES,
            status_getter=lambda r: getattr(r, "status", None),
            id_getter=lambda r: int(getattr(r, "id")),
            evaluated_at=now,
            force_unknown=True,
            unknown_reason="query_failure",
        )
    return evaluate_domain_from_rows(
        domain="MACHINE_RESERVATION",
        configuration=config,
        rows=rows,
        blocking_statuses=RESERVATION_BLOCKING_STATUSES,
        known_statuses=RESERVATION_KNOWN_STATUSES,
        status_getter=lambda r: getattr(r, "status", None),
        id_getter=lambda r: int(getattr(r, "id")),
        evaluated_at=now,
    )


async def _evaluate_capacity(
    repo: ResourceStateReadRepository,
    *,
    plan_id: int,
    task_key: str,
    now: datetime,
) -> DomainResourceStateResult:
    try:
        config = await repo.get_active_configuration(domain="CAPACITY_ALLOCATION")
        rows = await repo.list_capacity_allocations_for_task(
            execution_plan_id=plan_id, task_key=task_key
        )
    except Exception:
        return evaluate_domain_from_rows(
            domain="CAPACITY_ALLOCATION",
            configuration=None,
            rows=[],
            blocking_statuses=CAPACITY_BLOCKING_STATUSES,
            known_statuses=CAPACITY_KNOWN_STATUSES,
            status_getter=lambda r: getattr(r, "status", None),
            id_getter=lambda r: int(getattr(r, "id")),
            evaluated_at=now,
            force_unknown=True,
            unknown_reason="query_failure",
        )
    return evaluate_domain_from_rows(
        domain="CAPACITY_ALLOCATION",
        configuration=config,
        rows=rows,
        blocking_statuses=CAPACITY_BLOCKING_STATUSES,
        known_statuses=CAPACITY_KNOWN_STATUSES,
        status_getter=lambda r: getattr(r, "status", None),
        id_getter=lambda r: int(getattr(r, "id")),
        evaluated_at=now,
    )
