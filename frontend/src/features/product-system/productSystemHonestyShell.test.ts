import { describe, expect, it } from "vitest";
import {
  PRODUCT_SYSTEM_PLANNED_BADGE_RO,
  PRODUCT_SYSTEM_PLANNED_SECTION_MESSAGE,
  PRODUCT_SYSTEM_SHELL_NAV,
} from "@/features/product-system/productSystemShellConfig";

describe("productSystemHonestyShell", () => {
  it("keeps Products operational and marks peers Planificat", () => {
    const products = PRODUCT_SYSTEM_SHELL_NAV.find((item) => item.id === "products");
    expect(products?.plannedSection).toBeFalsy();
    const planned = PRODUCT_SYSTEM_SHELL_NAV.filter((item) => item.plannedSection);
    expect(planned.map((item) => item.id)).toEqual([
      "components",
      "resources",
      "operations",
      "dependencies",
      "validation",
      "advanced",
    ]);
    expect(PRODUCT_SYSTEM_PLANNED_BADGE_RO).toBe("Planificat");
    expect(PRODUCT_SYSTEM_PLANNED_SECTION_MESSAGE).toMatch(/nu este operațională/i);
  });
});
