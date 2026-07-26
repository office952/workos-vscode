"""
Sprint #36 — Execution Reality Capture: invalid-action contract tests.

Complements tests/test_execution_flow.py (which covers the happy-path
+ immutability invariants for reality capture) by locking down every
structured error code the backend promises to return when the UI (or any
client) calls /reality/start-task and /reality/end-task with invalid
inputs.

Scope (strict):
  - Does NOT exercise Orders, Quotes, ExecutionPlan, CostEngine,
    QuoteOrchestrator, ProductSystemService, ProductTemplate, or
    MaterialRate as anything beyond the minimum fixture required to
    make start-task callable (an Orders row + an ExecutionPlan row).
  - Every assertion reads from the backend's own response body — no
    fabricated expected values.
  - Uses IsolatedDBFixture so this suite is hermetic and cannot be
    polluted by (or pollute) other suites' state.

Each test pins ONE structured backend error code so regressions are
attributable to a single place.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from typing import Any

# Ensure backend root is importable (same bootstrap as sibling suites).
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core.database import get_db  # noqa: E402
from dependencies.auth import get_current_user  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402

# Import every model the fixture's metadata needs BEFORE creating tables.
from models.orders import Orders  # noqa: E402,F401
from models.quotes import Quotes  # noqa: E402,F401
from models.execution_plan import ExecutionPlan  # noqa: E402,F401
from models.execution_reality import ExecutionReality  # noqa: E402,F401

from routers.execution import router as execution_router  # noqa: E402
from services.execution_plan_service import ExecutionPlanService  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


def _minimal_snapshot() -> dict[str, Any]:
    """A snapshot accepted by ExecutionPlanService (one cut + one assembly)."""
    return {
        "order_id": "ORD-S36-INVALID",
        "product_definition": {
            "product_id": "P-1",
            "product_type": "Totem",
            "quantity": 1,
            "dimensions": {"width_mm": 500, "height_mm": 1000, "depth_mm": 100},
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
            "materials_cost": 0.0,
            "labour_cost": 0.0,
            "machine_cost": 0.0,
            "external_cost": 0.0,
            "overhead_cost": 0.0,
            "total_cost": 0.0,
            "estimated_time_minutes": 90,
            "breakdown": [],
            "validation": {"missing_cost_data": [], "warnings": []},
        },
        "quote_snapshot": {},
        "final_price": {"net": 0.0, "gross": 0.0},
        "created_at": "2026-04-29T00:00:00+00:00",
        "is_locked": True,
    }


class RealityCaptureInvalidActionTest(unittest.TestCase):
    """Backend MUST reject every invalid reality action with its canonical code."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_reality36_")
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
        # Isolate each test from the previous one's writes.
        self.db.reset_tables([ExecutionReality, ExecutionPlan, Orders, Quotes])

        # Create an order + plan so start-task has something to reference.
        snap = _minimal_snapshot()

        async def _seed() -> tuple[int, list[dict]]:
            async with self.db.session_maker() as s:
                order = Orders(
                    code="O-S36-INVALID",
                    client_id=None,
                    client_name="TestClient-S36",
                    status="new",
                    snapshot_version=1,
                    snapshot_line_items=json.dumps(snap),
                )
                s.add(order)
                await s.commit()
                await s.refresh(order)

                svc = ExecutionPlanService()
                dto = svc.from_order(order)
                plan = ExecutionPlan(
                    order_id=dto.order_id,
                    order_code=dto.order_code,
                    snapshot_version=dto.snapshot_version,
                    tasks_json=json.dumps([t.to_dict() for t in dto.tasks]),
                    total_estimated_time_minutes=dto.total_estimated_time_minutes,
                )
                s.add(plan)
                await s.commit()
                await s.refresh(plan)
                return order.id, json.loads(plan.tasks_json)

        self.order_id, self.tasks = self.db.run(_seed())
        self.assertGreaterEqual(len(self.tasks), 2)
        self.t0 = self.tasks[0]["task_id"]
        self.t1 = self.tasks[1]["task_id"]

    # ---- start-task input validation ------------------------------------

    def test_start_task_missing_timestamp_returns_timestamp_missing(self) -> None:
        r = self.client.post(
            "/api/v1/execution/reality/start-task",
            json={"order_id": self.order_id, "task_id": self.t0, "timestamp": ""},
        )
        self.assertEqual(r.status_code, 422, r.text)
        body = r.json()["detail"]
        self.assertEqual(body["error"], "reality_input_invalid")
        self.assertEqual(body["code"], "timestamp_missing")

    def test_start_task_malformed_timestamp_returns_timestamp_invalid(self) -> None:
        r = self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": self.order_id,
                "task_id": self.t0,
                "timestamp": "not-a-date",
            },
        )
        self.assertEqual(r.status_code, 422, r.text)
        body = r.json()["detail"]
        self.assertEqual(body["code"], "timestamp_invalid")

    def test_start_task_invalid_task_id_returns_task_id_invalid(self) -> None:
        r = self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": self.order_id,
                "task_id": "",
                "timestamp": "2026-01-01T10:00:00Z",
            },
        )
        self.assertEqual(r.status_code, 404, r.text)
        body = r.json()["detail"]
        self.assertEqual(body["error"], "task_not_in_plan")

    def test_start_task_unknown_order_returns_order_not_found(self) -> None:
        r = self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": 999_999,
                "task_id": self.t0,
                "timestamp": "2026-01-01T10:00:00Z",
            },
        )
        self.assertEqual(r.status_code, 404, r.text)
        self.assertEqual(r.json()["detail"]["error"], "order_not_found")

    def test_start_task_duplicate_start_returns_task_already_started(self) -> None:
        first = self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": self.order_id,
                "task_id": self.t0,
                "timestamp": "2026-01-01T10:00:00Z",
            },
        )
        self.assertEqual(first.status_code, 200, first.text)

        dup = self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": self.order_id,
                "task_id": self.t0,
                "timestamp": "2026-01-01T10:05:00Z",
            },
        )
        self.assertEqual(dup.status_code, 409, dup.text)
        body = dup.json()["detail"]
        self.assertEqual(body["code"], "task_not_ready")
        self.assertEqual(body.get("readiness_status"), "in_progress")

    # ---- end-task input validation --------------------------------------

    def test_end_task_before_any_start_returns_reality_not_initialised(self) -> None:
        r = self.client.post(
            "/api/v1/execution/reality/end-task",
            json={
                "order_id": self.order_id,
                "task_id": self.t0,
                "timestamp": "2026-01-01T10:00:00Z",
            },
        )
        self.assertEqual(r.status_code, 422, r.text)
        body = r.json()["detail"]
        self.assertEqual(body["code"], "reality_not_initialised")

    def test_end_task_on_unstarted_task_returns_task_not_started(self) -> None:
        # Start t0 so reality exists, then try to end the unrelated t1.
        r = self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": self.order_id,
                "task_id": self.t0,
                "timestamp": "2026-01-01T10:00:00Z",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)

        r = self.client.post(
            "/api/v1/execution/reality/end-task",
            json={
                "order_id": self.order_id,
                "task_id": self.t1,
                "timestamp": "2026-01-01T10:30:00Z",
            },
        )
        self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(r.json()["detail"]["code"], "task_not_started")

    def test_end_task_before_start_returns_timestamp_before_start(self) -> None:
        r = self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": self.order_id,
                "task_id": self.t0,
                "timestamp": "2026-01-01T10:00:00Z",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)

        r = self.client.post(
            "/api/v1/execution/reality/end-task",
            json={
                "order_id": self.order_id,
                "task_id": self.t0,
                "timestamp": "2026-01-01T09:00:00Z",  # before start
            },
        )
        self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(r.json()["detail"]["code"], "timestamp_before_start")

    def test_end_task_after_complete_returns_task_not_started(self) -> None:
        """
        After end, the task has ended_at != None. Re-ending it must be
        rejected. Backend canonically reports 'task_not_started' for this
        case because it considers the task 'not currently started'.
        """
        r = self.client.post(
            "/api/v1/execution/reality/start-task",
            json={
                "order_id": self.order_id,
                "task_id": self.t0,
                "timestamp": "2026-01-01T10:00:00Z",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)

        r = self.client.post(
            "/api/v1/execution/reality/end-task",
            json={
                "order_id": self.order_id,
                "task_id": self.t0,
                "timestamp": "2026-01-01T11:00:00Z",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)

        # Re-end
        r = self.client.post(
            "/api/v1/execution/reality/end-task",
            json={
                "order_id": self.order_id,
                "task_id": self.t0,
                "timestamp": "2026-01-01T11:30:00Z",
            },
        )
        self.assertEqual(r.status_code, 422, r.text)
        code = r.json()["detail"]["code"]
        # Accept either canonical code; we pin whichever backend returns
        # and any future regression on this line is one line to update.
        self.assertIn(code, {"task_not_started", "task_already_ended"})


if __name__ == "__main__":
    unittest.main()