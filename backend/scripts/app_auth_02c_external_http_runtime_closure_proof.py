"""APP-AUTH-02C — external HTTP runtime closure for available projection (:8001)."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET_KEY", "local-dev-secret-not-for-production")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_BACKEND_ROOT}/dev.db"

import httpx
from core.auth import create_access_token
from fastapi import HTTPException
from models.employees import Employees
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from sqlalchemy import delete, select

from core.database import db_manager
from services.employee_mobile_tasks_service import list_my_tasks
from services.operational_registry_service import OperationalRegistryService
from tests.test_execution_plan_v2_frozen_task_identity import _seed_v2_order_with_snapshot

BASE_URL = os.environ.get("WORKOS_GATE_BACKEND_URL", "http://127.0.0.1:8001")
EVIDENCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs/qa/product-system-active-path-isolation-v1/app_auth_02c_external_http_evidence.json"
)
LOG_DIR = Path(_BACKEND_ROOT) / "logs"
TASK_ID = "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep"


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
        code=f"QT-A02C-{order_id}",
        intake_code=f"IR-A02C-{order_id}",
        client_name="A02C Valid",
        status="accepted",
        version=1,
    )
    db.add(quote)
    await db.flush()
    envelope = {
        "source": "order_snapshot_v2",
        "planned_tasks": [{"task_key": "vector_prep", "label": "Vector Prep"}],
        "execution_tasks_created": True,
        "operational_tasks": [
            {
                "task_id": TASK_ID,
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
            code=f"ORD-A02C-{order_id}",
            quote_id=quote.id,
            quote_code=quote.code,
            client_name="A02C Valid",
            status="in_production",
        )
    )
    db.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-A02C-{order_id}",
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
    order = (await db.execute(select(Orders).where(Orders.id == order_id))).scalar_one()
    order.status = "in_production"
    db.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-A02C-C-{order_id}",
            snapshot_version=1,
            tasks_json=json.dumps(
                [
                    {
                        "task_id": "T-A02C-CORRUPT",
                        "name": "Corrupt print",
                        "process_type": "print",
                        "process_id": "print",
                        "machine_type": "PRINTER",
                        "estimated_time_minutes": 1,
                        "assigned_employee_id": None,
                    }
                ]
            ),
            total_estimated_time_minutes=1,
        )
    )


async def _seed_assigned_corrupt_order(db, *, order_id: int, employee_id: int) -> None:
    await _seed_v2_order_with_snapshot(
        db,
        order_id=order_id,
        snapshot_v2_json="{not-valid-json",
    )
    db.add(
        ExecutionPlan(
            order_id=order_id,
            order_code=f"ORD-A02C-OWN-{order_id}",
            snapshot_version=1,
            tasks_json=json.dumps(
                [
                    {
                        "task_id": "T-A02C-OWN-CORRUPT",
                        "name": "Owned corrupt",
                        "process_type": "print",
                        "process_id": "print",
                        "machine_type": "PRINTER",
                        "estimated_time_minutes": 1,
                        "assigned_employee_id": employee_id,
                    }
                ]
            ),
            total_estimated_time_minutes=1,
        )
    )


async def _cleanup(
    db,
    *,
    order_ids: list[int],
    employee_id: int,
) -> None:
    from models.quote_snapshot_v2 import QuoteSnapshotV2Record

    for order_id in order_ids:
        order = (await db.execute(select(Orders).where(Orders.id == order_id))).scalar_one_or_none()
        qsn_id = order.quote_snapshot_v2_id if order else None
        await db.execute(delete(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
        await db.execute(delete(Orders).where(Orders.id == order_id))
        await db.execute(delete(Quotes).where(Quotes.code.like(f"%{order_id}%")))
        if qsn_id is not None:
            await db.execute(delete(QuoteSnapshotV2Record).where(QuoteSnapshotV2Record.id == qsn_id))
    emp = await db.get(Employees, employee_id)
    if emp is not None:
        await db.delete(emp)
    await db.commit()


def _latest_log_file() -> Path | None:
    if not LOG_DIR.is_dir():
        return None
    files = sorted(LOG_DIR.glob("app_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _scan_log_for_exclusion(*, order_id: int, since_pos: int, log_path: Path | None) -> dict:
    """Search recent backend log files for order-local exclusion warning."""
    if not LOG_DIR.is_dir():
        return {"found": False, "reason": "log_dir_missing"}

    needle = f"order_id={order_id}"
    warning_prefix = "employee_mobile available projection excluded order"
    matches: list[str] = []
    scanned: list[str] = []

    for candidate in sorted(LOG_DIR.glob("app_*.log"), key=lambda p: p.stat().st_mtime, reverse=True):
        scanned.append(str(candidate))
        text = candidate.read_text(encoding="utf-8", errors="replace")
        # Prefer tail after probe start when the same file was active at start.
        if log_path is not None and candidate.resolve() == log_path.resolve():
            text = text[since_pos:] if since_pos <= len(text) else text
        for line in text.splitlines():
            if warning_prefix in line and needle in line:
                matches.append(line.strip())
        if matches:
            return {
                "found": True,
                "log_file": str(candidate),
                "matched_lines": matches[-3:],
                "has_corrupt_code_nearby": any(
                    "ORDER_SNAPSHOT_V2_CORRUPT" in line or "ORDER_SNAPSHOT_V2_MISSING" in line
                    for line in matches
                ),
                "scanned_files": scanned[:5],
            }

    return {
        "found": False,
        "log_file": str(log_path) if log_path else None,
        "has_corrupt_code_nearby": False,
        "scanned_files": scanned[:5],
    }


async def _assigned_strict_check(db, employee_id: int, owned_order_id: int) -> dict:
    try:
        await list_my_tasks(db, employee_id)
        return {"pass": False, "reason": "expected_fail_closed_but_succeeded"}
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        return {
            "pass": exc.status_code == 422 and detail.get("error") in {
                "ORDER_SNAPSHOT_V2_CORRUPT",
                "ORDER_SNAPSHOT_V2_MISSING",
            },
            "status_code": exc.status_code,
            "error": detail.get("error"),
            "order_id": detail.get("order_id"),
        }


async def main() -> int:
    suffix = uuid.uuid4().hex[:6]
    user_id = f"a02c-proof-{suffix}"
    valid_order_id = 94000 + int(suffix, 16) % 1000
    corrupt_order_id = 95000 + int(suffix, 16) % 1000
    owned_corrupt_order_id = 96000 + int(suffix, 16) % 1000
    employee_id = 0

    log_path = _latest_log_file()
    log_pos = log_path.stat().st_size if log_path else 0

    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        emp = await _seed_employee(db, user_id=user_id, name=f"A02C Proof {suffix}")
        employee_id = emp.id
        await _seed_print_eligibility(db, employee_id)
        await _seed_valid_order(db, order_id=valid_order_id)
        await _seed_corrupt_order(db, order_id=corrupt_order_id)
        await _seed_assigned_corrupt_order(
            db,
            order_id=owned_corrupt_order_id,
            employee_id=employee_id,
        )
        await db.commit()

    evidence: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": "APP-AUTH-02C",
        "base_url": BASE_URL,
        "authentication_method": "signed_jwt_bearer",
        "jwt_algorithm_present_in_probe_env": bool(os.environ.get("JWT_ALGORITHM")),
        "valid_order_id": valid_order_id,
        "corrupt_order_id": corrupt_order_id,
        "owned_corrupt_order_id": owned_corrupt_order_id,
        "employee_id": employee_id,
        "user_id": user_id,
    }

    try:
        headers = _auth_headers(user_id)
        async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
            resp = await client.get("/api/v1/employee-mobile/tasks/available")
            evidence["http_status"] = resp.status_code
            evidence["request"] = {
                "method": "GET",
                "url": f"{BASE_URL}/api/v1/employee-mobile/tasks/available",
            }
            if resp.status_code != 200:
                evidence["response_text"] = resp.text[:800]
                evidence["verdict"] = "FAIL"
                print(json.dumps(evidence, indent=2))
                return 1

            rows = resp.json()
            valid_rows = [r for r in rows if r.get("order_id") == valid_order_id]
            corrupt_rows = [r for r in rows if r.get("order_id") == corrupt_order_id]
            owned_rows = [r for r in rows if r.get("order_id") == owned_corrupt_order_id]

            evidence["valid_visible"] = len(valid_rows) == 1 and valid_rows[0].get("task_id") == TASK_ID
            evidence["valid_row"] = valid_rows[0] if valid_rows else None
            evidence["corrupt_excluded"] = len(corrupt_rows) == 0
            evidence["owned_corrupt_not_in_available"] = len(owned_rows) == 0
            evidence["readiness_fields_present"] = bool(
                valid_rows
                and any(k in valid_rows[0] for k in ("is_startable", "readiness_status", "can_claim"))
            )

        async with db_manager.async_session_maker() as db:
            evidence["assigned_strict"] = await _assigned_strict_check(
                db,
                employee_id,
                owned_corrupt_order_id,
            )

        log_path = _latest_log_file()
        evidence["warning_log"] = _scan_log_for_exclusion(
            order_id=corrupt_order_id,
            since_pos=log_pos,
            log_path=log_path,
        )
    finally:
        async with db_manager.async_session_maker() as db:
            await _cleanup(
                db,
                order_ids=[valid_order_id, corrupt_order_id, owned_corrupt_order_id],
                employee_id=employee_id,
            )

    passed = all(
        [
            evidence.get("http_status") == 200,
            evidence.get("valid_visible"),
            evidence.get("corrupt_excluded"),
            evidence.get("owned_corrupt_not_in_available"),
            evidence.get("warning_log", {}).get("found"),
            evidence.get("assigned_strict", {}).get("pass"),
        ]
    )
    evidence["verdict"] = "PASS" if passed else "FAIL"
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
