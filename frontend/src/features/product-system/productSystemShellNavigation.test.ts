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

  it("declares canonical shell nav without pricing duplicate", () => {
    const labels = PRODUCT_SYSTEM_SHELL_NAV.map((item) => item.label);
    expect(labels).toEqual([
      "Products",
      "Components",
      "Resources",
      "Operations",
      "Dependencies",
      "Validation",
      "Advanced",
    ]);
    expect(labels.some((label) => /pricing/i.test(label))).toBe(false);
  });

  it("marks future sections as planned only", () => {
    const planned = PRODUCT_SYSTEM_SHELL_NAV.filter((item) => item.plannedSection);
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
