"""Legacy session write-path assignment-gate closure — cross-path parity proofs.

Isolated DB only. Never touches QA fixture 880750.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from schemas.auth import UserResponse


TASK = "t_legacy_closure"


@pytest.fixture(autouse=True)
def _isolate_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _user(role: str = "operator") -> UserResponse:
    uid = f"lg-{uuid.uuid4().hex[:8]}"
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


async def _seed(db_session, order_id: int, *, assigned: int | None):
    db_session.add(
        Orders(
            id=order_id,
            code=f"ORD-LG-{order_id}",
            client_name="Legacy Closure",
            status="in_production",
        )
    )
    await db_session.commit()
    emp = Employees(name="Assignee", status="active", employee_type="productive")
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    other = Employees(name="Other", status="active", employee_type="productive")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)
    plan = ExecutionPlan(
        order_id=order_id,
        order_code=f"ORD-LG-{order_id}",
        snapshot_version=1,
        tasks_json=_envelope(
            [
                {
                    "task_id": TASK,
                    "assigned_employee_id": assigned if assigned is not None else emp.id,
                    "workcenter": "WC_LED",
                    "estimated_time_minutes": 20,
                }
            ]
        ),
        total_estimated_time_minutes=20,
    )
    if assigned is None:
        plan.tasks_json = _envelope(
            [{"task_id": TASK, "assigned_employee_id": None, "workcenter": "WC_LED"}]
        )
    db_session.add(plan)
    await db_session.commit()
    return emp, other


@pytest.mark.asyncio
async def test_reality_and_operator_start_require_assignment(db_fixture, db_session):
    order_id = 813001
    emp, other = await _seed(db_session, order_id, assigned=None)
    # force unassigned
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    plan.tasks_json = _envelope([{"task_id": TASK, "assigned_employee_id": None}])
    await db_session.commit()

    client = _client_for(db_fixture, _user("admin"))
    forged_ts = "2099-01-01T00:00:00+00:00"
    r1 = client.post(
        "/api/v1/execution/reality/start-task",
        json={"order_id": order_id, "task_id": TASK, "timestamp": forged_ts},
    )
    assert r1.status_code == 422
    assert r1.json()["detail"]["error"] == "task_unassigned"

    r2 = client.post(
        "/api/v1/operator/task-action",
        json={
            "order_id": order_id,
            "task_id": TASK,
            "action": "start",
            "employee_id": emp.id,
        },
    )
    assert r2.status_code == 422
    assert r2.json()["detail"]["error"] == "task_unassigned"


@pytest.mark.asyncio
async def test_wrong_employee_rejected_on_legacy_paths(db_fixture, db_session):
    order_id = 813002
    emp, other = await _seed(db_session, order_id, assigned=0)
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    plan.tasks_json = _envelope([{"task_id": TASK, "assigned_employee_id": emp.id}])
    await db_session.commit()

    client = _client_for(db_fixture, _user("manager"))
    r = client.post(
        "/api/v1/operator/task-action",
        json={
            "order_id": order_id,
            "task_id": TASK,
            "action": "start",
            "employee_id": other.id,
        },
    )
    assert r.status_code == 422
    assert r.json()["detail"]["error"] == "employee_not_assigned"


@pytest.mark.asyncio
async def test_cross_path_start_end_parity_and_forged_timestamp(db_fixture, db_session):
    order_id = 813003
    emp, _ = await _seed(db_session, order_id, assigned=0)
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    plan.tasks_json = _envelope(
        [{"task_id": TASK, "assigned_employee_id": emp.id, "estimated_time_minutes": 20}]
    )
    await db_session.commit()

    client = _client_for(db_fixture, _user("admin"))
    forged = "1999-01-01T00:00:00+00:00"
    start = client.post(
        "/api/v1/execution/reality/start-task",
        json={"order_id": order_id, "task_id": TASK, "timestamp": forged},
    )
    assert start.status_code == 200, start.text
    started_at = start.json()["tasks"][0]["started_at"]
    assert not started_at.startswith("1999")

    # Canonical session end via controlled URL
    end = client.post(
        f"/api/v1/execution/plan/{order_id}/tasks/{TASK}/sessions/end",
        json={"employee_id": emp.id},
    )
    assert end.status_code == 200, end.text
    assert end.json()["started_at"] == started_at
    assert end.json()["task_auto_completed"] is False

    reality = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one()
    tasks = json.loads(reality.tasks_json)
    assert len(tasks) == 1
    assert tasks[0]["started_at"] == started_at
    assert tasks[0].get("completed_by_employee_id") is None


@pytest.mark.asyncio
async def test_legacy_start_canonical_end_and_duplicate_start(db_fixture, db_session):
    order_id = 813004
    emp, _ = await _seed(db_session, order_id, assigned=0)
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    plan.tasks_json = _envelope([{"task_id": TASK, "assigned_employee_id": emp.id}])
    await db_session.commit()
    client = _client_for(db_fixture, _user("operator"))

    s1 = client.post(
        "/api/v1/operator/task-action",
        json={
            "order_id": order_id,
            "task_id": TASK,
            "action": "start",
            "employee_id": emp.id,
        },
    )
    assert s1.status_code == 200, s1.text
    started = s1.json()["timestamp"]

    s2 = client.post(
        f"/api/v1/execution/plan/{order_id}/tasks/{TASK}/sessions/start",
        json={"employee_id": emp.id},
    )
    assert s2.status_code == 200
    assert s2.json()["already_active"] is True
    assert s2.json()["started_at"] == started

    e1 = client.post(
        "/api/v1/execution/reality/end-task",
        json={
            "order_id": order_id,
            "task_id": TASK,
            "timestamp": "2099-12-31T00:00:00+00:00",
        },
    )
    assert e1.status_code == 200
    ended = e1.json()["tasks"][0]["ended_at"]
    assert not ended.startswith("2099")

    e2 = client.post(
        f"/api/v1/execution/plan/{order_id}/tasks/{TASK}/sessions/end",
        json={"employee_id": emp.id},
    )
    assert e2.status_code == 200
    assert e2.json()["already_ended"] is True
    assert e2.json()["ended_at"] == ended


@pytest.mark.asyncio
async def test_concurrent_legacy_vs_canonical_start(db_fixture, db_session):
    order_id = 813005
    emp, _ = await _seed(db_session, order_id, assigned=0)
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    plan.tasks_json = _envelope([{"task_id": TASK, "assigned_employee_id": emp.id}])
    await db_session.commit()

    from services.controlled_task_session_service import start_controlled_task_session

    async def _canon(session):
        try:
            return await start_controlled_task_session(
                session,
                order_id=order_id,
                task_id=TASK,
                employee_id=emp.id,
                actor_mode="supervisor",
            )
        except Exception as exc:  # noqa: BLE001 — capture for race outcomes
            return exc

    async with db_fixture.session_maker() as s1, db_fixture.session_maker() as s2:
        r1, r2 = await asyncio.gather(_canon(s1), _canon(s2))
    dicts = [r for r in (r1, r2) if isinstance(r, dict)]
    oks = [r for r in dicts if not r.get("already_active")]
    assert len(oks) <= 1
    assert len(dicts) >= 1

    async with db_fixture.session_maker() as check:
        reality = (
            await check.execute(
                select(ExecutionReality).where(ExecutionReality.order_id == order_id)
            )
        ).scalar_one()
        active = [t for t in json.loads(reality.tasks_json) if not t.get("ended_at")]
        assert len(active) == 1
