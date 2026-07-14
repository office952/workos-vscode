"""W5-T01 production release guard runtime proof against trusted :8001 backend."""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

from core.database import db_manager
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.quote_snapshot_v2 import QuoteSnapshotOwnerDecision
from services.execution_owner_decision_production_release_service import (
    OWNER_DECISION_RESOLUTIONS_KEY,
)
from tests.test_execution_plan_v2_preview import (
    _sample_aggregate,
    _sample_product_definition,
)
from tests.test_quote_snapshot_v2_accept_gate import _commercial_preview, _internal_preview

BASE = "http://127.0.0.1:8001"
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
GATE_ORDER_ID = 29991
OUT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "qa"
    / "product-system-active-path-isolation-v1"
    / "w5_t01_runtime_gate_evidence.json"
)


def _build_snapshot_json() -> str:
    decisions = [
        QuoteSnapshotOwnerDecision(
            code="INTERNAL_SABLON_FOREX_COST",
            label="Sablon Forex cost pending",
            source="estimated_internal_cost",
            module_code="sablon_forex",
        ),
        QuoteSnapshotOwnerDecision(
            code="INTERNAL_AMBALARE_RULE",
            label="Ambalare rule pending",
            source="estimated_internal_cost",
            module_code="ambalare",
        ),
    ]
    snapshot = OrderSnapshotV2(
        quote_id=GATE_ORDER_ID,
        quote_snapshot_v2_id=GATE_ORDER_ID,
        snapshot_code="OSN2-W5T01-GATE",
        content_hash="w5t01gatehashw5t01gatehashw5t01ga",
        product_definition_snapshot=_sample_product_definition(),
        product_aggregate_snapshot=_sample_aggregate(include_task_rules=True),
        commercial_price_proposal_snapshot=_commercial_preview(total=1500.0),
        estimated_internal_cost_snapshot=_internal_preview(total=620.0),
        owner_decisions_snapshot=decisions,
        accepted_commercial_total=1500.0,
        accepted_currency="RON",
        estimated_internal_total=620.0,
    )
    return snapshot.model_dump_json()


async def _seed_gate_fixture() -> dict:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        existing = await db.get(Orders, GATE_ORDER_ID)
        snapshot_json = _build_snapshot_json()
        if existing is None:
            order = Orders(
                id=GATE_ORDER_ID,
                code="ORD-W5T01-GATE",
                quote_id=GATE_ORDER_ID,
                quote_code="QT-W5T01-GATE",
                client_name="W5T01 Gate Fixture",
                status="locked",
                total_amount=1500.0,
                quote_snapshot_v2_id=GATE_ORDER_ID,
                snapshot_v2_json=snapshot_json,
                readiness_snapshot={
                    "source": "w5_t01_runtime_gate_fixture",
                    "execution_plan_created": False,
                    "no_execution_plan_created": True,
                },
            )
            db.add(order)
        else:
            existing.snapshot_v2_json = snapshot_json
            existing.readiness_snapshot = {
                "source": "w5_t01_runtime_gate_fixture",
                "execution_plan_created": False,
                "no_execution_plan_created": True,
            }

        plan = (
            await db.execute(
                __import__("sqlalchemy").select(ExecutionPlan).where(
                    ExecutionPlan.order_id == GATE_ORDER_ID
                )
            )
        ).scalar_one_or_none()
        tasks = [
            {
                "task_id": "T-W5T01",
                "task_name": "W5T01 Gate Task",
                "task_type": "assembly",
                "depends_on_task_ids": [],
            }
        ]
        if plan is None:
            db.add(
                ExecutionPlan(
                    order_id=GATE_ORDER_ID,
                    order_code="ORD-W5T01-GATE",
                    snapshot_version=1,
                    tasks_json=json.dumps(tasks),
                    total_estimated_time_minutes=60,
                )
            )
        else:
            plan.tasks_json = json.dumps(tasks)

        await db.commit()
        refreshed = await db.get(Orders, GATE_ORDER_ID)
        return {
            "order_id": GATE_ORDER_ID,
            "snapshot_v2_json_hash": hash(refreshed.snapshot_v2_json or ""),
            "readiness_snapshot": refreshed.readiness_snapshot,
        }


async def main() -> int:
    seeded = await _seed_gate_fixture()
    evidence: dict = {
        "base": BASE,
        "fixture": seeded,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps": {},
    }

    async with httpx.AsyncClient(base_url=BASE, timeout=30.0, headers=DEV_HEADERS) as client:
        status_resp = await client.get(
            f"/api/v1/execution/orders/{GATE_ORDER_ID}/production-release-status"
        )
        evidence["steps"]["production_release_status_before"] = {
            "status_code": status_resp.status_code,
            "body": status_resp.json() if status_resp.status_code == 200 else status_resp.text,
        }

        start_resp = await client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": GATE_ORDER_ID,
                "task_id": "T-W5T01",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        evidence["steps"]["start_blocked"] = {
            "status_code": start_resp.status_code,
            "body": start_resp.json() if start_resp.content else {},
        }

        resolve_resp = await client.post(
            f"/api/v1/execution/orders/{GATE_ORDER_ID}/owner-decisions/INTERNAL_SABLON_FOREX_COST/resolve",
            json={
                "status": "resolved",
                "note": "W5T01 runtime gate — Forex cost owner resolution.",
            },
        )
        evidence["steps"]["resolve_forex"] = {
            "status_code": resolve_resp.status_code,
            "body": resolve_resp.json() if resolve_resp.content else {},
        }

        start_after_resp = await client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": GATE_ORDER_ID,
                "task_id": "T-W5T01",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        evidence["steps"]["start_after_resolve"] = {
            "status_code": start_after_resp.status_code,
            "body": start_after_resp.json() if start_after_resp.content else {},
        }

        status_after_resp = await client.get(
            f"/api/v1/execution/orders/{GATE_ORDER_ID}/production-release-status"
        )
        evidence["steps"]["production_release_status_after"] = {
            "status_code": status_after_resp.status_code,
            "body": status_after_resp.json() if status_after_resp.status_code == 200 else status_after_resp.text,
        }

    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        final_order = await db.get(Orders, GATE_ORDER_ID)
        evidence["final_state"] = {
            "snapshot_v2_json_hash": hash(final_order.snapshot_v2_json or ""),
            "snapshot_unchanged": evidence["fixture"]["snapshot_v2_json_hash"]
            == hash(final_order.snapshot_v2_json or ""),
            "resolution_present": OWNER_DECISION_RESOLUTIONS_KEY
            in (final_order.readiness_snapshot or {}),
            "audit_history_len": len(
                (final_order.readiness_snapshot or {})
                .get(OWNER_DECISION_RESOLUTIONS_KEY, {})
                .get("audit_history", [])
            ),
        }

    checks = {
        "status_endpoint_live": evidence["steps"]["production_release_status_before"]["status_code"] == 200,
        "blocked_before_resolve": evidence["steps"]["start_blocked"]["status_code"] == 409
        and (evidence["steps"]["start_blocked"]["body"].get("detail") or {}).get("code")
        == "production_release_blocked",
        "resolve_ok": evidence["steps"]["resolve_forex"]["status_code"] == 200,
        "start_allowed_after_resolve": evidence["steps"]["start_after_resolve"]["status_code"] == 200,
        "release_allowed_after": (
            evidence["steps"]["production_release_status_after"]["body"].get("release_status")
            == "RELEASE_ALLOWED"
        ),
        "snapshot_unchanged": evidence["final_state"]["snapshot_unchanged"],
        "resolution_separate": evidence["final_state"]["resolution_present"],
        "audit_preserved": evidence["final_state"]["audit_history_len"] >= 1,
    }
    evidence["pass_checks"] = checks
    evidence["pass"] = all(checks.values())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"pass": evidence["pass"], "out": str(OUT), "checks": checks}, indent=2))
    return 0 if evidence["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
