"""Wave 11 / Phase B — controlled pre-start reassign/unassign (isolated DB only).

Never points at backend/dev.db. Mutating scenarios require
WORKOS_PHASE_B_RESOURCE_GUARDS=CLEAR (module autouse).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import PERMISSION_MATRIX, has_permission
from main import app
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.execution_task_assignment_transition import (
    ExecutionTaskAssignmentTransition,
)
from models.orders import Orders
from schemas.auth import UserResponse
from schemas.controlled_pre_start_reassignment import (
    ReassignPlanTaskRequest,
    UnassignPlanTaskRequest,
)
from services.assignment_transition_repository import (
    AssignmentTransitionAppendOnlyRepository,
    FORBIDDEN_MUTATOR_NAMES,
    repository_public_mutation_methods,
)
from services.controlled_pre_start_reassignment_service import (
    SOURCE_REASSIGN,
    reassign_operational_task_controlled,
    unassign_operational_task_controlled,
)
from services.employee_mobile_tasks_service import claim_my_task, start_available_task
from services.execution_task_assignment_service import (
    assign_plan_task,
    clear_plan_task_assignment,
)


TASK = "t_led"


@pytest.fixture(autouse=True)
def _phase_b_clear_guards(monkeypatch):
    # CLEAR accepted only when APP_ENV=test (conftest sets APP_ENV/ENVIRONMENT=test).
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("WORKOS_PHASE_B_RESOURCE_GUARDS", "CLEAR")
    yield
    monkeypatch.delenv("WORKOS_PHASE_B_RESOURCE_GUARDS", raising=False)


@pytest.fixture(autouse=True)
def _isolate_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _user(role: str = "manager") -> UserResponse:
    uid = f"w11-{uuid.uuid4().hex[:8]}"
    return UserResponse(
        id=uid,
        email=f"{uid}@workos.test",
        name=f"User {uid}",
        role=role,
        last_login=None,
    )


def _client_for(db_fixture, user: UserResponse) -> TestClient:
    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    return TestClient(app, raise_server_exceptions=False)


def _envelope(ops: list[dict], *, created: bool = True) -> str:
    return json.dumps(
        {
            "source": "order_snapshot_v2",
            "planned_tasks": [{"task_key": TASK, "canonical_task_type": "led_assembly"}],
            "execution_tasks_created": created,
            "operational_tasks": ops,
        }
    )


def _ready_elig(employee_ids: list[int]):
    return {
        "status": "ok",
        "tasks": [
            {
                "task_key": TASK,
                "eligibility_status": "ready_with_warnings",
                "eligible_employee_count": len(employee_ids),
                "eligible_employees": [
                    {"employee_id": eid, "display_name": f"E{eid}"} for eid in employee_ids
                ],
                "blockers": [],
                "warnings": [],
                "requirement_version": "eligibility-rm/v1",
            }
        ],
    }


async def _seed_order(db_session, order_id: int) -> Orders:
    row = Orders(
        id=order_id,
        code=f"ORD-W11-{order_id}",
        client_name="Wave11",
        status="in_production",
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _seed_employee(db_session, *, name: str = "Worker") -> Employees:
    emp = Employees(name=name, status="active", employee_type="productive")
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


async def _seed_plan(db_session, *, order_id: int, tasks_json: str) -> ExecutionPlan:
    row = ExecutionPlan(
        order_id=order_id,
        order_code=f"ORD-W11-{order_id}",
        snapshot_version=1,
        tasks_json=tasks_json,
        total_estimated_time_minutes=0,
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)
    return row


async def _seed_assign_history(
    db_session,
    *,
    plan: ExecutionPlan,
    task_key: str,
    employee_id: int,
    transition_id: str | None = None,
) -> str:
    tid = transition_id or str(uuid.uuid4())
    row = ExecutionTaskAssignmentTransition(
        transition_id=tid,
        execution_plan_id=plan.id,
        order_id=plan.order_id,
        task_key=task_key,
        transition_type="ASSIGN",
        previous_employee_id=None,
        new_employee_id=employee_id,
        actor_user_id="seed",
        actor_role="admin",
        reason_code="INITIAL_ASSIGNMENT_BACKFILL",
        source="LEGACY_EMBEDDED_BACKFILL",
        expected_current_employee_id=employee_id,
        command_version="seed",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(row)
    await db_session.commit()
    return tid


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


def test_permission_matrix_reassign_unassign_roles():
    assert "execution.task_reassign" in PERMISSION_MATRIX
    assert "execution.task_unassign" in PERMISSION_MATRIX
    assert set(PERMISSION_MATRIX["execution.task_reassign"]) == {"admin", "manager"}
    assert set(PERMISSION_MATRIX["execution.task_unassign"]) == {"admin", "manager"}
    assert has_permission("admin", "execution.task_reassign")
    assert has_permission("manager", "execution.task_unassign")
    assert not has_permission("operator", "execution.task_reassign")
    assert not has_permission("viewer", "execution.task_unassign")
    assert has_permission("operator", "execution.task_assign")
    assert not has_permission("operator", "execution.task_reassign")


@pytest.mark.asyncio
async def test_http_roles_reassign(db_fixture, db_session, monkeypatch):
    e7 = await _seed_employee(db_session, name="Cur")
    e6 = await _seed_employee(db_session, name="New")
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7.id, e6.id])),
    )

    async def _prep(order_id: int) -> None:
        await _seed_order(db_session, order_id)
        plan = await _seed_plan(
            db_session,
            order_id=order_id,
            tasks_json=_envelope(
                [{"task_id": TASK, "assigned_employee_id": e7.id}]
            ),
        )
        await _seed_assign_history(
            db_session, plan=plan, task_key=TASK, employee_id=e7.id
        )

    def _body(tid: str):
        return {
            "transition_id": tid,
            "expected_current_employee_id": e7.id,
            "new_employee_id": e6.id,
            "reason_code": "MANAGER_CORRECTION",
        }

    for idx, (role, expect) in enumerate(
        (("admin", 200), ("manager", 200), ("operator", 403), ("viewer", 403))
    ):
        order_id = 611001 + idx
        await _prep(order_id)
        client = _client_for(db_fixture, _user(role))
        resp = client.patch(
            f"/api/v1/execution/plan/{order_id}/tasks/{TASK}/reassign",
            json=_body(str(uuid.uuid4())),
        )
        assert resp.status_code == expect, (role, resp.status_code, resp.text)


@pytest.mark.asyncio
async def test_http_unassign_operator_denied(db_fixture, db_session):
    order_id = 611092
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session)
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": e7.id}]),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    client = _client_for(db_fixture, _user("operator"))
    resp = client.patch(
        f"/api/v1/execution/plan/{order_id}/tasks/{TASK}/unassign",
        json={
            "transition_id": str(uuid.uuid4()),
            "expected_current_employee_id": e7.id,
            "reason_code": "EMPLOYEE_UNAVAILABLE",
        },
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Request validation
# ---------------------------------------------------------------------------


def test_schema_rejects_invalid_and_other_without_note():
    with pytest.raises(Exception):
        ReassignPlanTaskRequest(
            transition_id="not-a-uuid",
            expected_current_employee_id=1,
            new_employee_id=2,
            reason_code="MANAGER_CORRECTION",
        )
    with pytest.raises(Exception):
        ReassignPlanTaskRequest(
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=1,
            new_employee_id=1,
            reason_code="MANAGER_CORRECTION",
        )
    with pytest.raises(Exception):
        ReassignPlanTaskRequest(
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=1,
            new_employee_id=2,
            reason_code="OTHER",
        )
    with pytest.raises(Exception):
        UnassignPlanTaskRequest(
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=1,
            reason_code="OTHER",
            reason_note="   ",
        )
    with pytest.raises(Exception):
        ReassignPlanTaskRequest(
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=1,
            new_employee_id=2,
            reason_code="MANAGER_CORRECTION",
            allow_reassign=True,
        )


# ---------------------------------------------------------------------------
# Happy path + idempotency + CAS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reassign_unassign_idempotency_and_history(
    db_fixture, db_session, monkeypatch
):
    order_id = 611010
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session, name="A")
    e6 = await _seed_employee(db_session, name="B")
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope(
            [{"task_id": TASK, "assigned_employee_id": e7.id}]
        ),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7.id, e6.id])),
    )

    tid_re = str(uuid.uuid4())
    r1 = await reassign_operational_task_controlled(
        db_session,
        order_id=order_id,
        task_id=TASK,
        transition_id=tid_re,
        expected_current_employee_id=e7.id,
        new_employee_id=e6.id,
        reason_code="MANAGER_CORRECTION",
        actor_user_id="mgr-1",
        actor_role="manager",
    )
    assert r1["status"] == "reassigned"
    assert r1["new_employee_id"] == e6.id

    # Capture updated_at
    await db_session.refresh(plan)
    upd_after_re = plan.updated_at
    tasks_after_re = plan.tasks_json

    r2 = await reassign_operational_task_controlled(
        db_session,
        order_id=order_id,
        task_id=TASK,
        transition_id=tid_re,
        expected_current_employee_id=e7.id,
        new_employee_id=e6.id,
        reason_code="MANAGER_CORRECTION",
        actor_user_id="mgr-1",
        actor_role="manager",
    )
    assert r2["status"] == "already_applied"
    await db_session.refresh(plan)
    assert plan.tasks_json == tasks_after_re
    assert plan.updated_at == upd_after_re

    with pytest.raises(HTTPException) as exc:
        await reassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=tid_re,
            expected_current_employee_id=e7.id,
            new_employee_id=e6.id,
            reason_code="PLANNING_CHANGE",
            actor_role="manager",
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["error"] == "transition_id_payload_conflict"

    with pytest.raises(HTTPException) as exc2:
        await reassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=e7.id,
            new_employee_id=e6.id,
            reason_code="MANAGER_CORRECTION",
            actor_role="manager",
        )
    assert exc2.value.detail["error"] == "stale_current_assignment"

    tid_un = str(uuid.uuid4())
    u1 = await unassign_operational_task_controlled(
        db_session,
        order_id=order_id,
        task_id=TASK,
        transition_id=tid_un,
        expected_current_employee_id=e6.id,
        reason_code="EMPLOYEE_UNAVAILABLE",
        actor_role="admin",
    )
    assert u1["status"] == "unassigned"
    assert u1["new_employee_id"] is None

    u2 = await unassign_operational_task_controlled(
        db_session,
        order_id=order_id,
        task_id=TASK,
        transition_id=tid_un,
        expected_current_employee_id=e6.id,
        reason_code="EMPLOYEE_UNAVAILABLE",
        actor_role="admin",
    )
    assert u2["status"] == "already_applied"

    repo = AssignmentTransitionAppendOnlyRepository(db_session)
    hist = await repo.list_for_task(execution_plan_id=plan.id, task_key=TASK)
    types = [h.transition_type for h in hist]
    assert types == ["ASSIGN", "REASSIGN", "UNASSIGN"]
    assert FORBIDDEN_MUTATOR_NAMES.isdisjoint(repository_public_mutation_methods())


@pytest.mark.asyncio
async def test_session_history_and_resource_not_configured_block(
    db_fixture, db_session, monkeypatch
):
    order_id = 611020
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session)
    e6 = await _seed_employee(db_session)
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": e7.id}]),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    reality = ExecutionReality(
        order_id=order_id,
        order_code=f"ORD-W11-{order_id}",
        tasks_json=json.dumps(
            [
                {
                    "task_id": TASK,
                    "started_at": "2026-08-01T10:00:00+00:00",
                    "ended_at": "2026-08-01T11:00:00+00:00",
                }
            ]
        ),
    )
    db_session.add(reality)
    await db_session.commit()
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7.id, e6.id])),
    )
    with pytest.raises(HTTPException) as exc:
        await reassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=e7.id,
            new_employee_id=e6.id,
            reason_code="MANAGER_CORRECTION",
            actor_role="manager",
        )
    assert exc.value.detail["error"] == "task_has_execution_history"

    # Clear history; remove CLEAR env → NOT_CONFIGURED block
    reality.tasks_json = "[]"
    await db_session.commit()
    monkeypatch.delenv("WORKOS_PHASE_B_RESOURCE_GUARDS", raising=False)
    with pytest.raises(HTTPException) as exc2:
        await reassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=e7.id,
            new_employee_id=e6.id,
            reason_code="MANAGER_CORRECTION",
            actor_role="manager",
        )
    assert exc2.value.detail["error"] == "scheduling_state_not_clear"


@pytest.mark.asyncio
async def test_mismatch_without_history_blocks(db_session):
    order_id = 611030
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session)
    e6 = await _seed_employee(db_session)
    await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": e7.id}]),
    )
    with pytest.raises(HTTPException) as exc:
        await reassign_operational_task_controlled(
            db_session,
            order_id=order_id,
            task_id=TASK,
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=e7.id,
            new_employee_id=e6.id,
            reason_code="MANAGER_CORRECTION",
            actor_role="manager",
        )
    assert exc.value.detail["error"] == "assignment_transition_state_mismatch"


@pytest.mark.asyncio
async def test_service_level_operator_denied_even_if_called_directly(db_session):
    with pytest.raises(HTTPException) as exc:
        await reassign_operational_task_controlled(
            db_session,
            order_id=1,
            task_id=TASK,
            transition_id=str(uuid.uuid4()),
            expected_current_employee_id=1,
            new_employee_id=2,
            reason_code="MANAGER_CORRECTION",
            actor_role="operator",
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_legacy_bypasses_remain_blocked():
    with pytest.raises(HTTPException) as e1:
        await assign_plan_task(
            AsyncMock(), order_id=1, task_id=TASK, assigned_employee_id=1
        )
    assert e1.value.status_code == 403
    with pytest.raises(HTTPException) as e2:
        await claim_my_task(
            AsyncMock(), order_id=1, task_id=TASK, employee_id=1
        )
    assert e2.value.detail["error"] == "employee_mobile_assignment_frozen"
    with pytest.raises(HTTPException) as e3:
        await start_available_task(
            AsyncMock(), order_id=1, task_id=TASK, employee_id=1
        )
    assert e3.value.detail["error"] == "employee_mobile_assignment_frozen"
    # clear helper is legacy (no transition) — not the Phase B unassign path.
    assert callable(clear_plan_task_assignment)


@pytest.mark.asyncio
async def test_concurrent_reassign_one_wins(db_fixture, db_session, monkeypatch):
    import asyncio

    order_id = 611050
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session, name="Cur")
    e6 = await _seed_employee(db_session, name="T6")
    e5 = await _seed_employee(db_session, name="T5")
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": e7.id}]),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7.id, e6.id, e5.id])),
    )

    async def _one(target: int, session):
        try:
            return await reassign_operational_task_controlled(
                session,
                order_id=order_id,
                task_id=TASK,
                transition_id=str(uuid.uuid4()),
                expected_current_employee_id=e7.id,
                new_employee_id=target,
                reason_code="OPERATIONAL_REBALANCE_PRE_START",
                actor_role="manager",
            )
        except HTTPException as exc:
            return exc

    async with db_fixture.session_maker() as s1, db_fixture.session_maker() as s2:
        r1, r2 = await asyncio.gather(_one(e6.id, s1), _one(e5.id, s2))
    outcomes = []
    for r in (r1, r2):
        if isinstance(r, dict):
            outcomes.append(("ok", r["new_employee_id"]))
        else:
            outcomes.append(("err", r.detail.get("error")))
    oks = [o for o in outcomes if o[0] == "ok"]
    errs = [o for o in outcomes if o[0] == "err"]
    assert len(oks) == 1
    assert len(errs) == 1
    assert errs[0][1] in {
        "stale_current_assignment",
        "assignment_transition_state_mismatch",
    }


@pytest.mark.asyncio
async def test_http_reassign_success_path(db_fixture, db_session, monkeypatch):
    order_id = 611040
    await _seed_order(db_session, order_id)
    e7 = await _seed_employee(db_session, name="Cur")
    e6 = await _seed_employee(db_session, name="New")
    plan = await _seed_plan(
        db_session,
        order_id=order_id,
        tasks_json=_envelope([{"task_id": TASK, "assigned_employee_id": e7.id}]),
    )
    await _seed_assign_history(
        db_session, plan=plan, task_key=TASK, employee_id=e7.id
    )
    monkeypatch.setattr(
        "services.controlled_pre_start_reassignment_service.build_employee_eligibility_read_model",
        AsyncMock(return_value=_ready_elig([e7.id, e6.id])),
    )
    client = _client_for(db_fixture, _user("manager"))
    tid = str(uuid.uuid4())
    path = f"/api/v1/execution/plan/{order_id}/tasks/{TASK}/reassign"
    resp = client.patch(
        path,
        json={
            "transition_id": tid,
            "expected_current_employee_id": e7.id,
            "new_employee_id": e6.id,
            "reason_code": "MANAGER_CORRECTION",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "reassigned"
    assert body["consistency"] == "MATCH"
    retry = client.patch(
        path,
        json={
            "transition_id": tid,
            "expected_current_employee_id": e7.id,
            "new_employee_id": e6.id,
            "reason_code": "MANAGER_CORRECTION",
        },
    )
    assert retry.status_code == 200
    assert retry.json()["status"] == "already_applied"
