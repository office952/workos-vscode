import { describe, expect, it } from "vitest";
import {
  formatIntakeProductFamilyLabel,
  isUnresolvedIntakeProductFamily,
  UNRESOLVED_INTAKE_PRODUCT_FAMILY_LABEL,
} from "./intakeProductFamilyDisplay";

describe("intakeProductFamilyDisplay", () => {
  it("treats empty product_family as unresolved", () => {
    expect(isUnresolvedIntakeProductFamily("")).toBe(true);
    expect(isUnresolvedIntakeProductFamily("   ")).toBe(true);
    expect(isUnresolvedIntakeProductFamily(null)).toBe(true);
  });

  it("formats unresolved family as Nespecificat, not internal slug", () => {
    expect(formatIntakeProductFamilyLabel("")).toBe(UNRESOLVED_INTAKE_PRODUCT_FAMILY_LABEL);
    expect(formatIntakeProductFamilyLabel("servicii_montaj")).toBe("servicii_montaj");
  });
});
