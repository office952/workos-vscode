"""MOBILE-T05B — live concurrent Complete probe against trusted :8001 backend."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET_KEY", "local-dev-secret-not-for-production")
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_BACKEND_ROOT}/dev.db"

import httpx
from dependencies.auth import SYNTHETIC_DEV_ADMIN_USER_ID
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from services.task_work_session_service import (
    derive_task_status_for_employee,
    is_session_active,
    sessions_for_task,
)
from sqlalchemy import delete, select

from core.database import db_manager

BASE_URL = "http://127.0.0.1:8001"
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
FIXTURE_ORDER_ID = 92350
FIXTURE_TASK_ID = "T-M05B-CONC-COMPLETE"
FIXTURE_STARTED_AT = "2026-06-12T08:00:00+00:00"
EVIDENCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs/qa/product-system-active-path-isolation-v1/mobile_t05b_concurrency_evidence.json"
)


def _completion_event_count(sessions: list[dict], *, employee_id: int) -> int:
    count = 0
    for entry in sessions:
        try:
            completed_by = int(entry.get("completed_by_employee_id") or 0)
        except (TypeError, ValueError):
            completed_by = 0
        if completed_by == employee_id and entry.get("ended_at"):
            count += 1
    return count


async def _ensure_gate_employee_link() -> dict:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        result = await db.execute(
            select(Employees).where(Employees.user_id == SYNTHETIC_DEV_ADMIN_USER_ID)
        )
        employee = result.scalar_one_or_none()
        if employee is None:
            employee = (
                await db.execute(select(Employees).order_by(Employees.id.asc()).limit(1))
            ).scalar_one()
            prior_user_id = employee.user_id
            employee.user_id = SYNTHETIC_DEV_ADMIN_USER_ID
            await db.commit()
        else:
            prior_user_id = employee.user_id
        return {
            "employee_id": employee.id,
            "employee_name": employee.name,
            "prior_user_id": prior_user_id,
            "linked_user_id": SYNTHETIC_DEV_ADMIN_USER_ID,
        }


async def _seed_isolated_fixture(employee_id: int) -> dict:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        await db.execute(delete(ExecutionReality).where(ExecutionReality.order_id == FIXTURE_ORDER_ID))
        await db.execute(delete(ExecutionPlan).where(ExecutionPlan.order_id == FIXTURE_ORDER_ID))

        plan_task = {
            "task_id": FIXTURE_TASK_ID,
            "name": "MOBILE-T05B Concurrency Probe",
            "display_name": "T05B Probe",
            "process_id": "print",
            "process_type": "print",
            "machine_type": "printer_large_format",
            "estimated_time_minutes": 15,
            "assigned_employee_id": employee_id,
        }
        db.add(
            ExecutionPlan(
                order_id=FIXTURE_ORDER_ID,
                order_code=f"ORD-{FIXTURE_ORDER_ID:05d}",
                snapshot_version=1,
                tasks_json=json.dumps([plan_task]),
                total_estimated_time_minutes=15,
            )
        )
        reality_entry = {
            "task_id": FIXTURE_TASK_ID,
            "employee_id": employee_id,
            "employee_name": "T05B Probe Worker",
            "operator_name": "T05B Probe Worker",
            "started_at": FIXTURE_STARTED_AT,
        }
        db.add(
            ExecutionReality(
                order_id=FIXTURE_ORDER_ID,
                order_code=f"ORD-{FIXTURE_ORDER_ID:05d}",
                tasks_json=json.dumps([reality_entry]),
                total_actual_time_minutes=0.0,
            )
        )
        await db.commit()
    return {
        "order_id": FIXTURE_ORDER_ID,
        "task_id": FIXTURE_TASK_ID,
        "employee_id": employee_id,
    }


async def _read_session_state(employee_id: int) -> dict:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        row = (
            await db.execute(
                select(ExecutionReality).where(ExecutionReality.order_id == FIXTURE_ORDER_ID)
            )
        ).scalar_one()
        plan = (
            await db.execute(
                select(ExecutionPlan).where(ExecutionPlan.order_id == FIXTURE_ORDER_ID)
            )
        ).scalar_one()
        sessions = sessions_for_task(json.loads(row.tasks_json or "[]"), FIXTURE_TASK_ID)
        return {
            "closed_sessions": sum(1 for s in sessions if s.get("ended_at")),
            "active_sessions": sum(1 for s in sessions if is_session_active(s)),
            "completion_events": _completion_event_count(sessions, employee_id=employee_id),
            "task_status": derive_task_status_for_employee(sessions, employee_id),
            "plan_tasks_json_hash": hash(plan.tasks_json or ""),
            "plan_snapshot_version": plan.snapshot_version,
        }


async def run_probe() -> dict:
    evidence: dict = {
        "task": "MOBILE-T05B",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backend_url": BASE_URL,
        "classification": "CONCURRENT_COMPLETE_IDEMPOTENT",
        "checks": {},
    }
    failed: list[str] = []

    link = await _ensure_gate_employee_link()
    evidence["employee_link"] = link
    fixture = await _seed_isolated_fixture(link["employee_id"])
    evidence["fixture"] = fixture
    evidence["checks"]["before"] = await _read_session_state(link["employee_id"])

    barrier = asyncio.Barrier(2)
    started: list[float] = []
    responses: list[dict] = []

    async with httpx.AsyncClient(base_url=BASE_URL, headers=DEV_HEADERS, timeout=30.0) as client:

        async def _complete_once():
            await barrier.wait()
            started.append(time.perf_counter())
            resp = await client.patch(
                f"/api/v1/employee-mobile/tasks/{FIXTURE_TASK_ID}/complete",
                json={"order_id": FIXTURE_ORDER_ID},
            )
            return {
                "status_code": resp.status_code,
                "body": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }

        r1, r2 = await asyncio.gather(_complete_once(), _complete_once())
        responses.extend([r1, r2])

        truth = await client.get("/api/v1/employee-mobile/tasks/truth")
        listed = await client.get("/api/v1/employee-mobile/tasks")

    evidence["concurrent"] = {
        "overlap_seconds": max(started) - min(started) if started else None,
        "responses": responses,
    }
    evidence["checks"]["after"] = await _read_session_state(link["employee_id"])
    evidence["truth_status"] = truth.status_code
    evidence["list_status"] = listed.status_code

    after = evidence["checks"]["after"]
    before = evidence["checks"]["before"]

    if not (started and max(started) - min(started) < 0.5):
        failed.append("concurrent_overlap_not_proven")
    if any(r["status_code"] >= 500 for r in responses):
        failed.append("server_error_on_complete")
    if not all(r["status_code"] == 200 for r in responses):
        failed.append("non_200_complete_response")
    if after["closed_sessions"] != 1:
        failed.append(f"closed_sessions={after['closed_sessions']}")
    if after["active_sessions"] != 0:
        failed.append(f"active_sessions={after['active_sessions']}")
    if after["completion_events"] != 1:
        failed.append(f"completion_events={after['completion_events']}")
    if after["task_status"] != "done":
        failed.append(f"task_status={after['task_status']}")
    if after["plan_tasks_json_hash"] != before["plan_tasks_json_hash"]:
        failed.append("plan_tasks_json_mutated")
    if after["plan_snapshot_version"] != before["plan_snapshot_version"]:
        failed.append("plan_snapshot_version_mutated")
    if truth.status_code != 200:
        failed.append(f"truth_status={truth.status_code}")

    evidence["pass"] = len(failed) == 0
    evidence["failures"] = failed
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="MOBILE-T05B concurrent Complete live probe")
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()

    evidence = asyncio.run(run_probe())
    print(json.dumps(evidence, indent=2, default=str))
    if args.write_evidence:
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
        print(f"Wrote {EVIDENCE_PATH}")
    return 0 if evidence.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
