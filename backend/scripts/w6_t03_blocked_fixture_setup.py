"""Seed isolated W6-T03 blocked production fixture (order 23150) without touching 23099."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from services.execution_owner_decision_production_release_service import (
    OWNER_DECISION_RESOLUTIONS_KEY,
)
from services.execution_plan_v2_materialize_service import (
    materialize_execution_plan_v2_operational_tasks,
)
from services.execution_plan_v2_persist_service import create_execution_plan_v2_from_order
from sqlalchemy import delete, select
from tests.test_execution_owner_decision_production_release_guard import (
    NONBLOCKING,
    PRODUCTION_BLOCKERS,
    _build_snapshot_with_owner_decisions,
)
from tests.test_execution_plan_v2_frozen_task_identity import (
    _seed_v2_order_with_snapshot,
)

from core.database import db_manager

BLOCKED_ORDER_ID = 23150
BLOCKED_ORDER_CODE = "ORD-W6T03-BLOCK-GATE"


async def seed_blocked_fixture() -> dict:
    await db_manager.ensure_initialized()
    owner_codes = list(PRODUCTION_BLOCKERS) + [NONBLOCKING[0]]
    snapshot_json = _build_snapshot_with_owner_decisions(
        owner_codes,
        quote_id=BLOCKED_ORDER_ID,
        quote_snapshot_v2_id=BLOCKED_ORDER_ID,
    )

    async with db_manager.async_session_maker() as db:
        existing_plan = (
            await db.execute(select(ExecutionPlan).where(ExecutionPlan.order_id == BLOCKED_ORDER_ID))
        ).scalar_one_or_none()
        if existing_plan is not None:
            await db.execute(delete(ExecutionPlan).where(ExecutionPlan.order_id == BLOCKED_ORDER_ID))

        existing = await db.get(Orders, BLOCKED_ORDER_ID)
        if existing is not None:
            existing.code = BLOCKED_ORDER_CODE
            existing.snapshot_v2_json = snapshot_json
            existing.readiness_snapshot = {
                "source": "w6_t03_blocked_fixture",
                OWNER_DECISION_RESOLUTIONS_KEY: {},
            }
        else:
            order = await _seed_v2_order_with_snapshot(
                db,
                order_id=BLOCKED_ORDER_ID,
                quote_snapshot_v2_id=BLOCKED_ORDER_ID,
                snapshot_v2_json=snapshot_json,
            )
            order.code = BLOCKED_ORDER_CODE
            order.readiness_snapshot = {
                "source": "w6_t03_blocked_fixture",
                OWNER_DECISION_RESOLUTIONS_KEY: {},
            }

        await create_execution_plan_v2_from_order(db, BLOCKED_ORDER_ID)
        await materialize_execution_plan_v2_operational_tasks(db, BLOCKED_ORDER_ID)
        await db.commit()

    return {
        "order_id": BLOCKED_ORDER_ID,
        "order_code": BLOCKED_ORDER_CODE,
        "owner_codes": owner_codes,
        "canonical_order_23099_touched": False,
    }


async def main() -> int:
    meta = await seed_blocked_fixture()
    out = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "qa"
        / "product-system-active-path-isolation-v1"
        / "w6_t03_blocked_fixture_meta.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
