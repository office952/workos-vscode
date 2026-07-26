import { describe, expect, it, vi } from "vitest";
import { priceExistingQuote, priceQuote, QuotePricingError } from "@/api/quotes";
import { LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO } from "@/lib/legacyQuotePriceRetirement";

describe("legacy quote price client isolation", () => {
  it("priceQuote refuses without network call", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    await expect(
      priceQuote({
        product_template: { id: 1 } as never,
        user_config: { quantity: 1, dimensions: { width_mm: 1, height_mm: 1, depth_mm: 1 } },
        pricing: { margin_pct: 0, vat_pct: 19, discount_pct: 0 },
        client_name: "X",
      }),
    ).rejects.toBeInstanceOf(QuotePricingError);
    await expect(
      priceQuote({
        product_template: { id: 1 } as never,
        user_config: { quantity: 1, dimensions: { width_mm: 1, height_mm: 1, depth_mm: 1 } },
        pricing: { margin_pct: 0, vat_pct: 19, discount_pct: 0 },
        client_name: "X",
      }),
    ).rejects.toMatchObject({
      message: LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO,
      status: 410,
    });
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });

  it("priceExistingQuote refuses without network call", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    await expect(
      priceExistingQuote(12, {
        product_template: { id: 1 } as never,
        user_config: { quantity: 1, dimensions: { width_mm: 1, height_mm: 1, depth_mm: 1 } },
        pricing: { margin_pct: 0, vat_pct: 19, discount_pct: 0 },
        client_name: "X",
      }),
    ).rejects.toMatchObject({ status: 410 });
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });
});
