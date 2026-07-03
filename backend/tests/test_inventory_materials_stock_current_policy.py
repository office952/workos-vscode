from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.database import get_db
from dependencies.auth import get_current_user
from routers.inventory_materials import router as inventory_materials_router
from schemas.auth import UserResponse
from tests._db_fixture import IsolatedDBFixture


class TestInventoryMaterialsStockCurrentPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="mgx_stock_current_26_44_")
        cls.db_fixture.setup()

        async def _override_get_db():
            async with cls.db_fixture.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return UserResponse(
                id="test-admin-id",
                email="admin@workos.test",
                name="Test Admin",
                role="admin",
                last_login=None,
            )

        cls.app = FastAPI()
        cls.app.include_router(inventory_materials_router)
        cls.app.dependency_overrides[get_db] = _override_get_db
        cls.app.dependency_overrides[get_current_user] = _override_get_current_user
        cls.client = TestClient(cls.app, raise_server_exceptions=False)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.client.close()
        finally:
            cls.db_fixture.teardown()

    def setUp(self) -> None:
        from models.inventory_materials import Inventory_materials

        self.db_fixture.reset_tables([Inventory_materials])

    def test_create_allows_initial_stock_current(self) -> None:
        response = self.client.post(
            "/api/v1/entities/inventory_materials",
            json={
                "code": "MAT-STOCK-POLICY-26-44-A",
                "name": "Policy Material A",
                "category": "qa",
                "unit": "mp",
                "stock_current": 12.5,
                "stock_min": 0,
                "stock_max": 100,
                "unit_cost": 9.5,
                "status": "active",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["stock_current"], 12.5)

    def test_update_non_stock_fields_still_works(self) -> None:
        created = self.client.post(
            "/api/v1/entities/inventory_materials",
            json={
                "code": "MAT-STOCK-POLICY-26-44-B",
                "name": "Policy Material B",
                "category": "qa",
                "unit": "mp",
                "stock_current": 7.0,
                "stock_min": 0,
                "stock_max": 100,
                "unit_cost": 11.0,
                "status": "active",
            },
        )
        self.assertEqual(created.status_code, 201, created.text)
        material_id = created.json()["id"]

        response = self.client.put(
            f"/api/v1/entities/inventory_materials/{material_id}",
            json={"name": "Policy Material B Updated"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["name"], "Policy Material B Updated")
        self.assertEqual(response.json()["stock_current"], 7.0)

    def test_update_stock_current_is_blocked(self) -> None:
        created = self.client.post(
            "/api/v1/entities/inventory_materials",
            json={
                "code": "MAT-STOCK-POLICY-26-44-C",
                "name": "Policy Material C",
                "category": "qa",
                "unit": "mp",
                "stock_current": 3.0,
                "stock_min": 0,
                "stock_max": 100,
                "unit_cost": 5.0,
                "status": "active",
            },
        )
        self.assertEqual(created.status_code, 201, created.text)
        material_id = created.json()["id"]

        response = self.client.put(
            f"/api/v1/entities/inventory_materials/{material_id}",
            json={"stock_current": 4.0},
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["detail"], "stock_current_update_requires_stock_movement")

    def test_batch_update_stock_current_is_blocked(self) -> None:
        created = self.client.post(
            "/api/v1/entities/inventory_materials",
            json={
                "code": "MAT-STOCK-POLICY-26-44-D",
                "name": "Policy Material D",
                "category": "qa",
                "unit": "mp",
                "stock_current": 6.0,
                "stock_min": 0,
                "stock_max": 100,
                "unit_cost": 6.0,
                "status": "active",
            },
        )
        self.assertEqual(created.status_code, 201, created.text)
        material_id = created.json()["id"]

        response = self.client.put(
            "/api/v1/entities/inventory_materials/batch",
            json={
                "items": [
                    {
                        "id": material_id,
                        "updates": {
                            "stock_current": 9.0,
                        },
                    }
                ]
            },
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["detail"], "stock_current_update_requires_stock_movement")


if __name__ == "__main__":
    unittest.main()
