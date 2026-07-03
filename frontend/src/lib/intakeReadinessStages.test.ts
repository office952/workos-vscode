import { describe, expect, it } from "vitest";
import {
  buildIntakeReadinessStages,
  evaluateSimulationReadiness,
  groupMissingReasonsByStage,
} from "@/lib/intakeReadinessStages";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { EMPTY_SITE_AUDIT } from "@/lib/intakeSiteAudit";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";

const wiSmokeSpec: IntakeProductSpec = {
  width_mm: 4800,
  height_mm: 600,
  depth_mm: 60,
  return_depth_mm: 60,
  letter_face_area_m2: 2.88,
  letter_perimeter_m: 18,
  letter_count: 9,
  selected_psu_watts: 100,
  paint_tube_count: 2,
  volume_finish: "none" as const,
  return_color: "white" as const,
  vector_analysis_status: "analyzed" as const,
};

const readinessBase = {
  description: "Smoke test",
  assignedTo: "Operator",
  deliveryType: "courier" as const,
  confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
  productSpec: wiSmokeSpec,
  requiresInstallAudit: false,
};

describe("intakeReadinessStages", () => {
  it("generic unresolved is Stage 0 with no downstream blockers", () => {
    const stages = buildIntakeReadinessStages({
      productFamily: "",
      status: "new",
      confirmedTemplateCode: null,
      showVolumetricForm: false,
      readinessInput: {
        description: "Banner request",
        assignedTo: "Op",
        deliveryType: "courier",
      },
      requiresInstallAudit: false,
    });
    expect(stages.currentStage).toBe("stage0_unresolved");
    expect(stages.simulationMissing).toEqual([]);
    expect(stages.commercialMissing).toEqual([]);
    expect(stages.productionMissing).toEqual([]);
    expect(stages.grouped).toHaveLength(1);
  });

  it("volumetric missing geometry is stage1 and blocks simulation", () => {
    const spec = {
      width_mm: 1000,
      height_mm: 200,
      depth_mm: 60,
    };
    const stages = buildIntakeReadinessStages({
      productFamily: "litere_volumetrice",
      status: "in_review",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      showVolumetricForm: true,
      readinessInput: {
        ...readinessBase,
        productSpec: spec,
      },
      requiresInstallAudit: false,
    });
    expect(stages.canSimulate).toBe(false);
    expect(stages.workingStage).toBe("stage1_spec");
    expect(stages.simulationMissing.length).toBeGreaterThan(0);
  });

  it("volumetric with simulation fields complete is simulation-ready", () => {
    const stages = buildIntakeReadinessStages({
      productFamily: "litere_volumetrice",
      status: "in_review",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      showVolumetricForm: true,
      readinessInput: readinessBase,
      requiresInstallAudit: false,
    });
    expect(stages.canSimulate).toBe(true);
    expect(stages.workingStage).toBe("stage2_simulation");
  });

  it("commercial blockers do not block preliminary simulation readiness", () => {
    const stages = buildIntakeReadinessStages({
      productFamily: "litere_volumetrice",
      status: "in_review",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      showVolumetricForm: true,
      readinessInput: {
        ...readinessBase,
        assignedTo: "",
        productSpec: {
          ...wiSmokeSpec,
          vector_file_name: undefined,
          vector_manual_review_approved: false,
          vector_analysis_status: undefined,
        },
      },
      requiresInstallAudit: false,
    });
    expect(stages.canSimulate).toBe(true);
    expect(stages.canMarkCommercial).toBe(false);
    expect(stages.commercialMissing.some((m) => m.includes("asignat"))).toBe(
      true
    );
  });

  it("production-only blockers do not block simulation readiness", () => {
    const stages = buildIntakeReadinessStages({
      productFamily: "litere_volumetrice",
      status: "in_review",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      showVolumetricForm: true,
      readinessInput: {
        ...readinessBase,
        productSpec: {
          ...wiSmokeSpec,
          vector_manual_review_approved: false,
          vector_analysis_status: undefined,
        },
      },
      requiresInstallAudit: false,
    });
    expect(stages.canSimulate).toBe(true);
    expect(stages.productionMissing.length).toBeGreaterThan(0);
  });

  it("delivery+install terrain appears under commercial not stage0", () => {
    const stages = buildIntakeReadinessStages({
      productFamily: "litere_volumetrice",
      status: "in_review",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      showVolumetricForm: true,
      readinessInput: {
        ...readinessBase,
        deliveryType: "delivery_install",
        siteAudit: {
          ...EMPTY_SITE_AUDIT,
          checks: {
            ...EMPTY_SITE_AUDIT.checks,
            address_confirmed: false,
            photos_verified: false,
            power_confirmed: false,
            access_confirmed: false,
          },
        },
      },
      requiresInstallAudit: true,
    });
    expect(stages.currentStage).not.toBe("stage0_unresolved");
    expect(stages.commercialMissing.some((m) => m.includes("Audit teren"))).toBe(
      true
    );
    expect(stages.simulationMissing.some((m) => m.includes("Audit teren"))).toBe(
      false
    );
  });

  it("non-install delivery does not produce terrain blockers", () => {
    const stages = buildIntakeReadinessStages({
      productFamily: "litere_volumetrice",
      status: "in_review",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      showVolumetricForm: true,
      readinessInput: readinessBase,
      requiresInstallAudit: false,
    });
    expect(stages.commercialMissing.some((m) => m.includes("teren"))).toBe(
      false
    );
  });

  it("SVG geometry suggestions do not make simulation-ready until metrics applied", () => {
    const spec: IntakeProductSpec = {
      width_mm: 1000,
      height_mm: 200,
      depth_mm: 60,
      geometry_source: "svg_suggestion_confirmed",
      vector_file_name: "letters.svg",
    };
    const sim = evaluateSimulationReadiness({
      showVolumetricForm: true,
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      productSpec: spec,
    });
    expect(sim.ready).toBe(false);
    expect(sim.missing.some((m) => m.includes("Aria față"))).toBe(true);
    expect(sim.missing.some((m) => m.includes("Perimetru"))).toBe(true);
  });

  it("stock cant with stale paint_tube_count does not require RAL for simulation", () => {
    const sim = evaluateSimulationReadiness({
      showVolumetricForm: true,
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      productSpec: {
        width_mm: 1000,
        height_mm: 200,
        return_depth_mm: 60,
        return_color: "white",
        volume_finish: "none",
        paint_tube_count: 3,
        letter_face_area_m2: 0.5,
        letter_perimeter_m: 4,
        letter_count: 3,
        lighting_system_type: "led_modules",
        led_module_power_w: 0.72,
        light_color: "warm",
        selected_psu_watts: 100,
        mounting_system: "direct_wall",
        mounting_template_enabled: true,
        mounting_template_area_m2: 0.5,
      },
    });
    expect(sim.ready).toBe(true);
    expect(sim.missing.some((m) => m.includes("RAL"))).toBe(false);
  });

  it("V2 psu_configuration satisfies simulation readiness without selected_psu_watts", () => {
    const sim = evaluateSimulationReadiness({
      showVolumetricForm: true,
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      productSpec: {
        width_mm: 1000,
        height_mm: 200,
        return_depth_mm: 60,
        return_color: "black",
        volume_finish: "none",
        letter_face_area_m2: 0.5,
        letter_perimeter_m: 4,
        letter_count: 3,
        lighting_system_type: "led_modules",
        led_module_power_w: 0.72,
        light_color: "warm",
        psu_allocation_status: "ok",
        psu_configuration: [100],
        mounting_system: "direct_wall",
        mounting_template_enabled: true,
        mounting_template_area_m2: 0.5,
      },
    });
    expect(sim.missing.some((m) => m.includes("Putere sursă LED"))).toBe(false);
  });

  it("applying SVG suggested dimensions clears width/height blockers only", () => {
    const withDims: IntakeProductSpec = {
      width_mm: 1000,
      height_mm: 200,
      depth_mm: 60,
      return_depth_mm: 60,
      selected_psu_watts: 100,
      paint_tube_count: 2,
      letter_face_area_m2: 0.5,
      letter_perimeter_m: 4,
      letter_count: 3,
    };
    const sim = evaluateSimulationReadiness({
      showVolumetricForm: true,
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      productSpec: withDims,
    });
    expect(sim.ready).toBe(true);
    expect(sim.missing.some((m) => m.includes("width/height"))).toBe(false);
  });

  it("groups missing reasons by stage for side panel", () => {
    const groups = groupMissingReasonsByStage({
      specMissing: ["Template produs — neconfirmat"],
      simulationMissing: ["Perimetru litere (ml)"],
      commercialMissing: ["Persoană asignată — lipsă"],
      productionMissing: ["Verificare vector finală pentru producție"],
      canSimulate: false,
      canMarkCommercial: false,
      canProduction: false,
      isStage0: false,
    });
    expect(groups).toHaveLength(4);
    expect(groups[1].missing).toContain("Perimetru litere (ml)");
    expect(groups[2].missing).toContain("Persoană asignată — lipsă");
    expect(groups[3].missing).toContain(
      "Verificare vector finală pentru producție"
    );
  });

  it("WI-SMOKE-P001 spec remains simulation-ready", () => {
    const stages = buildIntakeReadinessStages({
      productFamily: "litere_volumetrice",
      status: "ready_for_quote",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      showVolumetricForm: true,
      readinessInput: readinessBase,
      requiresInstallAudit: false,
    });
    expect(stages.canSimulate).toBe(true);
    expect(stages.legacyReadyForQuote).toBe(true);
  });

  it("preserves ready_for_quote legacy flag semantics", () => {
    const stages = buildIntakeReadinessStages({
      productFamily: "litere_volumetrice",
      status: "ready_for_quote",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      showVolumetricForm: true,
      readinessInput: readinessBase,
      requiresInstallAudit: false,
    });
    expect(stages.legacyReadyForQuote).toBe(true);
    // Stale paint_tube_count on stock cant no longer blocks production readiness.
    expect(stages.currentStage).toBe("stage4_production");
  });
});
