"""RESCHEDULE_MACHINE_RUN — isolated DB proofs (never QA)."""

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
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import get_db
from core.sqlite_pragma import register_sqlite_foreign_keys
from dependencies.auth import get_current_user
from main import app
from models.execution_task_machine_reservation import (
    ExecutionTaskMachineReservation,
    ExecutionTaskMachineReservationTransition,
)
from models.machine_run import MachineRun, MachineRunParticipant, MachineRunTransition
from schemas.auth import UserResponse
from schemas.resource_state_configuration import ResourceDomainConfigurationCommand
from schemas.resource_state_machine_run import (
    CancelMachineRunCommand,
    ConfirmMachineRunCommand,
    CreateMachineRunCommand,
    MachineRunParticipantRef,
    ReleaseMachineRunCommand,
    RescheduleMachineRunCommand,
)
from services.machine_run_command_service import (
    cancel_machine_run,
    confirm_machine_run,
    create_machine_run,
    release_machine_run,
    reschedule_machine_run,
)
from services.resource_domain_configuration_command_service import (
    configure_resource_domain,
)
from services.resource_state_read_service import evaluate_task_resource_state
from services.resource_state_write_common import ResourceStateWriteError, dt_key

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
    start = datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc) + timedelta(hours=hours)
    end = start + timedelta(hours=1)
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
        "assigned_employee_id": None,
    }


@pytest_asyncio.fixture
async def rs_db(tmp_path: Path):
    db = tmp_path / "reschedule_machine_run.db"
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
                "operational_status, is_available, is_active, "
                "created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            )
        )
        for pid, oid, tasks in (
            (21, 880751, [FACE_A, FACE_C]),
            (22, 880752, [FACE_B, FACE_D]),
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
                            "operational_tasks": [_task(t) for t in tasks],
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
            reason_code="rs_activate",
        ),
        actor_user_id="admin-1",
    )
    await session.commit()


async def _counts(session: AsyncSession) -> dict[str, int]:
    return {
        "runs": int(
            (
                await session.execute(select(func.count()).select_from(MachineRun))
            ).scalar_one()
        ),
        "participants": int(
            (
                await session.execute(
                    select(func.count()).select_from(MachineRunParticipant)
                )
            ).scalar_one()
        ),
        "run_transitions": int(
            (
                await session.execute(
                    select(func.count()).select_from(MachineRunTransition)
                )
            ).scalar_one()
        ),
        "reservations": int(
            (
                await session.execute(
                    select(func.count()).select_from(ExecutionTaskMachineReservation)
                )
            ).scalar_one()
        ),
        "reservation_transitions": int(
            (
                await session.execute(
                    select(func.count()).select_from(
                        ExecutionTaskMachineReservationTransition
                    )
                )
            ).scalar_one()
        ),
    }


def _part_fp(parts) -> list[tuple[int, str, int, str]]:
    return sorted(
        [(p.execution_plan_id, p.task_key, p.order_id, p.status) for p in parts],
        key=lambda x: (x[0], x[1]),
    )


async def _create(
    session: AsyncSession,
    *,
    hours: int = 0,
    parts: list[tuple[int, str]] | None = None,
):
    start, end = _window(hours)
    participants = parts or [(21, FACE_A), (22, FACE_B)]
    return await create_machine_run(
        session,
        command=CreateMachineRunCommand(
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            participants=[
                MachineRunParticipantRef(execution_plan_id=pid, task_key=tk)
                for pid, tk in participants
            ],
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )


async def _r6(session: AsyncSession, parts=((21, FACE_A), (22, FACE_B))):
    out = []
    for plan_id, task_key in parts:
        state = await evaluate_task_resource_state(
            session, plan_id=plan_id, task_key=task_key
        )
        out.append(state.machine_reservation.state)
    return tuple(out)


@pytest.mark.asyncio
async def test_reschedule_held_happy_path(rs_db: AsyncSession):
    await _activate(rs_db)
    created = await _create(rs_db, hours=0)
    assert created.status == "HELD"
    assert await _r6(rs_db) == ("ACTIVE", "ACTIVE")
    parts = _part_fp(created.participants)
    before = await _counts(rs_db)
    new_start, new_end = _window(hours=2)

    moved = await reschedule_machine_run(
        rs_db,
        machine_run_id=created.machine_run_id,
        command=RescheduleMachineRunCommand(
            reservation_start=new_start,
            reservation_end=new_end,
            timezone="UTC",
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert moved.machine_run_id == created.machine_run_id
    assert moved.reservation_id == created.reservation_id
    assert moved.machine_id == created.machine_id
    assert moved.status == "HELD"
    assert moved.reservation_status == "HELD"
    assert moved.version == 2
    assert moved.reservation_version == 2
    assert moved.operation == "RESCHEDULE_MACHINE_RUN"
    assert dt_key(moved.reservation_start) == dt_key(new_start)
    assert dt_key(moved.reservation_end) == dt_key(new_end)
    assert _part_fp(moved.participants) == parts
    assert await _r6(rs_db) == ("ACTIVE", "ACTIVE")
    after = await _counts(rs_db)
    assert after["run_transitions"] == before["run_transitions"] + 1
    assert after["reservation_transitions"] == before["reservation_transitions"] + 1
    assert after["participants"] == before["participants"]
    assert after["runs"] == before["runs"]
    assert after["reservations"] == before["reservations"]

    res_tr = (
        await rs_db.execute(
            select(ExecutionTaskMachineReservationTransition).where(
                ExecutionTaskMachineReservationTransition.reservation_id
                == moved.reservation_id,
                ExecutionTaskMachineReservationTransition.operation
                == "RESCHEDULE_RESERVATION",
            )
        )
    ).scalar_one()
    assert dt_key(res_tr.previous_start) == dt_key(created.reservation_start)
    assert dt_key(res_tr.previous_end) == dt_key(created.reservation_end)
    assert dt_key(res_tr.new_start) == dt_key(new_start)
    assert dt_key(res_tr.new_end) == dt_key(new_end)
    assert res_tr.previous_status == "HELD"
    assert res_tr.new_status == "HELD"


@pytest.mark.asyncio
async def test_reschedule_reserved_happy_path(rs_db: AsyncSession):
    await _activate(rs_db)
    created = await _create(rs_db, hours=0)
    await confirm_machine_run(
        rs_db,
        machine_run_id=created.machine_run_id,
        command=ConfirmMachineRunCommand(
            expected_version=1, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    new_start, new_end = _window(hours=4)
    moved = await reschedule_machine_run(
        rs_db,
        machine_run_id=created.machine_run_id,
        command=RescheduleMachineRunCommand(
            reservation_start=new_start,
            reservation_end=new_end,
            timezone="UTC",
            expected_version=2,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert moved.status == "RESERVED"
    assert moved.reservation_status == "RESERVED"
    assert moved.version == 3
    assert await _r6(rs_db) == ("ACTIVE", "ACTIVE")


@pytest.mark.asyncio
async def test_overlap_self_excluded_and_frees_old_window(rs_db: AsyncSession):
    await _activate(rs_db)
    run_a = await _create(rs_db, hours=0, parts=[(21, FACE_A), (22, FACE_B)])
    # Overlapping create for same machine must conflict.
    with pytest.raises(ResourceStateWriteError) as exc:
        await _create(rs_db, hours=0, parts=[(21, FACE_C), (22, FACE_D)])
    assert exc.value.code == "overlap_conflict"

    await reschedule_machine_run(
        rs_db,
        machine_run_id=run_a.machine_run_id,
        command=RescheduleMachineRunCommand(
            reservation_start=_window(hours=2)[0],
            reservation_end=_window(hours=2)[1],
            timezone="UTC",
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    # Old window now free for another run.
    run_b = await _create(rs_db, hours=0, parts=[(21, FACE_C), (22, FACE_D)])
    assert run_b.status == "HELD"
    assert run_b.machine_run_id != run_a.machine_run_id


@pytest.mark.asyncio
async def test_idempotency_replay_and_conflict(rs_db: AsyncSession):
    await _activate(rs_db)
    created = await _create(rs_db)
    key = str(uuid.uuid4())
    start, end = _window(hours=3)
    first = await reschedule_machine_run(
        rs_db,
        machine_run_id=created.machine_run_id,
        command=RescheduleMachineRunCommand(
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            expected_version=1,
            idempotency_key=key,
        ),
        actor_user_id="admin-1",
    )
    mid = await _counts(rs_db)
    second = await reschedule_machine_run(
        rs_db,
        machine_run_id=created.machine_run_id,
        command=RescheduleMachineRunCommand(
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            expected_version=1,
            idempotency_key=key,
        ),
        actor_user_id="admin-1",
    )
    assert second.already_applied is True
    assert second.machine_run_id == first.machine_run_id
    assert await _counts(rs_db) == mid

    other_start, other_end = _window(hours=5)
    with pytest.raises(ResourceStateWriteError) as exc:
        await reschedule_machine_run(
            rs_db,
            machine_run_id=created.machine_run_id,
            command=RescheduleMachineRunCommand(
                reservation_start=other_start,
                reservation_end=other_end,
                timezone="UTC",
                expected_version=1,
                idempotency_key=key,
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "idempotency_payload_conflict"
    assert await _counts(rs_db) == mid


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "setup,code",
    [
        ("released", "invalid_transition"),
        ("cancelled", "invalid_transition"),
        ("stale", "cas_stale"),
        ("bad_window", "invalid_time_window"),
        ("mismatch", "run_reservation_state_mismatch"),
    ],
)
async def test_negative_reschedule(rs_db: AsyncSession, setup, code):
    await _activate(rs_db)
    created = await _create(rs_db)
    run_id = created.machine_run_id
    ver = 1
    if setup == "released":
        await confirm_machine_run(
            rs_db,
            machine_run_id=run_id,
            command=ConfirmMachineRunCommand(
                expected_version=1, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        await release_machine_run(
            rs_db,
            machine_run_id=run_id,
            command=ReleaseMachineRunCommand(
                expected_version=2, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        ver = 3
    elif setup == "cancelled":
        await cancel_machine_run(
            rs_db,
            machine_run_id=run_id,
            command=CancelMachineRunCommand(
                expected_version=1, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        ver = 2
    elif setup == "mismatch":
        await rs_db.execute(
            text(
                "UPDATE execution_task_machine_reservations "
                "SET status='RESERVED' WHERE machine_run_id=:rid"
            ),
            {"rid": run_id},
        )
        await rs_db.commit()

    before = await _counts(rs_db)
    start, end = _window(hours=6)
    if setup == "bad_window":
        start, end = end, start  # inverted

    with pytest.raises(ResourceStateWriteError) as exc:
        await reschedule_machine_run(
            rs_db,
            machine_run_id=run_id,
            command=RescheduleMachineRunCommand(
                reservation_start=start,
                reservation_end=end,
                timezone="UTC",
                expected_version=99 if setup == "stale" else ver,
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == code
    assert await _counts(rs_db) == before


@pytest.mark.asyncio
async def test_domain_disabled_rejects_reschedule(rs_db: AsyncSession):
    await _activate(rs_db)
    created = await _create(rs_db)
    await cancel_machine_run(
        rs_db,
        machine_run_id=created.machine_run_id,
        command=CancelMachineRunCommand(
            expected_version=1, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    cfg = (
        await rs_db.execute(
            text(
                "SELECT version FROM resource_domain_configurations "
                "WHERE domain='MACHINE_RESERVATION'"
            )
        )
    ).fetchone()
    assert cfg is not None
    await configure_resource_domain(
        rs_db,
        domain="MACHINE_RESERVATION",
        command=ResourceDomainConfigurationCommand(
            target_status="DISABLED",
            expected_version=int(cfg[0]),
            idempotency_key=str(uuid.uuid4()),
            reason_code="rs_disable",
        ),
        actor_user_id="admin-1",
    )
    await rs_db.commit()
    # Seed HELD while DISABLED (bypass CREATE gate) — same pattern as lifecycle suite.
    await rs_db.execute(
        text(
            "INSERT INTO machine_runs "
            "(id, machine_id, status, version, timezone, created_at, updated_at, "
            "idempotency_key) "
            "VALUES (99, 1, 'HELD', 1, 'UTC', '2026-08-07 15:00:00', "
            "'2026-08-07 15:00:00', :ik)"
        ),
        {"ik": str(uuid.uuid4())},
    )
    await rs_db.execute(
        text(
            "INSERT INTO execution_task_machine_reservations "
            "(id, machine_run_id, machine_id, reservation_start, reservation_end, "
            "timezone, status, version, created_at, updated_at, idempotency_key) "
            "VALUES (99, 99, 1, '2026-08-07 16:00:00', '2026-08-07 18:00:00', "
            "'UTC', 'HELD', 1, '2026-08-07 15:00:00', '2026-08-07 15:00:00', :ik)"
        ),
        {"ik": str(uuid.uuid4())},
    )
    await rs_db.commit()
    before = await _counts(rs_db)
    start, end = _window(hours=9)
    with pytest.raises(ResourceStateWriteError) as exc:
        await reschedule_machine_run(
            rs_db,
            machine_run_id=99,
            command=RescheduleMachineRunCommand(
                reservation_start=start,
                reservation_end=end,
                timezone="UTC",
                expected_version=1,
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "domain_disabled"
    assert await _counts(rs_db) == before


@pytest.mark.asyncio
async def test_http_permission(tmp_path: Path):
    db = tmp_path / "rs_http.db"
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
                "operational_status, is_available, is_active, "
                "created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            )
        )
        for pid, oid, tk in ((21, 880751, FACE_A), (22, 880752, FACE_B)):
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
        await _activate(session)
        created = await _create(session)

    async def _override_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_db
    try:
        start, end = _window(hours=8)
        body = {
            "reservation_start": start.isoformat(),
            "reservation_end": end.isoformat(),
            "timezone": "UTC",
            "expected_version": 1,
            "idempotency_key": str(uuid.uuid4()),
        }
        app.dependency_overrides[get_current_user] = lambda: _user("op-1", "operator")
        with TestClient(app) as client:
            denied = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/reschedule",
                json=body,
            )
            assert denied.status_code == 403

        app.dependency_overrides[get_current_user] = lambda: _user("admin-1", "admin")
        with TestClient(app) as client:
            ok = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/reschedule",
                json=body,
            )
            assert ok.status_code == 200, ok.text
            assert ok.json()["status"] == "HELD"
            assert ok.json()["operation"] == "RESCHEDULE_MACHINE_RUN"
            assert ok.json()["version"] == 2
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        await engine.dispose()
