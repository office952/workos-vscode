import { describe, expect, it } from "vitest";

import {
  intakeV6HasOfficialCommercialTotals,
  intakeV6OfficialPricingBlockerMessage,
  intakeV6OperatorFacingPricingBlocker,
  V6_OFFICIAL_COMMERCIAL_AUTHORITY,
} from "./intakeV6OfficialPricing";
import type { IntakeV6PricedQuoteDryRunResponse } from "./intakeV6PricedQuoteTypes";

function basePricing(
  overrides: Partial<IntakeV6PricedQuoteDryRunResponse> = {},
): IntakeV6PricedQuoteDryRunResponse {
  return {
    pricing_status: "V6_PRICED_DRY_RUN_READY",
    pricing_authority: V6_OFFICIAL_COMMERCIAL_AUTHORITY,
    commercial_authority_status: "ready",
    workspace_id: "ws-1",
    pricing_source: "intake_v6_backend_priced_dry_run",
    commercial_totals: {
      subtotal_net: 1000,
      vat_rate: 19,
      vat_amount: 190,
      total_gross: 1190,
      currency: "RON",
    },
    ...overrides,
  };
}

describe("intakeV6OfficialPricing", () => {
  it("accepts ready 7G-backed totals", () => {
    expect(intakeV6HasOfficialCommercialTotals(basePricing())).toBe(true);
  });

  it("rejects blocked pricing even when totals are present", () => {
    expect(
      intakeV6HasOfficialCommercialTotals(
        basePricing({
          pricing_status: "V6_PRICED_DRY_RUN_BLOCKED",
          commercial_authority_status: "blocked",
        }),
      ),
    ).toBe(false);
  });

  it("rejects missing authority", () => {
    expect(intakeV6HasOfficialCommercialTotals(basePricing({ pricing_authority: null }))).toBe(false);
  });

  it("rejects when derived readiness says commercial composition incomplete", () => {
    expect(
      intakeV6HasOfficialCommercialTotals(
        basePricing({
          offer_composition_readiness: {
            product_composition_complete: true,
            commercial_composition_complete: false,
            confirmation_complete: false,
            offer_ready_to_freeze: false,
            canonical_gate: "blocked",
          },
        }),
      ),
    ).toBe(false);
  });

  it("surfaces blocker message when official price absent", () => {
    expect(
      intakeV6OfficialPricingBlockerMessage(
        basePricing({
          pricing_status: "V6_PRICED_DRY_RUN_BLOCKED",
          pricing_authority: null,
          commercial_totals: {
            subtotal_net: null,
            vat_rate: 19,
            vat_amount: null,
            total_gross: null,
            currency: "RON",
          },
          blockers: [{ code: "V6_PRICED_DRY_RUN_COMMERCIAL_REVIEW_NOT_READY", message: "7G blocked" }],
        }),
      ),
    ).toBe("7G blocked");
  });

  it("humanizes dry-run English for the offer rail", () => {
    expect(
      intakeV6OperatorFacingPricingBlocker("V6 backend pricing input is not ready for dry-run."),
    ).toMatch(/nu e gata/i);
    expect(intakeV6OperatorFacingPricingBlocker("7G blocked")).toMatch(/blocată/i);
  });
});
