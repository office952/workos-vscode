"""
SECURITY_RELEASE_AUDIT_FIX_02 — AIHub SSRF and local file-read lockdown tests.
"""

import pytest
from fastapi.testclient import TestClient

from services.aihub import (
    AIHubService,
    InvalidAudioInputError,
    InvalidRemoteFetchError,
)


def _build_service(monkeypatch) -> AIHubService:
    monkeypatch.setenv("APP_AI_BASE_URL", "https://api.example.ai")
    monkeypatch.setenv("APP_AI_KEY", "test-key")
    return AIHubService()


@pytest.mark.asyncio
async def test_remote_url_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AIHUB_REMOTE_FETCH_ENABLED", raising=False)
    monkeypatch.delenv("AIHUB_REMOTE_FETCH_ALLOWLIST", raising=False)

    with pytest.raises(InvalidAudioInputError, match="disabled by AIHub security policy"):
        service = _build_service(monkeypatch)
        await service._audio_str_to_upload_file("http://example.com/audio.mp3")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/audio.mp3",
        "http://localhost/audio.mp3",
        "http://169.254.169.254/latest/meta-data",
    ],
)
async def test_forbidden_ssrf_targets_are_blocked(url, monkeypatch):
    monkeypatch.setenv("AIHUB_REMOTE_FETCH_ENABLED", "true")
    monkeypatch.setenv("AIHUB_REMOTE_FETCH_ALLOWLIST", "localhost,127.0.0.1,169.254.169.254")

    with pytest.raises(InvalidRemoteFetchError):
        AIHubService._assert_remote_url_allowed(url)


@pytest.mark.asyncio
async def test_redirect_to_private_ip_is_blocked(monkeypatch):
    monkeypatch.setenv("AIHUB_REMOTE_FETCH_ENABLED", "true")
    monkeypatch.setenv("AIHUB_REMOTE_FETCH_ALLOWLIST", "93.184.216.34,127.0.0.1")

    # Keep test deterministic: avoid DNS dependence for the initial host.
    monkeypatch.setattr(AIHubService, "_assert_host_resolves_to_safe_public_ips", classmethod(lambda cls, host: None))

    class _MockResponse:
        def __init__(self, status_code, headers=None, body=b""):
            self.status_code = status_code
            self.headers = headers or {}
            self._body = body

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError("http error")

        async def aiter_bytes(self):
            if self._body:
                yield self._body

    class _MockClient:
        def __init__(self, *args, **kwargs):
            self.calls = 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url):
            self.calls += 1
            if self.calls == 1:
                return _MockResponse(302, headers={"location": "http://127.0.0.1/internal"})
            return _MockResponse(200, body=b"ok")

    import services.aihub as aihub_module

    monkeypatch.setattr(aihub_module.httpx, "AsyncClient", _MockClient)

    with pytest.raises(InvalidRemoteFetchError):
        await AIHubService._download_remote_bytes("http://93.184.216.34/source")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "audio_source",
    [
        "/etc/passwd",
        "C:/Windows/System32/drivers/etc/hosts",
        "../secret",
        "file:///etc/passwd",
    ],
)
async def test_local_file_sources_are_blocked(audio_source, monkeypatch):
    with pytest.raises(InvalidAudioInputError):
        service = _build_service(monkeypatch)
        await service._audio_str_to_upload_file(audio_source)


def test_aihub_endpoint_requires_explicit_permission(db_fixture, monkeypatch):
    from core.database import get_db
    from dependencies.auth import get_current_user
    from main import app
    from schemas.auth import UserResponse

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _viewer_user():
        return UserResponse(
            id="viewer-user",
            email="viewer@example.com",
            name="Viewer",
            role="viewer",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _viewer_user
    monkeypatch.setenv("APP_ENV", "test")

    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/api/v1/aihub/gentxt",
                json={
                    "messages": [{"role": "user", "content": "hello"}],
                    "stream": False,
                },
            )

        assert response.status_code == 403
        body = response.json()
        assert body["detail"]["error"] == "permission_denied"
        assert body["detail"]["permission"] == "aihub.execute"
    finally:
        app.dependency_overrides.clear()
