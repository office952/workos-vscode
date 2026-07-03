"""
BUILD 16 — Inventory Deduction Service: Stock Movement & Controlled Deduction.

Tests the complete deduction lifecycle:
  - Linked material rows (with material_id) can deduct stock
  - Free-text rows (no material_id) are skipped (observational only)
  - Duplicate deductions are idempotent (blocked)
  - Insufficient stock blocks deduction
  - Every deduction creates an auditable StockMovement record
  - Deduction status endpoint returns correct eligibility per row
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from typing import Any

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from core.database import get_db  # noqa: E402
from dependencies.auth import get_current_user  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402

from models.orders import Orders  # noqa: E402,F401
from models.quotes import Quotes  # noqa: E402,F401
from models.execution_plan import ExecutionPlan  # noqa: E402,F401
from models.execution_reality import ExecutionReality  # noqa: E402,F401
from models.inventory_materials import Inventory_materials  # noqa: E402,F401
from models.stock_movements import StockMovement  # noqa: E402,F401

from routers.inventory_deduction import router as deduction_router  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


class InventoryDeductionTest(unittest.TestCase):
    """Tests for the Inventory Deduction Service and Router."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_deduction16_")
        cls.db.setup()

        async def _override_get_db():
            async with cls.db.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return UserResponse(
                id="test-user-id",
                email="operator@workos.test",
                name="Test Operator",
                role="admin",
                last_login=None,
            )

        cls.app = FastAPI()
        cls.app.include_router(deduction_router)
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
        self.db.reset_tables([
            StockMovement, ExecutionReality, Inventory_materials, Orders, Quotes,
        ])
        self._seed_data()

    def _seed_data(self) -> None:
        """Create an order, inventory materials, and execution reality with mixed rows."""

        async def _seed():
            async with self.db.session_maker() as s:
                # Create order
                order = Orders(
                    code="O-B16-TEST",
                    client_id=None,
                    client_name="TestClient-B16",
                    status="in_production",
                    snapshot_version=1,
                    snapshot_line_items=json.dumps({}),
                )
                s.add(order)
                await s.commit()
                await s.refresh(order)

                # Create inventory materials
                mat1 = Inventory_materials(
                    id=101,
                    code="MAT-B16-001",
                    name="ACP 3mm Alb",
                    category="Plăci",
                    unit="mp",
                    stock_current=10.0,
                    stock_min=2.0,
                    stock_max=20.0,
                    unit_cost=85.0,
                    status="active",
                )
                mat2 = Inventory_materials(
                    id=102,
                    code="MAT-B16-002",
                    name="Vinyl autoadeziv",
                    category="Role",
                    unit="mp",
                    stock_current=5.0,
                    stock_min=1.0,
                    stock_max=15.0,
                    unit_cost=25.0,
                    status="active",
                )
                mat3 = Inventory_materials(
                    id=103,
                    code="MAT-B16-003",
                    name="Cerneală Cyan",
                    category="Consumabile",
                    unit="litru",
                    stock_current=0.5,
                    stock_min=1.0,
                    stock_max=5.0,
                    unit_cost=120.0,
                    status="active",
                )
                s.add_all([mat1, mat2, mat3])
                await s.commit()

                # Create ExecutionReality with mixed material rows
                materials = [
                    # Row 0: linked to mat1, sufficient stock
                    {"material_id": "101", "material_name": "ACP 3mm Alb", "quantity": 2.5, "unit": "mp", "task_id": "T1", "added_at": "2026-05-18T10:00:00Z"},
                    # Row 1: free-text (no material_id) — observational only
                    {"material_id": None, "material_name": "Adeziv special", "quantity": 1.0, "unit": "buc", "task_id": "T1", "added_at": "2026-05-18T10:05:00Z"},
                    # Row 2: linked to mat2, sufficient stock
                    {"material_id": "102", "material_name": "Vinyl autoadeziv", "quantity": 3.0, "unit": "mp", "task_id": "T2", "added_at": "2026-05-18T10:10:00Z"},
                    # Row 3: linked to mat3, INSUFFICIENT stock (needs 2.0, has 0.5)
                    {"material_id": "103", "material_name": "Cerneală Cyan", "quantity": 2.0, "unit": "litru", "task_id": "T2", "added_at": "2026-05-18T10:15:00Z"},
                    # Row 4: free-text (empty string material_id) — observational only
                    {"material_id": "", "material_name": "Bandă dublu adezivă", "quantity": 5.0, "unit": "m", "task_id": None, "added_at": "2026-05-18T10:20:00Z"},
                ]
                reality = ExecutionReality(
                    order_id=order.id,
                    order_code=order.code,
                    tasks_json="[]",
                    materials_json=json.dumps(materials),
                    total_actual_time_minutes=0.0,
                )
                s.add(reality)
                await s.commit()
                await s.refresh(reality)
                return order.id, reality.id

        self.order_id, self.reality_id = self.db.run(_seed())

    def _set_material_status(self, material_id: int, status: Any) -> None:
        async def _do_set() -> None:
            async with self.db.session_maker() as s:
                material = await s.get(Inventory_materials, material_id)
                self.assertIsNotNone(material)
                material.status = status
                await s.commit()

        self.db.run(_do_set())

    # ── Status endpoint tests ──────────────────────────────────────────

    def test_status_returns_correct_eligibility(self) -> None:
        """Status endpoint correctly classifies each row."""
        r = self.client.get(f"/api/v1/inventory/deduction/status/{self.order_id}")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["reality_exists"])
        self.assertEqual(body["order_id"], self.order_id)
        rows = body["rows"]
        self.assertEqual(len(rows), 5)

        # Row 0: eligible (linked, sufficient stock)
        self.assertEqual(rows[0]["status"], "eligible")
        self.assertEqual(rows[0]["material_id"], 101)

        # Row 1: not_linked (free-text)
        self.assertEqual(rows[1]["status"], "not_linked")

        # Row 2: eligible (linked, sufficient stock)
        self.assertEqual(rows[2]["status"], "eligible")
        self.assertEqual(rows[2]["material_id"], 102)

        # Row 3: insufficient_stock
        self.assertEqual(rows[3]["status"], "insufficient_stock")
        self.assertEqual(rows[3]["material_id"], 103)

        # Row 4: not_linked (empty string material_id)
        self.assertEqual(rows[4]["status"], "not_linked")

        # Summary
        self.assertEqual(body["summary"]["total"], 5)
        self.assertEqual(body["summary"]["not_linked"], 2)

    def test_status_marks_missing_price_material_as_non_operational(self) -> None:
        """Status endpoint reports non-operational materials as blocked."""
        self._set_material_status(101, "missing_price")

        r = self.client.get(f"/api/v1/inventory/deduction/status/{self.order_id}")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["rows"][0]["status"], "material_not_stock_operational")
        self.assertEqual(body["rows"][0]["material_status"], "missing_price")
        self.assertEqual(body["summary"]["non_operational_blocked"], 1)

    def test_status_no_reality_returns_empty(self) -> None:
        """Status for order without reality returns reality_exists=false."""
        r = self.client.get("/api/v1/inventory/deduction/status/999999")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertFalse(body["reality_exists"])
        self.assertEqual(body["rows"], [])

    # ── Deduction endpoint tests ──────────────────────────────────────

    def test_deduct_all_eligible_succeeds(self) -> None:
        """Deducting all eligible rows updates stock and creates movements."""
        r = self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={"reason": "Test deduction"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["order_id"], self.order_id)
        self.assertEqual(body["deducted_count"], 2)  # rows 0 and 2
        self.assertEqual(body["skipped_count"], 2)   # rows 1 and 4 (not_linked)
        self.assertEqual(body["blocked_count"], 1)   # row 3 (insufficient stock)

        # Verify per-row results
        rows = body["rows"]
        self.assertEqual(rows[0]["status"], "deducted")
        self.assertEqual(rows[0]["old_stock"], 10.0)
        self.assertEqual(rows[0]["new_stock"], 7.5)

        self.assertEqual(rows[1]["status"], "not_linked")

        self.assertEqual(rows[2]["status"], "deducted")
        self.assertEqual(rows[2]["old_stock"], 5.0)
        self.assertEqual(rows[2]["new_stock"], 2.0)

        self.assertEqual(rows[3]["status"], "insufficient_stock")

        self.assertEqual(rows[4]["status"], "not_linked")

    def test_deduct_specific_indices(self) -> None:
        """Deducting specific indices only processes those rows."""
        r = self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={"material_indices": [0], "reason": "Partial deduction"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["deducted_count"], 1)
        self.assertEqual(len(body["rows"]), 1)
        self.assertEqual(body["rows"][0]["status"], "deducted")
        self.assertEqual(body["rows"][0]["material_id"], 101)

    def test_deduct_idempotency_prevents_duplicate(self) -> None:
        """Second deduction of same row is idempotent (skipped)."""
        # First deduction
        r1 = self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={"material_indices": [0]},
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r1.json()["deducted_count"], 1)

        # Second deduction — same row
        r2 = self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={"material_indices": [0]},
        )
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertEqual(r2.json()["deducted_count"], 0)
        self.assertEqual(r2.json()["skipped_count"], 1)
        self.assertEqual(r2.json()["rows"][0]["status"], "already_deducted")

    def test_deduct_insufficient_stock_blocks_row(self) -> None:
        """Row with insufficient stock is blocked, not deducted."""
        r = self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={"material_indices": [3]},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["deducted_count"], 0)
        self.assertEqual(body["blocked_count"], 1)
        self.assertEqual(body["rows"][0]["status"], "insufficient_stock")

    def test_deduct_free_text_row_is_skipped(self) -> None:
        """Free-text row (no material_id) is skipped."""
        r = self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={"material_indices": [1]},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["deducted_count"], 0)
        self.assertEqual(body["skipped_count"], 1)
        self.assertEqual(body["rows"][0]["status"], "not_linked")

    def test_deduct_no_reality_returns_error(self) -> None:
        """Deduction for order without reality returns error."""
        r = self.client.post(
            "/api/v1/inventory/deduction/deduct/999999",
            json={},
        )
        self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(r.json()["detail"]["error"], "reality_not_found")

    def test_deduct_blocks_missing_price_material(self) -> None:
        """Deduction must block non-operational missing_price status."""
        self._set_material_status(101, "missing_price")

        r = self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={"material_indices": [0], "reason": "status gate test"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["deducted_count"], 0)
        self.assertEqual(body["blocked_count"], 1)
        self.assertEqual(body["rows"][0]["status"], "material_not_stock_operational")
        self.assertIn("missing_price", body["rows"][0]["message"])

    def test_deduct_blocks_inactive_material(self) -> None:
        """Deduction must block non-operational inactive status."""
        self._set_material_status(101, "inactive")

        r = self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={"material_indices": [0], "reason": "status gate test"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["deducted_count"], 0)
        self.assertEqual(body["blocked_count"], 1)
        self.assertEqual(body["rows"][0]["status"], "material_not_stock_operational")
        self.assertIn("inactive", body["rows"][0]["message"])

    def test_deduct_allows_none_status_material(self) -> None:
        """Deduction remains allowed for legacy rows with null status."""
        self._set_material_status(102, None)

        r = self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={"material_indices": [2], "reason": "legacy null status allowed"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["deducted_count"], 1)
        self.assertEqual(body["rows"][0]["status"], "deducted")

    def test_deduct_invalid_order_id(self) -> None:
        """Invalid order_id returns 422."""
        r = self.client.post(
            "/api/v1/inventory/deduction/deduct/0",
            json={},
        )
        self.assertEqual(r.status_code, 422, r.text)

    # ── Movements endpoint tests ──────────────────────────────────────

    def test_movements_after_deduction(self) -> None:
        """After deduction, movements endpoint returns audit trail."""
        # Perform deduction first
        self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={"reason": "Audit test"},
        )

        # Check movements
        r = self.client.get(f"/api/v1/inventory/deduction/movements/{self.order_id}")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["total"], 2)  # rows 0 and 2 were deducted
        movements = body["movements"]
        self.assertEqual(len(movements), 2)

        # Verify movement fields
        m = movements[0]
        self.assertIn("material_id", m)
        self.assertEqual(m["source_type"], "execution_reality")
        self.assertEqual(m["movement_type"], "consumption")
        self.assertIn("old_stock", m)
        self.assertIn("new_stock", m)
        self.assertEqual(m["performed_by"], "operator@workos.test")
        self.assertEqual(m["reason"], "Audit test")

    def test_recent_movements_empty_initially(self) -> None:
        """Recent movements is empty when no deductions have occurred."""
        r = self.client.get("/api/v1/inventory/deduction/movements/recent")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["total"], 0)

    def test_recent_movements_after_deduction(self) -> None:
        """Recent movements returns entries after deduction."""
        self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={},
        )
        r = self.client.get("/api/v1/inventory/deduction/movements/recent")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertGreater(r.json()["total"], 0)

    # ── Status after deduction ─────────────────────────────────────────

    def test_status_after_deduction_shows_already_deducted(self) -> None:
        """After deduction, status shows rows as already_deducted."""
        self.client.post(
            f"/api/v1/inventory/deduction/deduct/{self.order_id}",
            json={"material_indices": [0]},
        )
        r = self.client.get(f"/api/v1/inventory/deduction/status/{self.order_id}")
        self.assertEqual(r.status_code, 200, r.text)
        rows = r.json()["rows"]
        self.assertEqual(rows[0]["status"], "already_deducted")


if __name__ == "__main__":
    unittest.main()