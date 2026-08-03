import { describe, expect, it } from "vitest";
import type { IntakeV6CommercialProductBreakdown } from "@/lib/intakeV6/intakeV6PricedQuoteTypes";
import {
  OFFER_CURRENCY_MIX_MESSAGE,
  OFFER_PRODUCT_BLOCKED_MESSAGE,
  buildOfferProductSummary,
  formatOfferMoney,
  offerSubtotalLabel,
  offerTaxNote,
} from "@/lib/intakeV6/intakeV6OfferProductSummary";

function buildBreakdown(
  overrides: Partial<IntakeV6CommercialProductBreakdown> = {},
): IntakeV6CommercialProductBreakdown {
  return {
    products: [
      {
        product_key: "letters",
        label: "Litere volumetrice",
        line_codes: ["commercial.letters_face"],
        subtotals_by_currency: [{ currency: "EUR", subtotal: 1200.5 }],
        blocked: false,
        blocker_codes: [],
      },
      {
        product_key: "acm_panel",
        label: "Panou ACM",
        line_codes: ["commercial.acm_face"],
        subtotals_by_currency: [{ currency: "EUR", subtotal: 86.77 }],
        blocked: false,
        blocker_codes: [],
      },
    ],
    subtotals_by_currency: [{ currency: "EUR", subtotal: 1287.27 }],
    currency_mix_detected: false,
    complete_offer_total: 1287.27,
    complete_offer_total_currency: "EUR",
    complete_offer_total_unavailable_reason: null,
    tax_status: "tax_exclusive",
    vat_policy_source: null,
    vat_rate_percent: null,
    ...overrides,
  };
}

describe("buildOfferProductSummary", () => {
  it("returns null when the backend supplied no breakdown", () => {
    expect(buildOfferProductSummary(null)).toBeNull();
    expect(buildOfferProductSummary(undefined)).toBeNull();
  });

  it("exposes one row per product with its own currency amounts", () => {
    const vm = buildOfferProductSummary(buildBreakdown());

    expect(vm).not.toBeNull();
    expect(vm!.products).toHaveLength(2);
    expect(vm!.products[0]).toEqual({
      productKey: "letters",
      label: "Litere volumetrice",
      amounts: [{ currency: "EUR", subtotal: 1200.5 }],
      blocked: false,
      blockerCodes: [],
    });
    expect(vm!.products[1].productKey).toBe("acm_panel");
  });

  it("keeps every currency bucket of a multi-currency product separate", () => {
    const vm = buildOfferProductSummary(
      buildBreakdown({
        products: [
          {
            product_key: "letters",
            label: "Litere volumetrice",
            line_codes: [],
            subtotals_by_currency: [
              { currency: "EUR", subtotal: 100 },
              { currency: "RON", subtotal: 250 },
            ],
            blocked: false,
            blocker_codes: [],
          },
        ],
      }),
    );

    expect(vm!.products[0].amounts).toEqual([
      { currency: "EUR", subtotal: 100 },
      { currency: "RON", subtotal: 250 },
    ]);
  });

  it("uses the single-currency total the backend decided", () => {
    const vm = buildOfferProductSummary(buildBreakdown());

    expect(vm!.total).toEqual({
      kind: "available",
      amount: 1287.27,
      currency: "EUR",
      partial: false,
      pendingLineCodes: [],
    });
    expect(vm!.currencyMixDetected).toBe(false);
  });

  it("labels the total as partial when Owner-pending lines are excluded from it", () => {
    const vm = buildOfferProductSummary(
      buildBreakdown({
        complete_offer_total_is_partial: true,
        pending_line_codes: ["montaj", "ambalare"],
      }),
    );

    expect(vm!.total).toEqual({
      kind: "available",
      amount: 1287.27,
      currency: "EUR",
      partial: true,
      pendingLineCodes: ["montaj", "ambalare"],
    });
  });

  it("infers a partial total from pending line codes even without the explicit flag", () => {
    const vm = buildOfferProductSummary(buildBreakdown({ pending_line_codes: ["montaj"] }));

    expect(vm!.total.kind).toBe("available");
    expect(vm!.total.kind === "available" && vm!.total.partial).toBe(true);
  });

  it("reports the total as unavailable when currencies are mixed", () => {
    const vm = buildOfferProductSummary(
      buildBreakdown({
        subtotals_by_currency: [
          { currency: "EUR", subtotal: 1200.5 },
          { currency: "RON", subtotal: 430 },
        ],
        currency_mix_detected: true,
        complete_offer_total: null,
        complete_offer_total_currency: null,
        complete_offer_total_unavailable_reason: "COMMERCIAL_CURRENCY_MIX_UNRESOLVED",
      }),
    );

    expect(vm!.total).toEqual({
      kind: "unavailable",
      reasonCode: "COMMERCIAL_CURRENCY_MIX_UNRESOLVED",
      message: OFFER_CURRENCY_MIX_MESSAGE,
    });
  });

  it("reports the total as unavailable when a product is blocked", () => {
    const vm = buildOfferProductSummary(
      buildBreakdown({
        products: [
          {
            product_key: "letters",
            label: "Litere volumetrice",
            line_codes: [],
            subtotals_by_currency: [{ currency: "EUR", subtotal: 1200.5 }],
            blocked: false,
            blocker_codes: [],
          },
          {
            product_key: "acm_panel",
            label: "Panou ACM",
            line_codes: [],
            subtotals_by_currency: [],
            blocked: true,
            blocker_codes: ["ACM_PANEL_MOUNTING_RATE_MISSING"],
          },
        ],
        complete_offer_total: null,
        complete_offer_total_currency: null,
        complete_offer_total_unavailable_reason: "COMMERCIAL_PRODUCT_BLOCKED",
      }),
    );

    expect(vm!.total).toEqual({
      kind: "unavailable",
      reasonCode: "COMMERCIAL_PRODUCT_BLOCKED",
      message: OFFER_PRODUCT_BLOCKED_MESSAGE,
    });
    expect(vm!.products[1].blockerCodes).toEqual(["ACM_PANEL_MOUNTING_RATE_MISSING"]);
  });

  it("never shows an available total when a product is blocked, even if the backend sent an amount", () => {
    const vm = buildOfferProductSummary(
      buildBreakdown({
        products: [
          {
            product_key: "acm_panel",
            label: "Panou ACM",
            line_codes: [],
            subtotals_by_currency: [],
            blocked: true,
            blocker_codes: ["ACM_PANEL_BLOCKED"],
          },
        ],
      }),
    );

    expect(vm!.total.kind).toBe("unavailable");
    expect(vm!.total).toMatchObject({ reasonCode: "COMMERCIAL_PRODUCT_BLOCKED" });
  });

  it("treats a missing total currency as unavailable instead of assuming one", () => {
    const vm = buildOfferProductSummary(
      buildBreakdown({ complete_offer_total: 1287.27, complete_offer_total_currency: null }),
    );

    expect(vm!.total.kind).toBe("unavailable");
  });

  it("presents the tax-exclusive note without a rate when the fiscal policy has none", () => {
    const vm = buildOfferProductSummary(buildBreakdown());

    expect(vm!.vatRatePercent).toBeNull();
    expect(vm!.taxNote).toBe("Prețuri fără TVA");
    expect(vm!.taxNote).not.toMatch(/\d/);
  });

  it("presents the fiscal-policy VAT rate when the backend resolved one", () => {
    const vm = buildOfferProductSummary(
      buildBreakdown({ vat_rate_percent: 21, vat_policy_source: "company_commercial_settings" }),
    );

    expect(vm!.vatRatePercent).toBe(21);
    expect(vm!.taxNote).toBe("Prețuri fără TVA (TVA 21% conform politicii fiscale)");
  });
});

describe("offerTaxNote", () => {
  it("does not invent a default VAT rate", () => {
    expect(offerTaxNote(null)).toBe("Prețuri fără TVA");
  });

  it("formats a provided rate in ro-RO", () => {
    expect(offerTaxNote(19.5)).toBe("Prețuri fără TVA (TVA 19,5% conform politicii fiscale)");
  });
});

describe("formatOfferMoney", () => {
  it("formats ro-RO with two decimals and the explicit currency suffix", () => {
    expect(formatOfferMoney(1287.27, "EUR")).toBe("1.287,27 EUR");
    expect(formatOfferMoney(430, "RON")).toBe("430,00 RON");
  });

  it("normalizes the currency code casing", () => {
    expect(formatOfferMoney(10, "eur")).toBe("10,00 EUR");
  });
});

describe("offerSubtotalLabel", () => {
  it("uses the product-owned short labels", () => {
    expect(offerSubtotalLabel("letters", "Litere volumetrice")).toBe("Subtotal Litere");
    expect(offerSubtotalLabel("acm_panel", "Panou ACM")).toBe("Subtotal Panou ACM");
  });

  it("falls back to the backend label for unknown products", () => {
    expect(offerSubtotalLabel("future_product", "Produs nou")).toBe("Subtotal Produs nou");
  });

  it("never labels a product subtotal as Total ofertă", () => {
    expect(offerSubtotalLabel("letters", "Litere volumetrice")).not.toMatch(/Total ofertă/);
  });
});
