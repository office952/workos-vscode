"""
BUILD 17 — Backend Permission Infrastructure.
BUILD 20 — Auth Environment Hardening.

Provides `require_permission(permission_key)` dependency for FastAPI routes.
Uses a static role-permission map. Role is resolved from the current user's JWT.

Roles: admin, manager, sales, operator, viewer
Default dev/test role: admin (so existing tests continue to pass without changes).

Permission denial returns HTTP 403.

BUILD 20 hardening:
- role=user → admin fallback is ONLY allowed in dev/local/test environments.
- In staging/production, role=user maps to "viewer" (fail-closed).
- Unknown roles always map to "viewer".
"""

import logging
from typing import List

from fastapi import Depends, HTTPException, status
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from core.environment import dev_auth_allowed

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role definitions
# ---------------------------------------------------------------------------

VALID_ROLES = ("admin", "manager", "sales", "operator", "viewer", "employee_mobile")

# Dev/test fallback: if role is not in VALID_ROLES, map to this.
# "user" (the current default in token) maps to "admin" ONLY in dev environments.
# In staging/production, "user" maps to "viewer" (fail-closed).
_ROLE_FALLBACK_MAP_DEV = {
    "user": "admin",  # existing tokens have role="user" for admin users — dev only
}

_ROLE_FALLBACK_MAP_PROD = {
    "user": "viewer",  # fail-closed: unknown legacy role gets minimal access
}


def resolve_effective_role(raw_role: str) -> str:
    """
    Resolve the effective RBAC role from the JWT role claim.

    BUILD 20 hardening:
    - In dev/local/test: role=user → admin (backward compat)
    - In staging/production: role=user → viewer (fail-closed)
    - Unknown role always → viewer
    """
    if raw_role in VALID_ROLES:
        return raw_role

    # Select fallback map based on environment
    if dev_auth_allowed():
        fallback_map = _ROLE_FALLBACK_MAP_DEV
    else:
        fallback_map = _ROLE_FALLBACK_MAP_PROD

    mapped = fallback_map.get(raw_role)
    if mapped:
        if not dev_auth_allowed() and raw_role == "user":
            logger.warning(
                "Role 'user' encountered in non-dev environment — mapped to '%s' (fail-closed). "
                "Ensure JWT contains explicit role claim for staging/production.",
                mapped,
            )
        return mapped

    # Unknown role defaults to viewer (safest)
    logger.warning("Unknown role '%s', defaulting to 'viewer'", raw_role)
    return "viewer"


# ---------------------------------------------------------------------------
# Permission matrix
# ---------------------------------------------------------------------------

PERMISSION_MATRIX: dict[str, List[str]] = {
    # Intake
    "intake.create": ["admin", "manager", "sales"],
    "intake.update": ["admin", "manager", "sales"],
    "intake.delete": ["admin", "manager"],

    # Quotes
    "quote.create": ["admin", "manager", "sales"],
    "quote.update": ["admin", "manager", "sales"],
    "quote.delete": ["admin", "manager"],
    "quote.price": ["admin", "manager", "sales"],
    "quote.send": ["admin", "manager", "sales"],
    "quote.accept": ["admin", "manager", "sales"],
    "quote.reject": ["admin", "manager", "sales"],
    "quote.export_pdf": ["admin", "manager", "sales"],

    # Product Templates
    "product_template.create": ["admin", "manager"],
    "product_template.update": ["admin", "manager"],
    "product_template.delete": ["admin", "manager"],

    # Orders
    "order.create": ["admin", "manager", "sales"],
    "order.create_from_quote": ["admin", "manager", "sales"],
    "order.update": ["admin", "manager"],
    "order.update_status": ["admin", "manager"],
    "order.cancel": ["admin", "manager"],

    # Execution
    "execution.plan_generate": ["admin", "manager"],
    "execution.task_start": ["admin", "manager", "operator"],
    "execution.task_complete": ["admin", "manager", "operator"],
    "execution.task_block": ["admin", "manager", "operator"],
    "execution.task_assign": ["admin", "manager", "operator"],
    "execution.clarification_list": ["admin", "manager", "operator"],
    "execution.clarification_resolve": ["admin", "manager", "operator"],
    "execution.production_blueprint": ["admin", "manager", "operator"],
    "execution.owner_decision_resolve": ["admin", "manager"],
    "operator.task_action": ["admin", "manager", "operator"],

    # ExecutionReality
    "reality.create": ["admin", "manager", "operator"],
    "reality.verify": ["admin", "manager"],
    "reality.invalidate": ["admin", "manager"],
    "reality.restore_valid": ["admin", "manager"],

    # Execution Materials (observational capture)
    "execution.materials_add": ["admin", "manager", "operator"],
    "execution.materials_update": ["admin", "manager", "operator"],
    "execution.materials_delete": ["admin", "manager", "operator"],

    # Inventory
    "inventory.create": ["admin", "manager"],
    "inventory.update": ["admin", "manager"],
    "inventory.delete": ["admin", "manager"],
    "inventory.view": ["admin", "manager", "sales", "operator"],
    "inventory.deduct_stock": ["admin", "manager"],
    "inventory.adjust_stock": ["admin", "manager"],
    "inventory.view_movements": ["admin", "manager", "operator"],
    "inventory.material_actual.write": ["admin", "manager"],
    "inventory.material_actual.read_valuation": ["admin", "manager"],

    # Product Blueprint Dossier
    "dossier.create": ["admin", "manager"],
    "dossier.update": ["admin", "manager"],
    "dossier.delete": ["admin", "manager"],

    # Employees
    "employee.create": ["admin", "manager"],
    "employee.update": ["admin", "manager"],
    "employee.delete": ["admin", "manager"],

    # Suppliers
    "supplier.create": ["admin", "manager"],
    "supplier.update": ["admin", "manager"],
    "supplier.delete": ["admin", "manager"],

    # Clients
    "client.create": ["admin", "manager", "sales"],
    "client.update": ["admin", "manager", "sales"],
    "client.delete": ["admin", "manager"],

    # Product Families
    "product_family.create": ["admin", "manager"],
    "product_family.update": ["admin", "manager"],
    "product_family.delete": ["admin", "manager"],

    # Recurring Payments
    "recurring_payment.create": ["admin", "manager"],
    "recurring_payment.update": ["admin", "manager"],
    "recurring_payment.delete": ["admin", "manager"],

    # Cost Engine Config
    "cost_engine.update": ["admin"],

    # Reports
    "reports.view": ["admin", "manager", "sales"],
    "reports.view_profit": ["admin", "manager"],
    # Standard internal cost policies are management data, never operator data.
    "actual_cost_policy.manage": ["admin", "manager"],
    # Read-only operational prep; close/reopen remain execution.job_close.
    "execution.closure_readiness": ["admin", "manager", "operator"],
    "execution.job_close": ["admin", "manager"],

    # Settings
    "settings.view": ["admin"],
    "settings.update": ["admin"],

    # System diagnostics
    "system.diagnostics.read": ["admin"],

    # Documentation index (W0-B2 read-only; not a filesystem browser)
    "system.documentation_read": ["admin"],

    # Integrations
    "integrations.smartbill.view": ["admin"],
    "integrations.smartbill.update": ["admin"],

    # Storage
    "storage.upload_url": ["admin", "manager", "sales", "operator"],
    "storage.download_url": ["admin", "manager", "sales", "operator"],
    "storage.rename": ["admin", "manager", "sales"],
    "storage.delete": ["admin", "manager", "sales"],

    # Quote Output Snapshots
    "quote_output_snapshot.manage": ["admin", "manager", "sales"],

    # Output Blocks
    "output_blocks.snapshot_create": ["admin", "manager", "sales"],

    # Workcenter Rates
    "workcenter_rates.manage": ["admin"],

    # AI Hub
    "aihub.execute": ["admin", "manager", "sales"],

    # Admin
    "admin.manage_users": ["admin"],
}


def has_permission(role: str, permission_key: str) -> bool:
    """Check if a role has a specific permission."""
    allowed_roles = PERMISSION_MATRIX.get(permission_key, [])
    return role in allowed_roles


def get_role_permissions(role: str) -> List[str]:
    """Get all permissions for a given role."""
    return [perm for perm, roles in PERMISSION_MATRIX.items() if role in roles]


# ---------------------------------------------------------------------------
# FastAPI dependency factory
# ---------------------------------------------------------------------------


def require_permission(permission_key: str):
    """
    FastAPI dependency factory that enforces a permission check.

    Usage:
        @router.post("/some-action", dependencies=[Depends(require_permission("order.cancel"))])
        async def some_action(...): ...

    Or as a direct dependency:
        async def some_action(user=Depends(require_permission("order.cancel"))): ...
    """

    async def _check_permission(
        current_user: UserResponse = Depends(get_current_user),
    ) -> UserResponse:
        effective_role = resolve_effective_role(current_user.role)
        if not has_permission(effective_role, permission_key):
            logger.warning(
                "Permission denied: user=%s role=%s(%s) permission=%s",
                current_user.email or current_user.id,
                current_user.role,
                effective_role,
                permission_key,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "permission_denied",
                    "permission": permission_key,
                    "role": effective_role,
                    "message": f"Role '{effective_role}' does not have permission '{permission_key}'",
                },
            )
        return current_user

    return _check_permission