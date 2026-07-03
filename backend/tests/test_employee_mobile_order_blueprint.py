"""Tests for employee-mobile my order blueprint endpoint."""

from __future__ import annotations

import json
import uuid

import pytest
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from schemas.auth import UserResponse
from services.volumetric_return_task_taxonomy_service import (
    RETURN_BONDING_PROCESS_ID,
    SIDE_FORMING_PROCESS_ID,
    apply_volumetric_return_taxonomy_to_task,
)

from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_employee,
    _seed_plan_with_assigned_task,
    _user,
)


@pytest.fixture
def mobile_blueprint_fixture(db_fixture, db_session):
    user_id = f"mobile-bp-{uuid.uuid4().hex[:8]}"
    order_id = 9000 + int(uuid.uuid4().hex[:4], 16) % 1000

    async def _setup():
        worker = await _seed_employee(db_session, user_id=user_id, name="Sandu Worker")
        other = await _seed_employee(db_session, user_id=None, name="Other Worker")
        tasks = [
            apply_volumetric_return_taxonomy_to_task(
                {
                    "task_id": "T-003",
                    "process_id": SIDE_FORMING_PROCESS_ID,
                    "process_type": "edge_bending",
                    "machine_type": "RETURN_PROFILE_FORMING_MACHINE",
                    "display_name": "Modelare canturi litere volumetrice",
                    "instructions": "Modelează canturile.",
                },
                set_owner_instructions=True,
            ),
            apply_volumetric_return_taxonomy_to_task(
                {
                    "task_id": "T-004",
                    "process_id": RETURN_BONDING_PROCESS_ID,
                    "process_type": "welding",
                    "machine_type": "RETURN_PROFILE_FACE_BONDING",
                    "assigned_employee_id": worker.id,
                    "documents": [{"id": "doc-1", "name": "Schiță.svg", "type": "svg"}],
                    "instructions": "Lipește canturile.",
                },
                set_owner_instructions=True,
            ),
            {
                "task_id": "T-006",
                "name": "Montaj LED",
                "process_type": "led_assembly",
                "machine_type": "LED_ASSEMBLY",
                "assigned_employee_id": worker.id,
            },
            {
                "task_id": "T-001",
                "name": "Verificare grafică",
                "process_type": "print",
                "machine_type": "PREPRESS",
                "assigned_employee_id": other.id,
            },
        ]
        db_session.add(
            ExecutionPlan(
                order_id=order_id,
                order_code=f"ORD-BP-{order_id}",
                snapshot_version=1,
                tasks_json=json.dumps(tasks),
                total_estimated_time_minutes=90,
            )
        )
        db_session.add(
            ExecutionReality(
                order_id=order_id,
                order_code=f"ORD-BP-{order_id}",
                tasks_json="[]",
                total_actual_time_minutes=0,
            )
        )
        await db_session.commit()
        return worker.id

    worker_id = db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    yield client, order_id, worker_id, user_id
    _cleanup_overrides()


def test_sandu_can_access_my_blueprint(mobile_blueprint_fixture):
    client, order_id, worker_id, _ = mobile_blueprint_fixture
    response = client.get(f"/api/v1/employee-mobile/orders/{order_id}/my-blueprint")
    assert response.status_code == 200
    body = response.json()
    assert body["order_id"] == order_id
    assert body["summary"]["my_tasks"] == 2


def test_is_mine_flags(mobile_blueprint_fixture):
    client, order_id, _, _ = mobile_blueprint_fixture
    tasks = client.get(f"/api/v1/employee-mobile/orders/{order_id}/my-blueprint").json()["tasks"]
    t003 = next(t for t in tasks if t["task_id"] == "T-003")
    t004 = next(t for t in tasks if t["task_id"] == "T-004")
    assert t003["is_mine"] is False
    assert t004["is_mine"] is True


def test_non_mine_tasks_do_not_expose_other_employee_names(mobile_blueprint_fixture):
    client, order_id, _, _ = mobile_blueprint_fixture
    raw = client.get(f"/api/v1/employee-mobile/orders/{order_id}/my-blueprint").text.lower()
    assert "other worker" not in raw
    assert "assigned_employee_name" not in raw
    assert "active_worker_name" not in raw


def test_no_commercial_fields(mobile_blueprint_fixture):
    client, order_id, _, _ = mobile_blueprint_fixture
    raw = client.get(f"/api/v1/employee-mobile/orders/{order_id}/my-blueprint").text.lower()
    for forbidden in ("unit_cost", "price", "margin", "markup", "payroll", "prepared_by", "supplier"):
        assert forbidden not in raw


def test_employee_without_order_tasks_gets_403(db_fixture, db_session):
    user_id = f"mobile-no-order-{uuid.uuid4().hex[:6]}"
    order_id = 9100 + int(uuid.uuid4().hex[:3], 16) % 100

    async def _setup():
        worker = await _seed_employee(db_session, user_id=user_id, name="No Order Worker")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=worker.id + 999,
            task_id="T-999",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    response = client.get(f"/api/v1/employee-mobile/orders/{order_id}/my-blueprint")
    assert response.status_code == 403
    _cleanup_overrides()


def test_operator_role_cannot_use_employee_mobile_blueprint(db_fixture, db_session):
    order_id = 9200 + int(uuid.uuid4().hex[:3], 16) % 100

    async def _setup():
        worker = await _seed_employee(db_session, user_id=None, name="Plan Worker")
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=order_id,
            assigned_employee_id=worker.id,
            task_id="T-OP",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(f"op-{uuid.uuid4().hex[:6]}", "operator"))
    response = client.get(f"/api/v1/employee-mobile/orders/{order_id}/my-blueprint")
    assert response.status_code == 403
    _cleanup_overrides()


def test_summary_my_done_and_progress(mobile_blueprint_fixture, db_fixture, db_session):
    client, order_id, worker_id, _ = mobile_blueprint_fixture

    async def _complete_one():
        from sqlalchemy import select

        row = (
            await db_session.execute(
                select(ExecutionReality).where(ExecutionReality.order_id == order_id)
            )
        ).scalar_one()
        row.tasks_json = json.dumps(
            [
                {
                    "task_id": "T-006",
                    "employee_id": worker_id,
                    "employee_name": "Sandu Worker",
                    "started_at": "2026-06-14T08:00:00+00:00",
                    "ended_at": "2026-06-14T08:30:00+00:00",
                }
            ]
        )
        await db_session.commit()

    db_fixture.run(_complete_one())
    body = client.get(f"/api/v1/employee-mobile/orders/{order_id}/my-blueprint").json()
    assert body["summary"]["my_done"] == 1
    assert body["summary"]["my_progress_percent"] == 50


def test_t004_is_current_task(mobile_blueprint_fixture):
    client, order_id, _, _ = mobile_blueprint_fixture
    body = client.get(f"/api/v1/employee-mobile/orders/{order_id}/my-blueprint").json()
    assert body["current_task_id"] == "T-004"
    t004 = next(t for t in body["tasks"] if t["task_id"] == "T-004")
    assert t004["is_current"] is True
    assert t004["status_display"] == "Alocat"
