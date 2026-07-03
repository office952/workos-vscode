import { describe, expect, it } from "vitest";
import {
  PROFITABILITY_STATUS_LABELS,
  PROFITABILITY_WARNING_LABELS,
} from "./profitabilityAnalysis";

describe("profitabilityAnalysis labels", () => {
  it("maps estimated_only status for operator display", () => {
    expect(PROFITABILITY_STATUS_LABELS.estimated_only).toBe("Estimated only");
  });

  it("maps known warnings without implying final profit", () => {
    expect(PROFITABILITY_WARNING_LABELS.execution_reality_missing).toContain(
      "not recorded",
    );
    expect(PROFITABILITY_WARNING_LABELS.actual_costing_not_available).toContain(
      "not available",
    );
  });
});
