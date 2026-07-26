import { Wrench } from "lucide-react";
import { describe, expect, it } from "vitest";
import {
  acmPanelOnlyReviewTabs,
  isAcmPanelOnlyComposition,
  resolveAcmPanelOnlyUiScope,
} from "./acmPanelOnlyComposition";

describe("isAcmPanelOnlyComposition", () => {
  it("detects support_only recommendation", () => {
    expect(
      isAcmPanelOnlyComposition({
        product_composition_recommendation: { composition_type: "support_only" },
      }),
    ).toBe(true);
  });

  it("detects confirmed ACM-only items", () => {
    expect(
      isAcmPanelOnlyComposition({
        product_composition_confirmed: {
          confirmed: true,
          items: [{ template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" }],
        },
      }),
    ).toBe(true);
  });

  it("rejects letters + support", () => {
    expect(
      isAcmPanelOnlyComposition({
        product_composition_recommendation: { composition_type: "letters_plus_support" },
        product_composition_confirmed: {
          confirmed: true,
          items: [
            { template_code: "TPL-VOLUMETRIC-LETTERS_v2" },
            { template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" },
          ],
        },
      }),
    ).toBe(false);
  });
});

describe("acmPanelOnlyReviewTabs", () => {
  it("keeps only montaj with ACM hint", () => {
    const tabs = acmPanelOnlyReviewTabs([
      { id: "finisaje", label: "Finisaje", hint: "x", icon: Wrench, moduleCodes: [] },
      { id: "montaj", label: "Montaj", hint: "y", icon: Wrench, moduleCodes: ["mounting"] },
    ]);
    expect(tabs).toHaveLength(1);
    expect(tabs[0]?.id).toBe("montaj");
    expect(tabs[0]?.hint).toMatch(/Alucobond/i);
  });
});

describe("resolveAcmPanelOnlyUiScope", () => {
  it("teaches in-scope panou needs and out-of-scope letter adhesive", () => {
    const scope = resolveAcmPanelOnlyUiScope({
      product_composition_recommendation: { composition_type: "support_only" },
    });
    expect(scope.isAcmPanelOnly).toBe(true);
    expect(scope.scopeChipLabelRo).toMatch(/Alucobond/i);
    expect(scope.inScopeNeedsRo.some((s) => /geometrie/i.test(s))).toBe(true);
    expect(scope.outOfScopeNeedsRo.some((s) => /adeziv/i.test(s))).toBe(true);
  });
});
