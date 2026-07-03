from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from sqlalchemy import select  # noqa: E402

from core.database import db_manager  # noqa: E402
from models.execution_plan import ExecutionPlan  # noqa: E402
from models.orders import Orders  # noqa: E402
from routers.execution import create_plan_from_order  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402
from services.intake_v6_quote_to_order_service import (  # noqa: E402
    INTAKE_V6_ORDER_LINKAGE_JSON_KEY,
    rebuild_v6_order_snapshot_for_existing_order,
)


def _order_looks_like_v6(order: Orders) -> bool:
    for raw in (getattr(order, "notes", None), getattr(order, "snapshot_line_items", None)):
        if not raw or not str(raw).strip():
            continue
        try:
            parsed = json.loads(raw)
        except Exception:
            continue
        if not isinstance(parsed, dict):
            continue
        linkage = parsed.get(INTAKE_V6_ORDER_LINKAGE_JSON_KEY)
        if isinstance(linkage, dict):
            return True
        if parsed.get("created_from") == "intake_v6":
            return True
    return False


async def _plan_exists(order_id: int) -> bool:
    async with db_manager.async_session_maker() as session:
        row = (
            await session.execute(
                select(ExecutionPlan.id).where(ExecutionPlan.order_id == order_id)
            )
        ).first()
        return row is not None


def _script_user() -> UserResponse:
    return UserResponse(
        id="dev-admin-user-00000000",
        email="dev-admin@example.com",
        name="Dev Admin",
        role="admin",
    )


async def _generate_plan_for_order(order_id: int) -> dict[str, Any]:
    async with db_manager.async_session_maker() as session:
        plan = await create_plan_from_order(
            order_id,
            db=session,
            current_user=_script_user(),
            _user=None,
        )
        return {
            "plan_generated": True,
            "plan_id": plan.get("id"),
            "plan_task_count": len(plan.get("tasks", [])),
            "plan_total_estimated_time_minutes": plan.get("total_estimated_time_minutes"),
        }


async def _collect_target_order_ids(explicit_ids: list[int] | None) -> list[int]:
    if explicit_ids:
        return sorted(set(explicit_ids))

    await db_manager.init_db()
    await db_manager.create_tables()
    async with db_manager.async_session_maker() as session:
        rows = (await session.execute(select(Orders).order_by(Orders.id.asc()))).scalars().all()
        return [row.id for row in rows if _order_looks_like_v6(row)]


async def run_backfill(
    order_ids: list[int] | None = None,
    *,
    generate_plans: bool = False,
    skip_existing_plans: bool = True,
    fail_fast: bool = False,
) -> dict[str, Any]:
    await db_manager.init_db()
    await db_manager.create_tables()

    targets = await _collect_target_order_ids(order_ids)
    results: list[dict[str, Any]] = []

    async with db_manager.async_session_maker() as session:
        for order_id in targets:
            try:
                result = await rebuild_v6_order_snapshot_for_existing_order(session, order_id=order_id)
                if generate_plans:
                    existing_plan = await _plan_exists(order_id)
                    if existing_plan and skip_existing_plans:
                        result["plan_generated"] = False
                        result["plan_skipped"] = True
                        result["plan_skip_reason"] = "plan_already_exists"
                    else:
                        result.update(await _generate_plan_for_order(order_id))
                results.append(result)
            except Exception as exc:
                error_result = {
                    "order_id": order_id,
                    "rebuild_applied": False,
                    "error": str(exc),
                }
                results.append(error_result)
                if fail_fast:
                    raise

    return {
        "processed_order_ids": targets,
        "processed_count": len(results),
        "generate_plans": generate_plans,
        "skip_existing_plans": skip_existing_plans,
        "results": results,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill canonical Intake V6 order snapshots for historical orders.",
    )
    parser.add_argument(
        "order_ids",
        nargs="*",
        type=int,
        help="Optional explicit order ids. When omitted, all detectable Intake V6 orders are backfilled.",
    )
    parser.add_argument(
        "--generate-plans",
        action="store_true",
        help="Generate execution plans after backfilling the V6 order snapshots.",
    )
    parser.add_argument(
        "--no-skip-existing-plans",
        action="store_true",
        help="Attempt plan generation even when an ExecutionPlan already exists for the order.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on the first backfill or plan-generation failure instead of recording the error and continuing.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = asyncio.run(
        run_backfill(
            args.order_ids or None,
            generate_plans=args.generate_plans,
            skip_existing_plans=not args.no_skip_existing_plans,
            fail_fast=args.fail_fast,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())