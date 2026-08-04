"""Controlled Employee Assignment — Wave 6 canonical command unit coverage."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from services.controlled_employee_assignment_service import (
    assign_operational_task_controlled,
)


@pytest.mark.asyncio
async def test_controlled_rejects_blocked_no_matching_employee(monkeypatch):
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
    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.assert_operational_mutation_allowed",
        lambda p: None,
    )
    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.is_assignable",
        lambda e, d: True,
    )

    order = SimpleNamespace(id=973019)
    emp = SimpleNamespace(id=7, name="X", status="active", end_date=None)
    plan = SimpleNamespace(
        id=21,
        order_id=973019,
        order_code="O",
        tasks_json='{"source":"order_snapshot_v2","execution_tasks_created":true,"operational_tasks":[{"task_id":"t_prepress"}]}',
    )

    class _Result:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

    seq = [order, emp, plan, emp, None]

    async def fake_execute(stmt):
        return _Result(seq.pop(0) if seq else None)

    db = AsyncMock()
    db.execute = fake_execute

    with pytest.raises(HTTPException) as exc:
        await assign_operational_task_controlled(
            db,
            order_id=973019,
            task_id="t_prepress",
            assigned_employee_id=7,
        )
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == "blocked_no_matching_employee"


@pytest.mark.asyncio
async def test_controlled_rejects_employee_not_in_eligibility(monkeypatch):
    async def fake_elig(db, order_id):
        return {
            "status": "ok",
            "tasks": [
                {
                    "task_key": "t_led",
                    "eligibility_status": "ready_with_warnings",
                    "eligible_employee_count": 1,
                    "eligible_employees": [{"employee_id": 7, "display_name": "Andrei"}],
                    "blockers": [],
                    "warnings": ["planning_minutes_source_missing"],
                }
            ],
        }

    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.build_employee_eligibility_read_model",
        fake_elig,
    )
    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.assert_operational_mutation_allowed",
        lambda p: None,
    )
    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.is_assignable",
        lambda e, d: True,
    )

    order = SimpleNamespace(id=1)
    emp = SimpleNamespace(id=999, name="X", status="active", end_date=None)
    plan = SimpleNamespace(
        id=1,
        order_id=1,
        order_code="O",
        tasks_json='{"source":"order_snapshot_v2","execution_tasks_created":true,"operational_tasks":[{"task_id":"t_led"}]}',
    )

    class _Result:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

    seq = [order, emp, plan, emp, None]

    async def fake_execute(stmt):
        return _Result(seq.pop(0) if seq else None)

    db = AsyncMock()
    db.execute = fake_execute

    with pytest.raises(HTTPException) as exc:
        await assign_operational_task_controlled(
            db,
            order_id=1,
            task_id="t_led",
            assigned_employee_id=999,
        )
    assert exc.value.detail["error"] == "employee_not_eligible"


@pytest.mark.asyncio
async def test_controlled_accepts_eligible_and_persists(db_session, monkeypatch):
    from models.employees import Employees
    from models.execution_plan import ExecutionPlan
    from models.orders import Orders

    order = Orders(id=61201, code="ORD-61201", client_name="C", status="in_production")
    db_session.add(order)
    emp = Employees(name="Andrei Goghi", status="active", employee_type="productive")
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    db_session.add(
        ExecutionPlan(
            order_id=61201,
            order_code="ORD-61201",
            snapshot_version=1,
            tasks_json=(
                '{"source":"order_snapshot_v2","execution_tasks_created":true,'
                '"operational_tasks":[{"task_id":"t_led","process_type":"led_assembly"}]}'
            ),
            total_estimated_time_minutes=0,
        )
    )
    await db_session.commit()

    async def fake_elig(db, order_id):
        return {
            "status": "ok",
            "tasks": [
                {
                    "task_key": "t_led",
                    "eligibility_status": "ready_with_warnings",
                    "eligible_employee_count": 1,
                    "eligible_employees": [{"employee_id": emp.id, "display_name": "Andrei"}],
                    "blockers": [],
                    "warnings": [],
                    "requirement_version": "eligibility-rm/v1",
                }
            ],
        }

    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.build_employee_eligibility_read_model",
        fake_elig,
    )
    result = await assign_operational_task_controlled(
        db_session,
        order_id=61201,
        task_id="t_led",
        assigned_employee_id=emp.id,
        actor_user_id="u-1",
    )
    assert result["assigned_employee_id"] == emp.id
    assert result["controlled"] is True
    assert result["sessions_created"] == 0
    assert result["actuals_created"] == 0
    assert result["assignment_outcome"] == "assigned"
    assert result["task"]["assignment_actor_user_id"] == "u-1"
