/**
 * BUILD 17 — Convenience hook combining AuthContext with RBAC permissions.
 *
 * Usage:
 *   const { role, can, canViewNav, isAdmin } = useCurrentPermissions();
 */

import { useAuth } from "@/contexts/AuthContext";
import { usePermissions } from "./usePermissions";

export function useCurrentPermissions() {
  const { user } = useAuth();
  return usePermissions({ userRole: user?.role as string | undefined });
}