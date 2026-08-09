"""MACHINE_RUN operator read API — isolated proofs (never mutate QA)."""

from __future__ import annotations

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
from schemas.resource_state_machine_run import (
    CompleteMachineRunCommand,
    ConfirmMachineRunCommand,
    CreateMachineRunCommand,
    MachineRunParticipantRef,
    ReleaseMachineRunCommand,
    RemoveMachineRunParticipantCommand,
    StartMachineRunCommand,
)
from services.machine_run_command_service import (
    complete_machine_run,
    confirm_machine_run,
    create_machine_run,
    release_machine_run,
    remove_machine_run_participant,
    start_machine_run,
)
from services.machine_run_read_service import get_machine_run, list_machine_runs
from services.resource_domain_configuration_command_service import (
    configure_resource_domain,
)
from services.resource_state_write_common import ResourceStateNotFoundError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
FACE_A = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_a"
FACE_B = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_b"
FACE_C = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_c"
FACE_D = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_d"


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
    start = datetime(2026, 8, 7, 14, 0, tzinfo=timezone.utc) + timedelta(hours=hours)
    end = start + timedelta(hours=2)
    return start, end


def _user(uid: str, role: str) -> UserResponse:
    return UserResponse(
        id=uid, email=f"{uid}@t.test", name=uid, role=role, last_login=None
    )


def _task(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "source_operation_code": "face_cnc_cut",
        "resource_mode": "MACHINE_BOUND",
        "machine_capability_code": "CNC_ROUTER_CUTTING",
        "batch_eligible": True,
        "workcenter_code": "WC_CNC_ROUTING",
        "assigned_employee_id": None,
    }


@pytest_asyncio.fixture
async def read_db(tmp_path: Path):
    db = tmp_path / "machine_run_read.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(sync)
    with sync.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, capabilities, "
                "created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, '[\"CNC_ROUTER_CUTTING\"]', "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            )
        )
        for pid, oid, tk in (
            (21, 880751, FACE_A),
            (22, 880752, FACE_B),
            (23, 880753, FACE_C),
            (24, 880754, FACE_D),
        ):
            conn.execute(
                text(
                    "INSERT INTO execution_plan "
                    "(id, order_id, order_code, snapshot_version, tasks_json, "
                    "total_estimated_time_minutes, created_at, updated_at) "
                    "VALUES (:id, :oid, :code, 1, :tj, 0.0, "
                    "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
                ),
                {
                    "id": pid,
                    "oid": oid,
                    "code": str(oid),
                    "tj": json.dumps(
                        {
                            "source": "order_snapshot_v2",
                            "operational_tasks": [_task(tk)],
                        }
                    ),
                },
            )
    sync.dispose()
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _activate(session: AsyncSession):
    await configure_resource_domain(
        session,
        domain="MACHINE_RESERVATION",
        command=ResourceDomainConfigurationCommand(
            target_status="ACTIVE",
            expected_version=0,
            idempotency_key=str(uuid.uuid4()),
            reason_code="read_activate",
        ),
        actor_user_id="admin-1",
    )
    await session.commit()


async def _create(
    session: AsyncSession,
    *,
    hours: int = 0,
    participants: list[tuple[int, str]] | None = None,
):
    start, end = _window(hours)
    parts = participants or [
        (21, FACE_A),
        (22, FACE_B),
    ]
    return await create_machine_run(
        session,
        command=CreateMachineRunCommand(
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            participants=[
                MachineRunParticipantRef(execution_plan_id=pid, task_key=tk)
                for pid, tk in parts
            ],
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )


@pytest.mark.asyncio
async def test_list_empty(read_db: AsyncSession):
    result = await list_machine_runs(read_db)
    assert result.count == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_detail_404(read_db: AsyncSession):
    with pytest.raises(ResourceStateNotFoundError) as exc:
        await get_machine_run(read_db, machine_run_id=999)
    assert exc.value.code == "machine_run_not_found"


@pytest.mark.asyncio
async def test_read_after_lifecycle(read_db: AsyncSession):
    await _activate(read_db)
    created = await _create(read_db)
    run_id = created.machine_run_id

    listed = await list_machine_runs(read_db)
    assert listed.count == 1
    item = listed.items[0]
    assert item.machine_run_id == run_id
    assert item.status == "HELD"
    assert item.reservation_status == "HELD"
    assert item.machine_code == "CNC-1"
    assert item.machine_name == "CNC One"
    assert item.active_participant_count == 2
    assert item.total_participant_count == 2
    assert item.execution_plan_ids == [21, 22]
    assert item.order_ids == [880751, 880752]
    assert item.version == 1
    assert item.reservation_version == 1

    detail = await get_machine_run(read_db, machine_run_id=run_id)
    assert detail.status == "HELD"
    assert detail.machine.machine_code == "CNC-1"
    assert "CNC_ROUTER_CUTTING" in detail.machine.capabilities
    assert detail.reservation.status == "HELD"
    assert detail.version == 1
    assert detail.reservation.version == 1
    assert {p.execution_plan_id for p in detail.participants} == {21, 22}
    assert all(p.status == "ACTIVE" for p in detail.participants)
    assert all(p.operation_code == "face_cnc_cut" for p in detail.participants)
    assert all(p.machine_capability_code == "CNC_ROUTER_CUTTING" for p in detail.participants)
    assert all(p.batch_eligible is True for p in detail.participants)
    assert detail.started_at is None
    assert detail.completed_at is None
    assert detail.actual_runtime_seconds is None

    await confirm_machine_run(
        read_db,
        machine_run_id=run_id,
        command=ConfirmMachineRunCommand(
            expected_version=1, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    d2 = await get_machine_run(read_db, machine_run_id=run_id)
    assert d2.status == "RESERVED"
    assert d2.reservation.status == "RESERVED"
    assert d2.version == 2
    assert d2.reservation.version == 2

    await start_machine_run(
        read_db,
        machine_run_id=run_id,
        command=StartMachineRunCommand(
            expected_version=2, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    d3 = await get_machine_run(read_db, machine_run_id=run_id)
    assert d3.status == "RUNNING"
    assert d3.reservation.status == "RESERVED"
    assert d3.started_at is not None
    assert d3.completed_at is None
    assert d3.version == 3

    await complete_machine_run(
        read_db,
        machine_run_id=run_id,
        command=CompleteMachineRunCommand(
            expected_version=3, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    d4 = await get_machine_run(read_db, machine_run_id=run_id)
    assert d4.status == "COMPLETED"
    assert d4.reservation.status == "RESERVED"
    assert d4.started_at is not None
    assert d4.completed_at is not None
    assert d4.actual_runtime_seconds is not None
    assert d4.actual_runtime_seconds >= 0
    assert d4.version == 4

    open_list = await list_machine_runs(read_db, open_only=True)
    assert open_list.count == 1
    assert open_list.items[0].status == "COMPLETED"
    assert open_list.items[0].reservation_status == "RESERVED"

    await release_machine_run(
        read_db,
        machine_run_id=run_id,
        command=ReleaseMachineRunCommand(
            expected_version=4, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    d5 = await get_machine_run(read_db, machine_run_id=run_id)
    assert d5.status == "RELEASED"
    assert d5.reservation.status == "RELEASED"
    assert d5.started_at is not None
    assert d5.completed_at is not None
    assert d5.active_participant_count == 0
    assert d5.total_participant_count == 2
    assert all(p.status == "REMOVED" for p in d5.participants)

    closed = await list_machine_runs(read_db, open_only=True)
    assert closed.count == 0


@pytest.mark.asyncio
async def test_removed_participant_and_multi_plan(read_db: AsyncSession):
    await _activate(read_db)
    created = await _create(
        read_db,
        participants=[(21, FACE_A), (22, FACE_B), (23, FACE_C)],
    )
    run_id = created.machine_run_id
    await remove_machine_run_participant(
        read_db,
        machine_run_id=run_id,
        command=RemoveMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    detail = await get_machine_run(read_db, machine_run_id=run_id)
    by_plan = {p.execution_plan_id: p for p in detail.participants}
    assert by_plan[21].status == "ACTIVE"
    assert by_plan[22].status == "ACTIVE"
    assert by_plan[23].status == "REMOVED"
    assert by_plan[23].removed_at is not None
    assert detail.active_participant_count == 2
    assert detail.total_participant_count == 3
    assert detail.execution_plan_ids == [21, 22]
    assert detail.order_ids == [880751, 880752]
    # Full multi-plan provenance still present on participants
    assert {p.execution_plan_id for p in detail.participants} == {21, 22, 23}
    assert {p.order_id for p in detail.participants} == {880751, 880752, 880753}

    listed = await list_machine_runs(read_db, execution_plan_id=23)
    assert listed.count == 1
    assert listed.items[0].active_participant_count == 2
    assert listed.items[0].total_participant_count == 3


@pytest.mark.asyncio
async def test_list_filters_and_sort(read_db: AsyncSession):
    await _activate(read_db)
    a = await _create(read_db, hours=0, participants=[(21, FACE_A), (22, FACE_B)])
    b = await _create(read_db, hours=3, participants=[(23, FACE_C), (24, FACE_D)])
    await confirm_machine_run(
        read_db,
        machine_run_id=a.machine_run_id,
        command=ConfirmMachineRunCommand(
            expected_version=1, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    held = await list_machine_runs(read_db, status="HELD")
    assert held.count == 1
    assert held.items[0].machine_run_id == b.machine_run_id
    by_machine = await list_machine_runs(read_db, machine_id=1)
    assert by_machine.count == 2
    # open first: both open; earlier reservation_start first
    assert by_machine.items[0].machine_run_id == a.machine_run_id
    assert by_machine.items[1].machine_run_id == b.machine_run_id


@pytest.mark.asyncio
async def test_http_read_permission_and_qa_empty(tmp_path: Path):
    db = tmp_path / "read_http.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_db
    try:
        app.dependency_overrides[get_current_user] = lambda: _user("sales-1", "sales")
        with TestClient(app) as client:
            denied = client.get("/api/v1/execution/resource-state/machine-runs")
            assert denied.status_code == 403

        app.dependency_overrides[get_current_user] = lambda: _user("op-1", "operator")
        with TestClient(app) as client:
            empty = client.get("/api/v1/execution/resource-state/machine-runs")
            assert empty.status_code == 200, empty.text
            body = empty.json()
            assert body["count"] == 0
            assert body["items"] == []
            missing = client.get("/api/v1/execution/resource-state/machine-runs/999")
            assert missing.status_code == 404
            assert missing.json()["detail"]["error"] == "machine_run_not_found"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        await engine.dispose()
