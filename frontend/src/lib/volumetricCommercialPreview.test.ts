import { describe, expect, it } from "vitest";
import { computeCommercialPreviewBreakdown } from "./volumetricCommercialPreview";

describe("computeCommercialPreviewBreakdown", () => {
  const cost = 768.68;

  it("computes 25% markup and 19% VAT totals", () => {
    const row = computeCommercialPreviewBreakdown({
      productionCost: cost,
      marginPct: 25,
      discountPct: 0,
      vatPct: 19,
    });
    expect(row).not.toBeNull();
    expect(row!.markupValue).toBeCloseTo(192.17, 2);
    expect(row!.priceBeforeVat).toBeCloseTo(960.85, 2);
    expect(row!.totalWithVat).toBeCloseTo(1143.41, 2);
  });

  it("computes 50% markup with higher total than 25%", () => {
    const at25 = computeCommercialPreviewBreakdown({
      productionCost: cost,
      marginPct: 25,
      discountPct: 0,
      vatPct: 19,
    });
    const at50 = computeCommercialPreviewBreakdown({
      productionCost: cost,
      marginPct: 50,
      discountPct: 0,
      vatPct: 19,
    });
    expect(at50!.totalWithVat).toBeGreaterThan(at25!.totalWithVat);
    expect(at50!.totalWithVat).toBeCloseTo(1372.09, 2);
  });

  it("applies discount before VAT", () => {
    const row = computeCommercialPreviewBreakdown({
      productionCost: cost,
      marginPct: 25,
      discountPct: 10,
      vatPct: 19,
    });
    expect(row!.discountValue).toBeGreaterThan(0);
    expect(row!.subtotalBeforeVat).toBeLessThan(row!.priceBeforeVat);
    expect(row!.totalWithVat).toBeLessThan(1143.41);
  });

  it("returns null for non-positive production cost", () => {
    expect(
      computeCommercialPreviewBreakdown({
        productionCost: 0,
        marginPct: 25,
        discountPct: 0,
        vatPct: 19,
      })
    ).toBeNull();
  });
});
