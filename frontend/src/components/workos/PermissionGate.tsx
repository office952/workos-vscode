/**
 * BUILD 17 — PermissionGate component.
 *
 * Conditionally renders children based on the current user's permissions.
 * Hides content from unauthorized roles without showing an error.
 */

import React from "react";
import { Permission, Role, can, canAny } from "@/lib/rbac";

interface PermissionGateProps {
  /** Current user's resolved role */
  role: Role;
  /** Required permission (single) */
  permission?: Permission;
  /** Required permissions (any of these grants access) */
  anyOf?: Permission[];
  /** What to show when access is denied (default: nothing) */
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export function PermissionGate({
  role,
  permission,
  anyOf,
  fallback = null,
  children,
}: PermissionGateProps) {
  let hasAccess = false;

  if (permission) {
    hasAccess = can(role, permission);
  } else if (anyOf && anyOf.length > 0) {
    hasAccess = canAny(role, anyOf);
  } else {
    // No permission specified = always show
    hasAccess = true;
  }

  if (!hasAccess) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}