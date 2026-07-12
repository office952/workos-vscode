import { describe, expect, it } from "vitest";

import { isSoldModuleVisible, resolveSoldScopeFieldVisibility } from "./intakeV6SoldScopeVisibility";

describe("intakeV6SoldScopeVisibility", () => {
  it("keeps full product visibility unchanged", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "full_product", sold_modules: [] },
      offer_scope_confirmed: { confirmed: true },
    });
    expect(visibility).toMatchObject({ face: true, returnCant: true, back: true });
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
    expect(visibility).toMatchObject({ face: false, returnCant: false, back: true });
  });

  it("shows union for FACE + RETURN-CANT", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "component_subset", sold_modules: ["RETURN-CANT", "FACE"] },
    });
    expect(visibility).toMatchObject({ face: true, returnCant: true, back: false });
    expect(isSoldModuleVisible(visibility, "FACE")).toBe(true);
    expect(isSoldModuleVisible(visibility, "BACK")).toBe(false);
  });
});
