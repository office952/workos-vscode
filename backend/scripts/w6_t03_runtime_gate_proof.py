"""W6-T03 production blocker visibility runtime proof against :8001."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from scripts.w6_t03_blocked_fixture_setup import BLOCKED_ORDER_ID, seed_blocked_fixture

BASE = "http://127.0.0.1:8001"
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
ALLOWED_ORDER_ID = 23099
OUT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "qa"
    / "product-system-active-path-isolation-v1"
    / "w6_t03_runtime_gate_evidence.json"
)


async def main() -> int:
    evidence: dict = {
        "gate": "W6-T03",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE,
        "blocked_order_id": BLOCKED_ORDER_ID,
        "allowed_order_id": ALLOWED_ORDER_ID,
        "db_mutations": ["seed_blocked_fixture_order_23150"],
        "checks": {},
    }

    await seed_blocked_fixture()

    async with httpx.AsyncClient(base_url=BASE, headers=DEV_HEADERS, timeout=30.0) as client:
        blocked = await client.get(f"/api/v1/operator/orders/{BLOCKED_ORDER_ID}/task-truth")
        allowed = await client.get(f"/api/v1/operator/orders/{ALLOWED_ORDER_ID}/task-truth")
        blocked_body = blocked.json() if blocked.status_code == 200 else {"error": blocked.text}
        allowed_body = allowed.json() if allowed.status_code == 200 else {"error": allowed.text}

        blocking = [
            d for d in (blocked_body.get("owner_decisions_summary") or []) if d.get("blocking")
        ]
        nonblocking = [
            d for d in (blocked_body.get("owner_decisions_summary") or []) if not d.get("blocking")
        ]
        sample_task = (blocked_body.get("tasks") or [None])[0] or {}

        evidence["checks"]["blocked_truth"] = {
            "status_code": blocked.status_code,
            "production_release_blocked": blocked_body.get("production_release_blocked"),
            "production_release_status": blocked_body.get("production_release_status"),
            "blocking_count": len(blocking),
            "nonblocking_count": len(nonblocking),
            "task_is_startable": (sample_task.get("runtime") or {}).get("is_startable"),
            "task_production_release_blocked": (sample_task.get("runtime") or {}).get(
                "production_release_blocked"
            ),
        }

        evidence["checks"]["allowed_truth"] = {
            "status_code": allowed.status_code,
            "production_release_blocked": allowed_body.get("production_release_blocked"),
            "production_release_status": allowed_body.get("production_release_status"),
        }

        start_task_id = (sample_task.get("identity") or {}).get("task_id")
        start_probe = {"attempted": False}
        if start_task_id:
            start_probe["attempted"] = True
            start_probe["task_id"] = start_task_id
            start_res = await client.post(
                "/api/v1/execution/reality/start-task",
                json={
                    "order_id": BLOCKED_ORDER_ID,
                    "task_id": start_task_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            start_probe["status_code"] = start_res.status_code
            detail = start_res.json().get("detail") if start_res.content else {}
            start_probe["code"] = (detail or {}).get("code")
            start_probe["blocker_count"] = len((detail or {}).get("blockers") or [])
        evidence["checks"]["structured_start_rejection"] = start_probe

        blocked_again = await client.get(f"/api/v1/operator/orders/{BLOCKED_ORDER_ID}/task-truth")
        evidence["checks"]["refresh_stable"] = {
            "first_blocked": blocked_body.get("production_release_blocked"),
            "second_blocked": (blocked_again.json() if blocked_again.status_code == 200 else {}).get(
                "production_release_blocked"
            ),
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))

    ok = (
        evidence["checks"]["blocked_truth"]["status_code"] == 200
        and evidence["checks"]["blocked_truth"]["production_release_blocked"] is True
        and evidence["checks"]["blocked_truth"]["blocking_count"] >= 3
        and evidence["checks"]["blocked_truth"]["nonblocking_count"] >= 1
        and evidence["checks"]["allowed_truth"]["production_release_blocked"] is False
        and evidence["checks"]["structured_start_rejection"].get("code")
        in {"production_release_blocked", "task_not_ready"}
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
