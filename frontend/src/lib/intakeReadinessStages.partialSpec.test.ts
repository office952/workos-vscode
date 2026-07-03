import { describe, expect, it } from "vitest";
import { buildIntakeReadinessStages } from "./intakeReadinessStages";
import { TPL_VOLUMETRIC_LETTERS } from "./volumetricQuoteInput";

describe("intakeReadinessStages partial legacy spec", () => {
  it("does not throw for E2E WARN-like spec without new SVG mapping fields", () => {
    expect(() =>
      buildIntakeReadinessStages({
        productFamily: "litere_volumetrice",
        status: "in_review",
        confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
        showVolumetricForm: true,
        requiresInstallAudit: false,
        readinessInput: {
          productSpec: {
            width_mm: 4800,
            height_mm: 600,
            depth_mm: 60,
            vector_file_name: "e2e-volumetric-letters.svg",
            vector_analysis_status: "manual_review_approved",
            svg_layer_mappings: { Layer_x0020_1: TPL_VOLUMETRIC_LETTERS },
          },
          assignedTo: "Operator",
          description: "E2E WARN",
          dimensions: "4800x600",
          deliveryType: "courier",
        },
      })
    ).not.toThrow();
  });

  it("does not throw when productSpec is null", () => {
    const result = buildIntakeReadinessStages({
      productFamily: "litere_volumetrice",
      status: "new",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      showVolumetricForm: true,
      requiresInstallAudit: false,
      readinessInput: {
        productSpec: null,
        assignedTo: "",
        description: "",
        dimensions: "",
        deliveryType: "courier",
      },
    });
    expect(result.currentStage).toBeDefined();
  });
});
