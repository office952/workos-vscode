"""W5-T03 planning/readiness adapter runtime proof against trusted :8001 backend."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx

from core.database import db_manager
from models.orders import Orders
from services.order_snapshot_v2_planning_readiness_adapter_service import (
    load_order_planning_readiness_contract,
    load_order_planning_readiness_input,
)
from tests.test_order_snapshot_v2_planning_readiness_adapter import (
    ADAPTER_OID_BASE,
    _snapshot_with_preparation_canonical,
)

BASE = "http://127.0.0.1:8001"
DEV_HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Origin": "http://127.0.0.1:3000",
}
GATE_ORDER_ID = ADAPTER_OID_BASE + 99
OUT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "qa"
    / "product-system-active-path-isolation-v1"
    / "w5_t03_runtime_gate_evidence.json"
)


async def _seed_gate_fixture() -> dict:
    await db_manager.ensure_initialized()
    snapshot_json = _snapshot_with_preparation_canonical(
        quote_id=GATE_ORDER_ID,
        quote_snapshot_v2_id=GATE_ORDER_ID,
        preparation={
            "mounting_template_enabled": True,
            "mounting_template_material_type": "forex",
            "mounting_template_area_m2": 2.0,
            "face_finish_type": "oracal_651",
            "face_vinyl_color_code": "RAL9005",
            "face_vinyl_roll_width_mm": 1260,
        },
    )
    async with db_manager.async_session_maker() as db:
        existing = await db.get(Orders, GATE_ORDER_ID)
        if existing is None:
            db.add(
                Orders(
                    id=GATE_ORDER_ID,
                    code="ORD-W5T03-GATE",
                    quote_id=GATE_ORDER_ID,
                    quote_code="QT-W5T03-GATE",
                    client_name="W5T03 Gate Fixture",
                    status="locked",
                    total_amount=1500.0,
                    quote_snapshot_v2_id=GATE_ORDER_ID,
                    snapshot_v2_json=snapshot_json,
                    snapshot_line_items=json.dumps(
                        {
                            "quote_input": {
                                "mounting_template_material_type": "paper",
                            }
                        }
                    ),
                    readiness_snapshot={"source": "w5_t03_runtime_gate_fixture"},
                )
            )
        else:
            existing.snapshot_v2_json = snapshot_json
        await db.commit()
        before_hash = hash(snapshot_json)
        one = await load_order_planning_readiness_input(db, GATE_ORDER_ID)
        two = await load_order_planning_readiness_input(db, GATE_ORDER_ID)
        contract = await load_order_planning_readiness_contract(db, GATE_ORDER_ID)
        refreshed = await db.get(Orders, GATE_ORDER_ID)
        return {
            "order_id": GATE_ORDER_ID,
            "snapshot_hash": before_hash,
            "authority_one": one.get("_planning_readiness_authority"),
            "authority_two": two.get("_planning_readiness_authority"),
            "readiness_deterministic": one == two,
            "mounting_material_type": one.get("mounting_template_material_type"),
            "legacy_line_items_ignored": one.get("mounting_template_material_type") == "forex",
            "contract_authority": contract.authority_source if contract else None,
            "snapshot_unchanged": refreshed.snapshot_v2_json == snapshot_json,
        }


async def _http_checks(order_id: int) -> dict:
    async with httpx.AsyncClient(base_url=BASE, timeout=30.0) as client:
        release = await client.get(
            f"/api/v1/execution/orders/{order_id}/production-release-status",
            headers=DEV_HEADERS,
        )
        preview = await client.post(
            f"/api/v1/execution/plan-v2/preview/{order_id}",
            headers=DEV_HEADERS,
        )
        return {
            "production_release_status": {
                "status_code": release.status_code,
                "body": release.json() if release.status_code == 200 else release.text,
            },
            "plan_preview": {
                "status_code": preview.status_code,
                "task_count": len((preview.json() or {}).get("planned_tasks") or [])
                if preview.status_code == 200
                else 0,
            },
        }


async def main() -> int:
    fixture = await _seed_gate_fixture()
    http = await _http_checks(fixture["order_id"])
    evidence = {
        "base": BASE,
        "fixture": fixture,
        "http": http,
        "pass_checks": {
            "frozen_authority": fixture["authority_one"] == "FROZEN_ORDER_SNAPSHOT_V2",
            "deterministic_reads": fixture["readiness_deterministic"],
            "legacy_ignored": fixture["legacy_line_items_ignored"],
            "snapshot_unchanged": fixture["snapshot_unchanged"],
            "release_status_live": http["production_release_status"]["status_code"] == 200,
            "preview_http_ok": http["plan_preview"]["status_code"] == 200,
        },
    }
    evidence["pass"] = all(evidence["pass_checks"].values())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence["pass_checks"], indent=2))
    print(f"evidence={OUT}")
    return 0 if evidence["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
