/**
 * BUILD 17 — usePermissions hook.
 *
 * Provides role-based permission checks for the current user.
 * Reads role from the auth context (user.role from /api/v1/auth/me).
 */

import { useMemo } from "react";
import {
  Role,
  Permission,
  NavItem,
  resolveRole,
  can,
  canAll,
  canAny,
  getPermissions,
  canViewNav,
  getVisibleNavItems,
} from "@/lib/rbac";

interface UsePermissionsOptions {
  /** Raw role string from backend (e.g., "admin", "user", "operator") */
  userRole?: string | null;
}

interface UsePermissionsResult {
  /** Effective resolved role */
  role: Role;
  /** Check a single permission */
  can: (permission: Permission) => boolean;
  /** Check ALL permissions */
  canAll: (permissions: Permission[]) => boolean;
  /** Check ANY permission */
  canAny: (permissions: Permission[]) => boolean;
  /** Get all permissions for current role */
  permissions: Permission[];
  /** Check nav item visibility */
  canViewNav: (navItem: NavItem) => boolean;
  /** Get all visible nav items */
  visibleNavItems: NavItem[];
  /** Whether user is admin */
  isAdmin: boolean;
  /** Whether user is at least manager level */
  isManagerOrAbove: boolean;
  /** Whether user can see cost/profit data */
  canViewCosts: boolean;
}

export function usePermissions({
  userRole,
}: UsePermissionsOptions): UsePermissionsResult {
  const role = useMemo(() => resolveRole(userRole), [userRole]);

  return useMemo(
    () => ({
      role,
      can: (permission: Permission) => can(role, permission),
      canAll: (permissions: Permission[]) => canAll(role, permissions),
      canAny: (permissions: Permission[]) => canAny(role, permissions),
      permissions: getPermissions(role),
      canViewNav: (navItem: NavItem) => canViewNav(role, navItem),
      visibleNavItems: getVisibleNavItems(role),
      isAdmin: role === "admin",
      isManagerOrAbove: role === "admin" || role === "manager",
      canViewCosts: can(role, "view:quote_cost") || can(role, "view:reports_profit"),
    }),
    [role]
  );
}