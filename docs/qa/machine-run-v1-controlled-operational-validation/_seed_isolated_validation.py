"""
Seed isolated s67 DB for MachineRun controlled operational scenario validation.
Never touches backend/dev.db (protected QA).
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
DB_PATH = OUT_DIR / "_isolated_s67_validation.db"

FACE_A = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_a"
FACE_B = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_b"
FACE_C = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_c"
FACE_D = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_d"
FACE_E = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_e"
FACE_F = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:face_cnc_cut_f"


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
    return {
        "task_id": task_id,
        "display_name": label,
        "name": label,
        "source_operation_code": "face_cnc_cut",
        "resource_mode": "MACHINE_BOUND",
        "machine_capability_code": "CNC_ROUTER_CUTTING",
        "batch_eligible": True,
        "assigned_employee_id": None,
        "status": "READY",
    }


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
        # Enough plans for multi-plan, ADD/REMOVE, overlap, medium lookup.
        plans = []
        faces = [FACE_A, FACE_B, FACE_C, FACE_D, FACE_E, FACE_F]
        for i in range(40, 70):
            oid = 881000 + i
            face = faces[(i - 40) % len(faces)]
            plans.append((i, oid, face, f"Plan {i} order {oid}"))
        # medium plan with many tasks for lookup volume (plan 70)
        many = [_task(f"task_slot_{n}", f"Task slot {n}") for n in range(24)]
        conn.execute(
            text(
                "INSERT INTO execution_plan "
                "(id, order_id, order_code, snapshot_version, tasks_json, "
                "total_estimated_time_minutes, created_at, updated_at) "
                "VALUES (70, 881070, '881070', 1, :tj, 0.0, "
                "'2026-08-09 10:00:00', '2026-08-09 10:00:00')"
            ),
            {"tj": json.dumps({"source": "order_snapshot_v2", "operational_tasks": many})},
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
            reason_code="controlled_validation_seed_activate",
        ),
        actor_user_id="admin-1",
    )
    await session.commit()


async def main() -> None:
    sys.path.insert(0, str(BACKEND_ROOT))
    if DB_PATH.exists():
        DB_PATH.unlink()
    for suffix in ("-wal", "-shm"):
        p = Path(str(DB_PATH) + suffix)
        if p.exists():
            p.unlink()
    url = _async_url(DB_PATH)
    _alembic(url)
    _seed_base(DB_PATH)

    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _activate(session)
    await engine.dispose()

    manifest = {
        "db": str(DB_PATH.resolve()),
        "alembic": "s67_machine_run_execution_status",
        "machine_id": 1,
        "single_task_plans": list(range(40, 70)),
        "medium_plan_id": 70,
        "medium_task_count": 24,
        "note": "isolated only — never QA",
        "evidence_type": "CONTROLLED_SCENARIO_EVIDENCE",
    }
    (OUT_DIR / "_isolated_validation_ids.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
