/**
 * U7 — deterministic root / unknown-route landing by authenticated role.
 * Presentation-only redirect; does not alter auth semantics.
 */

import { Navigate } from "react-router-dom";
import { useCurrentPermissions } from "@/hooks/useCurrentPermissions";
import { getRoleHomePath } from "@/lib/shellNavigation";

export default function RoleHomeRedirect() {
  const { role } = useCurrentPermissions();
  return <Navigate to={getRoleHomePath(role)} replace />;
}
