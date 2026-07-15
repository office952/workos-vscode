"""MOBILE-T06 — concurrent claim and start-from-available integrity."""

from __future__ import annotations

import asyncio
import contextvars
import json
import time
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from schemas.auth import UserResponse
from services.task_work_session_service import is_session_active, sessions_for_task

from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _client_for,
    _seed_active_order,
    _seed_employee,
    _seed_plan_unassigned_task,
    _seed_print_eligibility,
    _user,
)

_claim_test_user: contextvars.ContextVar[UserResponse | None] = contextvars.ContextVar(
    "claim_test_user",
    default=None,
)


@pytest.fixture(autouse=True)
def _isolate_app_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


async def _plan_assignee(db_fixture, order_id: int, task_id: str) -> int | None:
    async with db_fixture.session_maker() as session:
        plan = (
            await session.execute(
                select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
            )
        ).scalar_one()
        tasks = json.loads(plan.tasks_json or "[]")
        match = next((t for t in tasks if t.get("task_id") == task_id), None)
        if not match:
            return None
        raw = match.get("assigned_employee_id")
        return int(raw) if raw is not None else None


async def _assignment_source(db_fixture, order_id: int, task_id: str) -> str | None:
    async with db_fixture.session_maker() as session:
        plan = (
            await session.execute(
                select(ExecutionPlan).where(ExecutionPlan.order_id == order_id)
            )
        ).scalar_one()
        tasks = json.loads(plan.tasks_json or "[]")
        match = next((t for t in tasks if t.get("task_id") == task_id), None)
        return match.get("assignment_source") if match else None


async def _active_session_count(db_fixture, order_id: int, task_id: str) -> int:
    async with db_fixture.session_maker() as session:
        row = (
            await session.execute(
                select(ExecutionReality).where(ExecutionReality.order_id == order_id)
            )
        ).scalar_one_or_none()
        if row is None:
            return 0
        sessions = sessions_for_task(json.loads(row.tasks_json or "[]"), task_id)
        return sum(1 for s in sessions if is_session_active(s))


@pytest.fixture
def claim_fixture(db_fixture):
    order_id = 93000 + int(uuid.uuid4().hex[:4], 16) % 1000
    task_id = "T-CONC-CLAIM"
    owner_user = f"claim-a-{uuid.uuid4().hex[:8]}"
    rival_user = f"claim-b-{uuid.uuid4().hex[:8]}"

    async def _setup():
        async with db_fixture.session_maker() as session:
            owner = await _seed_employee(session, user_id=owner_user, name="Claim A")
            rival = await _seed_employee(session, user_id=rival_user, name="Claim B")
            await _seed_print_eligibility(session, owner.id)
            await _seed_print_eligibility(session, rival.id)
            await _seed_active_order(session, order_id=order_id)
            await _seed_plan_unassigned_task(
                session,
                order_id=order_id,
                task_id=task_id,
            )
            return {
                "order_id": order_id,
                "task_id": task_id,
                "owner_id": owner.id,
                "owner_user": owner_user,
                "rival_id": rival.id,
                "rival_user": rival_user,
            }

    ids = db_fixture.run(_setup())
    yield {**ids, "db_fixture": db_fixture}
    _cleanup_overrides()


def _async_client_for(db_fixture) -> AsyncClient:
    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        user = _claim_test_user.get()
        if user is None:
            raise RuntimeError("claim test user not set")
        return user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_concurrent_claim_one_owner_controlled_loser(claim_fixture):
    fx = claim_fixture
    db_fixture = fx["db_fixture"]
    owner = _user(fx["owner_user"], "employee_mobile")
    rival = _user(fx["rival_user"], "employee_mobile")
    barrier = asyncio.Barrier(2)
    started: list[float] = []

    async with _async_client_for(db_fixture) as client:

        async def _claim_as(user: UserResponse):
            token = _claim_test_user.set(user)
            try:
                await barrier.wait()
                started.append(time.perf_counter())
                return await client.post(
                    f"/api/v1/employee-mobile/tasks/{fx['task_id']}/claim",
                    json={"order_id": fx["order_id"]},
                )
            finally:
                _claim_test_user.reset(token)

        r1, r2 = await asyncio.gather(_claim_as(owner), _claim_as(rival))
    _cleanup_overrides()

    assert len(started) == 2
    assert max(started) - min(started) < 0.5
    assert r1.status_code in (200, 409)
    assert r2.status_code in (200, 409)
    winners = [
        r
        for r in (r1, r2)
        if r.status_code == 200 and not r.json().get("already_claimed")
    ]
    controlled_losers = [
        r
        for r in (r1, r2)
        if r.status_code == 409
        or (r.status_code == 200 and r.json().get("already_claimed"))
    ]
    assert len(winners) == 1
    assert len(controlled_losers) == 1
    assignee = await _plan_assignee(db_fixture, fx["order_id"], fx["task_id"])
    assert assignee in (fx["owner_id"], fx["rival_id"])
    assert await _assignment_source(db_fixture, fx["order_id"], fx["task_id"]) == "employee_claim"
    assert await _active_session_count(db_fixture, fx["order_id"], fx["task_id"]) == 0


@pytest.mark.asyncio
async def test_concurrent_start_from_available_one_session(claim_fixture):
    fx = claim_fixture
    db_fixture = fx["db_fixture"]
    owner = _user(fx["owner_user"], "employee_mobile")
    rival = _user(fx["rival_user"], "employee_mobile")
    barrier = asyncio.Barrier(2)

    async with _async_client_for(db_fixture) as client:

        async def _start_as(user: UserResponse):
            token = _claim_test_user.set(user)
            try:
                await barrier.wait()
                return await client.post(
                    f"/api/v1/employee-mobile/tasks/{fx['task_id']}/start-from-available",
                    json={"order_id": fx["order_id"]},
                )
            finally:
                _claim_test_user.reset(token)

        r1, r2 = await asyncio.gather(_start_as(owner), _start_as(rival))
    _cleanup_overrides()

    ok = [r for r in (r1, r2) if r.status_code == 200]
    fail = [r for r in (r1, r2) if r.status_code != 200]
    assert len(ok) == 1
    assert len(fail) == 1
    assert fail[0].status_code in (403, 409, 422)
    assignee = await _plan_assignee(db_fixture, fx["order_id"], fx["task_id"])
    assert assignee in (fx["owner_id"], fx["rival_id"])
    assert await _active_session_count(db_fixture, fx["order_id"], fx["task_id"]) == 1


def test_claim_records_assignment_metadata(db_fixture, claim_fixture):
    fx = claim_fixture
    owner = _user(fx["owner_user"], "employee_mobile")
    client = _client_for(db_fixture, owner)
    try:
        resp = client.post(
            f"/api/v1/employee-mobile/tasks/{fx['task_id']}/claim",
            json={"order_id": fx["order_id"]},
        )
        assert resp.status_code == 200, resp.text
    finally:
        _cleanup_overrides()

    async def _assert():
        assert await _plan_assignee(db_fixture, fx["order_id"], fx["task_id"]) == fx["owner_id"]
        assert await _assignment_source(db_fixture, fx["order_id"], fx["task_id"]) == "employee_claim"

    db_fixture.run(_assert())
