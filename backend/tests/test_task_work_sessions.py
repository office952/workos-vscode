"""Tests for shared task work sessions in execution_reality.tasks_json."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.employees import Employees
from schemas.auth import UserResponse
from services.execution_reality_service import ExecutionRealityService, RealityInputError
from services.order_production_blueprint_service import get_order_production_blueprint
from services.task_work_session_service import (
    aggregate_task_work_metrics,
    derive_task_status_for_employee,
    derive_task_status_from_sessions,
    sessions_for_task,
)

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_employee,
    _seed_plan_with_assigned_task,
    _user,
)


def _mobile_user(user_id: str) -> UserResponse:
    return _user(user_id, "employee_mobile")


@pytest.fixture
def session_fixture(db_fixture, db_session):
    order_id = 8100 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        primary = await _seed_employee(db_session, user_id=f"primary-{uuid.uuid4().hex[:6]}")
        helper = await _seed_employee(db_session, user_id=f"helper-{uuid.uuid4().hex[:6]}")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=primary.id,
            task_id="T-WS-1",
        )
        return {"order_id": order_id, "primary_id": primary.id, "helper_id": helper.id}

    ids = db_fixture.run(_setup())
    yield {**ids, "db_fixture": db_fixture, "db_session": db_session}
    _cleanup_overrides()


def test_start_task_creates_session_with_session_id(session_fixture):
    db_session = session_fixture["db_session"]
    order_id = session_fixture["order_id"]
    employee_id = session_fixture["primary_id"]

    async def _run():
        svc = ExecutionRealityService(db_session)
        now = datetime.now(timezone.utc).isoformat()
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-WS-1",
            now,
            initial_fields={
                "employee_id": employee_id,
                "employee_name": "Primary Worker",
                "source": "employee_mobile",
            },
        )
        row = await svc.get_by_order(order_id)
        tasks = json.loads(row.tasks_json)
        assert len(tasks) == 1
        assert tasks[0]["session_id"]
        assert tasks[0]["employee_id"] == employee_id
        assert tasks[0]["started_at"] == now
        assert tasks[0]["ended_at"] is None

    session_fixture["db_fixture"].run(_run())


def test_duplicate_start_same_employee_rejected(session_fixture):
    db_session = session_fixture["db_session"]
    order_id = session_fixture["order_id"]
    employee_id = session_fixture["primary_id"]

    async def _run():
        svc = ExecutionRealityService(db_session)
        now = datetime.now(timezone.utc).isoformat()
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-WS-1",
            now,
            initial_fields={"employee_id": employee_id, "employee_name": "Primary Worker"},
        )
        with pytest.raises(RealityInputError) as exc:
            await svc.start_task(
                order_id,
                f"ORD-{order_id:04d}",
                "T-WS-1",
                now,
                initial_fields={"employee_id": employee_id, "employee_name": "Primary Worker"},
            )
        assert exc.value.code == "task_already_started"

    session_fixture["db_fixture"].run(_run())


def test_multiple_sessions_same_task_different_employees(session_fixture):
    db_session = session_fixture["db_session"]
    order_id = session_fixture["order_id"]
    primary_id = session_fixture["primary_id"]
    helper_id = session_fixture["helper_id"]

    async def _run():
        svc = ExecutionRealityService(db_session)
        t1 = datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc).isoformat()
        t2 = datetime(2026, 6, 14, 10, 5, tzinfo=timezone.utc).isoformat()
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-WS-1",
            t1,
            initial_fields={
                "employee_id": primary_id,
                "employee_name": "Primary Worker",
                "role": "primary",
            },
        )
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-WS-1",
            t2,
            initial_fields={
                "employee_id": helper_id,
                "employee_name": "Helper Worker",
                "role": "helper",
                "session_type": "assist",
            },
        )
        row = await svc.get_by_order(order_id)
        sessions = sessions_for_task(json.loads(row.tasks_json), "T-WS-1")
        assert len(sessions) == 2
        metrics = aggregate_task_work_metrics(sessions)
        assert len(metrics["active_workers"]) == 2
        assert metrics["participants_count"] == 2
        assert derive_task_status_from_sessions(sessions) == "in_progress"

    session_fixture["db_fixture"].run(_run())


def test_complete_closes_active_session_with_duration(session_fixture):
    db_session = session_fixture["db_session"]
    order_id = session_fixture["order_id"]
    employee_id = session_fixture["primary_id"]

    async def _run():
        svc = ExecutionRealityService(db_session)
        start = datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc).isoformat()
        end = datetime(2026, 6, 14, 10, 45, tzinfo=timezone.utc).isoformat()
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-WS-1",
            start,
            initial_fields={"employee_id": employee_id, "employee_name": "Primary Worker"},
        )
        await svc.end_task(
            order_id,
            "T-WS-1",
            end,
            employee_id=employee_id,
            completion_fields={"completed_by_employee_id": employee_id},
        )
        row = await svc.get_by_order(order_id)
        session = json.loads(row.tasks_json)[0]
        assert session["ended_at"] == end
        assert session["duration_minutes"] == 45
        assert session["completed_by_employee_id"] == employee_id
        assert derive_task_status_from_sessions([session]) == "done"

    session_fixture["db_fixture"].run(_run())


def test_operator_blueprint_exposes_work_session_metrics(session_fixture):
    db_session = session_fixture["db_session"]
    order_id = session_fixture["order_id"]
    primary_id = session_fixture["primary_id"]
    helper_id = session_fixture["helper_id"]

    async def _run():
        svc = ExecutionRealityService(db_session)
        start_primary = datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc).isoformat()
        end_primary = datetime(2026, 6, 14, 9, 30, tzinfo=timezone.utc).isoformat()
        start_helper = datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc).isoformat()
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-WS-1",
            start_primary,
            initial_fields={"employee_id": primary_id, "employee_name": "Primary Worker"},
        )
        await svc.end_task(
            order_id,
            "T-WS-1",
            end_primary,
            employee_id=primary_id,
            completion_fields={"completed_by_employee_id": primary_id},
        )
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-WS-1",
            start_helper,
            initial_fields={
                "employee_id": helper_id,
                "employee_name": "Helper Worker",
                "role": "helper",
                "session_type": "assist",
            },
        )
        blueprint = await get_order_production_blueprint(db_session, order_id)
        task = next(item for item in blueprint["tasks"] if item["task_id"] == "T-WS-1")
        assert task["work_sessions_count"] == 2
        assert task["participants_count"] == 2
        assert task["total_logged_minutes"] == 30
        assert len(task["active_workers"]) == 1

    session_fixture["db_fixture"].run(_run())


def test_partial_complete_does_not_mark_global_done_while_helper_active(session_fixture):
    db_session = session_fixture["db_session"]
    order_id = session_fixture["order_id"]
    primary_id = session_fixture["primary_id"]
    helper_id = session_fixture["helper_id"]

    async def _run():
        svc = ExecutionRealityService(db_session)
        start_primary = datetime(2026, 6, 14, 9, 0, tzinfo=timezone.utc).isoformat()
        start_helper = datetime(2026, 6, 14, 9, 10, tzinfo=timezone.utc).isoformat()
        end_primary = datetime(2026, 6, 14, 9, 30, tzinfo=timezone.utc).isoformat()
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-WS-1",
            start_primary,
            initial_fields={"employee_id": primary_id, "employee_name": "Primary Worker"},
        )
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-WS-1",
            start_helper,
            initial_fields={
                "employee_id": helper_id,
                "employee_name": "Helper Worker",
                "role": "helper",
            },
        )
        await svc.end_task(
            order_id,
            "T-WS-1",
            end_primary,
            employee_id=primary_id,
            completion_fields={"completed_by_employee_id": primary_id},
        )
        row = await svc.get_by_order(order_id)
        sessions = sessions_for_task(json.loads(row.tasks_json), "T-WS-1")
        assert derive_task_status_from_sessions(sessions) == "in_progress"
        assert derive_task_status_for_employee(sessions, primary_id) == "done"
        assert derive_task_status_for_employee(sessions, helper_id) == "in_progress"

    session_fixture["db_fixture"].run(_run())


def test_employee_mobile_start_flow_still_works(session_fixture):
    order_id = session_fixture["order_id"]
    user_id = f"mobile-ws-{uuid.uuid4().hex[:6]}"

    async def _link_user():
        emp = await _seed_employee(
            session_fixture["db_session"],
            user_id=user_id,
            name="Mobile WS Worker",
        )
        plan = (
            await session_fixture["db_session"].execute(
                __import__("sqlalchemy").select(ExecutionPlan).where(
                    ExecutionPlan.order_id == order_id
                )
            )
        ).scalar_one()
        tasks = json.loads(plan.tasks_json)
        tasks[0]["assigned_employee_id"] = emp.id
        plan.tasks_json = json.dumps(tasks)
        await session_fixture["db_session"].commit()
        return emp.id

    employee_id = session_fixture["db_fixture"].run(_link_user())
    client = _client_for(session_fixture["db_fixture"], _mobile_user(user_id))
    response = client.patch(
        f"/api/v1/employee-mobile/tasks/T-WS-1/start",
        json={"order_id": order_id},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "start"


def test_employee_blueprint_does_not_expose_other_employee_names(session_fixture):
    order_id = session_fixture["order_id"]
    user_id = f"mobile-bp-{uuid.uuid4().hex[:6]}"

    async def _seed():
        emp = await _seed_employee(
            session_fixture["db_session"],
            user_id=user_id,
            name="Sandu Viewer",
        )
        helper_id = session_fixture["helper_id"]
        db_session = session_fixture["db_session"]
        plan = (
            await db_session.execute(
                __import__("sqlalchemy").select(ExecutionPlan).where(
                    ExecutionPlan.order_id == order_id
                )
            )
        ).scalar_one()
        tasks = json.loads(plan.tasks_json)
        tasks[0]["assigned_employee_id"] = emp.id
        plan.tasks_json = json.dumps(tasks)
        svc = ExecutionRealityService(db_session)
        start = datetime(2026, 6, 14, 11, 0, tzinfo=timezone.utc).isoformat()
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-WS-1",
            start,
            initial_fields={"employee_id": emp.id, "employee_name": "Sandu Viewer"},
        )
        await svc.start_task(
            order_id,
            f"ORD-{order_id:04d}",
            "T-WS-1",
            datetime(2026, 6, 14, 11, 5, tzinfo=timezone.utc).isoformat(),
            initial_fields={
                "employee_id": helper_id,
                "employee_name": "Helper Worker",
                "role": "helper",
            },
        )
        await db_session.commit()

    session_fixture["db_fixture"].run(_seed())
    client = _client_for(session_fixture["db_fixture"], _mobile_user(user_id))
    response = client.get(f"/api/v1/employee-mobile/orders/{order_id}/my-blueprint")
    assert response.status_code == 200
    payload = json.dumps(response.json())
    assert "Helper Worker" not in payload
    task = next(item for item in response.json()["tasks"] if item["task_id"] == "T-WS-1")
    assert task["active_helper_count"] == 1
