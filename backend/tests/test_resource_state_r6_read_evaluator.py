"""Resource State R6 — read evaluator unit + isolated DB proofs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.schema_ownership import RESOURCE_STATE_TABLES
from core.sqlite_pragma import register_sqlite_foreign_keys
from services.resource_state_read_evaluator import (
    CAPACITY_BLOCKING_STATUSES,
    CAPACITY_KNOWN_STATUSES,
    RESERVATION_BLOCKING_STATUSES,
    RESERVATION_KNOWN_STATUSES,
    SCHEDULE_BLOCKING_STATUSES,
    SCHEDULE_KNOWN_STATUSES,
    aggregate_domain_states,
    evaluate_domain_from_rows,
)
from services.resource_state_read_repository import (
    FORBIDDEN_WRITE_METHOD_NAMES,
    repository_public_method_names,
)
from services.resource_state_read_service import (
    ResourceStatePlanNotFoundError,
    ResourceStateTaskNotFoundError,
    evaluate_task_resource_state,
)
from schemas.resource_state_read import DomainResourceStateResult

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LED_TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters"


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


def _cfg(*, domain: str, cfg_id: int = 1, version: int = 1):
    return SimpleNamespace(id=cfg_id, status="ACTIVE", version=version, domain=domain)


def test_repository_has_no_write_methods():
    names = {n.lower() for n in repository_public_method_names()}
    for forbidden in FORBIDDEN_WRITE_METHOD_NAMES:
        assert not any(forbidden in n for n in names), names


def test_absence_without_config_is_not_configured_not_clear():
    result = evaluate_domain_from_rows(
        domain="SCHEDULING",
        configuration=None,
        rows=[],
        blocking_statuses=SCHEDULE_BLOCKING_STATUSES,
        known_statuses=SCHEDULE_KNOWN_STATUSES,
        status_getter=lambda r: r.status,
        id_getter=lambda r: r.id,
    )
    assert result.state == "NOT_CONFIGURED"
    assert result.configured is False
    assert result.reason_code == "no_active_configuration"


def test_configured_no_rows_is_clear():
    result = evaluate_domain_from_rows(
        domain="SCHEDULING",
        configuration=_cfg(domain="SCHEDULING"),
        rows=[],
        blocking_statuses=SCHEDULE_BLOCKING_STATUSES,
        known_statuses=SCHEDULE_KNOWN_STATUSES,
        status_getter=lambda r: r.status,
        id_getter=lambda r: r.id,
    )
    assert result.state == "CLEAR"
    assert result.configured is True


def test_draft_schedule_is_not_blocking():
    rows = [SimpleNamespace(id=10, status="DRAFT")]
    result = evaluate_domain_from_rows(
        domain="SCHEDULING",
        configuration=_cfg(domain="SCHEDULING"),
        rows=rows,
        blocking_statuses=SCHEDULE_BLOCKING_STATUSES,
        known_statuses=SCHEDULE_KNOWN_STATUSES,
        status_getter=lambda r: r.status,
        id_getter=lambda r: r.id,
    )
    assert result.state == "CLEAR"


@pytest.mark.parametrize(
    "domain,status,blocking,known",
    [
        ("SCHEDULING", "PLANNED", SCHEDULE_BLOCKING_STATUSES, SCHEDULE_KNOWN_STATUSES),
        ("SCHEDULING", "CONFIRMED", SCHEDULE_BLOCKING_STATUSES, SCHEDULE_KNOWN_STATUSES),
        (
            "MACHINE_RESERVATION",
            "HELD",
            RESERVATION_BLOCKING_STATUSES,
            RESERVATION_KNOWN_STATUSES,
        ),
        (
            "MACHINE_RESERVATION",
            "RESERVED",
            RESERVATION_BLOCKING_STATUSES,
            RESERVATION_KNOWN_STATUSES,
        ),
        (
            "CAPACITY_ALLOCATION",
            "HELD",
            CAPACITY_BLOCKING_STATUSES,
            CAPACITY_KNOWN_STATUSES,
        ),
        (
            "CAPACITY_ALLOCATION",
            "ALLOCATED",
            CAPACITY_BLOCKING_STATUSES,
            CAPACITY_KNOWN_STATUSES,
        ),
    ],
)
def test_blocking_statuses_are_active(domain, status, blocking, known):
    result = evaluate_domain_from_rows(
        domain=domain,
        configuration=_cfg(domain=domain),
        rows=[SimpleNamespace(id=1, status=status)],
        blocking_statuses=blocking,
        known_statuses=known,
        status_getter=lambda r: r.status,
        id_getter=lambda r: r.id,
    )
    assert result.state == "ACTIVE"
    assert result.source_record_ids == [1]


def test_inconsistent_status_is_unknown():
    result = evaluate_domain_from_rows(
        domain="SCHEDULING",
        configuration=_cfg(domain="SCHEDULING"),
        rows=[SimpleNamespace(id=1, status="BOGUS")],
        blocking_statuses=SCHEDULE_BLOCKING_STATUSES,
        known_statuses=SCHEDULE_KNOWN_STATUSES,
        status_getter=lambda r: r.status,
        id_getter=lambda r: r.id,
    )
    assert result.state == "UNKNOWN"
    assert result.reason_code == "inconsistent_source_status"


def test_force_unknown_query_failure():
    result = evaluate_domain_from_rows(
        domain="SCHEDULING",
        configuration=_cfg(domain="SCHEDULING"),
        rows=[],
        blocking_statuses=SCHEDULE_BLOCKING_STATUSES,
        known_statuses=SCHEDULE_KNOWN_STATUSES,
        status_getter=lambda r: r.status,
        id_getter=lambda r: r.id,
        force_unknown=True,
        unknown_reason="query_failure",
    )
    assert result.state == "UNKNOWN"
    assert result.reason_code == "query_failure"


def _dom(state: str, domain: str = "SCHEDULING") -> DomainResourceStateResult:
    return DomainResourceStateResult(
        domain=domain,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
        configured=state != "NOT_CONFIGURED",
        reason_code="t",
        evaluated_at=datetime.now(timezone.utc),
    )


def test_aggregate_precedence_owner_r6():
    assert aggregate_domain_states(
        [_dom("CLEAR"), _dom("CLEAR"), _dom("CLEAR")]
    )[0] == "CLEAR"
    assert aggregate_domain_states(
        [_dom("CLEAR"), _dom("ACTIVE"), _dom("CLEAR")]
    )[0] == "BLOCKED_ACTIVE"
    assert aggregate_domain_states(
        [_dom("CLEAR"), _dom("NOT_CONFIGURED"), _dom("CLEAR")]
    )[0] == "BLOCKED_NOT_CONFIGURED"
    assert aggregate_domain_states(
        [_dom("ACTIVE"), _dom("UNKNOWN"), _dom("CLEAR")]
    )[0] == "BLOCKED_UNKNOWN"
    # UNKNOWN wins over NOT_CONFIGURED and ACTIVE per Owner R6 order
    assert aggregate_domain_states(
        [_dom("NOT_CONFIGURED"), _dom("UNKNOWN"), _dom("ACTIVE")]
    )[0] == "BLOCKED_UNKNOWN"


@pytest_asyncio.fixture
async def rs_session(tmp_path: Path):
    db = tmp_path / "r6.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(sync)
    tasks = {
        "source": "order_snapshot_v2",
        "operational_tasks": [
            {"task_id": LED_TASK, "assigned_employee_id": 7},
            {"task_id": "other-task", "assigned_employee_id": None},
        ],
    }
    with sync.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO employees "
                "(id, name, status, employee_type, salary_currency, salary_period) "
                "VALUES (7, 'Andrei', 'active', 'internal', 'RON', 'monthly')"
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
        conn.execute(
            text(
                "INSERT INTO execution_plan "
                "(id, order_id, order_code, snapshot_version, tasks_json, "
                "total_estimated_time_minutes, created_at, updated_at) "
                "VALUES (23, 880750, '880750', 1, :tj, 0.0, "
                "'2026-08-04 16:00:00', '2026-08-04 16:00:00')"
            ),
            {"tj": json.dumps(tasks)},
        )
    sync.dispose()

    engine = create_async_engine(url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_isolated_empty_config_blocked_not_configured(rs_session: AsyncSession):
    result = await evaluate_task_resource_state(
        rs_session, plan_id=23, task_key=LED_TASK
    )
    assert result.scheduling.state == "NOT_CONFIGURED"
    assert result.machine_reservation.state == "NOT_CONFIGURED"
    assert result.capacity_allocation.state == "NOT_CONFIGURED"
    assert result.aggregate == "BLOCKED_NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_isolated_configured_no_records_clear(rs_session: AsyncSession):
    now = datetime.now(timezone.utc)
    for domain in ("SCHEDULING", "MACHINE_RESERVATION", "CAPACITY_ALLOCATION"):
        await rs_session.execute(
            text(
                "INSERT INTO resource_domain_configurations "
                "(domain, application_scope_key, status, version, configured_at, "
                "configured_by, created_at, updated_at) "
                "VALUES (:d, 'application', 'ACTIVE', 1, :now, 'test', :now, :now)"
            ),
            {"d": domain, "now": now.isoformat()},
        )
    await rs_session.commit()
    result = await evaluate_task_resource_state(
        rs_session, plan_id=23, task_key=LED_TASK
    )
    assert result.scheduling.state == "CLEAR"
    assert result.machine_reservation.state == "CLEAR"
    assert result.capacity_allocation.state == "CLEAR"
    assert result.aggregate == "CLEAR"


@pytest.mark.asyncio
async def test_isolated_blocking_schedule_active(rs_session: AsyncSession):
    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=1)
    for domain in ("SCHEDULING", "MACHINE_RESERVATION", "CAPACITY_ALLOCATION"):
        await rs_session.execute(
            text(
                "INSERT INTO resource_domain_configurations "
                "(domain, application_scope_key, status, version, configured_at, "
                "configured_by, created_at, updated_at) "
                "VALUES (:d, 'application', 'ACTIVE', 1, :now, 'test', :now, :now)"
            ),
            {"d": domain, "now": now.isoformat()},
        )
    await rs_session.execute(
        text(
            "INSERT INTO execution_task_schedules "
            "(execution_plan_id, order_id, task_key, scheduled_start, scheduled_end, "
            "timezone, status, version, idempotency_key, created_at, updated_at) "
            "VALUES (23, 880750, :tk, :start, :end, 'UTC', 'PLANNED', 1, :ik, :now, :now)"
        ),
        {
            "tk": LED_TASK,
            "start": now.isoformat(),
            "end": end.isoformat(),
            "ik": str(uuid4()),
            "now": now.isoformat(),
        },
    )
    await rs_session.commit()
    result = await evaluate_task_resource_state(
        rs_session, plan_id=23, task_key=LED_TASK
    )
    assert result.scheduling.state == "ACTIVE"
    assert result.machine_reservation.state == "CLEAR"
    assert result.capacity_allocation.state == "CLEAR"
    assert result.aggregate == "BLOCKED_ACTIVE"


@pytest.mark.asyncio
async def test_task_identity_errors(rs_session: AsyncSession):
    with pytest.raises(ResourceStatePlanNotFoundError):
        await evaluate_task_resource_state(
            rs_session, plan_id=99999, task_key=LED_TASK
        )
    with pytest.raises(ResourceStateTaskNotFoundError):
        await evaluate_task_resource_state(
            rs_session, plan_id=23, task_key="missing-task-key"
        )


@pytest.mark.asyncio
async def test_rs_tables_still_owned_eight():
    assert len(RESOURCE_STATE_TABLES) == 8
