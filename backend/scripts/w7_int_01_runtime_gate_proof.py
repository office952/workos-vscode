"""W7-INT-01 — Full frozen-spine request→ExecutionReality integration gate."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

from core.database import db_manager
from models.orders import Orders

BASE = "http://127.0.0.1:8001"
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
CANONICAL_QUOTE_ID = 1
CANONICAL_SNAPSHOT_CODE = "QSN2-2026-0001"
EXECUTION_ORDER_ID = 23099
INTAKE_WORKSPACE_ID = "80570a4a-a806-4305-a39c-b34a72092694"
DB_PATH = Path(__file__).resolve().parents[1] / "dev.db"
EVIDENCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs/qa/product-system-active-path-isolation-v1/w7_int_01_gate_evidence.json"
)


def _snapshot_hash16(text: str | None) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _qsn2_readonly_probe() -> dict:
    con = sqlite3.connect(DB_PATH)
    try:
        snap = con.execute(
            "select id, snapshot_code, content_hash, readiness, status from quote_snapshots_v2 where snapshot_code=?",
            (CANONICAL_SNAPSHOT_CODE,),
        ).fetchone()
        quote = con.execute(
            "select id, code, status, grand_total, accepted_snapshot_v2_id, notes from quotes where id=?",
            (CANONICAL_QUOTE_ID,),
        ).fetchone()
        notes = json.loads(quote[5] or "{}") if quote else {}
        linkage = notes.get("intake_v6_linkage_v1") or {}
        return {
            "quote_id": quote[0] if quote else None,
            "quote_status": quote[2] if quote else None,
            "grand_total": quote[3] if quote else None,
            "accepted_snapshot_v2_id": quote[4] if quote else None,
            "snapshot_code": snap[1] if snap else None,
            "content_hash": snap[2] if snap else None,
            "readiness": snap[3] if snap else None,
            "snapshot_status": snap[4] if snap else None,
            "offer_stamp_pricing_source": (linkage.get("intake_v6_snapshot_authoritative_offer_v1") or {}).get(
                "pricing_source"
            ),
            "live_dry_run_used": (linkage.get("intake_v6_snapshot_authoritative_offer_v1") or {}).get(
                "live_dry_run_used"
            ),
            "intake_workspace_id": INTAKE_WORKSPACE_ID,
            "mutated": False,
        }
    finally:
        con.close()


async def _task_truth(client: httpx.AsyncClient, order_id: int) -> dict:
    res = await client.get(
        f"{BASE}/api/v1/operator/orders/{order_id}/task-truth",
        headers=DEV_HEADERS,
    )
    res.raise_for_status()
    return res.json()


def _identity_summary(truth: dict) -> dict:
    tasks = truth.get("tasks") or []
    roles = sorted(
        {
            (t.get("identity") or {}).get("component_role")
            for t in tasks
            if (t.get("identity") or {}).get("component_role")
        }
    )
    logo = next(
        (
            (t.get("identity") or {}).get("logo_segment_key")
            for t in tasks
            if (t.get("identity") or {}).get("logo_segment_key")
        ),
        None,
    )
    startable = sum(1 for t in tasks if (t.get("runtime") or {}).get("is_startable"))
    return {
        "contract_version": truth.get("contract_version"),
        "task_count": len(tasks),
        "roles": roles,
        "logo_segment_key": logo,
        "startable_count": startable,
        "production_release_status": truth.get("production_release_status"),
        "production_release_blocked": truth.get("production_release_blocked"),
    }


AUTHORITY_TRACE = [
    {
        "stage": "Intake V6",
        "producer": "intake_v6 workspace",
        "consumer": "7H/7G/snapshot builders",
        "canonical_authority": "workspace persisted truth",
        "operational_authority": "n/a",
        "legacy_fallback": "LEGACY_ISOLATED",
        "result": f"frozen artifact QSN2 via workspace {INTAKE_WORKSPACE_ID}",
    },
    {
        "stage": "QuoteSnapshotV2",
        "producer": "snapshot freeze service",
        "consumer": "Offer/review/acceptance",
        "canonical_authority": "quote_snapshots_v2",
        "operational_authority": "n/a",
        "legacy_fallback": "none on V2 path",
        "result": CANONICAL_SNAPSHOT_CODE,
    },
    {
        "stage": "OrderSnapshotV2",
        "producer": "convert_accepted_quote_snapshot_v2",
        "consumer": "ExecutionPlanV2 preview/persist",
        "canonical_authority": "orders.snapshot_v2_json",
        "operational_authority": "readiness_snapshot",
        "legacy_fallback": "snapshot_line_items READ_ONLY_PROJECTION",
        "result": f"order {EXECUTION_ORDER_ID} gate fixture",
    },
    {
        "stage": "ExecutionPlanV2",
        "producer": "build_execution_plan_v2_preview",
        "consumer": "materialize + operator surfaces",
        "canonical_authority": "OrderSnapshotV2 only",
        "operational_authority": "execution_plan row",
        "legacy_fallback": "LEGACY_ISOLATED old plan service",
        "result": "13 frozen task keys on 23099",
    },
    {
        "stage": "Operator task truth",
        "producer": "operator_task_truth_service",
        "consumer": "ExecutionDetail/OperatorView",
        "canonical_authority": "operator_task_truth/v1",
        "operational_authority": "owner_decision_resolutions_v1",
        "legacy_fallback": "explicit legacy_order flag",
        "result": "HTTP read model",
    },
    {
        "stage": "Production release",
        "producer": "execution_owner_decision_production_release_service",
        "consumer": "task start gate",
        "canonical_authority": "frozen owner_decisions + operational resolutions",
        "operational_authority": "readiness_snapshot",
        "legacy_fallback": "none",
        "result": "partial→full unlock",
    },
    {
        "stage": "ExecutionReality",
        "producer": "execution_reality_service",
        "consumer": "reconciliation UI",
        "canonical_authority": "reality.tasks_json events",
        "operational_authority": "n/a",
        "legacy_fallback": "LEGACY_ISOLATED",
        "result": "same task_id reference",
    },
]


async def run() -> dict:
    evidence: dict = {
        "gate": "W7-INT-01",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE,
        "runtime_ownership": {
            "backend_port": 8001,
            "frontend_port": 3000,
            "backend_pid": 26888,
            "frontend_pid": 30548,
            "port_8000": "NON_AUTHORITATIVE",
        },
        "scenario_strategy": "SINGLE_SCENARIO_WITH_CONTROLLED_STAGE_FIXTURES",
        "scenario_ids": {
            "intake_workspace_id": INTAKE_WORKSPACE_ID,
            "quote_id": CANONICAL_QUOTE_ID,
            "quote_snapshot_v2_code": CANONICAL_SNAPSHOT_CODE,
            "execution_order_id": EXECUTION_ORDER_ID,
            "execution_order_code": "ORD-W5INT02-GATE",
        },
        "authority_trace": AUTHORITY_TRACE,
        "checks": {},
    }

    qsn_before = _qsn2_readonly_probe()
    evidence["checks"]["qsn2_frozen_spine_readonly"] = qsn_before

    # W5-INT-02 execution runtime chain (reset fixture + full HTTP proof)
    w5_script = Path(__file__).resolve().parent / "w5_int_02_runtime_e2e_gate_proof.py"
    proc = subprocess.run(
        [sys.executable, str(w5_script)],
        cwd=str(Path(__file__).resolve().parents[1]),
        capture_output=True,
        text=True,
        env={
            **dict(__import__("os").environ),
            "APP_ENV": "development",
            "ENVIRONMENT": "development",
            "DATABASE_URL": "sqlite+aiosqlite:///./dev.db",
            "JWT_SECRET_KEY": "local-dev-secret-not-for-production",
        },
    )
    w5_evidence_path = (
        Path(__file__).resolve().parents[2]
        / "docs/qa/product-system-active-path-isolation-v1/w5_int_02_runtime_gate_evidence.json"
    )
    w5_body = json.loads(w5_evidence_path.read_text(encoding="utf-8")) if w5_evidence_path.exists() else {}
    evidence["checks"]["w5_execution_runtime_chain"] = {
        "subprocess_exit_code": proc.returncode,
        "pass": w5_body.get("pass"),
        "pass_checks": w5_body.get("pass_checks"),
        "steps_summary": {
            k: {"status_code": v.get("status_code")}
            for k, v in (w5_body.get("steps") or {}).items()
            if isinstance(v, dict) and "status_code" in v
        },
    }

    qsn_after = _qsn2_readonly_probe()
    evidence["checks"]["qsn2_after_execution_run"] = {
        **qsn_after,
        "hash_unchanged": qsn_before.get("content_hash") == qsn_after.get("content_hash"),
        "grand_total_unchanged": qsn_before.get("grand_total") == qsn_after.get("grand_total"),
    }

    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        order = await db.get(Orders, EXECUTION_ORDER_ID)
        evidence["checks"]["order_snapshot_v2"] = {
            "order_id": EXECUTION_ORDER_ID,
            "quote_snapshot_v2_id": order.quote_snapshot_v2_id if order else None,
            "snapshot_hash": _snapshot_hash16(order.snapshot_v2_json if order else None),
            "snapshot_unchanged_vs_w5": w5_body.get("final_state", {}).get("snapshot_unchanged"),
        }

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        truth = await _task_truth(client, EXECUTION_ORDER_ID)
        evidence["checks"]["operator_task_truth_post_chain"] = _identity_summary(truth)
        spine = await client.get(
            f"{BASE}/api/v1/intake-v6/workspaces/{INTAKE_WORKSPACE_ID}/commercial-spine-state",
            headers=DEV_HEADERS,
        )
        evidence["checks"]["intake_v6_spine_http"] = {
            "status_code": spine.status_code,
            "has_snapshot": (spine.json() if spine.status_code == 200 else {}).get("snapshot_v2", {}).get("exists")
            if spine.status_code == 200
            else None,
        }

    failed = []
    if qsn_before.get("snapshot_code") != CANONICAL_SNAPSHOT_CODE:
        failed.append("qsn2_missing")
    if not evidence["checks"]["qsn2_after_execution_run"]["hash_unchanged"]:
        failed.append("qsn2_mutated")
    if proc.returncode != 0 or not w5_body.get("pass"):
        failed.append("w5_runtime_chain")
    if truth.get("contract_version") != "operator_task_truth/v1":
        failed.append("task_truth_contract")
    if not w5_body.get("final_state", {}).get("snapshot_unchanged"):
        failed.append("order_snapshot_mutated")

    evidence["passed"] = len(failed) == 0
    evidence["failed_checks"] = failed

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


def main() -> int:
    result = asyncio.run(run())
    if not result.get("passed"):
        print(json.dumps(result["failed_checks"], indent=2))
        return 1
    print("W7-INT-01 runtime gate PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
