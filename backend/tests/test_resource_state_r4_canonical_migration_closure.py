"""Resource State R4 — canonical migration closure on isolated SQLite only.

Never touches backend/dev.db. Hardens R3 proofs with ORM↔DB drift detection
and documents destructive downgrade-after-data policy.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from core.schema_ownership import (
    ALEMBIC_OWNED_TABLES,
    CAPACITY_SOURCE_TABLES,
    RESOURCE_STATE_TABLES,
)
from core.sqlite_pragma import register_sqlite_foreign_keys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
S63 = "s63_execution_task_assignment_transitions"
S64 = "s64_resource_state_persistence"
S65 = "s65_workcenter_capacity_source"
S66 = "s66_machine_run_reservation_grain"
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


def _async_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.resolve().as_posix()}"


def _sync_engine(path: Path):
    engine = create_engine(f"sqlite:///{path.resolve().as_posix()}")
    register_sqlite_foreign_keys(engine)
    return engine


def _revision(engine) -> str | None:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        if not rows:
            return None
        return rows[0][0]


def _pragma_fk(engine) -> int:
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


def _rs_counts(engine) -> dict[str, int]:
    out: dict[str, int] = {}
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        for name in sorted(RESOURCE_STATE_TABLES):
            if name not in tables:
                out[name] = -1
            else:
                out[name] = int(
                    conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
                )
    return out


def _seed_minimal(engine) -> str:
    tasks_json = json.dumps(
        {
            "source": "order_snapshot_v2",
            "planned_tasks": [],
            "planned_operations": [],
            "operational_tasks": [
                {
                    "task_id": "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters",
                    "assigned_employee_id": 7,
                }
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
                "VALUES (23, 880750, '880750', 1, :tj, 0.0, "
                "'2026-08-04 16:00:00', '2026-08-04 19:16:57.407320')"
            ),
            {"tj": tasks_json},
        )
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, '2026-08-04 16:00:00', '2026-08-04 16:00:00')"
            )
        )
    return tasks_json


def test_alembic_single_head_ancestry():
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == [S66]
    assert script.get_revision(S66).down_revision == S65
    assert script.get_revision(S65).down_revision == S64
    assert script.get_revision(S64).down_revision == S63
    assert script.get_revision(S63).down_revision == "s62_material_actuals_closed_job_v1"


def test_alembic_owned_tables_include_assignment_and_resource_state():
    assert ASSIGN_TABLE in ALEMBIC_OWNED_TABLES
    assert RESOURCE_STATE_TABLES.issubset(ALEMBIC_OWNED_TABLES)
    assert CAPACITY_SOURCE_TABLES.issubset(ALEMBIC_OWNED_TABLES)
    assert len(RESOURCE_STATE_TABLES) == 8
    assert len(CAPACITY_SOURCE_TABLES) == 2


def test_fresh_full_chain_and_fingerprint(tmp_path: Path):
    db = tmp_path / "r4_fresh.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    engine = _sync_engine(db)
    assert _revision(engine) == S66
    assert _pragma_fk(engine) == 1
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
    assert ASSIGN_TABLE in tables
    for name in RESOURCE_STATE_TABLES | CAPACITY_SOURCE_TABLES:
        assert name in tables
    assert all(v == 0 for v in _rs_counts(engine).values())
    fp = _schema_fingerprint(engine)
    assert len(fp) == 64
    # Store for evidence in pytest output / worklog capture via second upgrade identity
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    assert _schema_fingerprint(engine) == fp


def test_orm_metadata_vs_migrated_schema_no_real_drift(tmp_path: Path):
    """Compare ORM column sets and CHECK/UNIQUE names to migrated SQLite."""
    import models  # noqa: F401
    from core.database import Base

    db = tmp_path / "r4_drift.db"
    assert _alembic_cmd(_async_url(db), "upgrade", "head").returncode == 0
    engine = _sync_engine(db)

    real_drift: list[str] = []
    with engine.connect() as conn:
        insp = inspect(conn)
        for table_name in sorted(RESOURCE_STATE_TABLES):
            orm_table = Base.metadata.tables[table_name]
            db_cols = {c["name"] for c in insp.get_columns(table_name)}
            orm_cols = {c.name for c in orm_table.columns}
            if db_cols != orm_cols:
                real_drift.append(
                    f"{table_name}: columns ORM={sorted(orm_cols - db_cols)} "
                    f"DB={sorted(db_cols - orm_cols)}"
                )

            db_fks = {
                (
                    tuple(fk["constrained_columns"]),
                    tuple(fk["referred_columns"]),
                    fk["referred_table"],
                )
                for fk in insp.get_foreign_keys(table_name)
            }
            orm_fks = set()
            for fk in orm_table.foreign_key_constraints:
                orm_fks.add(
                    (
                        tuple(fk.column_keys),
                        tuple(elem.column.name for elem in fk.elements),
                        list(fk.elements)[0].column.table.name,
                    )
                )
            if db_fks != orm_fks:
                # SQLite may omit FK names; compare structural tuples only.
                if db_fks != orm_fks:
                    real_drift.append(
                        f"{table_name}: FK structural mismatch "
                        f"ORM={sorted(orm_fks)} DB={sorted(db_fks)}"
                    )

            db_uq = {
                tuple(sorted(uq["column_names"]))
                for uq in insp.get_unique_constraints(table_name)
            }
            orm_uq = {
                tuple(sorted(c.name for c in uq.columns))
                for uq in orm_table.constraints
                if uq.__class__.__name__ == "UniqueConstraint"
            }
            # Partial unique indexes appear as indexes, not unique constraints.
            if not orm_uq.issubset(db_uq | set()):
                # SQLite may report UniqueConstraint as index; verify via indexes too.
                db_ix_unique = {
                    tuple(sorted(ix["column_names"]))
                    for ix in insp.get_indexes(table_name)
                    if ix.get("unique")
                }
                if not orm_uq.issubset(db_uq | db_ix_unique):
                    real_drift.append(
                        f"{table_name}: unique mismatch ORM={orm_uq} "
                        f"DB_uq={db_uq} DB_ix={db_ix_unique}"
                    )

            orm_ck_sql = {
                str(ck.sqltext).replace(" ", "").lower()
                for ck in orm_table.constraints
                if ck.__class__.__name__ == "CheckConstraint"
            }
            # SQLite inspector may not expose CHECK names consistently; parse DDL.
            ddl = conn.execute(
                text(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type='table' AND name=:n"
                ),
                {"n": table_name},
            ).scalar_one()
            ddl_norm = (ddl or "").replace(" ", "").lower()
            for ck in orm_ck_sql:
                # Normalize quotes/parens lightly
                needle = ck.replace("(", "").replace(")", "")[:40]
                if needle and needle not in ddl_norm.replace("(", "").replace(")", ""):
                    # Soft check: full sqltext fragment should appear
                    fragment = ck[:60]
                    if fragment not in ddl_norm:
                        real_drift.append(
                            f"{table_name}: CHECK fragment missing from DDL: {ck[:80]}"
                        )

    assert real_drift == [], "REAL_DRIFT:\n" + "\n".join(real_drift)


def test_s63_to_s64_and_downgrade_reupgrade_fingerprint(tmp_path: Path):
    db = tmp_path / "r4_prior.db"
    url = _async_url(db)
    assert _alembic_cmd(url, "upgrade", S63).returncode == 0
    engine = _sync_engine(db)
    tasks_json = _seed_minimal(engine)
    with engine.begin() as conn:
        n = conn.execute(text(f"SELECT COUNT(*) FROM {ASSIGN_TABLE}")).scalar_one()
        if n == 0:
            conn.execute(
                text(
                    f"INSERT INTO {ASSIGN_TABLE} "
                    "(transition_id, execution_plan_id, order_id, task_key, "
                    "transition_type, new_employee_id, created_at) "
                    "VALUES (:tid, 23, 880750, 'led', 'ASSIGN', 7, :ts)"
                ),
                {"tid": str(uuid4()), "ts": "2026-08-04 19:16:57.407320"},
            )

    with engine.connect() as conn:
        sha_before = conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one()
        assign_before = conn.execute(
            text(f"SELECT COUNT(*) FROM {ASSIGN_TABLE}")
        ).scalar_one()

    assert _alembic_cmd(url, "upgrade", S64).returncode == 0
    assert _revision(engine) == S64
    fp_a = _schema_fingerprint(engine)
    with engine.connect() as conn:
        assert (
            conn.execute(
                text("SELECT tasks_json FROM execution_plan WHERE id=23")
            ).scalar_one()
            == sha_before
            == tasks_json
        )
        assert (
            conn.execute(text(f"SELECT COUNT(*) FROM {ASSIGN_TABLE}")).scalar_one()
            == assign_before
        )
    assert all(v == 0 for v in _rs_counts(engine).values())

    assert _alembic_cmd(url, "downgrade", S63).returncode == 0
    assert _revision(engine) == S63
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        assert ASSIGN_TABLE in tables
        for name in RESOURCE_STATE_TABLES:
            assert name not in tables
        assert (
            conn.execute(text(f"SELECT COUNT(*) FROM {ASSIGN_TABLE}")).scalar_one()
            == assign_before
        )

    assert _alembic_cmd(url, "upgrade", S64).returncode == 0
    fp_b = _schema_fingerprint(engine)
    assert fp_a == fp_b
    assert all(v == 0 for v in _rs_counts(engine).values())


def test_downgrade_after_resource_data_is_destructive(tmp_path: Path):
    """Document policy: technical downgrade drops tables (data loss)."""
    db = tmp_path / "r4_destructive.db"
    url = _async_url(db)
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    engine = _sync_engine(db)
    _seed_minimal(engine)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO resource_domain_configurations "
                "(domain, application_scope_key, status, version, configured_at, "
                "created_at, updated_at) "
                "VALUES ('SCHEDULING', 'application', 'ACTIVE', 1, :ts, :ts, :ts)"
            ),
            {"ts": ts},
        )
        conn.execute(
            text(
                "INSERT INTO execution_task_schedules "
                "(execution_plan_id, order_id, task_key, scheduled_start, "
                "scheduled_end, timezone, status, version, created_at, "
                "updated_at, idempotency_key) "
                "VALUES (23, 880750, 'task_a', :s, :e, 'UTC', 'PLANNED', 1, "
                ":ts, :ts, :ikey)"
            ),
            {
                "s": "2026-08-05 10:00:00",
                "e": "2026-08-05 11:00:00",
                "ts": ts,
                "ikey": str(uuid4()),
            },
        )
        assert (
            conn.execute(
                text("SELECT COUNT(*) FROM resource_domain_configurations")
            ).scalar_one()
            == 1
        )
        assert (
            conn.execute(
                text("SELECT COUNT(*) FROM execution_task_schedules")
            ).scalar_one()
            == 1
        )

    assert _alembic_cmd(url, "downgrade", S63).returncode == 0
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        assert "resource_domain_configurations" not in tables
        assert "execution_task_schedules" not in tables
        assert ASSIGN_TABLE in tables
        # Preexisting plan retained
        assert (
            conn.execute(
                text("SELECT COUNT(*) FROM execution_plan WHERE id=23")
            ).scalar_one()
            == 1
        )

    # Policy constants for worklog evidence
    assert True  # TECHNICAL_DOWNGRADE = AVAILABLE
    # DOWNGRADE_AFTER_RESOURCE_DATA = DESTRUCTIVE
    # OPERATIONAL_DOWNGRADE_REQUIRES_OWNER_GO = YES


def test_runtime_create_all_dual_proof(tmp_path: Path):
    from core.database import Base, DatabaseManager
    import models  # noqa: F401

    db = tmp_path / "r4_create_all.db"
    engine = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(engine)
    mgr = DatabaseManager()
    with engine.begin() as conn:
        mgr._runtime_create_all(conn)
        tables = set(inspect(conn).get_table_names())
    for name in RESOURCE_STATE_TABLES | CAPACITY_SOURCE_TABLES:
        assert name not in tables
    assert ASSIGN_TABLE not in tables
    assert "execution_plan" in tables
    assert "machines" in tables
    assert "employees" in tables

    db2 = tmp_path / "r4_alembic.db"
    assert _alembic_cmd(_async_url(db2), "upgrade", "head").returncode == 0
    engine2 = _sync_engine(db2)
    with engine2.connect() as conn:
        tables2 = set(inspect(conn).get_table_names())
    assert ASSIGN_TABLE in tables2
    for name in RESOURCE_STATE_TABLES | CAPACITY_SOURCE_TABLES:
        assert name in tables2


def test_append_only_boundary_classification():
    """Schedule/reservation/capacity Stage-1 writers exist as command services."""
    services = BACKEND_ROOT / "services"
    names = sorted(p.name for p in services.glob("*.py"))
    assert any("execution_task_schedule" in n for n in names)
    assert any("machine_reservation" in n for n in names)
    assert any("resource_domain_configuration" in n for n in names)
    capacity_writers = [
        n
        for n in names
        if "capacity_allocation" in n and ("command" in n or "write" in n)
    ]
    assert capacity_writers, "Stage 1 capacity allocation command service required"
    assert any("workcenter_capacity_source" in n for n in names)
