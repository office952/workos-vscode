import { describe, expect, it } from "vitest";
import {
  canAccessEmployeeMobileRoute,
  canAccessManagerTeamWorkspace,
  canAccessRequestReviewWorkspace,
  employeeMobileAuthRoleLabel,
  getEmployeeMobileAccessSummary,
  getEmployeeMobileRouteBlockedMessage,
  getEmployeeMobileRouteKeyFromPath,
  shouldProbeEmployeeMobileSelfLink,
} from "./employeeMobileAccess";

describe("canAccessManagerTeamWorkspace", () => {
  it("returns false for employee_mobile (normal self-only user)", () => {
    expect(canAccessManagerTeamWorkspace("employee_mobile")).toBe(false);
  });

  it("returns false for unknown or empty roles", () => {
    expect(canAccessManagerTeamWorkspace(null)).toBe(false);
    expect(canAccessManagerTeamWorkspace(undefined)).toBe(false);
    expect(canAccessManagerTeamWorkspace("viewer")).toBe(false);
    expect(canAccessManagerTeamWorkspace("operator")).toBe(false);
  });

  it("returns true for admin and manager auth roles", () => {
    expect(canAccessManagerTeamWorkspace("admin")).toBe(true);
    expect(canAccessManagerTeamWorkspace("manager")).toBe(true);
  });
});

describe("canAccessRequestReviewWorkspace", () => {
  it("returns false for employee_mobile (normal self-only user)", () => {
    expect(canAccessRequestReviewWorkspace("employee_mobile")).toBe(false);
  });

  it("returns false for unknown or empty roles", () => {
    expect(canAccessRequestReviewWorkspace(null)).toBe(false);
    expect(canAccessRequestReviewWorkspace("viewer")).toBe(false);
  });

  it("returns true for admin and manager auth roles", () => {
    expect(canAccessRequestReviewWorkspace("admin")).toBe(true);
    expect(canAccessRequestReviewWorkspace("manager")).toBe(true);
  });
});

describe("employeeMobileAuthRoleLabel", () => {
  it("maps known roles to Romanian labels", () => {
    expect(employeeMobileAuthRoleLabel("employee_mobile")).toBe("Angajat mobil");
    expect(employeeMobileAuthRoleLabel("admin")).toBe("Administrator");
    expect(employeeMobileAuthRoleLabel("manager")).toBe("Manager");
  });
});

describe("getEmployeeMobileAccessSummary", () => {
  it("returns self-only summary for employee_mobile", () => {
    const summary = getEmployeeMobileAccessSummary("employee_mobile");
    expect(summary.variant).toBe("self");
    expect(summary.description).toMatch(/self-only/i);
  });

  it("returns manager summary for admin", () => {
    const summary = getEmployeeMobileAccessSummary("admin");
    expect(summary.variant).toBe("manager");
    expect(summary.description).toMatch(/review/i);
  });
});

describe("shouldProbeEmployeeMobileSelfLink", () => {
  it("probes for employee_mobile and manager only", () => {
    expect(shouldProbeEmployeeMobileSelfLink("employee_mobile")).toBe(true);
    expect(shouldProbeEmployeeMobileSelfLink("manager")).toBe(true);
    expect(shouldProbeEmployeeMobileSelfLink("admin")).toBe(false);
  });
});

describe("canAccessEmployeeMobileRoute", () => {
  it("allows self routes for employee_mobile", () => {
    expect(canAccessEmployeeMobileRoute("employee_mobile", "home")).toBe(true);
    expect(canAccessEmployeeMobileRoute("employee_mobile", "requests")).toBe(true);
    expect(canAccessEmployeeMobileRoute("employee_mobile", "attendance")).toBe(true);
    expect(canAccessEmployeeMobileRoute("employee_mobile", "tasks")).toBe(true);
  });

  it("blocks review and team for employee_mobile", () => {
    expect(canAccessEmployeeMobileRoute("employee_mobile", "review")).toBe(false);
    expect(canAccessEmployeeMobileRoute("employee_mobile", "team")).toBe(false);
  });

  it("allows review and team for admin and manager", () => {
    expect(canAccessEmployeeMobileRoute("admin", "review")).toBe(true);
    expect(canAccessEmployeeMobileRoute("admin", "team")).toBe(true);
    expect(canAccessEmployeeMobileRoute("manager", "review")).toBe(true);
    expect(canAccessEmployeeMobileRoute("manager", "team")).toBe(true);
  });
});

describe("getEmployeeMobileRouteKeyFromPath", () => {
  it("maps employee-app paths to route keys", () => {
    expect(getEmployeeMobileRouteKeyFromPath("/employee-app")).toBe("home");
    expect(getEmployeeMobileRouteKeyFromPath("/employee-app/")).toBe("home");
    expect(getEmployeeMobileRouteKeyFromPath("/employee-app/review")).toBe("review");
    expect(getEmployeeMobileRouteKeyFromPath("/employee-app/team")).toBe("team");
    expect(getEmployeeMobileRouteKeyFromPath("/employee-app/requests")).toBe("requests");
    expect(getEmployeeMobileRouteKeyFromPath("/employee-app/attendance")).toBe("attendance");
    expect(getEmployeeMobileRouteKeyFromPath("/employee-app/tasks")).toBe("tasks");
  });
});

describe("getEmployeeMobileRouteBlockedMessage", () => {
  it("returns role-specific messages for blocked manager routes", () => {
    expect(getEmployeeMobileRouteBlockedMessage("review")).toMatch(/manager sau administrator/i);
    expect(getEmployeeMobileRouteBlockedMessage("team")).toMatch(/manager sau administrator/i);
  });
});
