"""Phase B — controlled pre-start REASSIGN / UNASSIGN (backend).

Atomic dual-write under plan lock:
  INSERT transition row + UPDATE embedded assigned_employee_id

Never mutates QA by itself — callers must not point DATABASE_URL at QA for proofs.
No schema changes. Mobile / UI not wired.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any, Literal, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.permissions import has_permission, resolve_effective_role
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.execution_task_assignment_transition import (
    ExecutionTaskAssignmentTransition,
)
from models.orders import Orders
from services.assignment_transition_consistency_service import (
    STATUS_CURRENT_ASSIGNMENT_WITH_BACKFILLED_HISTORY,
    STATUS_CURRENT_STATE_MATCHES_LATEST_TRANSITION,
    evaluate_task_consistency,
)
from services.assignment_transition_repository import (
    AssignmentTransitionAppendOnlyRepository,
)
from services.controlled_employee_assignment_service import (
    _eligibility_task_row,
    _load_plan_operational_tasks,
    _normalize_employee_id,
    _plan_assignment_lock,
    _raise_eligibility_failure,
    _reality_task_lookup,
)
from services.employee_eligibility_read_model_service import (
    build_employee_eligibility_read_model,
)
from services.employee_lifecycle import is_assignable
from services.execution_plan_operational_readiness_service import (
    assert_operational_mutation_allowed,
)
from services.execution_plan_task_parser import serialize_operational_tasks_to_plan_json
from services.phase_b_resource_guard_service import (
    dec015_test_fixture_allowed,
    evaluate_resource_guards,
)
from services.phase_b_session_history_guard import probe_task_execution_history

logger = logging.getLogger(__name__)

COMMAND_VERSION = "phase_b_pre_start_v1"
SOURCE_REASSIGN = "CONTROLLED_PRE_START_REASSIGN_V1"
SOURCE_UNASSIGN = "CONTROLLED_PRE_START_UNASSIGN_V1"

PERM_REASSIGN = "execution.task_reassign"
PERM_UNASSIGN = "execution.task_unassign"

_MATCH_STATUSES = frozenset(
    {
        STATUS_CURRENT_ASSIGNMENT_WITH_BACKFILLED_HISTORY,
        STATUS_CURRENT_STATE_MATCHES_LATEST_TRANSITION,
    }
)


def _conflict(code: str, **extra: Any) -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={"error": code, **extra},
    )


def _auth_denied(permission: str) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"error": "permission_denied", "permission": permission},
    )


def _assert_actor_authorized(*, actor_role: str | None, permission: str) -> str:
    role = resolve_effective_role((actor_role or "").strip() or "viewer")
    if role not in {"admin", "manager"}:
        raise _auth_denied(permission)
    if not has_permission(role, permission):
        raise _auth_denied(permission)
    return role


def _dec015_fixture_eligibility(
    task_id: str, employee_ids: list[int]
) -> dict[str, Any]:
    """TEST_ONLY fixture — never used outside APP_ENV=test + READY env."""
    ids = sorted({int(i) for i in employee_ids if i is not None})
    return {
        "status": "ok",
        "tasks": [
            {
                "task_key": task_id,
                "eligibility_status": "ready_with_warnings",
                "eligible_employee_count": len(ids),
                "eligible_employees": [
                    {"employee_id": eid, "display_name": f"E{eid}"} for eid in ids
                ],
                "blockers": [],
                "warnings": ["phase_b_dec015_test_fixture"],
                "requirement_version": "eligibility-rm/v1",
            }
        ],
    }


def _transition_to_mapping(row: ExecutionTaskAssignmentTransition) -> dict[str, Any]:
    return {
        "transition_id": row.transition_id,
        "transition_type": row.transition_type,
        "new_employee_id": row.new_employee_id,
        "previous_employee_id": row.previous_employee_id,
        "source": row.source,
        "expected_current_employee_id": row.expected_current_employee_id,
        "reason_code": row.reason_code,
        "reason_note": row.reason_note,
        "actor_user_id": row.actor_user_id,
    }


def _canonical_payload(
    *,
    operation: Literal["REASSIGN", "UNASSIGN"],
    plan_id: int,
    task_key: str,
    expected_current_employee_id: int,
    new_employee_id: Optional[int],
    reason_code: str,
    reason_note: Optional[str],
) -> dict[str, Any]:
    """Fields that define transition identity for idempotency (actor not included)."""
    return {
        "operation": operation,
        "execution_plan_id": plan_id,
        "task_key": task_key,
        "expected_current_employee_id": expected_current_employee_id,
        "new_employee_id": new_employee_id,
        "reason_code": reason_code,
        "reason_note": reason_note,
    }


def _payload_from_row(row: ExecutionTaskAssignmentTransition) -> dict[str, Any]:
    return _canonical_payload(
        operation=row.transition_type,  # type: ignore[arg-type]
        plan_id=int(row.execution_plan_id),
        task_key=str(row.task_key),
        expected_current_employee_id=int(row.expected_current_employee_id or 0),
        new_employee_id=row.new_employee_id,
        reason_code=str(row.reason_code or ""),
        reason_note=row.reason_note,
    )


def _success_body(
    *,
    status: str,
    transition_id: str,
    previous_employee_id: Optional[int],
    new_employee_id: Optional[int],
    order_id: int,
    plan_id: int,
    task_id: str,
    already_applied: bool = False,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "status": status,
        "transition_id": transition_id,
        "previous_employee_id": previous_employee_id,
        "new_employee_id": new_employee_id,
        "task_id": task_id,
        "order_id": order_id,
        "plan_id": plan_id,
        "consistency": "MATCH",
        "command_version": COMMAND_VERSION,
    }
    if already_applied:
        body["already_applied"] = True
        body["canonical_original_result"] = {
            "status": status,
            "transition_id": transition_id,
            "previous_employee_id": previous_employee_id,
            "new_employee_id": new_employee_id,
            "consistency": "MATCH",
        }
    return body


async def _reassign_or_unassign(
    db: AsyncSession,
    *,
    operation: Literal["REASSIGN", "UNASSIGN"],
    order_id: int,
    task_id: str,
    transition_id: str,
    expected_current_employee_id: int,
    new_employee_id: Optional[int],
    reason_code: str,
    reason_note: Optional[str],
    actor_user_id: str | None,
    actor_role: str | None,
) -> dict[str, Any]:
    permission = PERM_REASSIGN if operation == "REASSIGN" else PERM_UNASSIGN
    effective_role = _assert_actor_authorized(
        actor_role=actor_role, permission=permission
    )

    if not isinstance(order_id, int) or order_id <= 0:
        raise HTTPException(status_code=422, detail={"error": "order_id_invalid"})
    tid = (task_id or "").strip()
    if not tid:
        raise HTTPException(status_code=422, detail={"error": "invalid_task_identity"})
    try:
        tid_uuid = str(uuid.UUID(str(transition_id).strip()))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422, detail={"error": "transition_id_invalid_uuid"}
        ) from exc

    order = (
        await db.execute(select(Orders).where(Orders.id == order_id))
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})

    event_prefix = (
        "TASK_REASSIGNMENT" if operation == "REASSIGN" else "TASK_UNASSIGNMENT"
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
            raise _conflict("plan_mismatch")

        assert_operational_mutation_allowed(plan)

        repo = AssignmentTransitionAppendOnlyRepository(db)
        existing = await repo.get_by_transition_id(tid_uuid)
        desired_payload = _canonical_payload(
            operation=operation,
            plan_id=int(plan.id),
            task_key=tid,
            expected_current_employee_id=int(expected_current_employee_id),
            new_employee_id=new_employee_id,
            reason_code=reason_code,
            reason_note=reason_note,
        )
        if existing is not None:
            stored = _payload_from_row(existing)
            if stored != desired_payload:
                logger.info(
                    "%s_CONFLICT code=transition_id_payload_conflict "
                    "order_id=%s plan_id=%s task_id=%s transition_id=%s "
                    "actor_user_id=%s role=%s",
                    event_prefix,
                    order_id,
                    plan.id,
                    tid,
                    tid_uuid,
                    actor_user_id,
                    effective_role,
                )
                raise _conflict("transition_id_payload_conflict")
            # Idempotent retry — no second write.
            logger.info(
                "%s_IDEMPOTENT_RETRY order_id=%s plan_id=%s task_id=%s "
                "transition_id=%s actor_user_id=%s role=%s reason_code=%s",
                event_prefix,
                order_id,
                plan.id,
                tid,
                tid_uuid,
                actor_user_id,
                effective_role,
                reason_code,
            )
            return _success_body(
                status="already_applied",
                transition_id=tid_uuid,
                previous_employee_id=existing.previous_employee_id,
                new_employee_id=existing.new_employee_id,
                order_id=order_id,
                plan_id=int(plan.id),
                task_id=tid,
                already_applied=True,
            )

        # Re-read tasks under lock.
        tasks, parsed = _load_plan_operational_tasks(plan.tasks_json)
        task_entry: Optional[dict[str, Any]] = None
        for entry in tasks:
            if isinstance(entry, dict) and str(entry.get("task_id")) == tid:
                task_entry = entry
                break
        if task_entry is None:
            raise HTTPException(status_code=404, detail={"error": "task_not_found"})

        embedded = _normalize_employee_id(task_entry.get("assigned_employee_id"))

        history = await repo.list_for_task(
            execution_plan_id=int(plan.id), task_key=tid
        )
        consistency = evaluate_task_consistency(
            execution_plan_id=int(plan.id),
            order_id=order_id,
            task_key=tid,
            embedded_assigned_employee_id=embedded,
            transitions=[_transition_to_mapping(r) for r in history],
        )
        if consistency.status not in _MATCH_STATUSES:
            logger.info(
                "%s_BLOCKED_STATE code=assignment_transition_state_mismatch "
                "order_id=%s plan_id=%s task_id=%s status=%s actor_user_id=%s",
                event_prefix,
                order_id,
                plan.id,
                tid,
                consistency.status,
                actor_user_id,
            )
            raise _conflict(
                "assignment_transition_state_mismatch",
                consistency_status=consistency.status,
            )

        # CAS expected current
        if embedded is None:
            raise _conflict("task_not_currently_assigned")
        if int(embedded) != int(expected_current_employee_id):
            logger.info(
                "%s_CONFLICT code=stale_current_assignment order_id=%s "
                "plan_id=%s task_id=%s expected=%s actual=%s actor_user_id=%s",
                event_prefix,
                order_id,
                plan.id,
                tid,
                expected_current_employee_id,
                embedded,
                actor_user_id,
            )
            raise _conflict(
                "stale_current_assignment",
                expected_current_employee_id=expected_current_employee_id,
                current_assigned_employee_id=embedded,
            )

        # Session / execution history — any canonical evidence blocks.
        history_probe = await probe_task_execution_history(
            db, order_id=order_id, task_id=tid
        )
        if history_probe.has_history:
            raise _conflict(
                "task_has_execution_history",
                sources=list(history_probe.sources),
                detail=history_probe.detail,
            )

        reality = (
            await db.execute(
                select(ExecutionReality).where(ExecutionReality.order_id == order_id)
            )
        ).scalar_one_or_none()
        reality_raw = reality.tasks_json if reality else None
        rt = _reality_task_lookup(reality_raw).get(tid, {})
        if rt.get("ended_at"):
            raise _conflict("task_not_pre_start", reason="task_already_completed")
        if rt.get("started_at") and not rt.get("ended_at"):
            raise _conflict("task_not_pre_start", reason="task_session_active")

        # Embedded terminal markers if present (do not invent fields).
        for key in ("status", "task_status", "state"):
            val = str(task_entry.get(key) or "").strip().lower()
            if val in {"completed", "cancelled", "canceled", "terminal", "done"}:
                raise _conflict("task_not_pre_start", reason=f"task_status_{val}")

        guards = evaluate_resource_guards(
            order_id=order_id, plan_id=int(plan.id), task_key=tid
        )
        block = guards.blocking_error()
        if block:
            logger.info(
                "%s_BLOCKED_STATE code=%s order_id=%s plan_id=%s task_id=%s "
                "scheduling=%s reservation=%s capacity=%s actor_user_id=%s "
                "override_rejected=%s",
                event_prefix,
                block,
                order_id,
                plan.id,
                tid,
                guards.scheduling_state,
                guards.machine_reservation_state,
                guards.capacity_allocation_state,
                actor_user_id,
                guards.override_rejected,
            )
            raise _conflict(
                block,
                scheduling_state=guards.scheduling_state,
                machine_reservation_state=guards.machine_reservation_state,
                capacity_allocation_state=guards.capacity_allocation_state,
            )

        if operation == "REASSIGN":
            assert new_employee_id is not None
            emp = (
                await db.execute(
                    select(Employees).where(Employees.id == new_employee_id)
                )
            ).scalar_one_or_none()
            if emp is None:
                raise HTTPException(
                    status_code=404, detail={"error": "employee_not_found"}
                )
            if not is_assignable(emp, date.today()):
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "inactive_employee",
                        "status": emp.status,
                    },
                )
            if dec015_test_fixture_allowed():
                eligibility = _dec015_fixture_eligibility(
                    tid, [int(expected_current_employee_id), int(new_employee_id)]
                )
            else:
                eligibility = await build_employee_eligibility_read_model(db, order_id)
            if eligibility.get("status") == "blocked_not_materialized":
                raise HTTPException(
                    status_code=422, detail={"error": "task_not_materialized"}
                )
            task_row = _eligibility_task_row(eligibility, tid)
            if task_row is None:
                raise HTTPException(
                    status_code=404, detail={"error": "task_not_found"}
                )
            _raise_eligibility_failure(task_row)
            eligible_ids = {
                int(e["employee_id"])
                for e in (task_row.get("eligible_employees") or [])
                if e.get("employee_id") is not None
            }
            if int(new_employee_id) not in eligible_ids:
                logger.info(
                    "%s_ELIGIBILITY_DENIED order_id=%s plan_id=%s task_id=%s "
                    "new_employee_id=%s actor_user_id=%s",
                    event_prefix,
                    order_id,
                    plan.id,
                    tid,
                    new_employee_id,
                    actor_user_id,
                )
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "new_employee_not_eligible",
                        "eligible_employee_ids": sorted(eligible_ids),
                    },
                )

        previous = int(embedded)
        now = datetime.now(timezone.utc)
        plan_id = int(plan.id)
        row = ExecutionTaskAssignmentTransition(
            transition_id=tid_uuid,
            execution_plan_id=plan_id,
            order_id=order_id,
            task_key=tid,
            transition_type=operation,
            previous_employee_id=previous,
            new_employee_id=new_employee_id,
            actor_user_id=actor_user_id,
            actor_role=effective_role,
            reason_code=reason_code,
            reason_note=reason_note,
            task_state_at_transition="pre_start",
            expected_current_employee_id=int(expected_current_employee_id),
            source=SOURCE_REASSIGN if operation == "REASSIGN" else SOURCE_UNASSIGN,
            command_version=COMMAND_VERSION,
            created_at=now,
        )

        try:
            await repo.insert_transition(row)
            if operation == "REASSIGN":
                task_entry["assigned_employee_id"] = int(new_employee_id)  # type: ignore[arg-type]
            else:
                task_entry["assigned_employee_id"] = None
            task_entry["assignment_updated_at"] = now.isoformat()
            task_entry["assignment_source"] = (
                SOURCE_REASSIGN if operation == "REASSIGN" else SOURCE_UNASSIGN
            )
            if actor_user_id:
                task_entry["assignment_actor_user_id"] = str(actor_user_id)
            plan.tasks_json = serialize_operational_tasks_to_plan_json(parsed, tasks)
            await db.flush()

            # Post-write consistency inside the same transaction.
            hist2 = await repo.list_for_task(
                execution_plan_id=plan_id, task_key=tid
            )
            emb2 = _normalize_employee_id(task_entry.get("assigned_employee_id"))
            post = evaluate_task_consistency(
                execution_plan_id=plan_id,
                order_id=order_id,
                task_key=tid,
                embedded_assigned_employee_id=emb2,
                transitions=[_transition_to_mapping(r) for r in hist2],
            )
            if post.status not in _MATCH_STATUSES:
                await db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "post_transition_consistency_failed",
                        "consistency_status": post.status,
                    },
                )
            await db.commit()
        except HTTPException:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            # Use captured scalars only — plan attrs are expired after rollback.
            logger.exception(
                "%s persist failed order_id=%s plan_id=%s task_id=%s",
                event_prefix,
                order_id,
                plan_id,
                tid,
            )
            raise HTTPException(
                status_code=500, detail={"error": "transition_persist_failed"}
            ) from None

        status = "reassigned" if operation == "REASSIGN" else "unassigned"
        logger.info(
            "%s_SUCCEEDED order_id=%s plan_id=%s task_id=%s transition_id=%s "
            "previous_employee_id=%s new_employee_id=%s reason_code=%s "
            "actor_user_id=%s role=%s",
            event_prefix,
            order_id,
            plan_id,
            tid,
            tid_uuid,
            previous,
            new_employee_id,
            reason_code,
            actor_user_id,
            effective_role,
        )
        return _success_body(
            status=status,
            transition_id=tid_uuid,
            previous_employee_id=previous,
            new_employee_id=new_employee_id,
            order_id=order_id,
            plan_id=plan_id,
            task_id=tid,
        )


async def reassign_operational_task_controlled(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    transition_id: str,
    expected_current_employee_id: int,
    new_employee_id: int,
    reason_code: str,
    reason_note: Optional[str] = None,
    actor_user_id: str | None = None,
    actor_role: str | None = None,
) -> dict[str, Any]:
    return await _reassign_or_unassign(
        db,
        operation="REASSIGN",
        order_id=order_id,
        task_id=task_id,
        transition_id=transition_id,
        expected_current_employee_id=expected_current_employee_id,
        new_employee_id=new_employee_id,
        reason_code=reason_code,
        reason_note=reason_note,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
    )


async def unassign_operational_task_controlled(
    db: AsyncSession,
    *,
    order_id: int,
    task_id: str,
    transition_id: str,
    expected_current_employee_id: int,
    reason_code: str,
    reason_note: Optional[str] = None,
    actor_user_id: str | None = None,
    actor_role: str | None = None,
) -> dict[str, Any]:
    return await _reassign_or_unassign(
        db,
        operation="UNASSIGN",
        order_id=order_id,
        task_id=task_id,
        transition_id=transition_id,
        expected_current_employee_id=expected_current_employee_id,
        new_employee_id=None,
        reason_code=reason_code,
        reason_note=reason_note,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
    )
