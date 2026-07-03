/**
 * Employee Mobile manager/review UI visibility.
 *
 * Mirrors backend reviewer roles (admin/manager) — UI only; routes stay guarded server-side.
 * - Team: MANAGER_TEAM_READER_ROLES in employee_manager_team_service.py
 * - Review: employee_request_reviewer guard (admin/manager)
 */
export const EMPLOYEE_MOBILE_MANAGER_WORKSPACE_ROLES = ["admin", "manager"] as const;

export type EmployeeMobileManagerWorkspaceRole =
  (typeof EMPLOYEE_MOBILE_MANAGER_WORKSPACE_ROLES)[number];

function hasEmployeeMobileManagerWorkspaceRole(
  userRole: string | null | undefined,
): boolean {
  if (!userRole) return false;
  return (EMPLOYEE_MOBILE_MANAGER_WORKSPACE_ROLES as readonly string[]).includes(userRole);
}

/** True when user may open the manager team workspace (admin/manager auth roles only). */
export function canAccessManagerTeamWorkspace(
  userRole: string | null | undefined,
): boolean {
  return hasEmployeeMobileManagerWorkspaceRole(userRole);
}

/** True when user may open the request review workspace (admin/manager auth roles only). */
export function canAccessRequestReviewWorkspace(
  userRole: string | null | undefined,
): boolean {
  return hasEmployeeMobileManagerWorkspaceRole(userRole);
}

/** Human-readable auth role label for Employee Mobile account UI. */
export function employeeMobileAuthRoleLabel(role: string | null | undefined): string {
  if (!role) return "—";
  if (role === "employee_mobile") return "Angajat mobil";
  if (role === "admin") return "Administrator";
  if (role === "manager") return "Manager";
  return role;
}

export type EmployeeMobileAccessSummary = {
  title: string;
  description: string;
  variant: "self" | "manager";
};

/** Short access explanation for the Employee Mobile account panel. */
export function getEmployeeMobileAccessSummary(
  userRole: string | null | undefined,
): EmployeeMobileAccessSummary {
  if (hasEmployeeMobileManagerWorkspaceRole(userRole)) {
    return {
      title: "Acces manager / admin",
      description:
        "Ai acces la review cereri și echipa, pe lângă cererile și pontajul tău personal.",
      variant: "manager",
    };
  }
  return {
    title: "Acces angajat",
    description: "Ai acces la cererile tale și pontajul tău — doar zona ta (self-only).",
    variant: "self",
  };
}

/** True when self employee-link probe is meaningful for the account panel. */
export function shouldProbeEmployeeMobileSelfLink(
  userRole: string | null | undefined,
): boolean {
  return userRole === "employee_mobile" || userRole === "manager";
}

export type EmployeeMobileRouteKey =
  | "home"
  | "requests"
  | "attendance"
  | "tasks"
  | "review"
  | "team";

const EMPLOYEE_MOBILE_SELF_ROUTES: EmployeeMobileRouteKey[] = [
  "home",
  "requests",
  "attendance",
  "tasks",
];

/** True when the auth role may open an Employee Mobile route (UI guard only). */
export function canAccessEmployeeMobileRoute(
  userRole: string | null | undefined,
  routeKey: EmployeeMobileRouteKey,
): boolean {
  if (EMPLOYEE_MOBILE_SELF_ROUTES.includes(routeKey)) return true;
  if (routeKey === "review") return canAccessRequestReviewWorkspace(userRole);
  if (routeKey === "team") return canAccessManagerTeamWorkspace(userRole);
  return false;
}

/** Resolve route key from a pathname under /employee-app. */
export function getEmployeeMobileRouteKeyFromPath(
  pathname: string,
): EmployeeMobileRouteKey | null {
  const normalized = pathname.replace(/\/$/, "") || "/";
  if (normalized === "/employee-app") return "home";
  if (normalized.startsWith("/employee-app/review")) return "review";
  if (normalized.startsWith("/employee-app/team")) return "team";
  if (normalized.startsWith("/employee-app/requests")) return "requests";
  if (normalized.startsWith("/employee-app/attendance")) return "attendance";
  if (normalized.startsWith("/employee-app/tasks")) return "tasks";
  return null;
}

/** User-facing message when a deep-linked route is blocked in UI. */
export function getEmployeeMobileRouteBlockedMessage(routeKey: EmployeeMobileRouteKey): string {
  if (routeKey === "review") {
    return "Review cereri este disponibil doar pentru conturi manager sau administrator.";
  }
  if (routeKey === "team") {
    return "Echipa mea este disponibilă doar pentru conturi manager sau administrator.";
  }
  return "Nu ai acces la această secțiune din Employee Mobile.";
}
