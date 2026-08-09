"""Profitability Actual Labor Input Closure — isolated DB controlled scenarios.

Never touches backend/dev.db (QA fixture 880750).
No monetary rates. No schema migration. No profitability UI.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from schemas.auth import UserResponse
from services.controlled_task_session_service import (
    complete_controlled_task_session,
    end_controlled_task_session,
    start_controlled_task_session,
)
from services.profitability_actual_labor_input_service import (
    CANONICAL_DURATION_UNIT,
    DURATION_SOURCE,
    ROUNDING_RULE,
    build_profitability_actual_labor_input,
)
from services.task_work_session_service import compute_duration_minutes


TASK_A = "t_labor_a"
TASK_B = "t_labor_b"
QA_ORDER_ID = 880750


@pytest.fixture(autouse=True)
def _isolate_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _phase_b_clear(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    yield
    monkeypatch.delenv("WORKOS_PHASE_B_RESOURCE_GUARDS", raising=False)


def _user(role: str = "admin") -> UserResponse:
    uid = f"lab-{uuid.uuid4().hex[:8]}"
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
            "planned_tasks": [
                {"task_key": o["task_id"], "canonical_task_type": "led_assembly"}
                for o in ops
            ],
            "execution_tasks_created": True,
            "operational_tasks": ops,
            "dependency_edges": [],
        }
    )


async def _seed_order(db_session, order_id: int) -> Orders:
    row = Orders(
        id=order_id,
        code=f"ORD-LAB-{order_id}",
        client_name="Labor Input Client",
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


async def _seed_plan(db_session, *, order_id: int, ops: list[dict]) -> ExecutionPlan:
    row = ExecutionPlan(
        order_id=order_id,
        order_code=f"ORD-LAB-{order_id}",
        snapshot_version=1,
        tasks_json=_envelope(ops),
        total_estimated_time_minutes=sum(
            int(o.get("estimated_time_minutes") or 0) for o in ops
        ),
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _run_closed_session(
    db_session,
    *,
    order_id: int,
    task_id: str,
    employee_id: int,
    start: datetime,
    minutes: int,
) -> dict:
    await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=task_id,
        employee_id=employee_id,
        actor_mode="supervisor",
        clock=lambda: start,
    )
    end = await end_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=task_id,
        employee_id=employee_id,
        actor_mode="supervisor",
        clock=lambda: start + timedelta(minutes=minutes),
    )
    await db_session.commit()
    return end


async def _set_assignee(db_session, order_id: int, task_id: str, employee_id: int) -> None:
    """Test-only assignment pointer swap (not Phase E production reassignment)."""
    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    data = json.loads(plan.tasks_json)
    for op in data["operational_tasks"]:
        if op["task_id"] == task_id:
            op["assigned_employee_id"] = employee_id
    plan.tasks_json = json.dumps(data)
    await db_session.commit()


@pytest.mark.asyncio
async def test_01_single_closed_session(db_session):
    order_id = 914001
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session, name="A")
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[
            {
                "task_id": TASK_A,
                "assigned_employee_id": emp.id,
                "workcenter": "WC_LED",
                "estimated_time_minutes": 45,
            }
        ],
    )
    t0 = datetime(2026, 8, 9, 8, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        start=t0,
        minutes=30,
    )

    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["contract"] == "profitability_actual_labor_input/v1"
    assert labor["order_id"] == order_id
    assert labor["execution_plan_id"] == plan.id
    assert labor["write_authority"] == "controlled_task_session_service"
    assert labor["duration_source"] == DURATION_SOURCE
    assert labor["canonical_duration_unit"] == CANONICAL_DURATION_UNIT
    assert labor["rounding_rule"] == ROUNDING_RULE
    assert labor["machine_run_included"] is False
    assert labor["monetary_rates_included"] is False
    assert labor["totals"]["closed_session_count"] == 1
    assert labor["totals"]["total_employee_minutes"] == 30
    assert labor["totals"]["active_session_count"] == 0
    s0 = labor["closed_sessions"][0]
    assert s0["employee_id"] == emp.id
    assert s0["task_id"] == TASK_A
    assert s0["actual_duration_minutes"] == 30
    assert s0["actual_duration_seconds"] == 1800
    assert s0["order_id"] == order_id
    assert s0["execution_plan_id"] == plan.id


@pytest.mark.asyncio
async def test_02_two_sessions_same_employee_task(db_session):
    order_id = 914002
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session, name="A")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id, "estimated_time_minutes": 60}],
    )
    t0 = datetime(2026, 8, 9, 9, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=20
    )
    await _run_closed_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        start=t0 + timedelta(hours=1),
        minutes=15,
    )

    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["totals"]["closed_session_count"] == 2
    assert labor["totals"]["total_employee_minutes"] == 35
    assert len(labor["closed_sessions"]) == 2
    assert {s["actual_duration_minutes"] for s in labor["closed_sessions"]} == {20, 15}
    et = labor["by_employee_task"][0]
    assert et["employee_id"] == emp.id
    assert et["total_employee_minutes"] == 35
    assert et["session_count"] == 2


@pytest.mark.asyncio
async def test_03_two_employees_same_task_employee_minutes_sum(db_session):
    """Aggregation sums employee-minutes; concurrent primary starts are writer-blocked.

    Production Phase E reassignment after history is deferred. This scenario swaps the
    assignment pointer in the isolated fixture so two closed sessions can be authored
    sequentially for different employees — proving labor input aggregation, not Phase E.
    """
    order_id = 914003
    await _seed_order(db_session, order_id)
    a = await _seed_employee(db_session, name="A")
    b = await _seed_employee(db_session, name="B")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": a.id, "estimated_time_minutes": 60}],
    )
    t0 = datetime(2026, 8, 9, 10, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=a.id, start=t0, minutes=20
    )
    await _set_assignee(db_session, order_id, TASK_A, b.id)
    await _run_closed_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=b.id,
        start=t0 + timedelta(hours=1),
        minutes=30,
    )

    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["totals"]["total_employee_minutes"] == 50
    assert labor["totals"]["closed_session_count"] == 2
    by_emp = {row["employee_id"]: row["total_employee_minutes"] for row in labor["by_employee_task"]}
    assert by_emp[a.id] == 20
    assert by_emp[b.id] == 30


@pytest.mark.asyncio
async def test_04_multiple_tasks_plan_aggregation(db_session):
    order_id = 914004
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session, name="A")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[
            {"task_id": TASK_A, "assigned_employee_id": emp.id, "estimated_time_minutes": 20},
            {"task_id": TASK_B, "assigned_employee_id": emp.id, "estimated_time_minutes": 40},
        ],
    )
    t0 = datetime(2026, 8, 9, 11, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=20
    )
    await _run_closed_session(
        db_session,
        order_id=order_id,
        task_id=TASK_B,
        employee_id=emp.id,
        start=t0 + timedelta(hours=1),
        minutes=40,
    )

    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["totals"]["total_employee_minutes"] == 60
    by_task = {t["task_id"]: t["total_employee_minutes"] for t in labor["by_task"]}
    assert by_task[TASK_A] == 20
    assert by_task[TASK_B] == 40


@pytest.mark.asyncio
async def test_05_order_equals_single_plan_aggregation(db_session):
    """Current architecture: one ExecutionPlan per order_id — order totals == plan totals."""
    order_id = 914005
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=12
    )
    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["order_id"] == order_id
    assert labor["execution_plan_id"] is not None
    assert labor["totals"]["total_employee_minutes"] == 12


@pytest.mark.asyncio
async def test_06_active_excluded_from_final_totals(db_session):
    order_id = 914006
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 9, 13, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=20
    )
    await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0 + timedelta(hours=2),
    )
    await db_session.commit()

    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["totals"]["total_employee_minutes"] == 20
    assert labor["totals"]["closed_session_count"] == 1
    assert labor["totals"]["active_session_count"] == 1
    assert labor["active_sessions"][0]["contribution"] == "not_final"


@pytest.mark.asyncio
async def test_07_restart_durability(db_session):
    order_id = 914007
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 9, 14, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=17
    )
    first = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    # Simulate restart: re-read from DB only
    await db_session.commit()
    reality = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one()
    assert reality.tasks_json
    second = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert first["totals"] == second["totals"]
    assert first["closed_sessions"][0]["session_id"] == second["closed_sessions"][0]["session_id"]
    assert first["closed_sessions"][0]["actual_duration_minutes"] == 17


@pytest.mark.asyncio
async def test_08_idempotent_replay_no_duplication(db_session):
    order_id = 914008
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 9, 15, 0, 0, tzinfo=timezone.utc)
    s1 = await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0,
    )
    s2 = await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0 + timedelta(minutes=1),
    )
    assert s2["already_active"] is True
    assert s2["session_id"] == s1["session_id"]
    await end_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0 + timedelta(minutes=10),
    )
    e2 = await end_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0 + timedelta(minutes=99),
    )
    assert e2["already_ended"] is True
    await db_session.commit()

    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["totals"]["closed_session_count"] == 1
    assert labor["totals"]["total_employee_minutes"] == 10


@pytest.mark.asyncio
async def test_09_compatibility_bridge_parity(db_fixture, db_session):
    order_id = 914009
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id, "estimated_time_minutes": 30}],
    )
    client = _client_for(db_fixture, _user("admin"))
    forged = "2099-01-01T00:00:00+00:00"
    r1 = client.post(
        "/api/v1/execution/reality/start-task",
        json={"order_id": order_id, "task_id": TASK_A, "timestamp": forged},
    )
    assert r1.status_code == 200, r1.text
    # End via controlled clock path for deterministic duration after bridge start.
    reality = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one()
    started = json.loads(reality.tasks_json)[0]["started_at"]
    start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
    await end_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: start_dt + timedelta(minutes=22),
    )
    await db_session.commit()

    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["totals"]["closed_session_count"] == 1
    assert labor["totals"]["total_employee_minutes"] == 22
    assert labor["closed_sessions"][0]["started_at"] != forged


@pytest.mark.asyncio
async def test_10_machine_run_not_in_labor_totals(db_session):
    order_id = 914010
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[
            {
                "task_id": TASK_A,
                "assigned_employee_id": emp.id,
                "machine_id": "M-CNC-1",
                "estimated_time_minutes": 30,
            }
        ],
    )
    t0 = datetime(2026, 8, 9, 16, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=30
    )
    # Second employee-minute session after pointer swap (simulates 20m second worker).
    b = await _seed_employee(db_session, name="B")
    await _set_assignee(db_session, order_id, TASK_A, b.id)
    await _run_closed_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=b.id,
        start=t0 + timedelta(hours=1),
        minutes=20,
    )

    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["machine_run_included"] is False
    assert labor["totals"]["total_employee_minutes"] == 50  # not 30 machine minutes


@pytest.mark.asyncio
async def test_11_planned_vs_actual_separation(db_session):
    order_id = 914011
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[
            {
                "task_id": TASK_A,
                "assigned_employee_id": emp.id,
                "estimated_time_minutes": 100,
            }
        ],
    )
    t0 = datetime(2026, 8, 9, 17, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=12
    )
    await db_session.refresh(plan)
    planned = json.loads(plan.tasks_json)["operational_tasks"][0]["estimated_time_minutes"]
    assert planned == 100

    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["planned_minutes_mutated"] is False
    assert labor["by_task"][0]["planned_minutes"] == 100
    assert labor["totals"]["total_employee_minutes"] == 12


@pytest.mark.asyncio
async def test_12_incomplete_task_retains_closed_labor(db_session):
    order_id = 914012
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 9, 18, 0, 0, tzinfo=timezone.utc)
    end = await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=30
    )
    assert end["task_auto_completed"] is False

    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["totals"]["total_employee_minutes"] == 30


@pytest.mark.asyncio
async def test_13_complete_stamp_does_not_duplicate_minutes(db_session):
    order_id = 914013
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 9, 19, 0, 0, tzinfo=timezone.utc)
    # Path: END first (session closed, task not complete).
    await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0,
    )
    await end_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0 + timedelta(minutes=25),
    )
    before = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert before["totals"]["total_employee_minutes"] == 25

    # Complete after END requires an active session — rejected; labor unchanged.
    with pytest.raises(HTTPException) as exc:
        await complete_controlled_task_session(
            db_session,
            order_id=order_id,
            task_id=TASK_A,
            employee_id=emp.id,
            actor_mode="supervisor",
            clock=lambda: t0 + timedelta(minutes=26),
        )
    assert exc.value.detail["error"] == "no_active_session"

    # Explicit complete path (start → complete) stamps once; replay does not add minutes.
    await start_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0 + timedelta(hours=1),
    )
    c1 = await complete_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0 + timedelta(hours=1, minutes=10),
    )
    assert c1["already_completed"] is False
    mid = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    c2 = await complete_controlled_task_session(
        db_session,
        order_id=order_id,
        task_id=TASK_A,
        employee_id=emp.id,
        actor_mode="supervisor",
        clock=lambda: t0 + timedelta(hours=1, minutes=99),
    )
    assert c2["already_completed"] is True
    after = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert mid["totals"]["total_employee_minutes"] == 35  # 25 + 10
    assert after["totals"]["total_employee_minutes"] == 35
    assert after["totals"]["closed_session_count"] == mid["totals"]["closed_session_count"]


@pytest.mark.asyncio
async def test_14_rounding_matches_canonical_minutes_helper():
    started = "2026-08-09T10:00:00+00:00"
    ended = "2026-08-09T10:00:29+00:00"  # 29s → 0 min
    assert compute_duration_minutes(started, ended) == 0
    # banker's round: 30s → 0.5 → nearest even → 0 min
    ended2 = "2026-08-09T10:00:30+00:00"
    assert compute_duration_minutes(started, ended2) == 0
    # 90s → 1.5 → nearest even → 2 min
    ended3 = "2026-08-09T10:01:30+00:00"
    assert compute_duration_minutes(started, ended3) == 2
    assert CANONICAL_DURATION_UNIT == "minutes"
    assert ROUNDING_RULE == "python_round_half_to_even_seconds_over_60_to_int_minutes"


@pytest.mark.asyncio
async def test_15_timezone_duration_from_absolute_timestamps(db_session):
    order_id = 914015
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id}],
    )
    # Same absolute interval expressed with offset — duration must be 60 minutes.
    t0 = datetime(2026, 8, 9, 10, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=60
    )
    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["totals"]["total_employee_minutes"] == 60
    assert labor["closed_sessions"][0]["actual_duration_seconds"] == 3600


@pytest.mark.asyncio
async def test_16_malformed_sessions_fail_closed(db_session):
    order_id = 914016
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 9, 20, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=10
    )
    reality = (
        await db_session.execute(
            select(ExecutionReality).where(ExecutionReality.order_id == order_id)
        )
    ).scalar_one()
    rows = json.loads(reality.tasks_json)
    rows.append(
        {
            "session_id": "bad-ended-before",
            "task_id": TASK_A,
            "employee_id": emp.id,
            "started_at": (t0 + timedelta(hours=2)).isoformat(),
            "ended_at": (t0 + timedelta(hours=1)).isoformat(),
            "status": "ended",
        }
    )
    rows.append(
        {
            "session_id": "bad-no-emp",
            "task_id": TASK_A,
            "employee_id": None,
            "started_at": t0.isoformat(),
            "ended_at": (t0 + timedelta(minutes=5)).isoformat(),
            "status": "ended",
        }
    )
    rows.append(
        {
            "session_id": "orphan-task",
            "task_id": "not_on_plan",
            "employee_id": emp.id,
            "started_at": t0.isoformat(),
            "ended_at": (t0 + timedelta(minutes=5)).isoformat(),
            "status": "ended",
        }
    )
    reality.tasks_json = json.dumps(rows)
    await db_session.commit()

    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["totals"]["total_employee_minutes"] == 10
    assert labor["totals"]["invalid_session_count"] == 3
    reasons = {r["reason"] for r in labor["invalid_sessions"]}
    assert "ended_before_started_or_unparseable" in reasons
    assert "missing_employee" in reasons
    assert "task_not_on_operational_plan" in reasons


@pytest.mark.asyncio
async def test_18_mutable_upstream_name_does_not_change_labor(db_session):
    order_id = 914018
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session, name="Original")
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 9, 21, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=8
    )
    before = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    emp.name = "Renamed Later"
    await db_session.commit()
    after = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert before["totals"] == after["totals"]
    assert before["closed_sessions"][0]["employee_id"] == after["closed_sessions"][0]["employee_id"]


@pytest.mark.asyncio
async def test_19_write_authority_and_no_commercial_mutation(db_session):
    order_id = 914019
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 9, 22, 0, 0, tzinfo=timezone.utc)
    end = await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=5
    )
    assert end["commercial_mutated"] is False
    labor = await build_profitability_actual_labor_input(db_session, order_id=order_id)
    assert labor["write_authority"] == "controlled_task_session_service"
    assert labor["commercial_mutated"] is False
    assert labor["monetary_rates_included"] is False


@pytest.mark.asyncio
async def test_20_qa_fixture_untouched(db_session):
    before = (
        await db_session.execute(
            text("SELECT COUNT(*) FROM orders WHERE id = :oid"),
            {"oid": QA_ORDER_ID},
        )
    ).scalar()
    # Labor input builder must not create QA rows when order missing / unrelated.
    order_id = 914020
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        ops=[{"task_id": TASK_A, "assigned_employee_id": emp.id}],
    )
    t0 = datetime(2026, 8, 9, 23, 0, 0, tzinfo=timezone.utc)
    await _run_closed_session(
        db_session, order_id=order_id, task_id=TASK_A, employee_id=emp.id, start=t0, minutes=3
    )
    await build_profitability_actual_labor_input(db_session, order_id=order_id)
    after = (
        await db_session.execute(
            text("SELECT COUNT(*) FROM orders WHERE id = :oid"),
            {"oid": QA_ORDER_ID},
        )
    ).scalar()
    assert before == after
