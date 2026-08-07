"""s67 MACHINE_RUN execution status schema foundation (isolated SQLite).

Never touches backend/dev.db. No START/COMPLETE command runtime.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from core.sqlite_pragma import register_sqlite_foreign_keys
from models.machine_run import MACHINE_RUN_STATUSES, MachineRun

BACKEND_ROOT = Path(__file__).resolve().parents[1]
S66 = "s66_machine_run_reservation_grain"
S67 = "s67_machine_run_execution_status"
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
    tasks = {
        "source": "order_snapshot_v2",
        "operational_tasks": [
            {
                "task_id": FACE_A,
                "resource_mode": "MACHINE_BOUND",
                "machine_capability_code": "CNC_ROUTER_CUTTING",
                "batch_eligible": True,
            },
            {
                "task_id": FACE_B,
                "resource_mode": "MACHINE_BOUND",
                "machine_capability_code": "CNC_ROUTER_CUTTING",
                "batch_eligible": True,
            },
        ],
    }
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, '2026-08-07 12:00:00', '2026-08-07 12:00:00')"
            )
        )
        for pid, oid in ((21, 880751), (22, 880752)):
            conn.execute(
                text(
                    "INSERT INTO execution_plan "
                    "(id, order_id, order_code, snapshot_version, tasks_json, "
                    "total_estimated_time_minutes, created_at, updated_at) "
                    "VALUES (:id, :oid, :code, 1, :tj, 0.0, "
                    "'2026-08-07 12:00:00', '2026-08-07 12:00:00')"
                ),
                {
                    "id": pid,
                    "oid": oid,
                    "code": str(oid),
                    "tj": json.dumps(tasks),
                },
            )


def _insert_run(
    conn,
    *,
    run_id: int,
    status: str,
    ik: str,
    task_key: str,
    plan_id: int = 21,
    order_id: int = 880751,
    start: str = "2026-08-07 10:00:00",
    end: str = "2026-08-07 11:00:00",
) -> None:
    res_status = (
        status
        if status in ("HELD", "RESERVED", "RELEASED", "CANCELLED")
        else "RESERVED"
    )
    conn.execute(
        text(
            "INSERT INTO machine_runs "
            "(id, machine_id, status, version, timezone, created_at, updated_at, "
            "idempotency_key) "
            "VALUES (:id, 1, :st, 1, 'UTC', :n, :n, :ik)"
        ),
        {"id": run_id, "st": status, "n": start, "ik": ik},
    )
    conn.execute(
        text(
            "INSERT INTO execution_task_machine_reservations "
            "(id, machine_run_id, machine_id, reservation_start, reservation_end, "
            "timezone, status, version, created_at, updated_at, idempotency_key) "
            "VALUES (:id, :rid, 1, :s, :e, 'UTC', :st, 1, :s, :s, :ik)"
        ),
        {
            "id": run_id,
            "rid": run_id,
            "st": res_status,
            "s": start,
            "e": end,
            "ik": str(uuid.uuid4()),
        },
    )
    part_status = "ACTIVE" if status in ("HELD", "RESERVED") else "REMOVED"
    conn.execute(
        text(
            "INSERT INTO machine_run_participants "
            "(machine_run_id, execution_plan_id, order_id, task_key, status, "
            "added_at, added_by, removed_at, removed_by) "
            "VALUES (:rid, :pid, :oid, :tk, :pst, :n, 'admin-1', "
            ":rm, :rb)"
        ),
        {
            "rid": run_id,
            "pid": plan_id,
            "oid": order_id,
            "tk": task_key,
            "pst": part_status,
            "n": start,
            "rm": None if part_status == "ACTIVE" else start,
            "rb": None if part_status == "ACTIVE" else "admin-1",
        },
    )
    conn.execute(
        text(
            "INSERT INTO machine_run_transitions "
            "(transition_id, machine_run_id, machine_id, operation, previous_status, "
            "new_status, previous_version, new_version, actor_user_id, "
            "idempotency_key, created_at) "
            "VALUES (:tid, :rid, 1, 'CREATE_MACHINE_RUN', NULL, 'HELD', NULL, 1, "
            "'admin-1', :ik, :n)"
        ),
        {
            "tid": str(uuid.uuid4()),
            "rid": run_id,
            "ik": str(uuid.uuid4()),
            "n": start,
        },
    )


def test_alembic_single_head_s67_ancestry():
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == [S67]
    assert script.get_revision(S67).down_revision == S66


def test_orm_status_tuple_includes_execution():
    assert "RUNNING" in MACHINE_RUN_STATUSES
    assert "COMPLETED" in MACHINE_RUN_STATUSES
    assert MachineRun.started_at is not None
    assert MachineRun.completed_at is not None


def test_fresh_full_chain_s67(tmp_path: Path):
    db = tmp_path / "s67_fresh.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    engine = _sync_engine(db)
    assert _revision(engine) == S67
    with engine.connect() as conn:
        assert int(conn.execute(text("PRAGMA foreign_keys")).scalar_one()) == 1
        assert conn.execute(text("PRAGMA foreign_key_check")).fetchall() == []
        cols = {c["name"] for c in inspect(conn).get_columns("machine_runs")}
        assert "started_at" in cols
        assert "completed_at" in cols
        ddl = conn.execute(
            text(
                "SELECT sql FROM sqlite_master WHERE type='table' "
                "AND name='machine_runs'"
            )
        ).scalar_one()
    assert "RUNNING" in (ddl or "")
    assert "COMPLETED" in (ddl or "")
    fp = _schema_fingerprint(engine)
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    assert _schema_fingerprint(engine) == fp


def test_s66_to_s67_preserves_commitment_rows(tmp_path: Path):
    db = tmp_path / "s67_from_s66.db"
    url = _async_url(db)
    assert _alembic_cmd(url, "upgrade", S66).returncode == 0
    engine = _sync_engine(db)
    _seed_plan_machine(engine)
    with engine.begin() as conn:
        _insert_run(
            conn, run_id=1, status="HELD", ik=str(uuid.uuid4()), task_key=FACE_A
        )
        _insert_run(
            conn,
            run_id=2,
            status="RESERVED",
            ik=str(uuid.uuid4()),
            task_key=FACE_B,
            plan_id=22,
            order_id=880752,
        )
        _insert_run(
            conn,
            run_id=3,
            status="RELEASED",
            ik=str(uuid.uuid4()),
            task_key="hist-released",
        )
        _insert_run(
            conn,
            run_id=4,
            status="CANCELLED",
            ik=str(uuid.uuid4()),
            task_key="hist-cancelled",
        )
        before = conn.execute(
            text(
                "SELECT id, status, version, timezone FROM machine_runs ORDER BY id"
            )
        ).fetchall()
        before_parts = conn.execute(
            text(
                "SELECT machine_run_id, task_key, status "
                "FROM machine_run_participants ORDER BY machine_run_id"
            )
        ).fetchall()
        before_res = conn.execute(
            text(
                "SELECT id, machine_run_id, status, version "
                "FROM execution_task_machine_reservations ORDER BY id"
            )
        ).fetchall()

    assert _alembic_cmd(url, "upgrade", S67).returncode == 0
    assert _revision(engine) == S67
    with engine.connect() as conn:
        after = conn.execute(
            text(
                "SELECT id, status, version, timezone, started_at, completed_at "
                "FROM machine_runs ORDER BY id"
            )
        ).fetchall()
        after_parts = conn.execute(
            text(
                "SELECT machine_run_id, task_key, status "
                "FROM machine_run_participants ORDER BY machine_run_id"
            )
        ).fetchall()
        after_res = conn.execute(
            text(
                "SELECT id, machine_run_id, status, version "
                "FROM execution_task_machine_reservations ORDER BY id"
            )
        ).fetchall()
        assert conn.execute(text("PRAGMA foreign_key_check")).fetchall() == []
    assert [(r[0], r[1], r[2], r[3]) for r in after] == [
        (b[0], b[1], b[2], b[3]) for b in before
    ]
    assert all(r[4] is None and r[5] is None for r in after)
    assert after_parts == before_parts
    assert after_res == before_res


def test_structural_running_completed_and_transitions(tmp_path: Path):
    db = tmp_path / "s67_struct.db"
    url = _async_url(db)
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    engine = _sync_engine(db)
    _seed_plan_machine(engine)
    now = "2026-08-07 10:00:00"
    end = "2026-08-07 11:00:00"
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO machine_runs "
                "(id, machine_id, status, version, timezone, created_at, updated_at, "
                "idempotency_key, started_at) "
                "VALUES (10, 1, 'RUNNING', 2, 'UTC', :n, :n, :ik, :n)"
            ),
            {"n": now, "ik": str(uuid.uuid4())},
        )
        conn.execute(
            text(
                "INSERT INTO execution_task_machine_reservations "
                "(id, machine_run_id, machine_id, reservation_start, reservation_end, "
                "timezone, status, version, created_at, updated_at, idempotency_key) "
                "VALUES (10, 10, 1, :s, :e, 'UTC', 'RESERVED', 2, :s, :s, :ik)"
            ),
            {"s": now, "e": end, "ik": str(uuid.uuid4())},
        )
        conn.execute(
            text(
                "INSERT INTO machine_run_transitions "
                "(transition_id, machine_run_id, machine_id, operation, "
                "previous_status, new_status, previous_version, new_version, "
                "idempotency_key, created_at) "
                "VALUES (:tid, 10, 1, 'START_MACHINE_RUN', 'RESERVED', 'RUNNING', "
                "1, 2, :ik, :n)"
            ),
            {"tid": str(uuid.uuid4()), "ik": str(uuid.uuid4()), "n": now},
        )
        conn.execute(
            text(
                "UPDATE machine_runs SET status='COMPLETED', completed_at=:n, "
                "version=3 WHERE id=10"
            ),
            {"n": end},
        )
        conn.execute(
            text(
                "INSERT INTO machine_run_transitions "
                "(transition_id, machine_run_id, machine_id, operation, "
                "previous_status, new_status, previous_version, new_version, "
                "idempotency_key, created_at) "
                "VALUES (:tid, 10, 1, 'COMPLETE_MACHINE_RUN', 'RUNNING', "
                "'COMPLETED', 2, 3, :ik, :n)"
            ),
            {"tid": str(uuid.uuid4()), "ik": str(uuid.uuid4()), "n": end},
        )
        row = conn.execute(
            text(
                "SELECT status, started_at, completed_at FROM machine_runs WHERE id=10"
            )
        ).fetchone()
        assert row[0] == "COMPLETED"
        assert row[1] is not None
        assert row[2] is not None
        assert conn.execute(text("PRAGMA foreign_key_check")).fetchall() == []

    # Reservation vocabulary must still reject RUNNING.
    with pytest.raises(Exception):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO execution_task_machine_reservations "
                    "(id, machine_run_id, machine_id, reservation_start, "
                    "reservation_end, timezone, status, version, created_at, "
                    "updated_at, idempotency_key) "
                    "VALUES (99, 10, 1, :s, :e, 'UTC', 'RUNNING', 1, :s, :s, :ik)"
                ),
                {"s": now, "e": end, "ik": str(uuid.uuid4())},
            )


def test_downgrade_guard_with_running_row(tmp_path: Path):
    db = tmp_path / "s67_down_guard.db"
    url = _async_url(db)
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    engine = _sync_engine(db)
    _seed_plan_machine(engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO machine_runs "
                "(id, machine_id, status, version, timezone, created_at, updated_at, "
                "idempotency_key, started_at) "
                "VALUES (1, 1, 'RUNNING', 1, 'UTC', "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00', :ik, "
                "'2026-08-07 10:00:00')"
            ),
            {"ik": str(uuid.uuid4())},
        )
    proc = _alembic_cmd(url, "downgrade", S66)
    assert proc.returncode != 0
    assert "downgrade blocked" in (proc.stderr + proc.stdout)


def test_downgrade_reupgrade_without_execution_rows(tmp_path: Path):
    db = tmp_path / "s67_down_ok.db"
    url = _async_url(db)
    assert _alembic_cmd(url, "upgrade", "head").returncode == 0
    engine = _sync_engine(db)
    _seed_plan_machine(engine)
    with engine.begin() as conn:
        _insert_run(
            conn, run_id=1, status="HELD", ik=str(uuid.uuid4()), task_key=FACE_A
        )
    assert _alembic_cmd(url, "downgrade", S66).returncode == 0
    assert _revision(engine) == S66
    with engine.connect() as conn:
        cols = {c["name"] for c in inspect(conn).get_columns("machine_runs")}
        assert "started_at" not in cols
        assert "completed_at" not in cols
        ddl = conn.execute(
            text(
                "SELECT sql FROM sqlite_master WHERE type='table' "
                "AND name='machine_runs'"
            )
        ).scalar_one()
        assert "RUNNING" not in (ddl or "")
        assert conn.execute(
            text("SELECT status FROM machine_runs WHERE id=1")
        ).scalar_one() == "HELD"
    assert _alembic_cmd(url, "upgrade", S67).returncode == 0
    assert _revision(engine) == S67
    with engine.connect() as conn:
        cols = {c["name"] for c in inspect(conn).get_columns("machine_runs")}
        assert "started_at" in cols
        assert "completed_at" in cols
        row = conn.execute(
            text(
                "SELECT status, started_at, completed_at FROM machine_runs WHERE id=1"
            )
        ).fetchone()
        assert row == ("HELD", None, None)
        assert conn.execute(text("PRAGMA foreign_key_check")).fetchall() == []
