import { describe, expect, it } from "vitest";
import {
  eligibilityStatusLabel,
  eligibilityStatusTone,
} from "./employeeEligibilityDisplay";

describe("employeeEligibilityDisplay", () => {
  it("labels ready as eligible candidate", () => {
    expect(eligibilityStatusLabel("ready")).toContain("eligibil");
    expect(eligibilityStatusTone("ready")).toBe("success");
  });

  it("labels missing requirements as not configured", () => {
    expect(eligibilityStatusLabel("blocked_missing_requirements")).toContain("neconfigurată");
    expect(eligibilityStatusTone("blocked_missing_requirements")).toBe("danger");
  });

  it("labels not_required as not applicable", () => {
    expect(eligibilityStatusLabel("not_required")).toContain("Neaplicabil");
    expect(eligibilityStatusTone("not_required")).toBe("warning");
  });
});
