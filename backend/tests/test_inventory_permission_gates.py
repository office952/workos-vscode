from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from core.database import get_db
from dependencies.auth import get_current_user
from models.inventory_materials import Inventory_materials
from routers.admin_inventory_materials import router as admin_inventory_materials_router
from routers.inventory_deduction import router as inventory_deduction_router
from schemas.auth import UserResponse


def _ensure_material(db_fixture, code: str = "MAT-PERM-GATE-001") -> None:
    async def _seed():
        async with db_fixture.session_maker() as session:
            existing = (
                await session.execute(
                    select(Inventory_materials).where(Inventory_materials.code == code)
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    Inventory_materials(
                        code=code,
                        name="Permission Gate Material",
                        unit="buc",
                        category="test",
                        unit_cost=10.0,
                        status="active",
                    )
                )
                await session.commit()

    db_fixture.run(_seed())


def _request_as_role(db_fixture, role: str, method: str, path: str, json_body: dict | None = None):
    app = FastAPI()
    app.include_router(inventory_deduction_router)
    app.include_router(admin_inventory_materials_router)

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id=f"test-{role}",
            email=f"{role}@workos.test",
            name=f"Test {role}",
            role=role,
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    with TestClient(app, raise_server_exceptions=False) as client:
        return client.request(method=method, url=path, json=json_body)


def _assert_permission_denied(response):
    assert response.status_code == 403
    body = response.json()
    assert body.get("detail", {}).get("error") == "permission_denied"


def test_deduction_status_requires_inventory_view(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="GET",
        path="/api/v1/inventory/deduction/status/7",
    )
    _assert_permission_denied(response)


def test_deduction_status_allows_sales_inventory_view(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="sales",
        method="GET",
        path="/api/v1/inventory/deduction/status/7",
    )
    assert response.status_code == 200


def test_deduction_movements_requires_inventory_view_movements(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="sales",
        method="GET",
        path="/api/v1/inventory/deduction/movements/recent",
    )
    _assert_permission_denied(response)


def test_deduction_movements_allows_operator(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="operator",
        method="GET",
        path="/api/v1/inventory/deduction/movements/recent",
    )
    assert response.status_code == 200


def test_deduction_post_requires_inventory_deduct_stock(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="operator",
        method="POST",
        path="/api/v1/inventory/deduction/deduct/7",
        json_body={},
    )
    _assert_permission_denied(response)


def test_admin_inventory_list_requires_inventory_view(db_fixture):
    response = _request_as_role(
        db_fixture,
        role="viewer",
        method="GET",
        path="/api/admin/inventory-materials",
    )
    _assert_permission_denied(response)


def test_admin_inventory_get_allows_sales_inventory_view(db_fixture):
    _ensure_material(db_fixture)
    response = _request_as_role(
        db_fixture,
        role="sales",
        method="GET",
        path="/api/admin/inventory-materials/MAT-PERM-GATE-001",
    )
    assert response.status_code == 200


def test_admin_inventory_patch_requires_inventory_update(db_fixture):
    _ensure_material(db_fixture)
    response = _request_as_role(
        db_fixture,
        role="sales",
        method="PATCH",
        path="/api/admin/inventory-materials/MAT-PERM-GATE-001",
        json_body={"supplier": "forbidden-update"},
    )
    _assert_permission_denied(response)


def test_admin_inventory_patch_allows_manager_inventory_update(db_fixture):
    _ensure_material(db_fixture)
    response = _request_as_role(
        db_fixture,
        role="manager",
        method="PATCH",
        path="/api/admin/inventory-materials/MAT-PERM-GATE-001",
        json_body={"supplier": "allowed-update"},
    )
    assert response.status_code == 200
    assert response.json().get("supplier") == "allowed-update"