"""
BUILD 20 — Environment Readiness Endpoint Tests.

Tests for GET /api/v1/system/environment-readiness.
"""

import os
from unittest.mock import patch

import pytest

from core.startup_safety import run_startup_safety_checks, EnvironmentReadinessReport


class TestStartupSafetyChecks:
    """Tests for the startup safety check logic."""

    def test_local_env_all_pass(self):
        """In local env, all checks pass (informational)."""
        with patch.dict(os.environ, {"APP_ENV": "local"}, clear=False):
            report = run_startup_safety_checks()
            assert report.environment == "local"
            assert report.overall_status == "PASS"

    def test_development_env_all_pass(self):
        """In development env, all checks pass."""
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
            report = run_startup_safety_checks()
            assert report.environment == "development"
            assert report.overall_status == "PASS"

    def test_production_without_database_url_blocked(self):
        """In production without DATABASE_URL, report is BLOCKED."""
        env = {
            "APP_ENV": "production",
            "JWT_SECRET_KEY": "test-secret-key-for-testing",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("DATABASE_URL", None)
            report = run_startup_safety_checks()
            assert report.environment == "production"
            blocked_names = [c.name for c in report.checks if c.status == "BLOCKED"]
            assert "DATABASE_URL_SET" in blocked_names

    def test_production_without_jwt_secret_blocked(self):
        """In production without JWT_SECRET_KEY, report is BLOCKED."""
        env = {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("JWT_SECRET_KEY", None)
            report = run_startup_safety_checks()
            assert report.environment == "production"
            blocked_names = [c.name for c in report.checks if c.status == "BLOCKED"]
            assert "JWT_SECRET_CONFIGURED" in blocked_names

    def test_production_with_debug_blocked(self):
        """In production with DEBUG=true, report is BLOCKED."""
        env = {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "JWT_SECRET_KEY": "test-secret-key-for-testing",
            "DEBUG": "true",
        }
        with patch.dict(os.environ, env, clear=False):
            report = run_startup_safety_checks()
            blocked_names = [c.name for c in report.checks if c.status == "BLOCKED"]
            assert "DEBUG_MODE_OFF" in blocked_names

    def test_production_with_all_required_passes(self):
        """In production with all required vars, no BLOCKED checks."""
        env = {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "JWT_SECRET_KEY": "test-secret-key-for-testing",
            "OIDC_ISSUER_URL": "https://auth.example.com",
            "DEBUG": "false",
        }
        with patch.dict(os.environ, env, clear=False):
            report = run_startup_safety_checks()
            blocked_names = [c.name for c in report.checks if c.status == "BLOCKED"]
            assert len(blocked_names) == 0

    def test_live_release_without_explicit_runtime_env_is_blocked(self):
        """Deployed builds must not silently fall back to development."""
        env = {
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "JWT_SECRET_KEY": "test-secret-key-for-testing",
            "OIDC_ISSUER_URL": "https://auth.example.com",
            "DEBUG": "false",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("APP_ENV", None)
            os.environ.pop("ENVIRONMENT", None)
            report = run_startup_safety_checks()
            blocked_names = [c.name for c in report.checks if c.status == "BLOCKED"]
            assert report.environment == "live"
            assert report.overall_status == "BLOCKED"
            assert "APP_ENV_SET" in blocked_names
            assert "DEPLOYMENT_ENVIRONMENT_MATCH" in blocked_names

    def test_invalid_runtime_env_is_blocked_for_live_release(self):
        """Invalid runtime env values must fail closed on deployed builds."""
        env = {
            "APP_ENV": "banana",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "JWT_SECRET_KEY": "test-secret-key-for-testing",
            "OIDC_ISSUER_URL": "https://auth.example.com",
            "DEBUG": "false",
        }
        with patch.dict(os.environ, env, clear=False):
            report = run_startup_safety_checks()
            blocked_names = [c.name for c in report.checks if c.status == "BLOCKED"]
            assert report.environment == "live"
            assert report.overall_status == "BLOCKED"
            assert "APP_ENV_SET" in blocked_names
            assert "DEPLOYMENT_ENVIRONMENT_MATCH" in blocked_names

    def test_staging_without_jwt_secret_blocked(self):
        """In staging without JWT_SECRET_KEY, report is BLOCKED."""
        env = {
            "APP_ENV": "staging",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("JWT_SECRET_KEY", None)
            report = run_startup_safety_checks()
            blocked_names = [c.name for c in report.checks if c.status == "BLOCKED"]
            assert "JWT_SECRET_CONFIGURED" in blocked_names

    def test_dev_auth_disabled_in_production(self):
        """Confirm dev auth is reported as disabled in production."""
        env = {"APP_ENV": "production", "DATABASE_URL": "x", "JWT_SECRET_KEY": "x"}
        with patch.dict(os.environ, env, clear=False):
            report = run_startup_safety_checks()
            dev_auth_check = next(
                (c for c in report.checks if c.name == "DEV_AUTH_DISABLED"), None
            )
            assert dev_auth_check is not None
            assert dev_auth_check.status == "PASS"
            assert "disabled" in dev_auth_check.message.lower()

    def test_cors_wildcard_warning_in_production(self):
        """CORS wildcard in production triggers WARNING."""
        env = {
            "APP_ENV": "production",
            "DATABASE_URL": "x",
            "JWT_SECRET_KEY": "x",
            "CORS_ALLOWED_ORIGINS": "*",
        }
        with patch.dict(os.environ, env, clear=False):
            report = run_startup_safety_checks()
            cors_check = next(
                (c for c in report.checks if c.name == "CORS_NOT_WILDCARD"), None
            )
            assert cors_check is not None
            assert cors_check.status == "WARNING"

    def test_report_does_not_expose_secrets(self):
        """Ensure no secret values appear in check messages."""
        env = {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://secret_user:secret_pass@db.example.com/prod",
            "JWT_SECRET_KEY": "super-secret-jwt-key-12345",
            "OIDC_ISSUER_URL": "https://auth.example.com",
        }
        with patch.dict(os.environ, env, clear=False):
            report = run_startup_safety_checks()
            all_messages = " ".join(c.message for c in report.checks)
            assert "secret_user" not in all_messages
            assert "secret_pass" not in all_messages
            assert "super-secret-jwt-key-12345" not in all_messages