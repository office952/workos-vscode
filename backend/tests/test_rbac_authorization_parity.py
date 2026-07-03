"""
BUILD 24 — RBAC Authorization Parity Hardening Tests.

Tests that:
1. Mutation endpoints in quotes, product_templates, inventory_materials,
   execution materials, and product_blueprint_dossier now require explicit
   permissions via require_permission().
2. Insufficient roles are blocked with HTTP 403.
3. Valid roles still succeed (no regression).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from dependencies.permissions import (
    PERMISSION_MATRIX,
    has_permission,
    resolve_effective_role,
    require_permission,
    VALID_ROLES,
)


# ---------------------------------------------------------------------------
# P1-001: Permission matrix completeness
# ---------------------------------------------------------------------------

class TestPermissionMatrixCompleteness:
    """Verify that the new permissions added in BUILD 24 exist in the matrix."""

    def test_quote_create_exists(self):
        assert "quote.create" in PERMISSION_MATRIX

    def test_quote_update_exists(self):
        assert "quote.update" in PERMISSION_MATRIX

    def test_quote_delete_exists(self):
        assert "quote.delete" in PERMISSION_MATRIX

    def test_product_template_create_exists(self):
        assert "product_template.create" in PERMISSION_MATRIX

    def test_product_template_update_exists(self):
        assert "product_template.update" in PERMISSION_MATRIX

    def test_product_template_delete_exists(self):
        assert "product_template.delete" in PERMISSION_MATRIX

    def test_inventory_create_exists(self):
        assert "inventory.create" in PERMISSION_MATRIX

    def test_inventory_update_exists(self):
        assert "inventory.update" in PERMISSION_MATRIX

    def test_inventory_delete_exists(self):
        assert "inventory.delete" in PERMISSION_MATRIX

    def test_execution_materials_add_exists(self):
        assert "execution.materials_add" in PERMISSION_MATRIX

    def test_execution_materials_update_exists(self):
        assert "execution.materials_update" in PERMISSION_MATRIX

    def test_execution_materials_delete_exists(self):
        assert "execution.materials_delete" in PERMISSION_MATRIX

    def test_dossier_create_exists(self):
        assert "dossier.create" in PERMISSION_MATRIX

    def test_dossier_update_exists(self):
        assert "dossier.update" in PERMISSION_MATRIX

    def test_dossier_delete_exists(self):
        assert "dossier.delete" in PERMISSION_MATRIX


# ---------------------------------------------------------------------------
# P1-001: Role-permission enforcement
# ---------------------------------------------------------------------------

class TestQuotePermissions:
    """Verify quote permissions are correctly assigned."""

    def test_admin_can_create_quote(self):
        assert has_permission("admin", "quote.create")

    def test_manager_can_create_quote(self):
        assert has_permission("manager", "quote.create")

    def test_sales_can_create_quote(self):
        assert has_permission("sales", "quote.create")

    def test_operator_cannot_create_quote(self):
        assert not has_permission("operator", "quote.create")

    def test_viewer_cannot_create_quote(self):
        assert not has_permission("viewer", "quote.create")

    def test_admin_can_delete_quote(self):
        assert has_permission("admin", "quote.delete")

    def test_manager_can_delete_quote(self):
        assert has_permission("manager", "quote.delete")

    def test_sales_cannot_delete_quote(self):
        assert not has_permission("sales", "quote.delete")

    def test_operator_cannot_delete_quote(self):
        assert not has_permission("operator", "quote.delete")

    def test_viewer_cannot_delete_quote(self):
        assert not has_permission("viewer", "quote.delete")


class TestProductTemplatePermissions:
    """Verify product_template permissions are correctly assigned."""

    def test_admin_can_create_template(self):
        assert has_permission("admin", "product_template.create")

    def test_manager_can_create_template(self):
        assert has_permission("manager", "product_template.create")

    def test_sales_cannot_create_template(self):
        assert not has_permission("sales", "product_template.create")

    def test_operator_cannot_create_template(self):
        assert not has_permission("operator", "product_template.create")

    def test_viewer_cannot_create_template(self):
        assert not has_permission("viewer", "product_template.create")

    def test_admin_can_delete_template(self):
        assert has_permission("admin", "product_template.delete")

    def test_manager_can_delete_template(self):
        assert has_permission("manager", "product_template.delete")

    def test_sales_cannot_delete_template(self):
        assert not has_permission("sales", "product_template.delete")


class TestInventoryPermissions:
    """Verify inventory permissions are correctly assigned."""

    def test_admin_can_create_inventory(self):
        assert has_permission("admin", "inventory.create")

    def test_manager_can_create_inventory(self):
        assert has_permission("manager", "inventory.create")

    def test_sales_cannot_create_inventory(self):
        assert not has_permission("sales", "inventory.create")

    def test_operator_cannot_create_inventory(self):
        assert not has_permission("operator", "inventory.create")

    def test_admin_can_delete_inventory(self):
        assert has_permission("admin", "inventory.delete")

    def test_manager_can_delete_inventory(self):
        assert has_permission("manager", "inventory.delete")

    def test_sales_cannot_delete_inventory(self):
        assert not has_permission("sales", "inventory.delete")

    def test_operator_cannot_delete_inventory(self):
        assert not has_permission("operator", "inventory.delete")


class TestExecutionMaterialsPermissions:
    """Verify execution materials permissions (P2-003)."""

    def test_admin_can_add_materials(self):
        assert has_permission("admin", "execution.materials_add")

    def test_manager_can_add_materials(self):
        assert has_permission("manager", "execution.materials_add")

    def test_operator_can_add_materials(self):
        assert has_permission("operator", "execution.materials_add")

    def test_sales_cannot_add_materials(self):
        assert not has_permission("sales", "execution.materials_add")

    def test_viewer_cannot_add_materials(self):
        assert not has_permission("viewer", "execution.materials_add")

    def test_operator_can_update_materials(self):
        assert has_permission("operator", "execution.materials_update")

    def test_operator_can_delete_materials(self):
        assert has_permission("operator", "execution.materials_delete")

    def test_viewer_cannot_update_materials(self):
        assert not has_permission("viewer", "execution.materials_update")

    def test_viewer_cannot_delete_materials(self):
        assert not has_permission("viewer", "execution.materials_delete")


class TestDossierPermissions:
    """Verify dossier permissions (P2-005)."""

    def test_admin_can_create_dossier(self):
        assert has_permission("admin", "dossier.create")

    def test_manager_can_create_dossier(self):
        assert has_permission("manager", "dossier.create")

    def test_sales_cannot_create_dossier(self):
        assert not has_permission("sales", "dossier.create")

    def test_operator_cannot_create_dossier(self):
        assert not has_permission("operator", "dossier.create")

    def test_viewer_cannot_create_dossier(self):
        assert not has_permission("viewer", "dossier.create")


# ---------------------------------------------------------------------------
# P1-002: Role resolution hardening (backend side)
# ---------------------------------------------------------------------------

class TestRoleResolutionHardening:
    """Verify role resolution aligns with fail-closed policy."""

    @patch("dependencies.permissions.dev_auth_allowed", return_value=True)
    def test_user_maps_to_admin_in_dev(self, mock_env):
        assert resolve_effective_role("user") == "admin"

    @patch("dependencies.permissions.dev_auth_allowed", return_value=False)
    def test_user_maps_to_viewer_in_prod(self, mock_env):
        assert resolve_effective_role("user") == "viewer"

    @patch("dependencies.permissions.dev_auth_allowed", return_value=False)
    def test_unknown_role_maps_to_viewer_in_prod(self, mock_env):
        assert resolve_effective_role("random_role") == "viewer"

    @patch("dependencies.permissions.dev_auth_allowed", return_value=True)
    def test_unknown_role_maps_to_viewer_in_dev(self, mock_env):
        assert resolve_effective_role("random_role") == "viewer"

    def test_valid_roles_pass_through(self):
        for role in VALID_ROLES:
            assert resolve_effective_role(role) == role


# ---------------------------------------------------------------------------
# P1-001: require_permission dependency blocks insufficient roles
# ---------------------------------------------------------------------------

class TestRequirePermissionDependency:
    """Verify require_permission raises 403 for insufficient roles."""

    @pytest.mark.asyncio
    @patch("dependencies.permissions.dev_auth_allowed", return_value=False)
    async def test_viewer_blocked_from_quote_create(self, mock_env):
        """A viewer should get 403 when trying to create a quote."""
        mock_user = MagicMock()
        mock_user.role = "viewer"
        mock_user.email = "viewer@test.com"
        mock_user.id = "test-id"

        checker = require_permission("quote.create")
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("dependencies.permissions.dev_auth_allowed", return_value=False)
    async def test_operator_blocked_from_inventory_create(self, mock_env):
        """An operator should get 403 when trying to create inventory."""
        mock_user = MagicMock()
        mock_user.role = "operator"
        mock_user.email = "operator@test.com"
        mock_user.id = "test-id"

        checker = require_permission("inventory.create")
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("dependencies.permissions.dev_auth_allowed", return_value=False)
    async def test_sales_blocked_from_product_template_create(self, mock_env):
        """Sales should get 403 when trying to create product templates."""
        mock_user = MagicMock()
        mock_user.role = "sales"
        mock_user.email = "sales@test.com"
        mock_user.id = "test-id"

        checker = require_permission("product_template.create")
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("dependencies.permissions.dev_auth_allowed", return_value=False)
    async def test_admin_allowed_for_quote_create(self, mock_env):
        """Admin should pass permission check for quote.create."""
        mock_user = MagicMock()
        mock_user.role = "admin"
        mock_user.email = "admin@test.com"
        mock_user.id = "test-id"

        checker = require_permission("quote.create")
        result = await checker(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    @patch("dependencies.permissions.dev_auth_allowed", return_value=False)
    async def test_manager_allowed_for_inventory_update(self, mock_env):
        """Manager should pass permission check for inventory.update."""
        mock_user = MagicMock()
        mock_user.role = "manager"
        mock_user.email = "manager@test.com"
        mock_user.id = "test-id"

        checker = require_permission("inventory.update")
        result = await checker(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    @patch("dependencies.permissions.dev_auth_allowed", return_value=False)
    async def test_operator_allowed_for_materials_add(self, mock_env):
        """Operator should pass permission check for execution.materials_add."""
        mock_user = MagicMock()
        mock_user.role = "operator"
        mock_user.email = "operator@test.com"
        mock_user.id = "test-id"

        checker = require_permission("execution.materials_add")
        result = await checker(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    @patch("dependencies.permissions.dev_auth_allowed", return_value=False)
    async def test_viewer_blocked_from_materials_add(self, mock_env):
        """Viewer should get 403 for execution.materials_add."""
        mock_user = MagicMock()
        mock_user.role = "viewer"
        mock_user.email = "viewer@test.com"
        mock_user.id = "test-id"

        checker = require_permission("execution.materials_add")
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("dependencies.permissions.dev_auth_allowed", return_value=False)
    async def test_sales_blocked_from_dossier_create(self, mock_env):
        """Sales should get 403 for dossier.create."""
        mock_user = MagicMock()
        mock_user.role = "sales"
        mock_user.email = "sales@test.com"
        mock_user.id = "test-id"

        checker = require_permission("dossier.create")
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("dependencies.permissions.dev_auth_allowed", return_value=True)
    async def test_user_role_resolves_to_admin_in_dev(self, mock_env):
        """In dev, role=user should resolve to admin and pass."""
        mock_user = MagicMock()
        mock_user.role = "user"
        mock_user.email = "dev@test.com"
        mock_user.id = "test-id"

        checker = require_permission("quote.create")
        result = await checker(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    @patch("dependencies.permissions.dev_auth_allowed", return_value=False)
    async def test_user_role_blocked_in_prod(self, mock_env):
        """In prod, role=user resolves to viewer and gets 403."""
        mock_user = MagicMock()
        mock_user.role = "user"
        mock_user.email = "user@test.com"
        mock_user.id = "test-id"

        checker = require_permission("quote.create")
        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=mock_user)
        assert exc_info.value.status_code == 403