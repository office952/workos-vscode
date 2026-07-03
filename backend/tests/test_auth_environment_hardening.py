"""
BUILD 20 — Auth Environment Hardening Tests.

Verifies that dev auth fallback behavior is correctly gated by environment.
"""

import os
from unittest.mock import patch

import pytest

from core.environment import (
    get_runtime_environment,
    is_development_environment,
    is_staging_environment,
    is_production_environment,
    dev_auth_allowed,
)
from dependencies.permissions import resolve_effective_role, has_permission


# ---------------------------------------------------------------------------
# Environment classification tests
# ---------------------------------------------------------------------------


class TestEnvironmentClassification:
    """Tests for core.environment module."""

    def test_default_environment_is_development(self):
        """Without APP_ENV, defaults to development."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove APP_ENV and ENVIRONMENT if present
            os.environ.pop("APP_ENV", None)
            os.environ.pop("ENVIRONMENT", None)
            assert get_runtime_environment() == "development"

    def test_app_env_local(self):
        with patch.dict(os.environ, {"APP_ENV": "local"}, clear=False):
            assert get_runtime_environment() == "local"

    def test_app_env_development(self):
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
            assert get_runtime_environment() == "development"

    def test_app_env_staging(self):
        with patch.dict(os.environ, {"APP_ENV": "staging"}, clear=False):
            assert get_runtime_environment() == "staging"

    def test_app_env_production(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            assert get_runtime_environment() == "production"

    def test_app_env_test(self):
        with patch.dict(os.environ, {"APP_ENV": "test"}, clear=False):
            assert get_runtime_environment() == "test"

    def test_unknown_app_env_defaults_to_development(self):
        with patch.dict(os.environ, {"APP_ENV": "banana"}, clear=False):
            assert get_runtime_environment() == "development"

    def test_environment_fallback_var(self):
        """ENVIRONMENT var is used if APP_ENV is not set."""
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}, clear=False):
            os.environ.pop("APP_ENV", None)
            assert get_runtime_environment() == "staging"

    def test_app_env_takes_precedence_over_environment(self):
        with patch.dict(os.environ, {"APP_ENV": "production", "ENVIRONMENT": "local"}, clear=False):
            assert get_runtime_environment() == "production"

    def test_is_development_for_local(self):
        with patch.dict(os.environ, {"APP_ENV": "local"}, clear=False):
            assert is_development_environment() is True

    def test_is_development_for_test(self):
        with patch.dict(os.environ, {"APP_ENV": "test"}, clear=False):
            assert is_development_environment() is True

    def test_is_development_for_development(self):
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
            assert is_development_environment() is True

    def test_is_not_development_for_staging(self):
        with patch.dict(os.environ, {"APP_ENV": "staging"}, clear=False):
            assert is_development_environment() is False

    def test_is_not_development_for_production(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            assert is_development_environment() is False

    def test_is_staging(self):
        with patch.dict(os.environ, {"APP_ENV": "staging"}, clear=False):
            assert is_staging_environment() is True

    def test_is_production(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            assert is_production_environment() is True

    def test_dev_auth_allowed_in_local(self):
        with patch.dict(os.environ, {"APP_ENV": "local"}, clear=False):
            assert dev_auth_allowed() is True

    def test_dev_auth_allowed_in_development(self):
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
            assert dev_auth_allowed() is True

    def test_dev_auth_allowed_in_test(self):
        with patch.dict(os.environ, {"APP_ENV": "test"}, clear=False):
            assert dev_auth_allowed() is True

    def test_dev_auth_blocked_in_staging(self):
        with patch.dict(os.environ, {"APP_ENV": "staging"}, clear=False):
            assert dev_auth_allowed() is False

    def test_dev_auth_blocked_in_production(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            assert dev_auth_allowed() is False


# ---------------------------------------------------------------------------
# Role resolution hardening tests
# ---------------------------------------------------------------------------


class TestRoleResolutionHardening:
    """Tests for resolve_effective_role with environment gating."""

    def test_role_user_maps_to_admin_in_dev(self):
        """In dev environment, role=user maps to admin (backward compat)."""
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
            assert resolve_effective_role("user") == "admin"

    def test_role_user_maps_to_admin_in_local(self):
        """In local environment, role=user maps to admin (backward compat)."""
        with patch.dict(os.environ, {"APP_ENV": "local"}, clear=False):
            assert resolve_effective_role("user") == "admin"

    def test_role_user_maps_to_admin_in_test(self):
        """In test environment, role=user maps to admin (backward compat)."""
        with patch.dict(os.environ, {"APP_ENV": "test"}, clear=False):
            assert resolve_effective_role("user") == "admin"

    def test_role_user_does_NOT_map_to_admin_in_staging(self):
        """In staging, role=user maps to viewer (fail-closed)."""
        with patch.dict(os.environ, {"APP_ENV": "staging"}, clear=False):
            assert resolve_effective_role("user") == "viewer"

    def test_role_user_does_NOT_map_to_admin_in_production(self):
        """In production, role=user maps to viewer (fail-closed)."""
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            assert resolve_effective_role("user") == "viewer"

    def test_unknown_role_maps_to_viewer_in_dev(self):
        """Unknown role always maps to viewer."""
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
            assert resolve_effective_role("banana") == "viewer"

    def test_unknown_role_maps_to_viewer_in_staging(self):
        with patch.dict(os.environ, {"APP_ENV": "staging"}, clear=False):
            assert resolve_effective_role("banana") == "viewer"

    def test_unknown_role_maps_to_viewer_in_production(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            assert resolve_effective_role("banana") == "viewer"

    def test_missing_role_empty_string_maps_to_viewer_in_production(self):
        """Empty role string maps to viewer."""
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            assert resolve_effective_role("") == "viewer"

    def test_valid_admin_role_works_in_all_environments(self):
        """Explicit admin role is always valid."""
        for env in ("local", "development", "test", "staging", "production"):
            with patch.dict(os.environ, {"APP_ENV": env}, clear=False):
                assert resolve_effective_role("admin") == "admin"

    def test_valid_manager_role_works_in_all_environments(self):
        """Explicit manager role is always valid."""
        for env in ("local", "development", "test", "staging", "production"):
            with patch.dict(os.environ, {"APP_ENV": env}, clear=False):
                assert resolve_effective_role("manager") == "manager"

    def test_valid_operator_role_works_in_all_environments(self):
        """Explicit operator role is always valid."""
        for env in ("local", "development", "test", "staging", "production"):
            with patch.dict(os.environ, {"APP_ENV": env}, clear=False):
                assert resolve_effective_role("operator") == "operator"

    def test_valid_sales_role_works_in_all_environments(self):
        """Explicit sales role is always valid."""
        for env in ("local", "development", "test", "staging", "production"):
            with patch.dict(os.environ, {"APP_ENV": env}, clear=False):
                assert resolve_effective_role("sales") == "sales"

    def test_valid_viewer_role_works_in_all_environments(self):
        """Explicit viewer role is always valid."""
        for env in ("local", "development", "test", "staging", "production"):
            with patch.dict(os.environ, {"APP_ENV": env}, clear=False):
                assert resolve_effective_role("viewer") == "viewer"


# ---------------------------------------------------------------------------
# Permission enforcement tests
# ---------------------------------------------------------------------------


class TestPermissionEnforcement:
    """Tests that permission matrix works correctly with hardened roles."""

    def test_admin_has_settings_view(self):
        assert has_permission("admin", "settings.view") is True

    def test_viewer_cannot_access_settings(self):
        assert has_permission("viewer", "settings.view") is False

    def test_viewer_cannot_deduct_stock(self):
        assert has_permission("viewer", "inventory.deduct_stock") is False

    def test_viewer_cannot_cancel_order(self):
        assert has_permission("viewer", "order.cancel") is False

    def test_viewer_cannot_invalidate_reality(self):
        assert has_permission("viewer", "reality.invalidate") is False

    def test_role_user_in_production_cannot_access_admin_endpoints(self):
        """role=user in production resolves to viewer, which has no admin access."""
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            effective = resolve_effective_role("user")
            assert effective == "viewer"
            assert has_permission(effective, "settings.view") is False
            assert has_permission(effective, "admin.manage_users") is False
            assert has_permission(effective, "order.cancel") is False
            assert has_permission(effective, "execution.plan_generate") is False
            assert has_permission(effective, "inventory.deduct_stock") is False
            assert has_permission(effective, "reality.invalidate") is False

    def test_role_user_in_dev_has_admin_access(self):
        """role=user in dev resolves to admin, which has full access."""
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
            effective = resolve_effective_role("user")
            assert effective == "admin"
            assert has_permission(effective, "settings.view") is True
            assert has_permission(effective, "admin.manage_users") is True