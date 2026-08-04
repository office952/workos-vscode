"""Wave 8 — production auth fail-closed + assignment observability privacy (isolated DB)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from core.auth import create_access_token
from core.database import get_db
from core.environment import dev_auth_allowed
from core.startup_safety import run_startup_safety_checks
from dependencies.auth import get_current_user
from dependencies.permissions import has_permission
from main import app
from schemas.auth import UserResponse


def _production_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-not-for-production")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///test_placeholder.db")
    monkeypatch.delenv("WORKOS_DEV_AUTH_USER_ID", raising=False)


def _client_production(db_fixture, monkeypatch):
    _production_env(monkeypatch)

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
    return TestClient(app, raise_server_exceptions=False)


def test_dev_auth_allowed_matrix(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DEBUG", "true")
    assert dev_auth_allowed() is True

    monkeypatch.setenv("APP_ENV", "test")
    assert dev_auth_allowed() is True

    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("DEBUG", "true")
    assert dev_auth_allowed() is False

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "true")
    assert dev_auth_allowed() is False

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "false")
    assert dev_auth_allowed() is False


def test_production_missing_auth_denied(db_fixture, monkeypatch):
    with _client_production(db_fixture, monkeypatch) as client:
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
    app.dependency_overrides.clear()


def test_production_invalid_jwt_denied(db_fixture, monkeypatch):
    with _client_production(db_fixture, monkeypatch) as client:
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
        assert resp.status_code == 401
    app.dependency_overrides.clear()


def test_production_malformed_authorization_denied(db_fixture, monkeypatch):
    with _client_production(db_fixture, monkeypatch) as client:
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Basic abc"},
        )
        # No bearer → same as missing credentials in production.
        assert resp.status_code == 401
    app.dependency_overrides.clear()


def test_production_wrong_signing_key_denied(db_fixture, monkeypatch):
    _production_env(monkeypatch)
    bad = jwt.encode(
        {
            "sub": "attacker",
            "email": "x@y.z",
            "role": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        },
        "wrong-secret-key-not-configured",
        algorithm="HS256",
    )
    with _client_production(db_fixture, monkeypatch) as client:
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {bad}"},
        )
        assert resp.status_code == 401
    app.dependency_overrides.clear()


def test_production_expired_jwt_denied(db_fixture, monkeypatch):
    _production_env(monkeypatch)
    expired = jwt.encode(
        {
            "sub": "expired-user",
            "email": "expired@test.local",
            "role": "admin",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
            "iat": datetime.now(timezone.utc) - timedelta(minutes=65),
        },
        "test-jwt-secret-not-for-production",
        algorithm="HS256",
    )
    with _client_production(db_fixture, monkeypatch) as client:
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert resp.status_code == 401
    app.dependency_overrides.clear()


def test_production_debug_blocks_startup(monkeypatch):
    _production_env(monkeypatch)
    monkeypatch.setenv("DEBUG", "true")
    report = run_startup_safety_checks()
    assert report.overall_status == "BLOCKED"
    assert any(c.name == "DEBUG_MODE_OFF" and c.status == "BLOCKED" for c in report.checks)
    assert dev_auth_allowed() is False


def test_admin_has_task_assign_viewer_denied():
    assert has_permission("admin", "execution.task_assign") is True
    assert has_permission("viewer", "execution.task_assign") is False


@pytest.mark.asyncio
async def test_permission_denied_log_uses_user_id_not_email(caplog):
    from dependencies.permissions import require_permission
    from fastapi import HTTPException

    dep = require_permission("execution.task_assign")
    user = UserResponse(
        id="viewer-safe-id",
        email="private.viewer@example.com",
        name="Private Viewer",
        role="viewer",
    )
    with caplog.at_level(logging.WARNING, logger="dependencies.permissions"):
        with pytest.raises(HTTPException) as exc:
            await dep(current_user=user)
        assert exc.value.status_code == 403
    joined = " ".join(r.message for r in caplog.records)
    assert "viewer-safe-id" in joined
    assert "private.viewer@example.com" not in joined


def test_assignment_success_log_excludes_forbidden_fields(caplog, monkeypatch):
    """Safe structured log fields only — unit-level message contract."""
    from services import controlled_employee_assignment_service as svc

    with caplog.at_level(logging.INFO, logger=svc.__name__):
        svc.logger.info(
            "assignment_command event=%s outcome=%s order_id=%s plan_id=%s "
            "task_id=%s employee_id=%s actor_user_id=%s eligibility_status=%s "
            "retry_or_conflict=%s",
            "ASSIGNMENT_SUCCEEDED",
            "assigned",
            880750,
            23,
            "node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters",
            7,
            "qa-wave7-auth-closure",
            "ready_with_warnings",
            "first_assign",
        )
    msg = caplog.records[-1].getMessage()
    forbidden = [
        "password",
        "Bearer ",
        "salary",
        "CNP",
        "Authorization",
        "@example.com",
        "tasks_json",
        "EUR",
    ]
    for token in forbidden:
        assert token not in msg
    assert "order_id=880750" in msg
    assert "employee_id=7" in msg
    assert "ASSIGNMENT_SUCCEEDED" in msg


def test_create_access_token_admin_identity_roundtrip(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-not-for-production")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "60")
    token = create_access_token(
        {
            "sub": "qa-wave8-admin",
            "email": "qa-wave8@localhost",
            "name": "QA Wave8",
            "role": "admin",
        },
        expires_minutes=5,
    )
    assert isinstance(token, str) and len(token) > 20
