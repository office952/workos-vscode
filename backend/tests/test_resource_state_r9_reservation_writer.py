"""Resource State R9 — machine reservation writer isolated proofs."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import get_db
from core.sqlite_pragma import register_sqlite_foreign_keys
from dependencies.auth import get_current_user
from main import app
from schemas.auth import UserResponse
from schemas.resource_state_configuration import ResourceDomainConfigurationCommand
from schemas.resource_state_reservation import (
    CancelReservationCommand,
    ConfirmReservationCommand,
    CreateReservationCommand,
    ReleaseReservationCommand,
    SupersedeReservationCommand,
)
from services.execution_task_machine_reservation_command_service import (
    cancel_reservation,
    confirm_reservation,
    create_reservation,
    release_reservation,
    supersede_reservation,
)
from services.execution_task_machine_reservation_repository import (
    FORBIDDEN_MUTATORS,
    ExecutionTaskMachineReservationRepository,
)
from services.resource_domain_configuration_command_service import (
    configure_resource_domain,
)
from services.resource_state_read_service import evaluate_task_resource_state
from services.resource_state_write_common import ResourceStateWriteError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LED_TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters"
OTHER_TASK = "other-task"


def _alembic_cmd(db_async_url: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["ENVIRONMENT"] = "test"
    env["DATABASE_URL"] = db_async_url
    env["JWT_SECRET_KEY"] = "local-dev-secret-not-for-production"
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _async_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.resolve().as_posix()}"


def _window(hours: int = 0):
    start = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc) + timedelta(hours=hours)
    end = start + timedelta(hours=1)
    return start, end


def _user(uid: str, role: str) -> UserResponse:
    return UserResponse(
        id=uid, email=f"{uid}@t.test", name=uid, role=role, last_login=None
    )


@pytest_asyncio.fixture
async def r9_res(tmp_path: Path):
    db = tmp_path / "r9_res.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(sync)
    tasks = {
        "source": "order_snapshot_v2",
        "operational_tasks": [
            {"task_id": LED_TASK, "assigned_employee_id": 7},
            {"task_id": OTHER_TASK, "assigned_employee_id": None},
        ],
    }
    with sync.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO employees "
                "(id, name, status, employee_type, salary_currency, salary_period) "
                "VALUES (7, 'Andrei', 'active', 'internal', 'RON', 'monthly')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, "
                "'2026-08-04 16:00:00', '2026-08-04 16:00:00')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, created_at, updated_at) "
                "VALUES (2, 'CNC-2', 'CNC Two', 'cnc', 'machine', "
                "'active', 1, 1, "
                "'2026-08-04 16:00:00', '2026-08-04 16:00:00')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, created_at, updated_at) "
                "VALUES (3, 'CNC-OFF', 'Offline', 'cnc', 'machine', "
                "'maintenance', 0, 0, "
                "'2026-08-04 16:00:00', '2026-08-04 16:00:00')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO execution_plan "
                "(id, order_id, order_code, snapshot_version, tasks_json, "
                "total_estimated_time_minutes, created_at, updated_at) "
                "VALUES (23, 880750, '880750', 1, :tj, 0.0, "
                "'2026-08-04 16:00:00', '2026-08-04 16:00:00')"
            ),
            {"tj": json.dumps(tasks)},
        )
    sync.dispose()
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _activate_reservation(session: AsyncSession):
    await configure_resource_domain(
        session,
        domain="MACHINE_RESERVATION",
        command=ResourceDomainConfigurationCommand(
            target_status="ACTIVE",
            expected_version=0,
            idempotency_key=str(uuid.uuid4()),
            reason_code="r9_res_activate",
        ),
        actor_user_id="admin-1",
    )
    await session.commit()


def test_repo_forbids_generic_mutators():
    names = {
        n.lower()
        for n in dir(ExecutionTaskMachineReservationRepository)
        if not n.startswith("_")
    }
    for forbidden in FORBIDDEN_MUTATORS:
        assert forbidden not in names


@pytest.mark.asyncio
async def test_inactive_machine_rejected(r9_res: AsyncSession):
    await _activate_reservation(r9_res)
    start, end = _window()
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_reservation(
            r9_res,
            command=CreateReservationCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                machine_id=3,
                reservation_start=start,
                reservation_end=end,
                timezone="UTC",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "machine_not_reservable"
    assert exc.value.http_status == 422


@pytest.mark.asyncio
async def test_reservation_lifecycle_overlap_adjacent(r9_res: AsyncSession):
    await _activate_reservation(r9_res)
    start, end = _window()
    key = str(uuid.uuid4())
    created = await create_reservation(
        r9_res,
        command=CreateReservationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            idempotency_key=key,
        ),
        actor_user_id="admin-1",
    )
    assert created.status == "HELD"
    replay = await create_reservation(
        r9_res,
        command=CreateReservationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            idempotency_key=key,
        ),
        actor_user_id="admin-1",
    )
    assert replay.already_applied is True

    # Overlap conflict on same machine different task
    with pytest.raises(ResourceStateWriteError) as overlap:
        await create_reservation(
            r9_res,
            command=CreateReservationCommand(
                execution_plan_id=23,
                task_key=OTHER_TASK,
                machine_id=1,
                reservation_start=start + timedelta(minutes=30),
                reservation_end=end + timedelta(minutes=30),
                timezone="UTC",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert overlap.value.code == "overlap_conflict"

    # Adjacent end==start allowed
    adj = await create_reservation(
        r9_res,
        command=CreateReservationCommand(
            execution_plan_id=23,
            task_key=OTHER_TASK,
            machine_id=1,
            reservation_start=end,
            reservation_end=end + timedelta(hours=1),
            timezone="UTC",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert adj.status == "HELD"

    # Multi-machine same task allowed
    multi = await create_reservation(
        r9_res,
        command=CreateReservationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            machine_id=2,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert multi.machine_id == 2

    confirmed = await confirm_reservation(
        r9_res,
        reservation_id=created.reservation_id,
        command=ConfirmReservationCommand(
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert confirmed.status == "RESERVED"

    eval_active = await evaluate_task_resource_state(
        r9_res, plan_id=23, task_key=LED_TASK
    )
    assert eval_active.machine_reservation.state == "ACTIVE"
    assert eval_active.aggregate == "BLOCKED_NOT_CONFIGURED"

    released = await release_reservation(
        r9_res,
        reservation_id=created.reservation_id,
        command=ReleaseReservationCommand(
            expected_version=2,
            idempotency_key=str(uuid.uuid4()),
            reason_code="free",
        ),
        actor_user_id="admin-1",
    )
    assert released.status == "RELEASED"

    # Cancel the multi-machine one
    await cancel_reservation(
        r9_res,
        reservation_id=multi.reservation_id,
        command=CancelReservationCommand(
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
            reason_code="abort",
        ),
        actor_user_id="admin-1",
    )
    eval_clear = await evaluate_task_resource_state(
        r9_res, plan_id=23, task_key=LED_TASK
    )
    assert eval_clear.machine_reservation.state == "CLEAR"


@pytest.mark.asyncio
async def test_supersede_and_cas(r9_res: AsyncSession):
    await _activate_reservation(r9_res)
    start, end = _window()
    created = await create_reservation(
        r9_res,
        command=CreateReservationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    with pytest.raises(ResourceStateWriteError) as stale:
        await confirm_reservation(
            r9_res,
            reservation_id=created.reservation_id,
            command=ConfirmReservationCommand(
                expected_version=99,
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert stale.value.code == "cas_stale"

    start2, end2 = _window(2)
    superseded = await supersede_reservation(
        r9_res,
        reservation_id=created.reservation_id,
        command=SupersedeReservationCommand(
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
            replacement_idempotency_key=str(uuid.uuid4()),
            reservation_start=start2,
            reservation_end=end2,
            timezone="UTC",
            reason_code="replace",
        ),
        actor_user_id="admin-1",
    )
    assert superseded.status == "SUPERSEDED"
    assert superseded.replacement_reservation_id is not None


@pytest.mark.asyncio
async def test_concurrent_overlap_one_wins(r9_res: AsyncSession):
    await _activate_reservation(r9_res)
    start, end = _window()

    async def _one(task: str):
        return await create_reservation(
            r9_res,
            command=CreateReservationCommand(
                execution_plan_id=23,
                task_key=task,
                machine_id=1,
                reservation_start=start,
                reservation_end=end,
                timezone="UTC",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )

    results = await asyncio.gather(
        _one(LED_TASK), _one(OTHER_TASK), return_exceptions=True
    )
    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]
    assert len(successes) == 1, results
    assert len(failures) == 1, results
    assert isinstance(failures[0], ResourceStateWriteError)
    assert failures[0].code in {"overlap_conflict", "open_row_conflict"}


@pytest.mark.asyncio
async def test_api_permissions(r9_res: AsyncSession):
    await _activate_reservation(r9_res)
    start, end = _window()

    async def _override_get_db():
        yield r9_res

    app.dependency_overrides[get_db] = _override_get_db
    try:
        for role, expect in (("admin", 200), ("manager", 200), ("operator", 403)):
            user = _user(f"{role}-r9", role)

            async def _u(u=user):
                return u

            app.dependency_overrides[get_current_user] = _u
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.post(
                "/api/v1/execution/resource-state/reservations",
                json={
                    "execution_plan_id": 23,
                    "task_key": LED_TASK if role != "manager" else OTHER_TASK,
                    "machine_id": 1 if role != "manager" else 2,
                    "reservation_start": start.isoformat(),
                    "reservation_end": end.isoformat(),
                    "timezone": "UTC",
                    "idempotency_key": str(uuid.uuid4()),
                },
            )
            assert resp.status_code == expect, (role, resp.status_code, resp.text)
    finally:
        app.dependency_overrides.clear()
