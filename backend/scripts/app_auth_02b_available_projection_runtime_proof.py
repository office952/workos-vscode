"""APP-AUTH-02B — available projection order-local fail-closed runtime proof (:8001)."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

import httpx
from core.auth import create_access_token
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from sqlalchemy import delete, select

from core.database import db_manager
from services.operational_registry_service import OperationalRegistryService
from tests.test_execution_plan_v2_frozen_task_identity import _seed_v2_order_with_snapshot

BASE_URL = "http://127.0.0.1:8001"


def _auth_headers(user_id: str) -> dict[str, str]:
    token = create_access_token(
        {
            "sub": user_id,
            "email": f"{user_id}@workos.test",
            "name": user_id,
            "role": "employee_mobile",
        }
    )
    return {
        "Authorization": f"Bearer {token}",
        "Origin": "http://127.0.0.1:3000",
    }


async def _seed_employee(db, *, user_id: str, name: str) -> Employees:
    emp = Employees(
        user_id=user_id,
        name=name,
        status="active",
        employee_type="productive",
    )
    db.add(emp)
    await db.flush()
    return emp


async def _seed_print_eligibility(db, employee_id: int) -> None:
    svc = OperationalRegistryService(db)
    await svc.set_employee_authorizations(
        employee_id,
        skill_codes=["SK_PRINT_OPERATOR"],
        workcenter_codes=["WC_PRINT"],
        resource_codes=["MCH-EPSON-60800"],
    )
    await svc.upsert_operation_mapping(
        {
            "operation_code": "print",
            "required_skill_codes": ["SK_PRINT_OPERATOR"],
            "allowed_workcenter_codes": ["WC_PRINT"],
            "allowed_resource_codes": ["MCH-EPSON-60800"],
            "authorization_mode": "hybrid",
            "authorized_employee_ids": [employee_id],
        }
    )


async def _seed_valid_order(db, *, order_id: int) -> None:
    quote = Quotes(
        code=f"QT-A02B-{order_id}",
        intake_code=f"IR-A02B-{order_id}",
        client_name="A02B Valid",
        status="accepted",
        version=1,
    )
    db.add(quote)
    await db.flush()
    task_id = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep"
    envelope = {
        "source": "order_snapshot_v2",
        "planned_tasks": [{"task_key": "vector_prep", "label": "Vector Prep"}],
        "execution_tasks_created": True,
        "operational_tasks": [
            {
                "task_id": task_id,
                "display_name": "Print",
                "process_type": "print",
                "process_id": "print",
                "machine_type": "PRINTER",
                "sequence_index": 0,
            }
        ],
    }
    db.add(
        Orders(
            id=order_id,
            code=f"ORD-A02B-{order_id}",
            quote_id=quote.id,
            quote_code=quote.code,
            client_name="A02B Valid",
            status="in_production",
        )
    )
    db.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-A02B-{order_id}",
            snapshot_version=2,
            tasks_json=json.dumps(envelope),
            total_estimated_time_minutes=60,
        )
    )


async def _seed_corrupt_order(db, *, order_id: int) -> None:
    await _seed_v2_order_with_snapshot(
        db,
        order_id=order_id,
        snapshot_v2_json="{not-valid-json",
    )
    db.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-A02B-C-{order_id}",
            snapshot_version=1,
            tasks_json=json.dumps(
                [
                    {
                        "task_id": "T-A02B-CORRUPT",
                        "name": "Corrupt print",
                        "process_type": "print",
                        "process_id": "print",
                        "machine_type": "PRINTER",
                        "estimated_time_minutes": 1,
                    }
                ]
            ),
            total_estimated_time_minutes=1,
        )
    )


async def _cleanup(db, *, order_ids: list[int], employee_id: int, user_id: str) -> None:
    from models.quote_snapshot_v2 import QuoteSnapshotV2Record

    for order_id in order_ids:
        order = (await db.execute(select(Orders).where(Orders.id == order_id))).scalar_one_or_none()
        qsn_id = order.quote_snapshot_v2_id if order else None
        await db.execute(delete(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
        await db.execute(delete(Orders).where(Orders.id == order_id))
        await db.execute(delete(Quotes).where(Quotes.code.like(f"%{order_id}%")))
        if qsn_id is not None:
            await db.execute(delete(QuoteSnapshotV2Record).where(QuoteSnapshotV2Record.id == qsn_id))
    emp = (await db.execute(select(Employees).where(Employees.id == employee_id))).scalar_one_or_none()
    if emp is not None:
        await db.delete(emp)
    await db.commit()


async def main() -> int:
    suffix = uuid.uuid4().hex[:6]
    user_id = f"a02b-proof-{suffix}"
    valid_order_id = 92000 + int(suffix, 16) % 1000
    corrupt_order_id = 93000 + int(suffix, 16) % 1000
    task_id = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep"
    employee_id = 0

    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        emp = await _seed_employee(db, user_id=user_id, name=f"A02B Proof {suffix}")
        employee_id = emp.id
        await _seed_print_eligibility(db, employee_id)
        await _seed_valid_order(db, order_id=valid_order_id)
        await _seed_corrupt_order(db, order_id=corrupt_order_id)
        await db.commit()

    evidence: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "valid_order_id": valid_order_id,
        "corrupt_order_id": corrupt_order_id,
        "employee_id": employee_id,
    }

    try:
        headers = _auth_headers(user_id)
        async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
            resp = await client.get("/api/v1/employee-mobile/tasks/available")
            evidence["http_status"] = resp.status_code
            evidence["response_ok"] = resp.status_code == 200
            if resp.status_code != 200:
                evidence["response_text"] = resp.text[:500]
                print(json.dumps(evidence, indent=2))
                return 1
            rows = resp.json()
            valid_rows = [r for r in rows if r.get("order_id") == valid_order_id]
            corrupt_rows = [r for r in rows if r.get("order_id") == corrupt_order_id]
            evidence["valid_visible"] = len(valid_rows) == 1 and valid_rows[0].get("task_id") == task_id
            evidence["corrupt_excluded"] = len(corrupt_rows) == 0
            evidence["valid_count"] = len(valid_rows)
            evidence["corrupt_count"] = len(corrupt_rows)
    finally:
        async with db_manager.async_session_maker() as db:
            await _cleanup(
                db,
                order_ids=[valid_order_id, corrupt_order_id],
                employee_id=employee_id,
                user_id=user_id,
            )

    passed = (
        evidence.get("response_ok")
        and evidence.get("valid_visible")
        and evidence.get("corrupt_excluded")
    )
    evidence["verdict"] = "PASS" if passed else "FAIL"
    print(json.dumps(evidence, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
