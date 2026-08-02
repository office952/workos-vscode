"""Controlled Task Sessions & ExecutionActuals V1 — targeted domain tests."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from services.controlled_task_session_service import (
    build_execution_actuals_read_model,
    end_controlled_task_session,
    start_controlled_task_session,
)


LED = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:INSTALL_LED_MODULES"
PREPRESS_TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:PREPRESS_VECTOR"


def _v2_plan(*, assigned_led: int | None = 7, assigned_prepress: int | None = None) -> dict:
    return {
        "source": "order_snapshot_v2",
        "operational_tasks": [
            {
                "task_id": LED,
                "name": "Install LED",
                "assigned_employee_id": assigned_led,
                "estimated_time_minutes": None,
                "workcenter": "WC_LED_ASSEMBLY",
            },
            {
                "task_id": PREPRESS_TASK,
                "name": "Prepress",
                "assigned_employee_id": assigned_prepress,
                "estimated_time_minutes": 10,
                "workcenter": "WC_PREPRESS",
            },
        ],
        "dependency_edges": [],
    }


@pytest.mark.asyncio
async def test_start_rejects_unassigned(monkeypatch):
    plan = SimpleNamespace(id=21, order_id=973019, tasks_json=json.dumps(_v2_plan(assigned_led=None)))
    order = SimpleNamespace(id=973019, code="ORD-973019")
    emp = SimpleNamespace(id=7, name="Andrei", status="active")

    async def fake_execute(stmt):
        # Rough: return plan / order / emp / reality based on call order is fragile;
        # monkeypatch helpers instead.
        return SimpleNamespace(scalar_one_or_none=lambda: None)

    monkeypatch.setattr(
        "services.controlled_task_session_service._load_plan",
        AsyncMock(return_value=plan),
    )
    monkeypatch.setattr(
        "services.controlled_task_session_service._load_order",
        AsyncMock(return_value=order),
    )
    monkeypatch.setattr(
        "services.controlled_task_session_service._load_active_employee",
        AsyncMock(return_value=emp),
    )
    db = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await start_controlled_task_session(
            db,
            order_id=973019,
            task_id=LED,
            employee_id=7,
            actor_mode="supervisor",
        )
    assert exc.value.detail["error"] == "task_unassigned"


@pytest.mark.asyncio
async def test_start_rejects_wrong_employee(monkeypatch):
    plan = SimpleNamespace(id=21, order_id=1, tasks_json=json.dumps(_v2_plan(assigned_led=7)))
    order = SimpleNamespace(id=1, code="ORD-1")
    emp = SimpleNamespace(id=5, name="Vali", status="active")
    monkeypatch.setattr(
        "services.controlled_task_session_service._load_plan",
        AsyncMock(return_value=plan),
    )
    monkeypatch.setattr(
        "services.controlled_task_session_service._load_order",
        AsyncMock(return_value=order),
    )
    monkeypatch.setattr(
        "services.controlled_task_session_service._load_active_employee",
        AsyncMock(return_value=emp),
    )
    db = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await start_controlled_task_session(
            db,
            order_id=1,
            task_id=LED,
            employee_id=5,
            actor_mode="supervisor",
        )
    assert exc.value.detail["error"] == "employee_not_assigned"


@pytest.mark.asyncio
async def test_start_end_idempotent_duration(monkeypatch):
    plan = SimpleNamespace(id=21, order_id=973019, tasks_json=json.dumps(_v2_plan()))
    order = SimpleNamespace(id=973019, code="ORD-973019")
    emp = SimpleNamespace(id=7, name="Andrei Goghi", status="active")
    reality_state = {"tasks": []}

    class FakeSvc:
        def __init__(self, db):
            self.db = db

        async def start_task(self, **kwargs):
            started = kwargs["timestamp"]
            observation = {
                "session_id": "ws-test1",
                "task_id": kwargs["task_id"],
                "employee_id": kwargs["initial_fields"]["employee_id"],
                "employee_name": kwargs["initial_fields"]["employee_name"],
                "started_at": started,
                "ended_at": None,
                "status": "in_progress",
                "source": "controlled_task_session_v1",
            }
            reality_state["tasks"].append(observation)
            return SimpleNamespace(
                tasks_json=json.dumps(reality_state["tasks"]),
                total_actual_time_minutes=0,
            )

        async def end_task(self, **kwargs):
            ended = kwargs["timestamp"]
            for t in reality_state["tasks"]:
                if (
                    t["task_id"] == kwargs["task_id"]
                    and t.get("employee_id") == kwargs.get("employee_id")
                    and not t.get("ended_at")
                ):
                    t["ended_at"] = ended
                    t["status"] = "ended"
                    from services.task_work_session_service import compute_duration_minutes

                    t["duration_minutes"] = compute_duration_minutes(
                        t["started_at"], ended
                    )
                    break
            total = sum(int(x.get("duration_minutes") or 0) for x in reality_state["tasks"])
            return SimpleNamespace(
                tasks_json=json.dumps(reality_state["tasks"]),
                total_actual_time_minutes=total,
            )

    monkeypatch.setattr(
        "services.controlled_task_session_service._load_plan",
        AsyncMock(return_value=plan),
    )
    monkeypatch.setattr(
        "services.controlled_task_session_service._load_order",
        AsyncMock(return_value=order),
    )
    monkeypatch.setattr(
        "services.controlled_task_session_service._load_active_employee",
        AsyncMock(return_value=emp),
    )
    monkeypatch.setattr(
        "services.controlled_task_session_service.ExecutionRealityService",
        FakeSvc,
    )

    t0 = datetime(2026, 8, 2, 10, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(minutes=25)

    db = AsyncMock()
    # first start — no reality
    db.execute = AsyncMock(
        return_value=SimpleNamespace(scalar_one_or_none=lambda: None)
    )
    r1 = await start_controlled_task_session(
        db,
        order_id=973019,
        task_id=LED,
        employee_id=7,
        actor_mode="supervisor",
        clock=lambda: t0,
    )
    assert r1["already_active"] is False
    assert r1["started_at"]

    # second start — active reality
    db.execute = AsyncMock(
        return_value=SimpleNamespace(
            scalar_one_or_none=lambda: SimpleNamespace(
                tasks_json=json.dumps(reality_state["tasks"])
            )
        )
    )
    r2 = await start_controlled_task_session(
        db,
        order_id=973019,
        task_id=LED,
        employee_id=7,
        actor_mode="supervisor",
        clock=lambda: t0 + timedelta(minutes=1),
    )
    assert r2["already_active"] is True
    assert len(reality_state["tasks"]) == 1

    end1 = await end_controlled_task_session(
        db,
        order_id=973019,
        task_id=LED,
        employee_id=7,
        actor_mode="supervisor",
        clock=lambda: t1,
    )
    assert end1["already_ended"] is False
    assert end1["duration_minutes"] == 25
    assert end1["task_auto_completed"] is False
    assert end1["variance_reason"] == "planning_minutes_source_missing"

    end2 = await end_controlled_task_session(
        db,
        order_id=973019,
        task_id=LED,
        employee_id=7,
        actor_mode="supervisor",
        clock=lambda: t1 + timedelta(minutes=5),
    )
    assert end2["already_ended"] is True
    assert end2["duration_minutes"] == 25


@pytest.mark.asyncio
async def test_actuals_projection_separates_planned(monkeypatch):
    plan = SimpleNamespace(id=21, order_id=1, tasks_json=json.dumps(_v2_plan()))
    monkeypatch.setattr(
        "services.controlled_task_session_service._load_plan",
        AsyncMock(return_value=plan),
    )
    reality = SimpleNamespace(
        tasks_json=json.dumps(
            [
                {
                    "session_id": "ws-1",
                    "task_id": LED,
                    "employee_id": 7,
                    "started_at": "2026-08-02T10:00:00+00:00",
                    "ended_at": "2026-08-02T10:30:00+00:00",
                    "duration_minutes": 30,
                }
            ]
        ),
        total_actual_time_minutes=30.0,
    )
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=SimpleNamespace(scalar_one_or_none=lambda: reality)
    )
    model = await build_execution_actuals_read_model(db, order_id=1, task_id=LED)
    row = model["tasks"][0]
    assert row["total_actual_duration_minutes"] == 30
    assert row["planned_minutes"] is None
    assert row["variance_reason"] == "planning_minutes_source_missing"
