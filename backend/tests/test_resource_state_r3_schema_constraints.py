"""Resource State R3 — DB-enforceable constraint matrix on isolated SQLite."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from core.schema_ownership import RESOURCE_STATE_TABLES
from core.sqlite_pragma import register_sqlite_foreign_keys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
S64 = "s64_resource_state_persistence"


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


@pytest.fixture()
def rs_engine(tmp_path: Path):
    db = tmp_path / "constraints.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    engine = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(engine)
    with engine.connect() as conn:
        assert int(conn.execute(text("PRAGMA foreign_keys")).scalar_one()) == 1
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
                "VALUES (23, 880750, '880750', 1, '{}', 0.0, "
                "'2026-08-04 16:00:00', '2026-08-04 16:00:00')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, "
                "'2026-08-04 16:00:00', '2026-08-04 16:00:00')"
            )
        )
    yield engine
    engine.dispose()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def test_zero_initial_resource_state_rows(rs_engine):
    with rs_engine.connect() as conn:
        for name in sorted(RESOURCE_STATE_TABLES):
            n = conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
            assert n == 0, name


def test_config_duplicate_domain_scope_rejected(rs_engine):
    sql = text(
        "INSERT INTO resource_domain_configurations "
        "(domain, application_scope_key, status, version, configured_at, "
        "created_at, updated_at) "
        "VALUES ('SCHEDULING', 'application', 'ACTIVE', 1, :ts, :ts, :ts)"
    )
    with rs_engine.begin() as conn:
        conn.execute(sql, {"ts": _now()})
        with pytest.raises(IntegrityError):
            conn.execute(sql, {"ts": _now()})


def test_config_invalid_domain_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO resource_domain_configurations "
                    "(domain, application_scope_key, status, version, configured_at, "
                    "created_at, updated_at) "
                    "VALUES ('NOT_A_DOMAIN', 'application', 'ACTIVE', 1, :ts, :ts, :ts)"
                ),
                {"ts": _now()},
            )


def test_config_version_zero_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO resource_domain_configurations "
                    "(domain, application_scope_key, status, version, configured_at, "
                    "created_at, updated_at) "
                    "VALUES ('SCHEDULING', 'application', 'ACTIVE', 0, :ts, :ts, :ts)"
                ),
                {"ts": _now()},
            )


def test_config_active_without_configured_at_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO resource_domain_configurations "
                    "(domain, application_scope_key, status, version, "
                    "created_at, updated_at) "
                    "VALUES ('SCHEDULING', 'application', 'ACTIVE', 1, :ts, :ts)"
                ),
                {"ts": _now()},
            )


def test_orphan_config_transition_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO resource_domain_configuration_transitions "
                    "(transition_id, configuration_id, domain, operation, "
                    "new_status, new_version, idempotency_key, created_at) "
                    "VALUES (:tid, 99999, 'SCHEDULING', 'CONFIGURE_DOMAIN', "
                    "'ACTIVE', 1, :ikey, :ts)"
                ),
                {"tid": str(uuid4()), "ikey": str(uuid4()), "ts": _now()},
            )


def test_schedule_invalid_plan_fk_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO execution_task_schedules "
                    "(execution_plan_id, order_id, task_key, scheduled_start, "
                    "scheduled_end, timezone, status, version, created_at, "
                    "updated_at, idempotency_key) "
                    "VALUES (99999, 1, 'task_a', :s, :e, 'UTC', 'PLANNED', 1, "
                    ":ts, :ts, :ikey)"
                ),
                {
                    "s": "2026-08-05 10:00:00",
                    "e": "2026-08-05 11:00:00",
                    "ts": _now(),
                    "ikey": str(uuid4()),
                },
            )


def test_schedule_blank_task_key_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO execution_task_schedules "
                    "(execution_plan_id, order_id, task_key, scheduled_start, "
                    "scheduled_end, timezone, status, version, created_at, "
                    "updated_at, idempotency_key) "
                    "VALUES (23, 880750, '   ', :s, :e, 'UTC', 'DRAFT', 1, "
                    ":ts, :ts, :ikey)"
                ),
                {
                    "s": "2026-08-05 10:00:00",
                    "e": "2026-08-05 11:00:00",
                    "ts": _now(),
                    "ikey": str(uuid4()),
                },
            )


def test_schedule_end_before_start_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO execution_task_schedules "
                    "(execution_plan_id, order_id, task_key, scheduled_start, "
                    "scheduled_end, timezone, status, version, created_at, "
                    "updated_at, idempotency_key) "
                    "VALUES (23, 880750, 'task_a', :s, :e, 'UTC', 'DRAFT', 1, "
                    ":ts, :ts, :ikey)"
                ),
                {
                    "s": "2026-08-05 11:00:00",
                    "e": "2026-08-05 10:00:00",
                    "ts": _now(),
                    "ikey": str(uuid4()),
                },
            )


def test_schedule_duplicate_idempotency_rejected(rs_engine):
    ikey = str(uuid4())
    sql = text(
        "INSERT INTO execution_task_schedules "
        "(execution_plan_id, order_id, task_key, scheduled_start, "
        "scheduled_end, timezone, status, version, created_at, "
        "updated_at, idempotency_key) "
        "VALUES (23, 880750, :task, :s, :e, 'UTC', 'DRAFT', 1, "
        ":ts, :ts, :ikey)"
    )
    with rs_engine.begin() as conn:
        conn.execute(
            sql,
            {
                "task": "task_a",
                "s": "2026-08-05 10:00:00",
                "e": "2026-08-05 11:00:00",
                "ts": _now(),
                "ikey": ikey,
            },
        )
        with pytest.raises(IntegrityError):
            conn.execute(
                sql,
                {
                    "task": "task_b",
                    "s": "2026-08-05 12:00:00",
                    "e": "2026-08-05 13:00:00",
                    "ts": _now(),
                    "ikey": ikey,
                },
            )


def test_schedule_open_partial_unique_includes_draft(rs_engine):
    """Authoring uniqueness: two DRAFT rows for same plan+task rejected."""
    sql = text(
        "INSERT INTO execution_task_schedules "
        "(execution_plan_id, order_id, task_key, scheduled_start, "
        "scheduled_end, timezone, status, version, created_at, "
        "updated_at, idempotency_key) "
        "VALUES (23, 880750, 'task_open', :s, :e, 'UTC', 'DRAFT', 1, "
        ":ts, :ts, :ikey)"
    )
    with rs_engine.begin() as conn:
        conn.execute(
            sql,
            {
                "s": "2026-08-05 10:00:00",
                "e": "2026-08-05 11:00:00",
                "ts": _now(),
                "ikey": str(uuid4()),
            },
        )
        with pytest.raises(IntegrityError):
            conn.execute(
                sql,
                {
                    "s": "2026-08-05 12:00:00",
                    "e": "2026-08-05 13:00:00",
                    "ts": _now(),
                    "ikey": str(uuid4()),
                },
            )


def test_schedule_self_supersession_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO execution_task_schedules "
                    "(id, execution_plan_id, order_id, task_key, scheduled_start, "
                    "scheduled_end, timezone, status, version, created_at, "
                    "updated_at, superseded_by_id, idempotency_key) "
                    "VALUES (101, 23, 880750, 'task_ss2', :s, :e, 'UTC', "
                    "'SUPERSEDED', 1, :ts, :ts, 101, :ikey)"
                ),
                {
                    "s": "2026-08-05 10:00:00",
                    "e": "2026-08-05 11:00:00",
                    "ts": _now(),
                    "ikey": str(uuid4()),
                },
            )


def test_reservation_invalid_machine_fk_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO execution_task_machine_reservations "
                    "(execution_plan_id, order_id, task_key, machine_id, "
                    "reservation_start, reservation_end, timezone, status, "
                    "version, created_at, updated_at, idempotency_key) "
                    "VALUES (23, 880750, 'task_m', 99999, :s, :e, 'UTC', "
                    "'HELD', 1, :ts, :ts, :ikey)"
                ),
                {
                    "s": "2026-08-05 10:00:00",
                    "e": "2026-08-05 11:00:00",
                    "ts": _now(),
                    "ikey": str(uuid4()),
                },
            )


def test_capacity_invalid_scope_xor_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO execution_task_capacity_allocations "
                    "(execution_plan_id, order_id, task_key, resource_scope_type, "
                    "resource_scope_id, workcenter_code, machine_id, bucket_start, "
                    "bucket_end, timezone, quantity, unit, status, version, "
                    "created_at, updated_at, idempotency_key) "
                    "VALUES (23, 880750, 'task_c', 'WORKCENTER', 'WC-A', 'WC-A', "
                    "1, :s, :e, 'UTC', 30, 'minutes', 'HELD', 1, :ts, :ts, :ikey)"
                ),
                {
                    "s": "2026-08-05 10:00:00",
                    "e": "2026-08-05 11:00:00",
                    "ts": _now(),
                    "ikey": str(uuid4()),
                },
            )


def test_capacity_quantity_zero_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO execution_task_capacity_allocations "
                    "(execution_plan_id, order_id, task_key, resource_scope_type, "
                    "resource_scope_id, workcenter_code, machine_id, bucket_start, "
                    "bucket_end, timezone, quantity, unit, status, version, "
                    "created_at, updated_at, idempotency_key) "
                    "VALUES (23, 880750, 'task_c', 'WORKCENTER', 'WC-A', 'WC-A', "
                    "NULL, :s, :e, 'UTC', 0, 'minutes', 'HELD', 1, :ts, :ts, :ikey)"
                ),
                {
                    "s": "2026-08-05 10:00:00",
                    "e": "2026-08-05 11:00:00",
                    "ts": _now(),
                    "ikey": str(uuid4()),
                },
            )


def test_capacity_invalid_unit_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO execution_task_capacity_allocations "
                    "(execution_plan_id, order_id, task_key, resource_scope_type, "
                    "resource_scope_id, workcenter_code, machine_id, bucket_start, "
                    "bucket_end, timezone, quantity, unit, status, version, "
                    "created_at, updated_at, idempotency_key) "
                    "VALUES (23, 880750, 'task_c', 'WORKCENTER', 'WC-A', 'WC-A', "
                    "NULL, :s, :e, 'UTC', 15, 'hours', 'HELD', 1, :ts, :ts, :ikey)"
                ),
                {
                    "s": "2026-08-05 10:00:00",
                    "e": "2026-08-05 11:00:00",
                    "ts": _now(),
                    "ikey": str(uuid4()),
                },
            )


def test_orphan_schedule_transition_rejected(rs_engine):
    with rs_engine.begin() as conn:
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO execution_task_schedule_transitions "
                    "(transition_id, schedule_id, execution_plan_id, task_key, "
                    "operation, new_status, new_version, idempotency_key, created_at) "
                    "VALUES (:tid, 99999, 23, 'task_a', 'CREATE_SCHEDULE', "
                    "'DRAFT', 1, :ikey, :ts)"
                ),
                {"tid": str(uuid4()), "ikey": str(uuid4()), "ts": _now()},
            )
