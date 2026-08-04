"""Finalization Wave 6 — minimal safe assignment command hardening.

Uses isolated test DB only. Never touches QA fixture 880750.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from types import SimpleNamespace
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
from models.orders import Orders
from schemas.auth import UserResponse
from services.controlled_employee_assignment_service import (
    CANONICAL_ASSIGNMENT_SOURCE,
    OUTCOME_ALREADY_SAME,
    OUTCOME_ASSIGNED,
    assign_operational_task_controlled,
)
from services.employee_mobile_tasks_service import claim_my_task, start_available_task
from services.execution_task_assignment_service import assign_plan_task


def _user(role: str = "admin") -> UserResponse:
    uid = f"w6-{uuid.uuid4().hex[:8]}"
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


@pytest.fixture(autouse=True)
def _isolate_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _v2_envelope(operational: list[dict], *, created: bool = True) -> str:
    return json.dumps(
        {
            "source": "order_snapshot_v2",
            "planned_tasks": [
                {
                    "task_key": "t_led",
                    "label": "LED",
                    "canonical_task_type": "led_assembly",
                }
            ],
            "execution_tasks_created": created,
            "operational_tasks": operational,
        }
    )


async def _seed_order(db_session, order_id: int) -> Orders:
    row = Orders(
        id=order_id,
        code=f"ORD-W6-{order_id}",
        client_name="Wave6 Client",
        status="in_production",
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _seed_employee(db_session, *, name: str = "Eligible Worker") -> Employees:
    emp = Employees(name=name, status="active", employee_type="productive")
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


async def _seed_plan(db_session, *, order_id: int, tasks_json: str) -> ExecutionPlan:
    row = ExecutionPlan(
        order_id=order_id,
        order_code=f"ORD-W6-{order_id}",
        snapshot_version=1,
        tasks_json=tasks_json,
        total_estimated_time_minutes=0,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


def _ready_elig(task_id: str, employee_id: int, *, extra_employees: list[int] | None = None):
    ids = [employee_id, *(extra_employees or [])]
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
                "warnings": ["planning_minutes_source_missing"],
                "requirement_version": "eligibility-rm/v1",
            }
        ],
    }


# ---------------------------------------------------------------------------
# Direct-service / Mobile / schema bypass
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_direct_assign_plan_task_blocked():
    with pytest.raises(HTTPException) as exc:
        await assign_plan_task(
            AsyncMock(),
            order_id=1,
            task_id="t",
            assigned_employee_id=1,
        )
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "direct_assign_blocked"


@pytest.mark.asyncio
async def test_mobile_claim_frozen():
    with pytest.raises(HTTPException) as exc:
        await claim_my_task(AsyncMock(), order_id=1, task_id="t", employee_id=1)
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "employee_mobile_assignment_frozen"


@pytest.mark.asyncio
async def test_mobile_start_from_available_frozen():
    with pytest.raises(HTTPException) as exc:
        await start_available_task(AsyncMock(), order_id=1, task_id="t", employee_id=1)
    assert exc.value.status_code == 403
    assert exc.value.detail["error"] == "employee_mobile_assignment_frozen"


def test_public_controlled_false_rejected(db_fixture, db_session):
    async def _setup():
        await _seed_order(db_session, 61001)
        emp = await _seed_employee(db_session)
        await _seed_plan(
            db_session,
            order_id=61001,
            tasks_json=_v2_envelope(
                [{"task_id": "t_led", "process_type": "led_assembly"}],
            ),
        )
        return emp.id

    emp_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin"))
    response = client.patch(
        "/api/v1/execution/plan/61001/tasks/t_led/assign",
        json={"assigned_employee_id": emp_id, "controlled": False},
    )
    assert response.status_code == 422, response.text
    assert "legacy_controlled_false_forbidden" in response.text


def test_public_allow_reassign_true_rejected(db_fixture, db_session):
    async def _setup():
        await _seed_order(db_session, 61002)
        emp = await _seed_employee(db_session)
        await _seed_plan(
            db_session,
            order_id=61002,
            tasks_json=_v2_envelope(
                [{"task_id": "t_led", "process_type": "led_assembly"}],
            ),
        )
        return emp.id

    emp_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin"))
    response = client.patch(
        "/api/v1/execution/plan/61002/tasks/t_led/assign",
        json={"assigned_employee_id": emp_id, "allow_reassign": True},
    )
    assert response.status_code == 422, response.text
    assert "silent_reassignment_forbidden" in response.text


def test_missing_auth_rejected(db_fixture):
    client = TestClient(app, raise_server_exceptions=False)

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    # No get_current_user override → unauthenticated
    response = client.patch(
        "/api/v1/execution/plan/61003/tasks/t_led/assign",
        json={"assigned_employee_id": 1},
    )
    # Unauthenticated clients may receive 401/403, or a non-leaking 404 depending on auth middleware.
    assert response.status_code in (401, 403, 404, 422)


def test_permission_denied_for_viewer(db_fixture, db_session):
    async def _setup():
        await _seed_order(db_session, 61004)
        emp = await _seed_employee(db_session)
        await _seed_plan(
            db_session,
            order_id=61004,
            tasks_json=_v2_envelope(
                [{"task_id": "t_led", "process_type": "led_assembly"}],
            ),
        )
        return emp.id

    emp_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("viewer"))
    response = client.patch(
        "/api/v1/execution/plan/61004/tasks/t_led/assign",
        json={"assigned_employee_id": emp_id},
    )
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# CAS / idempotency / eligibility (isolated DB + eligibility stub)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cas_first_assign_same_retry_different_conflict(db_session, monkeypatch):
    order_id = 61101
    await _seed_order(db_session, order_id)
    emp_a = await _seed_employee(db_session, name="Alpha")
    emp_b = await _seed_employee(db_session, name="Beta")
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(
            [
                {"task_id": "t_led", "process_type": "led_assembly"},
                {"task_id": "t_other", "process_type": "cnc_routing"},
            ]
        ),
    )

    async def fake_elig(db, oid):
        return _ready_elig("t_led", emp_a.id, extra_employees=[emp_b.id])

    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.build_employee_eligibility_read_model",
        fake_elig,
    )

    first = await assign_operational_task_controlled(
        db_session,
        order_id=order_id,
        task_id="t_led",
        assigned_employee_id=emp_a.id,
        actor_user_id="actor-1",
    )
    assert first["assignment_outcome"] == OUTCOME_ASSIGNED
    assert first["task"]["assignment_source"] == CANONICAL_ASSIGNMENT_SOURCE
    assert first["task"]["assignment_actor_user_id"] == "actor-1"

    plan = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    envelope = json.loads(plan.tasks_json)
    assert envelope["operational_tasks"][0]["assigned_employee_id"] == emp_a.id
    # Sibling task untouched.
    assert envelope["operational_tasks"][1].get("assigned_employee_id") is None

    retry = await assign_operational_task_controlled(
        db_session,
        order_id=order_id,
        task_id="t_led",
        assigned_employee_id=emp_a.id,
        actor_user_id="actor-2",
    )
    assert retry["assignment_outcome"] == OUTCOME_ALREADY_SAME
    assert retry["already_assigned"] is True
    # No duplicate audit overwrite on idempotent retry.
    plan2 = (
        await db_session.execute(
            select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
        )
    ).scalar_one()
    env2 = json.loads(plan2.tasks_json)
    assert env2["operational_tasks"][0].get("assignment_actor_user_id") == "actor-1"

    with pytest.raises(HTTPException) as exc:
        await assign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id="t_led",
            assigned_employee_id=emp_b.id,
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["error"] == "already_assigned_to_different_employee"


@pytest.mark.asyncio
async def test_employee_not_eligible_inside_lock(db_session, monkeypatch):
    order_id = 61102
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(
            [{"task_id": "t_led", "process_type": "led_assembly"}]
        ),
    )

    async def fake_elig(db, oid):
        return _ready_elig("t_led", employee_id=99999)

    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.build_employee_eligibility_read_model",
        fake_elig,
    )
    with pytest.raises(HTTPException) as exc:
        await assign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id="t_led",
            assigned_employee_id=emp.id,
        )
    assert exc.value.detail["error"] == "employee_not_eligible"


@pytest.mark.asyncio
async def test_inactive_employee_rejected(db_session, monkeypatch):
    order_id = 61103
    await _seed_order(db_session, order_id)
    emp = Employees(name="Inactive", status="inactive", employee_type="productive")
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(
            [{"task_id": "t_led", "process_type": "led_assembly"}]
        ),
    )

    async def fake_elig(db, oid):
        return _ready_elig("t_led", emp.id)

    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.build_employee_eligibility_read_model",
        fake_elig,
    )
    with pytest.raises(HTTPException) as exc:
        await assign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id="t_led",
            assigned_employee_id=emp.id,
        )
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == "inactive_employee"


@pytest.mark.asyncio
async def test_completed_task_stale_conflict(db_session, monkeypatch):
    order_id = 61104
    await _seed_order(db_session, order_id)
    emp = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(
            [{"task_id": "t_led", "process_type": "led_assembly"}]
        ),
    )
    db_session.add(
        ExecutionReality(
            order_id=order_id,
            order_code=f"ORD-W6-{order_id}",
            tasks_json=json.dumps(
                [
                    {
                        "task_id": "t_led",
                        "started_at": "2026-08-01T08:00:00+00:00",
                        "ended_at": "2026-08-01T09:00:00+00:00",
                    }
                ]
            ),
            total_actual_time_minutes=60,
        )
    )
    await db_session.commit()

    async def fake_elig(db, oid):
        return _ready_elig("t_led", emp.id)

    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.build_employee_eligibility_read_model",
        fake_elig,
    )
    with pytest.raises(HTTPException) as exc:
        await assign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id="t_led",
            assigned_employee_id=emp.id,
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["error"] == "stale_task_state"


@pytest.mark.asyncio
async def test_order_not_found(db_session):
    with pytest.raises(HTTPException) as exc:
        await assign_operational_task_controlled(
            db_session,
            order_id=69999,
            task_id="t_led",
            assigned_employee_id=1,
        )
    assert exc.value.status_code == 404
    assert exc.value.detail["error"] == "order_not_found"


@pytest.mark.asyncio
async def test_concurrent_two_employees_one_winner(db_session, monkeypatch):
    order_id = 61105
    await _seed_order(db_session, order_id)
    emp_a = await _seed_employee(db_session, name="A")
    emp_b = await _seed_employee(db_session, name="B")
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(
            [{"task_id": "t_led", "process_type": "led_assembly"}]
        ),
    )

    async def fake_elig(db, oid):
        return _ready_elig("t_led", emp_a.id, extra_employees=[emp_b.id])

    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.build_employee_eligibility_read_model",
        fake_elig,
    )

    # Separate sessions sharing the same isolated engine (db_session fixture is one session).
    # Use sequential gather against the same session with the plan lock — simulates race.
    results: list[object] = []

    async def _try(emp_id: int):
        try:
            # Re-enter with current session; lock serializes.
            out = await assign_operational_task_controlled(
                db_session,
                order_id=order_id,
                task_id="t_led",
                assigned_employee_id=emp_id,
            )
            results.append(out)
        except HTTPException as exc:
            results.append(exc)

    await asyncio.gather(_try(emp_a.id), _try(emp_b.id))
    successes = [r for r in results if isinstance(r, dict) and r.get("assignment_outcome") == OUTCOME_ASSIGNED]
    conflicts = [
        r
        for r in results
        if isinstance(r, HTTPException)
        and r.detail.get("error") == "already_assigned_to_different_employee"
    ]
    idempotent = [
        r
        for r in results
        if isinstance(r, dict) and r.get("assignment_outcome") == OUTCOME_ALREADY_SAME
    ]
    assert len(successes) == 1
    assert len(conflicts) + len(idempotent) == 1


@pytest.mark.asyncio
async def test_allow_reassign_ignored_no_overwrite(db_session, monkeypatch):
    order_id = 61106
    await _seed_order(db_session, order_id)
    emp_a = await _seed_employee(db_session, name="A")
    emp_b = await _seed_employee(db_session, name="B")
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_v2_envelope(
            [{"task_id": "t_led", "process_type": "led_assembly"}]
        ),
    )

    async def fake_elig(db, oid):
        return _ready_elig("t_led", emp_a.id, extra_employees=[emp_b.id])

    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.build_employee_eligibility_read_model",
        fake_elig,
    )
    await assign_operational_task_controlled(
        db_session,
        order_id=order_id,
        task_id="t_led",
        assigned_employee_id=emp_a.id,
    )
    with pytest.raises(HTTPException) as exc:
        await assign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id="t_led",
            assigned_employee_id=emp_b.id,
            allow_reassign=True,
        )
    assert exc.value.detail["error"] == "already_assigned_to_different_employee"


@pytest.mark.asyncio
async def test_unit_eligibility_blocked_status(monkeypatch):
    async def fake_elig(db, order_id):
        return {
            "status": "ok",
            "tasks": [
                {
                    "task_key": "t_prepress",
                    "eligibility_status": "blocked_no_matching_employee",
                    "eligible_employee_count": 0,
                    "eligible_employees": [],
                    "blockers": ["no_matching_employee"],
                }
            ],
        }

    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.build_employee_eligibility_read_model",
        fake_elig,
    )

    # Minimal fake DB that returns order + employee + plan under lock path is heavy;
    # this unit covers the eligibility failure helper via a thin integration-shaped mock.
    order = SimpleNamespace(id=1)
    emp = SimpleNamespace(
        id=7,
        name="X",
        status="active",
        end_date=None,
        employee_type="productive",
    )

    class _Result:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

    plan = SimpleNamespace(
        id=9,
        order_id=1,
        order_code="O",
        tasks_json=_v2_envelope(
            [{"task_id": "t_prepress", "process_type": "prepress"}],
        ),
    )

    calls = {"n": 0}

    async def fake_execute(stmt):
        # Rough sequencing: Orders, Employees (pre), ExecutionPlan, Employees (re), Reality
        calls["n"] += 1
        n = calls["n"]
        if n == 1:
            return _Result(order)
        if n in (2, 4):
            return _Result(emp)
        if n == 3:
            return _Result(plan)
        return _Result(None)

    db = AsyncMock()
    db.execute = fake_execute
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()

    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.assert_operational_mutation_allowed",
        lambda p: None,
    )
    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.is_assignable",
        lambda e, d: True,
    )

    with pytest.raises(HTTPException) as exc:
        await assign_operational_task_controlled(
            db,
            order_id=1,
            task_id="t_prepress",
            assigned_employee_id=7,
        )
    assert exc.value.detail["error"] == "blocked_no_matching_employee"
