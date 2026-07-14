"""W5-INT-02 frozen order → execution runtime E2E gate proof (:8001)."""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy import select

from core.database import db_manager
from models.execution_plan import ExecutionPlan
from models.execution_reality import ExecutionReality
from models.orders import Orders
from schemas.quote_snapshot_v2 import QuoteSnapshotOwnerDecision
from services.execution_plan_v2_preview_service import build_execution_plan_v2_preview
from services.execution_owner_decision_production_release_service import (
    OWNER_DECISION_RESOLUTIONS_KEY,
)
from services.order_snapshot_v2_planning_readiness_adapter_service import (
    load_order_planning_readiness_contract,
)
from tests.test_execution_owner_decision_production_release_guard import (
    NONBLOCKING,
    PRODUCTION_BLOCKERS,
)
from tests.test_execution_plan_v2_frozen_task_identity import (
    MOUNTING_NODE,
    _build_identity_snapshot,
    _identity_aggregate,
)

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
    / "w5_int_02_runtime_gate_evidence.json"
)


def _build_gate_snapshot_json() -> str:
    aggregate = _identity_aggregate(include_mounting=True)
    payload = json.loads(_build_identity_snapshot(aggregate))
    payload["quote_id"] = GATE_ORDER_ID
    payload["quote_snapshot_v2_id"] = GATE_ORDER_ID
    payload["snapshot_code"] = "OSN2-INT02-GATE"
    payload["content_hash"] = "int02gatehashint02gatehashint02ga"
    payload["owner_decisions_snapshot"] = [
        QuoteSnapshotOwnerDecision(
            code=code,
            label=code.replace("_", " ").title(),
            source="estimated_internal_cost",
            module_code="gate",
            detail="W5-INT-02 runtime gate",
        ).model_dump()
        for code in PRODUCTION_BLOCKERS
    ] + [
        QuoteSnapshotOwnerDecision(
            code=NONBLOCKING[0],
            label="Ambalare nonblocking",
            source="estimated_internal_cost",
            module_code="gate",
            detail="W5-INT-02 runtime gate",
        ).model_dump()
    ]
    pd = payload.get("product_definition_snapshot") or {}
    canonical = dict(pd.get("canonical_values") or {})
    canonical.update(
        {
            "mounting_template_enabled": True,
            "mounting_template_material_type": "forex",
            "mounting_template_area_m2": 2.0,
        }
    )
    pd["canonical_values"] = canonical
    payload["product_definition_snapshot"] = pd
    return json.dumps(payload)


async def _reset_gate_fixture() -> dict:
    await db_manager.ensure_initialized()
    snapshot_json = _build_gate_snapshot_json()
    async with db_manager.async_session_maker() as db:
        existing = await db.get(Orders, GATE_ORDER_ID)
        readiness = {
            "source": "w5_int_02_runtime_gate_fixture",
            OWNER_DECISION_RESOLUTIONS_KEY: {},
        }
        if existing is None:
            db.add(
                Orders(
                    id=GATE_ORDER_ID,
                    code="ORD-W5INT02-GATE",
                    quote_id=GATE_ORDER_ID,
                    quote_code="QT-W5INT02-GATE",
                    client_name="W5-INT-02 Gate Fixture",
                    status="locked",
                    total_amount=1500.0,
                    quote_snapshot_v2_id=GATE_ORDER_ID,
                    snapshot_v2_json=snapshot_json,
                    snapshot_line_items=json.dumps(
                        {"quote_input": {"mounting_template_material_type": "paper"}}
                    ),
                    readiness_snapshot=readiness,
                )
            )
        else:
            existing.snapshot_v2_json = snapshot_json
            existing.snapshot_line_items = json.dumps(
                {"quote_input": {"mounting_template_material_type": "paper"}}
            )
            existing.readiness_snapshot = readiness
            plan = (
                await db.execute(
                    select(ExecutionPlan).where(ExecutionPlan.order_id == GATE_ORDER_ID)
                )
            ).scalar_one_or_none()
            if plan is not None:
                await db.delete(plan)
            reality = (
                await db.execute(
                    select(ExecutionReality).where(ExecutionReality.order_id == GATE_ORDER_ID)
                )
            ).scalar_one_or_none()
            if reality is not None:
                await db.delete(reality)
        await db.commit()

        preview_one = await build_execution_plan_v2_preview(db, GATE_ORDER_ID)
        preview_two = await build_execution_plan_v2_preview(db, GATE_ORDER_ID)
        keys_one = [t.task_key for t in preview_one.planned_tasks]
        keys_two = [t.task_key for t in preview_two.planned_tasks]
        readiness_contract = await load_order_planning_readiness_contract(db, GATE_ORDER_ID)
        refreshed = await db.get(Orders, GATE_ORDER_ID)
        return {
            "order_id": GATE_ORDER_ID,
            "snapshot_hash": hash(snapshot_json),
            "snapshot_code": "OSN2-INT02-GATE",
            "preview_keys_one": keys_one,
            "preview_keys_two": keys_two,
            "mounting_tasks": [
                t.model_dump()
                for t in preview_one.planned_tasks
                if t.frozen_identity and t.frozen_identity.source_graph_node_id == MOUNTING_NODE
            ],
            "readiness_authority": readiness_contract.authority_source if readiness_contract else None,
            "legacy_line_items_present": refreshed.snapshot_line_items is not None,
        }



async def main() -> int:
    seeded = await _reset_gate_fixture()
    first_task_key = seeded["preview_keys_one"][0] if seeded["preview_keys_one"] else None
    evidence: dict = {
        "base": BASE,
        "trusted_backend_pid": 26888,
        "fixture": seeded,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps": {},
    }

    async with httpx.AsyncClient(base_url=BASE, timeout=60.0, headers=DEV_HEADERS) as client:
        preview_http = await client.post(f"/api/v1/execution/plan-v2/preview/{GATE_ORDER_ID}")
        evidence["steps"]["http_preview"] = {
            "status_code": preview_http.status_code,
            "task_keys": [
                t.get("task_key")
                for t in (preview_http.json() or {}).get("planned_tasks") or []
            ]
            if preview_http.status_code == 200
            else [],
        }

        persist_http = await client.post(f"/api/v1/execution/plan-v2/from-order/{GATE_ORDER_ID}")
        evidence["steps"]["http_persist_first"] = {
            "status_code": persist_http.status_code,
            "body": persist_http.json() if persist_http.content else {},
        }

        persist_http_two = await client.post(f"/api/v1/execution/plan-v2/from-order/{GATE_ORDER_ID}")
        evidence["steps"]["http_persist_second"] = {
            "status_code": persist_http_two.status_code,
            "body": persist_http_two.json() if persist_http_two.content else {},
        }

        materialize_http = await client.post(
            f"/api/v1/execution/plan-v2/materialize-tasks/{GATE_ORDER_ID}"
        )
        evidence["steps"]["http_materialize"] = {
            "status_code": materialize_http.status_code,
            "body": materialize_http.json() if materialize_http.content else {},
        }

        release_before = await client.get(
            f"/api/v1/execution/orders/{GATE_ORDER_ID}/production-release-status"
        )
        evidence["steps"]["production_release_before"] = {
            "status_code": release_before.status_code,
            "body": release_before.json() if release_before.content else {},
        }

        start_blocked = await client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": GATE_ORDER_ID,
                "task_id": first_task_key,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        evidence["steps"]["start_blocked"] = {
            "status_code": start_blocked.status_code,
            "body": start_blocked.json() if start_blocked.content else {},
        }

        resolve_partial = await client.post(
            f"/api/v1/execution/orders/{GATE_ORDER_ID}/owner-decisions/INTERNAL_SABLON_FOREX_COST/resolve",
            json={"status": "resolved", "note": "W5-INT-02 partial resolve"},
        )
        evidence["steps"]["resolve_one_blocker"] = {
            "status_code": resolve_partial.status_code,
            "body": resolve_partial.json() if resolve_partial.content else {},
        }

        start_still_blocked = await client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": GATE_ORDER_ID,
                "task_id": first_task_key,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        evidence["steps"]["start_after_partial_resolve"] = {
            "status_code": start_still_blocked.status_code,
            "body": start_still_blocked.json() if start_still_blocked.content else {},
        }

        for code in ("INTERNAL_MONTAJ_RULE", "INTERNAL_CONSUMABLES_RULE"):
            resp = await client.post(
                f"/api/v1/execution/orders/{GATE_ORDER_ID}/owner-decisions/{code}/resolve",
                json={"status": "resolved", "note": f"W5-INT-02 resolve {code}"},
            )
            evidence["steps"][f"resolve_{code.lower()}"] = {
                "status_code": resp.status_code,
                "body": resp.json() if resp.content else {},
            }

        start_allowed = await client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": GATE_ORDER_ID,
                "task_id": first_task_key,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        evidence["steps"]["start_after_full_resolve"] = {
            "status_code": start_allowed.status_code,
            "body": start_allowed.json() if start_allowed.content else {},
        }

        start_retry = await client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": GATE_ORDER_ID,
                "task_id": first_task_key,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        evidence["steps"]["start_retry_idempotent"] = {
            "status_code": start_retry.status_code,
            "body": start_retry.json() if start_retry.content else {},
        }

        reality_get = await client.get(f"/api/v1/execution/reality/{GATE_ORDER_ID}")
        evidence["steps"]["reality_get"] = {
            "status_code": reality_get.status_code,
            "body": reality_get.json() if reality_get.content else {},
        }

    service_chain = {
        "persist_two_status": evidence["steps"]["http_persist_second"]["body"].get("status"),
        "materialize_status": evidence["steps"]["http_materialize"]["body"].get("status"),
        "operational_tasks_count": evidence["steps"]["http_materialize"]["body"].get(
            "operational_tasks_count"
        ),
    }
    evidence["service_chain"] = service_chain

    async with db_manager.async_session_maker() as db:
        refreshed = await db.get(Orders, GATE_ORDER_ID)
        evidence["final_state"] = {
            "snapshot_hash": hash(refreshed.snapshot_v2_json or ""),
            "snapshot_unchanged": hash(refreshed.snapshot_v2_json or "") == seeded["snapshot_hash"],
            "resolutions_in_operational_store": bool(
                (refreshed.readiness_snapshot or {}).get(OWNER_DECISION_RESOLUTIONS_KEY)
            ),
        }

    blocked_detail = (evidence["steps"]["start_blocked"].get("body") or {}).get("detail") or {}
    partial_detail = (evidence["steps"]["start_after_partial_resolve"].get("body") or {}).get("detail") or {}
    release_body = (evidence["steps"]["production_release_before"].get("body") or {})

    pass_checks = {
        "preview_keys_stable": seeded["preview_keys_one"] == seeded["preview_keys_two"],
        "http_preview_ok": evidence["steps"]["http_preview"]["status_code"] == 200,
        "http_keys_match_service": evidence["steps"]["http_preview"]["task_keys"] == seeded["preview_keys_one"],
        "readiness_frozen_authority": seeded["readiness_authority"] == "FROZEN_ORDER_SNAPSHOT_V2",
        "mounting_identity_present": len(seeded["mounting_tasks"]) >= 1,
        "persist_first_ok": evidence["steps"]["http_persist_first"]["status_code"] in {200, 201},
        "persist_idempotent": evidence["steps"]["http_persist_second"]["body"].get("status") == "already_exists",
        "materialize_ok": evidence["steps"]["http_materialize"]["status_code"] in {200, 201},
        "release_status_live": evidence["steps"]["production_release_before"]["status_code"] == 200,
        "start_blocked_409": evidence["steps"]["start_blocked"]["status_code"] == 409,
        "start_blocked_code": blocked_detail.get("code") == "production_release_blocked",
        "partial_resolve_still_blocked": evidence["steps"]["start_after_partial_resolve"]["status_code"] == 409,
        "multi_blocker_proven": partial_detail.get("code") == "production_release_blocked",
        "start_allowed_after_resolve": evidence["steps"]["start_after_full_resolve"]["status_code"] == 200,
        "start_retry_ok": evidence["steps"]["start_retry_idempotent"]["status_code"] in {200, 409},
        "reality_recorded": evidence["steps"]["reality_get"]["status_code"] == 200,
        "snapshot_unchanged": evidence["final_state"]["snapshot_unchanged"],
        "resolutions_operational": evidence["final_state"]["resolutions_in_operational_store"],
        "nonblocking_not_in_blockers": NONBLOCKING[0] not in (release_body.get("blockers") or []),
    }
    evidence["pass_checks"] = pass_checks
    evidence["pass"] = all(pass_checks.values())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(pass_checks, indent=2))
    print(f"evidence={OUT}")
    return 0 if evidence["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
