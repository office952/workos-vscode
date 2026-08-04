"""Dev auth impersonation — development-only WORKOS_DEV_AUTH_USER_ID lookup."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from models.auth import User
from models.employees import Employees
from sqlalchemy import func, select

from core.config import resolve_dev_auth_impersonation_user_id
from core.database import get_db
from dependencies.auth import get_current_user
from main import app


async def _seed_user(
    db_session,
    *,
    user_id: str,
    email: str,
    name: str,
    role: str,
) -> User:
    user = User(id=user_id, email=email, name=name, role=role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _seed_employee(
    db_session,
    *,
    user_id: str | None,
    name: str = "Mobile Employee",
) -> Employees:
    emp = Employees(
        name=name,
        status="active",
        employee_type="productive",
        user_id=user_id,
    )
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


async def _count_users(db_session) -> int:
    result = await db_session.execute(select(func.count()).select_from(User))
    return int(result.scalar_one())


async def _count_employees(db_session) -> int:
    result = await db_session.execute(select(func.count()).select_from(Employees))
    return int(result.scalar_one())


def test_resolve_dev_auth_user_id_ignored_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("WORKOS_DEV_AUTH_USER_ID", "dev-employee-test-001")
    assert resolve_dev_auth_impersonation_user_id() is None


def test_dev_auth_without_env_returns_synthetic_dev_admin(unauth_client, monkeypatch):
    monkeypatch.delenv("WORKOS_DEV_AUTH_USER_ID", raising=False)
    resp = unauth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "dev-admin-user-00000000"
    assert body["email"] == "dev@localhost"
    assert body["role"] == "admin"


def test_dev_auth_with_env_returns_db_user(unauth_client, db_fixture, db_session, monkeypatch):
    uid = f"dev-impersonate-{uuid.uuid4().hex[:8]}"

    async def _setup():
        await _seed_user(
            db_session,
            user_id=uid,
            email=f"{uid}@workos.test",
            name="Impersonated User",
            role="employee_mobile",
        )

    db_fixture.run(_setup())
    monkeypatch.setenv("WORKOS_DEV_AUTH_USER_ID", uid)

    resp = unauth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == uid
    assert body["email"] == f"{uid}@workos.test"
    assert body["role"] == "employee_mobile"


def test_dev_auth_missing_user_returns_clear_error(unauth_client, monkeypatch):
    monkeypatch.setenv("WORKOS_DEV_AUTH_USER_ID", "missing-dev-user-id-xyz")
    resp = unauth_client.get("/api/v1/auth/me")
    assert resp.status_code == 503
    detail = resp.json()["detail"]
    assert detail["error"] == "dev_auth_user_not_found"
    assert "missing-dev-user-id-xyz" in detail["message"]


def test_employee_mobile_self_uses_impersonated_user(unauth_client, db_fixture, db_session, monkeypatch):
    uid = f"dev-mobile-{uuid.uuid4().hex[:8]}"

    async def _setup():
        await _seed_user(
            db_session,
            user_id=uid,
            email=f"{uid}@workos.test",
            name="Mobile Impersonated",
            role="employee_mobile",
        )
        await _seed_employee(db_session, user_id=uid, name="Mobile Impersonated")

    db_fixture.run(_setup())
    monkeypatch.setenv("WORKOS_DEV_AUTH_USER_ID", uid)

    me = unauth_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == uid

    requests = unauth_client.get("/api/v1/employee-mobile/requests")
    assert requests.status_code == 200
    assert requests.json() == []

    attendance = unauth_client.get("/api/v1/employee-mobile/attendance")
    assert attendance.status_code == 200
    assert attendance.json() == []


def test_impersonated_user_without_employee_link_gets_employee_link_missing(
    unauth_client, db_fixture, db_session, monkeypatch
):
    uid = f"dev-unlinked-{uuid.uuid4().hex[:8]}"

    async def _setup():
        await _seed_user(
            db_session,
            user_id=uid,
            email=f"{uid}@workos.test",
            name="Unlinked User",
            role="employee_mobile",
        )

    db_fixture.run(_setup())
    monkeypatch.setenv("WORKOS_DEV_AUTH_USER_ID", uid)

    resp = unauth_client.get("/api/v1/employee-mobile/requests")
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"] == "employee_link_missing"


def test_impersonation_does_not_create_user_or_employee(unauth_client, db_fixture, db_session, monkeypatch):
    uid = f"dev-count-{uuid.uuid4().hex[:8]}"

    async def _setup():
        await _seed_user(
            db_session,
            user_id=uid,
            email=f"{uid}@workos.test",
            name="Count User",
            role="employee_mobile",
        )
        return await _count_users(db_session), await _count_employees(db_session)

    before_users, before_employees = db_fixture.run(_setup())
    monkeypatch.setenv("WORKOS_DEV_AUTH_USER_ID", uid)

    assert unauth_client.get("/api/v1/auth/me").status_code == 200
    assert unauth_client.get("/api/v1/employee-mobile/requests").status_code == 403

    async def _after():
        return await _count_users(db_session), await _count_employees(db_session)

    after_users, after_employees = db_fixture.run(_after())
    assert after_users == before_users
    assert after_employees == before_employees


def test_production_blocks_dev_bypass_without_credentials(db_fixture, monkeypatch):
    """Production missing-auth must be 401 (fail-closed).

    Wave 7 failure root cause: this test previously left ``DEBUG`` inherited from
    the agent shell (``DEBUG=true``). Production + DEBUG blocks *startup* via
    ``startup_safety`` before the auth assertion can run — that is the intended
    DEBUG guard, not an auth fail-open. Isolate DEBUG=false for the 401 path.
    """
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("WORKOS_DEV_AUTH_USER_ID", "dev-employee-test-001")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-not-for-production")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///test_placeholder.db")

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/api/v1/auth/me")
            assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_production_debug_true_blocks_startup_not_auth_bypass(monkeypatch):
    """DEBUG=true in production must block startup — never enable missing-auth bypass."""
    from core.startup_safety import run_startup_safety_checks

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///test_placeholder.db")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-not-for-production")

    report = run_startup_safety_checks()
    assert report.overall_status == "BLOCKED"
    debug_check = next(c for c in report.checks if c.name == "DEBUG_MODE_OFF")
    assert debug_check.status == "BLOCKED"

    from core.environment import dev_auth_allowed

    assert dev_auth_allowed() is False


def test_unknown_app_env_denies_dev_auth_bypass(monkeypatch):
    monkeypatch.setenv("APP_ENV", "prodution")  # typo
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    from core.environment import dev_auth_allowed

    assert dev_auth_allowed() is False
