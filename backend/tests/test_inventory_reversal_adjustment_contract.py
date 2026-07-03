from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from core.database import get_db
from dependencies.auth import get_current_user
from models.inventory_materials import Inventory_materials
from models.stock_movements import StockMovement
from routers.inventory_deduction import router as inventory_deduction_router
from schemas.auth import UserResponse
from tests._db_fixture import IsolatedDBFixture


class TestInventoryReversalAdjustmentContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="mgx_reversal_26_44_")
        cls.db_fixture.setup()

        async def _override_get_db():
            async with cls.db_fixture.session_maker() as session:
                yield session

        cls.app = FastAPI()
        cls.app.include_router(inventory_deduction_router)
        cls.app.dependency_overrides[get_db] = _override_get_db
        cls.client = TestClient(cls.app, raise_server_exceptions=False)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.client.close()
        finally:
            cls.db_fixture.teardown()

    def setUp(self) -> None:
        self.db_fixture.reset_tables([Inventory_materials, StockMovement])

    def _seed(
        self,
        *,
        stock_current: float = 8.0,
        material_status: str = "active",
        source_type: str = "execution_reality",
        idempotency_key: str = "reality:1:mat_idx:0",
    ):
        async def _do_seed():
            async with self.db_fixture.session_maker() as session:
                material = Inventory_materials(
                    code="MAT-REV-26-44",
                    name="Reversal Material",
                    category="qa",
                    unit="mp",
                    stock_current=stock_current,
                    stock_min=0.0,
                    stock_max=100.0,
                    unit_cost=12.5,
                    status=material_status,
                )
                session.add(material)
                await session.commit()
                await session.refresh(material)

                original = StockMovement(
                    material_id=material.id,
                    source_type=source_type,
                    source_id=1,
                    order_id=7,
                    task_id="TASK-1",
                    quantity=2.0,
                    unit="mp",
                    movement_type="consumption",
                    old_stock=10.0,
                    new_stock=8.0,
                    performed_by="operator@workos.test",
                    performed_at=datetime.now(timezone.utc),
                    reason="initial deduction",
                    idempotency_key=idempotency_key,
                )
                session.add(original)
                await session.commit()
                await session.refresh(original)
                return material.id, original.id

        return self.db_fixture.run(_do_seed())

    def _override_user(self, role: str):
        async def _get_user():
            return UserResponse(
                id=f"test-{role}",
                email=f"{role}@workos.test",
                name=f"Test {role}",
                role=role,
                last_login=None,
            )

        self.app.dependency_overrides[get_current_user] = _get_user

    def test_reversal_requires_inventory_adjust_stock(self) -> None:
        self._override_user("sales")
        material_id, original_movement_id = self._seed()

        response = self.client.post(
            f"/api/v1/inventory/deduction/reverse/{original_movement_id}",
            json={"reason": "STAGING_TEST_BUILD_26_44_CONTRACT_TEST"},
        )
        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(response.json()["detail"]["error"], "permission_denied")
        self.assertEqual(response.json()["detail"]["permission"], "inventory.adjust_stock")

    def test_reversal_of_missing_movement_returns_404(self) -> None:
        self._override_user("manager")
        self._seed()

        response = self.client.post(
            "/api/v1/inventory/deduction/reverse/999999",
            json={"reason": "STAGING_TEST_BUILD_26_44_CONTRACT_TEST"},
        )
        self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(response.json()["detail"]["error"], "movement_not_found")

    def test_reversal_requires_non_empty_reason(self) -> None:
        self._override_user("manager")
        _, original_movement_id = self._seed()

        response = self.client.post(
            f"/api/v1/inventory/deduction/reverse/{original_movement_id}",
            json={"reason": ""},
        )
        self.assertEqual(response.status_code, 422, response.text)

    def test_reversal_of_consumption_adds_stock_and_creates_compensating_movement(self) -> None:
        self._override_user("manager")
        material_id, original_movement_id = self._seed()

        response = self.client.post(
            f"/api/v1/inventory/deduction/reverse/{original_movement_id}",
            json={"reason": "STAGING_TEST_BUILD_26_44_CONTRACT_TEST"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "reversed")
        self.assertEqual(body["original_movement_id"], original_movement_id)
        self.assertEqual(body["material_id"], material_id)
        self.assertEqual(body["quantity"], 2.0)
        self.assertEqual(body["old_stock"], 8.0)
        self.assertEqual(body["new_stock"], 10.0)

        # Verify original movement remains unchanged and stock increased.
        async def _load_after():
            async with self.db_fixture.session_maker() as session:
                material = await session.get(Inventory_materials, material_id)
                original = await session.get(StockMovement, original_movement_id)
                reversal = await session.execute(
                    select(StockMovement).where(
                        StockMovement.idempotency_key == f"reversal:{original_movement_id}"
                    )
                )
                return material, original, reversal.scalar_one_or_none()

        material, original, reversal = self.db_fixture.run(_load_after())
        self.assertIsNotNone(material)
        self.assertEqual(material.stock_current, 10.0)
        self.assertIsNotNone(original)
        self.assertEqual(original.movement_type, "consumption")
        self.assertEqual(original.old_stock, 10.0)
        self.assertEqual(original.new_stock, 8.0)
        self.assertIsNotNone(reversal)
        self.assertEqual(reversal.movement_type, "reversal")
        self.assertEqual(reversal.idempotency_key, f"reversal:{original_movement_id}")
        self.assertEqual(reversal.source_id, original_movement_id)

    def test_second_reversal_returns_409_and_no_second_movement(self) -> None:
        self._override_user("manager")
        _, original_movement_id = self._seed()

        first = self.client.post(
            f"/api/v1/inventory/deduction/reverse/{original_movement_id}",
            json={"reason": "STAGING_TEST_BUILD_26_44_CONTRACT_TEST"},
        )
        self.assertEqual(first.status_code, 200, first.text)

        second = self.client.post(
            f"/api/v1/inventory/deduction/reverse/{original_movement_id}",
            json={"reason": "STAGING_TEST_BUILD_26_44_CONTRACT_TEST"},
        )
        self.assertEqual(second.status_code, 409, second.text)
        body = second.json()["detail"]
        self.assertEqual(body["error"], "stock_movement_already_reversed")
        self.assertEqual(body["original_movement_id"], original_movement_id)
        self.assertIsNotNone(body["existing_reversal_movement_id"])

        async def _count_reversals():
            async with self.db_fixture.session_maker() as session:
                result = await session.execute(
                    select(StockMovement).where(
                        StockMovement.idempotency_key == f"reversal:{original_movement_id}"
                    )
                )
                return len(result.scalars().all())

        self.assertEqual(self.db_fixture.run(_count_reversals()), 1)

    def test_reversal_allows_recovery_for_missing_price_system_deduction(self) -> None:
        self._override_user("manager")
        material_id, original_movement_id = self._seed(material_status="missing_price")

        response = self.client.post(
            f"/api/v1/inventory/deduction/reverse/{original_movement_id}",
            json={"reason": "STAGING_TEST_BUILD_26_47_RECOVERY"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["material_status_non_operational_recovery"])
        self.assertEqual(body["material_status"], "missing_price")
        self.assertEqual(body["old_stock"], 8.0)
        self.assertEqual(body["new_stock"], 10.0)
        self.assertEqual(body["material_id"], material_id)

    def test_reversal_blocks_non_operational_for_non_system_movement(self) -> None:
        self._override_user("manager")
        _, original_movement_id = self._seed(
            material_status="missing_price",
            source_type="manual_adjustment",
            idempotency_key="manual:movement:1",
        )

        response = self.client.post(
            f"/api/v1/inventory/deduction/reverse/{original_movement_id}",
            json={"reason": "STAGING_TEST_BUILD_26_47_RECOVERY"},
        )
        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(response.json()["detail"]["error"], "material_inactive")

    def test_reversal_of_reversal_movement_is_blocked(self) -> None:
        self._override_user("manager")
        _, original_movement_id = self._seed()

        first = self.client.post(
            f"/api/v1/inventory/deduction/reverse/{original_movement_id}",
            json={"reason": "STAGING_TEST_BUILD_26_44_CONTRACT_TEST"},
        )
        self.assertEqual(first.status_code, 200, first.text)
        reversal_id = first.json()["reversal_movement_id"]

        second = self.client.post(
            f"/api/v1/inventory/deduction/reverse/{reversal_id}",
            json={"reason": "STAGING_TEST_BUILD_26_44_CONTRACT_TEST"},
        )
        self.assertEqual(second.status_code, 422, second.text)
        self.assertEqual(second.json()["detail"]["error"], "movement_not_reversible")


if __name__ == "__main__":
    unittest.main()
