import { describe, expect, it } from "vitest";
import {
  ADMIN_TRUTH_FLOW_STEPS,
  adminTruthFlowStep,
} from "./adminProductTruthUi";

describe("adminProductTruthUi", () => {
  it("keeps the product administration flow ordered and explicit", () => {
    expect(ADMIN_TRUTH_FLOW_STEPS.map((step) => step.id)).toEqual([
      "product",
      "templates",
      "pricing",
      "equipment",
      "settings",
    ]);
    expect(adminTruthFlowStep("equipment").description).toMatch(/capacitate/i);
  });
});
