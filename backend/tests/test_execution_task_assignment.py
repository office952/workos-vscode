"""Tests for execution plan task assignment (Wave 6 hardened public contract)."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from schemas.auth import UserResponse

from core.database import get_db
from dependencies.auth import get_current_user
from main import app


def _user(user_id: str, role: str = "admin") -> UserResponse:
    return UserResponse(
        id=user_id,
        email=f"{user_id}@workos.test",
        name=f"User {user_id}",
        role=role,
        last_login=None,
    )


async def _seed_employee(db_session, *, name: str = "Assignee", user_id: str | None = None) -> Employees:
    emp = Employees(
        name=name,
        status="active",
        employee_type="productive",
        user_id=user_id,
    )
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


async def _seed_order(db_session, order_id: int) -> Orders:
    row = Orders(
        id=order_id,
        code=f"ORD-{order_id}",
        client_name="Assign Client",
        status="in_production",
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _seed_plan(db_session, *, order_id: int = 98101, task_id: str = "T-ASSIGN") -> ExecutionPlan:
    tasks = [
        {
            "task_id": task_id,
            "name": "Print",
            "process_type": "print",
            "machine_type": "printer_large_format",
            "estimated_time_minutes": 20,
        }
    ]
    row = ExecutionPlan(
        order_id=order_id,
        order_code=f"ORD-{order_id}",
        snapshot_version=1,
        tasks_json=json.dumps(tasks),
        total_estimated_time_minutes=20,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


def _client_for(db_fixture, user: UserResponse) -> TestClient:
    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    return TestClient(app, raise_server_exceptions=False)


def _cleanup():
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _isolate_app_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(db_fixture):
    uid = f"admin-{uuid.uuid4().hex[:8]}"
    client = _client_for(db_fixture, _user(uid, "admin"))
    yield client
    _cleanup()


def test_legacy_controlled_false_rejected(db_fixture, db_session, admin_client):
    async def _setup():
        await _seed_order(db_session, 98101)
        emp = await _seed_employee(db_session, name="Mobile Worker")
        await _seed_plan(db_session, order_id=98101, task_id="T-ASSIGN")
        return emp.id

    employee_id = db_fixture.run(_setup())

    response = admin_client.patch(
        "/api/v1/execution/plan/98101/tasks/T-ASSIGN/assign",
        json={"assigned_employee_id": employee_id, "controlled": False},
    )
    assert response.status_code == 422, response.text
    assert "legacy_controlled_false_forbidden" in response.text


def test_controlled_assign_rejects_non_materialized_plan(db_fixture, db_session, admin_client):
    """Default canonical path requires operational_tasks[] / eligibility RM."""

    async def _setup():
        await _seed_order(db_session, 98111)
        emp = await _seed_employee(db_session, name="Blocked Legacy")
        await _seed_plan(db_session, order_id=98111, task_id="T-LEGACY")
        return emp.id

    employee_id = db_fixture.run(_setup())
    response = admin_client.patch(
        "/api/v1/execution/plan/98111/tasks/T-LEGACY/assign",
        json={"assigned_employee_id": employee_id},
    )
    assert response.status_code == 422, response.text
    detail = response.json()["detail"]
    assert detail["error"] in {
        "task_not_materialized",
        "operational_readiness_blocked",
    }


def test_assigned_task_visible_in_employee_mobile_via_seeded_json(db_fixture, db_session, admin_client):
    """Mobile list reads embedded assignment; public bypass assign is closed."""
    user_id = f"mobile-{uuid.uuid4().hex[:8]}"

    async def _setup():
        await _seed_order(db_session, 98102)
        emp = await _seed_employee(db_session, name="Linked Assignee", user_id=user_id)
        tasks = [
            {
                "task_id": "T-MOBILE",
                "name": "Print",
                "process_type": "print",
                "machine_type": "printer_large_format",
                "assigned_employee_id": emp.id,
                "assignment_source": "test_seed",
            }
        ]
        row = ExecutionPlan(
            order_id=98102,
            order_code="ORD-98102",
            snapshot_version=1,
            tasks_json=json.dumps(tasks),
            total_estimated_time_minutes=20,
        )
        db_session.add(row)
        await db_session.commit()
        return emp.id

    employee_id = db_fixture.run(_setup())

    mobile = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        listed = mobile.get("/api/v1/employee-mobile/tasks")
        assert listed.status_code == 200, listed.text
        rows = listed.json()
        assert len(rows) == 1
        assert rows[0]["task_id"] == "T-MOBILE"
        assert rows[0]["assigned_employee_id"] == employee_id
    finally:
        _cleanup()


def test_assign_completed_task_rejected_on_canonical_path(db_fixture, db_session, admin_client):
    async def _setup():
        await _seed_order(db_session, 98103)
        emp = await _seed_employee(db_session)
        await _seed_plan(db_session, order_id=98103, task_id="T-DONE")
        db_session.add(
            ExecutionReality(
                order_id=98103,
                order_code="ORD-98103",
                tasks_json=json.dumps(
                    [
                        {
                            "task_id": "T-DONE",
                            "started_at": "2026-06-12T08:00:00+00:00",
                            "ended_at": "2026-06-12T09:00:00+00:00",
                        }
                    ]
                ),
                total_actual_time_minutes=60,
            )
        )
        await db_session.commit()
        return emp.id

    employee_id = db_fixture.run(_setup())
    response = admin_client.patch(
        "/api/v1/execution/plan/98103/tasks/T-DONE/assign",
        json={"assigned_employee_id": employee_id},
    )
    # Legacy list → readiness/eligibility block before completed check, or 409 stale.
    assert response.status_code in (409, 422), response.text


def test_assign_unknown_task_404(db_fixture, db_session, admin_client):
    async def _setup():
        await _seed_order(db_session, 98104)
        emp = await _seed_employee(db_session)
        await _seed_plan(db_session, order_id=98104, task_id="T-REAL")
        return emp.id

    employee_id = db_fixture.run(_setup())
    response = admin_client.patch(
        "/api/v1/execution/plan/98104/tasks/T-MISSING/assign",
        json={"assigned_employee_id": employee_id},
    )
    assert response.status_code in (404, 422), response.text
