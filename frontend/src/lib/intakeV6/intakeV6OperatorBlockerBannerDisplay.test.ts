import { describe, expect, it } from "vitest";

import {
  asBlockerCodeList,
  buildOperatorBlockerBannerDisplay,
  collectMissingPriceLineKeysFromBreakdown,
  collectRuntimeBlockerCodes,
  OPERATOR_BLOCKER_BANNER_MAX_MESSAGES,
} from "./intakeV6OperatorBlockerBannerDisplay";
import type { ReviewHandoffSurfacing } from "./intakeV6QuoteHandoffReadiness";
import type {
  IntakeV6ProductTruthPromotionPlannerResponse,
  IntakeV6RuntimeCaptureReadModelResponse,
} from "./intakeV6Api";

const clearSurfacing: ReviewHandoffSurfacing = {
  showBanner: false,
  reasons: [],
  actions: [],
};

const handoffSurfacing: ReviewHandoffSurfacing = {
  showBanner: true,
  reasons: ["Confirmarea operatorului pentru draft intern lipsește încă."],
  actions: ["Confirmarea finală se face în pasul Confirmare."],
};

const runtimeWithSelectedLayerRefs: IntakeV6RuntimeCaptureReadModelResponse = {
  read_only: true,
  workspace_id: "ws-1",
  workspace_record_id: "ws-1",
  workspace_code: "IV6-TEST",
  root_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  product_binding_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  read_model_version: "v1",
  fields: [
    {
      field_key: "svg.selected_layer_refs[]",
      runtime_source: "svg.selected_layer_refs[]",
      product_truth_path: "svg.selected_layer_refs[]",
      state: "blocked",
      confirmation_rule: "rule",
      blockers: ["SELECTED_LAYER_REFS_MISSING"],
      ready_for_product_truth: false,
    },
  ],
  blockers: [
    {
      field_key: "svg.selected_layer_refs[]",
      blockers: ["SELECTED_LAYER_REFS_MISSING"],
      state: "blocked",
    },
  ],
  downstream_write_intent: {},
  notes: [],
};

const plannerWithBlockers: IntakeV6ProductTruthPromotionPlannerResponse = {
  read_only: true,
  workspace_id: "ws-1",
  workspace_record_id: "ws-1",
  workspace_code: "IV6-TEST",
  root_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  product_binding_template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  planner_version: "v1",
  eligible_entries: [],
  blocked_entries: [],
  blockers: [
    {
      field_key: "support.support_type",
      blockers: ["SUPPORT_TYPE_MISSING"],
      state: "blocked",
    },
  ],
  downstream_write_intent: {},
  notes: [],
};

describe("buildOperatorBlockerBannerDisplay", () => {
  it("returns no banner when no blockers exist", () => {
    const display = buildOperatorBlockerBannerDisplay({
      surfacing: clearSurfacing,
      runtimeModel: null,
      plannerModel: null,
    });
    expect(display.show).toBe(false);
    expect(display.messages).toEqual([]);
  });

  it("maps selected layer refs blocker to operator copy", () => {
    const display = buildOperatorBlockerBannerDisplay({
      surfacing: clearSurfacing,
      runtimeModel: runtimeWithSelectedLayerRefs,
      plannerModel: null,
    });
    expect(display.show).toBe(true);
    expect(display.messages[0]).toMatch(/Referințele straturilor selectate lipsesc/i);
    expect(display.messages.join(" ")).not.toMatch(/SELECTED_LAYER_REFS_MISSING/);
  });

  it("includes quote handoff surfacing reasons", () => {
    const display = buildOperatorBlockerBannerDisplay({
      surfacing: handoffSurfacing,
      runtimeModel: null,
      plannerModel: null,
    });
    expect(display.show).toBe(true);
    expect(display.messages[0]).toMatch(/Confirmarea operatorului/i);
  });

  it("limits messages to max count", () => {
    const display = buildOperatorBlockerBannerDisplay({
      surfacing: {
        showBanner: true,
        reasons: ["A", "B", "C", "D"],
        actions: [],
      },
      runtimeModel: runtimeWithSelectedLayerRefs,
      plannerModel: plannerWithBlockers,
    });
    expect(display.messages.length).toBeGreaterThan(0);
    expect(display.messages.length).toBeLessThanOrEqual(OPERATOR_BLOCKER_BANNER_MAX_MESSAGES);
    expect(display.summaryTitle).toMatch(/probleme blochează Confirmarea|problemă blochează Confirmarea/i);
  });

  it("maps MOUNTING_SOLUTION_MISSING to specific operator copy", () => {
    const display = buildOperatorBlockerBannerDisplay({
      surfacing: clearSurfacing,
      runtimeModel: {
        ...runtimeWithSelectedLayerRefs,
        fields: [
          {
            ...runtimeWithSelectedLayerRefs.fields[0],
            blockers: ["MOUNTING_SOLUTION_MISSING"],
          },
        ],
        blockers: [
          {
            field_key: "mounting.mounting_solution",
            blockers: ["MOUNTING_SOLUTION_MISSING"],
            state: "blocked",
          },
        ],
      },
      plannerModel: null,
    });
    expect(display.show).toBe(true);
    expect(display.severity).toBe("blocked");
    expect(display.messages.join(" ")).toMatch(/Soluția de montaj lipsește/i);
    expect(display.messages.join(" ")).not.toMatch(/Există blocaje tehnice/i);
  });

  it("shows exact code for unknown runtime blockers instead of generic panel", () => {
    const display = buildOperatorBlockerBannerDisplay({
      surfacing: clearSurfacing,
      runtimeModel: {
        ...runtimeWithSelectedLayerRefs,
        fields: [
          {
            ...runtimeWithSelectedLayerRefs.fields[0],
            blockers: ["UNKNOWN_BLOCKER_CODE_XYZ"],
          },
        ],
        blockers: [
          {
            field_key: "x",
            blockers: ["UNKNOWN_BLOCKER_CODE_XYZ"],
            state: "blocked",
          },
        ],
      },
      plannerModel: null,
    });
    expect(display.messages.join(" ")).toMatch(/UNKNOWN_BLOCKER_CODE_XYZ/);
    expect(display.messages.join(" ")).not.toMatch(/Există blocaje tehnice/i);
  });

  it("treats missing-tariff flag without rows as diagnostic warning", () => {
    const display = buildOperatorBlockerBannerDisplay({
      surfacing: {
        showBanner: true,
        reasons: ["Calculul live conține linii fără tarif configurat."],
        actions: ["Verifică liniile cu tarif lipsă în Calcul live."],
      },
      runtimeModel: null,
      plannerModel: null,
      missingPriceFlagWithoutRows: true,
      missingPriceLineKeys: [],
    });
    expect(display.warningCount).toBeGreaterThanOrEqual(1);
    expect(display.blockerCount).toBe(0);
    expect(display.severity).toBe("attention");
    expect(display.messages.join(" ")).toMatch(/diagnostic/i);
  });

  it("lists concrete missing-price line keys when provided", () => {
    const display = buildOperatorBlockerBannerDisplay({
      surfacing: {
        showBanner: true,
        reasons: ["Calculul live conține linii fără tarif configurat."],
        actions: ["Verifică liniile cu tarif lipsă în Calcul live."],
      },
      runtimeModel: null,
      plannerModel: null,
      missingPriceFlagWithoutRows: false,
      missingPriceLineKeys: ["forex_backing", "led_psu"],
    });
    expect(display.messages.join(" ")).toMatch(/forex_backing/);
    expect(display.messages.join(" ")).not.toMatch(/diagnostic/i);
    expect(display.severity).toBe("attention");
  });

  it("collectMissingPriceLineKeysFromBreakdown returns only unpriced rows", () => {
    const keys = collectMissingPriceLineKeysFromBreakdown({
      material_rows: [
        { material_key: "plexiglas_face", unit_price: 10, estimated_cost: 20 },
        { material_key: "mystery", unit_price: null, estimated_cost: null },
      ],
      operation_rows: [{ key: "cnc_x", unit_price: null, estimated_cost: null }],
      consumable_rows: [],
    });
    expect(keys).toEqual(["mystery", "cnc_x"]);
  });
});

describe("asBlockerCodeList / collectRuntimeBlockerCodes resilience", () => {
  it("keeps valid string blocker arrays", () => {
    expect(asBlockerCodeList(["SELECTED_LAYER_REFS_MISSING", "  MOUNTING_SOLUTION_MISSING  "])).toEqual([
      "SELECTED_LAYER_REFS_MISSING",
      "MOUNTING_SOLUTION_MISSING",
    ]);
    expect(collectRuntimeBlockerCodes(runtimeWithSelectedLayerRefs)).toEqual(["SELECTED_LAYER_REFS_MISSING"]);
  });

  it("treats missing and null blockers as empty", () => {
    expect(asBlockerCodeList(undefined)).toEqual([]);
    expect(asBlockerCodeList(null)).toEqual([]);
    expect(
      collectRuntimeBlockerCodes({
        ...runtimeWithSelectedLayerRefs,
        fields: [
          {
            ...runtimeWithSelectedLayerRefs.fields[0],
            blockers: undefined as unknown as string[],
          },
        ],
        blockers: [
          {
            field_key: "svg.selected_layer_refs[]",
            blockers: null as unknown as string[],
            state: "blocked",
          },
        ],
      }),
    ).toEqual([]);
  });

  it("ignores invalid non-array blockers without inventing codes", () => {
    expect(asBlockerCodeList("SELECTED_LAYER_REFS_MISSING")).toEqual([]);
    expect(asBlockerCodeList({ code: "X" })).toEqual([]);
    expect(asBlockerCodeList(12)).toEqual([]);
  });

  it("keeps valid rows when mixed with partial/backbone-shaped rows", () => {
    const codes = collectRuntimeBlockerCodes({
      ...runtimeWithSelectedLayerRefs,
      blockers: [
        {
          field_key: "svg.selected_layer_refs[]",
          blockers: ["SELECTED_LAYER_REFS_MISSING"],
          state: "blocked",
        },
        // Fail-closed Logo/backbone shape: blocker_code present, nested blockers absent.
        {
          field_key: "root",
          blocker_code: "LOGO_NOT_OFFERABLE",
          state: "blocked",
        } as unknown as IntakeV6RuntimeCaptureReadModelResponse["blockers"][number],
        {
          field_key: "broken",
          blockers: "not-an-array" as unknown as string[],
          state: "blocked",
        },
      ],
    });
    expect(codes).toEqual(["SELECTED_LAYER_REFS_MISSING"]);
  });

  it("does not white-screen Logo fail-closed runtime models and keeps surfacing usable", () => {
    const logoFailClosedRuntime = {
      ...runtimeWithSelectedLayerRefs,
      root_template_code: "TPL-VOLUMETRIC-LOGO_v1",
      product_binding_template_code: "TPL-VOLUMETRIC-LOGO_v1",
      fields: [],
      blockers: [
        {
          field_key: null,
          owning_component: null,
          blocker_code: "LOGO_NOT_OFFERABLE",
          state: "blocked",
          message: "TPL-VOLUMETRIC-LOGO_v1 remains candidate-only",
        },
      ],
    } as unknown as IntakeV6RuntimeCaptureReadModelResponse;

    expect(() => collectRuntimeBlockerCodes(logoFailClosedRuntime)).not.toThrow();
    expect(collectRuntimeBlockerCodes(logoFailClosedRuntime)).toEqual([]);

    const display = buildOperatorBlockerBannerDisplay({
      surfacing: {
        showBanner: true,
        reasons: ["Logo-only candidate · root comercial neofertabil fara owner GO"],
        actions: ["Nu crea quote/order/execution fără owner GO."],
      },
      runtimeModel: logoFailClosedRuntime,
      plannerModel: null,
    });
    expect(display.show).toBe(true);
    expect(display.messages.join(" ")).toMatch(/Logo-only candidate/i);
    expect(display.messages.join(" ")).toMatch(/neofertabil/i);
  });
});
