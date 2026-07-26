import { describe, expect, it } from "vitest";
import {
  isPricingStudioEligibleModule,
  showTemplatePricingStudio,
} from "./templatePricingStudioEligibility";

describe("templatePricingStudioEligibility", () => {
  it("exposes pricing studio for Volum Aluminiu module without product bucket", () => {
    expect(isPricingStudioEligibleModule("TPL-VOLUM-ALUMINIU_v1")).toBe(true);
    expect(
      showTemplatePricingStudio({
        isProduct: false,
        templateCode: "TPL-VOLUM-ALUMINIU_v1",
      }),
    ).toBe(true);
  });

  it("keeps unrelated modules without pricing tab", () => {
    expect(isPricingStudioEligibleModule("TPL-COMP-FACE-v1")).toBe(false);
    expect(
      showTemplatePricingStudio({
        isProduct: false,
        templateCode: "TPL-COMP-FACE-v1",
      }),
    ).toBe(false);
  });

  it("keeps products eligible", () => {
    expect(
      showTemplatePricingStudio({
        isProduct: true,
        templateCode: "TPL-VOLUMETRIC-LETTERS_v2",
      }),
    ).toBe(true);
  });
});
