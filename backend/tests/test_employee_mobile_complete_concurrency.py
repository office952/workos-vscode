"""MOBILE-T05B — concurrent Complete integrity for employee mobile."""

from __future__ import annotations

import asyncio
import contextvars
import json
import time
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from core.database import get_db
from dependencies.auth import get_current_user
from main import app
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from schemas.auth import UserResponse
from services.task_work_session_service import (
    active_session_for_employee,
    derive_task_status_for_employee,
    is_session_active,
    sessions_for_task,
)

from tests.test_employee_mobile_tasks import (
    _cleanup_overrides,
    _seed_employee,
    _seed_plan_with_assigned_task,
    _seed_reality_task,
    _user,
)

# Past timestamp — must be before "now" or end_task rejects with timestamp_before_start.
_FIXTURE_STARTED_AT = "2026-06-12T08:00:00+00:00"

_test_current_user: contextvars.ContextVar[UserResponse | None] = contextvars.ContextVar(
    "employee_mobile_test_user",
    default=None,
)


def _completion_event_count(sessions: list[dict[str, Any]], *, employee_id: int) -> int:
    count = 0
    for entry in sessions:
        try:
            completed_by = int(entry.get("completed_by_employee_id") or 0)
        except (TypeError, ValueError):
            completed_by = 0
        if completed_by == employee_id and entry.get("ended_at"):
            count += 1
    return count


def _closed_session_count(sessions: list[dict[str, Any]], *, employee_id: int) -> int:
    return sum(
        1
        for entry in sessions
        if entry.get("ended_at") and int(entry.get("employee_id") or 0) == employee_id
    )


def _active_session_count(sessions: list[dict[str, Any]], *, employee_id: int) -> int:
    return sum(
        1
        for entry in sessions
        if is_session_active(entry) and int(entry.get("employee_id") or 0) == employee_id
    )


async def _load_task_sessions(db_session, order_id: int, task_id: str) -> list[dict[str, Any]]:
    stmt = select(ExecutionReality).where(ExecutionReality.order_id == order_id)
    row = (await db_session.execute(stmt)).scalar_one_or_none()
    assert row is not None
    tasks = json.loads(row.tasks_json or "[]")
    return sessions_for_task(tasks, task_id)


@pytest.fixture
def concurrency_fixture(db_fixture):
    order_id = 92000 + int(uuid.uuid4().hex[:4], 16) % 1000
    task_id = "T-CONC-COMPLETE"
    owner_user = f"conc-owner-{uuid.uuid4().hex[:8]}"
    intruder_user = f"conc-intruder-{uuid.uuid4().hex[:8]}"

    async def _setup():
        async with db_fixture.session_maker() as session:
            owner = await _seed_employee(session, user_id=owner_user, name="Conc Owner")
            intruder = await _seed_employee(session, user_id=intruder_user, name="Conc Intruder")
            await _seed_plan_with_assigned_task(
                session,
                order_id=order_id,
                assigned_employee_id=owner.id,
                task_id=task_id,
            )
            await _seed_reality_task(
                session,
                order_id=order_id,
                task_id=task_id,
                employee_id=owner.id,
                started_at=_FIXTURE_STARTED_AT,
            )
            return {
                "order_id": order_id,
                "task_id": task_id,
                "owner_id": owner.id,
                "owner_user": owner_user,
                "intruder_id": intruder.id,
                "intruder_user": intruder_user,
            }

    ids = db_fixture.run(_setup())
    yield {**ids, "db_fixture": db_fixture}
    _cleanup_overrides()


def _async_client_for(db_fixture) -> AsyncClient:
    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        user = _test_current_user.get()
        if user is None:
            raise RuntimeError("test user context not set")
        return user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _sync_client_for(db_fixture):
    from fastapi.testclient import TestClient

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        user = _test_current_user.get()
        if user is None:
            raise RuntimeError("test user context not set")
        return user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.asyncio
async def test_concurrent_complete_one_close_one_idempotent_response(concurrency_fixture):
    fx = concurrency_fixture
    db_fixture = fx["db_fixture"]
    owner = _user(fx["owner_user"], "employee_mobile")
    barrier = asyncio.Barrier(2)
    started: list[float] = []

    token = _test_current_user.set(owner)
    try:
        async with _async_client_for(db_fixture) as client:

            async def _complete_once():
                await barrier.wait()
                started.append(time.perf_counter())
                return await client.patch(
                    f"/api/v1/employee-mobile/tasks/{fx['task_id']}/complete",
                    json={"order_id": fx["order_id"]},
                )

            r1, r2 = await asyncio.gather(_complete_once(), _complete_once())
    finally:
        _test_current_user.reset(token)
        _cleanup_overrides()

    assert len(started) == 2
    assert max(started) - min(started) < 0.5, "requests did not overlap"
    assert r1.status_code == 200, r1.text
    assert r2.status_code == 200, r2.text
    bodies = [r1.json(), r2.json()]
    assert all(b.get("action") == "complete" for b in bodies)
    assert not any(b.get("already_completed") for b in bodies) or sum(
        1 for b in bodies if b.get("already_completed")
    ) <= 1

    async def _assert_state():
        async with db_fixture.session_maker() as session:
            sessions = await _load_task_sessions(session, fx["order_id"], fx["task_id"])
            assert _active_session_count(sessions, employee_id=fx["owner_id"]) == 0
            assert _closed_session_count(sessions, employee_id=fx["owner_id"]) == 1
            assert _completion_event_count(sessions, employee_id=fx["owner_id"]) == 1
            assert derive_task_status_for_employee(sessions, fx["owner_id"]) == "done"
            assert active_session_for_employee(sessions, fx["owner_id"]) is None

    await _assert_state()


def test_sequential_complete_idempotent(concurrency_fixture):
    fx = concurrency_fixture
    db_fixture = fx["db_fixture"]
    owner = _user(fx["owner_user"], "employee_mobile")
    token = _test_current_user.set(owner)
    client = _sync_client_for(db_fixture)
    try:
        first = client.patch(
            f"/api/v1/employee-mobile/tasks/{fx['task_id']}/complete",
            json={"order_id": fx["order_id"]},
        )
        second = client.patch(
            f"/api/v1/employee-mobile/tasks/{fx['task_id']}/complete",
            json={"order_id": fx["order_id"]},
        )
    finally:
        _test_current_user.reset(token)
        _cleanup_overrides()

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json().get("already_completed") is True

    async def _assert_events():
        async with db_fixture.session_maker() as session:
            sessions = await _load_task_sessions(session, fx["order_id"], fx["task_id"])
            assert _completion_event_count(sessions, employee_id=fx["owner_id"]) == 1

    db_fixture.run(_assert_events())


def test_retry_after_commit_idempotent(concurrency_fixture):
    fx = concurrency_fixture
    db_fixture = fx["db_fixture"]
    owner = _user(fx["owner_user"], "employee_mobile")

    token = _test_current_user.set(owner)
    client = _sync_client_for(db_fixture)
    try:
        first = client.patch(
            f"/api/v1/employee-mobile/tasks/{fx['task_id']}/complete",
            json={"order_id": fx["order_id"]},
        )
    finally:
        _test_current_user.reset(token)
        _cleanup_overrides()
    assert first.status_code == 200, first.text

    token = _test_current_user.set(owner)
    client = _sync_client_for(db_fixture)
    try:
        retry = client.patch(
            f"/api/v1/employee-mobile/tasks/{fx['task_id']}/complete",
            json={"order_id": fx["order_id"]},
        )
    finally:
        _test_current_user.reset(token)
        _cleanup_overrides()

    assert retry.status_code == 200, retry.text
    assert retry.json().get("already_completed") is True

    async def _assert_events():
        async with db_fixture.session_maker() as session:
            sessions = await _load_task_sessions(session, fx["order_id"], fx["task_id"])
            assert _completion_event_count(sessions, employee_id=fx["owner_id"]) == 1

    db_fixture.run(_assert_events())


@pytest.mark.asyncio
async def test_concurrent_owner_and_intruder_only_owner_completes(concurrency_fixture):
    fx = concurrency_fixture
    db_fixture = fx["db_fixture"]
    owner = _user(fx["owner_user"], "employee_mobile")
    intruder = _user(fx["intruder_user"], "employee_mobile")
    barrier = asyncio.Barrier(2)

    async with _async_client_for(db_fixture) as client:

        async def _complete_as(user: UserResponse):
            token = _test_current_user.set(user)
            try:
                await barrier.wait()
                return await client.patch(
                    f"/api/v1/employee-mobile/tasks/{fx['task_id']}/complete",
                    json={"order_id": fx["order_id"]},
                )
            finally:
                _test_current_user.reset(token)

        owner_resp, intruder_resp = await asyncio.gather(
            _complete_as(owner),
            _complete_as(intruder),
        )
    _cleanup_overrides()

    assert owner_resp.status_code == 200, owner_resp.text
    assert intruder_resp.status_code in (403, 422), intruder_resp.text

    async def _assert_state():
        async with db_fixture.session_maker() as session:
            sessions = await _load_task_sessions(session, fx["order_id"], fx["task_id"])
            assert _completion_event_count(sessions, employee_id=fx["owner_id"]) == 1
            assert _completion_event_count(sessions, employee_id=fx["intruder_id"]) == 0

    await _assert_state()


@pytest.mark.asyncio
async def test_truth_stable_after_concurrent_complete(concurrency_fixture):
    fx = concurrency_fixture
    db_fixture = fx["db_fixture"]
    owner = _user(fx["owner_user"], "employee_mobile")
    barrier = asyncio.Barrier(2)
    token = _test_current_user.set(owner)

    try:
        async with _async_client_for(db_fixture) as client:

            async def _complete_once():
                await barrier.wait()
                await client.patch(
                    f"/api/v1/employee-mobile/tasks/{fx['task_id']}/complete",
                    json={"order_id": fx["order_id"]},
                )

            await asyncio.gather(_complete_once(), _complete_once())

            truth = await client.get("/api/v1/employee-mobile/tasks/truth")
            listed = await client.get("/api/v1/employee-mobile/tasks")
    finally:
        _test_current_user.reset(token)
        _cleanup_overrides()

    assert truth.status_code == 200, truth.text
    assert listed.status_code == 200, listed.text
    nested = truth.json().get("tasks") or []
    match = next(
        (t for t in nested if t.get("identity", {}).get("task_id") == fx["task_id"]),
        None,
    )
    assert match is not None
    readiness = match.get("readiness") or {}
    assert readiness.get("can_complete") is False
    flat = next((row for row in listed.json() if row.get("task_id") == fx["task_id"]), None)
    assert flat is not None
    assert flat.get("status") == "done"


@pytest.mark.asyncio
async def test_plan_and_snapshot_unchanged_after_concurrent_complete(concurrency_fixture):
    fx = concurrency_fixture
    db_fixture = fx["db_fixture"]
    owner = _user(fx["owner_user"], "employee_mobile")

    async def _read_plan():
        async with db_fixture.session_maker() as session:
            plan = (
                await session.execute(
                    select(ExecutionPlan).where(ExecutionPlan.order_id == fx["order_id"])
                )
            ).scalar_one()
            return plan.tasks_json, plan.snapshot_version

    plan_json_before, snapshot_before = await _read_plan()

    barrier = asyncio.Barrier(2)
    token = _test_current_user.set(owner)
    try:
        async with _async_client_for(db_fixture) as client:

            async def _complete_once():
                await barrier.wait()
                await client.patch(
                    f"/api/v1/employee-mobile/tasks/{fx['task_id']}/complete",
                    json={"order_id": fx["order_id"]},
                )

            await asyncio.gather(_complete_once(), _complete_once())
    finally:
        _test_current_user.reset(token)
        _cleanup_overrides()

    async def _read_plan_after():
        async with db_fixture.session_maker() as session:
            plan = (
                await session.execute(
                    select(ExecutionPlan).where(ExecutionPlan.order_id == fx["order_id"])
                )
            ).scalar_one()
            return plan.tasks_json, plan.snapshot_version

    plan_json_after, snapshot_after = await _read_plan_after()
    assert plan_json_after == plan_json_before
    assert snapshot_after == snapshot_before
