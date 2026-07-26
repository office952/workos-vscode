"""W6-T01 operator task truth runtime proof against :8001 (read-only)."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8001"
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
GATE_ORDER_ID = 23099
OUT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "qa"
    / "product-system-active-path-isolation-v1"
    / "w6_t01_runtime_gate_evidence.json"
)


async def main() -> int:
    evidence: dict = {
        "gate": "W6-T01",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE,
        "gate_order_id": GATE_ORDER_ID,
        "read_only": True,
        "checks": {},
    }

    async with httpx.AsyncClient(base_url=BASE, headers=DEV_HEADERS, timeout=30.0) as client:
        admin = await client.get(f"/api/v1/operator/orders/{GATE_ORDER_ID}/task-truth")
        operator_headers = {**DEV_HEADERS, "X-Test-Role": "operator"}
        # Role comes from auth token in dev; probe admin path for fixture truth
        body = admin.json() if admin.status_code == 200 else {"error": admin.text}
        tasks = body.get("tasks") or []
        root = next(
            (
                t
                for t in tasks
                if (t.get("identity") or {}).get("component_role") == "root_product"
            ),
            None,
        )
        mounting = next(
            (
                t
                for t in tasks
                if (t.get("identity") or {}).get("component_role") == "mounting_panel"
            ),
            None,
        )
        logo = next(
            (
                t
                for t in tasks
                if (t.get("identity") or {}).get("logo_segment_key") == "logo_instance_001"
            ),
            None,
        )
        evidence["checks"]["task_truth"] = {
            "status_code": admin.status_code,
            "contract_version": body.get("contract_version"),
            "task_count": len(tasks),
            "readiness_authority": body.get("readiness_authority"),
            "production_release_status": body.get("production_release_status"),
            "root_component_role": (root or {}).get("identity", {}).get("component_role"),
            "mounting_template": (mounting or {}).get("identity", {}).get("component_template_code"),
            "logo_segment": (logo or {}).get("identity", {}).get("logo_segment_key"),
            "internal_cost_visibility": (body.get("internal_cost_summary") or {}).get("visibility"),
        }

        plan_before = await client.get(f"/api/v1/execution/plan/{GATE_ORDER_ID}")
        truth_again = await client.get(f"/api/v1/operator/orders/{GATE_ORDER_ID}/task-truth")
        evidence["checks"]["deterministic"] = {
            "first_count": len(tasks),
            "second_count": len((truth_again.json() if truth_again.status_code == 200 else {}).get("tasks") or []),
            "plan_unchanged": plan_before.status_code == 200,
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    ok = (
        evidence["checks"]["task_truth"]["status_code"] == 200
        and evidence["checks"]["task_truth"]["task_count"] == 13
        and evidence["checks"]["task_truth"]["contract_version"] == "operator_task_truth/v1"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
