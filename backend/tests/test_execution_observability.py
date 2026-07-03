"""
Integration tests for Execution Observability v1 (Sprint #11).

Verified invariants (non-negotiable):
  1. Observability reads DivergenceService + config and NEVER writes
     to Orders / ExecutionPlan / ExecutionReality.
  2. Dashboard is read-only.
  3. Missing plan or missing reality -> UNCONFIRMED (no silent 0).
  4. Classification respects configurable thresholds.
  5. Alerts are a pure derived read-model (no DB writes).
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from core.database import get_db  # noqa: E402
from dependencies.auth import get_current_user  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402

# Ensure Base.metadata sees every model before create_all.
from models.execution_observation_config import ExecutionObservationConfig  # noqa: E402,F401
from models.execution_plan import ExecutionPlan  # noqa: E402,F401
from models.execution_reality import ExecutionReality  # noqa: E402,F401
from models.orders import Orders  # noqa: E402,F401
from models.quotes import Quotes  # noqa: E402,F401

from routers.execution import router as execution_router  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _complete_snapshot_dict(order_id: str = "ORD-OBS-001") -> dict:
    return {
        "order_id": order_id,
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


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------


class ExecutionObservabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_obs_")
        cls.db.setup()

        async def _override_get_db():
            async with cls.db.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return UserResponse(
                id="test-obs-user",
                email="obs-test@example.com",
                name="Test Obs User",
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
        self.db.reset_tables(
            [
                ExecutionReality,
                ExecutionPlan,
                ExecutionObservationConfig,
                Orders,
                Quotes,
            ]
        )
        # Seed one active config row per test. Warning at 15% OR 30 min,
        # critical at 35% OR 120 min.
        self._seed_config(
            warning_pct=15.0,
            critical_pct=35.0,
            warning_min=30.0,
            critical_min=120.0,
            is_active=True,
        )

    # ------------------------------------------------------------------
    # Seed helpers
    # ------------------------------------------------------------------
    def _seed_config(
        self,
        warning_pct: float,
        critical_pct: float,
        warning_min: float,
        critical_min: float,
        is_active: bool,
    ) -> None:
        async def _do():
            async with self.db.session_maker() as s:
                row = ExecutionObservationConfig(
                    warning_time_delta_pct=warning_pct,
                    critical_time_delta_pct=critical_pct,
                    warning_time_delta_minutes=warning_min,
                    critical_time_delta_minutes=critical_min,
                    is_active=is_active,
                )
                s.add(row)
                await s.commit()

        self.db.run(_do())

    def _create_order(self, snapshot_dict: dict, total_amount: float = 1398.25) -> Orders:
        async def _do():
            async with self.db.session_maker() as s:
                row = Orders(
                    code=snapshot_dict.get("order_id") or "ORD-OBS-001",
                    client_name="ACME",
                    status="locked",
                    total_amount=total_amount,
                    snapshot_version=1,
                    snapshot_line_items=json.dumps(snapshot_dict),
                )
                s.add(row)
                await s.commit()
                await s.refresh(row)
                # Patch snapshot order_id to match the actual row id so
                # the gate's BLK-09 int-coercion check passes.
                patched = dict(snapshot_dict)
                patched["order_id"] = row.id
                row.snapshot_line_items = json.dumps(patched)
                await s.commit()
                await s.refresh(row)
                return row

        return self.db.run(_do())

    def _generate_plan(self, order_id: int) -> None:
        resp = self.client.post(f"/api/v1/execution/plan/from-order/{order_id}")
        self.assertEqual(resp.status_code, 201, resp.text)

    def _record_reality(
        self,
        order_id: int,
        task_id: str,
        duration_minutes: float,
        start_iso: str = "2026-04-29T08:00:00+00:00",
    ) -> None:
        start = datetime.fromisoformat(start_iso)
        end = start + timedelta(minutes=duration_minutes)
        r1 = self.client.post(
            "/api/v1/execution/reality/start-task",
            json={"order_id": order_id, "task_id": task_id, "timestamp": start.isoformat()},
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        r2 = self.client.post(
            "/api/v1/execution/reality/end-task",
            json={"order_id": order_id, "task_id": task_id, "timestamp": end.isoformat()},
        )
        self.assertEqual(r2.status_code, 200, r2.text)

    def _count_rows(self, model_cls) -> int:
        async def _do():
            async with self.db.session_maker() as s:
                res = await s.execute(select(func.count()).select_from(model_cls))
                return int(res.scalar() or 0)

        return self.db.run(_do())

    def _snapshot_rows(self) -> tuple:
        return (
            self._count_rows(Orders),
            self._count_rows(ExecutionPlan),
            self._count_rows(ExecutionReality),
        )

    # ------------------------------------------------------------------
    # 1. OK when delta is under warning thresholds.
    # Plan: 2 * (30+60) = 180 minutes. Reality: T-001 60, T-002 125.
    # Actual total = 185, delta = 5 min (~2.78%). Under 15% and under 30 min -> OK.
    # ------------------------------------------------------------------
    def test_observability_ok_when_delta_under_warning(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        self._generate_plan(order.id)
        self._record_reality(order.id, "T-001", 60.0)
        self._record_reality(
            order.id, "T-002", 125.0, start_iso="2026-04-29T09:00:00+00:00"
        )

        resp = self.client.get(f"/api/v1/execution/observability/{order.id}")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["status"], "OK")
        self.assertTrue(data["has_plan"])
        self.assertTrue(data["has_reality"])
        self.assertAlmostEqual(data["plan_total_estimated_minutes"], 180.0)
        self.assertAlmostEqual(data["reality_total_actual_minutes"], 185.0)
        self.assertAlmostEqual(data["delta_minutes"], 5.0)
        self.assertIn("within_thresholds", data["reasons"])

    # ------------------------------------------------------------------
    # 2. WARNING when delta exceeds warning but not critical.
    # Plan 180, Reality T-001 60 + T-002 180 = 240. Delta 60 min = 33.33%.
    # 60 >= 30 (warn_min) and 33.33 < 35 (crit_pct), 60 < 120 (crit_min).
    # => WARNING.
    # ------------------------------------------------------------------
    def test_observability_warning_when_delta_exceeds_warning(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        self._generate_plan(order.id)
        self._record_reality(order.id, "T-001", 60.0)
        self._record_reality(
            order.id, "T-002", 180.0, start_iso="2026-04-29T09:00:00+00:00"
        )

        resp = self.client.get(f"/api/v1/execution/observability/{order.id}")
        data = resp.json()
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(data["status"], "WARNING")
        self.assertAlmostEqual(data["delta_minutes"], 60.0)
        self.assertAlmostEqual(data["delta_pct"], round(60.0 / 180.0 * 100.0, 4))

    # ------------------------------------------------------------------
    # 3. CRITICAL when delta exceeds critical thresholds.
    # Plan 180, Reality T-001 120 + T-002 240 = 360. Delta 180 min = 100%.
    # Both minute and pct crit thresholds exceeded.
    # ------------------------------------------------------------------
    def test_observability_critical_when_delta_exceeds_critical(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        self._generate_plan(order.id)
        self._record_reality(order.id, "T-001", 120.0)
        self._record_reality(
            order.id, "T-002", 240.0, start_iso="2026-04-29T10:00:00+00:00"
        )

        resp = self.client.get(f"/api/v1/execution/observability/{order.id}")
        data = resp.json()
        self.assertEqual(data["status"], "CRITICAL")
        self.assertAlmostEqual(data["delta_minutes"], 180.0)
        self.assertIn("minutes_over_critical", data["reasons"])

    # ------------------------------------------------------------------
    # 4. UNCONFIRMED when reality is missing (plan exists but no reality).
    # ------------------------------------------------------------------
    def test_observability_unconfirmed_when_reality_missing(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        self._generate_plan(order.id)

        resp = self.client.get(f"/api/v1/execution/observability/{order.id}")
        data = resp.json()
        self.assertEqual(data["status"], "UNCONFIRMED")
        self.assertIn("reality_missing", data["reasons"])
        # Plan figure is visible, reality is explicitly null.
        self.assertAlmostEqual(data["plan_total_estimated_minutes"], 180.0)
        self.assertIsNone(data["reality_total_actual_minutes"])
        self.assertIsNone(data["delta_minutes"])

    # ------------------------------------------------------------------
    # 5. Alert generated for WARNING classification.
    # ------------------------------------------------------------------
    def test_alert_generated_for_warning(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        self._generate_plan(order.id)
        self._record_reality(order.id, "T-001", 60.0)
        self._record_reality(
            order.id, "T-002", 180.0, start_iso="2026-04-29T09:00:00+00:00"
        )

        resp = self.client.get(f"/api/v1/execution/alerts/{order.id}")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["status"], "WARNING")
        self.assertEqual(len(data["alerts"]), 1)
        a = data["alerts"][0]
        self.assertEqual(a["order_id"], order.id)
        self.assertEqual(a["severity"], "WARNING")
        self.assertEqual(a["metric"], "time_minutes")
        self.assertAlmostEqual(a["expected_value"], 180.0)
        self.assertAlmostEqual(a["actual_value"], 240.0)
        self.assertAlmostEqual(a["delta"], 60.0)
        self.assertIn(a["reason"], {"minutes_over_warning", "pct_over_warning"})

    # ------------------------------------------------------------------
    # 6. Alert generated for CRITICAL classification.
    # ------------------------------------------------------------------
    def test_alert_generated_for_critical(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        self._generate_plan(order.id)
        self._record_reality(order.id, "T-001", 120.0)
        self._record_reality(
            order.id, "T-002", 240.0, start_iso="2026-04-29T10:00:00+00:00"
        )

        resp = self.client.get(f"/api/v1/execution/alerts/{order.id}")
        data = resp.json()
        self.assertEqual(data["status"], "CRITICAL")
        self.assertEqual(len(data["alerts"]), 1)
        a = data["alerts"][0]
        self.assertEqual(a["severity"], "CRITICAL")
        self.assertIn(a["reason"], {"minutes_over_critical", "pct_over_critical"})
        self.assertAlmostEqual(a["delta"], 180.0)

    # ------------------------------------------------------------------
    # 7. Dashboard is read-only (Orders / Plan / Reality counts unchanged).
    # ------------------------------------------------------------------
    def test_dashboard_is_read_only(self) -> None:
        o1 = self._create_order(_complete_snapshot_dict(order_id="ORD-OBS-D1"))
        o2 = self._create_order(_complete_snapshot_dict(order_id="ORD-OBS-D2"))
        self._generate_plan(o1.id)
        self._record_reality(o1.id, "T-001", 60.0)
        self._record_reality(
            o1.id, "T-002", 180.0, start_iso="2026-04-29T09:00:00+00:00"
        )
        # o2 has no plan/reality -> UNCONFIRMED on dashboard.

        before = self._snapshot_rows()
        for _ in range(3):
            resp = self.client.get("/api/v1/execution/dashboard")
            self.assertEqual(resp.status_code, 200, resp.text)
        after = self._snapshot_rows()
        self.assertEqual(before, after)

        data = resp.json()
        self.assertEqual(data["total"], 2)
        by_id = {r["order_id"]: r for r in data["rows"]}
        row1 = by_id[o1.id]
        self.assertEqual(row1["plan_status"], "present")
        self.assertEqual(row1["reality_status"], "present")
        self.assertEqual(row1["divergence_status"], "WARNING")
        self.assertEqual(row1["alert_severity"], "WARNING")
        self.assertAlmostEqual(row1["planned_time"], 180.0)
        self.assertAlmostEqual(row1["actual_time"], 240.0)
        self.assertAlmostEqual(row1["delta_time"], 60.0)

        row2 = by_id[o2.id]
        self.assertEqual(row2["plan_status"], "absent")
        self.assertEqual(row2["reality_status"], "absent")
        self.assertEqual(row2["divergence_status"], "UNCONFIRMED")
        self.assertIsNone(row2["alert_severity"])
        # Missing data must surface as null, never as 0.
        self.assertIsNone(row2["planned_time"])
        self.assertIsNone(row2["actual_time"])
        self.assertIsNone(row2["delta_time"])

    # ------------------------------------------------------------------
    # 8. Observability does NOT mutate Order, Plan, or Reality rows.
    # ------------------------------------------------------------------
    def test_observability_does_not_modify_order_plan_reality(self) -> None:
        order = self._create_order(_complete_snapshot_dict())
        self._generate_plan(order.id)
        self._record_reality(order.id, "T-001", 60.0)
        self._record_reality(
            order.id, "T-002", 180.0, start_iso="2026-04-29T09:00:00+00:00"
        )

        async def _snapshot_all():
            async with self.db.session_maker() as s:
                o_res = await s.execute(select(Orders).where(Orders.id == order.id))
                o_row = o_res.scalar_one()
                p_res = await s.execute(
                    select(ExecutionPlan).where(ExecutionPlan.order_id == order.id)
                )
                p_row = p_res.scalar_one()
                r_res = await s.execute(
                    select(ExecutionReality).where(ExecutionReality.order_id == order.id)
                )
                r_row = r_res.scalar_one()
                return (
                    {
                        "id": o_row.id,
                        "code": o_row.code,
                        "status": o_row.status,
                        "total_amount": o_row.total_amount,
                        "snapshot_version": o_row.snapshot_version,
                        "snapshot_line_items": o_row.snapshot_line_items,
                    },
                    {
                        "id": p_row.id,
                        "tasks_json": p_row.tasks_json,
                        "total_estimated_time_minutes": p_row.total_estimated_time_minutes,
                    },
                    {
                        "id": r_row.id,
                        "tasks_json": r_row.tasks_json,
                        "total_actual_time_minutes": r_row.total_actual_time_minutes,
                    },
                )

        before = self.db.run(_snapshot_all())

        # Hammer every observability endpoint several times.
        for _ in range(5):
            self.assertEqual(
                self.client.get(f"/api/v1/execution/observability/{order.id}").status_code,
                200,
            )
            self.assertEqual(
                self.client.get(f"/api/v1/execution/alerts/{order.id}").status_code,
                200,
            )
            self.assertEqual(
                self.client.get("/api/v1/execution/dashboard").status_code, 200
            )

        after = self.db.run(_snapshot_all())
        self.assertEqual(before, after)

    # ------------------------------------------------------------------
    # 9. Config inactive -> UNCONFIRMED even when all data present.
    # ------------------------------------------------------------------
    def test_observability_unconfirmed_when_config_inactive(self) -> None:
        # Replace the default active config with an inactive one.
        async def _do():
            async with self.db.session_maker() as s:
                await s.execute(ExecutionObservationConfig.__table__.delete())
                s.add(
                    ExecutionObservationConfig(
                        warning_time_delta_pct=15.0,
                        critical_time_delta_pct=35.0,
                        warning_time_delta_minutes=30.0,
                        critical_time_delta_minutes=120.0,
                        is_active=False,
                    )
                )
                await s.commit()

        self.db.run(_do())

        order = self._create_order(_complete_snapshot_dict())
        self._generate_plan(order.id)
        self._record_reality(order.id, "T-001", 60.0)
        self._record_reality(
            order.id, "T-002", 120.0, start_iso="2026-04-29T09:00:00+00:00"
        )

        data = self.client.get(
            f"/api/v1/execution/observability/{order.id}"
        ).json()
        self.assertEqual(data["status"], "UNCONFIRMED")
        self.assertIn("config_inactive", data["reasons"])


if __name__ == "__main__":
    unittest.main()