"""MACHINE_RUN START/COMPLETE runtime — isolated DB proofs (never QA)."""

from __future__ import annotations

import hashlib
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
    CompleteMachineRunCommand,
    ConfirmMachineRunCommand,
    CreateMachineRunCommand,
    MachineRunParticipantRef,
    ReleaseMachineRunCommand,
    RescheduleMachineRunCommand,
    StartMachineRunCommand,
)
from services.machine_run_command_service import (
    cancel_machine_run,
    complete_machine_run,
    confirm_machine_run,
    create_machine_run,
    release_machine_run,
    reschedule_machine_run,
    start_machine_run,
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
async def ex_db(tmp_path: Path):
    db = tmp_path / "machine_run_execution.db"
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
            reason_code="ex_activate",
        ),
        actor_user_id="admin-1",
    )
    await session.commit()


async def _counts(session: AsyncSession) -> dict[str, int]:
    return {
        "runs": int(
            (await session.execute(select(func.count()).select_from(MachineRun))).scalar_one()
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
        "sessions": int(
            (
                await session.execute(text("SELECT COUNT(*) FROM execution_reality"))
            ).scalar_one()
        ),
        "assign_tr": int(
            (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM execution_task_assignment_transitions"
                    )
                )
            ).scalar_one()
        ),
    }


async def _plan_fp(session: AsyncSession) -> dict[int, str]:
    out: dict[int, str] = {}
    for pid in (21, 22):
        row = (
            await session.execute(
                text("SELECT tasks_json FROM execution_plan WHERE id=:id"),
                {"id": pid},
            )
        ).fetchone()
        assert row is not None
        out[pid] = hashlib.sha256(str(row[0]).encode("utf-8")).hexdigest()
    return out


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


async def _confirm(session: AsyncSession, run_id: int, version: int = 1):
    return await confirm_machine_run(
        session,
        machine_run_id=run_id,
        command=ConfirmMachineRunCommand(
            expected_version=version, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )


async def _r6(session: AsyncSession) -> tuple[str, str]:
    a = await evaluate_task_resource_state(session, plan_id=21, task_key=FACE_A)
    b = await evaluate_task_resource_state(session, plan_id=22, task_key=FACE_B)
    return a.machine_reservation.state, b.machine_reservation.state


@pytest.mark.asyncio
async def test_start_complete_release_happy_path(ex_db: AsyncSession):
    await _activate(ex_db)
    created = await _create(ex_db)
    assert created.status == "HELD"
    assert created.reservation_status == "HELD"
    assert await _r6(ex_db) == ("ACTIVE", "ACTIVE")
    parts = _part_fp(created.participants)
    plans_before = await _plan_fp(ex_db)
    before = await _counts(ex_db)

    confirmed = await _confirm(ex_db, created.machine_run_id)
    assert confirmed.status == "RESERVED"
    assert confirmed.reservation_status == "RESERVED"
    assert await _r6(ex_db) == ("ACTIVE", "ACTIVE")

    started = await start_machine_run(
        ex_db,
        machine_run_id=created.machine_run_id,
        command=StartMachineRunCommand(
            expected_version=2, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    assert started.status == "RUNNING"
    assert started.reservation_status == "RESERVED"
    assert started.version == 3
    assert started.reservation_version == 3
    assert started.started_at is not None
    assert started.completed_at is None
    assert started.operation == "START_MACHINE_RUN"
    assert _part_fp(started.participants) == parts
    assert await _r6(ex_db) == ("ACTIVE", "ACTIVE")

    run_row = await ex_db.get(MachineRun, created.machine_run_id)
    assert run_row is not None
    started_at = run_row.started_at
    assert started_at is not None

    res_tr = (
        await ex_db.execute(
            select(ExecutionTaskMachineReservationTransition).where(
                ExecutionTaskMachineReservationTransition.operation
                == "START_MACHINE_RUN"
            )
        )
    ).scalar_one()
    assert res_tr.previous_status == "RESERVED"
    assert res_tr.new_status == "RESERVED"
    assert res_tr.previous_version == 2
    assert res_tr.new_version == 3

    completed = await complete_machine_run(
        ex_db,
        machine_run_id=created.machine_run_id,
        command=CompleteMachineRunCommand(
            expected_version=3, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    assert completed.status == "COMPLETED"
    assert completed.reservation_status == "RESERVED"
    assert completed.version == 4
    assert completed.reservation_version == 4
    assert completed.started_at is not None
    assert completed.completed_at is not None
    assert completed.completed_at.replace(tzinfo=None) >= completed.started_at.replace(
        tzinfo=None
    )
    assert completed.operation == "COMPLETE_MACHINE_RUN"
    assert _part_fp(completed.participants) == parts
    assert await _r6(ex_db) == ("ACTIVE", "ACTIVE")

    run_row = await ex_db.get(MachineRun, created.machine_run_id)
    assert run_row is not None
    assert run_row.started_at is not None
    assert run_row.started_at.replace(tzinfo=None) == started_at.replace(tzinfo=None)
    assert run_row.completed_at is not None
    # Actual runtime is derived, not persisted.
    cols = (
        await ex_db.execute(text("PRAGMA table_info(machine_runs)"))
    ).fetchall()
    assert "actual_runtime_minutes" not in {c[1] for c in cols}

    released = await release_machine_run(
        ex_db,
        machine_run_id=created.machine_run_id,
        command=ReleaseMachineRunCommand(
            expected_version=4, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    assert released.status == "RELEASED"
    assert released.reservation_status == "RELEASED"
    assert released.version == 5
    assert released.reservation_version == 5
    assert released.started_at is not None and started_at is not None
    assert released.started_at.replace(tzinfo=None) == started_at.replace(tzinfo=None)
    assert released.completed_at is not None
    assert await _r6(ex_db) == ("CLEAR", "CLEAR")

    rel_res_tr = (
        await ex_db.execute(
            select(ExecutionTaskMachineReservationTransition)
            .where(
                ExecutionTaskMachineReservationTransition.operation
                == "RELEASE_RESERVATION"
            )
            .order_by(ExecutionTaskMachineReservationTransition.id.desc())
        )
    ).scalars().first()
    assert rel_res_tr is not None
    assert rel_res_tr.previous_status == "RESERVED"
    assert rel_res_tr.new_status == "RELEASED"

    after = await _counts(ex_db)
    assert after["participants"] == before["participants"]
    assert after["sessions"] == before["sessions"] == 0
    assert after["assign_tr"] == before["assign_tr"] == 0
    assert await _plan_fp(ex_db) == plans_before


@pytest.mark.asyncio
async def test_direct_release_without_start(ex_db: AsyncSession):
    await _activate(ex_db)
    created = await _create(ex_db)
    await _confirm(ex_db, created.machine_run_id)
    released = await release_machine_run(
        ex_db,
        machine_run_id=created.machine_run_id,
        command=ReleaseMachineRunCommand(
            expected_version=2, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    assert released.status == "RELEASED"
    assert released.reservation_status == "RELEASED"
    assert released.started_at is None
    assert released.completed_at is None
    assert await _r6(ex_db) == ("CLEAR", "CLEAR")


@pytest.mark.asyncio
async def test_start_complete_idempotency_replay(ex_db: AsyncSession):
    await _activate(ex_db)
    created = await _create(ex_db)
    await _confirm(ex_db, created.machine_run_id)
    start_key = str(uuid.uuid4())
    first = await start_machine_run(
        ex_db,
        machine_run_id=created.machine_run_id,
        command=StartMachineRunCommand(expected_version=2, idempotency_key=start_key),
        actor_user_id="admin-1",
    )
    mid = await _counts(ex_db)
    started_at = first.started_at
    second = await start_machine_run(
        ex_db,
        machine_run_id=created.machine_run_id,
        command=StartMachineRunCommand(expected_version=2, idempotency_key=start_key),
        actor_user_id="admin-1",
    )
    assert second.already_applied is True
    assert second.started_at is not None and started_at is not None
    assert second.started_at.replace(tzinfo=None) == started_at.replace(tzinfo=None)
    assert await _counts(ex_db) == mid

    with pytest.raises(ResourceStateWriteError) as exc:
        await start_machine_run(
            ex_db,
            machine_run_id=created.machine_run_id,
            command=StartMachineRunCommand(
                expected_version=2,
                idempotency_key=start_key,
                reason_code="other",
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "idempotency_payload_conflict"

    complete_key = str(uuid.uuid4())
    c1 = await complete_machine_run(
        ex_db,
        machine_run_id=created.machine_run_id,
        command=CompleteMachineRunCommand(
            expected_version=3, idempotency_key=complete_key
        ),
        actor_user_id="admin-1",
    )
    mid2 = await _counts(ex_db)
    c2 = await complete_machine_run(
        ex_db,
        machine_run_id=created.machine_run_id,
        command=CompleteMachineRunCommand(
            expected_version=3, idempotency_key=complete_key
        ),
        actor_user_id="admin-1",
    )
    assert c2.already_applied is True
    assert c2.completed_at is not None and c1.completed_at is not None
    assert c2.completed_at.replace(tzinfo=None) == c1.completed_at.replace(tzinfo=None)
    assert await _counts(ex_db) == mid2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "action,setup,code",
    [
        ("start_held", "held", "invalid_transition"),
        ("start_running", "running", "invalid_transition"),
        ("start_completed", "completed", "invalid_transition"),
        ("start_released", "released", "invalid_transition"),
        ("start_cancelled", "cancelled", "invalid_transition"),
        ("start_stale", "reserved", "cas_stale"),
        ("complete_held", "held", "invalid_transition"),
        ("complete_reserved", "reserved", "invalid_transition"),
        ("complete_completed", "completed", "invalid_transition"),
        ("complete_released", "released", "invalid_transition"),
        ("complete_cancelled", "cancelled", "invalid_transition"),
        ("complete_stale", "running", "cas_stale"),
        ("cancel_running", "running", "invalid_transition"),
        ("cancel_completed", "completed", "invalid_transition"),
        ("reschedule_running", "running", "invalid_transition"),
        ("reschedule_completed", "completed", "invalid_transition"),
    ],
)
async def test_negative_start_complete_boundaries(
    ex_db: AsyncSession, action, setup, code
):
    await _activate(ex_db)
    created = await _create(ex_db)
    run_id = created.machine_run_id
    ver = 1
    if setup in ("reserved", "running", "completed", "released"):
        await _confirm(ex_db, run_id)
        ver = 2
    if setup in ("running", "completed", "released"):
        await start_machine_run(
            ex_db,
            machine_run_id=run_id,
            command=StartMachineRunCommand(
                expected_version=2, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        ver = 3
    if setup in ("completed", "released"):
        await complete_machine_run(
            ex_db,
            machine_run_id=run_id,
            command=CompleteMachineRunCommand(
                expected_version=3, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        ver = 4
    if setup == "released":
        await release_machine_run(
            ex_db,
            machine_run_id=run_id,
            command=ReleaseMachineRunCommand(
                expected_version=4, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        ver = 5
    if setup == "cancelled":
        await cancel_machine_run(
            ex_db,
            machine_run_id=run_id,
            command=CancelMachineRunCommand(
                expected_version=1, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        ver = 2

    before = await _counts(ex_db)
    expected_ver = 99 if "stale" in action else ver
    with pytest.raises(ResourceStateWriteError) as exc:
        if action.startswith("start"):
            await start_machine_run(
                ex_db,
                machine_run_id=run_id,
                command=StartMachineRunCommand(
                    expected_version=expected_ver, idempotency_key=str(uuid.uuid4())
                ),
                actor_user_id="admin-1",
            )
        elif action.startswith("complete"):
            await complete_machine_run(
                ex_db,
                machine_run_id=run_id,
                command=CompleteMachineRunCommand(
                    expected_version=expected_ver, idempotency_key=str(uuid.uuid4())
                ),
                actor_user_id="admin-1",
            )
        elif action.startswith("cancel"):
            await cancel_machine_run(
                ex_db,
                machine_run_id=run_id,
                command=CancelMachineRunCommand(
                    expected_version=ver, idempotency_key=str(uuid.uuid4())
                ),
                actor_user_id="admin-1",
            )
        else:
            s, e = _window(hours=3)
            await reschedule_machine_run(
                ex_db,
                machine_run_id=run_id,
                command=RescheduleMachineRunCommand(
                    expected_version=ver,
                    reservation_start=s,
                    reservation_end=e,
                    timezone="UTC",
                    idempotency_key=str(uuid.uuid4()),
                ),
                actor_user_id="admin-1",
            )
    assert exc.value.code == code
    assert await _counts(ex_db) == before


@pytest.mark.asyncio
async def test_phase_aware_mismatch_rejects(ex_db: AsyncSession):
    await _activate(ex_db)
    created = await _create(ex_db)
    await _confirm(ex_db, created.machine_run_id)
    await ex_db.execute(
        text(
            "UPDATE execution_task_machine_reservations "
            "SET status='HELD' WHERE machine_run_id=:rid"
        ),
        {"rid": created.machine_run_id},
    )
    await ex_db.commit()
    before = await _counts(ex_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await start_machine_run(
            ex_db,
            machine_run_id=created.machine_run_id,
            command=StartMachineRunCommand(
                expected_version=2, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "run_reservation_state_mismatch"
    assert await _counts(ex_db) == before


@pytest.mark.asyncio
async def test_domain_gate_start(ex_db: AsyncSession):
    await _activate(ex_db)
    created = await _create(ex_db)
    await cancel_machine_run(
        ex_db,
        machine_run_id=created.machine_run_id,
        command=CancelMachineRunCommand(
            expected_version=1, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    cfg = (
        await ex_db.execute(
            text(
                "SELECT version FROM resource_domain_configurations "
                "WHERE domain='MACHINE_RESERVATION'"
            )
        )
    ).fetchone()
    assert cfg is not None
    await configure_resource_domain(
        ex_db,
        domain="MACHINE_RESERVATION",
        command=ResourceDomainConfigurationCommand(
            target_status="DISABLED",
            expected_version=int(cfg[0]),
            idempotency_key=str(uuid.uuid4()),
            reason_code="ex_disable",
        ),
        actor_user_id="admin-1",
    )
    await ex_db.commit()

    # Seed RESERVED/RESERVED while domain DISABLED (bypass CREATE/CONFIRM gates).
    await ex_db.execute(
        text(
            "INSERT INTO machine_runs "
            "(id, machine_id, status, version, timezone, created_at, updated_at, "
            "idempotency_key) "
            "VALUES (99, 1, 'RESERVED', 2, 'UTC', '2026-08-07 15:00:00', "
            "'2026-08-07 15:00:00', :ik)"
        ),
        {"ik": str(uuid.uuid4())},
    )
    await ex_db.execute(
        text(
            "INSERT INTO execution_task_machine_reservations "
            "(id, machine_run_id, machine_id, reservation_start, reservation_end, "
            "timezone, status, version, created_at, updated_at, idempotency_key) "
            "VALUES (99, 99, 1, '2026-08-07 16:00:00', '2026-08-07 18:00:00', "
            "'UTC', 'RESERVED', 2, '2026-08-07 15:00:00', '2026-08-07 15:00:00', :ik)"
        ),
        {"ik": str(uuid.uuid4())},
    )
    await ex_db.commit()
    before = await _counts(ex_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await start_machine_run(
            ex_db,
            machine_run_id=99,
            command=StartMachineRunCommand(
                expected_version=2, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "domain_disabled"
    assert await _counts(ex_db) == before


@pytest.mark.asyncio
async def test_http_execute_permission(tmp_path: Path):
    db = tmp_path / "ex_http.db"
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
        await _confirm(session, created.machine_run_id)

    async def _override_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_db
    try:
        app.dependency_overrides[get_current_user] = lambda: _user("sales-1", "sales")
        with TestClient(app) as client:
            denied = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/start",
                json={"expected_version": 2, "idempotency_key": str(uuid.uuid4())},
            )
            assert denied.status_code == 403

        app.dependency_overrides[get_current_user] = lambda: _user("op-1", "operator")
        with TestClient(app) as client:
            started = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/start",
                json={"expected_version": 2, "idempotency_key": str(uuid.uuid4())},
            )
            assert started.status_code == 200, started.text
            body = started.json()
            assert body["status"] == "RUNNING"
            assert body["reservation_status"] == "RESERVED"
            assert body["started_at"] is not None

            # manage stays required for RELEASE
            rel_denied = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/release",
                json={"expected_version": 3, "idempotency_key": str(uuid.uuid4())},
            )
            assert rel_denied.status_code == 403

            done = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/complete",
                json={"expected_version": 3, "idempotency_key": str(uuid.uuid4())},
            )
            assert done.status_code == 200, done.text
            assert done.json()["status"] == "COMPLETED"
            assert done.json()["reservation_status"] == "RESERVED"

        app.dependency_overrides[get_current_user] = lambda: _user("admin-1", "admin")
        with TestClient(app) as client:
            rel = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/release",
                json={"expected_version": 4, "idempotency_key": str(uuid.uuid4())},
            )
            assert rel.status_code == 200, rel.text
            assert rel.json()["status"] == "RELEASED"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        await engine.dispose()
