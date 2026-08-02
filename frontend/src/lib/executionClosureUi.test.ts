import { describe, expect, it } from "vitest";
import { closureReasonRo, closureStateLabel } from "./executionClosureUi";

describe("executionClosureUi", () => {
  it("maps material and labor blockers to Romanian guidance", () => {
    expect(closureReasonRo("actual_material_cost_missing")).toMatch(/material/i);
    expect(closureReasonRo("actual_labor_cost_incomplete")).toMatch(/muncă|manoper/i);
    expect(closureReasonRo("unknown_code")).toMatch(/unknown_code/);
  });

  it("labels closed vs blocked vs ready states", () => {
    expect(closureStateLabel({ ready: true, closed: false, loading: false }).tone).toBe("ready");
    expect(closureStateLabel({ ready: false, closed: false, loading: false }).tone).toBe(
      "blocked",
    );
    expect(closureStateLabel({ ready: false, closed: true, loading: false }).tone).toBe("closed");
  });
});
