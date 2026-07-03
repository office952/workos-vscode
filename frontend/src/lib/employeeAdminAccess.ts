import type { EmployeeDTO } from "@/api/costEngine";

export type EmployeeMobileAccessVariant = "active" | "linked" | "unlinked";

export type EmployeeMobileAccessDisplay = {
  label: string;
  description: string;
  variant: EmployeeMobileAccessVariant;
};

/** True when API reports Employee Mobile access for the linked user. */
export function employeeHasMobileAccess(employee: EmployeeDTO): boolean {
  return employee.has_mobile_access === true;
}

/** True when employee row is linked to a WorkOS user account. */
export function employeeIsLinkedToUser(employee: EmployeeDTO): boolean {
  if (employee.is_linked_to_user != null) return employee.is_linked_to_user;
  return Boolean((employee.user_id ?? "").trim());
}

export function getEmployeeMobileAccessDisplay(
  employee: EmployeeDTO,
): EmployeeMobileAccessDisplay {
  if (employeeHasMobileAccess(employee)) {
    return {
      label: "Mobile activ",
      description: "Cont legat și eligibil pentru Employee Mobile (angajat activ + rol compatibil).",
      variant: "active",
    };
  }
  if (employeeIsLinkedToUser(employee)) {
    return {
      label: "Cont legat",
      description:
        "Există user WorkOS legat, dar accesul mobil nu este activ (status inactiv sau rol necompatibil).",
      variant: "linked",
    };
  }
  return {
    label: "Fără cont mobil",
    description: "Nu există user WorkOS legat — angajatul nu poate folosi Employee Mobile.",
    variant: "unlinked",
  };
}

export function employeeMatchesMobileQuickFilter(
  employee: EmployeeDTO,
  filter: "all" | "mobile" | "no_mobile",
): boolean {
  if (filter === "all") return true;
  if (filter === "mobile") return employeeHasMobileAccess(employee);
  return !employeeHasMobileAccess(employee);
}

export function employeeSearchHaystack(employee: EmployeeDTO): string {
  return [
    employee.name,
    employee.role ?? "",
    employee.department ?? "",
    (employee.skills ?? []).join(" "),
    employee.user_id ?? "",
    employee.auth_email ?? "",
    employee.auth_role ?? "",
  ]
    .join(" ")
    .toLowerCase();
}

export function employeeAuthRoleLabel(role: string | null | undefined): string {
  if (!role) return "—";
  if (role === "employee_mobile") return "Angajat mobil";
  if (role === "admin") return "Administrator";
  if (role === "manager") return "Manager";
  return role;
}
