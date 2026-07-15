import { describe, expect, it, vi } from "vitest";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  canShowClaimOnly,
  CLAIM_ONLY_LABEL,
  mapEmployeeMobileClaimError,
} from "@/lib/employeeMobileV2ClaimAction";
import { startFixtureAvailableStartable, startFixtureReadinessBlocked } from "@/lib/employeeMobileV2StartFixtures";

vi.mock("@/api/employeeMobileTasks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/employeeMobileTasks")>();
  return {
    ...actual,
    claimEmployeeMobileTask: vi.fn(),
  };
});

describe("employeeMobileV2ClaimAction", () => {
  it("shows claim-only when backend can_claim without start-from-available", () => {
    const task: EmployeeMobileTaskDTO = {
      ...startFixtureReadinessBlocked,
      is_available_for_claim: true,
      can_claim: true,
      can_start_from_available: false,
      can_start: false,
    };
    expect(canShowClaimOnly(task)).toBe(true);
  });

  it("hides claim-only when start-from-available is primary", () => {
    const task: EmployeeMobileTaskDTO = {
      ...startFixtureAvailableStartable,
    };
    expect(canShowClaimOnly(task)).toBe(false);
  });

  it("maps assignment conflict errors", () => {
    expect(
      mapEmployeeMobileClaimError({ code: "task_already_assigned", message: "x" }),
    ).toContain("preluat");
  });

  it("exports claim label", () => {
    expect(CLAIM_ONLY_LABEL).toBe("Preiau sarcina");
  });
});
