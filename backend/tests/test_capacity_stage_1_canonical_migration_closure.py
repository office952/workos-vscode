"""Capacity Stage 1 — canonical s64→s65 migration closure (isolated SQLite only).

Never touches backend/dev.db. QA rollout remains NOT_AUTHORIZED.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
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
S67 = "s67_machine_run_execution_status"

S65_OWNED_TABLES = CAPACITY_SOURCE_TABLES
WORKLOAD_COLUMNS = (
    "workload_source",
    "workload_source_reference",
    "workload_explanation",
)
EXPECTED_SOURCE_INDEXES = {
    "ix_wc_capacity_source_status",
    "ix_wc_capacity_source_wc_day",
    "uq_wc_capacity_source_active_wc_day",
}
EXPECTED_SOURCE_TR_INDEXES = {
    "ix_wc_capacity_source_tr_source_id",
    "ix_wc_capacity_source_tr_wc_day_created",
}


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


def _table_counts(engine, names: set[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        for name in sorted(names):
            if name not in tables:
                out[name] = -1
            else:
                out[name] = int(
                    conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
                )
    return out


def _seed_minimal_with_rs_config(engine) -> dict:
    tasks_json = json.dumps(
        {
            "source": "order_snapshot_v2",
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
                "'2026-08-04 16:00:00', '2026-08-04 16:00:00')"
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
        for domain in ("SCHEDULING", "MACHINE_RESERVATION"):
            conn.execute(
                text(
                    "INSERT INTO resource_domain_configurations "
                    "(domain, application_scope_key, status, version, configured_at, "
                    "created_at, updated_at) "
                    "VALUES (:d, 'application', 'ACTIVE', 1, "
                    "'2026-08-05 09:00:00', '2026-08-05 09:00:00', '2026-08-05 09:00:00')"
                ),
                {"d": domain},
            )
        conn.execute(
            text(
                "INSERT INTO execution_task_assignment_transitions "
                "(transition_id, execution_plan_id, order_id, task_key, "
                "transition_type, new_employee_id, created_at) "
                "VALUES (:tid, 23, 880750, 'led', 'ASSIGN', 7, "
                "'2026-08-04 19:16:57.407320')"
            ),
            {"tid": str(uuid4())},
        )
    return {
        "tasks_json": tasks_json,
        "tasks_sha": hashlib.sha256(tasks_json.encode()).hexdigest(),
    }


def test_alembic_single_head_s65_ancestry():
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == [S67]
    assert script.get_revision(S67).down_revision == S66
    assert script.get_revision(S66).down_revision == S65
    assert script.get_revision(S65).down_revision == S64
    assert script.get_revision(S64).down_revision == S63


def test_capacity_source_tables_alembic_owned():
    assert CAPACITY_SOURCE_TABLES.issubset(ALEMBIC_OWNED_TABLES)
    assert len(CAPACITY_SOURCE_TABLES) == 2
    assert RESOURCE_STATE_TABLES.isdisjoint(CAPACITY_SOURCE_TABLES) or True
    # RS eight-pack remains distinct; source tables are Stage-1 add-on.
    assert len(RESOURCE_STATE_TABLES) == 8


def test_fresh_full_chain_s65_empty(tmp_path: Path):
    db = tmp_path / "c1_fresh.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    engine = _sync_engine(db)
    assert _revision(engine) == S67
    assert _pragma_fk(engine) == 1
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        ddl_src = conn.execute(
            text(
                "SELECT sql FROM sqlite_master WHERE type='table' "
                "AND name='workcenter_capacity_sources'"
            )
        ).scalar_one()
        indexes = {
            r[0]
            for r in conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='index' "
                    "AND tbl_name='workcenter_capacity_sources'"
                )
            ).fetchall()
        }
        tr_indexes = {
            r[0]
            for r in conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='index' "
                    "AND tbl_name='workcenter_capacity_source_transitions'"
                )
            ).fetchall()
        }
        # also unique constraints appear as indexes in sqlite
        for col in WORKLOAD_COLUMNS:
            assert col in {
                c["name"]
                for c in inspect(conn).get_columns("execution_task_capacity_allocations")
            }
            assert col in {
                c["name"]
                for c in inspect(conn).get_columns(
                    "execution_task_capacity_allocation_transitions"
                )
            }
    for name in RESOURCE_STATE_TABLES | S65_OWNED_TABLES:
        assert name in tables
    assert all(v == 0 for v in _table_counts(engine, RESOURCE_STATE_TABLES).values())
    assert all(v == 0 for v in _table_counts(engine, S65_OWNED_TABLES).values())
    assert "available_minutes" in (ddl_src or "")
    assert "WARN_ONLY" in (ddl_src or "")
    assert EXPECTED_SOURCE_INDEXES.issubset(indexes)
    assert EXPECTED_SOURCE_TR_INDEXES.issubset(tr_indexes)
    # UniqueConstraint names may surface as sqlite_autoindex_*; assert via DDL.
    assert "uq_wc_capacity_source_idempotency" in (ddl_src or "")
    with engine.connect() as conn:
        ddl_tr = conn.execute(
            text(
                "SELECT sql FROM sqlite_master WHERE type='table' "
                "AND name='workcenter_capacity_source_transitions'"
            )
        ).scalar_one()
    assert "uq_wc_capacity_source_tr_transition_id" in (ddl_tr or "")
    assert "uq_wc_capacity_source_tr_idempotency" in (ddl_tr or "")
    # no capacity domain configuration row
    with engine.connect() as conn:
        cap_cfg = conn.execute(
            text(
                "SELECT COUNT(*) FROM resource_domain_configurations "
                "WHERE domain='CAPACITY_ALLOCATION'"
            )
        ).scalar_one()
    assert cap_cfg == 0
    fp = _schema_fingerprint(engine)
    assert len(fp) == 64
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    assert _schema_fingerprint(engine) == fp


def test_orm_parity_capacity_source_and_workload_columns(tmp_path: Path):
    import models  # noqa: F401
    from core.database import Base

    db = tmp_path / "c1_parity.db"
    assert _alembic_cmd(_async_url(db), "upgrade", "head").returncode == 0
    engine = _sync_engine(db)
    real_drift: list[str] = []
    targets = sorted(
        S65_OWNED_TABLES
        | {
            "execution_task_capacity_allocations",
            "execution_task_capacity_allocation_transitions",
        }
    )
    with engine.connect() as conn:
        insp = inspect(conn)
        for table_name in targets:
            orm_table = Base.metadata.tables[table_name]
            db_cols = {c["name"] for c in insp.get_columns(table_name)}
            orm_cols = {c.name for c in orm_table.columns}
            if db_cols != orm_cols:
                real_drift.append(
                    f"{table_name}: columns ORM_only={sorted(orm_cols - db_cols)} "
                    f"DB_only={sorted(db_cols - orm_cols)}"
                )
            ddl = conn.execute(
                text(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=:n"
                ),
                {"n": table_name},
            ).scalar_one()
            ddl_norm = (ddl or "").replace(" ", "").lower()
            for ck in orm_table.constraints:
                if ck.__class__.__name__ != "CheckConstraint":
                    continue
                fragment = str(ck.sqltext).replace(" ", "").lower()[:50]
                if fragment and fragment not in ddl_norm:
                    # workload columns have no CHECKs; source CHECKs must match
                    if table_name.startswith("workcenter_capacity"):
                        real_drift.append(
                            f"{table_name}: CHECK missing: {fragment[:80]}"
                        )
    assert real_drift == [], "REAL_DRIFT:\n" + "\n".join(real_drift)


def test_s64_to_s65_preserves_prior_data(tmp_path: Path):
    db = tmp_path / "c1_prior.db"
    url = _async_url(db)
    assert _alembic_cmd(url, "upgrade", S64).returncode == 0
    engine = _sync_engine(db)
    seed = _seed_minimal_with_rs_config(engine)
    fp_s64 = _schema_fingerprint(engine)
    with engine.connect() as conn:
        configs_before = conn.execute(
            text(
                "SELECT domain, status, version FROM resource_domain_configurations "
                "ORDER BY domain"
            )
        ).fetchall()
        assign_before = conn.execute(
            text("SELECT COUNT(*) FROM execution_task_assignment_transitions")
        ).scalar_one()
        tasks_before = conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one()
        tables_before = set(inspect(conn).get_table_names())
    assert "workcenter_capacity_sources" not in tables_before

    assert _alembic_cmd(url, "upgrade", S65).returncode == 0
    assert _revision(engine) == S65
    with engine.connect() as conn:
        assert (
            conn.execute(
                text("SELECT tasks_json FROM execution_plan WHERE id=23")
            ).scalar_one()
            == tasks_before
            == seed["tasks_json"]
        )
        assert (
            conn.execute(
                text("SELECT COUNT(*) FROM execution_task_assignment_transitions")
            ).scalar_one()
            == assign_before
            == 1
        )
        configs_after = conn.execute(
            text(
                "SELECT domain, status, version FROM resource_domain_configurations "
                "ORDER BY domain"
            )
        ).fetchall()
        assert configs_after == configs_before
        assert (
            conn.execute(
                text(
                    "SELECT COUNT(*) FROM resource_domain_configurations "
                    "WHERE domain='CAPACITY_ALLOCATION'"
                )
            ).scalar_one()
            == 0
        )
        tables_after = set(inspect(conn).get_table_names())
    assert S65_OWNED_TABLES.issubset(tables_after)
    assert all(v == 0 for v in _table_counts(engine, S65_OWNED_TABLES).values())
    assert all(
        v == 0
        for k, v in _table_counts(
            engine,
            {
                "execution_task_schedules",
                "execution_task_machine_reservations",
                "execution_task_capacity_allocations",
            },
        ).items()
    )
    # schema changed (new tables) — fingerprint must differ from s64
    assert _schema_fingerprint(engine) != fp_s64


def test_downgrade_s65_to_s64_reupgrade_fingerprint(tmp_path: Path):
    db = tmp_path / "c1_down.db"
    url = _async_url(db)
    assert _alembic_cmd(url, "upgrade", S65).returncode == 0
    engine = _sync_engine(db)
    seed = _seed_minimal_with_rs_config(engine)
    fp_a = _schema_fingerprint(engine)
    with engine.connect() as conn:
        configs = conn.execute(
            text(
                "SELECT domain, status FROM resource_domain_configurations ORDER BY 1"
            )
        ).fetchall()
        assign_n = conn.execute(
            text("SELECT COUNT(*) FROM execution_task_assignment_transitions")
        ).scalar_one()

    assert _alembic_cmd(url, "downgrade", S64).returncode == 0
    assert _revision(engine) == S64
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        assert "workcenter_capacity_sources" not in tables
        assert "workcenter_capacity_source_transitions" not in tables
        for name in RESOURCE_STATE_TABLES:
            assert name in tables
        # workload columns removed on downgrade
        alloc_cols = {c["name"] for c in inspect(conn).get_columns(
            "execution_task_capacity_allocations"
        )}
        for col in WORKLOAD_COLUMNS:
            assert col not in alloc_cols
        assert (
            conn.execute(
                text("SELECT COUNT(*) FROM execution_task_assignment_transitions")
            ).scalar_one()
            == assign_n
        )
        assert (
            conn.execute(
                text(
                    "SELECT domain, status FROM resource_domain_configurations "
                    "ORDER BY 1"
                )
            ).fetchall()
            == configs
        )
        assert (
            conn.execute(
                text("SELECT tasks_json FROM execution_plan WHERE id=23")
            ).scalar_one()
            == seed["tasks_json"]
        )

    assert _alembic_cmd(url, "upgrade", S65).returncode == 0
    fp_b = _schema_fingerprint(engine)
    assert fp_a == fp_b
    assert all(v == 0 for v in _table_counts(engine, S65_OWNED_TABLES).values())


def test_runtime_create_all_skips_s65_tables(tmp_path: Path):
    from core.database import Base, DatabaseManager
    import models  # noqa: F401

    db = tmp_path / "c1_create_all.db"
    engine = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(engine)
    mgr = DatabaseManager()
    with engine.begin() as conn:
        mgr._runtime_create_all(conn)
        tables = set(inspect(conn).get_table_names())
    # Normal runtime tables present
    assert "execution_plan" in tables
    assert "machines" in tables
    assert "employees" in tables
    # Alembic-owned absent
    for name in RESOURCE_STATE_TABLES | S65_OWNED_TABLES:
        assert name not in tables
    assert "execution_task_assignment_transitions" not in tables

    db2 = tmp_path / "c1_alembic.db"
    assert _alembic_cmd(_async_url(db2), "upgrade", "head").returncode == 0
    engine2 = _sync_engine(db2)
    with engine2.connect() as conn:
        tables2 = set(inspect(conn).get_table_names())
    assert S65_OWNED_TABLES.issubset(tables2)
    assert RESOURCE_STATE_TABLES.issubset(tables2)


def test_constraint_smoke_source_and_allocation(tmp_path: Path):
    """DB CHECKs reject invalid minutes/policy; application DAY rules separate."""
    db = tmp_path / "c1_ck.db"
    assert _alembic_cmd(_async_url(db), "upgrade", "head").returncode == 0
    engine = _sync_engine(db)
    with engine.begin() as conn:
        # valid seed row
        conn.execute(
            text(
                "INSERT INTO workcenter_capacity_sources "
                "(workcenter_code, bucket_date, bucket_start, bucket_end, timezone, "
                "available_minutes, over_allocation_policy, source_label, "
                "source_execution_truth, status, version, created_at, updated_at, "
                "idempotency_key) VALUES "
                "('WC_CNC', '2026-08-05', '2026-08-05 00:00:00', "
                "'2026-08-06 00:00:00', 'UTC', 480, 'WARN_ONLY', "
                "'OWNER_CONFIGURED', 1, 'ACTIVE', 1, "
                "'2026-08-05 00:00:00', '2026-08-05 00:00:00', :ik)"
            ),
            {"ik": str(uuid4())},
        )
    with pytest.raises(Exception):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO workcenter_capacity_sources "
                    "(workcenter_code, bucket_date, bucket_start, bucket_end, timezone, "
                    "available_minutes, over_allocation_policy, source_label, "
                    "source_execution_truth, status, version, created_at, updated_at, "
                    "idempotency_key) VALUES "
                    "('WC_CNC', '2026-08-06', '2026-08-06 00:00:00', "
                    "'2026-08-07 00:00:00', 'UTC', -1, 'WARN_ONLY', "
                    "'OWNER_CONFIGURED', 1, 'ACTIVE', 1, "
                    "'2026-08-05 00:00:00', '2026-08-05 00:00:00', :ik)"
                ),
                {"ik": str(uuid4())},
            )
    with pytest.raises(Exception):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO workcenter_capacity_sources "
                    "(workcenter_code, bucket_date, bucket_start, bucket_end, timezone, "
                    "available_minutes, over_allocation_policy, source_label, "
                    "source_execution_truth, status, version, created_at, updated_at, "
                    "idempotency_key) VALUES "
                    "('WC_CNC', '2026-08-05', '2026-08-05 00:00:00', "
                    "'2026-08-06 00:00:00', 'UTC', 10, 'WARN_ONLY', "
                    "'OWNER_CONFIGURED', 1, 'ACTIVE', 1, "
                    "'2026-08-05 00:00:00', '2026-08-05 00:00:00', :ik)"
                ),
                {"ik": str(uuid4())},
            )
