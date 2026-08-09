"""Controlled Execution Session / Task Reality command safety — isolated DB proofs.

Never touches backend/dev.db (QA fixture 880750).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.execution_task_assignment_transition import (
    ExecutionTaskAssignmentTransition,
)
from models.orders import Orders
from schemas.auth import UserResponse
from services.controlled_pre_start_reassignment_service import (
    reassign_operational_task_controlled,
    unassign_operational_task_controlled,
)
from services.controlled_task_session_service import (
    build_execution_actuals_read_model,
    end_controlled_task_session,
    start_controlled_task_session,
)


TASK = "t_led_session_safety"


@pytest.fixture(autouse=True)
def _isolate_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _phase_b_clear_for_cross_domain(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    yield
    monkeypatch.delenv("WORKOS_PHASE_B_RESOURCE_GUARDS", raising=False)


def _user(role: str = "operator") -> UserResponse:
    uid = f"sess-{uuid.uuid4().hex[:8]}"
    return UserResponse(
        id=uid,
        email=f"{uid}@workos.test",
        name=f"User {uid}",
        role=role,
        last_login=None,
    )


def _client_for(db_fixture, user: UserResponse) -> TestClient:
    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    return TestClient(app, raise_server_exceptions=False)


def _envelope(ops: list[dict]) -> str:
    return json.dumps(
        {
            "source": "order_snapshot_v2",
            "planned_tasks": [{"task_key": TASK, "canonical_task_type": "led_assembly"}],
            "execution_tasks_created": True,
            "operational_tasks": ops,
            "dependency_edges": [],
        }
    )


async def _seed_order(db_session, order_id: int) -> Orders:
    row = Orders(
        id=order_id,
        code=f"ORD-SESS-{order_id}",
        client_name="Session Safety Client",
        status="in_production",
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _seed_employee(db_session, *, name: str = "Worker") -> Employees:
    emp = Employees(name=name, status="active", employee_type="productive")
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


async def _seed_plan(db_session, *, order_id: int, tasks_json: str) -> ExecutionPlan:
    row = ExecutionPlan(
        order_id=order_id,
        order_code=f"ORD-SESS-{order_id}",
        snapshot_version=1,
        tasks_json=tasks_json,
        total_estimated_time_minutes=0,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _seed_assign_history(
    db_session,
    *,
    plan: ExecutionPlan,
    employee_id: int,
) -> None:
    row = ExecutionTaskAssignmentTransition(
        transition_id=str(uuid.uuid4()),
        execution_plan_id=plan.id,
        order_id=plan.order_id,
        task_key=TASK,
        transition_type="ASSIGN",
        previous_employee_id=None,
        new_employee_id=employee_id,
        actor_user_id="seed",
        actor_role="admin",
        reason_code="INITIAL_ASSIGNMENT_BACKFILL",
        source="LEGACY_EMBEDDED_BACKFILL",
        expected_current_employee_id=employee_id,
        command_version="seed",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(row)
    await db_session.commit()


def _ready_elig(employee_ids: list[int]) -> dict:
    return {
        "status": "ok",
        "tasks": [
            {
                "task_key": TASK,
                "eligibility_status": "ready_with_warnings",
                "eligible_employee_count": len(employee_ids),
                "eligible_employees": [
                    {"employee_id": eid, "display_name": f"E{eid}"} for eid in employee_ids
                ],
            }
        ],
    }


@pytest.mark.asyncio
async def test_valid_start_end_actuals_and_restart_durability(db_session):
    order_id = 712001
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session, name="Andrei")
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope(
            [
                {
                    "task_id": TASK,
                    "assigned_employee_id": emp.id,
                    "workcenter": "WC_LED_ASSEMBLY",
                    "estimated_time_minutes": 30,
                }
            ]
        ),
    )
    t0 = datetime(2026, 8, 9, 10, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(minutes=18)

    start = await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0,
    )
    assert start["already_active"] is False
    assert start["started_at"]
    assert start["commercial_mutated"] is False
    sid = start["session_id"]

    # Simulate backend restart: new ORM read of committed reality.
    await db_session.commit()
    reality = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one()
    persisted = json.loads(reality.tasks_json)
    assert len(persisted) == 1
    assert persisted[0]["session_id"] == sid
    assert persisted[0]["started_at"] == start["started_at"]
    assert persisted[0].get("ended_at") in (None, "")

    # Assignment / plan technical truth unchanged.
    await db_session.refresh(plan)
    ops = json.loads(plan.tasks_json)["operational_tasks"]
    assert ops[0]["assigned_employee_id"] == emp.id
    assert ops[0]["workcenter"] == "WC_LED_ASSEMBLY"

    end = await end_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t1,
    )
    assert end["already_ended"] is False
    assert end["task_auto_completed"] is False
    assert end["duration_minutes"] == 18
    assert end["ended_at"]

    await db_session.commit()
    reality2 = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one()
    closed = json.loads(reality2.tasks_json)[0]
    assert closed["ended_at"] == end["ended_at"]
    assert closed["duration_minutes"] == 18
    assert closed["started_at"] == start["started_at"]

    actuals = await build_execution_actuals_read_model(db_session, order_id=order_id)
    row = next(t for t in actuals["tasks"] if t["task_id"] == TASK)
    assert row["total_actual_duration_minutes"] == 18
    assert row["active_session"] is False
    assert row["first_started_at"] == start["started_at"]
    assert row["last_ended_at"] == end["ended_at"]


@pytest.mark.asyncio
async def test_unassigned_and_wrong_employee_rejected(db_session):
    order_id = 712002
    await _seed_order(db_session, order_id)
    a = await _seed_employee(db_session, name="A")
    b = await _seed_employee(db_session, name="B")
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": None}]),
    )
    with pytest.raises(HTTPException) as exc:
        await start_controlled_task_session(
            db_session,
            order_id=order_id,
            task_id=TASK,
            employee_id=a.id,
            actor_mode="supervisor",
        )
    assert exc.value.detail["error"] == "task_unassigned"

    # assign A, B cannot start
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    plan.tasks_json = _envelope([{"task_id": TASK, "assigned_employee_id": a.id}])
    await db_session.commit()

    with pytest.raises(HTTPException) as exc2:
        await start_controlled_task_session(
            db_session,
            order_id=order_id,
            task_id=TASK,
            employee_id=b.id,
            actor_mode="supervisor",
        )
    assert exc2.value.detail["error"] == "employee_not_assigned"
    n = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one_or_none()
    assert n is None


@pytest.mark.asyncio
async def test_duplicate_start_and_end_idempotent(db_session):
    order_id = 712003
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": emp.id}]),
    )
    t0 = datetime(2026, 8, 9, 11, 0, 0, tzinfo=timezone.utc)
    r1 = await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0,
    )
    r2 = await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0 + timedelta(minutes=5),
    )
    assert r2["already_active"] is True
    assert r2["session_id"] == r1["session_id"]
    assert r2["started_at"] == r1["started_at"]  # no timestamp rewrite

    t1 = t0 + timedelta(minutes=12)
    e1 = await end_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t1,
    )
    e2 = await end_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t1 + timedelta(minutes=9),
    )
    assert e2["already_ended"] is True
    assert e2["ended_at"] == e1["ended_at"]
    assert e2["duration_minutes"] == e1["duration_minutes"]

    reality = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one()
    assert len(json.loads(reality.tasks_json)) == 1


@pytest.mark.asyncio
async def test_end_without_start_rejected(db_session):
    order_id = 712004
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": emp.id}]),
    )
    with pytest.raises(HTTPException) as exc:
        await end_controlled_task_session(
            db_session,
            order_id=order_id,
            task_id=TASK,
            employee_id=emp.id,
            actor_mode="supervisor",
        )
    assert exc.value.detail["error"] == "no_active_session"


@pytest.mark.asyncio
async def test_forged_task_and_cross_order_rejected(db_session):
    order_a = 712005
    order_b = 712006
    await _seed_order(db_session, order_a)
    await _seed_order(db_session, order_b)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_a,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": emp.id}]),
    )
    await _seed_plan(
        db_session,
        order_id=order_b,
        tasks_json=_envelope(
            [{"task_id": "other_task", "assigned_employee_id": emp.id}]
        ),
    )
    with pytest.raises(HTTPException) as exc:
        await start_controlled_task_session(
            db_session,
            order_id=order_b,
            task_id=TASK,  # belongs to plan A
            employee_id=emp.id,
            actor_mode="supervisor",
        )
    assert exc.value.detail["error"] == "operational_task_not_found"

    with pytest.raises(HTTPException) as exc2:
        await start_controlled_task_session(
            db_session,
            order_id=order_a,
            task_id="forged_task_key",
            employee_id=emp.id,
            actor_mode="supervisor",
        )
    assert exc2.value.detail["error"] == "operational_task_not_found"

    assert (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id.in_([order_a, order_b]))
        )
    ).scalars().all() == []


@pytest.mark.asyncio
async def test_inactive_employee_rejected(db_session):
    order_id = 712007
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session, name="Inactive")
    emp.status = "inactive"
    await db_session.commit()
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": emp.id}]),
    )
    with pytest.raises(HTTPException) as exc:
        await start_controlled_task_session(
            db_session,
            order_id=order_id,
            task_id=TASK,
            employee_id=emp.id,
            actor_mode="supervisor",
        )
    assert exc.value.detail["error"] == "inactive_employee"


@pytest.mark.asyncio
async def test_concurrent_two_employees_one_active_session(db_fixture, db_session):
    order_id = 712008
    await _seed_order(db_session, order_id)
    a = await _seed_employee(db_session, name="A")
    b = await _seed_employee(db_session, name="B")
    # Assign A; B is not assignee — B should fail assignment. Race of two starts for A
    # plus one for wrong employee covered elsewhere. Here: two concurrent starts for A.
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": a.id}]),
    )
    await db_session.commit()

    async def _start(session):
        try:
            return await start_controlled_task_session(
                session,
                order_id=order_id,
                task_id=TASK,
                employee_id=a.id,
                actor_mode="supervisor",
            )
        except HTTPException as exc:
            return exc

    async with db_fixture.session_maker() as s1, db_fixture.session_maker() as s2:
        r1, r2 = await asyncio.gather(_start(s1), _start(s2))

    oks = [r for r in (r1, r2) if isinstance(r, dict) and not r.get("already_active")]
    idem = [r for r in (r1, r2) if isinstance(r, dict) and r.get("already_active")]
    errs = [r for r in (r1, r2) if isinstance(r, HTTPException)]
    assert len(oks) + len(idem) + len(errs) == 2
    assert len(oks) == 1 or (len(oks) == 0 and len(idem) >= 1)
    # Exactly one active observation in SoT
    async with db_fixture.session_maker() as check:
        reality = (
            await check.execute(
                select(ExecutionReality).where(ExecutionReality.order_id == order_id)
            )
        ).scalar_one()
        tasks = json.loads(reality.tasks_json)
        active = [t for t in tasks if not t.get("ended_at")]
        assert len(active) == 1


@pytest.mark.asyncio
async def test_active_session_blocks_reassign_and_unassign(db_session, monkeypatch):
    order_id = 712009
    await _seed_order(db_session, order_id)
    a = await _seed_employee(db_session, name="A")
    b = await _seed_employee(db_session, name="B")
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": a.id}]),
    )
    await _seed_assign_history(db_session, plan=plan, employee_id=a.id)
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([a.id, b.id])),
    )
    await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK,
        employee_id=a.id,
        actor_mode="supervisor",
    )
    with pytest.raises(HTTPException) as exc:
        await reassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=a.id,
            new_employee_id=b.id,
            reason_code="MANAGER_CORRECTION",
            actor_role="manager",
        )
    assert exc.value.detail["error"] == "task_has_execution_history"

    with pytest.raises(HTTPException) as exc2:
        await unassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=a.id,
            reason_code="MANAGER_CORRECTION",
            actor_role="manager",
        )
    assert exc2.value.detail["error"] == "task_has_execution_history"

    # Assignment still A
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    assert (
        json.loads(plan.tasks_json)["operational_tasks"][0]["assigned_employee_id"]
        == a.id
    )


@pytest.mark.asyncio
async def test_http_auth_roles_and_viewer_denied(db_fixture, db_session):
    order_id = 712010
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": emp.id}]),
    )
    path = f"/api/v1/execution/plan/{order_id}/tasks/{TASK}/sessions/start"
    for role, expect in (("admin", 200), ("manager", 200), ("operator", 200), ("viewer", 403)):
        client = _client_for(db_fixture, _user(role))
        resp = client.post(path, json={"employee_id": emp.id})
        assert resp.status_code == expect, (role, resp.status_code, resp.text)


@pytest.mark.asyncio
async def test_employee_active_elsewhere_blocks_second_task(db_session):
    order_id = 712011
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    other = "t_other"
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope(
            [
                {"task_id": TASK, "assigned_employee_id": emp.id},
                {"task_id": other, "assigned_employee_id": emp.id},
            ]
        ),
    )
    await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK,
        employee_id=emp.id,
        actor_mode="supervisor",
    )
    with pytest.raises(HTTPException) as exc:
        await start_controlled_task_session(
            db_session,
            order_id=order_id,
            task_id=other,
            employee_id=emp.id,
            actor_mode="supervisor",
        )
    assert exc.value.detail["error"] == "employee_active_elsewhere"
