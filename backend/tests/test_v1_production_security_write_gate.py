"""V1 production security write-gate closure — auth, HR projection, Intake V5 unmount."""

from __future__ import annotations

import pytest
from models.employees import Employees
from schemas.auth import UserResponse


@pytest.fixture
def operator_client(db_fixture):
    from main import app
    from core.database import get_db
    from dependencies.auth import get_current_user
    from fastapi.testclient import TestClient

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="op-user-id",
            email="operator@workos.test",
            name="Test Operator",
            role="operator",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def prod_unauth_client(db_fixture, monkeypatch):
    """Anonymous client with fail-closed auth (dev bypass disabled; env stays test)."""
    from main import app
    from core.database import get_db
    from dependencies.auth import get_current_user
    from fastapi.testclient import TestClient

    # Simulate production auth posture without flipping APP_ENV (startup safety BLOCKED).
    monkeypatch.setattr("dependencies.auth.dev_auth_allowed", lambda: False)

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


def test_intake_v5_not_mounted_anonymous(prod_unauth_client):
    """Intake V5 must not be production-mounted (404), not an open write surface."""
    resp = prod_unauth_client.get("/api/v1/intake-v5/config")
    assert resp.status_code == 404
    resp = prod_unauth_client.get("/api/v1/intake-v5/projects")
    assert resp.status_code == 404
    resp = prod_unauth_client.post("/api/v1/intake-v5/projects", json={})
    assert resp.status_code == 404
    resp = prod_unauth_client.post("/api/v1/intake-v5/calculate", json={})
    assert resp.status_code == 404


def test_intake_v5_module_has_no_discoverable_router():
    import routers.intake_v5 as mod

    assert getattr(mod, "router", None) is None
    assert getattr(mod, "_deprecated_router", None) is not None


@pytest.mark.asyncio
async def test_operator_employee_list_omits_hr_cost(db_session, operator_client):
    db_session.add(
        Employees(
            name="Sec Worker",
            status="active",
            employee_type="productive",
            cost_lunar_firma=9999.0,
            monthly_internal_pay_amount=4500.0,
            salary_currency="RON",
            observatii="private HR note",
        )
    )
    await db_session.commit()

    resp = operator_client.get("/api/v1/entities/employees")
    assert resp.status_code == 200
    items = resp.json()["items"]
    worker = next(i for i in items if i["name"] == "Sec Worker")
    assert worker["salary_amount"] is None
    assert worker["cost_lunar_firma"] is None
    assert worker["monthly_internal_pay_amount"] is None
    assert worker["cost_ora_calculat"] is None
    assert worker["observatii"] is None
    assert worker["name"] == "Sec Worker"
    assert worker["status"] == "active"


@pytest.mark.asyncio
async def test_admin_employee_list_includes_hr_cost(db_session, auth_client):
    db_session.add(
        Employees(
            name="HR Visible",
            status="active",
            employee_type="productive",
            cost_lunar_firma=7777.0,
            monthly_internal_pay_amount=3000.0,
        )
    )
    await db_session.commit()

    resp = auth_client.get("/api/v1/entities/employees")
    assert resp.status_code == 200
    worker = next(i for i in resp.json()["items"] if i["name"] == "HR Visible")
    assert worker["salary_amount"] == 7777.0
    assert worker["cost_lunar_firma"] == 7777.0
    assert worker["monthly_internal_pay_amount"] == 3000.0


@pytest.mark.asyncio
async def test_operator_registry_employee_omits_salary(db_session, operator_client):
    db_session.add(
        Employees(
            name="Reg Worker",
            status="active",
            employee_type="productive",
            cost_lunar_firma=8888.0,
        )
    )
    await db_session.commit()

    resp = operator_client.get("/api/v1/operational-registry/employees")
    assert resp.status_code == 200
    worker = next(i for i in resp.json()["items"] if i["name"] == "Reg Worker")
    assert worker.get("salary_amount") is None
    assert worker.get("salary_currency") is None


def test_operator_cannot_read_employee_payments(operator_client):
    resp = operator_client.get(
        "/api/v1/employee-payments/situation",
        params={"year": 2026, "month": 8},
    )
    assert resp.status_code == 403


def test_operator_cannot_read_hr_capacity(operator_client):
    resp = operator_client.get("/api/v1/entities/employees/lifecycle/capacity")
    assert resp.status_code == 403


def test_anonymous_employees_denied(prod_unauth_client):
    resp = prod_unauth_client.get("/api/v1/entities/employees")
    assert resp.status_code in (401, 403)


def test_anonymous_employee_payments_denied(prod_unauth_client):
    resp = prod_unauth_client.get(
        "/api/v1/employee-payments/situation",
        params={"year": 2026, "month": 8},
    )
    assert resp.status_code in (401, 403)


def test_malformed_auth_fail_closed(prod_unauth_client, monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-not-for-production")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    resp = prod_unauth_client.get(
        "/api/v1/entities/employees",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert resp.status_code in (401, 403)


def test_permission_matrix_hr_cost_roles():
    from dependencies.permissions import has_permission

    assert has_permission("admin", "employee.view_hr_cost")
    assert has_permission("manager", "employee.view_hr_cost")
    assert not has_permission("operator", "employee.view_hr_cost")
    assert not has_permission("sales", "employee.view_hr_cost")
    assert not has_permission("viewer", "employee.view_hr_cost")
    assert not has_permission("employee_mobile", "employee.view_hr_cost")


def test_no_fallback_identity_in_production_mode(prod_unauth_client):
    """Missing credentials must not resolve to synthetic Dev Admin in production mode."""
    resp = prod_unauth_client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)
