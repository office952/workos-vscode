import { describe, expect, it } from "vitest";
import {
  commercialReferenceLabel,
  shouldDisplayCommercialRateValue,
} from "./templatePricingCommercialReference";

describe("templatePricingCommercialReference", () => {
  it("labels Owner missing rate without implying published", () => {
    expect(commercialReferenceLabel("ACTIVE_MISSING_RATE")).toBe("Lipsă tarif Owner");
    expect(commercialReferenceLabel("ACTIVE_PUBLISHED")).toBe("Publicat (catalog)");
    expect(commercialReferenceLabel("BLOCKED_BY_POLICY")).toBe("Blocat de politică");
  });

  it("never displays a numeric value for missing commercial rates (including 0)", () => {
    expect(
      shouldDisplayCommercialRateValue({
        currentValue: 0,
        commercialReferenceStatus: "ACTIVE_MISSING_RATE",
        status: "missing",
      }),
    ).toBe(false);
    expect(
      shouldDisplayCommercialRateValue({
        currentValue: 5,
        commercialReferenceStatus: "ACTIVE_PUBLISHED",
        status: "active",
      }),
    ).toBe(true);
    expect(
      shouldDisplayCommercialRateValue({
        currentValue: null,
        commercialReferenceStatus: "ACTIVE_MISSING_RATE",
        status: "missing",
      }),
    ).toBe(false);
  });
});
