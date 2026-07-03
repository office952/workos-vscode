"""Tests for operator/admin production blueprint endpoint."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.task_clarification_request import TaskClarificationRequest
from schemas.auth import UserResponse
from services.volumetric_return_task_taxonomy_service import (
    BONDING_DISPLAY_NAME,
    BONDING_MACHINE_TYPE,
    BONDING_PROCESS_TYPE,
    RETURN_BONDING_PROCESS_ID,
    apply_volumetric_return_taxonomy_to_task,
)

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
def blueprint_fixture(db_fixture, db_session):
    order_id = 7000 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        worker = await _seed_employee(db_session, user_id=None, name="Blueprint Worker")
        tasks = [
            {
                "task_id": "T-UNASSIGNED",
                "name": "Neatribuit",
                "process_type": "print",
                "machine_type": "PRINTER",
                "estimated_time_minutes": 10,
            },
            {
                "task_id": "T-TODO",
                "name": "De făcut",
                "process_type": "cnc_routing",
                "machine_type": "CNC",
                "estimated_time_minutes": 20,
                "assigned_employee_id": worker.id,
                "instructions": "Urmați schița.",
            },
            apply_volumetric_return_taxonomy_to_task(
                {
                    "task_id": "T-004",
                    "process_id": RETURN_BONDING_PROCESS_ID,
                    "process_type": "welding",
                    "machine_type": "RETURN_PROFILE_FACE_BONDING",
                    "display_name": "Lipire cant pe față",
                    "assigned_employee_id": worker.id,
                    "instructions": "Lipește canturile.",
                    "documents": [
                        {
                            "id": "doc-1",
                            "name": "Schiță.svg",
                            "type": "svg",
                            "source": "intake_work_file",
                        }
                    ],
                },
                set_owner_instructions=True,
            ),
            {
                "task_id": "T-INPROG",
                "name": "În lucru",
                "process_type": "assembly",
                "machine_type": "ASSEMBLY",
                "estimated_time_minutes": 15,
                "assigned_employee_id": worker.id,
            },
            {
                "task_id": "T-BLOCKED",
                "name": "Blocat",
                "process_type": "paint",
                "machine_type": "PAINT",
                "estimated_time_minutes": 12,
                "assigned_employee_id": worker.id,
            },
            {
                "task_id": "T-DONE",
                "name": "Finalizat",
                "process_type": "qc",
                "machine_type": "QC",
                "estimated_time_minutes": 5,
                "assigned_employee_id": worker.id,
            },
        ]
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=f"ORD-BP-{order_id}",
                snapshot_version=1,
                tasks_json=json.dumps(tasks),
                total_estimated_time_minutes=72,
            )
        )
        db_session.add(
            ExecutionReality(
                order_id=order_id,
                order_code=f"ORD-BP-{order_id}",
                tasks_json=json.dumps(
                    [
                        {
                            "task_id": "T-INPROG",
                            "employee_id": worker.id,
                            "employee_name": "Blueprint Worker",
                            "started_at": "2026-06-14T10:00:00+00:00",
                        },
                        {
                            "task_id": "T-BLOCKED",
                            "employee_id": worker.id,
                            "employee_name": "Blueprint Worker",
                            "started_at": "2026-06-14T09:00:00+00:00",
                            "blocked_at": "2026-06-14T09:30:00+00:00",
                            "block_reason": "Lipsește material",
                        },
                        {
                            "task_id": "T-DONE",
                            "employee_id": worker.id,
                            "employee_name": "Blueprint Worker",
                            "started_at": "2026-06-14T08:00:00+00:00",
                            "ended_at": "2026-06-14T08:30:00+00:00",
                        },
                    ]
                ),
                total_actual_time_minutes=30,
            )
        )
        db_session.add(
            TaskClarificationRequest(
                order_id=order_id,
                task_id="T-TODO",
                employee_id=worker.id,
                message="Confirmă detaliile?",
                status="open",
            )
        )
        await db_session.commit()
        return worker.id

    worker_id = db_fixture.run(_setup())
    yield {"order_id": order_id, "worker_id": worker_id, "db_fixture": db_fixture}
    _cleanup_overrides()


def _admin_client(db_fixture):
    return _client_for(db_fixture, _user(f"admin-bp-{uuid.uuid4().hex[:6]}", "admin"))


def _operator_client(db_fixture):
    return _client_for(db_fixture, _user(f"op-bp-{uuid.uuid4().hex[:6]}", "operator"))


def _mobile_client(db_fixture):
    return _client_for(db_fixture, _user(f"mobile-bp-{uuid.uuid4().hex[:6]}", "employee_mobile"))


def test_operator_can_access_blueprint(blueprint_fixture):
    order_id = blueprint_fixture["order_id"]
    client = _operator_client(blueprint_fixture["db_fixture"])
    response = client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint")
    assert response.status_code == 200
    body = response.json()
    assert body["order_id"] == order_id
    assert body["summary"]["total_tasks"] >= 5


def test_employee_mobile_cannot_access_blueprint(blueprint_fixture):
    order_id = blueprint_fixture["order_id"]
    client = _mobile_client(blueprint_fixture["db_fixture"])
    response = client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint")
    assert response.status_code == 403


def test_summary_counts(blueprint_fixture):
    order_id = blueprint_fixture["order_id"]
    client = _admin_client(blueprint_fixture["db_fixture"])
    body = client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint").json()
    summary = body["summary"]
    assert summary["done"] >= 1
    assert summary["in_progress"] >= 1
    assert summary["blocked"] >= 1
    assert summary["todo"] >= 1
    assert summary["unassigned"] >= 1
    assert summary["progress_percent"] == round(
        (summary["done"] / summary["total_tasks"]) * 100
    )


def test_todo_task_status(blueprint_fixture):
    order_id = blueprint_fixture["order_id"]
    client = _admin_client(blueprint_fixture["db_fixture"])
    tasks = client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint").json()["tasks"]
    todo = next(t for t in tasks if t["task_id"] == "T-TODO")
    assert todo["status"] == "todo"
    assert todo["status_display"] == "De făcut"
    assert todo["assigned_employee_id"] == blueprint_fixture["worker_id"]


def test_in_progress_active_worker(blueprint_fixture):
    order_id = blueprint_fixture["order_id"]
    client = _admin_client(blueprint_fixture["db_fixture"])
    body = client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint").json()
    task = next(t for t in body["tasks"] if t["task_id"] == "T-INPROG")
    assert task["status"] == "in_progress"
    assert task["status_display"] == "În lucru"
    assert task["active_worker_id"] == blueprint_fixture["worker_id"]
    assert task["active_worker_name"] == "Blueprint Worker"
    assert len(body["active_workers"]) >= 1


def test_blocked_includes_reason(blueprint_fixture):
    order_id = blueprint_fixture["order_id"]
    client = _admin_client(blueprint_fixture["db_fixture"])
    task = next(
        t
        for t in client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint").json()["tasks"]
        if t["task_id"] == "T-BLOCKED"
    )
    assert task["status"] == "blocked"
    assert task["block_reason"] == "Lipsește material"


def test_done_counts_toward_progress(blueprint_fixture):
    order_id = blueprint_fixture["order_id"]
    client = _admin_client(blueprint_fixture["db_fixture"])
    task = next(
        t
        for t in client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint").json()["tasks"]
        if t["task_id"] == "T-DONE"
    )
    assert task["status"] == "done"
    assert task["completed_at"] is not None


def test_documents_and_instructions_flags(blueprint_fixture):
    order_id = blueprint_fixture["order_id"]
    client = _admin_client(blueprint_fixture["db_fixture"])
    task = next(
        t
        for t in client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint").json()["tasks"]
        if t["task_id"] == "T-004"
    )
    assert task["documents_count"] >= 1
    assert task["has_instructions"] is True


def test_open_clarification_reflected(blueprint_fixture):
    order_id = blueprint_fixture["order_id"]
    client = _admin_client(blueprint_fixture["db_fixture"])
    task = next(
        t
        for t in client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint").json()["tasks"]
        if t["task_id"] == "T-TODO"
    )
    assert task["has_open_clarification"] is True


def test_read_only_does_not_mutate_plan_or_reality(db_fixture, db_session):
    order_id = 8000 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        emp = await _seed_employee(db_session, user_id=None, name="Readonly Worker")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=emp.id,
            task_id="T-RO",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(f"admin-ro-{uuid.uuid4().hex[:6]}", "admin"))

    async def _snapshot():
        from sqlalchemy import select

        async with db_fixture.session_maker() as session:
            plan = (
                await session.execute(
                    select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
                )
            ).scalar_one()
            reality = (
                await session.execute(
                    select(ExecutionReality).where(ExecutionReality.order_id == order_id)
                )
            ).scalar_one_or_none()
            return plan.tasks_json, reality.tasks_json if reality else None

    before = db_fixture.run(_snapshot())
    response = client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint")
    after = db_fixture.run(_snapshot())
    assert response.status_code == 200
    assert before == after
    _cleanup_overrides()


def test_t004_taxonomy_correct(blueprint_fixture):
    order_id = blueprint_fixture["order_id"]
    client = _admin_client(blueprint_fixture["db_fixture"])
    task = next(
        t
        for t in client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint").json()["tasks"]
        if t["task_id"] == "T-004"
    )
    assert task["name"] == BONDING_DISPLAY_NAME
    assert task["process_type"] == BONDING_PROCESS_TYPE
    assert task["machine_type"] == BONDING_MACHINE_TYPE
    assert task["process_type"] != "welding"


def test_no_commercial_fields_exposed(blueprint_fixture):
    order_id = blueprint_fixture["order_id"]
    client = _admin_client(blueprint_fixture["db_fixture"])
    raw = client.get(f"/api/v1/operator/orders/{order_id}/production-blueprint").text.lower()
    for forbidden in ("unit_cost", "price", "margin", "quote_pdf", "markup", "payroll"):
        assert forbidden not in raw
