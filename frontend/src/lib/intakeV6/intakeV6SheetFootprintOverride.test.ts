import { describe, expect, it } from "vitest";

import { validateSheetFootprintOverrideInput } from "./intakeV6SheetFootprintOverride";

describe("validateSheetFootprintOverrideInput", () => {
  it("requires operator note", () => {
    const result = validateSheetFootprintOverrideInput({
      widthCm: 192.67,
      heightCm: 143.389,
      reason: "",
      useForQuoteEstimate: false,
    });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toContain("Notă operator obligatorie");
  });

  it("rejects footprint below eligible when estimate enabled", () => {
    const result = validateSheetFootprintOverrideInput({
      widthCm: 100,
      heightCm: 50,
      reason: "Măsurat în Corel",
      useForQuoteEstimate: true,
      eligibleFaceAreaSqm: 1.2638,
    });
    expect(result.ok).toBe(false);
  });
});