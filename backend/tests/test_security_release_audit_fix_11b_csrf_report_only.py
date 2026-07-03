import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from dependencies.auth import get_current_user


@pytest.fixture
def csrf_report_client(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://testserver")

    def _fake_decode_access_token(_token: str):
        return {
            "sub": "fix11b-user",
            "email": "fix11b@example.com",
            "role": "admin",
        }

    monkeypatch.setattr("dependencies.auth.decode_access_token", _fake_decode_access_token)

    app = FastAPI()

    @app.middleware("http")
    async def _csrf_report_header(request, call_next):
        response = await call_next(request)
        status_value = getattr(request.state, "csrf_report_only", None)
        reasons = getattr(request.state, "csrf_report_only_reasons", None)
        if status_value:
            header_value = status_value
            if reasons:
                header_value = f"{status_value}:{','.join(reasons)}"
            response.headers["X-CSRF-Report-Only"] = header_value
        return response

    @app.post("/mutate")
    async def mutate(_user=Depends(get_current_user)):
        return {"ok": True}

    @app.post("/api/v1/auth/token/exchange")
    async def token_exchange_shape(_user=Depends(get_current_user)):
        return {"ok": True}

    return TestClient(app)


def test_cookie_auth_missing_csrf_is_reported_not_blocked(csrf_report_client):
    response = csrf_report_client.post("/mutate", cookies={"app_token": "cookie-token"})

    assert response.status_code == 200
    assert response.headers["X-CSRF-Report-Only"].startswith("missing:")
    assert "csrf_cookie_missing" in response.headers["X-CSRF-Report-Only"]
    assert "csrf_header_missing" in response.headers["X-CSRF-Report-Only"]


def test_cookie_auth_invalid_mismatch_is_reported_not_blocked(csrf_report_client):
    response = csrf_report_client.post(
        "/mutate",
        cookies={
            "app_token": "cookie-token",
            "csrf_token": "cookie-csrf",
        },
        headers={
            "x-csrf-token": "header-csrf",
            "origin": "http://testserver",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-CSRF-Report-Only"].startswith("invalid:")
    assert "csrf_mismatch" in response.headers["X-CSRF-Report-Only"]


def test_cookie_auth_valid_csrf_marks_passed(csrf_report_client):
    response = csrf_report_client.post(
        "/mutate",
        cookies={
            "app_token": "cookie-token",
            "csrf_token": "same-token",
        },
        headers={
            "x-csrf-token": "same-token",
            "origin": "http://testserver",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-CSRF-Report-Only"] == "passed"


def test_bearer_auth_skips_csrf_requirement(csrf_report_client):
    response = csrf_report_client.post(
        "/mutate",
        headers={
            "authorization": "Bearer test-bearer",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-CSRF-Report-Only"] == "skipped_bearer:auth_source_bearer"


def test_token_exchange_path_is_explicitly_excluded(csrf_report_client):
    response = csrf_report_client.post(
        "/api/v1/auth/token/exchange",
        cookies={
            "app_token": "cookie-token",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-CSRF-Report-Only"] == "skipped_excluded:path_excluded"
