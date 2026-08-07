"""ADD/REMOVE MACHINE_RUN participant — isolated DB proofs (never QA)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database import get_db
from core.sqlite_pragma import register_sqlite_foreign_keys
from dependencies.auth import get_current_user
from main import app
from models.execution_task_machine_reservation import (
    ExecutionTaskMachineReservation,
    ExecutionTaskMachineReservationTransition,
)
from models.machine_run import MachineRun, MachineRunParticipant, MachineRunTransition
from schemas.auth import UserResponse
from schemas.resource_state_configuration import ResourceDomainConfigurationCommand
from schemas.resource_state_machine_run import (
    AddMachineRunParticipantCommand,
    CancelMachineRunCommand,
    ConfirmMachineRunCommand,
    CreateMachineRunCommand,
    MachineRunParticipantRef,
    ReleaseMachineRunCommand,
    RemoveMachineRunParticipantCommand,
)
from services.machine_run_command_service import (
    add_machine_run_participant,
    cancel_machine_run,
    confirm_machine_run,
    create_machine_run,
    release_machine_run,
    remove_machine_run_participant,
)
from services.resource_domain_configuration_command_service import (
    configure_resource_domain,
)
from services.resource_state_read_service import evaluate_task_resource_state
from services.resource_state_write_common import ResourceStateWriteError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
FACE_A = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_a"
FACE_B = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_b"
FACE_C = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_c"
FACE_D = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_d"
OTHER_CAP = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vinyl_apply"
NOT_BOUND = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:paint_job"
NO_BATCH = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:no_batch"
NO_CAP = "missing-cap"


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
    start = datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc) + timedelta(hours=hours)
    end = start + timedelta(hours=1)
    return start, end


def _user(uid: str, role: str) -> UserResponse:
    return UserResponse(
        id=uid, email=f"{uid}@t.test", name=uid, role=role, last_login=None
    )


def _task(
    task_id: str,
    *,
    resource_mode: str | None = "MACHINE_BOUND",
    capability: str | None = "CNC_ROUTER_CUTTING",
    batch_eligible: bool | None = True,
) -> dict:
    row: dict = {
        "task_id": task_id,
        "source_operation_code": "face_cnc_cut",
        "assigned_employee_id": None,
    }
    if resource_mode is not None:
        row["resource_mode"] = resource_mode
    if capability is not None:
        row["machine_capability_code"] = capability
    if batch_eligible is not None:
        row["batch_eligible"] = batch_eligible
    return row


@pytest_asyncio.fixture
async def mr_db(tmp_path: Path):
    db = tmp_path / "add_remove_participant.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(sync)
    with sync.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, capabilities, "
                "created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, :caps, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            ),
            {"caps": json.dumps(["CNC_ROUTER_CUTTING"])},
        )
        plans = (
            (
                21,
                880751,
                [
                    _task(FACE_A),
                    _task(NOT_BOUND, resource_mode="HYBRID"),
                    _task(OTHER_CAP, capability="VINYL_APPLICATION"),
                ],
            ),
            (
                22,
                880752,
                [
                    _task(FACE_B),
                    _task(NO_BATCH, batch_eligible=False),
                    _task(NO_CAP, capability=None),
                ],
            ),
            (23, 880753, [_task(FACE_C), _task(FACE_D)]),
        )
        for pid, oid, tasks in plans:
            conn.execute(
                text(
                    "INSERT INTO execution_plan "
                    "(id, order_id, order_code, snapshot_version, tasks_json, "
                    "total_estimated_time_minutes, created_at, updated_at) "
                    "VALUES (:id, :oid, :code, 1, :tj, 0.0, "
                    "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
                ),
                {
                    "id": pid,
                    "oid": oid,
                    "code": str(oid),
                    "tj": json.dumps(
                        {
                            "source": "order_snapshot_v2",
                            "operational_tasks": tasks,
                        }
                    ),
                },
            )
    sync.dispose()
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _activate(session: AsyncSession):
    await configure_resource_domain(
        session,
        domain="MACHINE_RESERVATION",
        command=ResourceDomainConfigurationCommand(
            target_status="ACTIVE",
            expected_version=0,
            idempotency_key=str(uuid.uuid4()),
            reason_code="mr_activate",
        ),
        actor_user_id="admin-1",
    )
    await session.commit()


async def _counts(session: AsyncSession) -> dict[str, int]:
    return {
        "runs": int(
            (
                await session.execute(select(func.count()).select_from(MachineRun))
            ).scalar_one()
        ),
        "participants": int(
            (
                await session.execute(
                    select(func.count()).select_from(MachineRunParticipant)
                )
            ).scalar_one()
        ),
        "run_transitions": int(
            (
                await session.execute(
                    select(func.count()).select_from(MachineRunTransition)
                )
            ).scalar_one()
        ),
        "reservations": int(
            (
                await session.execute(
                    select(func.count()).select_from(ExecutionTaskMachineReservation)
                )
            ).scalar_one()
        ),
        "reservation_transitions": int(
            (
                await session.execute(
                    select(func.count()).select_from(
                        ExecutionTaskMachineReservationTransition
                    )
                )
            ).scalar_one()
        ),
    }


async def _create(
    session: AsyncSession,
    parts: list[tuple[int, str]] | None = None,
    *,
    hours: int = 0,
):
    start, end = _window(hours)
    participants = parts or [(21, FACE_A), (22, FACE_B)]
    return await create_machine_run(
        session,
        command=CreateMachineRunCommand(
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            participants=[
                MachineRunParticipantRef(execution_plan_id=pid, task_key=tk)
                for pid, tk in participants
            ],
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )


async def _r6(session: AsyncSession, plan_id: int, task_key: str) -> str:
    state = await evaluate_task_resource_state(
        session, plan_id=plan_id, task_key=task_key
    )
    return state.machine_reservation.state


async def _active_parts(session: AsyncSession, run_id: int) -> list[tuple[int, str]]:
    rows = (
        await session.execute(
            select(MachineRunParticipant).where(
                MachineRunParticipant.machine_run_id == run_id,
                MachineRunParticipant.status == "ACTIVE",
            )
        )
    ).scalars().all()
    return sorted([(p.execution_plan_id, p.task_key) for p in rows])


@pytest.mark.asyncio
async def test_add_held_multi_plan_and_r6(mr_db: AsyncSession):
    await _activate(mr_db)
    created = await _create(mr_db)
    assert await _r6(mr_db, 23, FACE_C) == "CLEAR"
    before = await _counts(mr_db)
    res_before = (
        await mr_db.execute(
            select(ExecutionTaskMachineReservation).where(
                ExecutionTaskMachineReservation.id == created.reservation_id
            )
        )
    ).scalar_one()

    added = await add_machine_run_participant(
        mr_db,
        machine_run_id=created.machine_run_id,
        command=AddMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert added.status == "HELD"
    assert added.reservation_status == "HELD"
    assert added.version == 2
    assert added.reservation_version == 2
    assert added.machine_id == created.machine_id
    assert added.reservation_id == created.reservation_id
    assert added.reservation_start == res_before.reservation_start
    assert added.reservation_end == res_before.reservation_end
    assert added.operation == "ADD_MACHINE_RUN_PARTICIPANT"
    assert added.affected_participant is not None
    assert added.affected_participant.execution_plan_id == 23
    assert added.affected_participant.task_key == FACE_C
    assert added.affected_participant.status == "ACTIVE"
    assert await _active_parts(mr_db, created.machine_run_id) == [
        (21, FACE_A),
        (22, FACE_B),
        (23, FACE_C),
    ]
    assert await _r6(mr_db, 21, FACE_A) == "ACTIVE"
    assert await _r6(mr_db, 22, FACE_B) == "ACTIVE"
    assert await _r6(mr_db, 23, FACE_C) == "ACTIVE"
    after = await _counts(mr_db)
    assert after["participants"] == before["participants"] + 1
    assert after["run_transitions"] == before["run_transitions"] + 1
    assert after["reservation_transitions"] == before["reservation_transitions"] + 1
    assert after["runs"] == before["runs"]
    assert after["reservations"] == before["reservations"]


@pytest.mark.asyncio
async def test_remove_soft_and_r6_clear(mr_db: AsyncSession):
    await _activate(mr_db)
    created = await _create(
        mr_db, parts=[(21, FACE_A), (22, FACE_B), (23, FACE_C)]
    )
    removed = await remove_machine_run_participant(
        mr_db,
        machine_run_id=created.machine_run_id,
        command=RemoveMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert removed.status == "HELD"
    assert removed.version == 2
    assert removed.reservation_version == 2
    assert removed.affected_participant is not None
    assert removed.affected_participant.status == "REMOVED"
    assert await _active_parts(mr_db, created.machine_run_id) == [
        (21, FACE_A),
        (22, FACE_B),
    ]
    assert await _r6(mr_db, 23, FACE_C) == "CLEAR"
    assert await _r6(mr_db, 21, FACE_A) == "ACTIVE"

    row = (
        await mr_db.execute(
            select(MachineRunParticipant).where(
                MachineRunParticipant.machine_run_id == created.machine_run_id,
                MachineRunParticipant.execution_plan_id == 23,
                MachineRunParticipant.task_key == FACE_C,
            )
        )
    ).scalar_one()
    assert row.status == "REMOVED"
    assert row.removed_at is not None
    assert row.removed_by == "admin-1"


@pytest.mark.asyncio
async def test_reactivate_removed_same_row(mr_db: AsyncSession):
    await _activate(mr_db)
    created = await _create(
        mr_db, parts=[(21, FACE_A), (22, FACE_B), (23, FACE_C)]
    )
    await remove_machine_run_participant(
        mr_db,
        machine_run_id=created.machine_run_id,
        command=RemoveMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert await _r6(mr_db, 23, FACE_C) == "CLEAR"
    before_count = await _counts(mr_db)
    revived = await add_machine_run_participant(
        mr_db,
        machine_run_id=created.machine_run_id,
        command=AddMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=2,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    assert revived.affected_participant is not None
    assert revived.affected_participant.status == "ACTIVE"
    assert await _r6(mr_db, 23, FACE_C) == "ACTIVE"
    after = await _counts(mr_db)
    assert after["participants"] == before_count["participants"]  # no new row


@pytest.mark.asyncio
async def test_minimum_participants_violation(mr_db: AsyncSession):
    await _activate(mr_db)
    created = await _create(mr_db)  # 2 active
    before = await _counts(mr_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await remove_machine_run_participant(
            mr_db,
            machine_run_id=created.machine_run_id,
            command=RemoveMachineRunParticipantCommand(
                execution_plan_id=22,
                task_key=FACE_B,
                expected_version=1,
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "minimum_participants_violation"
    assert await _counts(mr_db) == before


@pytest.mark.asyncio
async def test_add_remove_idempotency(mr_db: AsyncSession):
    await _activate(mr_db)
    created = await _create(mr_db)
    add_key = str(uuid.uuid4())
    first = await add_machine_run_participant(
        mr_db,
        machine_run_id=created.machine_run_id,
        command=AddMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=1,
            idempotency_key=add_key,
        ),
        actor_user_id="admin-1",
    )
    mid = await _counts(mr_db)
    second = await add_machine_run_participant(
        mr_db,
        machine_run_id=created.machine_run_id,
        command=AddMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=1,
            idempotency_key=add_key,
        ),
        actor_user_id="admin-1",
    )
    assert second.already_applied is True
    assert second.version == first.version
    assert await _counts(mr_db) == mid

    with pytest.raises(ResourceStateWriteError) as exc:
        await add_machine_run_participant(
            mr_db,
            machine_run_id=created.machine_run_id,
            command=AddMachineRunParticipantCommand(
                execution_plan_id=23,
                task_key=FACE_D,
                expected_version=1,
                idempotency_key=add_key,
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "idempotency_payload_conflict"

    rem_key = str(uuid.uuid4())
    rem1 = await remove_machine_run_participant(
        mr_db,
        machine_run_id=created.machine_run_id,
        command=RemoveMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=2,
            idempotency_key=rem_key,
        ),
        actor_user_id="admin-1",
    )
    mid2 = await _counts(mr_db)
    rem2 = await remove_machine_run_participant(
        mr_db,
        machine_run_id=created.machine_run_id,
        command=RemoveMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=2,
            idempotency_key=rem_key,
        ),
        actor_user_id="admin-1",
    )
    assert rem2.already_applied is True
    assert rem2.version == rem1.version
    assert await _counts(mr_db) == mid2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "setup,code,kwargs",
    [
        ("reserved", "invalid_transition", {"execution_plan_id": 23, "task_key": FACE_C}),
        ("cancelled", "invalid_transition", {"execution_plan_id": 23, "task_key": FACE_C}),
        ("released", "invalid_transition", {"execution_plan_id": 23, "task_key": FACE_C}),
        ("stale", "cas_stale", {"execution_plan_id": 23, "task_key": FACE_C}),
        ("unknown", "task_key_not_found", {"execution_plan_id": 23, "task_key": "nope"}),
        ("not_bound", "task_not_machine_bound", {"execution_plan_id": 21, "task_key": NOT_BOUND}),
        ("no_cap", "task_capability_unknown", {"execution_plan_id": 22, "task_key": NO_CAP}),
        ("no_batch", "task_not_batch_eligible", {"execution_plan_id": 22, "task_key": NO_BATCH}),
        ("cap_mismatch", "participant_capability_mismatch", {"execution_plan_id": 21, "task_key": OTHER_CAP}),
        ("duplicate", "participant_already_exists", {"execution_plan_id": 21, "task_key": FACE_A}),
    ],
)
async def test_add_negatives(mr_db: AsyncSession, setup, code, kwargs):
    await _activate(mr_db)
    created = await _create(mr_db)
    run_id = created.machine_run_id
    ver = 1
    if setup == "reserved":
        await confirm_machine_run(
            mr_db,
            machine_run_id=run_id,
            command=ConfirmMachineRunCommand(
                expected_version=1, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        ver = 2
    elif setup == "cancelled":
        await cancel_machine_run(
            mr_db,
            machine_run_id=run_id,
            command=CancelMachineRunCommand(
                expected_version=1, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        ver = 2
    elif setup == "released":
        await confirm_machine_run(
            mr_db,
            machine_run_id=run_id,
            command=ConfirmMachineRunCommand(
                expected_version=1, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        await release_machine_run(
            mr_db,
            machine_run_id=run_id,
            command=ReleaseMachineRunCommand(
                expected_version=2, idempotency_key=str(uuid.uuid4())
            ),
            actor_user_id="admin-1",
        )
        ver = 3

    before = await _counts(mr_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await add_machine_run_participant(
            mr_db,
            machine_run_id=run_id,
            command=AddMachineRunParticipantCommand(
                expected_version=99 if setup == "stale" else ver,
                idempotency_key=str(uuid.uuid4()),
                **kwargs,
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == code
    assert await _counts(mr_db) == before


@pytest.mark.asyncio
async def test_add_active_elsewhere_rejected(mr_db: AsyncSession):
    await _activate(mr_db)
    await _create(mr_db, parts=[(21, FACE_A), (22, FACE_B)], hours=0)
    other = await _create(mr_db, parts=[(23, FACE_C), (23, FACE_D)], hours=3)
    before = await _counts(mr_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await add_machine_run_participant(
            mr_db,
            machine_run_id=other.machine_run_id,
            command=AddMachineRunParticipantCommand(
                execution_plan_id=21,
                task_key=FACE_A,
                expected_version=1,
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "task_already_in_active_machine_run"
    assert await _counts(mr_db) == before


@pytest.mark.asyncio
async def test_remove_negatives(mr_db: AsyncSession):
    await _activate(mr_db)
    created = await _create(
        mr_db, parts=[(21, FACE_A), (22, FACE_B), (23, FACE_C)]
    )
    await remove_machine_run_participant(
        mr_db,
        machine_run_id=created.machine_run_id,
        command=RemoveMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=1,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    before = await _counts(mr_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await remove_machine_run_participant(
            mr_db,
            machine_run_id=created.machine_run_id,
            command=RemoveMachineRunParticipantCommand(
                execution_plan_id=23,
                task_key=FACE_C,
                expected_version=2,
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "participant_not_found"
    assert await _counts(mr_db) == before

    await add_machine_run_participant(
        mr_db,
        machine_run_id=created.machine_run_id,
        command=AddMachineRunParticipantCommand(
            execution_plan_id=23,
            task_key=FACE_C,
            expected_version=2,
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    await confirm_machine_run(
        mr_db,
        machine_run_id=created.machine_run_id,
        command=ConfirmMachineRunCommand(
            expected_version=3, idempotency_key=str(uuid.uuid4())
        ),
        actor_user_id="admin-1",
    )
    before2 = await _counts(mr_db)
    with pytest.raises(ResourceStateWriteError) as exc2:
        await remove_machine_run_participant(
            mr_db,
            machine_run_id=created.machine_run_id,
            command=RemoveMachineRunParticipantCommand(
                execution_plan_id=23,
                task_key=FACE_C,
                expected_version=4,
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
    assert exc2.value.code == "invalid_transition"
    assert await _counts(mr_db) == before2


@pytest.mark.asyncio
async def test_http_permission(tmp_path: Path):
    db = tmp_path / "ar_http.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(sync)
    with sync.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, "
                "created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            )
        )
        for pid, oid, tasks in (
            (21, 880751, [FACE_A]),
            (22, 880752, [FACE_B]),
            (23, 880753, [FACE_C]),
        ):
            conn.execute(
                text(
                    "INSERT INTO execution_plan "
                    "(id, order_id, order_code, snapshot_version, tasks_json, "
                    "total_estimated_time_minutes, created_at, updated_at) "
                    "VALUES (:id, :oid, :code, 1, :tj, 0.0, "
                    "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
                ),
                {
                    "id": pid,
                    "oid": oid,
                    "code": str(oid),
                    "tj": json.dumps(
                        {
                            "source": "order_snapshot_v2",
                            "operational_tasks": [_task(t) for t in tasks],
                        }
                    ),
                },
            )
    sync.dispose()
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _activate(session)
        created = await _create(session)

    async def _override_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_db
    try:
        body = {
            "execution_plan_id": 23,
            "task_key": FACE_C,
            "expected_version": 1,
            "idempotency_key": str(uuid.uuid4()),
        }
        app.dependency_overrides[get_current_user] = lambda: _user("op-1", "operator")
        with TestClient(app) as client:
            denied = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/add-participant",
                json=body,
            )
            assert denied.status_code == 403

        app.dependency_overrides[get_current_user] = lambda: _user("admin-1", "admin")
        with TestClient(app) as client:
            ok = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/add-participant",
                json=body,
            )
            assert ok.status_code == 200, ok.text
            assert ok.json()["operation"] == "ADD_MACHINE_RUN_PARTICIPANT"
            assert ok.json()["version"] == 2
            rem = client.post(
                f"/api/v1/execution/resource-state/machine-runs/"
                f"{created.machine_run_id}/remove-participant",
                json={
                    "execution_plan_id": 23,
                    "task_key": FACE_C,
                    "expected_version": 2,
                    "idempotency_key": str(uuid.uuid4()),
                },
            )
            assert rem.status_code == 200, rem.text
            assert rem.json()["operation"] == "REMOVE_MACHINE_RUN_PARTICIPANT"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        await engine.dispose()
