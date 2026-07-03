"""Production readiness start gates — unified backend enforcement."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from schemas.auth import UserResponse
from services.task_dependency_rules_service import apply_task_dependency_rules_to_plan_tasks
from services.task_readiness_service import (
    READINESS_WAITING_FILE,
    READINESS_WAITING_TEMPLATE_DECISION,
    evaluate_all_task_readiness,
)
from services.volumetric_return_task_taxonomy_service import apply_volumetric_return_taxonomy_to_plan_tasks

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_employee,
    _user,
)
from tests.test_task_readiness_dependencies import _build_volumetric_tasks


def test_cnc_tasks_depend_on_vector_prep():
    tasks = _build_volumetric_tasks(sandu_id=4)
    by_id = {t["task_id"]: t for t in tasks}
    assert "T-001" in by_id["T-002"]["depends_on_task_ids"]
    assert "T-001" in by_id["T-005"]["depends_on_task_ids"]
    assert "T-001" in by_id["T-008"]["depends_on_task_ids"]


def test_face_cnc_waiting_file_when_vector_prep_not_done():
    tasks = _build_volumetric_tasks(sandu_id=4)
    readiness = evaluate_all_task_readiness(tasks, [], employee_id=4)
    assert readiness["T-002"]["readiness_status"] == READINESS_WAITING_FILE
    assert readiness["T-002"]["is_startable"] is False


def test_mounting_template_paper_blocks_cnc_template_task():
    tasks = _build_volumetric_tasks(sandu_id=4)
    reality = [
        {
            "task_id": "T-001",
            "employee_id": 9,
            "started_at": "2026-06-12T08:00:00+00:00",
            "ended_at": "2026-06-12T08:30:00+00:00",
            "completed_by_employee_id": 9,
        }
    ]
    quote_input = {
        "mounting_template_enabled": True,
        "mounting_template_material_type": "paper",
        "mounting_template_area_m2": 2.5,
    }
    readiness = evaluate_all_task_readiness(
        tasks,
        reality,
        employee_id=4,
        quote_input=quote_input,
    )
    assert readiness["T-008"]["readiness_status"] == READINESS_WAITING_TEMPLATE_DECISION
    assert readiness["T-008"]["is_startable"] is False


def test_mounting_template_missing_type_waiting_decision():
    tasks = _build_volumetric_tasks(sandu_id=4)
    reality = [
        {
            "task_id": "T-001",
            "employee_id": 9,
            "started_at": "2026-06-12T08:00:00+00:00",
            "ended_at": "2026-06-12T08:30:00+00:00",
        }
    ]
    readiness = evaluate_all_task_readiness(
        tasks,
        reality,
        employee_id=4,
        quote_input={"mounting_template_enabled": False},
    )
    assert readiness["T-008"]["readiness_status"] == READINESS_WAITING_TEMPLATE_DECISION


@pytest.fixture
def start_gate_fixture(db_fixture, db_session):
    order_id = 7200 + int(uuid.uuid4().hex[:4], 16) % 1000
    user_id = f"sg-{uuid.uuid4().hex[:8]}"

    async def _setup():
        worker = await _seed_employee(db_session, user_id=user_id, name="Gate Worker")
        tasks = _build_volumetric_tasks(sandu_id=worker.id)
        quote = Quotes(
            code=f"QT-{order_id}",
            intake_code="IR-GATE",
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
                snapshot_line_items=json.dumps(
                    {
                        "quote_input": {
                            "mounting_template_enabled": True,
                            "mounting_template_material_type": "paper",
                            "mounting_template_area_m2": 2.0,
                        }
                    }
                ),
            )
        )
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=f"ORD-{order_id}",
                snapshot_version=1,
                tasks_json=json.dumps(tasks),
                total_estimated_time_minutes=300,
            )
        )
        await db_session.commit()
        return worker.id

    worker_id = db_fixture.run(_setup())
    yield {
        "order_id": order_id,
        "worker_id": worker_id,
        "user_id": user_id,
        "db_fixture": db_fixture,
    }
    _cleanup_overrides()


def test_employee_mobile_start_blocked_cnc_without_vector_prep(start_gate_fixture):
    client = _client_for(
        start_gate_fixture["db_fixture"],
        _user(start_gate_fixture["user_id"], "employee_mobile"),
    )
    response = client.patch(
        "/api/v1/employee-mobile/tasks/T-008/start",
        json={"order_id": start_gate_fixture["order_id"]},
    )
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail.get("code") == "task_not_ready"
    assert detail.get("readiness_status") in {
        READINESS_WAITING_FILE,
        READINESS_WAITING_TEMPLATE_DECISION,
    }


def test_operator_start_blocked_without_readiness(start_gate_fixture):
    client = _client_for(
        start_gate_fixture["db_fixture"],
        _user(f"op-{uuid.uuid4().hex[:6]}", "operator"),
    )
    response = client.post(
        "/api/v1/operator/task-action",
        json={
            "order_id": start_gate_fixture["order_id"],
            "task_id": "T-002",
            "action": "start",
            "employee_id": start_gate_fixture["worker_id"],
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "task_not_ready"


def test_execution_reality_start_blocked_without_readiness(start_gate_fixture):
    async def _override_get_db():
        async with start_gate_fixture["db_fixture"].session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="admin-gate",
            email="admin-gate@test",
            name="Admin Gate",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    client = TestClient(app, raise_server_exceptions=False)
    try:
        response = client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": start_gate_fixture["order_id"],
                "task_id": "T-002",
                "timestamp": "2026-06-14T10:00:00+00:00",
            },
        )
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "task_not_ready"
    finally:
        app.dependency_overrides.clear()


def test_operator_override_allows_start_with_reason(start_gate_fixture):
    client = _client_for(
        start_gate_fixture["db_fixture"],
        _user(f"adm-{uuid.uuid4().hex[:6]}", "admin"),
    )
    response = client.post(
        "/api/v1/operator/task-action",
        json={
            "order_id": start_gate_fixture["order_id"],
            "task_id": "T-002",
            "action": "start",
            "employee_id": start_gate_fixture["worker_id"],
            "override_readiness": True,
            "override_reason": "Urgență producție — vector în lucru paralel",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("readiness_override") is True
