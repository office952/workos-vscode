"""Wave 10 closure — canonical Alembic chain, ownership, collision, downgrade.

All scenarios use isolated temporary databases. Never touches backend/dev.db.
PostgreSQL runtime is skipped when no isolated PG URL is available.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from core.schema_ownership import (
    ALEMBIC_OWNED_TABLES,
    CANONICAL_ASSIGNMENT_TRANSITION_INDEXES,
    LEGACY_ORM_ASSIGNMENT_TRANSITION_INDEX_NAMES,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
S62 = "s62_material_actuals_closed_job_v1"
S63 = "s63_execution_task_assignment_transitions"
TABLE = "execution_task_assignment_transitions"


def _ops_envelope(tasks: list[dict]) -> str:
    return json.dumps(
        {
            "source": "order_snapshot_v2",
            "planned_tasks": [],
            "planned_operations": [],
            "operational_tasks": tasks,
        }
    )


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
    return create_engine(f"sqlite:///{path.resolve().as_posix()}")


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


def _index_names(engine, table: str) -> set[str]:
    with engine.connect() as conn:
        if table not in set(inspect(conn).get_table_names()):
            return set()
        names = {ix["name"] for ix in inspect(conn).get_indexes(table)}
        # SQLite unique constraints also appear as autoindexes
        return {n for n in names if n}


def _insert_minimal_row(conn, table: str, values: dict) -> None:
    """Insert using only columns that exist; rely on DB defaults for the rest."""
    cols = {c["name"] for c in inspect(conn).get_columns(table)}
    use = {k: v for k, v in values.items() if k in cols}
    col_sql = ", ".join(use.keys())
    placeholders = ", ".join(f":{k}" for k in use)
    conn.execute(
        text(f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})"),
        use,
    )


def _seed_assignment(engine, *, plan_id: int = 23, order_id: int = 880750) -> str:
    tasks_json = _ops_envelope(
        [
            {
                "task_id": "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters",
                "assigned_employee_id": 7,
                "assignment_actor_user_id": "dev-admin-user-00000000",
                "assignment_updated_at": "2026-08-04T16:16:57.406324+00:00",
                "assignment_source": "canonical_controlled_assign_v1",
            },
            {"task_id": "other_unassigned"},
        ]
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
                "id": plan_id,
                "order_id": order_id,
                "order_code": str(order_id),
                "snapshot_version": 1,
                "tasks_json": tasks_json,
                "total_estimated_time_minutes": 0.0,
                "created_at": "2026-08-04 16:00:00",
                "updated_at": "2026-08-04 19:16:57.407320",
            },
        )
    return tasks_json


# ---------------------------------------------------------------------------
# Migration graph
# ---------------------------------------------------------------------------


def test_migration_graph_single_head_and_s63_predecessor():
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert heads == [S63], heads
    rev = script.get_revision(S63)
    assert rev is not None
    assert rev.down_revision == S62
    assert rev.branch_labels in (None, set(), ())
    assert rev.dependencies in (None, ())


# ---------------------------------------------------------------------------
# Fresh / prior / collision / downgrade via real alembic CLI
# ---------------------------------------------------------------------------


def test_scenario_a_fresh_empty_database_upgrade_head(tmp_path: Path):
    db = tmp_path / "fresh.db"
    url = _async_sqlite_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout

    engine = _sync_engine(db)
    assert _current_revision(engine) == S63
    with engine.connect() as conn:
        assert TABLE in set(inspect(conn).get_table_names())
        cols = {c["name"] for c in inspect(conn).get_columns(TABLE)}
        assert "transition_id" in cols
        assert "execution_plan_id" in cols
        n = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE}")).scalar_one()
        assert n == 0
    names = _index_names(engine, TABLE)
    canonical = {n for n, _ in CANONICAL_ASSIGNMENT_TRANSITION_INDEXES}
    assert canonical.issubset(names), names
    legacy = names & LEGACY_ORM_ASSIGNMENT_TRANSITION_INDEX_NAMES
    assert legacy == set(), f"fresh migration must not create ORM auto-names: {legacy}"


def test_scenario_b_prior_revision_to_head_backfill(tmp_path: Path):
    db = tmp_path / "prior.db"
    url = _async_sqlite_url(db)
    proc = _alembic_cmd(url, "upgrade", S62)
    assert proc.returncode == 0, proc.stderr + proc.stdout

    engine = _sync_engine(db)
    assert _current_revision(engine) == S62
    with engine.connect() as conn:
        assert TABLE not in set(inspect(conn).get_table_names())

    tasks_json = _seed_assignment(engine)
    with engine.connect() as conn:
        sha_before = conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one()
        upd_before = conn.execute(
            text("SELECT updated_at FROM execution_plan WHERE id=23")
        ).scalar_one()
        assert sha_before == tasks_json

    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert _current_revision(engine) == S63

    with engine.connect() as conn:
        assert TABLE in set(inspect(conn).get_table_names())
        n = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE}")).scalar_one()
        assert n == 1
        row = conn.execute(
            text(
                f"SELECT transition_type, new_employee_id, source, reason_code "
                f"FROM {TABLE}"
            )
        ).one()
        assert row[0] == "ASSIGN"
        assert row[1] == 7
        assert row[2] == "LEGACY_EMBEDDED_BACKFILL"
        assert row[3] == "INITIAL_ASSIGNMENT_BACKFILL"
        sha_after = conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one()
        upd_after = conn.execute(
            text("SELECT updated_at FROM execution_plan WHERE id=23")
        ).scalar_one()
        assert sha_after == sha_before
        assert upd_after == upd_before


def test_scenario_collision_create_all_table_then_alembic_upgrade(tmp_path: Path):
    """Table present via create_all; alembic_version still at s62; upgrade head."""
    db = tmp_path / "collision.db"
    url = _async_sqlite_url(db)
    assert _alembic_cmd(url, "upgrade", S62).returncode == 0

    engine = _sync_engine(db)
    _seed_assignment(engine)

    # Simulate historical runtime create_all of the ORM model (not Alembic).
    from core.database import Base
    import models.execution_task_assignment_transition  # noqa: F401

    with engine.begin() as conn:
        Base.metadata.create_all(conn, tables=[Base.metadata.tables[TABLE]])
        assert TABLE in set(inspect(conn).get_table_names())
        assert _current_revision(engine) == S62

    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert _current_revision(engine) == S63

    names = _index_names(engine, TABLE)
    canonical = {n for n, _ in CANONICAL_ASSIGNMENT_TRANSITION_INDEXES}
    assert canonical.issubset(names)

    with engine.connect() as conn:
        n = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE}")).scalar_one()
        assert n == 1
        # Idempotent second upgrade
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    with engine.connect() as conn:
        n2 = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE}")).scalar_one()
        assert n2 == 1


def test_scenario_downgrade_reupgrade_isolated(tmp_path: Path):
    db = tmp_path / "down.db"
    url = _async_sqlite_url(db)
    assert _alembic_cmd(url, "upgrade", S62).returncode == 0
    engine = _sync_engine(db)
    _seed_assignment(engine)
    with engine.connect() as conn:
        sha_before = conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one()
        upd_before = conn.execute(
            text("SELECT updated_at FROM execution_plan WHERE id=23")
        ).scalar_one()

    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    with engine.connect() as conn:
        assert conn.execute(text(f"SELECT COUNT(*) FROM {TABLE}")).scalar_one() == 1

    proc = _alembic_cmd(url, "downgrade", S62)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert _current_revision(engine) == S62
    with engine.connect() as conn:
        assert TABLE not in set(inspect(conn).get_table_names())
        sha_mid = conn.execute(
            text("SELECT tasks_json FROM execution_plan WHERE id=23")
        ).scalar_one()
        upd_mid = conn.execute(
            text("SELECT updated_at FROM execution_plan WHERE id=23")
        ).scalar_one()
        assert sha_mid == sha_before
        assert upd_mid == upd_before

    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    with engine.connect() as conn:
        n = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE}")).scalar_one()
        assert n == 1
        tid1 = conn.execute(
            text(f"SELECT transition_id FROM {TABLE}")
        ).scalar_one()

    # Second upgrade idempotent (revision already head)
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    with engine.connect() as conn:
        n2 = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE}")).scalar_one()
        tid2 = conn.execute(
            text(f"SELECT transition_id FROM {TABLE}")
        ).scalar_one()
        assert n2 == 1
        assert tid1 == tid2


def test_backfill_idempotent_via_repeated_s63_body(tmp_path: Path):
    """Re-run backfill service after canonical upgrade → zero new rows."""
    from services.assignment_transition_backfill_service import (
        run_legacy_embedded_backfill,
    )

    db = tmp_path / "idem.db"
    url = _async_sqlite_url(db)
    assert _alembic_cmd(url, "upgrade", S62).returncode == 0
    engine = _sync_engine(db)
    _seed_assignment(engine)
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0

    with engine.begin() as conn:
        first = run_legacy_embedded_backfill(conn)
        second = run_legacy_embedded_backfill(conn)
    assert first.inserted == 0  # already inserted by migration
    assert first.skipped_existing == 1
    assert second.inserted == 0
    assert second.skipped_existing == 1


# ---------------------------------------------------------------------------
# Runtime create_all ownership
# ---------------------------------------------------------------------------


def test_runtime_create_all_excludes_alembic_owned_from_table_list():
    from core.database import Base
    import models.execution_task_assignment_transition  # noqa: F401

    assert TABLE in ALEMBIC_OWNED_TABLES
    assert TABLE in Base.metadata.tables
    selected = [
        name
        for name in Base.metadata.tables
        if name not in ALEMBIC_OWNED_TABLES
    ]
    assert TABLE not in selected


def test_orm_index_names_match_canonical_migration_only():
    from models.execution_task_assignment_transition import (
        ExecutionTaskAssignmentTransition,
    )

    table = ExecutionTaskAssignmentTransition.__table__
    ix_names = {ix.name for ix in table.indexes}
    canonical = {n for n, _ in CANONICAL_ASSIGNMENT_TRANSITION_INDEXES}
    assert ix_names == canonical
    assert ix_names.isdisjoint(LEGACY_ORM_ASSIGNMENT_TRANSITION_INDEX_NAMES)


# ---------------------------------------------------------------------------
# PostgreSQL — skip unless isolated URL provided
# ---------------------------------------------------------------------------


def test_postgresql_canonical_upgrade_if_available():
    pg_url = os.environ.get("WORKOS_ISOLATED_POSTGRES_URL", "").strip()
    if not pg_url:
        pytest.skip(
            "PRODUCTION_DATABASE_MIGRATION_RUNTIME not verified: "
            "WORKOS_ISOLATED_POSTGRES_URL unset / no isolated PostgreSQL"
        )
    assert pg_url.startswith("postgresql")
    proc = _alembic_cmd(pg_url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
