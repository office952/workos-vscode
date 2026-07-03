import { describe, expect, it } from "vitest";
import type { EmployeeDTO } from "@/api/costEngine";
import {
  employeeAuthRoleLabel,
  employeeHasMobileAccess,
  employeeIsLinkedToUser,
  employeeMatchesMobileQuickFilter,
  employeeSearchHaystack,
  getEmployeeMobileAccessDisplay,
} from "./employeeAdminAccess";

const linkedMobile: EmployeeDTO = {
  id: 1,
  name: "Calin Cimpean",
  status: "active",
  employee_type: "productive",
  valid_for_cost_engine: true,
  user_id: "dev-employee-test-001",
  auth_email: "test.employee@local",
  auth_role: "employee_mobile",
  is_linked_to_user: true,
  has_mobile_access: true,
};

const linkedInactive: EmployeeDTO = {
  ...linkedMobile,
  id: 2,
  status: "inactive",
  has_mobile_access: false,
};

const unlinked: EmployeeDTO = {
  id: 3,
  name: "No User",
  status: "active",
  employee_type: "productive",
  valid_for_cost_engine: false,
  user_id: null,
  is_linked_to_user: false,
  has_mobile_access: false,
};

describe("employeeAdminAccess helpers", () => {
  it("detects mobile access from API flags", () => {
    expect(employeeHasMobileAccess(linkedMobile)).toBe(true);
    expect(employeeHasMobileAccess(linkedInactive)).toBe(false);
    expect(employeeHasMobileAccess(unlinked)).toBe(false);
  });

  it("detects linked user", () => {
    expect(employeeIsLinkedToUser(linkedMobile)).toBe(true);
    expect(employeeIsLinkedToUser(unlinked)).toBe(false);
  });

  it("returns display labels for mobile access states", () => {
    expect(getEmployeeMobileAccessDisplay(linkedMobile).label).toBe("Mobile activ");
    expect(getEmployeeMobileAccessDisplay(linkedInactive).variant).toBe("linked");
    expect(getEmployeeMobileAccessDisplay(unlinked).label).toBe("Fără cont mobil");
  });

  it("filters mobile quick filters", () => {
    expect(employeeMatchesMobileQuickFilter(linkedMobile, "mobile")).toBe(true);
    expect(employeeMatchesMobileQuickFilter(unlinked, "mobile")).toBe(false);
    expect(employeeMatchesMobileQuickFilter(unlinked, "no_mobile")).toBe(true);
  });

  it("includes auth fields in search haystack", () => {
    const hay = employeeSearchHaystack(linkedMobile);
    expect(hay).toContain("dev-employee-test-001");
    expect(hay).toContain("test.employee@local");
  });

  it("maps auth roles to Romanian labels", () => {
    expect(employeeAuthRoleLabel("employee_mobile")).toBe("Angajat mobil");
    expect(employeeAuthRoleLabel("admin")).toBe("Administrator");
  });
});
