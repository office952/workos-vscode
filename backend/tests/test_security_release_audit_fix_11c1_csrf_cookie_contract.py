from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from main import app


class _FakeTokenResponse:
    status_code = 200
    text = "ok"

    @staticmethod
    def json():
        return {
            "id_token": "fake-id-token",
            "access_token": "fake-access-token",
        }


class _FakeAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        return _FakeTokenResponse()


class _FakeAuthService:
    def __init__(self, _db):
        pass

    async def get_and_delete_oidc_state(self, _state):
        return {"nonce": "nonce-123", "code_verifier": "verifier-123"}

    async def get_or_create_user(self, platform_sub, email, name):
        return {
            "id": platform_sub,
            "email": email,
            "name": name,
            "role": "manager",
        }

    async def issue_app_token(self, user):
        return ("fake-app-token", "2099-01-01T00:00:00Z", {})


def test_callback_sets_app_and_csrf_cookie(monkeypatch):
    from routers import auth as auth_router

    monkeypatch.setenv("OIDC_ISSUER_URL", "https://issuer.example")
    monkeypatch.setenv("OIDC_CLIENT_ID", "client-id")
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("FRONTEND_URL", "https://staging.workos.ro")

    monkeypatch.setattr(auth_router, "AuthService", _FakeAuthService)
    monkeypatch.setattr(auth_router, "validate_id_token", AsyncMock(return_value={"sub": "u-1", "email": "u@example.com", "name": "User", "nonce": "nonce-123"}))
    monkeypatch.setattr(auth_router, "_resolve_token_endpoint", lambda: "https://issuer.example/token")
    monkeypatch.setattr(auth_router.httpx, "AsyncClient", _FakeAsyncClient)

    client = TestClient(app)

    response = client.get(
        "/api/v1/auth/callback?code=fake-code&state=fake-state",
        headers={"x-forwarded-proto": "https", "host": "staging.workos.ro"},
        follow_redirects=False,
    )

    assert response.status_code == 302

    set_cookie_headers = response.headers.get_list("set-cookie")
    app_cookie = next((h for h in set_cookie_headers if h.startswith("app_token=")), "")
    csrf_cookie = next((h for h in set_cookie_headers if h.startswith("csrf_token=")), "")

    assert app_cookie
    assert "HttpOnly" in app_cookie

    assert csrf_cookie
    assert "HttpOnly" not in csrf_cookie
    assert "SameSite=lax" in csrf_cookie
    assert "Path=/" in csrf_cookie


def test_logout_clears_app_and_csrf_cookie(monkeypatch):
    from core.config import settings

    for attr in ("oidc_issuer_url", "frontend_url"):
        settings.__dict__.pop(attr, None)

    monkeypatch.setenv("OIDC_ISSUER_URL", "https://issuer.example")
    monkeypatch.setenv("FRONTEND_URL", "https://staging.workos.ro")

    client = TestClient(app)
    client.cookies.set("app_token", "test-token")
    client.cookies.set("csrf_token", "csrf-test")
    response = client.get("/api/v1/auth/logout", headers={"x-forwarded-proto": "https"})

    assert response.status_code == 200
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any("app_token=" in header and "Max-Age=0" in header for header in set_cookie_headers)
    assert any("csrf_token=" in header and "Max-Age=0" in header for header in set_cookie_headers)

    for attr in ("oidc_issuer_url", "frontend_url"):
        settings.__dict__.pop(attr, None)
