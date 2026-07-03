"""Tests for execution plan prepared_by and clarification target routing."""

from __future__ import annotations

import json
import uuid

from fastapi.testclient import TestClient
from models.auth import User
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.task_clarification_request import TaskClarificationRequest
from schemas.auth import UserResponse
from sqlalchemy import select

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_employee,
    _user,
)


def _admin_user(user_id: str = "admin-prepared-by") -> UserResponse:
    return UserResponse(
        id=user_id,
        email=f"{user_id}@workos.test",
        name="Plan Preparer",
        role="admin",
        last_login=None,
    )


async def _seed_plan_with_prepared_by(
    db_session,
    *,
    order_id: int,
    prepared_by_user_id: str | None,
    assigned_employee_id: int,
    task_id: str = "T-CL",
) -> None:
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-{order_id:04d}",
            snapshot_version=1,
            tasks_json=json.dumps(
                [
                    {
                        "task_id": task_id,
                        "name": "Task",
                        "process_type": "assembly",
                        "estimated_time_minutes": 30,
                        "assigned_employee_id": assigned_employee_id,
                    }
                ]
            ),
            total_estimated_time_minutes=30,
            prepared_by_user_id=prepared_by_user_id,
        )
    )
    await db_session.commit()


def test_clarification_gets_target_from_plan_prepared_by(db_fixture, db_session):
    order_id = 6001 + int(uuid.uuid4().hex[:4], 16) % 100
    preparer_id = f"prep-{uuid.uuid4().hex[:8]}"
    mobile_id = f"mobile-{uuid.uuid4().hex[:8]}"

    async def _setup():
        db_session.add(
            User(
                id=preparer_id,
                email=f"{preparer_id}@workos.test",
                name="Responsabil Pregătire",
                role="operator",
            )
        )
        emp = await _seed_employee(db_session, user_id=mobile_id, name="Sandu Worker")
        await _seed_plan_with_prepared_by(
            db_session,
            order_id=order_id,
            prepared_by_user_id=preparer_id,
            assigned_employee_id=emp.id,
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(mobile_id, "employee_mobile"))
    try:
        resp = client.post(
            "/api/v1/employee-mobile/tasks/T-CL/clarification-requests",
            json={"order_id": order_id, "message": "Lipsește detaliu montaj."},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["target_user_id"] == preparer_id
        assert body["target_user_name"] == "Responsabil Pregătire"
        assert body["routed_to_responsible"] is True
    finally:
        _cleanup_overrides()


def test_clarification_without_prepared_by_has_null_target(db_fixture, db_session):
    order_id = 6101 + int(uuid.uuid4().hex[:4], 16) % 100
    mobile_id = f"mobile-{uuid.uuid4().hex[:8]}"

    async def _setup():
        emp = await _seed_employee(db_session, user_id=mobile_id, name="Worker")
        await _seed_plan_with_prepared_by(
            db_session,
            order_id=order_id,
            prepared_by_user_id=None,
            assigned_employee_id=emp.id,
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(mobile_id, "employee_mobile"))
    try:
        resp = client.post(
            "/api/v1/employee-mobile/tasks/T-CL/clarification-requests",
            json={"order_id": order_id, "message": "Unde este schița?"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body.get("target_user_id") in (None, "")
        assert body["routed_to_responsible"] is False
    finally:
        _cleanup_overrides()


def test_operator_list_includes_target_user(db_fixture, db_session):
    order_id = 6201 + int(uuid.uuid4().hex[:4], 16) % 100
    preparer_id = "operator-target-user"

    async def _setup():
        db_session.add(
            User(
                id=preparer_id,
                email="operator-target@workos.test",
                name="Operator Target",
                role="operator",
            )
        )
        emp = Employees(name="Req Worker", status="active", employee_type="productive", user_id="req-worker")
        db_session.add(emp)
        await db_session.flush()
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=f"ORD-{order_id:04d}",
                snapshot_version=1,
                tasks_json=json.dumps([{"task_id": "T-1", "estimated_time_minutes": 10}]),
                total_estimated_time_minutes=10,
                prepared_by_user_id=preparer_id,
            )
        )
        db_session.add(
            TaskClarificationRequest(
                order_id=order_id,
                task_id="T-1",
                employee_id=emp.id,
                message="Need info",
                status="open",
                target_user_id=preparer_id,
            )
        )
        await db_session.commit()

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user("operator-list-user", "operator"))
    try:
        resp = client.get("/api/v1/operator/clarification-requests?status=open")
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        match = next((r for r in rows if r["order_id"] == order_id), None)
        assert match is not None
        assert match["target_user_id"] == preparer_id
        assert match["target_user_name"] == "Operator Target"
    finally:
        _cleanup_overrides()


def test_plan_from_order_sets_prepared_by_user_id(db_fixture, db_session):
    from tests.test_production_document_handoff import _admin_user as handoff_admin
    from tests.test_execution_flow import _complete_snapshot_dict
    from models.orders import Orders
    from models.quotes import Quotes

    order_id = 6301 + int(uuid.uuid4().hex[:4], 16) % 100
    preparer = handoff_admin()

    async def _setup():
        quote = Quotes(
            code=f"QT-{order_id}",
            intake_code="IR-PREP",
            client_name="Client",
            status="accepted",
            version=1,
        )
        db_session.add(quote)
        await db_session.flush()
        db_session.add(
            Orders(
                id=order_id,
                code=f"ORD-{order_id}",
                quote_id=quote.id,
                quote_code=quote.code,
                client_name="Client",
                status="locked",
                snapshot_version=1,
                snapshot_line_items=json.dumps(_complete_snapshot_dict()),
            )
        )
        await db_session.commit()

    db_fixture.run(_setup())

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return preparer

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    client = TestClient(app, raise_server_exceptions=False)
    try:
        resp = client.post(f"/api/v1/execution/plan/from-order/{order_id}")
        assert resp.status_code in {200, 201}, resp.text
        assert resp.json().get("prepared_by_user_id") == preparer.id

        async def _check():
            plan = (
                await db_session.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
            ).scalar_one()
            assert plan.prepared_by_user_id == preparer.id

        db_fixture.run(_check())
    finally:
        app.dependency_overrides.clear()
