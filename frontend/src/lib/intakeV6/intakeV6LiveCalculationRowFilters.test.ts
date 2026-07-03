import { describe, expect, it } from "vitest";
import {
  filterLiveCalcRows,
  liveCalcRowMatchesFilter,
  parseLiveCalcRowCost,
  resolveLiveCalcFilterOptions,
  sumFilteredLiveCalcRows,
} from "@/lib/intakeV6/intakeV6LiveCalculationRowFilters";
import type { IntakeV6LiveMaterialUsedRow } from "@/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay";

const sampleRows: IntakeV6LiveMaterialUsedRow[] = [
  {
    groupKey: "plexi_letters",
    label: "Plexiglas litere",
    quantityText: "1 m²",
    costText: "16.00 EUR",
    muted: false,
  },
  {
    groupKey: "led_modules",
    label: "Module LED",
    quantityText: "10 buc",
    costText: "5.00 EUR",
    muted: false,
  },
  {
    groupKey: "edge_oracal_application",
    label: "Aplicare cant",
    quantityText: "2 m",
    costText: "tarif lipsă",
    muted: true,
  },
];

describe("intakeV6LiveCalculationRowFilters", () => {
  it("returns all rows for all filter", () => {
    expect(filterLiveCalcRows(sampleRows, "all")).toHaveLength(3);
  });

  it("filters lighting and missing rates", () => {
    expect(filterLiveCalcRows(sampleRows, "lighting").map((r) => r.groupKey)).toEqual(["led_modules"]);
    expect(filterLiveCalcRows(sampleRows, "missing_rates").map((r) => r.groupKey)).toEqual([
      "edge_oracal_application",
    ]);
  });

  it("omits artwork filter and exposes Fără tarif only when missing rates exist", () => {
    const withMissing = resolveLiveCalcFilterOptions(sampleRows);
    expect(withMissing.map((o) => o.id)).not.toContain("artwork");
    expect(withMissing.some((o) => o.id === "missing_rates")).toBe(true);

    const pricedOnly = resolveLiveCalcFilterOptions([sampleRows[0]!]);
    expect(pricedOnly.some((o) => o.id === "missing_rates")).toBe(false);
  });

  it("sums filtered row costs for subtotal footer", () => {
    expect(parseLiveCalcRowCost("16.00 EUR")).toBe(16);
    expect(parseLiveCalcRowCost("tarif lipsă")).toBeNull();
    const totals = sumFilteredLiveCalcRows(sampleRows.slice(0, 2));
    expect(totals.subtotal).toBe(21);
    expect(totals.lineCount).toBe(2);
  });

  it("classifies materials excluding known operation keys", () => {
    expect(liveCalcRowMatchesFilter(sampleRows[0], "materials")).toBe(true);
    expect(liveCalcRowMatchesFilter(sampleRows[1], "materials")).toBe(false);
  });
});
