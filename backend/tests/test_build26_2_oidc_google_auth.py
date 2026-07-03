"""BUILD 26.2 — Staging OIDC Google Auth Canonical Fix Tests.

Tests cover:
1. Authorization endpoint override vs fallback
2. Token endpoint override vs fallback
3. JWKS URL override vs fallback
4. validate_id_token accepts access_token parameter
5. Callback redirect targets FRONTEND_URL, not backend URL
6. Static safety: no secrets, no dev-auth in staging
"""

import os
from unittest.mock import AsyncMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Keys that must be explicitly controlled in fallback tests
_OVERRIDE_KEYS = [
    "OIDC_AUTHORIZATION_ENDPOINT",
    "OIDC_TOKEN_ENDPOINT",
    "OIDC_JWKS_URL",
    "FRONTEND_URL",
]

# Corresponding settings cache attribute names (lowercase)
_SETTINGS_CACHE_ATTRS = [
    "oidc_authorization_endpoint",
    "oidc_token_endpoint",
    "oidc_jwks_url",
    "frontend_url",
]


def _clean_env(**kwargs):
    """Context manager that sets exactly the given env vars and removes override keys not specified.

    Also clears the settings object's __dict__ cache for the affected attributes
    to prevent stale cached values from prior tests.
    """
    env_to_set = dict(kwargs)

    class _Ctx:
        def __enter__(self):
            self._removed = {}
            self._original = {}
            self._cached = {}

            # Clear settings cache for override attributes
            from core.config import settings
            for attr in _SETTINGS_CACHE_ATTRS:
                if attr in settings.__dict__:
                    self._cached[attr] = settings.__dict__.pop(attr)

            # Remove env keys that should not be present
            for k in _OVERRIDE_KEYS:
                if k not in kwargs and k in os.environ:
                    self._removed[k] = os.environ.pop(k)

            # Set keys
            for k, v in env_to_set.items():
                if k in os.environ:
                    self._original[k] = os.environ[k]
                os.environ[k] = v

            return self

        def __exit__(self, *args):
            # Restore removed env vars
            for k, v in self._removed.items():
                os.environ[k] = v
            # Restore or remove set keys
            for k in env_to_set:
                if k in self._original:
                    os.environ[k] = self._original[k]
                elif k in os.environ:
                    del os.environ[k]
            # Restore settings cache
            from core.config import settings
            for attr, val in self._cached.items():
                settings.__dict__[attr] = val
            # Also clear any newly cached values from this test
            for attr in _SETTINGS_CACHE_ATTRS:
                settings.__dict__.pop(attr, None)

    return _Ctx()


# ---------------------------------------------------------------------------
# 1. Authorization Endpoint Override
# ---------------------------------------------------------------------------


class TestAuthorizationEndpoint:
    """OIDC_AUTHORIZATION_ENDPOINT override and fallback."""

    def test_uses_override_when_set(self):
        """Auth URL uses OIDC_AUTHORIZATION_ENDPOINT when set."""
        with _clean_env(
            OIDC_ISSUER_URL="https://accounts.google.com",
            OIDC_CLIENT_ID="test-client",
            OIDC_SCOPE="openid email profile",
            OIDC_AUTHORIZATION_ENDPOINT="https://accounts.google.com/o/oauth2/v2/auth",
        ):
            from core.auth import build_authorization_url

            url = build_authorization_url(state="s", nonce="n")
            assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
            assert "client_id=test-client" in url

    def test_falls_back_to_issuer_authorize(self):
        """Auth URL falls back to issuer + /authorize when endpoint env is absent."""
        with _clean_env(
            OIDC_ISSUER_URL="https://accounts.google.com",
            OIDC_CLIENT_ID="test-client",
            OIDC_SCOPE="openid email profile",
        ):
            from core.auth import _resolve_authorization_endpoint

            result = _resolve_authorization_endpoint()
            assert result == "https://accounts.google.com/authorize"


# ---------------------------------------------------------------------------
# 2. Token Endpoint Override
# ---------------------------------------------------------------------------


class TestTokenEndpoint:
    """OIDC_TOKEN_ENDPOINT override and fallback."""

    def test_uses_override_when_set(self):
        """Token exchange uses OIDC_TOKEN_ENDPOINT when set."""
        with _clean_env(
            OIDC_ISSUER_URL="https://accounts.google.com",
            OIDC_TOKEN_ENDPOINT="https://oauth2.googleapis.com/token",
        ):
            from core.auth import _resolve_token_endpoint

            result = _resolve_token_endpoint()
            assert result == "https://oauth2.googleapis.com/token"

    def test_falls_back_to_issuer_token(self):
        """Token exchange falls back to issuer + /token when endpoint env is absent."""
        with _clean_env(
            OIDC_ISSUER_URL="https://accounts.google.com",
        ):
            from core.auth import _resolve_token_endpoint

            result = _resolve_token_endpoint()
            assert result == "https://accounts.google.com/token"


# ---------------------------------------------------------------------------
# 3. JWKS URL Override
# ---------------------------------------------------------------------------


class TestJwksUrl:
    """OIDC_JWKS_URL override and fallback."""

    def test_uses_override_when_set(self):
        """JWKS fetch uses OIDC_JWKS_URL when set."""
        with _clean_env(
            OIDC_ISSUER_URL="https://accounts.google.com",
            OIDC_JWKS_URL="https://www.googleapis.com/oauth2/v3/certs",
        ):
            from core.auth import _resolve_jwks_url

            result = _resolve_jwks_url()
            assert result == "https://www.googleapis.com/oauth2/v3/certs"

    def test_falls_back_to_issuer_jwks(self):
        """JWKS fetch falls back to issuer + /.well-known/jwks.json when env is absent."""
        with _clean_env(
            OIDC_ISSUER_URL="https://accounts.google.com",
        ):
            from core.auth import _resolve_jwks_url

            result = _resolve_jwks_url()
            assert result == "https://accounts.google.com/.well-known/jwks.json"


# ---------------------------------------------------------------------------
# 4. validate_id_token accepts access_token
# ---------------------------------------------------------------------------


class TestValidateIdTokenAccessToken:
    """validate_id_token signature accepts optional access_token."""

    def test_signature_accepts_access_token(self):
        """validate_id_token has access_token parameter with default None."""
        import inspect

        from core.auth import validate_id_token

        sig = inspect.signature(validate_id_token)
        params = list(sig.parameters.keys())
        assert "id_token" in params
        assert "access_token" in params
        # Default should be None
        assert sig.parameters["access_token"].default is None

    @pytest.mark.asyncio
    async def test_access_token_passed_to_decode(self):
        """validate_id_token passes access_token into JWT decode kwargs when provided."""
        fake_header = {"kid": "test-kid", "alg": "RS256"}
        fake_jwks = {
            "keys": [
                {
                    "kid": "test-kid",
                    "kty": "RSA",
                    "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
                    "e": "AQAB",
                }
            ]
        }

        with _clean_env(
            OIDC_ISSUER_URL="https://accounts.google.com",
            OIDC_CLIENT_ID="test-client",
        ):
            with patch("core.auth.get_jwks", new_callable=AsyncMock, return_value=fake_jwks):
                with patch("core.auth.jwt") as mock_jwt:
                    mock_jwt.get_unverified_header.return_value = fake_header
                    mock_jwt.decode.return_value = {"sub": "123", "nonce": "n"}

                    from core.auth import validate_id_token

                    result = await validate_id_token("fake.id.token", access_token="fake-access-token")

                    # Verify jwt.decode was called with access_token in kwargs
                    call_kwargs = mock_jwt.decode.call_args
                    assert call_kwargs is not None
                    # access_token should be in the keyword arguments
                    if call_kwargs.kwargs:
                        assert call_kwargs.kwargs.get("access_token") == "fake-access-token"
                    else:
                        # Positional + keyword mixed
                        all_kwargs = call_kwargs[1] if len(call_kwargs) > 1 else {}
                        assert all_kwargs.get("access_token") == "fake-access-token"


# ---------------------------------------------------------------------------
# 5. Callback Redirect to FRONTEND_URL
# ---------------------------------------------------------------------------


class TestCallbackRedirectTarget:
    """Successful callback redirects to FRONTEND_URL + /auth/callback."""

    def test_resolve_frontend_url_uses_config(self):
        """_resolve_frontend_url returns FRONTEND_URL when configured."""
        with _clean_env(FRONTEND_URL="https://staging.workos.ro"):
            from routers.auth import _resolve_frontend_url

            result = _resolve_frontend_url("https://api-staging.workos.ro")
            assert result == "https://staging.workos.ro"

    def test_resolve_frontend_url_fallback(self):
        """_resolve_frontend_url falls back to backend_url when FRONTEND_URL is absent."""
        with _clean_env(OIDC_ISSUER_URL="https://accounts.google.com"):
            # FRONTEND_URL is explicitly removed by _clean_env
            from routers.auth import _resolve_frontend_url

            result = _resolve_frontend_url("https://api-staging.workos.ro")
            assert result == "https://api-staging.workos.ro"

    def test_resolve_frontend_url_strips_trailing_slash(self):
        """_resolve_frontend_url strips trailing slash from FRONTEND_URL."""
        with _clean_env(FRONTEND_URL="https://staging.workos.ro/"):
            from routers.auth import _resolve_frontend_url

            result = _resolve_frontend_url("https://api-staging.workos.ro")
            assert result == "https://staging.workos.ro"


# ---------------------------------------------------------------------------
# 6. Static Safety
# ---------------------------------------------------------------------------


class TestStaticSafety:
    """No secrets, no dev-auth in staging config."""

    def test_env_example_has_no_real_secrets(self):
        """Verify .env.example contains only placeholders, no real secrets."""
        import pathlib

        env_example = pathlib.Path(__file__).parent.parent / ".env.example"
        content = env_example.read_text()

        # Should not contain actual Google client IDs or secrets
        assert "GOCSPX-" not in content  # Google client secret prefix
        assert ".apps.googleusercontent.com" not in content
        # Should contain placeholder markers
        assert "<google-client-id>" in content
        assert "<google-client-secret>" in content
        assert "<generated-secret>" in content

    def test_env_example_documents_all_oidc_vars(self):
        """Verify .env.example documents all required OIDC variables."""
        import pathlib

        env_example = pathlib.Path(__file__).parent.parent / ".env.example"
        content = env_example.read_text()

        required_vars = [
            "OIDC_ISSUER_URL",
            "OIDC_CLIENT_ID",
            "OIDC_CLIENT_SECRET",
            "OIDC_SCOPE",
            "OIDC_AUTHORIZATION_ENDPOINT",
            "OIDC_TOKEN_ENDPOINT",
            "OIDC_JWKS_URL",
            "JWT_SECRET_KEY",
            "JWT_ALGORITHM",
            "FRONTEND_URL",
        ]
        for var in required_vars:
            assert var in content, f"Missing required variable in .env.example: {var}"

    def test_env_example_dev_auth_staging_note(self):
        """Verify .env.example notes DEV_AUTH_ENABLED must be false in staging."""
        import pathlib

        env_example = pathlib.Path(__file__).parent.parent / ".env.example"
        content = env_example.read_text()

        assert "DEV_AUTH_ENABLED" in content
        assert "false in staging" in content.lower() or "false in staging/production" in content.lower()


# ---------------------------------------------------------------------------
# 7. OIDC Scope Configuration
# ---------------------------------------------------------------------------


class TestOidcScope:
    """OIDC scope is required and configurable."""

    def test_build_authorization_url_includes_scope(self):
        """Authorization URL includes configured OIDC_SCOPE."""
        with _clean_env(
            OIDC_ISSUER_URL="https://accounts.google.com",
            OIDC_CLIENT_ID="test-client",
            OIDC_SCOPE="openid email profile",
            OIDC_AUTHORIZATION_ENDPOINT="https://accounts.google.com/o/oauth2/v2/auth",
        ):
            from core.auth import build_authorization_url

            url = build_authorization_url(state="s", nonce="n")
            assert "scope=openid+email+profile" in url or "scope=openid%20email%20profile" in url


# ---------------------------------------------------------------------------
# 8. Integration: Full endpoint resolution with Google config
# ---------------------------------------------------------------------------


class TestGoogleIntegration:
    """Verify all three endpoints resolve correctly with Google-specific overrides."""

    def test_all_google_endpoints_resolve(self):
        """With Google overrides set, all endpoints resolve to Google-specific URLs."""
        with _clean_env(
            OIDC_ISSUER_URL="https://accounts.google.com",
            OIDC_AUTHORIZATION_ENDPOINT="https://accounts.google.com/o/oauth2/v2/auth",
            OIDC_TOKEN_ENDPOINT="https://oauth2.googleapis.com/token",
            OIDC_JWKS_URL="https://www.googleapis.com/oauth2/v3/certs",
        ):
            from core.auth import (
                _resolve_authorization_endpoint,
                _resolve_jwks_url,
                _resolve_token_endpoint,
            )

            assert _resolve_authorization_endpoint() == "https://accounts.google.com/o/oauth2/v2/auth"
            assert _resolve_token_endpoint() == "https://oauth2.googleapis.com/token"
            assert _resolve_jwks_url() == "https://www.googleapis.com/oauth2/v3/certs"

    def test_all_endpoints_fallback_without_overrides(self):
        """Without overrides, all endpoints derive from issuer URL."""
        with _clean_env(
            OIDC_ISSUER_URL="https://accounts.google.com",
        ):
            from core.auth import (
                _resolve_authorization_endpoint,
                _resolve_jwks_url,
                _resolve_token_endpoint,
            )

            assert _resolve_authorization_endpoint() == "https://accounts.google.com/authorize"
            assert _resolve_token_endpoint() == "https://accounts.google.com/token"
            assert _resolve_jwks_url() == "https://accounts.google.com/.well-known/jwks.json"