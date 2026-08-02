import { describe, expect, it } from "vitest";
import { blockersFor, executionResultRole, isManagementRole } from "./executionResultWorkspace";

describe("execution result workspace role surface", () => {
  it("keeps costs and closure management-only", () => {
    expect(isManagementRole(executionResultRole("operator"))).toBe(false);
    expect(isManagementRole(executionResultRole("manager"))).toBe(true);
    expect(isManagementRole(executionResultRole("admin"))).toBe(true);
  });

  it("combines missing execution facts and backend alert reasons", () => {
    const blockers = blockersFor(
      { has_plan: false, has_reality: false, reasons: ["data_incomplete"] } as never,
      { alerts: [{ reason: "minutes_over_warning" }] } as never,
    );
    expect(blockers).toEqual([
      "data_incomplete",
      "plan_missing",
      "reality_missing",
      "minutes_over_warning",
    ]);
  });
});
