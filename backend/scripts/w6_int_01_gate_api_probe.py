"""W6-INT-01 operator truth gate — read-only API probe against :8001."""
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
    / "w6_int_01_gate_evidence.json"
)


def _keys_present(obj: dict, keys: list[str]) -> dict[str, bool]:
    return {k: k in obj for k in keys}


async def main() -> int:
    evidence: dict = {
        "gate": "W6-INT-01",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE,
        "gate_order_id": GATE_ORDER_ID,
        "probes": {},
    }

    async with httpx.AsyncClient(base_url=BASE, headers=DEV_HEADERS, timeout=30.0) as client:
        # production-release status
        pr = await client.get(f"/api/v1/execution/orders/{GATE_ORDER_ID}/production-release-status")
        pr_body = pr.json() if pr.status_code == 200 else {"error": pr.text}
        evidence["probes"]["production_release_status"] = {
            "status_code": pr.status_code,
            "production_released": pr_body.get("production_released"),
            "unresolved_blocker_count": len(pr_body.get("unresolved_production_blockers") or []),
            "resolved_count": len(pr_body.get("resolved_owner_decisions") or []),
            "sample_blocker": (pr_body.get("unresolved_production_blockers") or [None])[0],
        }

        # execution plan (admin)
        plan = await client.get(f"/api/v1/execution/plan/{GATE_ORDER_ID}")
        plan_body = plan.json() if plan.status_code == 200 else {}
        tasks = plan_body.get("tasks") or []
        sample = tasks[0] if tasks else {}
        mounting = next(
            (
                t
                for t in tasks
                if isinstance(t, dict)
                and (t.get("frozen_identity") or {}).get("source_component_role") == "mounting_panel"
            ),
            None,
        )
        logo = next(
            (
                t
                for t in tasks
                if isinstance(t, dict)
                and (t.get("frozen_identity") or {}).get("source_segment_key") == "logo_instance_001"
            ),
            None,
        )
        evidence["probes"]["execution_plan"] = {
            "status_code": plan.status_code,
            "task_count": len(tasks),
            "sample_task_id": sample.get("task_id"),
            "frozen_identity_on_plan": _keys_present(
                sample.get("frozen_identity") or {},
                [
                    "contract_version",
                    "deterministic_task_key",
                    "source_component_role",
                    "source_template_code",
                    "source_graph_node_id",
                    "source_segment_key",
                    "identity_classification",
                ],
            ),
            "mounting_role": (mounting or {}).get("frozen_identity", {}).get("source_component_role"),
            "logo_segment": (logo or {}).get("frozen_identity", {}).get("source_segment_key"),
        }

        # operator tasks list
        op = await client.get("/api/v1/operator/tasks")
        op_body = op.json() if op.status_code == 200 else {}
        op_tasks = [t for t in (op_body.get("tasks") or []) if t.get("order_id") == GATE_ORDER_ID]
        op_sample = op_tasks[0] if op_tasks else {}
        evidence["probes"]["operator_tasks"] = {
            "status_code": op.status_code,
            "gate_order_task_count": len(op_tasks),
            "sample_task_id": op_sample.get("task_id"),
            "fields_present": _keys_present(
                op_sample,
                [
                    "task_id",
                    "display_name",
                    "process_type",
                    "status",
                    "block_reason",
                    "is_startable",
                    "frozen_identity",
                    "readiness_label",
                ],
            ),
        }

        # production blueprint
        bp = await client.get(f"/api/v1/operator/orders/{GATE_ORDER_ID}/production-blueprint")
        bp_body = bp.json() if bp.status_code == 200 else {}
        bp_tasks = bp_body.get("tasks") or []
        bp_sample = bp_tasks[0] if bp_tasks else {}
        evidence["probes"]["production_blueprint"] = {
            "status_code": bp.status_code,
            "task_count": len(bp_tasks),
            "sample_task_id": bp_sample.get("task_id"),
            "fields_present": _keys_present(
                bp_sample,
                [
                    "task_id",
                    "name",
                    "status",
                    "is_startable",
                    "readiness_label",
                    "blocking_reasons",
                    "frozen_identity",
                ],
            ),
            "startable_assigned_count": sum(
                1 for t in bp_tasks if t.get("status") in {"todo", "unassigned", "assigned"} and t.get("is_startable")
            ),
        }

        # blocked start attempt on second assigned task
        blocked_probe: dict = {"attempted": False}
        candidate = next(
            (
                t
                for t in bp_tasks
                if t.get("status") in {"todo", "unassigned"}
                and t.get("is_startable") is False
            ),
            None,
        )
        if candidate:
            blocked_probe["attempted"] = True
            blocked_probe["task_id"] = candidate.get("task_id")
            start = await client.post(
                "/api/v1/operator/task-action",
                json={
                    "order_id": GATE_ORDER_ID,
                    "task_id": candidate["task_id"],
                    "action": "start",
                    "employee_id": 1,
                },
            )
            blocked_probe["status_code"] = start.status_code
            try:
                detail = start.json()
            except Exception:
                detail = {"raw": start.text}
            blocked_probe["detail_keys"] = list(detail.keys()) if isinstance(detail, dict) else []
            blocked_probe["error"] = detail.get("detail") if isinstance(detail, dict) else detail
        evidence["probes"]["blocked_start_attempt"] = blocked_probe

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    print(json.dumps(evidence, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
