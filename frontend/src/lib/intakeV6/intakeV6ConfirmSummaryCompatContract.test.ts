import { describe, expect, it } from "vitest";
import { buildIntakeV6ConfirmSummary } from "./intakeV6ConfirmSummary";

const pblPayload = {
  finish_setup: {
    face_finish_type: "none",
    return_finish_type: "standard_aluminum",
    return_depth_mm: 60,
    illuminated: true,
    lighting_system_type: "led_modules",
    led_module_power_w: 1.44,
    confirmed: true,
    artwork_finishes: [
      {
        layer_key: "Layer_x0020_1",
        layer_name: "Layer_x0020_1",
        execution_type: "needs_decision",
        return_finish_type: "standard_aluminum",
        return_depth_mm: 60,
      },
    ],
  },
  quote_geometry: {
    letter_perimeter_m: 11.6139,
    led_perimeter_ml: 11.6139,
    face_area_m2: 0.6907,
    letter_count: 10,
    real_letters_count: 10,
    inner_holes_count: 5,
    return_material_perimeter_ml: 15.47,
    face_cutting_perimeter_ml: 13.62,
    cutting_perimeter_ml: 13.62,
    artwork_piece_count: 1,
  },
} as Record<string, unknown>;

const materialBreakdown = {
  workspace_id: "ws",
  template_code: "TPL-VOLUMETRIC-LETTERS",
  breakdown_scope: "quote_estimate",
  stock_consumption: false,
  nesting_rows: [],
  material_rows: [
    {
      material_key: "plexiglas_face",
      display_name: "Plexiglas față",
      category: "material",
      quantity: 0.5834,
      unit: "m2",
      quantity_source: "nesting",
      quantity_quality: "estimate",
      quantity_with_waste: 0.5834,
      currency: "RON",
      price_source: "registry",
      warnings: [],
      priced_quantity: 0.5834,
    },
  ],
  consumable_rows: [],
  totals: {},
  warnings: [],
};

const nestingPreview = {
  preview_mode: "bounding_box_mvp",
  preview_only: true,
  mutates_inventory: false,
  uses_stock: false,
  source: "intake_v6",
  disclaimer: "",
  active_sheet_config_id: "sheet-1",
  breakdown_uses_single_active_layout: true,
  boundary: {
    preview_only: true,
    mutates_inventory: false,
    uses_stock: false,
    creates_execution_plan: false,
    creates_execution_tasks: false,
    consumes_stock: false,
    used_for_stock_reservation: false,
  },
  summary: {
    sheet_layouts: 1,
    roll_layouts: 0,
    active_sheet_layouts: 1,
    active_roll_layouts: 0,
    alternative_layouts: 0,
    nestable_parts: 10,
    holes_excluded: 5,
    artwork_parts: 1,
  },
  sheets: [],
  rolls: [],
  parts: [],
  material_traces: [],
  warnings: [],
};

describe("buildIntakeV6ConfirmSummary compat contract", () => {
  it("maps PBL structure counters", () => {
    const summary = buildIntakeV6ConfirmSummary({
      payload: pblPayload,
      layerCount: 3,
      materialBreakdown,
      nestingPreview,
      handoffBlockers: ["artwork_execution_undecided:Layer_x0020_1"],
    });

    expect(summary.structure.layerCount).toBe(3);
    expect(summary.structure.childPartsCount).toBe(11);
    expect(summary.structure.realLettersCount).toBe(10);
    expect(summary.structure.artworkCount).toBe(1);
    expect(summary.structure.innerHolesCount).toBe(5);
  });

  it("shows gross vs quoteable plexiglas area", () => {
    const summary = buildIntakeV6ConfirmSummary({
      payload: pblPayload,
      layerCount: 3,
      materialBreakdown,
      nestingPreview,
    });

    expect(summary.geometry.grossFaceAreaM2).toBeCloseTo(0.6907, 4);
    expect(summary.geometry.quoteablePlexiglasM2).toBeCloseTo(0.5834, 4);
  });

  it("keeps canonical quote geometry return perimeter over letter-only material rows", () => {
    const effectiveBreakdown = {
      ...materialBreakdown,
      material_rows: [
        ...materialBreakdown.material_rows,
        {
          material_key: "return_material",
          display_name: "Cant / volum litere",
          category: "material",
          quantity: 11,
          base_quantity: 11,
          unit: "ml",
          quantity_source: "quote_geometry.letter_return_perimeter",
          quantity_quality: "calculated",
          quantity_with_waste: 13.2,
          currency: "EUR",
          price_source: "registry",
          warnings: [],
          priced_quantity: 13.2,
        },
      ],
      operation_rows: [
        {
          key: "cnc_face_cutting_plexiglas_3mm",
          display_name: "Debitare CNC fata",
          operation_type: "cnc_cutting",
          quantity: 31.6373,
          unit: "ml",
        },
      ],
    };

    const summary = buildIntakeV6ConfirmSummary({
      payload: pblPayload,
      layerCount: 3,
      materialBreakdown: effectiveBreakdown,
      nestingPreview,
    });

    expect(summary.geometry.cncPerimeterM).toBeCloseTo(31.6373, 4);
    expect(summary.geometry.returnPerimeterM).toBeCloseTo(15.47, 4);
  });

  it("uses backend return rows for letters plus artwork when quote geometry is stale", () => {
    const effectiveBreakdown = {
      ...materialBreakdown,
      material_rows: [
        ...materialBreakdown.material_rows,
        {
          material_key: "return_material",
          display_name: "Cant / volum litere",
          category: "material",
          quantity: 26.7472,
          base_quantity: 26.7472,
          unit: "m",
          quantity_source: "quote_geometry.letter_return_perimeter",
          quantity_quality: "calculated",
          quantity_with_waste: 32.0966,
          priced_quantity: 32.0966,
          currency: "EUR",
          price_source: "registry",
          unit_price: 3,
          estimated_cost: 96.2898,
          warnings: [],
        },
        {
          material_key: "artwork_return_logo-stanga",
          display_name: "Cant / volum logo stanga",
          category: "material",
          quantity: 2.4455,
          base_quantity: 2.4455,
          unit: "m",
          quantity_source: "artwork_finishes",
          quantity_quality: "calculated",
          quantity_with_waste: 2.9346,
          priced_quantity: 2.9346,
          currency: "EUR",
          price_source: "registry",
          unit_price: 3,
          estimated_cost: 8.8038,
          warnings: [],
        },
        {
          material_key: "artwork_return_logo-dreapta",
          display_name: "Cant / volum logo dreapta",
          category: "material",
          quantity: 2.4455,
          base_quantity: 2.4455,
          unit: "m",
          quantity_source: "artwork_finishes",
          quantity_quality: "calculated",
          quantity_with_waste: 2.9346,
          priced_quantity: 2.9346,
          currency: "EUR",
          price_source: "registry",
          unit_price: 3,
          estimated_cost: 8.8038,
          warnings: [],
        },
      ],
    };

    const summary = buildIntakeV6ConfirmSummary({
      payload: {
        ...pblPayload,
        quote_geometry: {
          ...(pblPayload.quote_geometry as Record<string, unknown>),
          return_material_perimeter_ml: 29.5398,
        },
      },
      layerCount: 3,
      materialBreakdown: effectiveBreakdown,
      nestingPreview,
    });

    expect(summary.geometry.returnPerimeterM).toBeCloseTo(31.6382, 4);
    expect(summary.edgeCant.realPerimeterM).toBeCloseTo(31.6382, 4);
    expect(summary.edgeCant.calculatedCantM).toBeCloseTo(31.6382, 4);
    expect(summary.edgeCant.pricedCantM).toBeCloseTo(37.9658, 4);
  });

  it("computes LED load from module wattage selector", () => {
    const summary = buildIntakeV6ConfirmSummary({
      payload: pblPayload,
      layerCount: 3,
      materialBreakdown,
      nestingPreview,
    });

    expect(summary.lighting.moduleCount).toBe(47);
    expect(summary.lighting.moduleWattageW).toBe(1.44);
    expect(summary.lighting.totalLedWatts).toBeCloseTo(67.68, 2);
    expect(summary.lighting.requiredPsuWatts).toBeCloseTo(87.98, 1);
    expect(summary.lighting.psuConfiguration).toEqual([100]);
  });

  it("marks print and lamination present after artwork execution is decided", () => {
    const summary = buildIntakeV6ConfirmSummary({
      payload: {
        ...pblPayload,
        finish_setup: {
          ...(pblPayload.finish_setup as Record<string, unknown>),
          artwork_finishes: [
            {
              layer_key: "Layer_x0020_1",
              layer_name: "Layer_x0020_1",
              execution_type: "print_laminate",
              print_transparency: "translucent",
              return_finish_type: "standard_aluminum",
              return_depth_mm: 60,
            },
          ],
        },
      },
      layerCount: 3,
      materialBreakdown: {
        ...materialBreakdown,
        material_rows: [
          ...materialBreakdown.material_rows,
          {
            material_key: "print_laminate_artwork",
            display_name: "Printat / Laminat",
            category: "material",
            quantity: 0.4,
            unit: "m2",
            quantity_source: "finish_setup.artwork_finishes",
            quantity_quality: "calculated",
            quantity_with_waste: 0.4,
            currency: "EUR",
            price_source: "registry",
            warnings: [],
            priced_quantity: 0.4,
          },
        ],
      },
      nestingPreview,
    });

    expect(summary.finish.printLaminate).toBe("present");
  });

  it("keeps print and lamination pending only for undecided artwork", () => {
    const summary = buildIntakeV6ConfirmSummary({
      payload: pblPayload,
      layerCount: 3,
      materialBreakdown: {
        ...materialBreakdown,
        material_rows: [
          ...materialBreakdown.material_rows,
          {
            material_key: "print_laminate_artwork",
            display_name: "Printat / Laminat",
            category: "material",
            quantity: 0.4,
            unit: "m2",
            quantity_source: "finish_setup.artwork_finishes",
            quantity_quality: "calculated",
            quantity_with_waste: 0.4,
            currency: "EUR",
            price_source: "registry",
            warnings: [],
            priced_quantity: 0.4,
          },
        ],
      },
      nestingPreview,
    });

    expect(summary.finish.printLaminate).toBe("present (pending artwork decision)");
  });

  it("surfaces artwork undecided warning", () => {
    const summary = buildIntakeV6ConfirmSummary({
      payload: pblPayload,
      layerCount: 3,
      materialBreakdown,
      nestingPreview,
      handoffBlockers: ["artwork_execution_undecided:Layer_x0020_1"],
    });

    expect(summary.warnings.some((warning) => warning.code.includes("artwork_execution_undecided"))).toBe(true);
    expect(summary.warnings[0]?.message).toMatch(/Layer_x0020_1/);
  });

  it("F7E A-F4: acm is null when the workspace has no ACM/support component", () => {
    const summary = buildIntakeV6ConfirmSummary({
      payload: pblPayload,
      layerCount: 3,
      materialBreakdown,
      nestingPreview,
    });

    expect(summary.acm).toBeNull();
  });

  it("F7E A-F4: recap never silently omits a priced ACM/support panel", () => {
    const summary = buildIntakeV6ConfirmSummary({
      payload: {
        ...pblPayload,
        finish_setup: {
          ...(pblPayload.finish_setup as Record<string, unknown>),
          mounting_solution: { template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" },
          applied_content: "letters",
        },
        product_composition_recommendation: {
          composition_items: [{ component_role: "support_panel", template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" }],
        },
      },
      layerCount: 3,
      materialBreakdown,
      nestingPreview,
    });

    expect(summary.acm).not.toBeNull();
    expect(summary.acm?.inclusionState).toBe("active_priced");
    expect(summary.acm?.tone).toBe("ok");
    expect(summary.acm?.inclusionStateLabel).toMatch(/inclus activ în ofertă/i);
  });

  it("F7E A-F4: recap shows the un-priced state honestly instead of hiding the ACM component", () => {
    const summary = buildIntakeV6ConfirmSummary({
      payload: {
        ...pblPayload,
        product_composition_recommendation: {
          composition_items: [{ component_role: "support_panel", template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" }],
        },
      },
      layerCount: 3,
      materialBreakdown,
      nestingPreview,
    });

    expect(summary.acm).not.toBeNull();
    expect(summary.acm?.inclusionState).toBe("selected_incomplete");
    expect(summary.acm?.tone).toBe("pending");
  });

  it("surfaces unclassified vector decision warning", () => {
    const summary = buildIntakeV6ConfirmSummary({
      payload: pblPayload,
      layerCount: 3,
      materialBreakdown: {
        ...materialBreakdown,
        warnings: [
          {
            code: "unclassified_vector_artwork_requires_decision",
            severity: "warning",
            message: "Vector neclasificat detectat in SVG (~4.89 m).",
            source: "path_geometry_summary.perimeter_mm_approx|finish_setup.artwork_finishes",
          },
        ],
      },
      nestingPreview,
    });

    expect(summary.warnings).toEqual([
      {
        code: "unclassified_vector_artwork_requires_decision",
        message: "Vector neclasificat detectat in SVG (~4.89 m).",
      },
    ]);
  });
});