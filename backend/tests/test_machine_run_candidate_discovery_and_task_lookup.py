"""MACHINE_RUN candidate discovery + task→active lookup — isolated (never QA)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import get_db
from core.sqlite_pragma import register_sqlite_foreign_keys
from dependencies.auth import get_current_user
from main import app
from models.machine_run import MachineRunParticipant
from schemas.auth import UserResponse
from schemas.resource_state_configuration import ResourceDomainConfigurationCommand
from schemas.resource_state_machine_run import (
    AddMachineRunParticipantCommand,
    ConfirmMachineRunCommand,
    CreateMachineRunCommand,
    MachineRunParticipantRef,
    ReleaseMachineRunCommand,
    RemoveMachineRunParticipantCommand,
    StartMachineRunCommand,
)
from services.machine_run_candidate_service import (
    list_add_candidates,
    list_create_candidates,
    lookup_active_machine_run_by_task,
)
from services.machine_run_command_service import (
    add_machine_run_participant,
    confirm_machine_run,
    create_machine_run,
    release_machine_run,
    remove_machine_run_participant,
    start_machine_run,
)
from services.resource_domain_configuration_command_service import (
    configure_resource_domain,
)
from services.resource_state_write_common import ResourceStateWriteError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
FACE_A = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_a"
FACE_B = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_b"
FACE_C = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_c"
FACE_D = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_d"
FACE_PAINT = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:paint_a"


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
    start = datetime(2026, 8, 9, 8, 0, tzinfo=timezone.utc) + timedelta(hours=hours)
    end = start + timedelta(hours=2)
    return start, end


def _user(uid: str, role: str) -> UserResponse:
    return UserResponse(
        id=uid, email=f"{uid}@t.test", name=uid, role=role, last_login=None
    )


def _task(
    task_id: str,
    *,
    resource_mode: str = "MACHINE_BOUND",
    capability: str = "CNC_ROUTER_CUTTING",
    batch_eligible: bool | None = True,
) -> dict:
    row = {
        "task_id": task_id,
        "source_operation_code": "face_cnc_cut",
        "resource_mode": resource_mode,
        "machine_capability_code": capability,
        "workcenter_code": "WC_CNC_ROUTING",
        "assigned_employee_id": None,
    }
    if batch_eligible is not None:
        row["batch_eligible"] = batch_eligible
    return row


@pytest_asyncio.fixture
async def cand_db(tmp_path: Path):
    db = tmp_path / "machine_run_candidates.db"
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
                "'2026-08-09 10:00:00', '2026-08-09 10:00:00')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, capabilities, "
                "created_at, updated_at) "
                "VALUES (2, 'LASER-1', 'Laser One', 'laser', 'machine', "
                "'active', 1, 1, '[\"LASER_CUT\"]', "
                "'2026-08-09 10:00:00', '2026-08-09 10:00:00')"
            )
        )
        plans = (
            (21, 880751, FACE_A, _task(FACE_A)),
            (22, 880752, FACE_B, _task(FACE_B)),
            (23, 880753, FACE_C, _task(FACE_C)),
            (24, 880754, FACE_D, _task(FACE_D)),
            (
                25,
                880755,
                FACE_PAINT,
                _task(
                    FACE_PAINT,
                    resource_mode="EMPLOYEE_BOUND",
                    capability="PAINT",
                    batch_eligible=False,
                ),
            ),
            (
                26,
                880756,
                FACE_A + "_nobatch",
                _task(FACE_A + "_nobatch", batch_eligible=False),
            ),
            (
                27,
                880757,
                FACE_A + "_laser",
                _task(FACE_A + "_laser", capability="LASER_CUT"),
            ),
        )
        for pid, oid, _tk, task in plans:
            conn.execute(
                text(
                    "INSERT INTO execution_plan "
                    "(id, order_id, order_code, snapshot_version, tasks_json, "
                    "total_estimated_time_minutes, created_at, updated_at) "
                    "VALUES (:id, :oid, :code, 1, :tj, 0.0, "
                    "'2026-08-09 10:00:00', '2026-08-09 10:00:00')"
                ),
                {
                    "id": pid,
                    "oid": oid,
                    "code": str(oid),
                    "tj": json.dumps(
                        {
                            "source": "order_snapshot_v2",
                            "operational_tasks": [task],
                        }
                    ),
                },
            )
    sync.dispose()
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await configure_resource_domain(
            session,
            domain="MACHINE_RESERVATION",
            command=ResourceDomainConfigurationCommand(
                target_status="ACTIVE",
                expected_version=0,
                idempotency_key=str(uuid.uuid4()),
                reason_code="cand_activate",
            ),
            actor_user_id="admin-1",
        )
        await session.commit()
        yield session
    await engine.dispose()


async def _create_ab(session: AsyncSession, hour: int = 0):
    start, end = _window(hour)
    return await create_machine_run(
        session,
        command=CreateMachineRunCommand(
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="Europe/Bucharest",
            participants=[
                MachineRunParticipantRef(execution_plan_id=21, task_key=FACE_A),
                MachineRunParticipantRef(execution_plan_id=22, task_key=FACE_B),
            ],
            idempotency_key=str(uuid.uuid4()),
            reason_code="cand_create",
        ),
        actor_user_id="admin-1",
    )


@pytest.mark.asyncio
async def test_create_candidates_filters_and_excludes_active(cand_db: AsyncSession):
    before = await list_create_candidates(cand_db, machine_id=1)
    keys = {(c.execution_plan_id, c.task_key) for c in before.items}
    assert (21, FACE_A) in keys
    assert (22, FACE_B) in keys
    assert (23, FACE_C) in keys
    assert (25, FACE_PAINT) not in keys  # not MACHINE_BOUND
    assert (26, FACE_A + "_nobatch") not in keys
    assert (27, FACE_A + "_laser") not in keys  # wrong machine capability

    created = await _create_ab(cand_db)
    await cand_db.commit()

    after = await list_create_candidates(cand_db, machine_id=1)
    after_keys = {(c.execution_plan_id, c.task_key) for c in after.items}
    assert (21, FACE_A) not in after_keys
    assert (22, FACE_B) not in after_keys
    assert (23, FACE_C) in after_keys

    lookup_a = await lookup_active_machine_run_by_task(
        cand_db, execution_plan_id=21, task_key=FACE_A
    )
    assert lookup_a.membership is not None
    assert lookup_a.membership.machine_run_id == created.machine_run_id
    assert lookup_a.membership.status == "HELD"


@pytest.mark.asyncio
async def test_add_candidates_held_only_and_remove_reeligibility(cand_db: AsyncSession):
    created = await _create_ab(cand_db)
    await cand_db.commit()

    addable = await list_add_candidates(cand_db, machine_run_id=created.machine_run_id)
    assert addable.mutation_allowed is True
    assert addable.required_capability == "CNC_ROUTER_CUTTING"
    add_keys = {(c.execution_plan_id, c.task_key) for c in addable.items}
    assert (23, FACE_C) in add_keys
    assert (21, FACE_A) not in add_keys

    added = await add_machine_run_participant(
        cand_db,
        machine_run_id=created.machine_run_id,
        command=AddMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=created.version,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    await cand_db.commit()

    lookup_c = await lookup_active_machine_run_by_task(
        cand_db, execution_plan_id=23, task_key=FACE_C
    )
    assert lookup_c.membership is not None
    assert lookup_c.membership.machine_run_id == created.machine_run_id

    after_add = await list_add_candidates(
        cand_db, machine_run_id=created.machine_run_id
    )
    assert (23, FACE_C) not in {
        (c.execution_plan_id, c.task_key) for c in after_add.items
    }

    removed = await remove_machine_run_participant(
        cand_db,
        machine_run_id=created.machine_run_id,
        command=RemoveMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=added.version,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    await cand_db.commit()
    assert removed.status == "HELD"

    lookup_removed = await lookup_active_machine_run_by_task(
        cand_db, execution_plan_id=23, task_key=FACE_C
    )
    assert lookup_removed.membership is None

    reeligible = await list_add_candidates(
        cand_db, machine_run_id=created.machine_run_id
    )
    assert (23, FACE_C) in {
        (c.execution_plan_id, c.task_key) for c in reeligible.items
    }

    confirmed = await confirm_machine_run(
        cand_db,
        machine_run_id=created.machine_run_id,
        command=ConfirmMachineRunCommand(
            expected_version=removed.version,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    await cand_db.commit()
    reserved_cands = await list_add_candidates(
        cand_db, machine_run_id=confirmed.machine_run_id
    )
    assert reserved_cands.mutation_allowed is False
    assert reserved_cands.reason_code == "invalid_transition"
    assert reserved_cands.count == 0


@pytest.mark.asyncio
async def test_lookup_running_and_released_excluded(cand_db: AsyncSession):
    created = await _create_ab(cand_db, hour=0)
    await cand_db.commit()
    confirmed = await confirm_machine_run(
        cand_db,
        machine_run_id=created.machine_run_id,
        command=ConfirmMachineRunCommand(
            expected_version=created.version,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    await cand_db.commit()
    await start_machine_run(
        cand_db,
        machine_run_id=confirmed.machine_run_id,
        command=StartMachineRunCommand(
            expected_version=confirmed.version,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    await cand_db.commit()
    running_lookup = await lookup_active_machine_run_by_task(
        cand_db, execution_plan_id=21, task_key=FACE_A
    )
    assert running_lookup.membership is not None
    assert running_lookup.membership.status == "RUNNING"

    # Separate multi-order run C+D → confirm → release → lookup none
    start, end = _window(4)
    other = await create_machine_run(
        cand_db,
        command=CreateMachineRunCommand(
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="Europe/Bucharest",
            participants=[
                MachineRunParticipantRef(execution_plan_id=23, task_key=FACE_C),
                MachineRunParticipantRef(execution_plan_id=24, task_key=FACE_D),
            ],
            idempotency_key=str(uuid.uuid4()),
            reason_code="cand_create2",
        ),
        actor_user_id="admin-1",
    )
    await cand_db.commit()
    conf2 = await confirm_machine_run(
        cand_db,
        machine_run_id=other.machine_run_id,
        command=ConfirmMachineRunCommand(
            expected_version=other.version,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    await cand_db.commit()
    held_lookup = await lookup_active_machine_run_by_task(
        cand_db, execution_plan_id=23, task_key=FACE_C
    )
    assert held_lookup.membership is not None
    assert held_lookup.membership.status == "RESERVED"

    rel = await release_machine_run(
        cand_db,
        machine_run_id=conf2.machine_run_id,
        command=ReleaseMachineRunCommand(
            expected_version=conf2.version,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    await cand_db.commit()
    assert rel.status == "RELEASED"
    term_lookup = await lookup_active_machine_run_by_task(
        cand_db, execution_plan_id=23, task_key=FACE_C
    )
    assert term_lookup.membership is None


@pytest.mark.asyncio
async def test_writer_parity_create_accepts_candidates(cand_db: AsyncSession):
    cands = await list_create_candidates(cand_db, machine_id=1)
    assert cands.count >= 2
    a, b = cands.items[0], cands.items[1]
    start, end = _window(12)
    result = await create_machine_run(
        cand_db,
        command=CreateMachineRunCommand(
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="Europe/Bucharest",
            participants=[
                MachineRunParticipantRef(
                    execution_plan_id=a.execution_plan_id, task_key=a.task_key
                ),
                MachineRunParticipantRef(
                    execution_plan_id=b.execution_plan_id, task_key=b.task_key
                ),
            ],
            idempotency_key=str(uuid.uuid4()),
            reason_code="parity_create",
        ),
        actor_user_id="admin-1",
    )
    await cand_db.commit()
    assert result.status == "HELD"


@pytest.mark.asyncio
async def test_writer_parity_add_accepts_candidate(cand_db: AsyncSession):
    created = await _create_ab(cand_db, hour=16)
    await cand_db.commit()
    cands = await list_add_candidates(cand_db, machine_run_id=created.machine_run_id)
    assert cands.count >= 1
    pick = cands.items[0]
    added = await add_machine_run_participant(
        cand_db,
        machine_run_id=created.machine_run_id,
        command=AddMachineRunParticipantCommand(
            execution_plan_id=pick.execution_plan_id,
            task_key=pick.task_key,
            expected_version=created.version,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    await cand_db.commit()
    assert added.status == "HELD"


@pytest.mark.asyncio
async def test_uniqueness_integrity_conflict(cand_db: AsyncSession, monkeypatch):
    p1 = MachineRunParticipant(
        id=1,
        machine_run_id=10,
        execution_plan_id=21,
        order_id=1,
        task_key=FACE_A,
        status="ACTIVE",
    )
    p2 = MachineRunParticipant(
        id=2,
        machine_run_id=11,
        execution_plan_id=21,
        order_id=1,
        task_key=FACE_A,
        status="ACTIVE",
    )
    monkeypatch.setattr(
        "services.machine_run_candidate_service.find_all_active_memberships",
        AsyncMock(return_value=[p1, p2]),
    )
    with pytest.raises(ResourceStateWriteError) as exc:
        await lookup_active_machine_run_by_task(
            cand_db, execution_plan_id=21, task_key=FACE_A
        )
    assert exc.value.code == "integrity_conflict"


@pytest.mark.asyncio
async def test_http_candidates_lookup_and_permission(cand_db: AsyncSession, tmp_path: Path):
    """HTTP routes share the isolated cand_db engine via dependency override."""
    # Re-bind get_db to the same session factory behind cand_db is hard;
    # exercise routes against a fresh engine cloned from alembic + seed.
    db = tmp_path / "http_cand2.db"
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
                "'2026-08-09 10:00:00', '2026-08-09 10:00:00')"
            )
        )
        for pid, oid, tk in ((21, 880751, FACE_A), (22, 880752, FACE_B)):
            conn.execute(
                text(
                    "INSERT INTO execution_plan "
                    "(id, order_id, order_code, snapshot_version, tasks_json, "
                    "total_estimated_time_minutes, created_at, updated_at) "
                    "VALUES (:id, :oid, :code, 1, :tj, 0.0, "
                    "'2026-08-09 10:00:00', '2026-08-09 10:00:00')"
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
        await configure_resource_domain(
            session,
            domain="MACHINE_RESERVATION",
            command=ResourceDomainConfigurationCommand(
                target_status="ACTIVE",
                expected_version=0,
                idempotency_key=str(uuid.uuid4()),
                reason_code="http_cand",
            ),
            actor_user_id="admin-1",
        )
        await session.commit()

    async def _override_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: _user("admin-1", "admin")
    try:
        with TestClient(app) as client:
            r = client.get(
                "/api/v1/execution/resource-state/machine-runs/candidates",
                params={"machine_id": 1},
            )
            assert r.status_code == 200, r.text
            assert r.json()["count"] >= 2

            r2 = client.get(
                "/api/v1/execution/resource-state/machine-runs/by-task",
                params={"execution_plan_id": 21, "task_key": FACE_A},
            )
            assert r2.status_code == 200
            assert r2.json()["membership"] is None

            app.dependency_overrides[get_current_user] = lambda: _user(
                "sales-1", "sales"
            )
            denied = client.get(
                "/api/v1/execution/resource-state/machine-runs/candidates",
                params={"machine_id": 1},
            )
            assert denied.status_code == 403
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

