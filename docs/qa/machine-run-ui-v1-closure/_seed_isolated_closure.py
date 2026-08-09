"""
Seed isolated s67 DB for MachineRun UI CREATE/ADD/context-link closure.
Never touches backend/dev.db (QA).
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[3] / "backend"
OUT_DIR = Path(__file__).resolve().parent
DB_PATH = OUT_DIR / "_isolated_s67_closure.db"

FACE_A = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_a"
FACE_B = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_b"
FACE_C = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_c"
FACE_D = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_d"
FACE_E = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_e"


def _async_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path.resolve().as_posix()}"


def _alembic(url: str) -> None:
    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["ENVIRONMENT"] = "test"
    env["DATABASE_URL"] = url
    env["JWT_SECRET_KEY"] = "local-dev-secret-not-for-production"
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr + proc.stdout)


def _task(task_id: str, label: str | None = None) -> dict:
    row = {
        "task_id": task_id,
        "display_name": label,
        "name": label,
        "source_operation_code": "face_cnc_cut",
        "resource_mode": "MACHINE_BOUND",
        "machine_capability_code": "CNC_ROUTER_CUTTING",
        "batch_eligible": True,
        "assigned_employee_id": None,
    }
    return row


def _seed_base(db: Path) -> None:
    sync = create_engine(f"sqlite:///{db.resolve().as_posix()}")
    with sync.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO machines "
                "(id, machine_code, name, machine_type, resource_kind, "
                "operational_status, is_available, is_active, capabilities, "
                "created_at, updated_at) "
                "VALUES (1, 'CNC-1', 'CNC One', 'cnc', 'machine', "
                "'active', 1, 1, :caps, "
                "'2026-08-09 10:00:00', '2026-08-09 10:00:00')"
            ),
            {"caps": json.dumps(["CNC_ROUTER_CUTTING"])},
        )
        # 21-22 → HELD seed; 23-24 → ADD candidates; 25-26 → RUNNING chip;
        # 27-28 → spare CREATE candidates; 29 → extra CREATE.
        plans = (
            (21, 880751, FACE_A, "Față A — comandă 880751"),
            (22, 880752, FACE_B, "Față B — comandă 880752"),
            (23, 880753, FACE_C, "Față C — ADD candidat"),
            (24, 880754, FACE_D, "Față D — ADD candidat"),
            (25, 880755, FACE_A, "Față A — chip RUNNING"),
            (26, 880756, FACE_B, "Față B — chip RUNNING"),
            (27, 880757, FACE_C, "Față C — CREATE"),
            (28, 880758, FACE_D, "Față D — CREATE"),
            (29, 880759, FACE_E, "Față E — CREATE"),
        )
        for pid, oid, tk, label in plans:
            conn.execute(
                text(
                    "INSERT INTO execution_plan "
                    "(id, order_id, order_code, snapshot_version, tasks_json, "
                    "total_estimated_time_minutes, created_at, updated_at) "
                    "VALUES (:id, :oid, :code, 1, :tj, 0.0, "
                    "'2026-08-09 10:00:00', '2026-08-09 10:00:00')"
                ),
                {
                    "id": pid,
                    "oid": oid,
                    "code": str(oid),
                    "tj": json.dumps(
                        {
                            "source": "order_snapshot_v2",
                            "operational_tasks": [_task(tk, label)],
                        }
                    ),
                },
            )
    sync.dispose()


async def _activate(session: AsyncSession) -> None:
    from schemas.resource_state_configuration import ResourceDomainConfigurationCommand
    from services.resource_domain_configuration_command_service import (
        configure_resource_domain,
    )

    await configure_resource_domain(
        session,
        domain="MACHINE_RESERVATION",
        command=ResourceDomainConfigurationCommand(
            target_status="ACTIVE",
            expected_version=0,
            idempotency_key=str(uuid.uuid4()),
            reason_code="ui_closure_seed_activate",
        ),
        actor_user_id="admin-1",
    )
    await session.commit()


def _window(offset_hours: int):
    start = datetime(2026, 8, 9, 8, 0, tzinfo=timezone.utc) + timedelta(
        hours=offset_hours
    )
    end = start + timedelta(hours=2)
    return start, end


async def _create(session: AsyncSession, hour: int, p1: int, t1: str, p2: int, t2: str):
    from schemas.resource_state_machine_run import (
        CreateMachineRunCommand,
        MachineRunParticipantRef,
    )
    from services.machine_run_command_service import create_machine_run

    start, end = _window(hour)
    result = await create_machine_run(
        session,
        command=CreateMachineRunCommand(
            machine_id=1,
            reservation_start=start,
            reservation_end=end,
            timezone="Europe/Bucharest",
            participants=[
                MachineRunParticipantRef(execution_plan_id=p1, task_key=t1),
                MachineRunParticipantRef(execution_plan_id=p2, task_key=t2),
            ],
            idempotency_key=str(uuid.uuid4()),
            reason_code="ui_closure_seed_create",
        ),
        actor_user_id="admin-1",
    )
    await session.commit()
    return result


async def main() -> None:
    sys.path.insert(0, str(BACKEND_ROOT))
    if DB_PATH.exists():
        DB_PATH.unlink()
    url = _async_url(DB_PATH)
    _alembic(url)
    _seed_base(DB_PATH)

    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    from schemas.resource_state_machine_run import (
        ConfirmMachineRunCommand,
        StartMachineRunCommand,
    )
    from services.machine_run_command_service import (
        confirm_machine_run,
        start_machine_run,
    )

    ids: dict[str, int] = {}
    async with factory() as session:
        await _activate(session)

        held = await _create(session, 0, 21, FACE_A, 22, FACE_B)
        ids["HELD"] = held.machine_run_id

        running = await _create(session, 6, 25, FACE_A, 26, FACE_B)
        running = await confirm_machine_run(
            session,
            machine_run_id=running.machine_run_id,
            command=ConfirmMachineRunCommand(
                expected_version=running.version,
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
        await session.commit()
        running = await start_machine_run(
            session,
            machine_run_id=running.machine_run_id,
            command=StartMachineRunCommand(
                expected_version=running.version,
                idempotency_key=str(uuid.uuid4()),
            ),
            actor_user_id="admin-1",
        )
        await session.commit()
        ids["RUNNING"] = running.machine_run_id

    await engine.dispose()
    manifest = {
        "db": str(DB_PATH),
        "alembic": "s67_machine_run_execution_status",
        "ids": ids,
        "create_candidate_plans": [27, 28, 29],
        "add_candidate_plans": [23, 24],
        "chip_plan_ids": [25, 26],
        "note": "isolated only — never QA",
    }
    (OUT_DIR / "_isolated_closure_ids.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
