import { describe, expect, it } from "vitest";
import { resolveIntakeV6ReviewRefetchGroups } from "./intakeV6ReviewRefetchDomains";

describe("resolveIntakeV6ReviewRefetchGroups", () => {
  it("refreshes task preview and readiness for lighting changes without widening to global refetch", () => {
    expect(resolveIntakeV6ReviewRefetchGroups(["lighting"])).toEqual([
      "breakdown",
      "pricing",
      "pricedQuote",
      "productionDryRun",
      "productionHandoff",
      "quoteHandoff",
      "taskPreview",
      "orderBoundReadiness",
    ]);
  });

  it("limits commercial input changes to pricing refreshes", () => {
    expect(resolveIntakeV6ReviewRefetchGroups(["commercial_preview"])).toEqual([
      "pricing",
      "pricedQuote",
    ]);
  });

  it("refreshes task generation, task preview and readiness for template-level changes", () => {
    expect(resolveIntakeV6ReviewRefetchGroups(["template"])).toEqual([
      "breakdown",
      "pricing",
      "pricedQuote",
      "productionDryRun",
      "productionHandoff",
      "quoteHandoff",
      "taskGeneration",
      "taskPreview",
      "orderBoundReadiness",
    ]);
  });
});