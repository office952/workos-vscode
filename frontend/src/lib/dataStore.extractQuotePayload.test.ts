import { describe, it, expect } from "vitest";
import { extractQuotePayload } from "./dataStore";

function makeSyntheticLayers(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    layer_id: `layer_${i + 1}`,
    layer_type: "structure",
  }));
}

function makeCanonicalSnapshot(layerCount: number) {
  return {
    product_definition: {
      template_code: "TPL-VOLUMETRIC-LETTERS",
      layers: makeSyntheticLayers(layerCount),
    },
    cost_result: {
      materials_cost: 220.74,
      labour_cost: 444.78,
      total_cost: 665.52,
      currency: "RON",
    },
    pricing: { margin_pct: 20, discount_pct: 0, vat_pct: 19 },
    price: { net: 1000, gross: 1190, final: 1190 },
    status: "priced",
  };
}

const REAL_COMPONENT_BREAKDOWN = [
  {
    component_id: "comp_face_litere",
    type: "LITERE_3D",
    name: "Față litere — plexi/acrilic (CNC/laser)",
    material_cost: 120.5,
    operation_cost: 210.25,
    total_component_cost: 330.75,
    materials_detail: [{ material_code: "MAT-ACP-FATA-LITERE", quantity: 1.2, unit: "mp", unit_cost: 50, line_total: 60 }],
    operations_detail: [{ code: "face_cnc_cut", workcenter: "CNC_ROUTER", line_total: 40 }],
  },
  {
    component_id: "comp_lateral_litere",
    type: "LITERE_3D",
    name: "Laterale litere — profil aluminiu (bordură)",
    material_cost: 45,
    operation_cost: 88,
    total_component_cost: 133,
    materials_detail: [],
    operations_detail: [{ code: "side_forming", workcenter: "RETURN_PROFILE_MACHINE_FORMING", line_total: 88 }],
  },
  {
    component_id: "comp_spate_litere",
    type: "STRUCTURA",
    name: "Spate litere — Forex 10 mm",
    material_cost: 30,
    operation_cost: 55,
    total_component_cost: 85,
  },
];

describe("extractQuotePayload — component_breakdown precedence", () => {
  it("Shape B prefers persisted component_breakdown over synthetic layer split", () => {
    const payload = JSON.stringify({
      line_items: makeCanonicalSnapshot(13),
      component_breakdown: REAL_COMPONENT_BREAKDOWN,
    });

    const { componentBreakdown } = extractQuotePayload(payload);

    expect(componentBreakdown).toBeDefined();
    expect(componentBreakdown).toHaveLength(3);
    expect(componentBreakdown!.map((c) => c.component_id)).toEqual([
      "comp_face_litere",
      "comp_lateral_litere",
      "comp_spate_litere",
    ]);
    expect(componentBreakdown!.some((c) => c.component_id?.startsWith("layer_"))).toBe(false);
    expect(componentBreakdown![0].material_cost).toBe(120.5);
    expect(componentBreakdown![0].materials_detail).toHaveLength(1);
    expect(componentBreakdown![0].operations_detail).toHaveLength(1);
  });

  it("Shape B without component_breakdown falls back to legacy synthetic layer split", () => {
    const payload = JSON.stringify({
      line_items: makeCanonicalSnapshot(13),
    });

    const { componentBreakdown } = extractQuotePayload(payload);

    expect(componentBreakdown).toHaveLength(13);
    expect(componentBreakdown![0].component_id).toBe("layer_1");
    expect(componentBreakdown![0].type).toBe("structure");
    expect(componentBreakdown![0].material_cost).toBeCloseTo(220.74 / 13, 5);
    expect(componentBreakdown![0].operation_cost).toBeCloseTo(444.78 / 13, 5);
    expect(componentBreakdown![0].materials_detail).toEqual([]);
  });

  it("Shape B with empty component_breakdown array uses legacy synthetic fallback", () => {
    const payload = JSON.stringify({
      line_items: makeCanonicalSnapshot(4),
      component_breakdown: [],
    });

    const { componentBreakdown } = extractQuotePayload(payload);

    expect(componentBreakdown).toHaveLength(4);
    expect(componentBreakdown![0].component_id).toBe("layer_1");
  });

  it("Shape C top-level canonical still uses legacy synthetic fallback when no wrapper breakdown", () => {
    const payload = JSON.stringify(makeCanonicalSnapshot(5));

    const { componentBreakdown } = extractQuotePayload(payload);

    expect(componentBreakdown).toHaveLength(5);
    expect(componentBreakdown![0].component_id).toBe("layer_1");
  });

  it("normalizes alternate persisted field names without inventing costs", () => {
    const payload = JSON.stringify({
      line_items: makeCanonicalSnapshot(13),
      component_breakdown: [
        {
          component_name: "Panel",
          component_type: "panel",
          material_cost: 30,
          operation_cost: 12.5,
          total_component_cost: 42.5,
          materials: [{ name: "Bond", qty: 1, unit_price: 30, total: 30 }],
          operations: [{ name: "CNC", minutes: 15, total: 12.5 }],
        },
      ],
    });

    const { componentBreakdown } = extractQuotePayload(payload);

    expect(componentBreakdown).toHaveLength(1);
    expect(componentBreakdown![0].name).toBe("Panel");
    expect(componentBreakdown![0].type).toBe("panel");
    expect(componentBreakdown![0].material_cost).toBe(30);
    expect(componentBreakdown![0].materials_detail).toHaveLength(1);
    expect(componentBreakdown![0].operations_detail).toHaveLength(1);
  });
});
