import { describe, expect, it } from "vitest";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import {
  buildClientMaterialFiles,
  buildInitialVolumetricQuoteFlowState,
  buildSimulateQuoteInputPayload,
  isSimulateInputReady,
  isVolumetricWorkIntakeHandoffCommercialMode,
  shouldOpenWizardFromNav,
  shouldRouteToVolumetricQuoteFlow,
  shouldShowVolumetricQuoteWorkspace,
  suggestMountingTemplateAreaM2,
  switchCalculationMethod,
  updateFlowDimension,
  updateFlowQuoteInputField,
  VOLUMETRIC_TEMPLATE_DEFAULTS,
} from "./volumetricQuoteFlowState";
import { isCantRalPaintEnabled, TPL_VOLUMETRIC_LETTERS } from "./volumetricQuoteInput";

const WI_SMOKE_SPEC: IntakeProductSpec = {
  text: "BT",
  width_mm: 4800,
  height_mm: 600,
  depth_mm: 60,
  return_depth_mm: 60,
  letter_face_area_m2: 2.88,
  letter_perimeter_m: 18,
  letter_count: 9,
  paint_tube_count: 3,
  selected_psu_watts: 100,
  mounting_system: "direct_wall",
  mounting_template_enabled: true,
  mounting_template_area_m2: 2.88,
  paint_ral_code: "RAL 9005",
  vector_file_name: "logo.svg",
  svg_layer_mappings: { letters: "primary" },
};

describe("isVolumetricWorkIntakeHandoffCommercialMode", () => {
  it("returns false without openedFromIntake", () => {
    expect(
      isVolumetricWorkIntakeHandoffCommercialMode({
        openedFromIntake: false,
        templateCode: TPL_VOLUMETRIC_LETTERS,
        productSpec: WI_SMOKE_SPEC,
      })
    ).toBe(false);
  });

  it("returns false for incomplete spec from intake", () => {
    expect(
      isVolumetricWorkIntakeHandoffCommercialMode({
        openedFromIntake: true,
        templateCode: TPL_VOLUMETRIC_LETTERS,
        productSpec: { width_mm: 100 },
      })
    ).toBe(false);
  });
});

describe("volumetricQuoteFlowState routing", () => {
  it("routes TPL-VOLUMETRIC-LETTERS to volumetric flow", () => {
    expect(shouldRouteToVolumetricQuoteFlow(TPL_VOLUMETRIC_LETTERS)).toBe(true);
  });

  it("keeps non-volumetric templates on generic wizard", () => {
    expect(shouldRouteToVolumetricQuoteFlow("TPL-ACP-LIGHT-ROUTED")).toBe(false);
    expect(shouldRouteToVolumetricQuoteFlow(undefined)).toBe(false);
  });

  it("opens wizard from intake handoff nav state", () => {
    expect(
      shouldOpenWizardFromNav({
        openWizard: true,
      })
    ).toBe(true);
    expect(shouldOpenWizardFromNav({ openWizard: false })).toBe(false);
  });

  it("shows volumetric workspace before quotes list when handoff is active", () => {
    expect(
      shouldShowVolumetricQuoteWorkspace(true, {
        templateCode: TPL_VOLUMETRIC_LETTERS,
      })
    ).toBe(true);
    expect(
      shouldShowVolumetricQuoteWorkspace(true, {
        templateCode: "TPL-ACP-LIGHT-ROUTED",
      })
    ).toBe(false);
    expect(
      shouldShowVolumetricQuoteWorkspace(false, {
        templateCode: TPL_VOLUMETRIC_LETTERS,
      })
    ).toBe(false);
  });
});

describe("volumetricQuoteFlowState stale geometry", () => {
  it("does not treat stale vector geometry as extracted", () => {
    expect(
      buildInitialVolumetricQuoteFlowState({
        vector_file_name: "b.svg",
        geometry_stale: true,
        geometry_confirmed_for_file_name: "a.svg",
        vector_metrics_source: "svg_analysis",
        letter_perimeter_m: 50,
        letter_face_area_m2: 10,
        letter_count: 5,
        return_depth_mm: 80,
      }).quoteInput.letter_perimeter_m
    ).toBeUndefined();
  });
});

describe("volumetricQuoteFlowState prefill precedence", () => {
  it("uses Work Intake values as active field state", () => {
    const state = buildInitialVolumetricQuoteFlowState(WI_SMOKE_SPEC);
    expect(state.widthMm).toBe(4800);
    expect(state.heightMm).toBe(600);
    expect(state.depthMm).toBe(60);
    expect(state.quoteInput.letter_face_area_m2).toBe("2.88");
    expect(state.quoteInput.letter_perimeter_m).toBe("18");
    expect(state.quoteInput.letter_count).toBe("9");
  });

  it("does not show 1000/2000 defaults when intake prefill exists", () => {
    const state = buildInitialVolumetricQuoteFlowState(WI_SMOKE_SPEC);
    expect(state.widthMm).not.toBe(VOLUMETRIC_TEMPLATE_DEFAULTS.widthMm);
    expect(state.heightMm).not.toBe(VOLUMETRIC_TEMPLATE_DEFAULTS.heightMm);
  });

  it("applies defaults when prefill missing", () => {
    const state = buildInitialVolumetricQuoteFlowState(null);
    expect(state.widthMm).toBe(VOLUMETRIC_TEMPLATE_DEFAULTS.widthMm);
    expect(state.heightMm).toBe(VOLUMETRIC_TEMPLATE_DEFAULTS.heightMm);
  });

  it("user edit overrides prefill in simulation payload", () => {
    let state = buildInitialVolumetricQuoteFlowState(WI_SMOKE_SPEC);
    state = updateFlowDimension(state, "widthMm", 5000, "width_mm");
    const payload = buildSimulateQuoteInputPayload(state);
    expect(payload.width_mm).toBe(5000);
  });

  it("prefers intake_input_pathway over vector file inference", () => {
    const state = buildInitialVolumetricQuoteFlowState({
      ...WI_SMOKE_SPEC,
      intake_input_pathway: "quick_estimate",
    });
    expect(state.method).toBe("quick_estimate");
  });

  it("switching methods does not clear data", () => {
    const initial = buildInitialVolumetricQuoteFlowState(WI_SMOKE_SPEC);
    const switched = switchCalculationMethod(initial, "quick_estimate");
    expect(switched.widthMm).toBe(4800);
    expect(switched.quoteInput.letter_face_area_m2).toBe("2.88");
    expect(switched.method).toBe("quick_estimate");
  });

  it("suggests mounting_template_area_m2 from letter_face_area_m2 when enabled and missing", () => {
    const spec: IntakeProductSpec = {
      letter_face_area_m2: 2.88,
      mounting_template_enabled: true,
    };
    const prefill = { letter_face_area_m2: "2.88", mounting_template_enabled: "true" };
    const { values, suggestedKeys } = suggestMountingTemplateAreaM2(prefill, spec);
    expect(values.mounting_template_area_m2).toBe("2.88");
    expect(suggestedKeys).toContain("mounting_template_area_m2");
  });

  it("simulation payload uses effective state dimensions and geometry", () => {
    const state = buildInitialVolumetricQuoteFlowState(WI_SMOKE_SPEC);
    const payload = buildSimulateQuoteInputPayload(state, WI_SMOKE_SPEC);
    expect(payload.width_mm).toBe(4800);
    expect(payload.height_mm).toBe(600);
    expect(payload.depth_mm).toBe(60);
    expect(payload.return_depth_mm).toBe(60);
    expect(payload.letter_face_area_m2).toBe(2.88);
    expect(payload.letter_perimeter_m).toBe(18);
    expect(payload.letter_count).toBe(9);
    // Stock/default return — stale paint fields stripped from payload.
    expect(isCantRalPaintEnabled(WI_SMOKE_SPEC)).toBe(false);
    expect(payload.paint_ral_code).toBeUndefined();
    expect(payload.paint_tube_count).toBeUndefined();
    expect((payload as { volume_finish?: string }).volume_finish).toBe("none");
    expect(state.quoteInput.paint_ral_code).toBeUndefined();
  });

  it("isSimulateInputReady does not require paint tubes for stock cant", () => {
    const state = buildInitialVolumetricQuoteFlowState(WI_SMOKE_SPEC);
    expect(isSimulateInputReady(state, WI_SMOKE_SPEC)).toBe(true);
  });

  it("syncs return_depth_mm and depth_mm on dimension update", () => {
    let state = buildInitialVolumetricQuoteFlowState(WI_SMOKE_SPEC);
    state = updateFlowQuoteInputField(state, "return_depth_mm", "80");
    expect(state.depthMm).toBe(80);
    expect(state.quoteInput.return_depth_mm).toBe("80");
    expect(state.quoteInput.depth_mm).toBe("80");
  });

  it("includes paint_ral_code in simulation payload when cant RAL painting is enabled", () => {
    const paintedSpec: IntakeProductSpec = {
      ...WI_SMOKE_SPEC,
      volume_finish: "paint_after_face_miter_bond",
      paint_tube_count: 3,
      paint_ral_code: "RAL 9005",
    };
    expect(isCantRalPaintEnabled(paintedSpec)).toBe(true);
    const state = buildInitialVolumetricQuoteFlowState(paintedSpec);
    const payload = buildSimulateQuoteInputPayload(state, paintedSpec);
    expect(payload.paint_ral_code).toBe("RAL 9005");
    expect(payload.paint_tube_count).toBe(3);
  });
});

describe("volumetricQuoteFlowState materials UI", () => {
  it("materials row collapsed by default", () => {
    const state = buildInitialVolumetricQuoteFlowState(WI_SMOKE_SPEC);
    expect(state.materialsExpanded).toBe(false);
  });

  it("expanding materials shows file cards with statuses", () => {
    const files = buildClientMaterialFiles(WI_SMOKE_SPEC);
    expect(files.length).toBeGreaterThan(0);
    expect(files[0].name).toBe("logo.svg");
    expect(files[0].status).toBe("mapped");
  });

  it("photos are context-only, not cost inputs", () => {
    const files = buildClientMaterialFiles(
      null,
      "Poză locație: fata_magazin.jpg și referință"
    );
    const photo = files.find((f) => f.category === "location_photo");
    expect(photo?.contextOnly).toBe(true);
    const state = buildInitialVolumetricQuoteFlowState(null);
    const payload = buildSimulateQuoteInputPayload(state);
    expect(payload).not.toHaveProperty("fata_magazin");
  });
});

describe("volumetricQuoteFlowState user edits", () => {
  it("tracks user edits on quote input fields", () => {
    let state = buildInitialVolumetricQuoteFlowState(WI_SMOKE_SPEC);
    state = updateFlowQuoteInputField(state, "paint_tube_count", "4");
    expect(state.quoteInput.paint_tube_count).toBe("4");
    expect(state.userEditedKeys).toContain("paint_tube_count");
  });
});
