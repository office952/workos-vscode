from fastapi.testclient import TestClient

from main import app


def test_logout_clears_app_and_csrf_cookie_and_returns_redirect_url(monkeypatch):
    from core.config import settings

    for attr in ("oidc_issuer_url", "frontend_url"):
        settings.__dict__.pop(attr, None)

    monkeypatch.setenv("OIDC_ISSUER_URL", "https://issuer.example")
    monkeypatch.setenv("FRONTEND_URL", "https://staging.workos.ro")

    client = TestClient(app)
    client.cookies.set("app_token", "test-token")
    client.cookies.set("csrf_token", "csrf-token")
    response = client.get("/api/v1/auth/logout", headers={"x-forwarded-proto": "https"})

    assert response.status_code == 200
    assert response.json()["redirect_url"] == "https://issuer.example/logout?post_logout_redirect_uri=https%3A%2F%2Fstaging.workos.ro%2Fauth%2Flogout"

    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any("app_token=" in header and "Max-Age=0" in header for header in set_cookie_headers)
    assert any("csrf_token=" in header and "Max-Age=0" in header for header in set_cookie_headers)
    assert any("Path=/" in header for header in set_cookie_headers)

    for attr in ("oidc_issuer_url", "frontend_url"):
        settings.__dict__.pop(attr, None)