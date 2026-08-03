import { describe, expect, it } from "vitest";
import {
  commercialReferenceLabel,
  shouldDisplayCommercialRateValue,
} from "./templatePricingCommercialReference";

describe("templatePricingCommercialReference", () => {
  it("labels Owner missing / provisional / published honestly", () => {
    expect(commercialReferenceLabel("ACTIVE_MISSING_RATE")).toBe("Lipsă tarif Owner");
    expect(commercialReferenceLabel("ACTIVE_PROVISIONAL")).toBe("Tarif provizoriu");
    expect(commercialReferenceLabel("ACTIVE_PUBLISHED")).toBe("Publicat (catalog)");
    expect(commercialReferenceLabel("BLOCKED_BY_POLICY")).toBe("Blocat de politică");
  });

  it("displays resolved provisional rates (never treats provisional as missing)", () => {
    expect(
      shouldDisplayCommercialRateValue({
        currentValue: 15,
        commercialReferenceStatus: "ACTIVE_PROVISIONAL",
        status: "warning",
      }),
    ).toBe(true);
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
