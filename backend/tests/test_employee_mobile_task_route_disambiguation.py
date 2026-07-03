"""Employee Mobile task route disambiguation — order_id + task_id scoped lookup."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from schemas.auth import UserResponse

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_active_order,
    _seed_employee,
    _seed_plan_with_assigned_task,
    _seed_print_eligibility,
    _user,
)


async def _seed_plan_tasks(
    db_session,
    *,
    order_id: int,
    tasks: list[dict],
) -> None:
    db_session.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-{order_id:04d}",
            snapshot_version=1,
            tasks_json=json.dumps(tasks),
            total_estimated_time_minutes=30,
        )
    )
    await db_session.commit()


def test_get_order_task_returns_available_preview_not_other_order(db_fixture, db_session):
    user_id = f"route-{uuid.uuid4().hex[:8]}"
    owned_order = 88011
    preview_order = 88012

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Sandu Route")
        await _seed_print_eligibility(db_session, emp.id)
        await _seed_active_order(db_session, order_id=owned_order)
        await _seed_active_order(db_session, order_id=preview_order)
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=owned_order,
            assigned_employee_id=emp.id,
            task_id="T-003",
            extra_task_fields={
                "display_name": "Colantare fețe litere vechi",
                "instructions": "Aplică autocolantul pe fețele literelor, nu pe cant.",
            },
        )
        await _seed_plan_tasks(
            db_session,
            order_id=preview_order,
            tasks=[
                {
                    "task_id": "T-003",
                    "name": "Colantare fețe litere",
                    "display_name": "Colantare fețe litere",
                    "process_id": "print",
                    "process_type": "print",
                    "machine_type": "printer_large_format",
                    "estimated_time_minutes": 20,
                    "instructions": (
                        "Colantezi fețele din plexiglas ale literelor cu autocolantul selectat.\n"
                        "Lungime pregătire: 0,80 ml"
                    ),
                }
            ],
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        preview = client.get(f"/api/v1/employee-mobile/orders/{preview_order}/tasks/T-003")
        assert preview.status_code == 200, preview.text
        body = preview.json()
        assert body["order_id"] == preview_order
        assert body["preview_only"] is True
        assert body["access_mode"] == "available_preview"
        assert "Colantezi fețele" in body["instructions"]
        assert "nu pe cant" not in body["instructions"]

        owned = client.get(f"/api/v1/employee-mobile/orders/{owned_order}/tasks/T-003")
        assert owned.status_code == 200, owned.text
        owned_body = owned.json()
        assert owned_body["order_id"] == owned_order
        assert owned_body["preview_only"] is False
        assert owned_body["access_mode"] == "owned"
    finally:
        _cleanup_overrides()


def test_get_order_task_not_found_when_wrong_order(db_fixture, db_session):
    user_id = f"route-miss-{uuid.uuid4().hex[:8]}"
    owned_order = 88001
    missing_order = 88002

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Owner Only")
        await _seed_active_order(db_session, order_id=owned_order)
        await _seed_plan_with_assigned_task(
            db_session,
            order_id=owned_order,
            assigned_employee_id=emp.id,
            task_id="T-003",
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        response = client.get(f"/api/v1/employee-mobile/orders/{missing_order}/tasks/T-003")
        assert response.status_code == 404, response.text
        assert response.json()["detail"]["error"] == "task_not_found"
    finally:
        _cleanup_overrides()


def test_get_order_task_preview_does_not_create_execution_reality(db_fixture, db_session):
    user_id = f"route-readonly-{uuid.uuid4().hex[:8]}"
    order_id = 88021

    async def _setup():
        emp = await _seed_employee(db_session, user_id=user_id, name="Preview Reader")
        await _seed_active_order(db_session, order_id=order_id)
        await _seed_print_eligibility(db_session, emp.id)
        await _seed_plan_tasks(
            db_session,
            order_id=order_id,
            tasks=[
                {
                    "task_id": "T-003",
                    "name": "Colantare fețe litere",
                    "display_name": "Colantare fețe litere",
                    "process_id": "print",
                    "process_type": "print",
                    "machine_type": "printer_large_format",
                    "estimated_time_minutes": 20,
                    "instructions": "Instrucțiuni preview",
                }
            ],
        )

    db_fixture.run(_setup())
    client = _client_for(db_fixture, _user(user_id, "employee_mobile"))
    try:
        async def _count_reality() -> int:
            from sqlalchemy import func, select

            result = await db_session.execute(
                select(func.count())
                .select_from(ExecutionReality)
                .where(ExecutionReality.order_id == order_id)
            )
            return int(result.scalar_one())

        before = db_fixture.run(_count_reality())
        response = client.get(f"/api/v1/employee-mobile/orders/{order_id}/tasks/T-003")
        assert response.status_code == 200, response.text
        after = db_fixture.run(_count_reality())
        assert before == after == 0
    finally:
        _cleanup_overrides()
