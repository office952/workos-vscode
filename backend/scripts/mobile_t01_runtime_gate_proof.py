"""MOBILE-T01 — canonical mobile task read model runtime gate proof."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

import httpx
from dependencies.auth import SYNTHETIC_DEV_ADMIN_USER_ID
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from services.execution_plan_task_parser import parse_tasks_json_raw
from sqlalchemy import select

from core.database import db_manager

BASE_URL = "http://127.0.0.1:8001"
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
ALLOWED_ORDER_ID = 23099
GATE_EMPLOYEE_ID = 4
GATE_EMPLOYEE_NAME = "Putaru Sandu"
EVIDENCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs/qa/product-system-active-path-isolation-v1/mobile_t01_gate_evidence.json"
)


async def _ensure_gate_employee_link() -> dict:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        employee = await db.get(Employees, GATE_EMPLOYEE_ID)
        if employee is None:
            raise RuntimeError(f"employee_id={GATE_EMPLOYEE_ID} missing from dev.db")
        prior_user_id = employee.user_id
        employee.user_id = SYNTHETIC_DEV_ADMIN_USER_ID
        await db.commit()
        return {
            "employee_id": employee.id,
            "employee_name": employee.name,
            "prior_user_id": prior_user_id,
            "linked_user_id": SYNTHETIC_DEV_ADMIN_USER_ID,
        }


async def _plan_operational_count(order_id: int) -> dict:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        plan = (
            await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
        ).scalar_one_or_none()
        if plan is None:
            return {"order_id": order_id, "error": "execution_plan_missing"}
        parsed = parse_tasks_json_raw(plan.tasks_json)
        operational = list(parsed.operational_tasks)
        return {
            "order_id": order_id,
            "format": parsed.format,
            "operational_count": len(operational),
            "sample_task_ids": [str(t.get("task_id")) for t in operational[:5]],
        }


async def _assign_sample_tasks(order_id: int, employee_id: int, count: int = 2) -> dict:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        plan = (
            await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
        ).scalar_one_or_none()
        if plan is None:
            return {"order_id": order_id, "assigned": [], "error": "execution_plan_missing"}
        parsed = parse_tasks_json_raw(plan.tasks_json)
        assigned: list[str] = []
        if parsed.format == "v2_envelope" and parsed.envelope is not None:
            operational = parsed.operational_tasks
            for idx, task in enumerate(operational):
                task_id = str(task.get("task_id") or "")
                if task_id and idx < count:
                    task["assigned_employee_id"] = employee_id
                    assigned.append(task_id)
            envelope = dict(parsed.envelope)
            envelope["operational_tasks"] = operational
            plan.tasks_json = json.dumps(envelope)
            await db.commit()
        return {"order_id": order_id, "assigned": assigned, "mutation": "plan_assignment_only"}


async def run_gate(*, assign_tasks: bool) -> dict:
    evidence: dict = {
        "task": "MOBILE-T01",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "backend_url": BASE_URL,
        "order_id": ALLOWED_ORDER_ID,
        "employee_id": GATE_EMPLOYEE_ID,
        "checks": {},
    }
    failed: list[str] = []

    link = await _ensure_gate_employee_link()
    evidence["employee_link"] = link
    evidence["checks"]["plan_operational_count"] = await _plan_operational_count(ALLOWED_ORDER_ID)

    if assign_tasks:
        evidence["assignment"] = await _assign_sample_tasks(ALLOWED_ORDER_ID, GATE_EMPLOYEE_ID)

    async with httpx.AsyncClient(base_url=BASE_URL, headers=DEV_HEADERS, timeout=30.0) as client:
        assigned_resp = await client.get("/api/v1/employee-mobile/tasks")
        available_resp = await client.get("/api/v1/employee-mobile/tasks/available")
        truth_resp = await client.get("/api/v1/employee-mobile/tasks/truth")

        evidence["checks"]["assigned_tasks"] = {
            "status_code": assigned_resp.status_code,
            "count": len(assigned_resp.json()) if assigned_resp.status_code == 200 else 0,
            "sample": assigned_resp.json()[:2] if assigned_resp.status_code == 200 else assigned_resp.text,
        }
        evidence["checks"]["available_tasks"] = {
            "status_code": available_resp.status_code,
            "count": len(available_resp.json()) if available_resp.status_code == 200 else 0,
        }
        evidence["checks"]["task_truth"] = {
            "status_code": truth_resp.status_code,
            "contract_version": truth_resp.json().get("contract_version")
            if truth_resp.status_code == 200
            else None,
            "total_tasks": truth_resp.json().get("summary", {}).get("total_tasks")
            if truth_resp.status_code == 200
            else 0,
        }

        if assigned_resp.status_code != 200:
            failed.append("assigned_tasks_http")
        elif evidence["checks"]["assigned_tasks"]["count"] == 0 and assign_tasks:
            failed.append("assigned_tasks_empty_after_assignment")

        plan_count = evidence["checks"]["plan_operational_count"].get("operational_count", 0)
        if plan_count < 13:
            failed.append("plan_operational_count_below_13")

        if available_resp.status_code != 200:
            failed.append("available_tasks_http")
        elif assign_tasks and evidence["checks"]["available_tasks"]["count"] == 0:
            failed.append("available_tasks_empty")

        if truth_resp.status_code != 200:
            failed.append("task_truth_http")
        elif truth_resp.json().get("contract_version") != "employee_mobile_task_truth/v1":
            failed.append("task_truth_contract")

        if assigned_resp.status_code == 200 and assigned_resp.json():
            sample = assigned_resp.json()[0]
            evidence["checks"]["identity_sample"] = {
                "task_id": sample.get("task_id"),
                "deterministic_task_key": sample.get("deterministic_task_key"),
                "identity_source": sample.get("identity_source"),
                "component_role": sample.get("component_role"),
                "logo_segment_label": sample.get("logo_segment_label"),
                "contract_version": sample.get("contract_version"),
                "legacy_mode": sample.get("legacy_mode"),
            }
            if not sample.get("deterministic_task_key"):
                failed.append("identity_missing_deterministic_key")
            if sample.get("identity_source") != "frozen_task_identity/v1":
                failed.append("identity_source_not_frozen")

    evidence["verdict"] = "PASS" if not failed else "FAIL"
    evidence["failed_checks"] = failed
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assign-tasks", action="store_true")
    args = parser.parse_args()
    evidence = asyncio.run(run_gate(assign_tasks=args.assign_tasks))
    print(json.dumps(evidence, indent=2))
    return 0 if evidence.get("verdict") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
