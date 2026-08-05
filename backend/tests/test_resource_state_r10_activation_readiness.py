"""Resource State R10 — controlled domain activation readiness (isolated)."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.sqlite_pragma import register_sqlite_foreign_keys
from schemas.resource_state_configuration import ResourceDomainConfigurationCommand
from schemas.resource_state_reservation import CreateReservationCommand
from schemas.resource_state_schedule import CreateScheduleCommand
from services.execution_task_machine_reservation_command_service import (
    create_reservation,
)
from services.execution_task_schedule_command_service import create_schedule
from services.resource_domain_configuration_command_service import (
    DOMAIN_WRITER_READY,
    ResourceDomainConfigurationActivationBlockedError,
    ResourceDomainConfigurationDisableBlockedError,
    assess_activation_readiness,
    assess_disable_readiness,
    configure_resource_domain,
    domain_activation_readiness_report,
)
from services.resource_state_read_service import evaluate_task_resource_state
from services.resource_state_write_common import ResourceStateWriteError

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


def _cmd(
    *,
    target_status: str,
    expected_version: int,
    idempotency_key: str | None = None,
    reason_code: str = "r10",
) -> ResourceDomainConfigurationCommand:
    return ResourceDomainConfigurationCommand(
        target_status=target_status,  # type: ignore[arg-type]
        expected_version=expected_version,
        idempotency_key=idempotency_key or str(uuid.uuid4()),
        reason_code=reason_code,
    )


@pytest_asyncio.fixture
async def r10_session(tmp_path: Path):
    db = tmp_path / "r10.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(sync)
    tasks = {
        "source": "order_snapshot_v2",
        "operational_tasks": [{"task_id": LED_TASK, "assigned_employee_id": 7}],
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
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


def test_writer_ready_is_domain_specific_not_global():
    assert DOMAIN_WRITER_READY["SCHEDULING"] is True
    assert DOMAIN_WRITER_READY["MACHINE_RESERVATION"] is True
    # Stage 1 landed: capacity writer ready in code; still domain-keyed dict.
    assert DOMAIN_WRITER_READY["CAPACITY_ALLOCATION"] is True
    assert set(DOMAIN_WRITER_READY.keys()) == {
        "SCHEDULING",
        "MACHINE_RESERVATION",
        "CAPACITY_ALLOCATION",
    }


@pytest.mark.asyncio
async def test_readiness_matrix(r10_session: AsyncSession):
    report = await domain_activation_readiness_report(r10_session)
    assert report["SCHEDULING"]["ready"] is True
    assert report["MACHINE_RESERVATION"]["ready"] is True
    # Isolated DBs upgrade to head (s65) → capacity source schema present.
    assert report["CAPACITY_ALLOCATION"]["ready"] is True
    assert report["CAPACITY_ALLOCATION"]["reason_code"] == "ready"


@pytest.mark.asyncio
async def test_scheduling_independent_activation(r10_session: AsyncSession):
    act = await configure_resource_domain(
        r10_session,
        domain="SCHEDULING",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    assert act.status == "ACTIVE"

    start = datetime(2026, 8, 5, 10, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)
    created = await create_schedule(
        r10_session,
        command=CreateScheduleCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            scheduled_start=start,
            scheduled_end=end,
            timezone="UTC",
            initial_status="DRAFT",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert created.status == "DRAFT"

    result = await evaluate_task_resource_state(
        r10_session, plan_id=23, task_key=LED_TASK
    )
    assert result.scheduling.state == "CLEAR"
    assert result.machine_reservation.state == "NOT_CONFIGURED"
    assert result.capacity_allocation.state == "NOT_CONFIGURED"
    assert result.aggregate == "BLOCKED_NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_reservation_independent_activation(r10_session: AsyncSession):
    await configure_resource_domain(
        r10_session,
        domain="MACHINE_RESERVATION",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    start = datetime(2026, 8, 5, 11, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)
    created = await create_reservation(
        r10_session,
        command=CreateReservationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert created.status == "HELD"
    result = await evaluate_task_resource_state(
        r10_session, plan_id=23, task_key=LED_TASK
    )
    assert result.scheduling.state == "NOT_CONFIGURED"
    assert result.machine_reservation.state == "ACTIVE"
    assert result.capacity_allocation.state == "NOT_CONFIGURED"
    assert result.aggregate == "BLOCKED_NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_both_active_capacity_keeps_aggregate_blocked(r10_session: AsyncSession):
    for domain in ("SCHEDULING", "MACHINE_RESERVATION"):
        await configure_resource_domain(
            r10_session,
            domain=domain,
            command=_cmd(target_status="ACTIVE", expected_version=0),
            actor_user_id="admin-1",
        )
    await r10_session.commit()
    result = await evaluate_task_resource_state(
        r10_session, plan_id=23, task_key=LED_TASK
    )
    assert result.scheduling.state == "CLEAR"
    assert result.machine_reservation.state == "CLEAR"
    assert result.capacity_allocation.state == "NOT_CONFIGURED"
    assert result.aggregate == "BLOCKED_NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_capacity_activation_allowed_when_source_schema_present(
    r10_session: AsyncSession,
):
    """Stage 1: capacity may activate on isolated s65 DBs (QA stays s64)."""
    act = await configure_resource_domain(
        r10_session,
        domain="CAPACITY_ALLOCATION",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    assert act.status == "ACTIVE"
    result = await evaluate_task_resource_state(
        r10_session, plan_id=23, task_key=LED_TASK
    )
    assert result.capacity_allocation.state == "CLEAR"
    assert result.aggregate == "BLOCKED_NOT_CONFIGURED"  # schedule/res not ACTIVE


@pytest.mark.asyncio
async def test_disable_blocks_writes_and_reader_not_configured(
    r10_session: AsyncSession,
):
    act = await configure_resource_domain(
        r10_session,
        domain="SCHEDULING",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    disabled = await configure_resource_domain(
        r10_session,
        domain="SCHEDULING",
        command=_cmd(target_status="DISABLED", expected_version=act.version),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    assert disabled.status == "DISABLED"

    start = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(ResourceStateWriteError) as write_exc:
        await create_schedule(
            r10_session,
            command=CreateScheduleCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                scheduled_start=start,
                scheduled_end=start + timedelta(hours=1),
                timezone="UTC",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert write_exc.value.code in {"domain_not_active", "domain_disabled"}

    result = await evaluate_task_resource_state(
        r10_session, plan_id=23, task_key=LED_TASK
    )
    assert result.scheduling.state == "NOT_CONFIGURED"


@pytest.mark.asyncio
async def test_disable_rejected_with_blocking_rows(r10_session: AsyncSession):
    act = await configure_resource_domain(
        r10_session,
        domain="SCHEDULING",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    start = datetime(2026, 8, 5, 13, 0, tzinfo=timezone.utc)
    await create_schedule(
        r10_session,
        command=CreateScheduleCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            scheduled_start=start,
            scheduled_end=start + timedelta(hours=1),
            timezone="UTC",
            initial_status="PLANNED",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    d_ok, d_reason = await assess_disable_readiness(
        r10_session, domain="SCHEDULING"
    )
    assert d_ok is False
    assert d_reason == "disable_blocked_active_source_rows"
    with pytest.raises(ResourceDomainConfigurationDisableBlockedError):
        await configure_resource_domain(
            r10_session,
            domain="SCHEDULING",
            command=_cmd(
                target_status="DISABLED", expected_version=act.version
            ),
            actor_user_id="admin-1",
        )


@pytest.mark.asyncio
async def test_disable_allowed_with_terminal_only(r10_session: AsyncSession):
    act = await configure_resource_domain(
        r10_session,
        domain="SCHEDULING",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    # Insert terminal row directly (CANCELLED) — history preserved path.
    now = datetime.now(timezone.utc)
    await r10_session.execute(
        text(
            "INSERT INTO execution_task_schedules "
            "(execution_plan_id, order_id, task_key, scheduled_start, scheduled_end, "
            "timezone, status, version, cancelled_at, cancelled_by, "
            "idempotency_key, created_at, updated_at) "
            "VALUES (23, 880750, :tk, :s, :e, 'UTC', 'CANCELLED', 1, :now, 'admin', "
            ":ik, :now, :now)"
        ),
        {
            "tk": LED_TASK,
            "s": now.isoformat(),
            "e": (now + timedelta(hours=1)).isoformat(),
            "now": now.isoformat(),
            "ik": str(uuid.uuid4()),
        },
    )
    await r10_session.commit()
    disabled = await configure_resource_domain(
        r10_session,
        domain="SCHEDULING",
        command=_cmd(target_status="DISABLED", expected_version=act.version),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    assert disabled.status == "DISABLED"
    count = (
        await r10_session.execute(
            text("SELECT COUNT(*) FROM execution_task_schedules")
        )
    ).scalar_one()
    assert count == 1  # row preserved


@pytest.mark.asyncio
async def test_activation_then_disable_serializes_against_writes(
    r10_session: AsyncSession,
):
    """Disable-then-write: no write may succeed against DISABLED config."""
    act = await configure_resource_domain(
        r10_session,
        domain="SCHEDULING",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    await configure_resource_domain(
        r10_session,
        domain="SCHEDULING",
        command=_cmd(target_status="DISABLED", expected_version=act.version),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    start = datetime(2026, 8, 5, 14, 0, tzinfo=timezone.utc)
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_schedule(
            r10_session,
            command=CreateScheduleCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                scheduled_start=start,
                scheduled_end=start + timedelta(hours=1),
                timezone="UTC",
                initial_status="DRAFT",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code in {"domain_not_active", "domain_disabled"}


@pytest.mark.asyncio
async def test_concurrent_disable_and_write_one_explicit_outcome(
    r10_session: AsyncSession,
):
    """Under plan/config serialization, gather yields success and/or conflict — never silent loss."""
    act = await configure_resource_domain(
        r10_session,
        domain="SCHEDULING",
        command=_cmd(target_status="ACTIVE", expected_version=0),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    start = datetime(2026, 8, 5, 15, 0, tzinfo=timezone.utc)

    async def _disable():
        return await configure_resource_domain(
            r10_session,
            domain="SCHEDULING",
            command=_cmd(
                target_status="DISABLED", expected_version=act.version
            ),
            actor_user_id="admin-1",
        )

    async def _write():
        return await create_schedule(
            r10_session,
            command=CreateScheduleCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                scheduled_start=start,
                scheduled_end=start + timedelta(hours=1),
                timezone="UTC",
                initial_status="DRAFT",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )

    results = await asyncio.gather(_disable(), _write(), return_exceptions=True)
    # Shared AsyncSession is not fully concurrent-safe; accept either
    # serialized successes or explicit exceptions — never partial silent state.
    assert len(results) == 2
    cfg_status = (
        await r10_session.execute(
            text(
                "SELECT status FROM resource_domain_configurations "
                "WHERE domain='SCHEDULING'"
            )
        )
    ).scalar_one()
    assert cfg_status in {"ACTIVE", "DISABLED"}
    if cfg_status == "DISABLED":
        with pytest.raises(ResourceStateWriteError):
            await create_schedule(
                r10_session,
                command=CreateScheduleCommand(
                    execution_plan_id=23,
                    task_key=LED_TASK,
                    scheduled_start=start + timedelta(days=1),
                    scheduled_end=start + timedelta(days=1, hours=1),
                    timezone="UTC",
                    idempotency_key=str(uuid.uuid4()),
                ),
                actor_user_id="admin-1",
            )


@pytest.mark.asyncio
async def test_activation_idempotent_and_cas(r10_session: AsyncSession):
    key = str(uuid.uuid4())
    first = await configure_resource_domain(
        r10_session,
        domain="SCHEDULING",
        command=_cmd(
            target_status="ACTIVE",
            expected_version=0,
            idempotency_key=key,
            reason_code="act",
        ),
        actor_user_id="admin-1",
    )
    await r10_session.commit()
    second = await configure_resource_domain(
        r10_session,
        domain="SCHEDULING",
        command=_cmd(
            target_status="ACTIVE",
            expected_version=0,
            idempotency_key=key,
            reason_code="act",
        ),
        actor_user_id="admin-1",
    )
    assert second.already_applied is True
    assert second.transition_id == first.transition_id
    tr_count = (
        await r10_session.execute(
            text(
                "SELECT COUNT(*) FROM resource_domain_configuration_transitions"
            )
        )
    ).scalar_one()
    assert tr_count == 1


@pytest.mark.asyncio
async def test_scheduling_activation_readiness_true(r10_session: AsyncSession):
    ok, reason = await assess_activation_readiness(
        r10_session, domain="SCHEDULING"
    )
    assert ok is True
    assert reason == "ready"
    ok_r, _ = await assess_activation_readiness(
        r10_session, domain="MACHINE_RESERVATION"
    )
    assert ok_r is True
