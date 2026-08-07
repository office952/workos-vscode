"""CREATE_MACHINE_RUN minimal runtime — isolated DB proofs (never QA)."""

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
from models.execution_task_machine_reservation import ExecutionTaskMachineReservation
from models.machine_run import MachineRun, MachineRunParticipant, MachineRunTransition
from schemas.auth import UserResponse
from schemas.resource_state_configuration import ResourceDomainConfigurationCommand
from schemas.resource_state_machine_run import (
    CreateMachineRunCommand,
    MachineRunParticipantRef,
)
from schemas.resource_state_reservation import CreateReservationCommand
from services.execution_task_machine_reservation_command_service import (
    create_reservation,
)
from services.machine_run_command_service import create_machine_run
from services.resource_domain_configuration_command_service import (
    configure_resource_domain,
)
from services.resource_state_read_service import evaluate_task_resource_state
from services.resource_state_write_common import ResourceStateWriteError

BACKEND_ROOT = Path(__file__).resolve().parents[1]

FACE_A = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_a"
FACE_B = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_b"
FACE_C = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_c"
OTHER_CAP = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vinyl_apply"
NOT_BOUND = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:paint_job"


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
    end = start + timedelta(hours=2)
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
    source_operation_code: str = "face_cnc_cut",
) -> dict:
    row: dict = {
        "task_id": task_id,
        "source_operation_code": source_operation_code,
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
    db = tmp_path / "create_machine_run.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(sync)
    tasks_21 = {
        "source": "order_snapshot_v2",
        "operational_tasks": [
            _task(FACE_A),
            _task(NOT_BOUND, resource_mode="HYBRID", capability="CNC_ROUTER_CUTTING"),
            _task(
                OTHER_CAP,
                capability="VINYL_APPLICATION",
                source_operation_code="face_vinyl_apply",
            ),
        ],
    }
    tasks_22 = {
        "source": "order_snapshot_v2",
        "operational_tasks": [
            _task(FACE_B),
            _task(
                FACE_C,
                batch_eligible=False,
            ),
            _task(
                "missing-cap",
                capability=None,
            ),
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
                "operational_status, is_available, is_active, capabilities, "
                "created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, :caps, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            ),
            {"caps": json.dumps(["CNC_ROUTER_CUTTING"])},
        )
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, capabilities, "
                "created_at, updated_at) "
                "VALUES (2, 'CNC-2', 'CNC Two', 'cnc', 'machine', "
                "'active', 1, 1, NULL, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, "
                "created_at, updated_at) "
                "VALUES (3, 'CNC-OFF', 'Offline', 'cnc', 'machine', "
                "'maintenance', 0, 0, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, capabilities, "
                "created_at, updated_at) "
                "VALUES (4, 'VINYL-1', 'Vinyl', 'vinyl', 'machine', "
                "'active', 1, 1, :caps, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            ),
            {"caps": json.dumps(["VINYL_APPLICATION"])},
        )
        conn.execute(
            text(
                "INSERT INTO execution_plan "
                "(id, order_id, order_code, snapshot_version, tasks_json, "
                "total_estimated_time_minutes, created_at, updated_at) "
                "VALUES (21, 880751, '880751', 1, :tj, 0.0, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            ),
            {"tj": json.dumps(tasks_21)},
        )
        conn.execute(
            text(
                "INSERT INTO execution_plan "
                "(id, order_id, order_code, snapshot_version, tasks_json, "
                "total_estimated_time_minutes, created_at, updated_at) "
                "VALUES (22, 880752, '880752', 1, :tj, 0.0, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            ),
            {"tj": json.dumps(tasks_22)},
        )
    sync.dispose()
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _activate_reservation(session: AsyncSession):
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
    runs = (
        await session.execute(select(func.count()).select_from(MachineRun))
    ).scalar_one()
    parts = (
        await session.execute(select(func.count()).select_from(MachineRunParticipant))
    ).scalar_one()
    tr = (
        await session.execute(select(func.count()).select_from(MachineRunTransition))
    ).scalar_one()
    res = (
        await session.execute(
            select(func.count()).select_from(ExecutionTaskMachineReservation)
        )
    ).scalar_one()
    res_tr = (
        await session.execute(
            text(
                "SELECT COUNT(*) FROM execution_task_machine_reservation_transitions"
            )
        )
    ).scalar_one()
    return {
        "runs": int(runs),
        "participants": int(parts),
        "run_transitions": int(tr),
        "reservations": int(res),
        "reservation_transitions": int(res_tr),
    }


def _cmd(
    *,
    participants: list[tuple[int, str]],
    machine_id: int = 1,
    hours: int = 0,
    idem: str | None = None,
    expected_version: int = 0,
) -> CreateMachineRunCommand:
    start, end = _window(hours)
    return CreateMachineRunCommand(
        machine_id=machine_id,
        reservation_start=start,
        reservation_end=end,
        timezone="UTC",
        participants=[
            MachineRunParticipantRef(execution_plan_id=pid, task_key=tk)
            for pid, tk in participants
        ],
        expected_version=expected_version,
        idempotency_key=idem or str(uuid.uuid4()),
        reason_code="machine_run_create",
    )


@pytest.mark.asyncio
async def test_create_happy_path_multi_plan(mr_db: AsyncSession):
    await _activate_reservation(mr_db)
    before = await _counts(mr_db)
    result = await create_machine_run(
        mr_db,
        command=_cmd(participants=[(21, FACE_A), (22, FACE_B)]),
        actor_user_id="admin-1",
    )
    assert result.status == "HELD"
    assert result.version == 1
    assert result.reservation_status == "HELD"
    assert result.reservation_version == 1
    assert result.already_applied is False
    assert len(result.participants) == 2
    orders = {p.order_id for p in result.participants}
    assert orders == {880751, 880752}
    after = await _counts(mr_db)
    assert after["runs"] == before["runs"] + 1
    assert after["participants"] == before["participants"] + 2
    assert after["run_transitions"] == before["run_transitions"] + 1
    assert after["reservations"] == before["reservations"] + 1
    assert after["reservation_transitions"] == before["reservation_transitions"] + 1

    res = await mr_db.get(ExecutionTaskMachineReservation, result.reservation_id)
    assert res is not None
    assert res.execution_plan_id is None
    assert res.task_key is None
    assert res.machine_run_id == result.machine_run_id


@pytest.mark.asyncio
async def test_r6_both_participants_see_active_reservation(mr_db: AsyncSession):
    await _activate_reservation(mr_db)
    await create_machine_run(
        mr_db,
        command=_cmd(participants=[(21, FACE_A), (22, FACE_B)]),
        actor_user_id="admin-1",
    )
    for plan_id, task_key in ((21, FACE_A), (22, FACE_B)):
        state = await evaluate_task_resource_state(
            mr_db, plan_id=plan_id, task_key=task_key
        )
        assert state.machine_reservation.state == "ACTIVE"


@pytest.mark.asyncio
async def test_idempotency_replay_order_independent(mr_db: AsyncSession):
    await _activate_reservation(mr_db)
    key = str(uuid.uuid4())
    first = await create_machine_run(
        mr_db,
        command=_cmd(
            participants=[(21, FACE_A), (22, FACE_B)],
            idem=key,
        ),
        actor_user_id="admin-1",
    )
    mid = await _counts(mr_db)
    second = await create_machine_run(
        mr_db,
        command=_cmd(
            participants=[(22, FACE_B), (21, FACE_A)],
            idem=key,
        ),
        actor_user_id="admin-1",
    )
    assert second.already_applied is True
    assert second.machine_run_id == first.machine_run_id
    assert second.reservation_id == first.reservation_id
    assert await _counts(mr_db) == mid


@pytest.mark.asyncio
async def test_idempotency_conflict_different_payload(mr_db: AsyncSession):
    await _activate_reservation(mr_db)
    key = str(uuid.uuid4())
    await create_machine_run(
        mr_db,
        command=_cmd(participants=[(21, FACE_A), (22, FACE_B)], idem=key),
        actor_user_id="admin-1",
    )
    before = await _counts(mr_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_machine_run(
            mr_db,
            command=_cmd(
                participants=[(21, FACE_A), (22, FACE_B)],
                idem=key,
                hours=3,
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "idempotency_payload_conflict"
    assert await _counts(mr_db) == before


@pytest.mark.asyncio
async def test_overlap_with_task_owned_reservation(mr_db: AsyncSession):
    await _activate_reservation(mr_db)
    start, end = _window()
    await create_reservation(
        mr_db,
        command=CreateReservationCommand(
            execution_plan_id=21,
            task_key=FACE_A,
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="UTC",
            idempotency_key=str(uuid.uuid4()),
        ),
        actor_user_id="admin-1",
    )
    before = await _counts(mr_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_machine_run(
            mr_db,
            command=_cmd(participants=[(21, FACE_A), (22, FACE_B)]),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "overlap_conflict"
    # FACE_A already has task reservation; create must not add run rows.
    after = await _counts(mr_db)
    assert after["runs"] == before["runs"]
    assert after["participants"] == before["participants"]


@pytest.mark.asyncio
async def test_active_membership_guard(mr_db: AsyncSession):
    await _activate_reservation(mr_db)
    await create_machine_run(
        mr_db,
        command=_cmd(participants=[(21, FACE_A), (22, FACE_B)], hours=0),
        actor_user_id="admin-1",
    )
    before = await _counts(mr_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_machine_run(
            mr_db,
            command=_cmd(
                participants=[(21, FACE_A), (22, FACE_B)],
                machine_id=2,
                hours=5,
            ),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "task_already_in_active_machine_run"
    assert await _counts(mr_db) == before


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "parts,code",
    [
        ([(21, FACE_A)], "invalid_participant_set"),
        ([(21, FACE_A), (21, FACE_A)], "duplicate_participant"),
        ([(21, "no-such-task"), (22, FACE_B)], "task_key_not_found"),
        ([(21, NOT_BOUND), (22, FACE_B)], "task_not_machine_bound"),
        ([(21, FACE_A), (22, "missing-cap")], "task_capability_unknown"),
        ([(21, FACE_A), (22, FACE_C)], "task_not_batch_eligible"),
        ([(21, FACE_A), (21, OTHER_CAP)], "participant_capability_mismatch"),
    ],
)
async def test_negative_demand_and_participants(
    mr_db: AsyncSession, parts, code
):
    await _activate_reservation(mr_db)
    before = await _counts(mr_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_machine_run(
            mr_db,
            command=_cmd(participants=parts, machine_id=2),
            actor_user_id="admin-1",
        )
    assert exc.value.code == code
    assert await _counts(mr_db) == before


@pytest.mark.asyncio
async def test_machine_inactive_and_capability_mismatch(mr_db: AsyncSession):
    await _activate_reservation(mr_db)
    before = await _counts(mr_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_machine_run(
            mr_db,
            command=_cmd(participants=[(21, FACE_A), (22, FACE_B)], machine_id=3),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "machine_not_reservable"
    with pytest.raises(ResourceStateWriteError) as exc2:
        await create_machine_run(
            mr_db,
            command=_cmd(participants=[(21, FACE_A), (22, FACE_B)], machine_id=4),
            actor_user_id="admin-1",
        )
    assert exc2.value.code == "machine_capability_mismatch"
    assert await _counts(mr_db) == before


@pytest.mark.asyncio
async def test_domain_gate_required(mr_db: AsyncSession):
    before = await _counts(mr_db)
    with pytest.raises(ResourceStateWriteError) as exc:
        await create_machine_run(
            mr_db,
            command=_cmd(participants=[(21, FACE_A), (22, FACE_B)]),
            actor_user_id="admin-1",
        )
    assert exc.value.code == "domain_not_active"
    assert await _counts(mr_db) == before


@pytest.mark.asyncio
async def test_empty_machine_capabilities_allowed(mr_db: AsyncSession):
    await _activate_reservation(mr_db)
    result = await create_machine_run(
        mr_db,
        command=_cmd(participants=[(21, FACE_A), (22, FACE_B)], machine_id=2),
        actor_user_id="admin-1",
    )
    assert result.status == "HELD"


@pytest.mark.asyncio
async def test_http_create_and_permission(tmp_path: Path):
    db = tmp_path / "mr_http.db"
    url = _async_url(db)
    proc = _alembic_cmd(url, "upgrade", "head")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    register_sqlite_foreign_keys(sync)
    tasks_21 = {
        "source": "order_snapshot_v2",
        "operational_tasks": [_task(FACE_A)],
    }
    tasks_22 = {
        "source": "order_snapshot_v2",
        "operational_tasks": [_task(FACE_B)],
    }
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
        conn.execute(
            text(
                "INSERT INTO execution_plan "
                "(id, order_id, order_code, snapshot_version, tasks_json, "
                "total_estimated_time_minutes, created_at, updated_at) "
                "VALUES (21, 880751, '880751', 1, :tj, 0.0, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            ),
            {"tj": json.dumps(tasks_21)},
        )
        conn.execute(
            text(
                "INSERT INTO execution_plan "
                "(id, order_id, order_code, snapshot_version, tasks_json, "
                "total_estimated_time_minutes, created_at, updated_at) "
                "VALUES (22, 880752, '880752', 1, :tj, 0.0, "
                "'2026-08-07 10:00:00', '2026-08-07 10:00:00')"
            ),
            {"tj": json.dumps(tasks_22)},
        )
    sync.dispose()

    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _activate_reservation(session)

    async def _override_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_db
    try:
        app.dependency_overrides[get_current_user] = lambda: _user("op-1", "operator")
        with TestClient(app) as client:
            start, end = _window(hours=8)
            body = {
                "machine_id": 1,
                "reservation_start": start.isoformat(),
                "reservation_end": end.isoformat(),
                "timezone": "UTC",
                "participants": [
                    {"execution_plan_id": 21, "task_key": FACE_A},
                    {"execution_plan_id": 22, "task_key": FACE_B},
                ],
                "idempotency_key": str(uuid.uuid4()),
            }
            denied = client.post(
                "/api/v1/execution/resource-state/machine-runs", json=body
            )
            assert denied.status_code == 403

        app.dependency_overrides[get_current_user] = lambda: _user("admin-1", "admin")
        with TestClient(app) as client:
            start, end = _window(hours=8)
            key = str(uuid.uuid4())
            body = {
                "machine_id": 1,
                "reservation_start": start.isoformat(),
                "reservation_end": end.isoformat(),
                "timezone": "UTC",
                "participants": [
                    {"execution_plan_id": 21, "task_key": FACE_A},
                    {"execution_plan_id": 22, "task_key": FACE_B},
                ],
                "idempotency_key": key,
                "reason_code": "machine_run_create",
            }
            ok = client.post(
                "/api/v1/execution/resource-state/machine-runs", json=body
            )
            assert ok.status_code == 200, ok.text
            data = ok.json()
            assert data["status"] == "HELD"
            assert data["reservation_status"] == "HELD"
            assert len(data["participants"]) == 2
            replay = client.post(
                "/api/v1/execution/resource-state/machine-runs", json=body
            )
            assert replay.status_code == 200
            assert replay.json()["already_applied"] is True
            assert replay.json()["machine_run_id"] == data["machine_run_id"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        await engine.dispose()


def test_face_cnc_cut_contract_stamps_match_create_eligibility():
    from services.operation_machine_requirement_contract import (
        FACE_CNC_CUT_MACHINE_REQUIREMENT,
    )

    assert FACE_CNC_CUT_MACHINE_REQUIREMENT.resource_mode == "MACHINE_BOUND"
    assert (
        FACE_CNC_CUT_MACHINE_REQUIREMENT.machine_capability_code
        == "CNC_ROUTER_CUTTING"
    )
    assert FACE_CNC_CUT_MACHINE_REQUIREMENT.batch_eligible is True
    stamped = _task(FACE_A)
    assert stamped["resource_mode"] == FACE_CNC_CUT_MACHINE_REQUIREMENT.resource_mode
    assert (
        stamped["machine_capability_code"]
        == FACE_CNC_CUT_MACHINE_REQUIREMENT.machine_capability_code
    )
    assert stamped["batch_eligible"] is FACE_CNC_CUT_MACHINE_REQUIREMENT.batch_eligible
