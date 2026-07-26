import { describe, expect, it } from "vitest";
import {
  classifyInventoryUiTab,
  computeInventoryStockStatus,
  formatStockQuantity,
} from "./inventoryMaterialClassification";

describe("inventoryMaterialClassification", () => {
  it("classifies plates from live category without mock IDs", () => {
    expect(
      classifyInventoryUiTab({ category: "panou_compozit", code: "MAT-ACM-BOND-3MM" })
    ).toBe("placi");
    expect(
      classifyInventoryUiTab({ category: "plexiglas", code: "MAT-PLEXI-TRANSP-10MM" })
    ).toBe("placi");
  });

  it("classifies rolls from live category", () => {
    expect(classifyInventoryUiTab({ category: "vinyl", code: "MAT-ORACAL-651" })).toBe("role");
    expect(classifyInventoryUiTab({ category: "banner", code: "MAT-BANNER-510" })).toBe("role");
  });

  it("puts LED/profiles/consumables in altele", () => {
    expect(classifyInventoryUiTab({ category: "iluminat_led", code: "MAT-LED-MODULE" })).toBe(
      "altele"
    );
    expect(classifyInventoryUiTab({ category: "profil_metal", code: "MAT-PROFIL-ALU" })).toBe(
      "altele"
    );
  });

  it("treats null stock as untracked, not out_of_stock", () => {
    expect(computeInventoryStockStatus({ stockCurrent: null, stockMin: 10 })).toBe("untracked");
    expect(computeInventoryStockStatus({ stockCurrent: 0, stockMin: 10 })).toBe("out_of_stock");
    expect(computeInventoryStockStatus({ stockCurrent: 5, stockMin: 10 })).toBe("critical");
  });

  it("formats untracked quantity without inventing zero", () => {
    expect(formatStockQuantity(null, "mp")).toBe("— mp");
    expect(formatStockQuantity(0, "mp")).toBe("0 mp");
  });
});
