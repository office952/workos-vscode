"""MACHINE_RUN CONFIRM/RELEASE/CANCEL — isolated DB proofs (never QA)."""

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
from models.execution_task_machine_reservation import ExecutionTaskMachineReservation
from models.machine_run import MachineRun, MachineRunParticipant, MachineRunTransition
from schemas.auth import UserResponse
from schemas.resource_state_configuration import ResourceDomainConfigurationCommand
from schemas.resource_state_machine_run import (
    CancelMachineRunCommand,
    ConfirmMachineRunCommand,
    CreateMachineRunCommand,
    MachineRunParticipantRef,
    ReleaseMachineRunCommand,
)
from schemas.resource_state_reservation import CreateReservationCommand
from services.execution_task_machine_reservation_command_service import (
    create_reservation,
)
from services.machine_run_command_service import (
    cancel_machine_run,
    confirm_machine_run,
    create_machine_run,
    release_machine_run,
)
from services.resource_domain_configuration_command_service import (
    configure_resource_domain,
)
from services.resource_state_read_service import evaluate_task_resource_state
from services.resource_state_write_common import ResourceStateWriteError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
FACE_A = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_a"
FACE_B = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_b"


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
        "assigned_employee_id": None,
    }


@pytest_asyncio.fixture
async def lc_db(tmp_path: Path):
    db = tmp_path / "machine_run_lifecycle.db"
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
        conn.execute(
            text(
                "INSERT INTO execution_plan "
                "(id, order_id, order_code, snapshot_version, tasks_json, "
                "total_estimated_time_minutes, created_at, updated_at) "
                "VALUES (21, 880751, '880751', 1, :tj, 0.0, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            ),
            {
                "tj": json.dumps(
                    {
                        "source": "order_snapshot_v2",
                        "operational_tasks": [_task(FACE_A)],
                    }
                )
            },
        )
        conn.execute(
            text(
                "INSERT INTO execution_plan "
                "(id, order_id, order_code, snapshot_version, tasks_json, "
                "total_estimated_time_minutes, created_at, updated_at) "
                "VALUES (22, 880752, '880752', 1, :tj, 0.0, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            ),
            {
                "tj": json.dumps(
                    {
                        "source": "order_snapshot_v2",
                        "operational_tasks": [_task(FACE_B)],
                    }
                )
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
            reason_code="lc_activate",
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
                    text(
                        "SELECT COUNT(*) FROM "
                        "execution_task_machine_reservation_transitions"
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


async def _create(session: AsyncSession, *, hours: int = 0):
    start, end = _window(hours)
    return await create_machine_run(
        session,
        command=CreateMachineRunCommand(
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            participants=[
                MachineRunParticipantRef(execution_plan_id=21, task_key=FACE_A),
                MachineRunParticipantRef(execution_plan_id=22, task_key=FACE_B),
            ],
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )


async def _r6(session: AsyncSession) -> tuple[str, str]:
    a = await evaluate_task_resource_state(session, plan_id=21, task_key=FACE_A)
    b = await evaluate_task_resource_state(session, plan_id=22, task_key=FACE_B)
    return a.machine_reservation.state, b.machine_reservation.state


@pytest.mark.asyncio
async def test_confirm_release_happy_path(lc_db: AsyncSession):
    await _activate(lc_db)
    created = await _create(lc_db)
    assert created.status == "HELD"
    assert await _r6(lc_db) == ("ACTIVE", "ACTIVE")
    parts_before = _part_fp(created.participants)
    before = await _counts(lc_db)

    confirmed = await confirm_machine_run(
        lc_db,
        machine_run_id=created.machine_run_id,
        command=ConfirmMachineRunCommand(
            expected_version=1, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    assert confirmed.status == "RESERVED"
    assert confirmed.reservation_status == "RESERVED"
    assert confirmed.version == 2
    assert confirmed.reservation_version == 2
    assert confirmed.operation == "CONFIRM_MACHINE_RUN"
    assert _part_fp(confirmed.participants) == parts_before
    assert confirmed.reservation_start.replace(tzinfo=None) == created.reservation_start.replace(
        tzinfo=None
    )
    assert confirmed.reservation_end.replace(tzinfo=None) == created.reservation_end.replace(
        tzinfo=None
    )
    assert await _r6(lc_db) == ("ACTIVE", "ACTIVE")
    mid = await _counts(lc_db)
    assert mid["run_transitions"] == before["run_transitions"] + 1
    assert mid["reservation_transitions"] == before["reservation_transitions"] + 1
    assert mid["participants"] == before["participants"]

    released = await release_machine_run(
        lc_db,
        machine_run_id=created.machine_run_id,
        command=ReleaseMachineRunCommand(
            expected_version=2, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    assert released.status == "RELEASED"
    assert released.reservation_status == "RELEASED"
    assert released.version == 3
    assert released.reservation_version == 3
    assert _part_fp(released.participants) == parts_before
    assert await _r6(lc_db) == ("CLEAR", "CLEAR")

    # Overlap closed — task-owned reservation can take same window.
    start, end = _window(0)
    ok = await create_reservation(
        lc_db,
        command=CreateReservationCommand(
            execution_plan_id=21,
            task_key=FACE_A,
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert ok.status == "HELD"


@pytest.mark.asyncio
async def test_cancel_from_held(lc_db: AsyncSession):
    await _activate(lc_db)
    held = await _create(lc_db, hours=0)
    parts = _part_fp(held.participants)
    cancelled = await cancel_machine_run(
        lc_db,
        machine_run_id=held.machine_run_id,
        command=CancelMachineRunCommand(
            expected_version=1, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    assert cancelled.status == "CANCELLED"
    assert cancelled.reservation_status == "CANCELLED"
    assert cancelled.version == 2
    assert _part_fp(cancelled.participants) == parts
    assert await _r6(lc_db) == ("CLEAR", "CLEAR")


@pytest.mark.asyncio
async def test_cancel_from_reserved(lc_db: AsyncSession):
    await _activate(lc_db)
    created = await _create(lc_db, hours=0)
    await confirm_machine_run(
        lc_db,
        machine_run_id=created.machine_run_id,
        command=ConfirmMachineRunCommand(
            expected_version=1, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    cancelled = await cancel_machine_run(
        lc_db,
        machine_run_id=created.machine_run_id,
        command=CancelMachineRunCommand(
            expected_version=2, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    assert cancelled.status == "CANCELLED"
    assert cancelled.reservation_status == "CANCELLED"
    assert await _r6(lc_db) == ("CLEAR", "CLEAR")


@pytest.mark.asyncio
async def test_lifecycle_idempotency_and_conflict(lc_db: AsyncSession):
    await _activate(lc_db)
    created = await _create(lc_db)
    key = str(uuid.uuid4())
    first = await confirm_machine_run(
        lc_db,
        machine_run_id=created.machine_run_id,
        command=ConfirmMachineRunCommand(expected_version=1, idempotency_key=key),
        actor_user_id="admin-1",
    )
    mid = await _counts(lc_db)
    second = await confirm_machine_run(
        lc_db,
        machine_run_id=created.machine_run_id,
        command=ConfirmMachineRunCommand(expected_version=1, idempotency_key=key),
        actor_user_id="admin-1",
    )
    assert second.already_applied is True
    assert second.machine_run_id == first.machine_run_id
    assert await _counts(lc_db) == mid

    with pytest.raises(ResourceStateWriteError) as exc:
        await confirm_machine_run(
            lc_db,
            machine_run_id=created.machine_run_id,
            command=ConfirmMachineRunCommand(
                expected_version=1,
                idempotency_key=key,
                reason_code="other_reason",
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "idempotency_payload_conflict"
    assert await _counts(lc_db) == mid


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "action,setup,code",
    [
        ("confirm_released", "release", "invalid_transition"),
        ("confirm_cancelled", "cancel_held", "invalid_transition"),
        ("release_held", "held", "invalid_transition"),
        ("release_released", "release", "invalid_transition"),
        ("cancel_released", "release", "invalid_transition"),
        ("cancel_cancelled", "cancel_held", "invalid_transition"),
        ("confirm_stale", "held", "cas_stale"),
    ],
)
async def test_negative_transitions(lc_db: AsyncSession, action, setup, code):
    await _activate(lc_db)
    created = await _create(lc_db)
    run_id = created.machine_run_id
    if setup in ("release",):
        await confirm_machine_run(
            lc_db,
            machine_run_id=run_id,
            command=ConfirmMachineRunCommand(
                expected_version=1, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        await release_machine_run(
            lc_db,
            machine_run_id=run_id,
            command=ReleaseMachineRunCommand(
                expected_version=2, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        ver = 3
    elif setup == "cancel_held":
        await cancel_machine_run(
            lc_db,
            machine_run_id=run_id,
            command=CancelMachineRunCommand(
                expected_version=1, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        ver = 2
    else:
        ver = 1

    before = await _counts(lc_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        if action.startswith("confirm"):
            await confirm_machine_run(
                lc_db,
                machine_run_id=run_id,
                command=ConfirmMachineRunCommand(
                    expected_version=9 if action == "confirm_stale" else ver,
                    idempotency_key=str(uuid.uuid4()),
                ),
                actor_user_id="admin-1",
            )
        elif action.startswith("release"):
            await release_machine_run(
                lc_db,
                machine_run_id=run_id,
                command=ReleaseMachineRunCommand(
                    expected_version=ver, idempotency_key=str(uuid.uuid4())
                ),
                actor_user_id="admin-1",
            )
        else:
            await cancel_machine_run(
                lc_db,
                machine_run_id=run_id,
                command=CancelMachineRunCommand(
                    expected_version=ver, idempotency_key=str(uuid.uuid4())
                ),
                actor_user_id="admin-1",
            )
    assert exc.value.code == code
    assert await _counts(lc_db) == before


@pytest.mark.asyncio
async def test_state_mismatch_rejects(lc_db: AsyncSession):
    await _activate(lc_db)
    created = await _create(lc_db)
    await lc_db.execute(
        text(
            "UPDATE execution_task_machine_reservations "
            "SET status='RESERVED' WHERE machine_run_id=:rid"
        ),
        {"rid": created.machine_run_id},
    )
    await lc_db.commit()
    before = await _counts(lc_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await confirm_machine_run(
            lc_db,
            machine_run_id=created.machine_run_id,
            command=ConfirmMachineRunCommand(
                expected_version=1, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "run_reservation_state_mismatch"
    assert await _counts(lc_db) == before


@pytest.mark.asyncio
async def test_domain_gate_and_not_found(lc_db: AsyncSession):
    with pytest.raises(ResourceStateWriteError) as exc:
        await confirm_machine_run(
            lc_db,
            machine_run_id=999,
            command=ConfirmMachineRunCommand(
                expected_version=1, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "machine_run_not_found"

    await _activate(lc_db)
    created = await _create(lc_db)
    await cancel_machine_run(
        lc_db,
        machine_run_id=created.machine_run_id,
        command=CancelMachineRunCommand(
            expected_version=1, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    cfg = (
        await lc_db.execute(
            text(
                "SELECT version FROM resource_domain_configurations "
                "WHERE domain='MACHINE_RESERVATION'"
            )
        )
    ).fetchone()
    assert cfg is not None
    await configure_resource_domain(
        lc_db,
        domain="MACHINE_RESERVATION",
        command=ResourceDomainConfigurationCommand(
            target_status="DISABLED",
            expected_version=int(cfg[0]),
            idempotency_key=str(uuid.uuid4()),
            reason_code="lc_disable",
        ),
        actor_user_id="admin-1",
    )
    await lc_db.commit()

    # Seed a HELD run+reservation while domain is DISABLED (bypass CREATE gate).
    await lc_db.execute(
        text(
            "INSERT INTO machine_runs "
            "(id, machine_id, status, version, timezone, created_at, updated_at, "
            "idempotency_key) "
            "VALUES (99, 1, 'HELD', 1, 'UTC', '2026-08-07 15:00:00', "
            "'2026-08-07 15:00:00', :ik)"
        ),
        {"ik": str(uuid.uuid4())},
    )
    await lc_db.execute(
        text(
            "INSERT INTO execution_task_machine_reservations "
            "(id, machine_run_id, machine_id, reservation_start, reservation_end, "
            "timezone, status, version, created_at, updated_at, idempotency_key) "
            "VALUES (99, 99, 1, '2026-08-07 16:00:00', '2026-08-07 18:00:00', "
            "'UTC', 'HELD', 1, '2026-08-07 15:00:00', '2026-08-07 15:00:00', :ik)"
        ),
        {"ik": str(uuid.uuid4())},
    )
    await lc_db.commit()
    before = await _counts(lc_db)
    with pytest.raises(ResourceStateWriteError) as exc2:
        await confirm_machine_run(
            lc_db,
            machine_run_id=99,
            command=ConfirmMachineRunCommand(
                expected_version=1, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
    assert exc2.value.code == "domain_disabled"
    assert await _counts(lc_db) == before


@pytest.mark.asyncio
async def test_held_blocks_overlap_until_cancel(lc_db: AsyncSession):
    await _activate(lc_db)
    created = await _create(lc_db)
    start, end = _window(0)
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_reservation(
            lc_db,
            command=CreateReservationCommand(
                execution_plan_id=21,
                task_key=FACE_A,
                machine_id=1,
                reservation_start=start,
                reservation_end=end,
                timezone="UTC",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "overlap_conflict"

    await cancel_machine_run(
        lc_db,
        machine_run_id=created.machine_run_id,
        command=CancelMachineRunCommand(
            expected_version=1, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    ok = await create_reservation(
        lc_db,
        command=CreateReservationCommand(
            execution_plan_id=21,
            task_key=FACE_A,
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert ok.status == "HELD"


@pytest.mark.asyncio
async def test_http_lifecycle_permission(tmp_path: Path):
    db = tmp_path / "lc_http.db"
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
        app.dependency_overrides[get_current_user] = lambda: _user("op-1", "operator")
        with TestClient(app) as client:
            denied = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/confirm",
                json={"expected_version": 1, "idempotency_key": str(uuid.uuid4())},
            )
            assert denied.status_code == 403

        app.dependency_overrides[get_current_user] = lambda: _user("admin-1", "admin")
        with TestClient(app) as client:
            ok = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/confirm",
                json={"expected_version": 1, "idempotency_key": str(uuid.uuid4())},
            )
            assert ok.status_code == 200, ok.text
            assert ok.json()["status"] == "RESERVED"
            rel = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/release",
                json={"expected_version": 2, "idempotency_key": str(uuid.uuid4())},
            )
            assert rel.status_code == 200, rel.text
            assert rel.json()["status"] == "RELEASED"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        await engine.dispose()
