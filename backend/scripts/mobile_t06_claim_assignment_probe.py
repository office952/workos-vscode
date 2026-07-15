"""MOBILE-T06 — live claim / assignment policy probe against :8001."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
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
from models.orders import Orders
from models.quotes import Quotes
from services.operational_registry_service import OperationalRegistryService
from services.task_work_session_service import is_session_active, sessions_for_task
from sqlalchemy import delete, select

from core.database import db_manager

BASE_URL = "http://127.0.0.1:8001"
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
FIXTURE_ORDER_ID = 92400
FIXTURE_TASK_ID = "T-M06-CLAIM-POLICY"
EVIDENCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs/qa/product-system-active-path-isolation-v1/mobile_t06_claim_assignment_evidence.json"
)


async def _ensure_gate_employee_link() -> dict:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        employee = (
            await db.execute(
                select(Employees).where(Employees.user_id == SYNTHETIC_DEV_ADMIN_USER_ID)
            )
        ).scalar_one_or_none()
        if employee is None:
            raise RuntimeError("gate employee missing")
        return {"employee_id": employee.id, "employee_name": employee.name}


async def _seed_unassigned_fixture(employee_id: int) -> dict:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        await db.execute(delete(ExecutionReality).where(ExecutionReality.order_id == FIXTURE_ORDER_ID))
        await db.execute(delete(ExecutionPlan).where(ExecutionPlan.order_id == FIXTURE_ORDER_ID))
        existing_order = await db.get(Orders, FIXTURE_ORDER_ID)
        if existing_order is None:
            quote = Quotes(
                code=f"QT-{FIXTURE_ORDER_ID:05d}",
                intake_code=f"IR-{FIXTURE_ORDER_ID:05d}",
                client_name="T06 Probe",
                status="accepted",
                version=1,
            )
            db.add(quote)
            await db.flush()
            db.add(
                Orders(
                    id=FIXTURE_ORDER_ID,
                    code=f"ORD-{FIXTURE_ORDER_ID:05d}",
                    quote_id=quote.id,
                    quote_code=quote.code,
                    client_name="T06 Probe",
                    status="in_production",
                )
            )
        registry = OperationalRegistryService(db)
        await registry.set_employee_authorizations(
            employee_id,
            skill_codes=["SK_PRINT_OPERATOR"],
            workcenter_codes=["WC_PRINT"],
            resource_codes=["MCH-EPSON-60800"],
        )
        await registry.upsert_operation_mapping(
            {
                "operation_code": "print",
                "required_skill_codes": ["SK_PRINT_OPERATOR"],
                "allowed_workcenter_codes": ["WC_PRINT"],
                "allowed_resource_codes": ["MCH-EPSON-60800"],
                "authorization_mode": "hybrid",
                "authorized_employee_ids": [employee_id],
            }
        )
        task = {
            "task_id": FIXTURE_TASK_ID,
            "name": "MOBILE-T06 Claim Probe",
            "display_name": "T06 Claim Probe",
            "process_id": "print",
            "process_type": "print",
            "machine_type": "printer_large_format",
            "estimated_time_minutes": 15,
        }
        db.add(
            ExecutionPlan(
                order_id=FIXTURE_ORDER_ID,
                order_code=f"ORD-{FIXTURE_ORDER_ID:05d}",
                snapshot_version=1,
                tasks_json=json.dumps([task]),
                total_estimated_time_minutes=15,
            )
        )
        await db.commit()
    return {"order_id": FIXTURE_ORDER_ID, "task_id": FIXTURE_TASK_ID, "employee_id": employee_id}


async def _plan_assignee() -> int | None:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        plan = (
            await db.execute(
                select(ExecutionPlan).where(ExecutionPlan.order_id == FIXTURE_ORDER_ID)
            )
        ).scalar_one()
        tasks = json.loads(plan.tasks_json or "[]")
        match = next((t for t in tasks if t.get("task_id") == FIXTURE_TASK_ID), None)
        raw = match.get("assigned_employee_id") if match else None
        return int(raw) if raw is not None else None


async def _active_sessions() -> int:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        row = (
            await db.execute(
                select(ExecutionReality).where(ExecutionReality.order_id == FIXTURE_ORDER_ID)
            )
        ).scalar_one_or_none()
        if row is None:
            return 0
        sessions = sessions_for_task(json.loads(row.tasks_json or "[]"), FIXTURE_TASK_ID)
        return sum(1 for s in sessions if is_session_active(s))


async def run_probe() -> dict:
    evidence: dict = {
        "task": "MOBILE-T06",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backend_url": BASE_URL,
        "checks": {},
    }
    failed: list[str] = []
    link = await _ensure_gate_employee_link()
    evidence["employee_link"] = link
    evidence["fixture"] = await _seed_unassigned_fixture(link["employee_id"])

    async with httpx.AsyncClient(base_url=BASE_URL, headers=DEV_HEADERS, timeout=30.0) as client:
        avail = await client.get("/api/v1/employee-mobile/tasks/available")
        claim = await client.post(
            f"/api/v1/employee-mobile/tasks/{FIXTURE_TASK_ID}/claim",
            json={"order_id": FIXTURE_ORDER_ID},
        )
        my_tasks = await client.get("/api/v1/employee-mobile/tasks")
        evidence["checks"]["claim_only"] = {
            "available_status": avail.status_code,
            "claim_status": claim.status_code,
            "claim_body": claim.json() if claim.headers.get("content-type", "").startswith("application/json") else claim.text,
            "my_tasks_status": my_tasks.status_code,
        }

        assignee = await _plan_assignee()
        sessions = await _active_sessions()
        evidence["checks"]["post_claim"] = {
            "assigned_employee_id": assignee,
            "active_sessions": sessions,
        }

        if claim.status_code != 200:
            failed.append(f"claim_status={claim.status_code}")
        if assignee != link["employee_id"]:
            failed.append("claim_did_not_assign")
        if sessions != 0:
            failed.append("claim_started_session")

        # Reset fixture for start-from-available
        await _seed_unassigned_fixture(link["employee_id"])
        start = await client.post(
            f"/api/v1/employee-mobile/tasks/{FIXTURE_TASK_ID}/start-from-available",
            json={"order_id": FIXTURE_ORDER_ID},
        )
        assignee2 = await _plan_assignee()
        sessions2 = await _active_sessions()
        evidence["checks"]["start_from_available"] = {
            "status": start.status_code,
            "body": start.json() if start.headers.get("content-type", "").startswith("application/json") else start.text,
            "assigned_employee_id": assignee2,
            "active_sessions": sessions2,
        }
        if start.status_code != 200:
            failed.append(f"start_from_available={start.status_code}")
        if assignee2 != link["employee_id"]:
            failed.append("start_did_not_assign")
        if sessions2 != 1:
            failed.append(f"start_sessions={sessions2}")

    evidence["pass"] = len(failed) == 0
    evidence["failures"] = failed
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()
    evidence = asyncio.run(run_probe())
    print(json.dumps(evidence, indent=2, default=str))
    if args.write_evidence:
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    return 0 if evidence.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
