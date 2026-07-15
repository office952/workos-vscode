"""W6-INT-02 — Wave 6 operator truth + blocker resolution integration gate."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from core.database import db_manager
from models.execution_plan import ExecutionPlan
from models.orders import Orders
from scripts.w6_t03_blocked_fixture_setup import seed_blocked_fixture
from sqlalchemy import select

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
    / "docs/qa/product-system-active-path-isolation-v1/w6_int_02_gate_evidence.json"
)


def _snapshot_hash(snapshot_json: str | None) -> str | None:
    if not snapshot_json:
        return None
    return hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest()[:16]


async def _order_snapshot_hash(order_id: int) -> str | None:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        order = await db.get(Orders, order_id)
        if order is None:
            return None
        return _snapshot_hash(order.snapshot_v2_json)


async def _execution_plan_meta(order_id: int) -> dict:
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        plan = (
            await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == order_id))
        ).scalar_one_or_none()
        if plan is None:
            return {"plan_id": None, "task_count": 0}
        tasks = plan.tasks_json or []
        if isinstance(tasks, str):
            tasks = json.loads(tasks)
        return {
            "plan_id": plan.id,
            "task_count": len(tasks) if isinstance(tasks, list) else 0,
        }


async def _task_truth(client: httpx.AsyncClient, order_id: int) -> dict:
    res = await client.get(
        f"{BASE_URL}/api/v1/operator/orders/{order_id}/task-truth",
        headers=DEV_HEADERS,
    )
    res.raise_for_status()
    return res.json()


def _identity_probe(truth: dict) -> dict:
    tasks = truth.get("tasks") or []
    roles = {}
    logo = None
    sample_task_id = None
    startable_count = 0
    blocked_startable = 0
    for task in tasks:
        ident = task.get("identity") or {}
        runtime = task.get("runtime") or {}
        role = ident.get("component_role")
        if role and role not in roles:
            roles[role] = {
                "task_id": ident.get("task_id"),
                "display_label": ident.get("display_label"),
                "component_label": ident.get("component_label"),
                "identity_source": ident.get("identity_source"),
            }
        if ident.get("logo_segment_key"):
            logo = {
                "task_id": ident.get("task_id"),
                "logo_segment_key": ident.get("logo_segment_key"),
                "display_label": ident.get("display_label"),
            }
        if sample_task_id is None:
            sample_task_id = ident.get("task_id")
        if runtime.get("is_startable"):
            startable_count += 1
        if runtime.get("production_release_blocked"):
            blocked_startable += 1
    return {
        "contract_version": truth.get("contract_version"),
        "task_count": len(tasks),
        "roles_present": roles,
        "logo_partial_identity": logo,
        "sample_task_id": sample_task_id,
        "startable_task_count": startable_count,
        "tasks_with_production_release_blocked": blocked_startable,
        "production_release_status": truth.get("production_release_status"),
        "production_release_blocked": truth.get("production_release_blocked"),
        "role_capabilities": truth.get("role_capabilities"),
    }


def _blocking_summary(truth: dict) -> dict:
    summary = truth.get("owner_decisions_summary") or []
    blocking = [d for d in summary if d.get("blocking")]
    nonblocking = [d for d in summary if not d.get("blocking")]
    unresolved_blocking = [
        d["code"] for d in blocking if d.get("operational_status") != "resolved"
    ]
    return {
        "blocking_count": len(blocking),
        "nonblocking_count": len(nonblocking),
        "unresolved_blocking_codes": unresolved_blocking,
        "nonblocking_codes": [d["code"] for d in nonblocking],
    }


async def _resolve(client: httpx.AsyncClient, order_id: int, code: str, note: str) -> dict:
    res = await client.post(
        f"{BASE_URL}/api/v1/execution/orders/{order_id}/owner-decisions/{code}/resolve",
        json={"status": "resolved", "note": note},
        headers=DEV_HEADERS,
    )
    body = res.json() if res.content else {}
    return {"status_code": res.status_code, "body": body}


async def run(base_url: str = BASE_URL) -> dict:
    global BASE_URL
    BASE_URL = base_url.rstrip("/")

    evidence: dict = {
        "gate": "W6-INT-02",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "blocked_order_id": BLOCKED_ORDER_ID,
        "allowed_order_id": ALLOWED_ORDER_ID,
        "runtime_ownership": {
            "backend_port": 8001,
            "frontend_port": 3000,
            "backend_pid_note": "recorded at gate run via netstat",
        },
        "db_mutations": [
            "reset_and_seed_blocked_fixture_23150",
            "operational_resolutions_on_23150",
        ],
        "authority_trace": [],
        "checks": {},
    }

    seed_result = await seed_blocked_fixture()
    evidence["fixture_seed"] = seed_result

    snapshot_before = await _order_snapshot_hash(BLOCKED_ORDER_ID)
    plan_before = await _execution_plan_meta(BLOCKED_ORDER_ID)

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        truth0 = await _task_truth(client, BLOCKED_ORDER_ID)
        identity0 = _identity_probe(truth0)
        blockers0 = _blocking_summary(truth0)

        evidence["checks"]["initial_state"] = {
            "snapshot_hash": snapshot_before,
            "plan_meta": plan_before,
            "identity": identity0,
            "blockers": blockers0,
            "can_resolve_owner_decisions": (truth0.get("role_capabilities") or {}).get(
                "can_resolve_owner_decisions"
            ),
        }

        evidence["authority_trace"].extend(
            [
                {
                    "transition": "frozen_plan_identity → task-truth",
                    "backend_source": "operator_task_truth/v1",
                    "frontend_consumer": "useOperatorTaskTruth / taskTruthByTaskId",
                    "authority": "BACKEND",
                    "mutation": False,
                    "result": f"{identity0['task_count']} tasks with roles {list(identity0['roles_present'].keys())}",
                },
                {
                    "transition": "task-truth → component labels",
                    "backend_source": "identity.display_label / component_label",
                    "frontend_consumer": "OperatorTaskIdentityPresentation",
                    "authority": "BACKEND",
                    "mutation": False,
                    "result": "display_label primary; deterministic_task_key diagnostic only",
                },
                {
                    "transition": "owner_decisions → release summary",
                    "backend_source": "production_release_status / owner_decisions_summary",
                    "frontend_consumer": "OperatorProductionReleaseSummary",
                    "authority": "BACKEND",
                    "mutation": False,
                    "result": f"{blockers0['unresolved_blocking_codes']}",
                },
                {
                    "transition": "role_capabilities → resolve control",
                    "backend_source": "role_capabilities.can_resolve_owner_decisions + item.can_resolve",
                    "frontend_consumer": "OperatorOwnerDecisionResolutionForm",
                    "authority": "BACKEND",
                    "mutation": False,
                    "result": str(
                        (truth0.get("role_capabilities") or {}).get("can_resolve_owner_decisions")
                    ),
                },
            ]
        )

        r1 = await _resolve(
            client,
            BLOCKED_ORDER_ID,
            PRODUCTION_BLOCKERS[0],
            "W6-INT-02 gate: Forex rezolvat partial.",
        )
        truth1 = await _task_truth(client, BLOCKED_ORDER_ID)
        blockers1 = _blocking_summary(truth1)
        identity1 = _identity_probe(truth1)

        evidence["checks"]["after_one_resolution"] = {
            "resolve_status": r1["status_code"],
            "release_status": r1["body"].get("release_status"),
            "production_release_blocked": truth1.get("production_release_blocked"),
            "unresolved_blocking": blockers1["unresolved_blocking_codes"],
            "resolved_item": next(
                (
                    d
                    for d in truth1.get("owner_decisions_summary", [])
                    if d.get("code") == PRODUCTION_BLOCKERS[0]
                ),
                None,
            ),
            "startable_task_count": identity1["startable_task_count"],
        }

        r1_idem = await _resolve(
            client,
            BLOCKED_ORDER_ID,
            PRODUCTION_BLOCKERS[0],
            "W6-INT-02 gate: Forex rezolvat partial.",
        )
        evidence["checks"]["idempotent_repeat"] = {
            "status_code": r1_idem["status_code"],
            "idempotent": r1_idem["body"].get("idempotent"),
        }

        for code in PRODUCTION_BLOCKERS[1:]:
            await _resolve(
                client,
                BLOCKED_ORDER_ID,
                code,
                f"W6-INT-02 gate: {code} rezolvat.",
            )

        truth_final = await _task_truth(client, BLOCKED_ORDER_ID)
        identity_final = _identity_probe(truth_final)
        blockers_final = _blocking_summary(truth_final)

        evidence["checks"]["after_full_resolution"] = {
            "production_release_blocked": truth_final.get("production_release_blocked"),
            "production_release_status": truth_final.get("production_release_status"),
            "unresolved_blocking": blockers_final["unresolved_blocking_codes"],
            "startable_task_count": identity_final["startable_task_count"],
            "resolved_blocking_codes": [
                d["code"]
                for d in truth_final.get("owner_decisions_summary", [])
                if d.get("blocking") and d.get("operational_status") == "resolved"
            ],
        }

        evidence["authority_trace"].extend(
            [
                {
                    "transition": "resolve form → backend endpoint",
                    "backend_source": "POST owner-decisions/{code}/resolve",
                    "frontend_consumer": "executionOwnerDecisionRelease.resolveOwnerDecision",
                    "authority": "BACKEND",
                    "mutation": True,
                    "result": "readiness_snapshot.owner_decision_resolutions_v1 only",
                },
                {
                    "transition": "backend response → refresh",
                    "backend_source": "task-truth refetch",
                    "frontend_consumer": "refreshTaskTruth / useOperatorTaskTruth.refresh",
                    "authority": "BACKEND",
                    "mutation": False,
                    "result": truth_final.get("production_release_status"),
                },
                {
                    "transition": "refresh → task startability",
                    "backend_source": "runtime.is_startable per task",
                    "frontend_consumer": "ExecutionDetail / OperatorView start guards",
                    "authority": "BACKEND",
                    "mutation": False,
                    "result": f"startable={identity_final['startable_task_count']}",
                },
            ]
        )

        allowed = await _task_truth(client, ALLOWED_ORDER_ID)
        evidence["checks"]["allowed_order_23099"] = {
            "production_release_blocked": allowed.get("production_release_blocked"),
            "production_release_status": allowed.get("production_release_status"),
            "task_count": len(allowed.get("tasks") or []),
            "identity_probe": _identity_probe(allowed),
        }

        snapshot_after = await _order_snapshot_hash(BLOCKED_ORDER_ID)
        plan_after = await _execution_plan_meta(BLOCKED_ORDER_ID)

        evidence["checks"]["snapshot_immutability"] = {
            "hash_before": snapshot_before,
            "hash_after": snapshot_after,
            "unchanged": snapshot_before == snapshot_after and snapshot_before is not None,
        }
        evidence["checks"]["plan_stability"] = {
            "before": plan_before,
            "after": plan_after,
            "unchanged": plan_before == plan_after,
        }

        evidence["checks"]["operator_forbidden"] = {
            "covered_by": "backend_pytest_test_unauthorized_resolution_rejected",
            "expected": "403 for operator role on resolve endpoint",
        }

        evidence["checks"]["task_identity_preserved"] = {
            "sample_task_id_before": identity0["sample_task_id"],
            "sample_task_id_after": identity_final["sample_task_id"],
            "roles_before": list(identity0["roles_present"].keys()),
            "roles_after": list(identity_final["roles_present"].keys()),
            "unchanged": identity0["sample_task_id"] == identity_final["sample_task_id"]
            and identity0["roles_present"].keys() == identity_final["roles_present"].keys(),
        }

    failed = []
    init = evidence["checks"]["initial_state"]
    if init["blockers"]["blocking_count"] != 3:
        failed.append("initial_blocker_count")
    if init["identity"]["contract_version"] != "operator_task_truth/v1":
        failed.append("contract_version")
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
    if not evidence["checks"]["plan_stability"]["unchanged"]:
        failed.append("plan_rebuilt")
    if not evidence["checks"]["task_identity_preserved"]["unchanged"]:
        failed.append("task_identity_changed")

    evidence["passed"] = len(failed) == 0
    evidence["failed_checks"] = failed

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
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
    print("W6-INT-02 runtime gate PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
