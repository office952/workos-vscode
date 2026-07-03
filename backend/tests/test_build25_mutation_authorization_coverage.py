"""
BUILD 25 — Full Mutation Authorization Coverage Hardening Tests.

Tests that all mutation endpoints in the 8 targeted routers now require
explicit granular permissions via require_permission().

Routers covered:
1. orders.py — order.create, order.update, order.cancel, order.create_from_quote
2. intake_requests.py — intake.create, intake.update, intake.delete
3. employees.py — employee.create, employee.update, employee.delete
4. suppliers.py — supplier.create, supplier.update, supplier.delete
5. clients.py — client.create, client.update, client.delete
6. recurring_payments.py — recurring_payment.create, recurring_payment.update, recurring_payment.delete
7. cost_engine_config.py — cost_engine.update
8. product_families.py — product_family.create, product_family.update, product_family.delete
"""

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from dependencies.permissions import (
    PERMISSION_MATRIX,
    has_permission,
    resolve_effective_role,
    require_permission,
    VALID_ROLES,
)


# ---------------------------------------------------------------------------
# Section 1: Permission Matrix Completeness for BUILD 25
# ---------------------------------------------------------------------------

class TestBuild25PermissionMatrixCompleteness:
    """Verify all BUILD 25 permissions exist in the matrix."""

    # Orders
    def test_order_create_exists(self):
        assert "order.create" in PERMISSION_MATRIX

    def test_order_update_exists(self):
        assert "order.update" in PERMISSION_MATRIX

    def test_order_cancel_exists(self):
        assert "order.cancel" in PERMISSION_MATRIX

    def test_order_create_from_quote_exists(self):
        assert "order.create_from_quote" in PERMISSION_MATRIX

    # Intake Requests
    def test_intake_create_exists(self):
        assert "intake.create" in PERMISSION_MATRIX

    def test_intake_update_exists(self):
        assert "intake.update" in PERMISSION_MATRIX

    def test_intake_delete_exists(self):
        assert "intake.delete" in PERMISSION_MATRIX

    # Employees
    def test_employee_create_exists(self):
        assert "employee.create" in PERMISSION_MATRIX

    def test_employee_update_exists(self):
        assert "employee.update" in PERMISSION_MATRIX

    def test_employee_delete_exists(self):
        assert "employee.delete" in PERMISSION_MATRIX

    # Suppliers
    def test_supplier_create_exists(self):
        assert "supplier.create" in PERMISSION_MATRIX

    def test_supplier_update_exists(self):
        assert "supplier.update" in PERMISSION_MATRIX

    def test_supplier_delete_exists(self):
        assert "supplier.delete" in PERMISSION_MATRIX

    # Clients
    def test_client_create_exists(self):
        assert "client.create" in PERMISSION_MATRIX

    def test_client_update_exists(self):
        assert "client.update" in PERMISSION_MATRIX

    def test_client_delete_exists(self):
        assert "client.delete" in PERMISSION_MATRIX

    # Recurring Payments
    def test_recurring_payment_create_exists(self):
        assert "recurring_payment.create" in PERMISSION_MATRIX

    def test_recurring_payment_update_exists(self):
        assert "recurring_payment.update" in PERMISSION_MATRIX

    def test_recurring_payment_delete_exists(self):
        assert "recurring_payment.delete" in PERMISSION_MATRIX

    # Cost Engine Config
    def test_cost_engine_update_exists(self):
        assert "cost_engine.update" in PERMISSION_MATRIX

    # Product Families
    def test_product_family_create_exists(self):
        assert "product_family.create" in PERMISSION_MATRIX

    def test_product_family_update_exists(self):
        assert "product_family.update" in PERMISSION_MATRIX

    def test_product_family_delete_exists(self):
        assert "product_family.delete" in PERMISSION_MATRIX


# ---------------------------------------------------------------------------
# Section 2: Role Access Validation — Valid roles allowed
# ---------------------------------------------------------------------------

class TestBuild25ValidRolesAllowed:
    """Verify that valid roles have access to their permitted mutations."""

    # Orders — admin, manager, sales for create; admin, manager for update/cancel
    def test_admin_can_create_order(self):
        assert has_permission("admin", "order.create")

    def test_manager_can_create_order(self):
        assert has_permission("manager", "order.create")

    def test_sales_can_create_order(self):
        assert has_permission("sales", "order.create")

    def test_admin_can_update_order(self):
        assert has_permission("admin", "order.update")

    def test_manager_can_update_order(self):
        assert has_permission("manager", "order.update")

    def test_admin_can_cancel_order(self):
        assert has_permission("admin", "order.cancel")

    def test_manager_can_cancel_order(self):
        assert has_permission("manager", "order.cancel")

    def test_admin_can_create_from_quote(self):
        assert has_permission("admin", "order.create_from_quote")

    def test_manager_can_create_from_quote(self):
        assert has_permission("manager", "order.create_from_quote")

    def test_sales_can_create_from_quote(self):
        assert has_permission("sales", "order.create_from_quote")

    # Intake Requests — admin, manager, sales for create/update; admin, manager for delete
    def test_admin_can_create_intake(self):
        assert has_permission("admin", "intake.create")

    def test_manager_can_create_intake(self):
        assert has_permission("manager", "intake.create")

    def test_sales_can_create_intake(self):
        assert has_permission("sales", "intake.create")

    def test_admin_can_update_intake(self):
        assert has_permission("admin", "intake.update")

    def test_manager_can_update_intake(self):
        assert has_permission("manager", "intake.update")

    def test_sales_can_update_intake(self):
        assert has_permission("sales", "intake.update")

    def test_admin_can_delete_intake(self):
        assert has_permission("admin", "intake.delete")

    def test_manager_can_delete_intake(self):
        assert has_permission("manager", "intake.delete")

    # Employees — admin, manager
    def test_admin_can_create_employee(self):
        assert has_permission("admin", "employee.create")

    def test_manager_can_create_employee(self):
        assert has_permission("manager", "employee.create")

    def test_admin_can_update_employee(self):
        assert has_permission("admin", "employee.update")

    def test_manager_can_update_employee(self):
        assert has_permission("manager", "employee.update")

    def test_admin_can_delete_employee(self):
        assert has_permission("admin", "employee.delete")

    def test_manager_can_delete_employee(self):
        assert has_permission("manager", "employee.delete")

    # Suppliers — admin, manager
    def test_admin_can_create_supplier(self):
        assert has_permission("admin", "supplier.create")

    def test_manager_can_create_supplier(self):
        assert has_permission("manager", "supplier.create")

    def test_admin_can_update_supplier(self):
        assert has_permission("admin", "supplier.update")

    def test_manager_can_update_supplier(self):
        assert has_permission("manager", "supplier.update")

    def test_admin_can_delete_supplier(self):
        assert has_permission("admin", "supplier.delete")

    def test_manager_can_delete_supplier(self):
        assert has_permission("manager", "supplier.delete")

    # Clients — admin, manager, sales for create/update; admin, manager for delete
    def test_admin_can_create_client(self):
        assert has_permission("admin", "client.create")

    def test_manager_can_create_client(self):
        assert has_permission("manager", "client.create")

    def test_sales_can_create_client(self):
        assert has_permission("sales", "client.create")

    def test_admin_can_update_client(self):
        assert has_permission("admin", "client.update")

    def test_sales_can_update_client(self):
        assert has_permission("sales", "client.update")

    def test_admin_can_delete_client(self):
        assert has_permission("admin", "client.delete")

    def test_manager_can_delete_client(self):
        assert has_permission("manager", "client.delete")

    # Recurring Payments — admin, manager
    def test_admin_can_create_recurring_payment(self):
        assert has_permission("admin", "recurring_payment.create")

    def test_manager_can_create_recurring_payment(self):
        assert has_permission("manager", "recurring_payment.create")

    def test_admin_can_update_recurring_payment(self):
        assert has_permission("admin", "recurring_payment.update")

    def test_manager_can_update_recurring_payment(self):
        assert has_permission("manager", "recurring_payment.update")

    def test_admin_can_delete_recurring_payment(self):
        assert has_permission("admin", "recurring_payment.delete")

    def test_manager_can_delete_recurring_payment(self):
        assert has_permission("manager", "recurring_payment.delete")

    # Cost Engine Config — admin only
    def test_admin_can_update_cost_engine(self):
        assert has_permission("admin", "cost_engine.update")

    # Product Families — admin, manager
    def test_admin_can_create_product_family(self):
        assert has_permission("admin", "product_family.create")

    def test_manager_can_create_product_family(self):
        assert has_permission("manager", "product_family.create")

    def test_admin_can_update_product_family(self):
        assert has_permission("admin", "product_family.update")

    def test_manager_can_update_product_family(self):
        assert has_permission("manager", "product_family.update")

    def test_admin_can_delete_product_family(self):
        assert has_permission("admin", "product_family.delete")

    def test_manager_can_delete_product_family(self):
        assert has_permission("manager", "product_family.delete")


# ---------------------------------------------------------------------------
# Section 3: Role Access Validation — Insufficient roles blocked
# ---------------------------------------------------------------------------

class TestBuild25InsufficientRolesBlocked:
    """Verify that insufficient roles are denied access."""

    # Orders — viewer and operator cannot mutate
    def test_viewer_cannot_create_order(self):
        assert not has_permission("viewer", "order.create")

    def test_operator_cannot_create_order(self):
        assert not has_permission("operator", "order.create")

    def test_viewer_cannot_update_order(self):
        assert not has_permission("viewer", "order.update")

    def test_operator_cannot_update_order(self):
        assert not has_permission("operator", "order.update")

    def test_viewer_cannot_cancel_order(self):
        assert not has_permission("viewer", "order.cancel")

    def test_operator_cannot_cancel_order(self):
        assert not has_permission("operator", "order.cancel")

    def test_sales_cannot_update_order(self):
        assert not has_permission("sales", "order.update")

    def test_sales_cannot_cancel_order(self):
        assert not has_permission("sales", "order.cancel")

    # Intake — viewer and operator cannot mutate
    def test_viewer_cannot_create_intake(self):
        assert not has_permission("viewer", "intake.create")

    def test_operator_cannot_create_intake(self):
        assert not has_permission("operator", "intake.create")

    def test_viewer_cannot_update_intake(self):
        assert not has_permission("viewer", "intake.update")

    def test_operator_cannot_update_intake(self):
        assert not has_permission("operator", "intake.update")

    def test_viewer_cannot_delete_intake(self):
        assert not has_permission("viewer", "intake.delete")

    def test_operator_cannot_delete_intake(self):
        assert not has_permission("operator", "intake.delete")

    def test_sales_cannot_delete_intake(self):
        assert not has_permission("sales", "intake.delete")

    # Employees — viewer, operator, sales cannot mutate
    def test_viewer_cannot_create_employee(self):
        assert not has_permission("viewer", "employee.create")

    def test_operator_cannot_create_employee(self):
        assert not has_permission("operator", "employee.create")

    def test_sales_cannot_create_employee(self):
        assert not has_permission("sales", "employee.create")

    def test_viewer_cannot_update_employee(self):
        assert not has_permission("viewer", "employee.update")

    def test_viewer_cannot_delete_employee(self):
        assert not has_permission("viewer", "employee.delete")

    def test_sales_cannot_delete_employee(self):
        assert not has_permission("sales", "employee.delete")

    # Suppliers — viewer, operator, sales cannot mutate
    def test_viewer_cannot_create_supplier(self):
        assert not has_permission("viewer", "supplier.create")

    def test_operator_cannot_create_supplier(self):
        assert not has_permission("operator", "supplier.create")

    def test_sales_cannot_create_supplier(self):
        assert not has_permission("sales", "supplier.create")

    def test_viewer_cannot_update_supplier(self):
        assert not has_permission("viewer", "supplier.update")

    def test_viewer_cannot_delete_supplier(self):
        assert not has_permission("viewer", "supplier.delete")

    def test_sales_cannot_delete_supplier(self):
        assert not has_permission("sales", "supplier.delete")

    # Clients — viewer and operator cannot mutate
    def test_viewer_cannot_create_client(self):
        assert not has_permission("viewer", "client.create")

    def test_operator_cannot_create_client(self):
        assert not has_permission("operator", "client.create")

    def test_viewer_cannot_update_client(self):
        assert not has_permission("viewer", "client.update")

    def test_operator_cannot_update_client(self):
        assert not has_permission("operator", "client.update")

    def test_viewer_cannot_delete_client(self):
        assert not has_permission("viewer", "client.delete")

    def test_operator_cannot_delete_client(self):
        assert not has_permission("operator", "client.delete")

    # Recurring Payments — viewer, operator, sales cannot mutate
    def test_viewer_cannot_create_recurring_payment(self):
        assert not has_permission("viewer", "recurring_payment.create")

    def test_operator_cannot_create_recurring_payment(self):
        assert not has_permission("operator", "recurring_payment.create")

    def test_sales_cannot_create_recurring_payment(self):
        assert not has_permission("sales", "recurring_payment.create")

    def test_viewer_cannot_update_recurring_payment(self):
        assert not has_permission("viewer", "recurring_payment.update")

    def test_viewer_cannot_delete_recurring_payment(self):
        assert not has_permission("viewer", "recurring_payment.delete")

    def test_sales_cannot_delete_recurring_payment(self):
        assert not has_permission("sales", "recurring_payment.delete")

    # Cost Engine Config — only admin can update
    def test_viewer_cannot_update_cost_engine(self):
        assert not has_permission("viewer", "cost_engine.update")

    def test_operator_cannot_update_cost_engine(self):
        assert not has_permission("operator", "cost_engine.update")

    def test_sales_cannot_update_cost_engine(self):
        assert not has_permission("sales", "cost_engine.update")

    def test_manager_cannot_update_cost_engine(self):
        assert not has_permission("manager", "cost_engine.update")

    # Product Families — viewer, operator, sales cannot mutate
    def test_viewer_cannot_create_product_family(self):
        assert not has_permission("viewer", "product_family.create")

    def test_operator_cannot_create_product_family(self):
        assert not has_permission("operator", "product_family.create")

    def test_sales_cannot_create_product_family(self):
        assert not has_permission("sales", "product_family.create")

    def test_viewer_cannot_update_product_family(self):
        assert not has_permission("viewer", "product_family.update")

    def test_viewer_cannot_delete_product_family(self):
        assert not has_permission("viewer", "product_family.delete")

    def test_sales_cannot_delete_product_family(self):
        assert not has_permission("sales", "product_family.delete")


# ---------------------------------------------------------------------------
# Section 4: require_permission dependency — 403 enforcement
# ---------------------------------------------------------------------------

class TestBuild25RequirePermission403:
    """Verify require_permission raises 403 for insufficient roles."""

    @pytest.mark.asyncio
    async def test_viewer_blocked_from_order_create(self):
        mock_user = MagicMock()
        mock_user.role = "viewer"
        dep = require_permission("order.create")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_blocked_from_order_cancel(self):
        mock_user = MagicMock()
        mock_user.role = "operator"
        dep = require_permission("order.cancel")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_blocked_from_intake_create(self):
        mock_user = MagicMock()
        mock_user.role = "operator"
        dep = require_permission("intake.create")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_sales_blocked_from_intake_delete(self):
        mock_user = MagicMock()
        mock_user.role = "sales"
        dep = require_permission("intake.delete")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_sales_blocked_from_employee_create(self):
        mock_user = MagicMock()
        mock_user.role = "sales"
        dep = require_permission("employee.create")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_sales_blocked_from_supplier_create(self):
        mock_user = MagicMock()
        mock_user.role = "sales"
        dep = require_permission("supplier.create")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_operator_blocked_from_client_delete(self):
        mock_user = MagicMock()
        mock_user.role = "operator"
        dep = require_permission("client.delete")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_sales_blocked_from_recurring_payment_create(self):
        mock_user = MagicMock()
        mock_user.role = "sales"
        dep = require_permission("recurring_payment.create")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_manager_blocked_from_cost_engine_update(self):
        mock_user = MagicMock()
        mock_user.role = "manager"
        dep = require_permission("cost_engine.update")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_sales_blocked_from_product_family_create(self):
        mock_user = MagicMock()
        mock_user.role = "sales"
        dep = require_permission("product_family.create")
        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=mock_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_allowed_order_create(self):
        mock_user = MagicMock()
        mock_user.role = "admin"
        dep = require_permission("order.create")
        result = await dep(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_manager_allowed_supplier_create(self):
        mock_user = MagicMock()
        mock_user.role = "manager"
        dep = require_permission("supplier.create")
        result = await dep(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_sales_allowed_client_create(self):
        mock_user = MagicMock()
        mock_user.role = "sales"
        dep = require_permission("client.create")
        result = await dep(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_admin_allowed_cost_engine_update(self):
        mock_user = MagicMock()
        mock_user.role = "admin"
        dep = require_permission("cost_engine.update")
        result = await dep(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_admin_allowed_intake_delete(self):
        mock_user = MagicMock()
        mock_user.role = "admin"
        dep = require_permission("intake.delete")
        result = await dep(current_user=mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_manager_allowed_recurring_payment_delete(self):
        mock_user = MagicMock()
        mock_user.role = "manager"
        dep = require_permission("recurring_payment.delete")
        result = await dep(current_user=mock_user)
        assert result == mock_user


# ---------------------------------------------------------------------------
# Section 5: Endpoint-level verification — router source has permission deps
# ---------------------------------------------------------------------------

class TestBuild25EndpointPermissionDeps:
    """Verify that mutation endpoints have require_permission in their source."""

    # Orders
    def test_orders_create_has_permission_dep(self):
        from routers import orders
        source = open(orders.__file__).read()
        assert 'require_permission("order.create")' in source

    def test_orders_update_has_permission_dep(self):
        from routers import orders
        source = open(orders.__file__).read()
        assert 'require_permission("order.update")' in source

    def test_orders_cancel_has_permission_dep(self):
        from routers import orders
        source = open(orders.__file__).read()
        assert 'require_permission("order.cancel")' in source

    def test_orders_create_from_quote_has_permission_dep(self):
        from routers import orders
        source = open(orders.__file__).read()
        assert 'require_permission("order.create_from_quote")' in source

    # Intake Requests
    def test_intake_create_has_permission_dep(self):
        from routers import intake_requests
        source = open(intake_requests.__file__).read()
        assert 'require_permission("intake.create")' in source

    def test_intake_update_has_permission_dep(self):
        from routers import intake_requests
        source = open(intake_requests.__file__).read()
        assert 'require_permission("intake.update")' in source

    def test_intake_delete_has_permission_dep(self):
        from routers import intake_requests
        source = open(intake_requests.__file__).read()
        assert 'require_permission("intake.delete")' in source

    # Employees
    def test_employees_create_has_permission_dep(self):
        from routers import employees
        source = open(employees.__file__).read()
        assert 'require_permission("employee.create")' in source

    def test_employees_update_has_permission_dep(self):
        from routers import employees
        source = open(employees.__file__).read()
        assert 'require_permission("employee.update")' in source

    def test_employees_delete_has_permission_dep(self):
        from routers import employees
        source = open(employees.__file__).read()
        assert 'require_permission("employee.delete")' in source

    # Suppliers
    def test_suppliers_create_has_permission_dep(self):
        from routers import suppliers
        source = open(suppliers.__file__).read()
        assert 'require_permission("supplier.create")' in source

    def test_suppliers_update_has_permission_dep(self):
        from routers import suppliers
        source = open(suppliers.__file__).read()
        assert 'require_permission("supplier.update")' in source

    def test_suppliers_delete_has_permission_dep(self):
        from routers import suppliers
        source = open(suppliers.__file__).read()
        assert 'require_permission("supplier.delete")' in source

    # Clients
    def test_clients_create_has_permission_dep(self):
        from routers import clients
        source = open(clients.__file__).read()
        assert 'require_permission("client.create")' in source

    def test_clients_update_has_permission_dep(self):
        from routers import clients
        source = open(clients.__file__).read()
        assert 'require_permission("client.update")' in source

    def test_clients_delete_has_permission_dep(self):
        from routers import clients
        source = open(clients.__file__).read()
        assert 'require_permission("client.delete")' in source

    # Recurring Payments
    def test_recurring_payments_create_has_permission_dep(self):
        from routers import recurring_payments
        source = open(recurring_payments.__file__).read()
        assert 'require_permission("recurring_payment.create")' in source

    def test_recurring_payments_update_has_permission_dep(self):
        from routers import recurring_payments
        source = open(recurring_payments.__file__).read()
        assert 'require_permission("recurring_payment.update")' in source

    def test_recurring_payments_delete_has_permission_dep(self):
        from routers import recurring_payments
        source = open(recurring_payments.__file__).read()
        assert 'require_permission("recurring_payment.delete")' in source

    # Cost Engine Config
    def test_cost_engine_update_has_permission_dep(self):
        from routers import cost_engine_config
        source = open(cost_engine_config.__file__).read()
        assert 'require_permission("cost_engine.update")' in source

    # Product Families
    def test_product_families_create_has_permission_dep(self):
        from routers import product_families
        source = open(product_families.__file__).read()
        assert 'require_permission("product_family.create")' in source

    def test_product_families_update_has_permission_dep(self):
        from routers import product_families
        source = open(product_families.__file__).read()
        assert 'require_permission("product_family.update")' in source

    def test_product_families_delete_has_permission_dep(self):
        from routers import product_families
        source = open(product_families.__file__).read()
        assert 'require_permission("product_family.delete")' in source


# ---------------------------------------------------------------------------
# Section 6: Cross-router permission count verification
# ---------------------------------------------------------------------------

class TestBuild25PermissionCountVerification:
    """Verify each router has the expected number of require_permission calls."""

    def _count_permission_calls(self, module_name):
        import importlib
        mod = importlib.import_module(f"routers.{module_name}")
        source = open(mod.__file__).read()
        return source.count("require_permission(")

    def test_orders_has_at_least_5_permission_calls(self):
        assert self._count_permission_calls("orders") >= 5

    def test_intake_requests_has_at_least_6_permission_calls(self):
        assert self._count_permission_calls("intake_requests") >= 6

    def test_employees_has_at_least_3_permission_calls(self):
        assert self._count_permission_calls("employees") >= 3

    def test_suppliers_has_at_least_6_permission_calls(self):
        assert self._count_permission_calls("suppliers") >= 6

    def test_clients_has_at_least_6_permission_calls(self):
        assert self._count_permission_calls("clients") >= 6

    def test_recurring_payments_has_at_least_3_permission_calls(self):
        assert self._count_permission_calls("recurring_payments") >= 3

    def test_cost_engine_config_has_at_least_1_permission_call(self):
        assert self._count_permission_calls("cost_engine_config") >= 1

    def test_product_families_has_at_least_3_permission_calls(self):
        assert self._count_permission_calls("product_families") >= 3