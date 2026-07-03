"""Tests for production task clarification requests."""

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
from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_employee,
    _seed_plan_with_assigned_task,
    _seed_reality_task,
    _user,
)


@pytest.fixture
def mobile_user(db_fixture, db_session):
    user_id = f"mobile-clarify-{uuid.uuid4().hex[:8]}"
    order_id = 5000 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Clarify Worker")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=emp.id,
            task_id="T-CL",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    yield client, user_id, order_id
    _cleanup_overrides()


@pytest.fixture
def operator_client(db_fixture):
    user_id = f"operator-clarify-{uuid.uuid4().hex[:8]}"
    yield _client_for(db_fixture, _user(user_id, "operator")), user_id
    _cleanup_overrides()


def test_empty_message_is_rejected(mobile_user):
    client, _, order_id = mobile_user
    response = client.post(
        "/api/v1/employee-mobile/tasks/T-CL/clarification-requests",
        json={"order_id": order_id, "message": "   "},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "message_required"


def test_employee_can_create_clarification_for_own_task(mobile_user):
    client, _, order_id = mobile_user
    response = client.post(
        "/api/v1/employee-mobile/tasks/T-CL/clarification-requests",
        json={"order_id": order_id, "message": "Nu găsesc cota pentru cadru."},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "open"
    assert body["message"] == "Nu găsesc cota pentru cadru."
    assert body["task_id"] == "T-CL"


def test_create_does_not_change_task_status(mobile_user, db_fixture, db_session):
    client, user_id, order_id = mobile_user

    async def _setup():
        emp = (
            await db_session.execute(select(Employees).where(Employees.user_id == user_id))
        ).scalar_one()

        await _seed_reality_task(
            db_session,
            order_id=order_id,
            task_id="T-CL",
            employee_id=emp.id,
            started_at="2026-06-14T10:00:00+00:00",
        )

    db_fixture.run(_setup())

    before = client.get("/api/v1/employee-mobile/tasks")
    assert before.json()[0]["status"] == "in_progress"

    create = client.post(
        "/api/v1/employee-mobile/tasks/T-CL/clarification-requests",
        json={"order_id": order_id, "message": "Schița nu este clară."},
    )
    assert create.status_code == 200, create.text

    after = client.get("/api/v1/employee-mobile/tasks")
    assert after.json()[0]["status"] == "in_progress"
    assert after.json()[0]["clarification_request"]["status"] == "open"


def test_employee_cannot_create_for_unassigned_task(db_fixture, db_session):
    owner_id = f"owner-{uuid.uuid4().hex[:8]}"
    other_id = f"other-{uuid.uuid4().hex[:8]}"

    async def _setup():
        owner = await _seed_employee(db_session, user_id=owner_id, name="Owner")
        await _seed_employee(db_session, user_id=other_id, name="Other")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=601,
            assigned_employee_id=owner.id,
            task_id="T-OWN",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(other_id, "employee_mobile"))
    try:
        response = client.post(
            "/api/v1/employee-mobile/tasks/T-OWN/clarification-requests",
            json={"order_id": 601, "message": "Nu am acces."},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "task_not_assigned_to_employee"
    finally:
        _cleanup_overrides()


def test_open_duplicate_is_rejected(mobile_user):
    client, _, order_id = mobile_user
    payload = {"order_id": order_id, "message": "Lipsește documentul pentru montaj."}
    first = client.post(
        "/api/v1/employee-mobile/tasks/T-CL/clarification-requests",
        json=payload,
    )
    assert first.status_code == 200, first.text
    second = client.post(
        "/api/v1/employee-mobile/tasks/T-CL/clarification-requests",
        json={"order_id": order_id, "message": "Alt mesaj."},
    )
    assert second.status_code == 409
    assert second.json()["detail"]["error"] == "open_clarification_exists"


def test_operator_can_list_and_resolve(db_fixture, db_session):
    mobile_user_id = f"mobile-op-{uuid.uuid4().hex[:8]}"
    operator_user_id = f"operator-op-{uuid.uuid4().hex[:8]}"
    order_id = 6000 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        emp = await _seed_employee(db_session, user_id=mobile_user_id, name="Mobile OP")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=emp.id,
            task_id="T-CL",
        )

    db_fixture.run(_setup())
    mobile = _client_for(db_fixture, _user(mobile_user_id, "employee_mobile"))
    create = mobile.post(
        "/api/v1/employee-mobile/tasks/T-CL/clarification-requests",
        json={"order_id": order_id, "message": "Confirmăm vopsirea înainte de montaj?"},
    )
    assert create.status_code == 200, create.text
    request_id = create.json()["id"]
    _cleanup_overrides()

    operator = _client_for(db_fixture, _user(operator_user_id, "operator"))
    try:
        listed = operator.get("/api/v1/operator/clarification-requests?status=open")
        assert listed.status_code == 200, listed.text
        ids = [row["id"] for row in listed.json()]
        assert request_id in ids

        resolved = operator.patch(
            f"/api/v1/operator/clarification-requests/{request_id}/resolve",
            json={},
        )
        assert resolved.status_code == 200, resolved.text
        assert resolved.json()["status"] == "resolved"
    finally:
        _cleanup_overrides()


def test_employee_mobile_cannot_resolve(mobile_user):
    client, _, order_id = mobile_user
    create = client.post(
        "/api/v1/employee-mobile/tasks/T-CL/clarification-requests",
        json={"order_id": order_id, "message": "Întrebare simplă."},
    )
    assert create.status_code == 200, create.text
    request_id = create.json()["id"]

    resolve = client.patch(
        f"/api/v1/operator/clarification-requests/{request_id}/resolve",
        json={},
    )
    assert resolve.status_code == 403
