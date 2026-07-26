"""W6-T04 runtime gate: multi-blocker partial + full resolution on order 23150."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from core.database import db_manager
from models.orders import Orders
from scripts.w6_t03_blocked_fixture_setup import seed_blocked_fixture

BASE_URL = "http://127.0.0.1:8001"
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
BLOCKED_ORDER_ID = 23150
ALLOWED_ORDER_ID = 23099
PRODUCTION_BLOCKERS = (
    "INTERNAL_SABLON_FOREX_COST",
    "INTERNAL_MONTAJ_RULE",
    "INTERNAL_CONSUMABLES_RULE",
)
EVIDENCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs/qa/product-system-active-path-isolation-v1/w6_t04_runtime_gate_evidence.json"
)


def _snapshot_hash(snapshot_json: str | None) -> str | None:
    if not snapshot_json:
        return None
    return hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest()[:16]


async def _login(client: httpx.AsyncClient, username: str, password: str) -> None:
    """Unused when DEV_HEADERS apply — kept for optional real-auth runs."""
    res = await client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    res.raise_for_status()


async def _task_truth(client: httpx.AsyncClient, order_id: int) -> dict:
    res = await client.get(
        f"{BASE_URL}/api/v1/operator/orders/{order_id}/task-truth",
        headers=DEV_HEADERS,
    )
    res.raise_for_status()
    return res.json()


async def _resolve(
    client: httpx.AsyncClient,
    order_id: int,
    code: str,
    note: str,
) -> dict:
    res = await client.post(
        f"{BASE_URL}/api/v1/execution/orders/{order_id}/owner-decisions/{code}/resolve",
        json={"status": "resolved", "note": note},
        headers=DEV_HEADERS,
    )
    if res.status_code >= 400:
        return {"status_code": res.status_code, "body": res.json()}
    return {"status_code": res.status_code, "body": res.json()}


async def _order_snapshot_hash(order_id: int) -> str | None:
    """Read frozen OrderSnapshotV2 directly — no public HTTP read model for hash proof."""
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        order = await db.get(Orders, order_id)
        if order is None:
            return None
        return _snapshot_hash(order.snapshot_v2_json)


async def run(base_url: str = BASE_URL) -> dict:
    global BASE_URL
    BASE_URL = base_url.rstrip("/")

    evidence: dict = {
        "gate": "W6-T04",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "blocked_order_id": BLOCKED_ORDER_ID,
        "allowed_order_id": ALLOWED_ORDER_ID,
        "db_mutations": ["reset_and_seed_blocked_fixture_23150", "operational_resolutions_on_23150"],
        "checks": {},
    }

    seed_result = await seed_blocked_fixture()
    evidence["fixture_seed"] = seed_result

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        snapshot_before = await _order_snapshot_hash(BLOCKED_ORDER_ID)

        truth0 = await _task_truth(client, BLOCKED_ORDER_ID)
        blocking_unresolved = [
            d["code"]
            for d in truth0.get("owner_decisions_summary", [])
            if d.get("blocking") and d.get("operational_status") != "resolved"
        ]
        evidence["checks"]["initial_blockers"] = {
            "count": len(blocking_unresolved),
            "codes": blocking_unresolved,
            "production_release_blocked": truth0.get("production_release_blocked"),
        }

        # Resolve one — release must stay blocked
        r1 = await _resolve(
            client,
            BLOCKED_ORDER_ID,
            PRODUCTION_BLOCKERS[0],
            "W6-T04 runtime: Forex rezolvat partial.",
        )
        truth1 = await _task_truth(client, BLOCKED_ORDER_ID)
        evidence["checks"]["after_one_resolution"] = {
            "resolve_status": r1["status_code"],
            "release_status": r1["body"].get("release_status"),
            "production_release_blocked": truth1.get("production_release_blocked"),
            "unresolved_blocking": [
                d["code"]
                for d in truth1.get("owner_decisions_summary", [])
                if d.get("blocking") and d.get("operational_status") != "resolved"
            ],
        }

        # Idempotent repeat
        r1_idem = await _resolve(
            client,
            BLOCKED_ORDER_ID,
            PRODUCTION_BLOCKERS[0],
            "W6-T04 runtime: Forex rezolvat partial.",
        )
        evidence["checks"]["idempotent_repeat"] = {
            "status_code": r1_idem["status_code"],
            "idempotent": r1_idem["body"].get("idempotent"),
        }

        # Resolve remaining two
        for code in PRODUCTION_BLOCKERS[1:]:
            await _resolve(
                client,
                BLOCKED_ORDER_ID,
                code,
                f"W6-T04 runtime: {code} rezolvat.",
            )

        truth_final = await _task_truth(client, BLOCKED_ORDER_ID)
        evidence["checks"]["after_full_resolution"] = {
            "production_release_blocked": truth_final.get("production_release_blocked"),
            "production_release_status": truth_final.get("production_release_status"),
            "resolved_codes": [
                d["code"]
                for d in truth_final.get("owner_decisions_summary", [])
                if d.get("blocking") and d.get("operational_status") == "resolved"
            ],
        }

        snapshot_after = await _order_snapshot_hash(BLOCKED_ORDER_ID)
        evidence["checks"]["snapshot_immutability"] = {
            "hash_before": snapshot_before,
            "hash_after": snapshot_after,
            "unchanged": snapshot_before == snapshot_after and snapshot_before is not None,
        }

        evidence["checks"]["operator_forbidden"] = {
            "covered_by": "backend_pytest_test_unauthorized_resolution_rejected",
            "note": "Dev bypass token resolves as admin; operator 403 proven in focused pytest.",
        }

        allowed = await _task_truth(client, ALLOWED_ORDER_ID)
        evidence["checks"]["allowed_order_23099"] = {
            "production_release_blocked": allowed.get("production_release_blocked"),
            "production_release_status": allowed.get("production_release_status"),
        }

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    failed = []
    if evidence["checks"]["initial_blockers"]["count"] != 3:
        failed.append("initial_blocker_count")
    if not evidence["checks"]["after_one_resolution"]["production_release_blocked"]:
        failed.append("partial_should_remain_blocked")
    if evidence["checks"]["after_one_resolution"]["resolve_status"] != 200:
        failed.append("resolve_one_failed")
    if not evidence["checks"]["idempotent_repeat"].get("idempotent"):
        failed.append("idempotent_false")
    if evidence["checks"]["after_full_resolution"]["production_release_blocked"]:
        failed.append("full_should_be_allowed")
    if not evidence["checks"]["snapshot_immutability"]["unchanged"]:
        failed.append("snapshot_mutated")

    evidence["passed"] = len(failed) == 0
    evidence["failed_checks"] = failed
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=BASE_URL)
    args = parser.parse_args()
    result = asyncio.run(run(args.base_url))
    if not result.get("passed"):
        print(json.dumps(result["failed_checks"], indent=2))
        return 1
    print("W6-T04 runtime gate PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
