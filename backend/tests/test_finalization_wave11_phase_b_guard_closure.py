"""Wave 11 closure — resource TEST_ONLY, session-history, dual-write, concurrency.

Isolated SQLite / ASGI only. Never touches backend/dev.db.
ISOLATED_PROCESS_RUNTIME_PROOF is covered by
scripts/wave11_phase_b_isolated_process_runtime_proof.py (separate process).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from core.startup_safety import run_startup_safety_checks
from models.actual_cost_policy import ActualLaborCostLine
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.execution_task_assignment_transition import (
    REASON_NOTE_MAX_LEN,
    ExecutionTaskAssignmentTransition,
)
from schemas.controlled_pre_start_reassignment import ReassignPlanTaskRequest
from services.assignment_transition_consistency_service import (
    STATUS_CURRENT_STATE_MISMATCH,
    TaskConsistencyResult,
)
from services.controlled_pre_start_reassignment_service import (
    reassign_operational_task_controlled,
    unassign_operational_task_controlled,
)
from services.phase_b_resource_guard_service import (
    evaluate_resource_guards,
    validate_phase_b_test_overrides_at_startup,
)
from services.phase_b_session_history_guard import (
    probe_task_execution_history,
    reality_entry_counts_as_history,
)
from tests.test_finalization_wave11_phase_b_reassignment import (
    TASK,
    _envelope,
    _ready_elig,
    _seed_assign_history,
    _seed_employee,
    _seed_order,
    _seed_plan,
)

SIBLING = "t_sibling"


# ---------------------------------------------------------------------------
# Resource override TEST_ONLY boundary
# ---------------------------------------------------------------------------


def test_resource_clear_accepted_only_in_test(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    snap = evaluate_resource_guards(order_id=1, plan_id=1, task_key=TASK)
    assert snap.blocking_error() is None
    assert snap.override_applied is True
    assert snap.override_rejected is False
    status, _msg = validate_phase_b_test_overrides_at_startup()
    assert status == "PASS"


def test_resource_clear_ignored_in_development(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    snap = evaluate_resource_guards(order_id=1, plan_id=1, task_key=TASK)
    assert snap.scheduling_state == "NOT_CONFIGURED"
    assert snap.override_rejected is True
    assert snap.blocking_error() == "scheduling_state_not_clear"
    status, msg = validate_phase_b_test_overrides_at_startup()
    assert status == "WARNING"
    assert "outside APP_ENV=test" in msg


def test_resource_clear_blocks_startup_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    monkeypatch.setenv("JWT_SECRET_KEY", "prod-jwt-secret-for-startup-check")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./prod_like.db")
    status, _msg = validate_phase_b_test_overrides_at_startup()
    assert status == "BLOCKED"
    report = run_startup_safety_checks()
    names = {c.name: c for c in report.checks}
    assert names["PHASE_B_TEST_ONLY_OVERRIDES"].status == "BLOCKED"
    assert report.overall_status == "BLOCKED"


def test_default_resource_guards_not_configured(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("WORKOS_PHASE_B_RESOURCE_GUARDS", raising=False)
    snap = evaluate_resource_guards(order_id=1, plan_id=1, task_key=TASK)
    assert snap.scheduling_state == "NOT_CONFIGURED"
    assert snap.override_applied is False


# ---------------------------------------------------------------------------
# Session-history probe
# ---------------------------------------------------------------------------


def test_reality_null_started_at_counts_as_history():
    assert reality_entry_counts_as_history({"task_id": TASK, "started_at": None})


@pytest.mark.asyncio
async def test_probe_blocks_closed_session_and_null_started_at(db_session):
    order_id = 711001
    await _seed_order(db_session, order_id)
    db_session.add(
        ExecutionReality(
            order_id=order_id,
            order_code=f"ORD-W11C-{order_id}",
            tasks_json=json.dumps(
                [{"task_id": TASK, "started_at": None, "ended_at": None}]
            ),
        )
    )
    await db_session.commit()
    probe = await probe_task_execution_history(
        db_session, order_id=order_id, task_id=TASK
    )
    assert probe.has_history is True
    assert "execution_reality" in probe.sources


@pytest.mark.asyncio
async def test_probe_blocks_actual_labor_lines(db_session):
    order_id = 711002
    await _seed_order(db_session, order_id)
    db_session.add(
        ActualLaborCostLine(
            order_id=order_id,
            task_id=TASK,
            session_ref=f"sess-{order_id}",
            employee_id=7,
            role_code="OP",
            duration_seconds=60,
            rate_used=1.0,
            currency="EUR",
            labor_cost_amount=1.0,
            policy_id=1,
            policy_version=1,
            computed_at=datetime.now(timezone.utc),
            freeze_status="frozen",
        )
    )
    await db_session.commit()
    probe = await probe_task_execution_history(
        db_session, order_id=order_id, task_id=TASK
    )
    assert probe.has_history is True
    assert "actual_labor_cost_lines" in probe.sources


@pytest.mark.asyncio
async def test_probe_inconsistent_reality_fail_closed(db_session):
    order_id = 711003
    await _seed_order(db_session, order_id)
    db_session.add(
        ExecutionReality(
            order_id=order_id,
            order_code=f"ORD-W11C-{order_id}",
            tasks_json="{not-json",
        )
    )
    await db_session.commit()
    probe = await probe_task_execution_history(
        db_session, order_id=order_id, task_id=TASK
    )
    assert probe.has_history is True
    assert probe.fail_closed_error is True


@pytest.mark.asyncio
async def test_probe_no_history(db_session):
    order_id = 711004
    await _seed_order(db_session, order_id)
    probe = await probe_task_execution_history(
        db_session, order_id=order_id, task_id=TASK
    )
    assert probe.has_history is False
    assert probe.detail == "no_history"


@pytest.mark.asyncio
async def test_reassign_blocked_by_null_started_at_row(
    db_session, monkeypatch
):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    order_id = 711010
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session)
    e6 = await _seed_employee(db_session)
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": e7.id}]),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    db_session.add(
        ExecutionReality(
            order_id=order_id,
            order_code=f"ORD-W11C-{order_id}",
            tasks_json=json.dumps([{"task_id": TASK}]),
        )
    )
    await db_session.commit()
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7.id, e6.id])),
    )
    with pytest.raises(HTTPException) as exc:
        await reassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=e7.id,
            new_employee_id=e6.id,
            reason_code="MANAGER_CORRECTION",
            actor_role="manager",
        )
    assert exc.value.detail["error"] == "task_has_execution_history"


# ---------------------------------------------------------------------------
# Schema: note length / OTHER
# ---------------------------------------------------------------------------


def test_schema_rejects_note_too_long():
    with pytest.raises(Exception):
        ReassignPlanTaskRequest(
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=1,
            new_employee_id=2,
            reason_code="OTHER",
            reason_note="x" * (REASON_NOTE_MAX_LEN + 1),
        )


# ---------------------------------------------------------------------------
# Dual-write rollback matrix
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dual_write_transition_insert_failure_rolls_back(
    db_session, monkeypatch
):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    order_id = 711020
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session)
    e6 = await _seed_employee(db_session)
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": e7.id}]),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    plan_id = int(plan.id)
    e7_id = int(e7.id)
    e6_id = int(e6.id)
    tasks_before = plan.tasks_json
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7_id, e6_id])),
    )

    async def _boom(*_a, **_k):
        raise RuntimeError("inject_transition_insert_fail")

    monkeypatch.setattr(
        "services.assignment_transition_repository.AssignmentTransitionAppendOnlyRepository.insert_transition",
        _boom,
    )
    with pytest.raises(HTTPException) as exc:
        await reassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=e7_id,
            new_employee_id=e6_id,
            reason_code="MANAGER_CORRECTION",
            actor_role="manager",
        )
    assert exc.value.status_code == 500
    assert exc.value.detail["error"] == "transition_persist_failed"
    plan2 = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.id == plan_id)
        )
    ).scalar_one()
    assert plan2.tasks_json == tasks_before
    rows = (
        await db_session.execute(
            select(ExecutionTaskAssignmentTransition).where(
                ExecutionTaskAssignmentTransition.order_id == order_id,
                ExecutionTaskAssignmentTransition.transition_type == "REASSIGN",
            )
        )
    ).scalars().all()
    assert rows == []


@pytest.mark.asyncio
async def test_dual_write_tasks_json_failure_rolls_back(
    db_session, monkeypatch
):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    order_id = 711021
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session)
    e6 = await _seed_employee(db_session)
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": e7.id}]),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    plan_id = int(plan.id)
    e7_id = int(e7.id)
    e6_id = int(e6.id)
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7_id, e6_id])),
    )

    def _boom(*_a, **_k):
        raise RuntimeError("inject_tasks_json_serialize_fail")

    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.serialize_operational_tasks_to_plan_json",
        _boom,
    )
    with pytest.raises(HTTPException) as exc:
        await reassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=e7_id,
            new_employee_id=e6_id,
            reason_code="MANAGER_CORRECTION",
            actor_role="manager",
        )
    assert exc.value.detail["error"] == "transition_persist_failed"
    plan2 = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.id == plan_id)
        )
    ).scalar_one()
    embedded = json.loads(plan2.tasks_json)["operational_tasks"][0][
        "assigned_employee_id"
    ]
    assert embedded == e7_id
    rows = (
        await db_session.execute(
            select(ExecutionTaskAssignmentTransition).where(
                ExecutionTaskAssignmentTransition.order_id == order_id,
                ExecutionTaskAssignmentTransition.transition_type == "REASSIGN",
            )
        )
    ).scalars().all()
    assert rows == []


@pytest.mark.asyncio
async def test_dual_write_post_consistency_failure_rolls_back(
    db_session, monkeypatch
):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    order_id = 711022
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session)
    e6 = await _seed_employee(db_session)
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": e7.id}]),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7.id, e6.id])),
    )

    from services import controlled_pre_start_reassignment_service as svc

    real_eval = svc.evaluate_task_consistency
    calls = {"n": 0}

    def _flaky(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return real_eval(**kwargs)
        return TaskConsistencyResult(
            execution_plan_id=kwargs["execution_plan_id"],
            order_id=kwargs["order_id"],
            task_key=kwargs["task_key"],
            embedded_assigned_employee_id=kwargs["embedded_assigned_employee_id"],
            latest_transition_id=None,
            latest_transition_type=None,
            latest_new_employee_id=None,
            transition_count=0,
            legacy_backfill_count=0,
            status=STATUS_CURRENT_STATE_MISMATCH,
            detail="inject_post_consistency_fail",
        )

    monkeypatch.setattr(svc, "evaluate_task_consistency", _flaky)
    plan_id = int(plan.id)
    e7_id = int(e7.id)
    e6_id = int(e6.id)
    with pytest.raises(HTTPException) as exc:
        await reassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=e7_id,
            new_employee_id=e6_id,
            reason_code="MANAGER_CORRECTION",
            actor_role="manager",
        )
    assert exc.value.detail["error"] == "post_transition_consistency_failed"
    plan2 = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.id == plan_id)
        )
    ).scalar_one()
    embedded = json.loads(plan2.tasks_json)["operational_tasks"][0][
        "assigned_employee_id"
    ]
    assert embedded == e7_id
    rows = (
        await db_session.execute(
            select(ExecutionTaskAssignmentTransition).where(
                ExecutionTaskAssignmentTransition.order_id == order_id,
                ExecutionTaskAssignmentTransition.transition_type == "REASSIGN",
            )
        )
    ).scalars().all()
    assert rows == []


def test_commit_failure_injection_not_feasibly_claimed():
    """Document boundary: SQLite commit injection is not safely faked in-suite.

    TRANSACTION_ROLLBACK_EVIDENCE = exception path in
    controlled_pre_start_reassignment_service (await db.rollback() on Exception /
    post_consistency failure) proven by the three dual-write tests above.
    """
    assert True  # COMMIT_FAILURE_INJECTION = NOT_FEASIBLE


# ---------------------------------------------------------------------------
# Concurrency + sibling fingerprint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reassign_vs_unassign_one_winner(db_fixture, db_session, monkeypatch):
    import asyncio

    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    order_id = 711030
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session)
    e6 = await _seed_employee(db_session)
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": e7.id}]),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7.id, e6.id])),
    )

    async def _re(session):
        try:
            return await reassign_operational_task_controlled(
                session,
                order_id=order_id,
                task_id=TASK,
                transition_id=str(uuid.uuid4()),
                expected_current_employee_id=e7.id,
                new_employee_id=e6.id,
                reason_code="MANAGER_CORRECTION",
                actor_role="manager",
            )
        except HTTPException as exc:
            return exc

    async def _un(session):
        try:
            return await unassign_operational_task_controlled(
                session,
                order_id=order_id,
                task_id=TASK,
                transition_id=str(uuid.uuid4()),
                expected_current_employee_id=e7.id,
                reason_code="EMPLOYEE_UNAVAILABLE",
                actor_role="manager",
            )
        except HTTPException as exc:
            return exc

    async with db_fixture.session_maker() as s1, db_fixture.session_maker() as s2:
        r1, r2 = await asyncio.gather(_re(s1), _un(s2))
    oks = [r for r in (r1, r2) if isinstance(r, dict)]
    errs = [r for r in (r1, r2) if isinstance(r, HTTPException)]
    assert len(oks) == 1
    assert len(errs) == 1


@pytest.mark.asyncio
async def test_sibling_task_fingerprint_unchanged(db_session, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    order_id = 711031
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session)
    e6 = await _seed_employee(db_session)
    e8 = await _seed_employee(db_session)
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope(
            [
                {"task_id": TASK, "assigned_employee_id": e7.id},
                {"task_id": SIBLING, "assigned_employee_id": e8.id, "marker": "keep"},
            ]
        ),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=SIBLING, employee_id=e8.id
    )
    before = json.loads(plan.tasks_json)
    sibling_before = next(
        t for t in before["operational_tasks"] if t["task_id"] == SIBLING
    )
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7.id, e6.id])),
    )
    await reassign_operational_task_controlled(
        db_session,
        order_id=order_id,
        task_id=TASK,
        transition_id=str(uuid.uuid4()),
        expected_current_employee_id=e7.id,
        new_employee_id=e6.id,
        reason_code="MANAGER_CORRECTION",
        actor_role="manager",
    )
    await db_session.refresh(plan)
    after = json.loads(plan.tasks_json)
    sibling_after = next(
        t for t in after["operational_tasks"] if t["task_id"] == SIBLING
    )
    assert sibling_after == sibling_before


@pytest.mark.asyncio
async def test_same_transition_id_different_target_conflict(
    db_session, monkeypatch
):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    order_id = 711032
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session)
    e6 = await _seed_employee(db_session)
    e5 = await _seed_employee(db_session)
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": e7.id}]),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7.id, e6.id, e5.id])),
    )
    tid = str(uuid.uuid4())
    await reassign_operational_task_controlled(
        db_session,
        order_id=order_id,
        task_id=TASK,
        transition_id=tid,
        expected_current_employee_id=e7.id,
        new_employee_id=e6.id,
        reason_code="MANAGER_CORRECTION",
        actor_role="manager",
    )
    with pytest.raises(HTTPException) as exc:
        await reassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=tid,
            expected_current_employee_id=e7.id,
            new_employee_id=e5.id,
            reason_code="MANAGER_CORRECTION",
            actor_role="manager",
        )
    assert exc.value.detail["error"] == "transition_id_payload_conflict"
