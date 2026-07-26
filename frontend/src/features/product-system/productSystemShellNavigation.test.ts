import { describe, expect, it } from "vitest";
import { can } from "@/lib/rbac";
import {
  PRODUCT_SYSTEM_ADVANCED_PERMISSION,
  PRODUCT_SYSTEM_SHELL_NAV,
} from "@/features/product-system/productSystemShellConfig";

describe("productSystemShellNavigation", () => {
  it("uses existing view:governance for Advanced visibility", () => {
    expect(PRODUCT_SYSTEM_ADVANCED_PERMISSION).toBe("view:governance");
    expect(can("admin", PRODUCT_SYSTEM_ADVANCED_PERMISSION)).toBe(true);
    expect(can("manager", PRODUCT_SYSTEM_ADVANCED_PERMISSION)).toBe(false);
    expect(can("operator", PRODUCT_SYSTEM_ADVANCED_PERMISSION)).toBe(false);
  });

  it("declares shell nav without pricing duplicate", () => {
    const labels = PRODUCT_SYSTEM_SHELL_NAV.map((item) => item.label);
    expect(labels).toEqual([
      "Products",
      "Module produs (amânat)",
      "Resources",
      "Operations",
      "Dependencies",
      "Validation",
      "Advanced",
    ]);
    expect(labels.some((label) => /pricing/i.test(label))).toBe(false);
  });

  it("keeps planned sections out of primary operational chrome", () => {
    const operational = PRODUCT_SYSTEM_SHELL_NAV.filter((item) => !item.plannedSection);
    const planned = PRODUCT_SYSTEM_SHELL_NAV.filter((item) => item.plannedSection);
    expect(operational.map((item) => item.id)).toEqual(["products"]);
    expect(planned.map((item) => item.id)).toEqual([
      "components",
      "resources",
      "operations",
      "dependencies",
      "validation",
      "advanced",
    ]);
  });
});
