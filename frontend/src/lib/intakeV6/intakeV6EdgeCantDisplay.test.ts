import { describe, expect, it } from "vitest";

import type { IntakeV6MaterialBreakdownResponse } from "./intakeV6Api";
import {
  buildIntakeV6EdgeCantLayerBreakdown,
  buildIntakeV6EdgeCantViewModel,
  formatEdgeCantCostFormula,
  formatEdgeCantLayerPerimeter,
  isIntakeV6ReturnFinishActive,
  normalizeIntakeV6EdgeCantGroupsToTotal,
} from "./intakeV6EdgeCantDisplay";

function breakdownFixture(withUnitPrice = false): IntakeV6MaterialBreakdownResponse {
  return {
    workspace_id: "ws",
    template_code: "TPL-VOLUMETRIC-LETTERS",
    breakdown_scope: "quote_estimate",
    nesting_rows: [],
    material_rows: [
      {
        material_key: "return_material",
        display_name: "Aluminiu cant / volum",
        category: "material",
        quantity: 15.4672,
        base_quantity: 15.4672,
        priced_quantity: 18.5606,
        unit: "m",
        waste_percent: 20,
        quantity_source: "shared_edge_cant_rules",
        quantity_quality: "calculated",
        quantity_with_waste: 18.5606,
        price_source: withUnitPrice ? "registry" : "missing",
        unit_price: withUnitPrice ? 12.5 : undefined,
        estimated_cost: withUnitPrice ? 193.34 : undefined,
        currency: "EUR",
        warnings: [],
      },
    ],
    consumable_rows: [],
    edge_cant_operation_rows: [],
    totals: {
      material_cost_total: withUnitPrice ? 193.34 : 0,
      estimated_cost_total: withUnitPrice ? 193.34 : 0,
      currency: "EUR",
      contains_estimates: false,
      contains_missing_prices: !withUnitPrice,
    },
    warnings: [],
  };
}

describe("buildIntakeV6EdgeCantViewModel", () => {
  it("shows unit price EUR/ml when registry rate exists", () => {
    const model = buildIntakeV6EdgeCantViewModel({
      finish: { return_finish_type: "white_aluminum", return_depth_mm: 60 },
      breakdown: breakdownFixture(true),
    });

    expect(model.cantPriceLabel).toBe("12.50 EUR/ml");
    expect(model.cantPricingMissing).toBe(false);
    expect(model.cantUnitPrice).toBe(12.5);
  });

  it("shows tarif lipsă when return_material unit_price is missing", () => {
    const model = buildIntakeV6EdgeCantViewModel({
      finish: { return_finish_type: "white_aluminum" },
      breakdown: breakdownFixture(false),
    });

    expect(model.cantPriceLabel).toBe("tarif lipsă");
    expect(model.cantPricingMissing).toBe(true);
  });

  it("sums letter and artwork return rows before stale geometry", () => {
    const fixture = breakdownFixture(true);
    const model = buildIntakeV6EdgeCantViewModel({
      finish: { return_finish_type: "white_aluminum", return_depth_mm: 60 },
      breakdown: {
        ...fixture,
        material_rows: [
          {
            ...fixture.material_rows[0],
            quantity: 26.7472,
            base_quantity: 26.7472,
            quantity_with_waste: 32.0966,
            priced_quantity: 32.0966,
            unit_price: 3,
            estimated_cost: 96.2898,
          },
          {
            ...fixture.material_rows[0],
            material_key: "artwork_return_logo-stanga",
            display_name: "Cant / volum logo stanga",
            quantity: 2.4455,
            base_quantity: 2.4455,
            quantity_with_waste: 2.9346,
            priced_quantity: 2.9346,
            unit_price: 3,
            estimated_cost: 8.8038,
          },
          {
            ...fixture.material_rows[0],
            material_key: "artwork_return_logo-dreapta",
            display_name: "Cant / volum logo dreapta",
            quantity: 2.4455,
            base_quantity: 2.4455,
            quantity_with_waste: 2.9346,
            priced_quantity: 2.9346,
            unit_price: 3,
            estimated_cost: 8.8038,
          },
        ],
      },
      geometryReturnPerimeterM: 29.5398,
    });

    expect(model.calculatedCantM).toBeCloseTo(31.6382, 4);
    expect(model.pricedCantM).toBeCloseTo(37.9658, 4);
    expect(model.cantEstimatedCost).toBeCloseTo(113.8974, 4);
  });
});

describe("formatEdgeCantCostFormula", () => {
  it("builds perimeter × rate = cost when price exists", () => {
    expect(
      formatEdgeCantCostFormula({
        perimeterM: 26.747,
        unitPrice: 12.5,
        currency: "EUR",
        pricingMissing: false,
      }),
    ).toBe("26.75 m × 12.50 EUR/ml = 334.34 EUR");
  });

  it("returns unavailable label when tariff missing", () => {
    expect(
      formatEdgeCantCostFormula({
        perimeterM: 26.747,
        unitPrice: null,
        pricingMissing: true,
      }),
    ).toBe("indisponibil — tarif lipsă");
  });
});

describe("buildIntakeV6EdgeCantLayerBreakdown", () => {
  it("sums active letter and emblem layers and marks inactive as fără cant", () => {
    const breakdown = buildIntakeV6EdgeCantLayerBreakdown({
      letterGroups: [
        {
          group_key: "maria",
          layer_name: "pseudo maria",
          face_finish_type: "oracal_651",
          return_finish_type: "white_aluminum",
          perimeter_m: 8.12,
          confirmed: true,
        },
        {
          group_key: "plain",
          layer_name: "plain face",
          face_finish_type: "none",
          return_finish_type: "none",
          perimeter_m: 3.5,
          confirmed: true,
        },
      ],
      artworkFinishes: [
        {
          layer_key: "logo-stanga",
          layer_name: "Emblemă stânga",
          execution_type: "print_laminate",
          color_mode: "polychrome",
          return_finish_type: "white_aluminum",
          confirmed: true,
        },
        {
          layer_key: "logo-dreapta",
          layer_name: "Emblemă dreapta",
          execution_type: "print_laminate",
          color_mode: "polychrome",
          return_finish_type: "none",
          confirmed: true,
        },
      ],
      report: {
        layers: [
          {
            id: "logo-stanga",
            name: "logo-stanga",
            perimeterMl: 2.445,
            elementCount: 1,
            colors: [],
            autoRole: "logo",
            layerKind: "vector_artwork",
          },
        ],
      } as never,
    });

    expect(breakdown.totalLettersM).toBeCloseTo(8.12, 2);
    expect(breakdown.totalEmblemM).toBeCloseTo(2.445, 2);
    expect(breakdown.totalCantM).toBeCloseTo(10.565, 2);
    expect(formatEdgeCantLayerPerimeter(breakdown.layers[1])).toBe("fără cant");
    expect(breakdown.layers.some((row) => row.key === "logo-dreapta")).toBe(false);
    expect(isIntakeV6ReturnFinishActive("none")).toBe(false);
    expect(isIntakeV6ReturnFinishActive("white_aluminum")).toBe(true);
  });
});

describe("normalizeIntakeV6EdgeCantGroupsToTotal", () => {
  it("scales grouped display rows to the canonical operator total", () => {
    const result = normalizeIntakeV6EdgeCantGroupsToTotal({
      targetTotalM: 29.91,
      groups: [
        {
          key: "artwork|60|Alb",
          label: "Alb",
          scope: "artwork",
          perimeterM: 4.89,
          finishLabel: "Alb",
          depthMm: 60,
          layerCount: 1,
        },
        {
          key: "letters|60|Alb",
          label: "Alb",
          scope: "letters",
          perimeterM: 26.75,
          finishLabel: "Alb",
          depthMm: 60,
          layerCount: 2,
        },
      ],
    });

    expect(result.normalized).toBe(true);
    expect(result.rawTotalM).toBeCloseTo(31.64, 2);
    expect(result.groups.reduce((sum, group) => sum + group.perimeterM, 0)).toBeCloseTo(29.91, 2);
  });
});