/**
 * U7 — UI path accessibility guard inside AppShell.
 *
 * Redirects to role home when the desktop path is outside the role's projected nav.
 * Explicitly NOT backend authorization — mutations remain fail-closed on the API.
 */

import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useCurrentPermissions } from "@/hooks/useCurrentPermissions";
import { getRoleHomePath, pathAllowedForRole } from "@/lib/shellNavigation";

export default function ShellPathGuard({ children }: { children: ReactNode }) {
  const { role } = useCurrentPermissions();
  const location = useLocation();

  if (!pathAllowedForRole(role, location.pathname)) {
    return (
      <Navigate
        to={getRoleHomePath(role)}
        replace
        state={{ shellAccess: "ui_nav_hidden", from: location.pathname }}
      />
    );
  }

  return <>{children}</>;
}
