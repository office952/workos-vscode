import { describe, expect, it } from "vitest";
import type { PricingRegistryItem } from "@/api/pricingRegistry";
import {
  classifyWorkcenterTypedCatalog,
  filterByTypedCatalogView,
  hasRateBasisMismatch,
  resolveMachineFamily,
  resolveTypedCatalog,
} from "./pricingTypedCatalog";

function item(partial: Partial<PricingRegistryItem>): PricingRegistryItem {
  return {
    pricing_code: "X",
    display_name: "X",
    pricing_kind: "operation_rate",
    registry_category: "Operații / Rate",
    unit: "EUR/ml",
    base_cost: 1,
    currency: "EUR",
    status: "active",
    confidence: "owner_confirmed",
    used_by_templates: [],
    affects_quote_calculation: true,
    technical_source: "workcenter_rates",
    ...partial,
  };
}

describe("pricingTypedCatalog", () => {
  it("classifies CNC mechanical vs laser", () => {
    expect(classifyWorkcenterTypedCatalog("CNC_ROUTER")).toBe("machine_operation");
    expect(resolveMachineFamily(item({ pricing_code: "CNC_ROUTER" }))).toBe("cnc_mechanical");
    expect(resolveMachineFamily(item({ pricing_code: "LASER_CUTTING" }))).toBe("cnc_laser");
  });

  it("prefers API typed_catalog when present", () => {
    expect(
      resolveTypedCatalog(
        item({ pricing_code: "FOO", typed_catalog: "labor", pricing_kind: "operation_rate" })
      )
    ).toBe("labor");
  });

  it("filters typed views without dropping unmatched unknown into materials", () => {
    const rows = [
      item({ pricing_code: "MAT-A", pricing_kind: "material", typed_catalog: "material" }),
      item({ pricing_code: "CNC_ROUTER", typed_catalog: "machine_operation" }),
      item({ pricing_code: "LAMINATION", typed_catalog: "service" }),
      item({ pricing_code: "WEIRD", typed_catalog: "unknown" }),
    ];
    expect(filterByTypedCatalogView(rows, "material")).toHaveLength(1);
    expect(filterByTypedCatalogView(rows, "machine_operation")).toHaveLength(1);
    expect(filterByTypedCatalogView(rows, "labor_service").map((r) => r.pricing_code)).toEqual([
      "LAMINATION",
      "WEIRD",
    ]);
    expect(filterByTypedCatalogView(rows, "all")).toHaveLength(4);
  });

  it("detects rate basis mismatch flag", () => {
    expect(
      hasRateBasisMismatch(
        item({ data_quality_flags: ["rate_basis_column_mismatch"] })
      )
    ).toBe(true);
  });
});
