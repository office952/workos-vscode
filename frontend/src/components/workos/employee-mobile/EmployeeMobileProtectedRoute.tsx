import type { ReactNode } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  canAccessEmployeeMobileRoute,
  type EmployeeMobileRouteKey,
} from "@/lib/employeeMobileAccess";
import EmployeeMobileRouteBlocked from "@/components/workos/employee-mobile/EmployeeMobileRouteBlocked";

type EmployeeMobileProtectedRouteProps = {
  routeKey: EmployeeMobileRouteKey;
  children: ReactNode;
};

export default function EmployeeMobileProtectedRoute({
  routeKey,
  children,
}: EmployeeMobileProtectedRouteProps) {
  const { user } = useAuth();

  if (!canAccessEmployeeMobileRoute(user?.role, routeKey)) {
    return <EmployeeMobileRouteBlocked routeKey={routeKey} />;
  }

  return children;
}
