import { describe, expect, it } from "vitest";
import { buildIntakeActionSummary } from "@/lib/intakeActionSummary";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";

const volumetricSpec: IntakeProductSpec = {
  width_mm: 4800,
  height_mm: 600,
  depth_mm: 60,
  return_depth_mm: 60,
  letter_face_area_m2: 2.88,
  letter_perimeter_m: 18,
  letter_count: 9,
  selected_psu_watts: 100,
  paint_tube_count: 2,
};

describe("buildIntakeActionSummary", () => {
  it("suggests confirm template when not confirmed", () => {
    const model = buildIntakeActionSummary({
      status: "in_review",
      confirmedTemplateCode: null,
      productSpec: null,
      showVolumetricForm: true,
      readinessInput: {
        description: "desc",
        assignedTo: "Operator",
        deliveryType: "courier",
        confirmedTemplateCode: null,
      },
      requiresInstallAudit: false,
    });
    expect(model.primaryAction).toBe("confirm_template");
    expect(model.templateOk).toBe(false);
  });

  it("suggests open preliminary quote when ready and volumetric", () => {
    const model = buildIntakeActionSummary({
      status: "ready_for_quote",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      productSpec: volumetricSpec,
      showVolumetricForm: true,
      readinessInput: {
        description: "desc",
        assignedTo: "Operator",
        deliveryType: "courier",
        confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
        productSpec: volumetricSpec,
      },
      requiresInstallAudit: false,
    });
    expect(model.intakeReady).toBe(true);
    expect(model.primaryAction).toBe("open_preliminary_quote");
    expect(model.showPreliminaryQuote).toBe(true);
  });

  it("exposes staged readiness groups for volumetric intake", () => {
    const model = buildIntakeActionSummary({
      status: "in_review",
      productFamily: "litere_volumetrice",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      productSpec: volumetricSpec,
      showVolumetricForm: true,
      readinessInput: {
        description: "desc",
        assignedTo: "",
        deliveryType: "courier",
        confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
        productSpec: volumetricSpec,
      },
      requiresInstallAudit: false,
    });
    expect(model.stagedMissingGroups.length).toBeGreaterThan(0);
    expect(model.readinessStageLabel.length).toBeGreaterThan(0);
  });

  it("lists readiness missing reasons when mark ready blocked", () => {
    const model = buildIntakeActionSummary({
      status: "in_review",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      productSpec: volumetricSpec,
      showVolumetricForm: true,
      readinessInput: {
        description: "desc",
        assignedTo: "",
        deliveryType: "courier",
        confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
        productSpec: volumetricSpec,
      },
      requiresInstallAudit: false,
    });
    expect(model.primaryDisabled).toBe(true);
    expect(model.readinessMissing.some((m) => m.includes("asignat"))).toBe(true);
  });
});
