"""
BUILD 17 — Backend Permission Tests.

Tests the permission infrastructure: role resolution, permission matrix,
and the require_permission dependency.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from dependencies.permissions import (
    PERMISSION_MATRIX,
    VALID_ROLES,
    get_role_permissions,
    has_permission,
    require_permission,
    resolve_effective_role,
)


# ---------------------------------------------------------------------------
# Unit tests: resolve_effective_role
# ---------------------------------------------------------------------------


class TestResolveEffectiveRole:
    def test_valid_roles_pass_through(self):
        for role in VALID_ROLES:
            assert resolve_effective_role(role) == role

    def test_user_maps_to_admin(self):
        """Backward compat: existing 'user' role maps to admin."""
        assert resolve_effective_role("user") == "admin"

    def test_unknown_role_maps_to_viewer(self):
        assert resolve_effective_role("unknown_role") == "viewer"
        assert resolve_effective_role("") == "viewer"

    def test_case_sensitive(self):
        """Role matching is case-sensitive."""
        assert resolve_effective_role("Admin") == "viewer"  # not in map
        assert resolve_effective_role("ADMIN") == "viewer"


# ---------------------------------------------------------------------------
# Unit tests: has_permission
# ---------------------------------------------------------------------------


class TestHasPermission:
    def test_admin_has_all_permissions(self):
        for perm in PERMISSION_MATRIX:
            if "admin" in PERMISSION_MATRIX[perm]:
                assert has_permission("admin", perm)

    def test_operator_cannot_access_settings(self):
        assert not has_permission("operator", "settings.view")
        assert not has_permission("operator", "settings.update")

    def test_operator_can_start_tasks(self):
        assert has_permission("operator", "execution.task_start")
        assert has_permission("operator", "execution.task_complete")
        assert has_permission("operator", "execution.task_block")

    def test_operator_cannot_deduct_stock(self):
        assert not has_permission("operator", "inventory.deduct_stock")

    def test_manager_can_deduct_stock(self):
        assert has_permission("manager", "inventory.deduct_stock")

    def test_sales_can_create_orders(self):
        assert has_permission("sales", "order.create_from_quote")

    def test_sales_cannot_cancel_orders(self):
        assert not has_permission("sales", "order.cancel")

    def test_viewer_has_no_permissions(self):
        """Viewer role is not in any permission list."""
        for perm, roles in PERMISSION_MATRIX.items():
            assert "viewer" not in roles

    def test_unknown_permission_returns_false(self):
        assert not has_permission("admin", "nonexistent.permission")

    def test_reports_profit_restricted(self):
        assert has_permission("admin", "reports.view_profit")
        assert has_permission("manager", "reports.view_profit")
        assert not has_permission("sales", "reports.view_profit")
        assert not has_permission("operator", "reports.view_profit")


# ---------------------------------------------------------------------------
# Unit tests: get_role_permissions
# ---------------------------------------------------------------------------


class TestGetRolePermissions:
    def test_admin_has_most_permissions(self):
        admin_perms = get_role_permissions("admin")
        manager_perms = get_role_permissions("manager")
        assert len(admin_perms) >= len(manager_perms)

    def test_operator_limited_permissions(self):
        operator_perms = get_role_permissions("operator")
        assert "execution.task_start" in operator_perms
        assert "execution.task_complete" in operator_perms
        assert "settings.view" not in operator_perms
        assert "order.create_from_quote" not in operator_perms

    def test_unknown_role_empty(self):
        perms = get_role_permissions("nonexistent")
        assert perms == []


# ---------------------------------------------------------------------------
# Integration test: require_permission dependency
# ---------------------------------------------------------------------------


class TestRequirePermission:
    @pytest.mark.asyncio
    async def test_admin_passes_permission_check(self):
        """Admin user should pass any permission check."""
        from schemas.auth import UserResponse

        mock_user = UserResponse(id="u1", email="admin@test.com", role="admin")
        checker = require_permission("settings.update")

        # Simulate the dependency by calling it directly
        result = await checker(current_user=mock_user)
        assert result.id == "u1"

    @pytest.mark.asyncio
    async def test_operator_blocked_from_settings(self):
        """Operator should be blocked from settings."""
        from schemas.auth import UserResponse

        mock_user = UserResponse(id="u2", email="op@test.com", role="operator")
        checker = require_permission("settings.update")

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"] == "permission_denied"

    @pytest.mark.asyncio
    async def test_user_role_backward_compat(self):
        """'user' role maps to admin, should pass all checks."""
        from schemas.auth import UserResponse

        mock_user = UserResponse(id="u3", email="old@test.com", role="user")
        checker = require_permission("settings.update")

        result = await checker(current_user=mock_user)
        assert result.id == "u3"

    @pytest.mark.asyncio
    async def test_manager_can_deduct_stock(self):
        from schemas.auth import UserResponse

        mock_user = UserResponse(id="u4", email="mgr@test.com", role="manager")
        checker = require_permission("inventory.deduct_stock")

        result = await checker(current_user=mock_user)
        assert result.id == "u4"

    @pytest.mark.asyncio
    async def test_sales_cannot_generate_plan(self):
        from schemas.auth import UserResponse

        mock_user = UserResponse(id="u5", email="sales@test.com", role="sales")
        checker = require_permission("execution.plan_generate")

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Permission matrix integrity tests
# ---------------------------------------------------------------------------


class TestPermissionMatrixIntegrity:
    def test_all_roles_in_matrix_are_valid(self):
        """Every role referenced in the matrix must be in VALID_ROLES."""
        for perm, roles in PERMISSION_MATRIX.items():
            for role in roles:
                assert role in VALID_ROLES, f"Invalid role '{role}' in permission '{perm}'"

    def test_admin_has_settings_permissions(self):
        assert has_permission("admin", "settings.view")
        assert has_permission("admin", "settings.update")

    def test_no_duplicate_permissions_in_role(self):
        """Sanity: no role appears twice in the same permission."""
        for perm, roles in PERMISSION_MATRIX.items():
            assert len(roles) == len(set(roles)), f"Duplicate role in '{perm}'"

    def test_hierarchy_admin_superset_of_manager(self):
        """Admin should have all permissions that manager has."""
        manager_perms = set(get_role_permissions("manager"))
        admin_perms = set(get_role_permissions("admin"))
        missing = manager_perms - admin_perms
        assert not missing, f"Admin missing manager permissions: {missing}"