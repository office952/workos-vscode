"""Tests for manual execution task instructions on execution_plan.tasks_json."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from schemas.auth import UserResponse
from sqlalchemy import select

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from services.execution_task_instructions_service import update_plan_task_instructions


def _user(user_id: str, role: str) -> UserResponse:
    return UserResponse(
        id=user_id,
        email=f"{user_id}@workos.test",
        name=f"User {user_id}",
        role=role,
        last_login=None,
    )


async def _seed_plan(db_session, *, order_id: int, task_id: str = "T-INST") -> None:
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-{order_id:04d}",
            snapshot_version=1,
            tasks_json=json.dumps(
                [
                    {
                        "task_id": task_id,
                        "name": "Cadru metalic",
                        "process_type": "metal_frame",
                        "estimated_time_minutes": 45,
                    }
                ]
            ),
            total_estimated_time_minutes=45,
        )
    )
    await db_session.commit()


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


@pytest.mark.asyncio
async def test_update_plan_task_instructions_trims_and_persists(db_session):
    order_id = 5001
    await _seed_plan(db_session, order_id=order_id)
    result = await update_plan_task_instructions(
        db_session,
        order_id=order_id,
        task_id="T-INST",
        instructions="  Taie țevi la 3000 mm.  ",
    )
    assert result["instructions"] == "Taie țevi la 3000 mm."

    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one()
    tasks = json.loads(plan.tasks_json)
    assert tasks[0]["instructions"] == "Taie țevi la 3000 mm."


@pytest.mark.asyncio
async def test_empty_instructions_removes_field(db_session):
    order_id = 5002
    await _seed_plan(db_session, order_id=order_id)
    await update_plan_task_instructions(
        db_session,
        order_id=order_id,
        task_id="T-INST",
        instructions="Temporar",
    )
    await update_plan_task_instructions(
        db_session,
        order_id=order_id,
        task_id="T-INST",
        instructions="",
    )
    plan = (
        await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
    ).scalar_one()
    tasks = json.loads(plan.tasks_json)
    assert "instructions" not in tasks[0]


def test_admin_can_save_instructions_via_api(db_fixture, db_session):
    order_id = 5101

    async def _setup():
        await _seed_plan(db_session, order_id=order_id)

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("admin-inst", "admin"))
    try:
        resp = client.patch(
            f"/api/v1/execution/plan/{order_id}/tasks/T-INST/instructions",
            json={"instructions": "Vezi schița atașată."},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["instructions"] == "Vezi schița atașată."
    finally:
        _cleanup()


def test_employee_mobile_cannot_save_instructions(db_fixture, db_session):
    order_id = 5102
    user_id = f"mobile-{uuid.uuid4().hex[:8]}"

    async def _setup():
        emp = Employees(name="Mobile", status="active", employee_type="productive", user_id=user_id)
        db_session.add(emp)
        await db_session.flush()
        await _seed_plan(db_session, order_id=order_id)

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        resp = client.patch(
            f"/api/v1/execution/plan/{order_id}/tasks/T-INST/instructions",
            json={"instructions": "Nu ar trebui permis."},
        )
        assert resp.status_code == 403, resp.text
    finally:
        _cleanup()


def test_save_instructions_does_not_touch_reality(db_fixture, db_session):
    order_id = 5103

    async def _setup():
        await _seed_plan(db_session, order_id=order_id)
        db_session.add(
            ExecutionReality(
                order_id=order_id,
                order_code=f"ORD-{order_id:04d}",
                tasks_json=json.dumps(
                    [{"task_id": "T-INST", "started_at": "2026-06-12T08:00:00+00:00"}]
                ),
                total_actual_time_minutes=0.0,
            )
        )
        await db_session.commit()

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("operator-inst", "operator"))
    try:
        resp = client.patch(
            f"/api/v1/execution/plan/{order_id}/tasks/T-INST/instructions",
            json={"instructions": "Manual note"},
        )
        assert resp.status_code == 200, resp.text

        async def _check():
            reality = (
                await db_session.execute(
                    select(ExecutionReality).where(ExecutionReality.order_id == order_id)
                )
            ).scalar_one()
            tasks = json.loads(reality.tasks_json)
            assert "instructions" not in tasks[0]
            assert tasks[0]["started_at"]

        db_fixture.run(_check())
    finally:
        _cleanup()
