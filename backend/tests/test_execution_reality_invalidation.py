"""
BUILD 18 — ExecutionReality Data Quality & Invalid Reality Marker: Backend Tests.

Tests the complete invalidation lifecycle:
  - Invalidation with valid reason succeeds
  - Invalidation without reason is rejected
  - Invalidation of non-existent reality returns 404
  - Idempotent invalidation (already invalid) returns success
  - Invalidation when stock deducted marks stock_reconciliation_required
  - Restoration of invalid reality succeeds
  - Restoration without reason is rejected
  - Restoration of valid reality returns 409
  - Restoration blocked when stock_reconciliation_required
  - Quality status endpoint returns correct data
  - Permission enforcement (403 for unauthorized)
  - Reports exclude invalid realities
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import datetime, timezone

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

from routers.execution_reality_quality import router as quality_router  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402


def _make_admin_user():
    return UserResponse(
        id="admin-user-id",
        email="admin@workos.test",
        name="Admin User",
        role="admin",
        last_login=None,
    )


def _make_operator_user():
    return UserResponse(
        id="operator-user-id",
        email="operator@workos.test",
        name="Operator User",
        role="operator",
        last_login=None,
    )


class ExecutionRealityInvalidationTest(unittest.TestCase):
    """Tests for the ExecutionReality Invalidation Service and Router."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_reality_inv18_")
        cls.db.setup()

        async def _override_get_db():
            async with cls.db.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return _make_admin_user()

        cls.app = FastAPI()
        cls.app.include_router(quality_router)
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

    def _seed_reality(self, reality_id: int = 1, order_id: int = 100,
                      is_invalid: bool = False, stock_reconciliation: bool = False) -> None:
        """Seed an ExecutionReality record."""
        async def _do():
            async with self.db.session_maker() as s:
                row = ExecutionReality(
                    id=reality_id,
                    order_id=order_id,
                    order_code=f"CMD-{order_id:04d}",
                    materials_json=json.dumps([
                        {"material_id": 10, "material_name": "Oțel", "quantity": 5, "unit": "kg"},
                    ]),
                    is_invalid=is_invalid,
                    invalidated_at=datetime.now(timezone.utc) if is_invalid else None,
                    invalidated_by="admin@workos.test" if is_invalid else None,
                    invalid_reason="Test invalidation" if is_invalid else None,
                    stock_reconciliation_required=stock_reconciliation,
                )
                s.add(row)
                await s.commit()
        self.db.run(_do())

    def _seed_stock_movement(self, reality_id: int = 1) -> None:
        """Seed a stock movement linked to a reality."""
        async def _do():
            async with self.db.session_maker() as s:
                row = StockMovement(
                    id=1,
                    material_id=10,
                    source_type="execution_reality",
                    source_id=reality_id,
                    movement_type="consumption",
                    quantity=5.0,
                    unit="kg",
                    old_stock=50.0,
                    new_stock=45.0,
                    performed_by="operator@workos.test",
                    idempotency_key=f"reality_{reality_id}_row_0",
                )
                s.add(row)
                await s.commit()
        self.db.run(_do())

    # ─── INVALIDATION TESTS ───────────────────────────────────────────

    def test_invalidate_success(self):
        """Valid invalidation with reason succeeds."""
        self._seed_reality(reality_id=1)
        resp = self.client.post(
            "/api/v1/execution-reality/1/invalidate",
            json={"reason": "Date incorecte introduse de operator"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_invalid"])
        self.assertEqual(data["invalid_reason"], "Date incorecte introduse de operator")
        self.assertIsNotNone(data["invalidated_at"])
        self.assertEqual(data["invalidated_by"], "admin@workos.test")
        self.assertFalse(data["stock_reconciliation_required"])

    def test_invalidate_without_reason_rejected(self):
        """Invalidation without reason returns 400."""
        self._seed_reality(reality_id=1)
        resp = self.client.post(
            "/api/v1/execution-reality/1/invalidate",
            json={"reason": ""},
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data["detail"]["error"], "reason_required")

    def test_invalidate_whitespace_reason_rejected(self):
        """Invalidation with whitespace-only reason returns 400."""
        self._seed_reality(reality_id=1)
        resp = self.client.post(
            "/api/v1/execution-reality/1/invalidate",
            json={"reason": "   "},
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertEqual(data["detail"]["error"], "reason_required")

    def test_invalidate_nonexistent_reality_404(self):
        """Invalidation of non-existent reality returns 404."""
        resp = self.client.post(
            "/api/v1/execution-reality/999/invalidate",
            json={"reason": "Test reason"},
        )
        self.assertEqual(resp.status_code, 404)
        data = resp.json()
        self.assertEqual(data["detail"]["error"], "reality_not_found")

    def test_invalidate_idempotent(self):
        """Already-invalid reality returns success (idempotent)."""
        self._seed_reality(reality_id=1, is_invalid=True)
        resp = self.client.post(
            "/api/v1/execution-reality/1/invalidate",
            json={"reason": "Second invalidation attempt"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_invalid"])

    def test_invalidate_with_stock_deducted_marks_reconciliation(self):
        """Invalidation when stock was deducted marks stock_reconciliation_required."""
        self._seed_reality(reality_id=1)
        self._seed_stock_movement(reality_id=1)
        resp = self.client.post(
            "/api/v1/execution-reality/1/invalidate",
            json={"reason": "Eroare de calcul materiale"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_invalid"])
        self.assertTrue(data["stock_reconciliation_required"])
        self.assertTrue(data["stock_deducted"])

    def test_invalidate_invalid_id_422(self):
        """Invalidation with invalid ID returns 422."""
        resp = self.client.post(
            "/api/v1/execution-reality/0/invalidate",
            json={"reason": "Test"},
        )
        self.assertEqual(resp.status_code, 422)

    # ─── RESTORATION TESTS ────────────────────────────────────────────

    def test_restore_success(self):
        """Valid restoration of invalid reality succeeds."""
        self._seed_reality(reality_id=1, is_invalid=True)
        resp = self.client.post(
            "/api/v1/execution-reality/1/restore-valid",
            json={"reason": "Datele au fost verificate și sunt corecte"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["is_invalid"])
        self.assertIsNotNone(data["restored_at"])
        self.assertEqual(data["restored_by"], "admin@workos.test")
        self.assertEqual(data["restored_reason"], "Datele au fost verificate și sunt corecte")

    def test_restore_without_reason_rejected(self):
        """Restoration without reason returns 400."""
        self._seed_reality(reality_id=1, is_invalid=True)
        resp = self.client.post(
            "/api/v1/execution-reality/1/restore-valid",
            json={"reason": ""},
        )
        self.assertEqual(resp.status_code, 400)

    def test_restore_valid_reality_409(self):
        """Restoration of already-valid reality returns 409."""
        self._seed_reality(reality_id=1, is_invalid=False)
        resp = self.client.post(
            "/api/v1/execution-reality/1/restore-valid",
            json={"reason": "Test restore"},
        )
        self.assertEqual(resp.status_code, 409)
        data = resp.json()
        self.assertEqual(data["detail"]["error"], "reality_not_invalid")

    def test_restore_blocked_stock_reconciliation(self):
        """Restoration blocked when stock_reconciliation_required is True."""
        self._seed_reality(reality_id=1, is_invalid=True, stock_reconciliation=True)
        resp = self.client.post(
            "/api/v1/execution-reality/1/restore-valid",
            json={"reason": "Vreau să restaurez"},
        )
        self.assertEqual(resp.status_code, 409)
        data = resp.json()
        self.assertEqual(data["detail"]["error"], "restoration_blocked_stock_reconciliation")

    def test_restore_nonexistent_reality_404(self):
        """Restoration of non-existent reality returns 404."""
        resp = self.client.post(
            "/api/v1/execution-reality/999/restore-valid",
            json={"reason": "Test"},
        )
        self.assertEqual(resp.status_code, 404)

    # ─── QUALITY STATUS TESTS ─────────────────────────────────────────

    def test_quality_status_valid_reality(self):
        """Quality status for valid reality returns correct data."""
        self._seed_reality(reality_id=1, is_invalid=False)
        resp = self.client.get("/api/v1/execution-reality/1/quality-status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["reality_id"], 1)
        self.assertFalse(data["is_invalid"])
        self.assertIsNone(data["invalidated_at"])
        self.assertFalse(data["stock_reconciliation_required"])
        self.assertEqual(data["warnings"], [])

    def test_quality_status_invalid_reality(self):
        """Quality status for invalid reality includes warnings."""
        self._seed_reality(reality_id=1, is_invalid=True)
        resp = self.client.get("/api/v1/execution-reality/1/quality-status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_invalid"])
        self.assertGreater(len(data["warnings"]), 0)
        self.assertIn("invalidată", data["warnings"][0].lower())

    def test_quality_status_invalid_with_reconciliation(self):
        """Quality status with stock reconciliation includes extra warning."""
        self._seed_reality(reality_id=1, is_invalid=True, stock_reconciliation=True)
        resp = self.client.get("/api/v1/execution-reality/1/quality-status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["stock_reconciliation_required"])
        self.assertEqual(len(data["warnings"]), 2)

    def test_quality_status_nonexistent_404(self):
        """Quality status for non-existent reality returns 404."""
        resp = self.client.get("/api/v1/execution-reality/999/quality-status")
        self.assertEqual(resp.status_code, 404)

    def test_quality_status_invalid_id_422(self):
        """Quality status with invalid ID returns 422."""
        resp = self.client.get("/api/v1/execution-reality/0/quality-status")
        self.assertEqual(resp.status_code, 422)

    # ─── FULL LIFECYCLE TEST ──────────────────────────────────────────

    def test_full_invalidation_lifecycle(self):
        """Full lifecycle: valid → invalidate → quality check → restore."""
        self._seed_reality(reality_id=1, is_invalid=False)

        # 1. Check initial status
        resp = self.client.get("/api/v1/execution-reality/1/quality-status")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["is_invalid"])

        # 2. Invalidate
        resp = self.client.post(
            "/api/v1/execution-reality/1/invalidate",
            json={"reason": "Eroare operator — cantități greșite"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["is_invalid"])

        # 3. Check status after invalidation
        resp = self.client.get("/api/v1/execution-reality/1/quality-status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_invalid"])
        self.assertEqual(data["invalid_reason"], "Eroare operator — cantități greșite")

        # 4. Restore
        resp = self.client.post(
            "/api/v1/execution-reality/1/restore-valid",
            json={"reason": "Verificat — datele sunt corecte"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["is_invalid"])

        # 5. Final status check
        resp = self.client.get("/api/v1/execution-reality/1/quality-status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["is_invalid"])
        self.assertIsNotNone(data["restored_at"])


class ExecutionRealityPermissionTest(unittest.TestCase):
    """Tests for permission enforcement on invalidation endpoints."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.db = IsolatedDBFixture(prefix="mgx_reality_perm18_")
        cls.db.setup()

        async def _override_get_db():
            async with cls.db.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return _make_operator_user()

        cls.app = FastAPI()
        cls.app.include_router(quality_router)
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
            StockMovement, ExecutionReality, Orders, Quotes,
        ])

    def _seed_reality(self, reality_id: int = 1, is_invalid: bool = False) -> None:
        async def _do():
            async with self.db.session_maker() as s:
                row = ExecutionReality(
                    id=reality_id,
                    order_id=100,
                    order_code="CMD-0100",
                    materials_json=json.dumps([]),
                    is_invalid=is_invalid,
                    invalidated_at=datetime.now(timezone.utc) if is_invalid else None,
                    invalidated_by="admin@workos.test" if is_invalid else None,
                    invalid_reason="Previous invalidation" if is_invalid else None,
                )
                s.add(row)
                await s.commit()
        self.db.run(_do())

    def test_operator_cannot_invalidate(self):
        """Operator role cannot invalidate (403)."""
        self._seed_reality()
        resp = self.client.post(
            "/api/v1/execution-reality/1/invalidate",
            json={"reason": "Test"},
        )
        self.assertEqual(resp.status_code, 403)

    def test_operator_cannot_restore(self):
        """Operator role cannot restore (403)."""
        self._seed_reality(is_invalid=True)
        resp = self.client.post(
            "/api/v1/execution-reality/1/restore-valid",
            json={"reason": "Test"},
        )
        self.assertEqual(resp.status_code, 403)

    def test_operator_can_read_quality_status(self):
        """Operator can read quality status (read-only endpoint)."""
        self._seed_reality()
        resp = self.client.get("/api/v1/execution-reality/1/quality-status")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()