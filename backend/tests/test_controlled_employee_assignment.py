"""Controlled Employee Assignment V1 — eligibility-gated mutations."""

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
    db = AsyncMock()
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
    db = AsyncMock()
    # Reality query returns none
    db.execute = AsyncMock(
        return_value=SimpleNamespace(scalar_one_or_none=lambda: None)
    )
    with pytest.raises(HTTPException) as exc:
        await assign_operational_task_controlled(
            db,
            order_id=1,
            task_id="t_led",
            assigned_employee_id=999,
        )
    assert exc.value.detail["error"] == "employee_not_eligible"


@pytest.mark.asyncio
async def test_controlled_accepts_eligible_and_calls_assign(monkeypatch):
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
                    "warnings": [],
                    "requirement_version": "eligibility-rm/v1",
                }
            ],
        }

    async def fake_assign(db, **kwargs):
        return {
            "plan_id": 21,
            "order_id": kwargs["order_id"],
            "task_id": kwargs["task_id"],
            "assigned_employee_id": kwargs["assigned_employee_id"],
            "assigned_employee_name": "Andrei Goghi",
            "already_assigned": False,
        }

    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.build_employee_eligibility_read_model",
        fake_elig,
    )
    monkeypatch.setattr(
        "services.controlled_employee_assignment_service.assign_plan_task",
        fake_assign,
    )
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=SimpleNamespace(scalar_one_or_none=lambda: None)
    )
    result = await assign_operational_task_controlled(
        db,
        order_id=973019,
        task_id="t_led",
        assigned_employee_id=7,
    )
    assert result["assigned_employee_id"] == 7
    assert result["controlled"] is True
    assert result["sessions_created"] == 0
    assert result["actuals_created"] == 0
