import { describe, expect, it } from "vitest";
import { Layers, Lightbulb, Wrench } from "lucide-react";

import {
  filterReviewTabsBySoldScope,
  isSoldModuleVisible,
  resolveActiveReviewTabForScope,
  resolveSoldScopeFieldVisibility,
} from "./intakeV6SoldScopeVisibility";
import type { IntakeV6ReviewTabDefinition } from "./intakeV6ProductPlugin";

const GOLDEN_TABS: IntakeV6ReviewTabDefinition[] = [
  { id: "finisaje", label: "Finisaje", hint: "x", icon: Layers, moduleCodes: [] },
  { id: "iluminare", label: "Iluminare", hint: "x", icon: Lightbulb, moduleCodes: [] },
  { id: "montaj", label: "Montaj", hint: "x", icon: Wrench, moduleCodes: [] },
];

describe("intakeV6SoldScopeVisibility", () => {
  it("keeps full product visibility unchanged", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "full_product", sold_modules: [] },
      offer_scope_confirmed: { confirmed: true },
    });
    expect(visibility).toMatchObject({ face: true, returnCant: true, back: true });
  });

  it("ACM panel-alone composition suppresses VL letter modules even under full_product", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "full_product", sold_modules: [] },
      product_composition_recommendation: { composition_type: "support_only" },
    });
    expect(visibility).toMatchObject({
      face: false,
      returnCant: false,
      back: false,
      lighting: false,
      electrical: false,
    });
  });

  it("shows FACE only", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "component_subset", sold_modules: ["FACE"] },
    });
    expect(visibility).toMatchObject({ face: true, returnCant: false, back: false });
  });

  it("shows RETURN-CANT only", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "component_subset", sold_modules: ["RETURN-CANT"] },
    });
    expect(visibility).toMatchObject({ face: false, returnCant: true, back: false });
  });

  it("shows BACK only", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "component_subset", sold_modules: ["BACK"] },
    });
    expect(visibility).toMatchObject({ face: false, returnCant: false, back: true, lighting: false, electrical: false });
  });

  it("shows LIGHTING only", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "component_subset", sold_modules: ["LIGHTING"] },
    });
    expect(visibility).toMatchObject({ lighting: true, electrical: false });
  });

  it("shows ELECTRICAL only", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "component_subset", sold_modules: ["ELECTRICAL"] },
    });
    expect(visibility).toMatchObject({ lighting: false, electrical: true });
  });

  it("shows union for FACE + RETURN-CANT", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "component_subset", sold_modules: ["RETURN-CANT", "FACE"] },
    });
    expect(visibility).toMatchObject({ face: true, returnCant: true, back: false });
    expect(isSoldModuleVisible(visibility, "FACE")).toBe(true);
    expect(isSoldModuleVisible(visibility, "BACK")).toBe(false);
  });

  it("keeps golden three tabs for full product", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "full_product", sold_modules: [] },
    });
    expect(filterReviewTabsBySoldScope(GOLDEN_TABS, visibility)?.map((t) => t.id)).toEqual([
      "finisaje",
      "iluminare",
      "montaj",
    ]);
  });

  it("silences Iluminare and Montaj for CANT-only", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "component_subset", sold_modules: ["RETURN-CANT"] },
    });
    expect(filterReviewTabsBySoldScope(GOLDEN_TABS, visibility)?.map((t) => t.id)).toEqual([
      "finisaje",
    ]);
    expect(resolveActiveReviewTabForScope("montaj", filterReviewTabsBySoldScope(GOLDEN_TABS, visibility))).toBe(
      "finisaje",
    );
  });

  it("silences Iluminare and Montaj for FACE-only and FACE+CANT", () => {
    for (const sold of [["FACE"], ["FACE", "RETURN-CANT"]] as const) {
      const visibility = resolveSoldScopeFieldVisibility({
        offer_scope: { mode: "component_subset", sold_modules: [...sold] },
      });
      expect(filterReviewTabsBySoldScope(GOLDEN_TABS, visibility)?.map((t) => t.id)).toEqual([
        "finisaje",
      ]);
    }
  });
});
