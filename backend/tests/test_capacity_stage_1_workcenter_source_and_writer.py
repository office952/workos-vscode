"""Capacity Stage 1 — workcenter source + allocation writer (isolated only)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.sqlite_pragma import register_sqlite_foreign_keys
from schemas.resource_state_capacity_allocation import (
    AdjustAllocationCommand,
    CancelAllocationCommand,
    CreateAllocationCommand,
    ReleaseAllocationCommand,
    SupersedeAllocationCommand,
)
from schemas.resource_state_capacity_source import (
    AdjustWorkcenterCapacityCommand,
    CreateWorkcenterCapacityCommand,
    DisableWorkcenterCapacityCommand,
)
from schemas.resource_state_configuration import ResourceDomainConfigurationCommand
from schemas.resource_state_reservation import CreateReservationCommand
from schemas.resource_state_schedule import CreateScheduleCommand
from services.capacity_day_bucket import day_bounds_for_date
from services.execution_task_capacity_allocation_command_service import (
    adjust_allocation,
    cancel_allocation,
    create_allocation,
    release_allocation,
    supersede_allocation,
)
from services.execution_task_capacity_allocation_repository import (
    FORBIDDEN_MUTATORS as ALLOC_FORBIDDEN,
    ExecutionTaskCapacityAllocationRepository,
)
from services.execution_task_machine_reservation_command_service import (
    create_reservation,
)
from services.execution_task_schedule_command_service import create_schedule
from services.resource_domain_configuration_command_service import (
    DOMAIN_WRITER_READY,
    configure_resource_domain,
)
from services.resource_state_read_service import evaluate_task_resource_state
from services.resource_state_write_common import ResourceStateWriteError
from services.workcenter_capacity_source_command_service import (
    adjust_workcenter_capacity,
    create_workcenter_capacity,
    disable_workcenter_capacity,
)
from services.workcenter_capacity_source_repository import (
    FORBIDDEN_MUTATORS as SOURCE_FORBIDDEN,
    WorkcenterCapacitySourceRepository,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
LED_TASK = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters"
WC = "WC_CNC"


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


@pytest_asyncio.fixture
async def c1(tmp_path: Path):
    db = tmp_path / "capacity_stage1.db"
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
        rev = conn.execute(text("select version_num from alembic_version")).scalar()
        assert rev == "s67_machine_run_execution_status"
    sync.dispose()
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _activate_capacity(session: AsyncSession):
    await configure_resource_domain(
        session,
        domain="CAPACITY_ALLOCATION",
        command=ResourceDomainConfigurationCommand(
            target_status="ACTIVE",
            expected_version=0,
            idempotency_key=str(uuid.uuid4()),
            reason_code="c1_test_activate",
        ),
        actor_user_id="admin-1",
    )
    await session.commit()


async def _create_source(
    session: AsyncSession,
    *,
    minutes: int = 480,
    policy: str = "WARN_ONLY",
    day: date | None = None,
):
    d = day or date(2026, 8, 5)
    return await create_workcenter_capacity(
        session,
        command=CreateWorkcenterCapacityCommand(
            workcenter_code=WC,
            bucket_date=d,
            timezone="UTC",
            available_minutes=minutes,
            over_allocation_policy=policy,  # type: ignore[arg-type]
            source_label="OWNER_CONFIGURED",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )


def test_writer_ready_capacity_true():
    assert DOMAIN_WRITER_READY["CAPACITY_ALLOCATION"] is True


def test_repos_forbid_generic_mutators():
    for names, forbidden in (
        (dir(WorkcenterCapacitySourceRepository), SOURCE_FORBIDDEN),
        (dir(ExecutionTaskCapacityAllocationRepository), ALLOC_FORBIDDEN),
    ):
        lower = {n.lower() for n in names if not n.startswith("_")}
        for f in forbidden:
            assert f not in lower


@pytest.mark.asyncio
async def test_source_create_adjust_cas_idempotency(c1: AsyncSession):
    created = await _create_source(c1, minutes=480)
    assert created.status == "ACTIVE"
    assert created.version == 1
    assert created.available_minutes == 480

    key = str(uuid.uuid4())
    cmd = CreateWorkcenterCapacityCommand(
        workcenter_code="WC_LED",
        bucket_date=date(2026, 8, 5),
        timezone="UTC",
        available_minutes=100,
        idempotency_key=key,
    )
    first = await create_workcenter_capacity(c1, command=cmd, actor_user_id="admin-1")
    second = await create_workcenter_capacity(c1, command=cmd, actor_user_id="admin-1")
    assert second.already_applied is True
    assert second.source_id == first.source_id

    with pytest.raises(ResourceStateWriteError) as exc:
        await create_workcenter_capacity(
            c1,
            command=CreateWorkcenterCapacityCommand(
                workcenter_code="WC_LED",
                bucket_date=date(2026, 8, 5),
                timezone="UTC",
                available_minutes=200,
                idempotency_key=key,
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "idempotency_payload_conflict"

    adj = await adjust_workcenter_capacity(
        c1,
        source_id=created.source_id,
        command=AdjustWorkcenterCapacityCommand(
            available_minutes=400,
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
            reason_code="capacity_adjust",
        ),
        actor_user_id="admin-1",
    )
    assert adj.version == 2
    assert adj.available_minutes == 400

    with pytest.raises(ResourceStateWriteError) as cas:
        await adjust_workcenter_capacity(
            c1,
            source_id=created.source_id,
            command=AdjustWorkcenterCapacityCommand(
                available_minutes=300,
                expected_version=1,
                idempotency_key=str(uuid.uuid4()),
                reason_code="stale",
            ),
            actor_user_id="admin-1",
        )
    assert cas.value.code == "cas_stale"


@pytest.mark.asyncio
async def test_source_invalid_minutes_and_ai_rules(c1: AsyncSession):
    with pytest.raises(Exception):
        CreateWorkcenterCapacityCommand(
            workcenter_code=WC,
            bucket_date=date(2026, 8, 5),
            timezone="UTC",
            available_minutes=-1,
            idempotency_key=str(uuid.uuid4()),
        )
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_workcenter_capacity(
            c1,
            command=CreateWorkcenterCapacityCommand(
                workcenter_code=WC,
                bucket_date=date(2026, 8, 5),
                timezone="UTC",
                available_minutes=10,
                source_label="AI_DECISION",
                source_execution_truth=True,
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code in {"ai_not_execution_truth", "ai_explanation_required"}


@pytest.mark.asyncio
async def test_allocation_lifecycle_and_evaluator(c1: AsyncSession):
    await _activate_capacity(c1)
    await _create_source(c1, minutes=480)
    start, end = day_bounds_for_date(date(2026, 8, 5), "UTC")

    with pytest.raises(ResourceStateWriteError) as miss:
        await create_allocation(
            c1,
            command=CreateAllocationCommand(
                execution_plan_id=23,
                task_key="missing-task",
                workcenter_code=WC,
                bucket_start=start,
                bucket_end=end,
                timezone="UTC",
                quantity_minutes=60,
                workload_source="MANUAL_MANAGER_ESTIMATE",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert miss.value.code in {"task_key_not_found", "invalid_task_identity"}

    created = await create_allocation(
        c1,
        command=CreateAllocationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            workcenter_code=WC,
            bucket_start=start,
            bucket_end=end,
            timezone="UTC",
            quantity_minutes=60,
            workload_source="MANUAL_MANAGER_ESTIMATE",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert created.status == "ALLOCATED"
    assert created.over_allocation is not None
    assert created.over_allocation.over_allocated is False

    ev = await evaluate_task_resource_state(c1, plan_id=23, task_key=LED_TASK)
    assert ev.capacity_allocation.state == "ACTIVE"
    # Schedule/reservation still NOT_CONFIGURED → aggregate precedence keeps
    # BLOCKED_NOT_CONFIGURED (R6: NOT_CONFIGURED before ACTIVE).
    assert ev.aggregate == "BLOCKED_NOT_CONFIGURED"

    released = await release_allocation(
        c1,
        allocation_id=created.allocation_id,
        command=ReleaseAllocationCommand(
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
            reason_code="done",
        ),
        actor_user_id="admin-1",
    )
    assert released.status == "RELEASED"
    ev2 = await evaluate_task_resource_state(c1, plan_id=23, task_key=LED_TASK)
    assert ev2.capacity_allocation.state == "CLEAR"


@pytest.mark.asyncio
async def test_warn_only_hard_block_allow_with_reason(c1: AsyncSession):
    await _activate_capacity(c1)
    start, end = day_bounds_for_date(date(2026, 8, 5), "UTC")

    # WARN_ONLY
    await _create_source(c1, minutes=100, policy="WARN_ONLY")
    warn = await create_allocation(
        c1,
        command=CreateAllocationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            workcenter_code=WC,
            bucket_start=start,
            bucket_end=end,
            timezone="UTC",
            quantity_minutes=150,
            workload_source="OWNER_CONFIGURED",
            idempotency_key=str(uuid.uuid4()),
            reason_code="overflow_warn",
        ),
        actor_user_id="admin-1",
    )
    assert warn.over_allocation and warn.over_allocation.over_allocated is True
    assert warn.over_allocation.excess_minutes == 50

    # HARD_BLOCK on another day
    d2 = date(2026, 8, 6)
    s2, e2 = day_bounds_for_date(d2, "UTC")
    src2 = await _create_source(c1, minutes=50, policy="HARD_BLOCK", day=d2)
    assert src2.over_allocation_policy == "HARD_BLOCK"
    with pytest.raises(ResourceStateWriteError) as hb:
        await create_allocation(
            c1,
            command=CreateAllocationCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                workcenter_code=WC,
                bucket_start=s2,
                bucket_end=e2,
                timezone="UTC",
                quantity_minutes=80,
                workload_source="OWNER_CONFIGURED",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert hb.value.code == "over_allocation"
    repo = ExecutionTaskCapacityAllocationRepository(c1)
    # only the WARN_ONLY allocation exists as open
    total = await repo.sum_open_minutes_for_workcenter_bucket(
        workcenter_code=WC, bucket_start=s2, bucket_end=e2
    )
    assert total == 0

    # ALLOW_WITH_REASON requires note
    d3 = date(2026, 8, 7)
    s3, e3 = day_bounds_for_date(d3, "UTC")
    await _create_source(c1, minutes=10, policy="ALLOW_WITH_REASON", day=d3)
    with pytest.raises(ResourceStateWriteError) as aw:
        await create_allocation(
            c1,
            command=CreateAllocationCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                workcenter_code=WC,
                bucket_start=s3,
                bucket_end=e3,
                timezone="UTC",
                quantity_minutes=20,
                workload_source="OWNER_CONFIGURED",
                idempotency_key=str(uuid.uuid4()),
                reason_code="manager_ok",
            ),
            actor_user_id="admin-1",
        )
    assert aw.value.code == "over_allocation_reason_required"
    ok = await create_allocation(
        c1,
        command=CreateAllocationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            workcenter_code=WC,
            bucket_start=s3,
            bucket_end=e3,
            timezone="UTC",
            quantity_minutes=20,
            workload_source="OWNER_CONFIGURED",
            idempotency_key=str(uuid.uuid4()),
            reason_code="manager_ok",
            reason_note="approved overflow",
        ),
        actor_user_id="admin-1",
    )
    assert ok.over_allocation and ok.over_allocation.over_allocated is True


@pytest.mark.asyncio
async def test_null_workload_rejected_and_invalid_bucket(c1: AsyncSession):
    await _activate_capacity(c1)
    await _create_source(c1)
    start, end = day_bounds_for_date(date(2026, 8, 5), "UTC")
    with pytest.raises(Exception):
        CreateAllocationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            workcenter_code=WC,
            bucket_start=start,
            bucket_end=end,
            timezone="UTC",
            quantity_minutes=None,  # type: ignore[arg-type]
            workload_source="OWNER_CONFIGURED",
            idempotency_key=str(uuid.uuid4()),
        )
    bad_end = start + timedelta(hours=12)
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_allocation(
            c1,
            command=CreateAllocationCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                workcenter_code=WC,
                bucket_start=start,
                bucket_end=bad_end,
                timezone="UTC",
                quantity_minutes=10,
                workload_source="OWNER_CONFIGURED",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "invalid_bucket"


@pytest.mark.asyncio
async def test_domain_inactive_blocks_allocation(c1: AsyncSession):
    await _create_source(c1)
    start, end = day_bounds_for_date(date(2026, 8, 5), "UTC")
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_allocation(
            c1,
            command=CreateAllocationCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                workcenter_code=WC,
                bucket_start=start,
                bucket_end=end,
                timezone="UTC",
                quantity_minutes=10,
                workload_source="OWNER_CONFIGURED",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code in {"domain_not_active", "domain_disabled"}


@pytest.mark.asyncio
async def test_aggregate_clear_and_blocked_active(c1: AsyncSession):
    for domain in ("SCHEDULING", "MACHINE_RESERVATION", "CAPACITY_ALLOCATION"):
        await configure_resource_domain(
            c1,
            domain=domain,
            command=ResourceDomainConfigurationCommand(
                target_status="ACTIVE",
                expected_version=0,
                idempotency_key=str(uuid.uuid4()),
                reason_code="c1_all",
            ),
            actor_user_id="admin-1",
        )
    await c1.commit()
    start = datetime(2026, 8, 5, 10, 0, tzinfo=timezone.utc)
    await create_schedule(
        c1,
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
    ev = await evaluate_task_resource_state(c1, plan_id=23, task_key=LED_TASK)
    assert ev.scheduling.state == "CLEAR"
    assert ev.machine_reservation.state == "CLEAR"
    assert ev.capacity_allocation.state == "CLEAR"
    assert ev.aggregate == "CLEAR"

    await _create_source(c1, minutes=480)
    b_start, b_end = day_bounds_for_date(date(2026, 8, 5), "UTC")
    await create_allocation(
        c1,
        command=CreateAllocationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            workcenter_code=WC,
            bucket_start=b_start,
            bucket_end=b_end,
            timezone="UTC",
            quantity_minutes=30,
            workload_source="OWNER_CONFIGURED",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    ev2 = await evaluate_task_resource_state(c1, plan_id=23, task_key=LED_TASK)
    assert ev2.capacity_allocation.state == "ACTIVE"
    assert ev2.aggregate == "BLOCKED_ACTIVE"


@pytest.mark.asyncio
async def test_cancel_supersede_adjust(c1: AsyncSession):
    await _activate_capacity(c1)
    await _create_source(c1, minutes=1000)
    start, end = day_bounds_for_date(date(2026, 8, 5), "UTC")
    created = await create_allocation(
        c1,
        command=CreateAllocationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            workcenter_code=WC,
            bucket_start=start,
            bucket_end=end,
            timezone="UTC",
            quantity_minutes=30,
            workload_source="PRODUCT_AGGREGATE_DERIVED",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    adj = await adjust_allocation(
        c1,
        allocation_id=created.allocation_id,
        command=AdjustAllocationCommand(
            quantity_minutes=45,
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
            reason_code="bump",
        ),
        actor_user_id="admin-1",
    )
    assert adj.quantity_minutes == 45
    assert adj.version == 2

    sup = await supersede_allocation(
        c1,
        allocation_id=adj.allocation_id,
        command=SupersedeAllocationCommand(
            expected_version=2,
            idempotency_key=str(uuid.uuid4()),
            replacement_idempotency_key=str(uuid.uuid4()),
            workcenter_code=WC,
            bucket_start=start,
            bucket_end=end,
            timezone="UTC",
            quantity_minutes=50,
            workload_source="MANUAL_MANAGER_ESTIMATE",
            reason_code="replace",
        ),
        actor_user_id="admin-1",
    )
    assert sup.status == "SUPERSEDED"
    assert sup.replacement_allocation_id is not None

    # cancel a fresh allocation
    created2 = await create_allocation(
        c1,
        command=CreateAllocationCommand(
            execution_plan_id=23,
            task_key=LED_TASK,
            workcenter_code=WC,
            bucket_start=start,
            bucket_end=end,
            timezone="UTC",
            quantity_minutes=5,
            workload_source="OWNER_CONFIGURED",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    cancelled = await cancel_allocation(
        c1,
        allocation_id=created2.allocation_id,
        command=CancelAllocationCommand(
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
            reason_code="abort",
        ),
        actor_user_id="admin-1",
    )
    assert cancelled.status == "CANCELLED"


@pytest.mark.asyncio
async def test_source_missing_and_disable(c1: AsyncSession):
    await _activate_capacity(c1)
    start, end = day_bounds_for_date(date(2026, 8, 5), "UTC")
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_allocation(
            c1,
            command=CreateAllocationCommand(
                execution_plan_id=23,
                task_key=LED_TASK,
                workcenter_code="WC_UNKNOWN",
                bucket_start=start,
                bucket_end=end,
                timezone="UTC",
                quantity_minutes=10,
                workload_source="OWNER_CONFIGURED",
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "capacity_source_missing"

    src = await _create_source(c1)
    disabled = await disable_workcenter_capacity(
        c1,
        source_id=src.source_id,
        command=DisableWorkcenterCapacityCommand(
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
            reason_code="retire",
        ),
        actor_user_id="admin-1",
    )
    assert disabled.status == "DISABLED"
