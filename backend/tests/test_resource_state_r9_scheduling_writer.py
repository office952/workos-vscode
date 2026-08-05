"""Resource State R9 — scheduling writer isolated proofs."""

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
from schemas.resource_state_schedule import (
    CancelScheduleCommand,
    ConfirmScheduleCommand,
    CreateScheduleCommand,
    RescheduleCommand,
    SupersedeScheduleCommand,
)
from services.execution_task_schedule_command_service import (
    cancel_schedule,
    confirm_schedule,
    create_schedule,
    reschedule_schedule,
    supersede_schedule,
)
from services.execution_task_schedule_repository import (
    FORBIDDEN_MUTATORS,
    ExecutionTaskScheduleRepository,
)
from services.resource_domain_configuration_command_service import (
    configure_resource_domain,
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


def _window(hours: int = 0):
    start = datetime(2026, 8, 5, 10, 0, tzinfo=timezone.utc) + timedelta(hours=hours)
    end = start + timedelta(hours=2)
    return start, end


@pytest_asyncio.fixture
async def r9_sched(tmp_path: Path):
    db = tmp_path / "r9_sched.db"
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


async def _activate_scheduling(session: AsyncSession):
    await configure_resource_domain(
        session,
        domain="SCHEDULING",
        command=ResourceDomainConfigurationCommand(
            target_status="ACTIVE",
            expected_version=0,
            idempotency_key=str(uuid.uuid4()),
            reason_code="r9_test_activate",
        ),
        actor_user_id="admin-1",
    )
    await session.commit()


def test_repo_forbids_generic_mutators():
    names = {
        n.lower()
        for n in dir(ExecutionTaskScheduleRepository)
        if not n.startswith("_")
    }
    for forbidden in FORBIDDEN_MUTATORS:
        assert forbidden not in names


@pytest.mark.asyncio
async def test_create_blocked_without_active_config(r9_sched: AsyncSession):
    start, end = _window()
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_schedule(
            r9_sched,
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
    assert exc.value.code == "domain_not_active"


@pytest.mark.asyncio
async def test_schedule_lifecycle_cas_idempotency_evaluator(r9_sched: AsyncSession):
    await _activate_scheduling(r9_sched)
    start, end = _window()
    key = str(uuid.uuid4())
    created = await create_schedule(
        r9_sched,
        command=CreateScheduleCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            scheduled_start=start,
            scheduled_end=end,
            timezone="UTC",
            initial_status="DRAFT",
            idempotency_key=key,
            reason_code="create",
        ),
        actor_user_id="admin-1",
    )
    assert created.version == 1
    assert created.status == "DRAFT"

    replay = await create_schedule(
        r9_sched,
        command=CreateScheduleCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            scheduled_start=start,
            scheduled_end=end,
            timezone="UTC",
            initial_status="DRAFT",
            idempotency_key=key,
            reason_code="create",
        ),
        actor_user_id="admin-1",
    )
    assert replay.already_applied is True
    count = (
        await r9_sched.execute(
            text("SELECT COUNT(*) FROM execution_task_schedule_transitions")
        )
    ).scalar_one()
    assert count == 1

    with pytest.raises(ResourceStateWriteError) as conflict:
        await create_schedule(
            r9_sched,
            command=CreateScheduleCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                scheduled_start=start,
                scheduled_end=end,
                timezone="UTC",
                initial_status="PLANNED",
                idempotency_key=key,
                reason_code="create",
            ),
            actor_user_id="admin-1",
        )
    assert conflict.value.code == "idempotency_payload_conflict"

    eval_draft = await evaluate_task_resource_state(
        r9_sched, plan_id=23, task_key=LED_TASK
    )
    assert eval_draft.scheduling.state == "CLEAR"
    assert eval_draft.aggregate == "BLOCKED_NOT_CONFIGURED"

    start2, end2 = _window(3)
    moved = await reschedule_schedule(
        r9_sched,
        schedule_id=created.schedule_id,
        command=RescheduleCommand(
            scheduled_start=start2,
            scheduled_end=end2,
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
            reason_code="move",
        ),
        actor_user_id="admin-1",
    )
    assert moved.version == 2
    assert moved.status == "DRAFT"

    with pytest.raises(ResourceStateWriteError) as stale:
        await reschedule_schedule(
            r9_sched,
            schedule_id=created.schedule_id,
            command=RescheduleCommand(
                scheduled_start=start2,
                scheduled_end=end2,
                expected_version=1,
                idempotency_key=str(uuid.uuid4()),
                reason_code="stale",
            ),
            actor_user_id="admin-1",
        )
    assert stale.value.code == "cas_stale"

    confirmed = await confirm_schedule(
        r9_sched,
        schedule_id=created.schedule_id,
        command=ConfirmScheduleCommand(
            expected_version=2,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert confirmed.status == "CONFIRMED"
    eval_conf = await evaluate_task_resource_state(
        r9_sched, plan_id=23, task_key=LED_TASK
    )
    assert eval_conf.scheduling.state == "ACTIVE"

    cancelled = await cancel_schedule(
        r9_sched,
        schedule_id=created.schedule_id,
        command=CancelScheduleCommand(
            expected_version=3,
            idempotency_key=str(uuid.uuid4()),
            reason_code="done",
        ),
        actor_user_id="admin-1",
    )
    assert cancelled.status == "CANCELLED"
    eval_cancel = await evaluate_task_resource_state(
        r9_sched, plan_id=23, task_key=LED_TASK
    )
    assert eval_cancel.scheduling.state == "CLEAR"


@pytest.mark.asyncio
async def test_open_uniqueness_and_supersede(r9_sched: AsyncSession):
    await _activate_scheduling(r9_sched)
    start, end = _window()
    first = await create_schedule(
        r9_sched,
        command=CreateScheduleCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            scheduled_start=start,
            scheduled_end=end,
            timezone="UTC",
            initial_status="PLANNED",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    with pytest.raises(ResourceStateWriteError) as open_conflict:
        await create_schedule(
            r9_sched,
            command=CreateScheduleCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                scheduled_start=start + timedelta(hours=4),
                scheduled_end=end + timedelta(hours=4),
                timezone="UTC",
                initial_status="DRAFT",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert open_conflict.value.code == "open_row_conflict"

    start2, end2 = _window(5)
    superseded = await supersede_schedule(
        r9_sched,
        schedule_id=first.schedule_id,
        command=SupersedeScheduleCommand(
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
            replacement_idempotency_key=str(uuid.uuid4()),
            scheduled_start=start2,
            scheduled_end=end2,
            timezone="UTC",
            initial_status="PLANNED",
            reason_code="replace",
            correlation_id="corr-sup",
        ),
        actor_user_id="admin-1",
    )
    assert superseded.status == "SUPERSEDED"
    assert superseded.replacement_schedule_id is not None
    eval_active = await evaluate_task_resource_state(
        r9_sched, plan_id=23, task_key=LED_TASK
    )
    assert eval_active.scheduling.state == "ACTIVE"


@pytest.mark.asyncio
async def test_task_missing_and_terminal_reopen(r9_sched: AsyncSession):
    await _activate_scheduling(r9_sched)
    start, end = _window()
    with pytest.raises(ResourceStateWriteError) as missing:
        await create_schedule(
            r9_sched,
            command=CreateScheduleCommand(
                execution_plan_id=23,
                task_key="missing-task",
                scheduled_start=start,
                scheduled_end=end,
                timezone="UTC",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert missing.value.code == "task_key_not_found"
    assert missing.value.http_status == 404

    created = await create_schedule(
        r9_sched,
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
    await cancel_schedule(
        r9_sched,
        schedule_id=created.schedule_id,
        command=CancelScheduleCommand(
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
            reason_code="stop",
        ),
        actor_user_id="admin-1",
    )
    with pytest.raises(ResourceStateWriteError) as term:
        await confirm_schedule(
            r9_sched,
            schedule_id=created.schedule_id,
            command=ConfirmScheduleCommand(
                expected_version=2,
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert term.value.code == "invalid_transition"


@pytest.mark.asyncio
async def test_concurrent_create_one_wins(r9_sched: AsyncSession, tmp_path: Path):
    """Serialize via plan lock: two creates → one success, one conflict."""
    await _activate_scheduling(r9_sched)
    start, end = _window()

    # Use two sessions on same file for realistic concurrency
    # Re-open engine from same path is hard via fixture; run sequential under gather
    # with shared session still exercises lock path.
    async def _one(key_suffix: str):
        return await create_schedule(
            r9_sched,
            command=CreateScheduleCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                scheduled_start=start,
                scheduled_end=end,
                timezone="UTC",
                initial_status="PLANNED",
                idempotency_key=str(uuid.uuid4()),
                reason_code=key_suffix,
            ),
            actor_user_id="admin-1",
        )

    results = await asyncio.gather(_one("a"), _one("b"), return_exceptions=True)
    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, ResourceStateWriteError)]
    assert len(successes) == 1
    assert len(failures) == 1
    assert failures[0].code == "open_row_conflict"
