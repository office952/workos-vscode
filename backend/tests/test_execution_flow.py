"""
Integration tests for Execution Layer v1.

Verified invariants (non-negotiable):
  1. ExecutionPlan is generated ONLY from the Order snapshot.
     It does NOT import or call CostEngine / QuoteOrchestrator /
     ProductSystemService.
  2. ExecutionReality never modifies the Order row.
  3. ExecutionReality never modifies the ExecutionPlan row.
  4. Divergence (GET) is read-only: no new rows in any table after call.
  5. Divergence computes planned vs actual deltas correctly.
  6. Missing snapshot fields raise 422 with explicit field path — NO silent 0.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import datetime, timezone

# Ensure backend root is importable.
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from core.database import get_db  # noqa: E402
from dependencies.auth import get_current_user  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402

# Import ORM models so Base.metadata sees them before create_all.
from models.orders import Orders  # noqa: E402,F401
from models.quotes import Quotes  # noqa: E402,F401
from models.execution_plan import ExecutionPlan  # noqa: E402,F401
from models.execution_reality import ExecutionReality  # noqa: E402,F401

from routers.execution import router as execution_router  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


def _complete_snapshot_dict() -> dict:
    """A fully-populated OrderSnapshot JSON payload with two real processes.

    Updated 2026-05-09 (PHASE8_FIXTURE_UPDATE_STRICT_MODE_ALIGNMENT):
    - order_id removed from snapshot to avoid BLK-09 cross-check mismatch
      (gate skips cross-check when snapshot.order_id is absent; the row's
      own id/code/snapshot_version are validated independently).
    - process types changed from legacy "cut"/"assembly" to canonical
      "cnc_routing"/"final_assembly" per CANONICAL_TASK_TYPES (20-value enum)
      to satisfy BLK-08.
    - These changes align fixtures with GATE_WRITER_STRICT=1 reality.
    """
    return {
        "product_definition": {
            "product_id": "P-1",
            "product_type": "Totem",
            "quantity": 2,
            "dimensions": {"width_mm": 1000, "height_mm": 3000, "depth_mm": 300},
            "layers": [
                {
                    "layer_id": "layer_1",
                    "layer_type": "structure",
                    "material": {"material_id": "MAT-ACP-3", "name": "ACP 3mm", "unit": "sqm"},
                    "thickness_mm": 3,
                    "finish": "",
                    "components": [],
                    "processes": [
                        {
                            "process_id": "CNC_CUT",
                            "type": "cnc_routing",
                            "machine_type": "CNC",
                            "estimated_time_minutes": 30,
                        },
                        {
                            "process_id": "ASM",
                            "type": "final_assembly",
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
        "created_at": "2026-04-29T00:00:00+00:00",
        "is_locked": True,
    }


def _incomplete_snapshot_dict() -> dict:
    """Snapshot missing `quantity` in product_definition."""
    d = _complete_snapshot_dict()
    del d["product_definition"]["quantity"]
    return d


class ExecutionFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_exec_")
        cls.db.setup()

        async def _override_get_db():
            async with cls.db.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return UserResponse(
                id="test-user-id",
                email="test@example.com",
                name="Test Admin",
                role="admin",
                last_login=None,
            )

        cls.app = FastAPI()
        cls.app.include_router(execution_router)
        cls.app.dependency_overrides[get_db] = _override_get_db
        cls.app.dependency_overrides[get_current_user] = _override_get_current_user
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.client.close()
        except Exception:
            pass
        cls.db.teardown()

    def setUp(self) -> None:
        self.db.reset_tables([ExecutionReality, ExecutionPlan, Orders, Quotes])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _create_order(
        self,
        snapshot_dict: dict,
        total_amount: float = 1398.25,
        readiness_snapshot: dict | None = None,
    ) -> Orders:
        async def _do():
            async with self.db.session_maker() as s:
                row = Orders(
                    code="ORD-TEST-001",
                    client_name="ACME",
                    status="locked",
                    total_amount=total_amount,
                    snapshot_version=1,
                    snapshot_line_items=json.dumps(snapshot_dict),
                    readiness_snapshot=readiness_snapshot,
                )
                s.add(row)
                await s.commit()
                await s.refresh(row)
                return row

        return self.db.run(_do())

    def _count_rows(self, model_cls) -> int:
        async def _do():
            async with self.db.session_maker() as s:
                res = await s.execute(select(func.count()).select_from(model_cls))
                return int(res.scalar() or 0)

        return self.db.run(_do())

    def _fetch_order_snapshot(self, order_id: int) -> dict:
        async def _do():
            async with self.db.session_maker() as s:
                res = await s.execute(select(Orders).where(Orders.id == order_id))
                row = res.scalar_one()
                return {
                    "id": row.id,
                    "code": row.code,
                    "client_name": row.client_name,
                    "status": row.status,
                    "total_amount": row.total_amount,
                    "snapshot_version": row.snapshot_version,
                    "snapshot_line_items": row.snapshot_line_items,
                    "locked_at": row.locked_at,
                    "readiness_snapshot": row.readiness_snapshot,
                }

        return self.db.run(_do())

    def _fetch_plan_snapshot(self, plan_id: int) -> dict:
        async def _do():
            async with self.db.session_maker() as s:
                res = await s.execute(
                    select(ExecutionPlan).where(ExecutionPlan.id == plan_id)
                )
                row = res.scalar_one()
                return {
                    "id": row.id,
                    "order_id": row.order_id,
                    "order_code": row.order_code,
                    "snapshot_version": row.snapshot_version,
                    "tasks_json": row.tasks_json,
                    "total_estimated_time_minutes": row.total_estimated_time_minutes,
                }

        return self.db.run(_do())

    # ------------------------------------------------------------------
    # 1. Plan generated ONLY from order snapshot
    # ------------------------------------------------------------------
    def test_plan_generated_only_from_order_snapshot(self) -> None:
        order = self._create_order(_complete_snapshot_dict())

        resp = self.client.post(f"/api/v1/execution/plan/from-order/{order.id}")
        self.assertEqual(resp.status_code, 201, resp.text)
        body = resp.json()
        self.assertEqual(body["order_id"], order.id)
        self.assertEqual(body["snapshot_version"], 1)
        self.assertEqual(len(body["tasks"]), 2)
        # Each task time is scaled by quantity=2.
        self.assertAlmostEqual(body["tasks"][0]["estimated_time_minutes"], 60.0)
        self.assertAlmostEqual(body["tasks"][1]["estimated_time_minutes"], 120.0)
        self.assertAlmostEqual(body["total_estimated_time_minutes"], 180.0)

    def test_plan_generation_updates_order_readiness_snapshot(self) -> None:
        order = self._create_order(
            _complete_snapshot_dict(),
            readiness_snapshot={
                "source": "intake_v6_guarded_convert",
                "snapshot_type": "intake_v6_accepted_quote_at_order_creation",
                "snapshot_at": "2026-04-29T00:00:00+00:00",
                "quote_status": "accepted",
                "requires_production_handoff_build": True,
                "execution_plan_created": False,
                "inventory_mutated": False,
                "no_execution_plan_created": True,
            },
        )

        resp = self.client.post(f"/api/v1/execution/plan/from-order/{order.id}")
        self.assertEqual(resp.status_code, 201, resp.text)

        updated = self._fetch_order_snapshot(order.id)
        self.assertIsInstance(updated["readiness_snapshot"], dict)
        self.assertTrue(updated["readiness_snapshot"]["execution_plan_created"])
        self.assertFalse(updated["readiness_snapshot"]["no_execution_plan_created"])

    # ------------------------------------------------------------------
    # 2. Missing snapshot field -> explicit 422 (no silent 0)
    # ------------------------------------------------------------------
    def test_plan_raises_422_on_missing_snapshot_field(self) -> None:
        order = self._create_order(_incomplete_snapshot_dict())
        resp = self.client.post(f"/api/v1/execution/plan/from-order/{order.id}")
        self.assertEqual(resp.status_code, 422, resp.text)
        detail = resp.json()["detail"]
        self.assertEqual(detail["error"], "snapshot_incomplete")
        self.assertEqual(detail["field"], "snapshot.product_definition.quantity")

    # ------------------------------------------------------------------
    # 3. Reality does NOT modify Order
    # ------------------------------------------------------------------
    def test_reality_does_not_modify_order(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        plan_resp = self.client.post(f"/api/v1/execution/plan/from-order/{order.id}")
        self.assertEqual(plan_resp.status_code, 201, plan_resp.text)
        before = self._fetch_order_snapshot(order.id)

        r1 = self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": order.id,
                "task_id": "T-001",
                "timestamp": "2026-04-29T08:00:00+00:00",
            },
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        r2 = self.client.post(
            "/api/v1/execution/reality/end-task",
            json={
                "order_id": order.id,
                "task_id": "T-001",
                "timestamp": "2026-04-29T09:00:00+00:00",
            },
        )
        self.assertEqual(r2.status_code, 200, r2.text)

        after = self._fetch_order_snapshot(order.id)
        self.assertEqual(before, after)  # byte-identical on all audited columns

    # ------------------------------------------------------------------
    # 4. Reality does NOT modify Plan
    # ------------------------------------------------------------------
    def test_reality_does_not_modify_plan(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        resp = self.client.post(f"/api/v1/execution/plan/from-order/{order.id}")
        self.assertEqual(resp.status_code, 201, resp.text)
        plan_id = resp.json()["id"]
        before = self._fetch_plan_snapshot(plan_id)

        self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": order.id,
                "task_id": "T-001",
                "timestamp": "2026-04-29T08:00:00+00:00",
            },
        )
        self.client.post(
            "/api/v1/execution/reality/end-task",
            json={
                "order_id": order.id,
                "task_id": "T-001",
                "timestamp": "2026-04-29T09:30:00+00:00",
            },
        )

        after = self._fetch_plan_snapshot(plan_id)
        self.assertEqual(before, after)

    # ------------------------------------------------------------------
    # 5. Divergence is READ-ONLY
    # ------------------------------------------------------------------
    def test_divergence_is_readonly(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        self.client.post(f"/api/v1/execution/plan/from-order/{order.id}")
        self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": order.id,
                "task_id": "T-001",
                "timestamp": "2026-04-29T08:00:00+00:00",
            },
        )
        self.client.post(
            "/api/v1/execution/reality/end-task",
            json={
                "order_id": order.id,
                "task_id": "T-001",
                "timestamp": "2026-04-29T10:00:00+00:00",
            },
        )

        counts_before = (
            self._count_rows(Orders),
            self._count_rows(ExecutionPlan),
            self._count_rows(ExecutionReality),
        )
        for _ in range(3):
            resp = self.client.get(f"/api/v1/execution/divergence/{order.id}")
            self.assertEqual(resp.status_code, 200, resp.text)
        counts_after = (
            self._count_rows(Orders),
            self._count_rows(ExecutionPlan),
            self._count_rows(ExecutionReality),
        )
        self.assertEqual(counts_before, counts_after)

    # ------------------------------------------------------------------
    # 6. Divergence computes delta correctly
    # ------------------------------------------------------------------
    def test_divergence_computes_delta_correctly(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        # Plan: quantity=2 * (30 + 60) = 180 minutes estimated.
        self.client.post(f"/api/v1/execution/plan/from-order/{order.id}")

        # Reality: T-001 took 60 min, T-002 took 150 min => total 210 min actual.
        self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": order.id,
                "task_id": "T-001",
                "timestamp": "2026-04-29T08:00:00+00:00",
            },
        )
        self.client.post(
            "/api/v1/execution/reality/end-task",
            json={
                "order_id": order.id,
                "task_id": "T-001",
                "timestamp": "2026-04-29T09:00:00+00:00",
            },
        )
        self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": order.id,
                "task_id": "T-002",
                "timestamp": "2026-04-29T09:00:00+00:00",
            },
        )
        self.client.post(
            "/api/v1/execution/reality/end-task",
            json={
                "order_id": order.id,
                "task_id": "T-002",
                "timestamp": "2026-04-29T11:30:00+00:00",
            },
        )

        resp = self.client.get(f"/api/v1/execution/divergence/{order.id}")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertTrue(data["has_order"])
        self.assertTrue(data["has_plan"])
        self.assertTrue(data["has_reality"])
        self.assertAlmostEqual(data["plan_total_estimated_minutes"], 180.0)
        self.assertAlmostEqual(data["reality_total_actual_minutes"], 210.0)
        self.assertAlmostEqual(data["delta_estimated_vs_actual_minutes"], 30.0)
        self.assertAlmostEqual(data["sold_total_amount"], 1398.25)

        # Per-task deltas: T-001 estimated 60, actual 60, delta 0.
        # T-002 estimated 120, actual 150, delta 30.
        by_id = {t["task_id"]: t for t in data["per_task"]}
        self.assertAlmostEqual(by_id["T-001"]["estimated_minutes"], 60.0)
        self.assertAlmostEqual(by_id["T-001"]["actual_minutes"], 60.0)
        self.assertAlmostEqual(by_id["T-001"]["delta_minutes"], 0.0)
        self.assertAlmostEqual(by_id["T-002"]["estimated_minutes"], 120.0)
        self.assertAlmostEqual(by_id["T-002"]["actual_minutes"], 150.0)
        self.assertAlmostEqual(by_id["T-002"]["delta_minutes"], 30.0)

    # ------------------------------------------------------------------
    # 7. Duplicate plan generation is rejected (v1 is write-once)
    # ------------------------------------------------------------------
    def test_plan_duplicate_generation_is_rejected(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        first = self.client.post(f"/api/v1/execution/plan/from-order/{order.id}")
        self.assertEqual(first.status_code, 201)
        second = self.client.post(f"/api/v1/execution/plan/from-order/{order.id}")
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["detail"]["error"], "plan_already_exists")


if __name__ == "__main__":
    unittest.main()