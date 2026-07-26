"""W6-T02 task identity UI runtime proof against :8001 (read-only)."""
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
    / "w6_t02_runtime_gate_evidence.json"
)


async def main() -> int:
    evidence: dict = {
        "gate": "W6-T02",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE,
        "gate_order_id": GATE_ORDER_ID,
        "read_only": True,
        "checks": {},
    }

    async with httpx.AsyncClient(base_url=BASE, headers=DEV_HEADERS, timeout=30.0) as client:
        res = await client.get(f"/api/v1/operator/orders/{GATE_ORDER_ID}/task-truth")
        body = res.json() if res.status_code == 200 else {"error": res.text}
        tasks = body.get("tasks") or []

        def pick(role: str | None = None, *, logo: bool = False) -> dict | None:
            for t in tasks:
                ident = t.get("identity") or {}
                if logo and ident.get("logo_segment_key"):
                    return t
                if role and ident.get("component_role") == role:
                    return t
            return None

        root = pick("root_product")
        mounting = pick("mounting_panel")
        logo = pick(logo=True)

        samples = []
        for label, item in [("root", root), ("mounting", mounting), ("logo", logo)]:
            if not item:
                continue
            ident = item.get("identity") or {}
            runtime = item.get("runtime") or {}
            samples.append(
                {
                    "bucket": label,
                    "task_id": ident.get("task_id"),
                    "display_label": ident.get("display_label"),
                    "component_label": ident.get("component_label"),
                    "component_role": ident.get("component_role"),
                    "deterministic_task_key": ident.get("deterministic_task_key"),
                    "is_startable": runtime.get("is_startable"),
                    "identity_source": ident.get("identity_source"),
                }
            )

        evidence["checks"]["task_truth"] = {
            "status_code": res.status_code,
            "contract_version": body.get("contract_version"),
            "task_count": len(tasks),
            "samples": samples,
            "raw_key_not_primary_label": all(
                (s.get("display_label") or "") != (s.get("deterministic_task_key") or "")
                for s in samples
                if s.get("deterministic_task_key")
            ),
        }

        res2 = await client.get(f"/api/v1/operator/orders/{GATE_ORDER_ID}/task-truth")
        body2 = res2.json() if res2.status_code == 200 else {}
        evidence["checks"]["refresh_stable"] = {
            "first_count": len(tasks),
            "second_count": len(body2.get("tasks") or []),
            "root_task_id_stable": (
                (root or {}).get("identity", {}).get("task_id")
                == next(
                    (
                        t.get("identity", {}).get("task_id")
                        for t in (body2.get("tasks") or [])
                        if (t.get("identity") or {}).get("component_role") == "root_product"
                    ),
                    None,
                )
            ),
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    ok = (
        evidence["checks"]["task_truth"]["status_code"] == 200
        and evidence["checks"]["task_truth"]["task_count"] == 13
        and evidence["checks"]["refresh_stable"]["root_task_id_stable"]
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
