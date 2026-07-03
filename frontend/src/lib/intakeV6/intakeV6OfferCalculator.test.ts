import { describe, expect, it } from "vitest";
import {
  buildIntakeV6OfferModel,
  convertIntakeV6InternalCostToRon,
  resolveIntakeV6OfferCommercialDefaults,
  type IntakeV6OfferCommercialInputs,
} from "./intakeV6OfferCalculator";
import type { IntakeV6MaterialBreakdownResponse, IntakeV6PricingInputPreviewResponse } from "./intakeV6Api";

const commercialInputs: IntakeV6OfferCommercialInputs = {
  markupPercent: 35,
  discountPercent: 0,
  vatPercent: 19,
  manualAdjustmentRon: 0,
};

function buildPreview(): IntakeV6PricingInputPreviewResponse {
  return {
    workspace_id: "ws-1",
    adapter_status: "ready",
    is_ready_for_quote: true,
    readiness_status: "ready",
    requires_grouped_finish_review: false,
    production_counts: { letter_count: 4 },
    quote_input_payload: {},
    adapter_blockers: [],
    adapter_warnings: [],
  };
}

function buildBreakdown(totalEur: number): IntakeV6MaterialBreakdownResponse {
  return {
    material_rows: [
      {
        material_key: "plexi_letters",
        display_name: "Plexi litere",
        material_name: "Plexi",
        material_code: "plexi",
        quantity_basis: "area",
        category: "material",
        quantity: 1,
        unit: "m2",
        material_cost: totalEur,
        estimated_cost: totalEur,
        currency: "EUR",
        warnings: [],
      },
    ],
    consumable_rows: [],
    operation_rows: [],
    edge_cant_operation_rows: [],
    totals: {
      material_cost_total: totalEur,
      estimated_cost_total: totalEur,
      contains_missing_prices: false,
      currency: "EUR",
    },
  } as IntakeV6MaterialBreakdownResponse;
}

describe("intakeV6OfferCalculator currency", () => {
  it("converts EUR internal costs to RON before commercial markup", () => {
    expect(convertIntakeV6InternalCostToRon(100, "EUR", 5)).toBe(500);
    expect(convertIntakeV6InternalCostToRon(100, "RON", 5)).toBe(100);
  });

  it("builds offer totals in RON using company EUR/RON rate", () => {
    const model = buildIntakeV6OfferModel({
      preview: buildPreview(),
      breakdown: buildBreakdown(100),
      commercialInputs,
      eurToRonRate: 5,
    });

    expect(model).not.toBeNull();
    expect(model!.productionBaseInternal).toBe(100);
    expect(model!.productionBaseInternalCurrency).toBe("EUR");
    expect(model!.productionBase).toBe(500);
    expect(model!.offerCurrency).toBe("RON");
    expect(model!.subtotalNet).toBe(675);
    expect(model!.totalGross).toBe(803.25);
  });

  it("normalizes missing persisted commercial inputs to safe defaults", () => {
    expect(resolveIntakeV6OfferCommercialDefaults(buildPreview(), null)).toEqual({
      markupPercent: 35,
      discountPercent: 0,
      vatPercent: 19,
      manualAdjustmentRon: 0,
    });
  });

  it("prefers persisted commercial inputs when they exist", () => {
    expect(
      resolveIntakeV6OfferCommercialDefaults(buildPreview(), {
        markup_percent: 12,
        discount_percent: 3,
        vat_percent: 21,
        manual_adjustment_ron: 150,
      }),
    ).toEqual({
      markupPercent: 12,
      discountPercent: 3,
      vatPercent: 21,
      manualAdjustmentRon: 150,
    });
  });
});
