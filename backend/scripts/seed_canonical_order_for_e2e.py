"""
seed_canonical_order_for_e2e.py — Sprint #33

Creates ONE canonical Order row whose `snapshot_line_items` JSON satisfies
`ExecutionPlanService.from_order()` strict contract (Sprint #27 hardening),
so that `POST /api/v1/execution/plan/from-order/{id}` can be proven end-to-end
to return HTTP 201 and persist a real ExecutionPlan.

Scope boundaries (enforced, non-negotiable):
  - Does NOT modify CostEngine, QuoteOrchestrator, ProductSystemService.
  - Does NOT modify ExecutionPlanService or the strict snapshot contract.
  - Does NOT relax `snapshot_incomplete` validation.
  - Only INSERTS one `orders` row; idempotent (detects pre-existing seed by code).
  - Snapshot shape is byte-copied from the passing test
    `tests/test_execution_flow.py::_complete_snapshot_dict()`, which is the
    canonical reference for the contract.

Usage:
    cd /workspace/app/backend
    python scripts/seed_canonical_order_for_e2e.py

Output:
    Prints the resulting order_id on success. Idempotent: if a row with the
    seed code already exists, it is re-used (not duplicated, not mutated).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

# Ensure backend root is importable when run from anywhere.
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from sqlalchemy import select  # noqa: E402

from core.database import db_manager  # noqa: E402
from models.orders import Orders  # noqa: E402


SEED_ORDER_CODE = "O-E2E-SPRINT33"


def canonical_snapshot_dict() -> dict:
    """Return a fully-populated OrderSnapshot that satisfies the strict
    contract in `ExecutionPlanService.from_order`.

    The shape mirrors the reference used in `test_execution_flow.py::
    _complete_snapshot_dict` (which already proves 201 in the isolated DB
    test suite). Two real processes, total est. minutes = 2 * (30 + 60) = 180.
    """
    return {
        "order_id": SEED_ORDER_CODE,
        "product_definition": {
            "product_id": "P-E2E-1",
            "product_type": "Totem",
            "quantity": 2,
            "dimensions": {"width_mm": 1000, "height_mm": 3000, "depth_mm": 300},
            "layers": [
                {
                    "layer_id": "layer_1",
                    "layer_type": "structure",
                    "material": {
                        "material_id": "MAT-ACP-3",
                        "name": "ACP 3mm",
                        "unit": "sqm",
                    },
                    "thickness_mm": 3,
                    "finish": "",
                    "components": [],
                    "processes": [
                        {
                            "process_id": "CNC_CUT",
                            "type": "cut",
                            "machine_type": "CNC",
                            "estimated_time_minutes": 30,
                        },
                        {
                            "process_id": "ASM",
                            "type": "assembly",
                            "machine_type": "assembly",
                            "estimated_time_minutes": 60,
                        },
                    ],
                }
            ],
            "validation": {"is_valid": True, "missing_fields": [], "warnings": []},
        },
        "cost_result": {
            "is_valid": True,
            "currency": "RON",
            "materials_cost": 480.0,
            "labour_cost": 240.0,
            "machine_cost": 120.0,
            "external_cost": 0.0,
            "overhead_cost": 100.8,
            "total_cost": 940.8,
            "estimated_time_minutes": 180,
            "breakdown": [],
            "validation": {"missing_cost_data": [], "warnings": []},
        },
        "quote_snapshot": {},
        "final_price": {"net": 1175.0, "gross": 1398.25},
        "created_at": "2026-05-02T00:00:00+00:00",
        "is_locked": True,
    }


async def seed() -> dict:
    """Insert or re-use the seed order. Returns a dict with order_id + status."""
    snapshot = canonical_snapshot_dict()
    snapshot_json = json.dumps(snapshot)

    # Lazy-init the db_manager (same path as FastAPI's get_db dependency).
    await db_manager.ensure_initialized()
    if not db_manager.async_session_maker:
        raise RuntimeError("seed_canonical_order_for_e2e: no async_session_maker available")

    async with db_manager.async_session_maker() as session:
        # Idempotency guard: re-use existing row if already seeded.
        res = await session.execute(
            select(Orders).where(Orders.code == SEED_ORDER_CODE)
        )
        existing = res.scalar_one_or_none()
        if existing is not None:
            return {
                "order_id": existing.id,
                "order_code": existing.code,
                "status": "already_exists",
                "snapshot_version": existing.snapshot_version,
            }

        row = Orders(
            code=SEED_ORDER_CODE,
            client_name="E2E Smoke Client — Sprint #33",
            status="locked",
            total_amount=1398.25,
            snapshot_version=1,
            snapshot_line_items=snapshot_json,
            locked_at=datetime.now(timezone.utc).isoformat(),
            notes="Seeded by scripts/seed_canonical_order_for_e2e.py (Sprint #33). "
                  "Canonical snapshot for execution plan 201 smoke. Do not mutate.",
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return {
            "order_id": row.id,
            "order_code": row.code,
            "status": "created",
            "snapshot_version": row.snapshot_version,
        }


def main() -> int:
    result = asyncio.run(seed())
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())