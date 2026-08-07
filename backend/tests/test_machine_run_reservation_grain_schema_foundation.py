"""s66 MACHINE_RUN + Reservation grain schema foundation (isolated SQLite).

Never touches backend/dev.db. No MACHINE_RUN command runtime.
"""

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
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.schema_ownership import (
    ALEMBIC_OWNED_TABLES,
    MACHINE_RUN_TABLES,
    RESOURCE_STATE_TABLES,
)
from core.sqlite_pragma import register_sqlite_foreign_keys
from models.execution_task_machine_reservation import (
    ExecutionTaskMachineReservation,
    ExecutionTaskMachineReservationTransition,
)
from models.machine_run import (
    MachineRun,
    MachineRunParticipant,
    MachineRunTransition,
)
from services.execution_task_machine_reservation_repository import (
    ExecutionTaskMachineReservationRepository,
)
from services.resource_state_read_repository import ResourceStateReadRepository
from services.resource_state_read_service import evaluate_task_resource_state
from services.resource_domain_configuration_command_service import (
    configure_resource_domain,
)
from schemas.resource_state_configuration import ResourceDomainConfigurationCommand

BACKEND_ROOT = Path(__file__).resolve().parents[1]
S65 = "s65_workcenter_capacity_source"
S66 = "s66_machine_run_reservation_grain"
LED_TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters"
OTHER_TASK = "other-task"

OWNER_XOR_SQL_FRAG = "machine_run_id IS NULL"


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


def _sync_engine(path: Path):
    engine = create_engine(f"sqlite:///{path.resolve().as_posix()}")
    register_sqlite_foreign_keys(engine)
    return engine


def _revision(engine) -> str | None:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        return rows[0][0] if rows else None


def _schema_fingerprint(engine) -> str:
    with engine.connect() as conn:
        rows = [
            dict(r)
            for r in conn.execute(
                text(
                    "SELECT type, name, sql FROM sqlite_master "
                    "WHERE name NOT LIKE 'sqlite_%' ORDER BY 1, 2"
                )
            ).mappings()
        ]
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True, default=str).encode()
    ).hexdigest()


def _seed_plan_machine(engine) -> None:
    tasks_json = json.dumps(
        {
            "source": "order_snapshot_v2",
            "operational_tasks": [
                {"task_id": LED_TASK, "assigned_employee_id": 7},
                {"task_id": OTHER_TASK, "assigned_employee_id": None},
            ],
        }
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO employees "
                "(id, name, status, employee_type, salary_currency, salary_period) "
                "VALUES (7, 'Andrei', 'active', 'internal', 'RON', 'monthly')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO execution_plan "
                "(id, order_id, order_code, snapshot_version, tasks_json, "
                "total_estimated_time_minutes, created_at, updated_at) "
                "VALUES (31, 880031, '880031', 1, :tj, 0.0, "
                "'2026-08-07 12:00:00', '2026-08-07 12:00:00')"
            ),
            {"tj": tasks_json},
        )
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, '2026-08-07 12:00:00', '2026-08-07 12:00:00')"
            )
        )


def test_alembic_single_head_s66_ancestry():
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == [S66]
    assert script.get_revision(S66).down_revision == S65


def test_machine_run_tables_alembic_owned():
    assert MACHINE_RUN_TABLES.issubset(ALEMBIC_OWNED_TABLES)
    assert len(MACHINE_RUN_TABLES) == 3
    assert len(RESOURCE_STATE_TABLES) == 8


def test_fresh_full_chain_s66(tmp_path: Path):
    db = tmp_path / "s66_fresh.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    engine = _sync_engine(db)
    assert _revision(engine) == S66
    with engine.connect() as conn:
        assert int(conn.execute(text("PRAGMA foreign_keys")).scalar_one()) == 1
        assert conn.execute(text("PRAGMA foreign_key_check")).fetchall() == []
        tables = set(inspect(conn).get_table_names())
        ddl = conn.execute(
            text(
                "SELECT sql FROM sqlite_master WHERE type='table' "
                "AND name='execution_task_machine_reservations'"
            )
        ).scalar_one()
    assert MACHINE_RUN_TABLES.issubset(tables)
    assert OWNER_XOR_SQL_FRAG in (ddl or "")
    assert "ck_exec_task_machine_res_owner_xor" in (ddl or "")
    fp = _schema_fingerprint(engine)
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    assert _schema_fingerprint(engine) == fp


def test_s65_to_s66_preserves_task_reservation(tmp_path: Path):
    db = tmp_path / "s66_from_s65.db"
    url = _async_url(db)
    assert _alembic_cmd(url, "upgrade", S65).returncode == 0
    engine = _sync_engine(db)
    _seed_plan_machine(engine)
    start = "2026-08-07 10:00:00"
    end = "2026-08-07 11:00:00"
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO execution_task_machine_reservations "
                "(id, execution_plan_id, order_id, task_key, machine_id, "
                "reservation_start, reservation_end, timezone, status, version, "
                "created_at, updated_at, idempotency_key) "
                "VALUES (9, 31, 880031, :tk, 1, :s, :e, 'UTC', 'HELD', 1, "
                ":s, :s, :ik)"
            ),
            {
                "tk": LED_TASK,
                "s": start,
                "e": end,
                "ik": str(uuid.uuid4()),
            },
        )
        conn.execute(
            text(
                "INSERT INTO execution_task_machine_reservation_transitions "
                "(transition_id, reservation_id, execution_plan_id, task_key, "
                "machine_id, operation, new_status, new_version, "
                "idempotency_key, created_at) "
                "VALUES (:tid, 9, 31, :tk, 1, 'CREATE_RESERVATION', 'HELD', 1, "
                ":ik, :s)"
            ),
            {
                "tid": str(uuid.uuid4()),
                "tk": LED_TASK,
                "ik": str(uuid.uuid4()),
                "s": start,
            },
        )
    before = None
    with engine.connect() as conn:
        before = conn.execute(
            text(
                "SELECT id, execution_plan_id, task_key, status, version "
                "FROM execution_task_machine_reservations WHERE id=9"
            )
        ).fetchone()

    assert _alembic_cmd(url, "upgrade", S66).returncode == 0
    assert _revision(engine) == S66
    with engine.connect() as conn:
        after = conn.execute(
            text(
                "SELECT id, execution_plan_id, task_key, status, version, "
                "machine_run_id FROM execution_task_machine_reservations WHERE id=9"
            )
        ).fetchone()
        tr = conn.execute(
            text(
                "SELECT owner_form, machine_run_id, task_key "
                "FROM execution_task_machine_reservation_transitions "
                "WHERE reservation_id=9"
            )
        ).fetchone()
        assert conn.execute(text("SELECT COUNT(*) FROM machine_runs")).scalar_one() == 0
        assert conn.execute(text("PRAGMA foreign_key_check")).fetchall() == []
    assert after[0:5] == before
    assert after[5] is None
    assert tr[0] == "TASK"
    assert tr[1] is None
    assert tr[2] == LED_TASK


def test_downgrade_s66_to_s65_reupgrade(tmp_path: Path):
    db = tmp_path / "s66_down.db"
    url = _async_url(db)
    assert _alembic_cmd(url, "upgrade", S66).returncode == 0
    engine = _sync_engine(db)
    assert _alembic_cmd(url, "downgrade", S65).returncode == 0
    assert _revision(engine) == S65
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        assert "machine_runs" not in tables
        assert "machine_run_id" not in {
            c["name"] for c in inspect(conn).get_columns(
                "execution_task_machine_reservations"
            )
        }
    assert _alembic_cmd(url, "upgrade", S66).returncode == 0
    assert _revision(engine) == S66
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        assert MACHINE_RUN_TABLES.issubset(tables)
        res_cols = {
            c["name"] for c in inspect(conn).get_columns(
                "execution_task_machine_reservations"
            )
        }
        assert "machine_run_id" in res_cols
        ddl = conn.execute(
            text(
                "SELECT sql FROM sqlite_master WHERE type='table' "
                "AND name='execution_task_machine_reservations'"
            )
        ).scalar_one()
        assert "ck_exec_task_machine_res_owner_xor" in (ddl or "")
        assert conn.execute(text("PRAGMA foreign_key_check")).fetchall() == []


def test_xor_rejects_both_and_neither_owners(tmp_path: Path):
    db = tmp_path / "s66_xor.db"
    url = _async_url(db)
    assert _alembic_cmd(url, "upgrade", S66).returncode == 0
    engine = _sync_engine(db)
    _seed_plan_machine(engine)
    now = "2026-08-07 10:00:00"
    end = "2026-08-07 11:00:00"
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO machine_runs "
                "(id, machine_id, status, version, timezone, created_at, updated_at, "
                "idempotency_key) "
                "VALUES (1, 1, 'HELD', 1, 'UTC', :n, :n, :ik)"
            ),
            {"n": now, "ik": str(uuid.uuid4())},
        )
    with pytest.raises(Exception):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO execution_task_machine_reservations "
                    "(execution_plan_id, order_id, task_key, machine_run_id, machine_id, "
                    "reservation_start, reservation_end, timezone, status, version, "
                    "created_at, updated_at, idempotency_key) "
                    "VALUES (31, 880031, :tk, 1, 1, :s, :e, 'UTC', 'HELD', 1, "
                    ":s, :s, :ik)"
                ),
                {"tk": LED_TASK, "s": now, "e": end, "ik": str(uuid.uuid4())},
            )
    with pytest.raises(Exception):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO execution_task_machine_reservations "
                    "(execution_plan_id, order_id, task_key, machine_run_id, machine_id, "
                    "reservation_start, reservation_end, timezone, status, version, "
                    "created_at, updated_at, idempotency_key) "
                    "VALUES (NULL, NULL, NULL, NULL, 1, :s, :e, 'UTC', 'HELD', 1, "
                    ":s, :s, :ik)"
                ),
                {"s": now, "e": end, "ik": str(uuid.uuid4())},
            )


@pytest_asyncio.fixture
async def s66_session(tmp_path: Path):
    db = tmp_path / "s66_async.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(sync)
    _seed_plan_machine(sync)
    engine = create_async_engine(url)
    register_sqlite_foreign_keys(engine.sync_engine)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        await configure_resource_domain(
            session,
            domain="MACHINE_RESERVATION",
            command=ResourceDomainConfigurationCommand(
                target_status="ACTIVE",
                expected_version=0,
                idempotency_key=str(uuid.uuid4()),
                reason_code="s66_foundation_activate",
            ),
            actor_user_id="tester",
        )
        await session.commit()
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_atomic_run_reservation_participants_persistence(s66_session: AsyncSession):
    db = s66_session
    now = datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc)
    end = now + timedelta(hours=1)
    run = MachineRun(
        machine_id=1,
        status="HELD",
        version=1,
        timezone="UTC",
        created_at=now,
        updated_at=now,
        idempotency_key=str(uuid.uuid4()),
    )
    db.add(run)
    await db.flush()
    res = ExecutionTaskMachineReservation(
        execution_plan_id=None,
        order_id=None,
        task_key=None,
        machine_run_id=run.id,
        machine_id=1,
        reservation_start=now,
        reservation_end=end,
        timezone="UTC",
        status="HELD",
        version=1,
        created_at=now,
        updated_at=now,
        idempotency_key=str(uuid.uuid4()),
    )
    db.add(res)
    await db.flush()
    for tk in (LED_TASK, OTHER_TASK):
        db.add(
            MachineRunParticipant(
                machine_run_id=run.id,
                execution_plan_id=31,
                order_id=880031,
                task_key=tk,
                status="ACTIVE",
                added_at=now,
            )
        )
    db.add(
        MachineRunTransition(
            transition_id=str(uuid.uuid4()),
            machine_run_id=run.id,
            machine_id=1,
            operation="CREATE_RUN",
            previous_status=None,
            new_status="HELD",
            previous_version=None,
            new_version=1,
            idempotency_key=str(uuid.uuid4()),
            created_at=now,
        )
    )
    db.add(
        ExecutionTaskMachineReservationTransition(
            transition_id=str(uuid.uuid4()),
            reservation_id=res.id,
            owner_form="MACHINE_RUN",
            execution_plan_id=None,
            task_key=None,
            machine_run_id=run.id,
            machine_id=1,
            operation="CREATE_RESERVATION",
            previous_status=None,
            new_status="HELD",
            previous_version=None,
            new_version=1,
            new_start=now,
            new_end=end,
            idempotency_key=str(uuid.uuid4()),
            created_at=now,
        )
    )
    await db.commit()

    repo = ResourceStateReadRepository(db)
    rows_a = await repo.list_reservations_visible_to_task(
        execution_plan_id=31, task_key=LED_TASK
    )
    rows_b = await repo.list_reservations_visible_to_task(
        execution_plan_id=31, task_key=OTHER_TASK
    )
    assert len(rows_a) == 1 and rows_a[0].id == res.id
    assert len(rows_b) == 1 and rows_b[0].id == res.id
    assert rows_a[0].machine_run_id == run.id
    task_only = await repo.list_reservations_for_task(
        execution_plan_id=31, task_key=LED_TASK
    )
    assert task_only == []


@pytest.mark.asyncio
async def test_overlap_task_owned_vs_run_owned(s66_session: AsyncSession):
    db = s66_session
    now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
    end = now + timedelta(hours=1)
    task_res = ExecutionTaskMachineReservation(
        execution_plan_id=31,
        order_id=880031,
        task_key=LED_TASK,
        machine_run_id=None,
        machine_id=1,
        reservation_start=now,
        reservation_end=end,
        timezone="UTC",
        status="HELD",
        version=1,
        created_at=now,
        updated_at=now,
        idempotency_key=str(uuid.uuid4()),
    )
    db.add(task_res)
    await db.flush()

    run = MachineRun(
        machine_id=1,
        status="HELD",
        version=1,
        timezone="UTC",
        created_at=now,
        updated_at=now,
        idempotency_key=str(uuid.uuid4()),
    )
    db.add(run)
    await db.flush()
    run_res = ExecutionTaskMachineReservation(
        execution_plan_id=None,
        order_id=None,
        task_key=None,
        machine_run_id=run.id,
        machine_id=1,
        reservation_start=now + timedelta(minutes=30),
        reservation_end=end + timedelta(minutes=30),
        timezone="UTC",
        status="HELD",
        version=1,
        created_at=now,
        updated_at=now,
        idempotency_key=str(uuid.uuid4()),
    )
    db.add(run_res)
    await db.flush()

    repo = ExecutionTaskMachineReservationRepository(db)
    hit = await repo.find_overlapping_open(
        machine_id=1,
        start=now + timedelta(minutes=30),
        end=end + timedelta(minutes=30),
        exclude_id=run_res.id,
    )
    assert hit is not None
    assert hit.id == task_res.id

    hit2 = await repo.find_overlapping_open(
        machine_id=1,
        start=now,
        end=end,
        exclude_id=task_res.id,
    )
    assert hit2 is not None
    assert hit2.id == run_res.id


@pytest.mark.asyncio
async def test_r6_union_sees_run_owned_reservation(s66_session: AsyncSession):
    db = s66_session
    now = datetime(2026, 8, 7, 14, 0, tzinfo=timezone.utc)
    end = now + timedelta(hours=1)
    run = MachineRun(
        machine_id=1,
        status="HELD",
        version=1,
        timezone="UTC",
        created_at=now,
        updated_at=now,
        idempotency_key=str(uuid.uuid4()),
    )
    db.add(run)
    await db.flush()
    res = ExecutionTaskMachineReservation(
        execution_plan_id=None,
        order_id=None,
        task_key=None,
        machine_run_id=run.id,
        machine_id=1,
        reservation_start=now,
        reservation_end=end,
        timezone="UTC",
        status="RESERVED",
        version=1,
        created_at=now,
        updated_at=now,
        idempotency_key=str(uuid.uuid4()),
    )
    db.add(res)
    db.add(
        MachineRunParticipant(
            machine_run_id=run.id,
            execution_plan_id=31,
            order_id=880031,
            task_key=LED_TASK,
            status="ACTIVE",
            added_at=now,
        )
    )
    await db.commit()

    result = await evaluate_task_resource_state(db, plan_id=31, task_key=LED_TASK)
    assert result.machine_reservation.state == "ACTIVE"
    assert res.id in result.machine_reservation.source_record_ids
