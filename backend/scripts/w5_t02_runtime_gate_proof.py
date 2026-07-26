"""W5-T02 frozen task identity runtime proof against trusted :8001 backend."""
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
from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview
from tests.test_execution_plan_v2_frozen_task_identity import (
    IDENTITY_OID_BASE,
    MOUNTING_NODE,
    ROOT_NODE,
    _build_identity_snapshot,
    _identity_aggregate,
)

BASE = "http://127.0.0.1:8001"
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
GATE_ORDER_ID = IDENTITY_OID_BASE + 99
OUT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "qa"
    / "product-system-active-path-isolation-v1"
    / "w5_t02_runtime_gate_evidence.json"
)


async def _seed_gate_fixture() -> dict:
    await db_manager.ensure_initialized()
    aggregate = _identity_aggregate(include_mounting=True)
    snapshot_json = _build_identity_snapshot(aggregate)
    async with db_manager.async_session_maker() as db:
        existing = await db.get(Orders, GATE_ORDER_ID)
        if existing is None:
            db.add(
                Orders(
                    id=GATE_ORDER_ID,
                    code="ORD-W5T02-GATE",
                    quote_id=GATE_ORDER_ID,
                    quote_code="QT-W5T02-GATE",
                    client_name="W5T02 Gate Fixture",
                    status="locked",
                    total_amount=1500.0,
                    quote_snapshot_v2_id=GATE_ORDER_ID,
                    snapshot_v2_json=snapshot_json,
                    readiness_snapshot={"source": "w5_t02_runtime_gate_fixture"},
                )
            )
        else:
            existing.snapshot_v2_json = snapshot_json
        await db.commit()
        before_hash = hash(snapshot_json)
        preview_one = await build_execution_plan_v2_preview(db, GATE_ORDER_ID)
        preview_two = await build_execution_plan_v2_preview(db, GATE_ORDER_ID)
        keys_one = [t.task_key for t in preview_one.planned_tasks]
        keys_two = [t.task_key for t in preview_two.planned_tasks]
        refreshed = await db.get(Orders, GATE_ORDER_ID)
        return {
            "order_id": GATE_ORDER_ID,
            "snapshot_hash": before_hash,
            "preview_keys_one": keys_one,
            "preview_keys_two": keys_two,
            "mounting_tasks": [
                t.model_dump()
                for t in preview_one.planned_tasks
                if t.frozen_identity
                and t.frozen_identity.source_graph_node_id == MOUNTING_NODE
            ],
            "root_tasks": [
                t.model_dump()
                for t in preview_one.planned_tasks
                if t.frozen_identity
                and t.frozen_identity.source_graph_node_id == ROOT_NODE
            ][:2],
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
        preview_resp = await client.post(
            f"/api/v1/execution/plan-v2/preview/{GATE_ORDER_ID}"
        )
        evidence["steps"]["http_preview"] = {
            "status_code": preview_resp.status_code,
            "body": preview_resp.json() if preview_resp.status_code == 200 else preview_resp.text,
        }

        status_resp = await client.get(
            f"/api/v1/execution/orders/{GATE_ORDER_ID}/production-release-status"
        )
        evidence["steps"]["production_release_status"] = {
            "status_code": status_resp.status_code,
            "body": status_resp.json() if status_resp.status_code == 200 else status_resp.text,
        }

    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        order = await db.get(Orders, GATE_ORDER_ID)
        snapshot = OrderSnapshotV2.model_validate_json(order.snapshot_v2_json or "{}")
        evidence["final_state"] = {
            "snapshot_hash": hash(order.snapshot_v2_json or ""),
            "snapshot_code": snapshot.snapshot_code,
            "content_hash": snapshot.content_hash,
            "snapshot_unchanged": evidence["fixture"]["snapshot_hash"] == hash(order.snapshot_v2_json or ""),
        }

    http_tasks = (evidence["steps"]["http_preview"].get("body") or {}).get("planned_tasks") or []
    http_keys = [t.get("task_key") for t in http_tasks if isinstance(t, dict)]
    mounting_http = [
        t for t in http_tasks
        if isinstance(t, dict)
        and (t.get("frozen_identity") or {}).get("source_graph_node_id") == MOUNTING_NODE
    ]

    checks = {
        "preview_http_ok": evidence["steps"]["http_preview"]["status_code"] == 200,
        "preview_keys_stable": seeded["preview_keys_one"] == seeded["preview_keys_two"],
        "http_keys_match_service": http_keys == seeded["preview_keys_one"],
        "mounting_identity_present": len(mounting_http) >= 2,
        "no_legacy_name_only_keys": all(":" in key for key in http_keys),
        "snapshot_unchanged": evidence["final_state"]["snapshot_unchanged"],
        "release_status_live": evidence["steps"]["production_release_status"]["status_code"] == 200,
    }
    evidence["pass_checks"] = checks
    evidence["pass"] = all(checks.values())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"pass": evidence["pass"], "out": str(OUT), "checks": checks}, indent=2))
    return 0 if evidence["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
