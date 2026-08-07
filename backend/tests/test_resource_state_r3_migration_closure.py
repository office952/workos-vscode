"""Resource State R3 — isolated migration closure proofs.

Never touches backend/dev.db. All DBs are temporary under tmp_path.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from core.schema_ownership import ALEMBIC_OWNED_TABLES, RESOURCE_STATE_TABLES
from core.sqlite_pragma import register_sqlite_foreign_keys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
S63 = "s63_execution_task_assignment_transitions"
S64 = "s64_resource_state_persistence"
ASSIGN_TABLE = "execution_task_assignment_transitions"


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


def _async_sqlite_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.resolve().as_posix()}"


def _sync_engine(path: Path):
    engine = create_engine(f"sqlite:///{path.resolve().as_posix()}")
    register_sqlite_foreign_keys(engine)
    return engine


def _current_revision(engine) -> str | None:
    with engine.connect() as conn:
        try:
            rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        except Exception:  # noqa: BLE001
            return None
        if not rows:
            return None
        assert len(rows) == 1, rows
        return rows[0][0]


def _pragma_foreign_keys(engine) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text("PRAGMA foreign_keys")).scalar_one())


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


def _row_counts(engine) -> dict[str, int]:
    out: dict[str, int] = {}
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        for name in sorted(RESOURCE_STATE_TABLES):
            if name not in tables:
                out[name] = -1
                continue
            out[name] = int(
                conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
            )
    return out


def _insert_minimal_row(conn, table: str, values: dict) -> None:
    cols = {c["name"] for c in inspect(conn).get_columns(table)}
    use = {k: v for k, v in values.items() if k in cols}
    col_sql = ", ".join(use.keys())
    placeholders = ", ".join(f":{k}" for k in use)
    conn.execute(
        text(f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})"),
        use,
    )


def _seed_pre_s64(engine) -> str:
    tasks_json = json.dumps(
        {
            "source": "order_snapshot_v2",
            "planned_tasks": [],
            "planned_operations": [],
            "operational_tasks": [
                {
                    "task_id": "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters",
                    "assigned_employee_id": 7,
                },
                {"task_id": "other_unassigned"},
            ],
        }
    )
    with engine.begin() as conn:
        _insert_minimal_row(
            conn,
            "employees",
            {
                "id": 7,
                "name": "Andrei",
                "status": "active",
                "employee_type": "internal",
                "salary_currency": "RON",
                "salary_period": "monthly",
            },
        )
        _insert_minimal_row(
            conn,
            "execution_plan",
            {
                "id": 23,
                "order_id": 880750,
                "order_code": "880750",
                "snapshot_version": 1,
                "tasks_json": tasks_json,
                "total_estimated_time_minutes": 0.0,
                "created_at": "2026-08-04 16:00:00",
                "updated_at": "2026-08-04 19:16:57.407320",
            },
        )
        _insert_minimal_row(
            conn,
            "machines",
            {
                "id": 1,
                "machine_code": "CNC-1",
                "name": "CNC One",
                "machine_type": "cnc",
                "resource_kind": "machine",
                "operational_status": "active",
                "is_available": 1,
                "is_active": 1,
                "created_at": "2026-08-04 16:00:00",
                "updated_at": "2026-08-04 16:00:00",
            },
        )
    return tasks_json


def test_migration_graph_single_head_s64_after_s63():
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    # Head advanced to s66 (MACHINE_RUN grain); s64 remains the RS eight-pack revision.
    assert heads == ["s66_machine_run_reservation_grain"], heads
    assert script.get_revision("s66_machine_run_reservation_grain").down_revision == (
        "s65_workcenter_capacity_source"
    )
    assert script.get_revision("s65_workcenter_capacity_source").down_revision == S64
    rev = script.get_revision(S64)
    assert rev is not None
    assert rev.down_revision == S63


def test_fresh_sqlite_upgrade_head_resource_state(tmp_path: Path):
    db = tmp_path / "fresh_r3.db"
    url = _async_sqlite_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout

    engine = _sync_engine(db)
    # Head is s66; RS eight-pack from s64 remains present and empty.
    assert _current_revision(engine) == "s66_machine_run_reservation_grain"
    assert _pragma_foreign_keys(engine) == 1

    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
    for name in RESOURCE_STATE_TABLES:
        assert name in tables, name
    assert ASSIGN_TABLE in tables

    counts = _row_counts(engine)
    assert all(v == 0 for v in counts.values()), counts
    fp = _schema_fingerprint(engine)
    assert len(fp) == 64


def test_s63_to_s64_preserves_prior_data(tmp_path: Path):
    db = tmp_path / "prior_r3.db"
    url = _async_sqlite_url(db)
    assert _alembic_cmd(url, "upgrade", S63).returncode == 0
    engine = _sync_engine(db)
    tasks_json = _seed_pre_s64(engine)

    # Ensure assignment transition exists via s63 backfill path if empty,
    # otherwise insert one canonical row for fingerprint stability.
    with engine.begin() as conn:
        n = conn.execute(text(f"SELECT COUNT(*) FROM {ASSIGN_TABLE}")).scalar_one()
        if n == 0:
            _insert_minimal_row(
                conn,
                ASSIGN_TABLE,
                {
                    "transition_id": "11111111-1111-1111-1111-111111111111",
                    "execution_plan_id": 23,
                    "order_id": 880750,
                    "task_key": "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters",
                    "transition_type": "ASSIGN",
                    "previous_employee_id": None,
                    "new_employee_id": 7,
                    "source": "TEST_SEED",
                    "created_at": "2026-08-04 19:16:57.407320",
                },
            )

    with engine.connect() as conn:
        sha_before = conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one()
        upd_before = conn.execute(
            text("SELECT updated_at FROM execution_plan WHERE id=23")
        ).scalar_one()
        assign_before = conn.execute(
            text(
                f"SELECT transition_id, transition_type, new_employee_id "
                f"FROM {ASSIGN_TABLE} ORDER BY id"
            )
        ).fetchall()
        assert sha_before == tasks_json

    assert _pragma_foreign_keys(engine) == 1
    proc = _alembic_cmd(url, "upgrade", S64)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert _current_revision(engine) == S64

    with engine.connect() as conn:
        sha_after = conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one()
        upd_after = conn.execute(
            text("SELECT updated_at FROM execution_plan WHERE id=23")
        ).scalar_one()
        assign_after = conn.execute(
            text(
                f"SELECT transition_id, transition_type, new_employee_id "
                f"FROM {ASSIGN_TABLE} ORDER BY id"
            )
        ).fetchall()
        tables = set(inspect(conn).get_table_names())
    assert sha_after == sha_before
    assert upd_after == upd_before
    assert assign_after == assign_before
    for name in RESOURCE_STATE_TABLES:
        assert name in tables
    assert all(v == 0 for v in _row_counts(engine).values())


def test_downgrade_reupgrade_s64_isolated(tmp_path: Path):
    db = tmp_path / "down_r3.db"
    url = _async_sqlite_url(db)
    assert _alembic_cmd(url, "upgrade", S63).returncode == 0
    engine = _sync_engine(db)
    tasks_json = _seed_pre_s64(engine)
    with engine.begin() as conn:
        n = conn.execute(text(f"SELECT COUNT(*) FROM {ASSIGN_TABLE}")).scalar_one()
        if n == 0:
            _insert_minimal_row(
                conn,
                ASSIGN_TABLE,
                {
                    "transition_id": "22222222-2222-2222-2222-222222222222",
                    "execution_plan_id": 23,
                    "order_id": 880750,
                    "task_key": "led",
                    "transition_type": "ASSIGN",
                    "new_employee_id": 7,
                    "created_at": "2026-08-04 19:16:57.407320",
                },
            )

    assert _alembic_cmd(url, "upgrade", S64).returncode == 0
    fp_s64 = _schema_fingerprint(engine)
    with engine.connect() as conn:
        assign_n_before = conn.execute(
            text(f"SELECT COUNT(*) FROM {ASSIGN_TABLE}")
        ).scalar_one()
        sha_before = conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one()

    proc = _alembic_cmd(url, "downgrade", S63)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert _current_revision(engine) == S63

    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        assert ASSIGN_TABLE in tables
        for name in RESOURCE_STATE_TABLES:
            assert name not in tables
        assign_n_mid = conn.execute(
            text(f"SELECT COUNT(*) FROM {ASSIGN_TABLE}")
        ).scalar_one()
        sha_mid = conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one()
    assert assign_n_mid == assign_n_before
    assert sha_mid == sha_before == tasks_json

    assert _alembic_cmd(url, "upgrade", S64).returncode == 0
    assert _current_revision(engine) == S64
    fp_re = _schema_fingerprint(engine)
    assert fp_re == fp_s64
    assert all(v == 0 for v in _row_counts(engine).values())


def test_runtime_create_all_excludes_resource_state_but_creates_runtime_tables(
    tmp_path: Path,
):
    """Both absences of RS tables and presence of runtime-owned tables."""
    from core.database import Base, DatabaseManager
    import models  # noqa: F401 — populate metadata

    db = tmp_path / "create_all_r3.db"
    engine = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(engine)

    mgr = DatabaseManager()
    with engine.begin() as conn:
        mgr._runtime_create_all(conn)
        tables = set(inspect(conn).get_table_names())

    for name in RESOURCE_STATE_TABLES:
        assert name in ALEMBIC_OWNED_TABLES
        assert name not in tables, f"create_all must not own {name}"

    # Runtime-owned tables must still materialize (create_all not broken).
    assert "execution_plan" in tables
    assert "machines" in tables
    assert "employees" in tables
    assert ASSIGN_TABLE not in tables


def test_alembic_connection_has_foreign_keys_on(tmp_path: Path):
    db = tmp_path / "fk_alembic.db"
    url = _async_sqlite_url(db)
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    engine = _sync_engine(db)
    assert _pragma_foreign_keys(engine) == 1


def test_database_manager_registers_foreign_keys(tmp_path: Path, monkeypatch):
    import asyncio

    from core.database import DatabaseManager

    db = tmp_path / "fk_dm.db"
    db.touch()
    monkeypatch.setenv("DATABASE_URL", _async_sqlite_url(db))
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENVIRONMENT", "test")

    mgr = DatabaseManager()

    async def _run():
        await mgr.init_db()
        assert mgr.engine is not None
        async with mgr.engine.connect() as conn:
            val = await conn.scalar(text("PRAGMA foreign_keys"))
            assert int(val) == 1
        await mgr.close_db()

    asyncio.run(_run())


def test_isolated_db_fixture_registers_foreign_keys():
    import models  # noqa: F401
    from tests._db_fixture import IsolatedDBFixture

    fixture = IsolatedDBFixture(prefix="r3_fk_fix_")
    fixture.setup()
    try:

        async def _check():
            async with fixture.session_maker() as session:
                val = await session.scalar(text("PRAGMA foreign_keys"))
                assert int(val) == 1

        fixture.loop.run_until_complete(_check())
    finally:
        fixture.teardown()
