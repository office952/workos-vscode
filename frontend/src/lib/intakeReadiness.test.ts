import { describe, expect, it } from "vitest";
import {
  evaluateIntakeReadyPrerequisites,
  shouldShowVolumetricProductForm,
} from "./intakeReadiness";
import { isLitereVolumetriceFamily } from "./intakeProductSpec";
import { TPL_VOLUMETRIC_LETTERS } from "./volumetricQuoteInput";

describe("intakeReadiness", () => {
  const volumetricSpec = {
    width_mm: 4800,
    height_mm: 600,
    return_depth_mm: 60,
    letter_face_area_m2: 2.88,
    letter_perimeter_m: 18,
    letter_count: 9,
  };

  it("volumetric structured dimensions satisfy prerequisite without free-text dimensions", () => {
    const result = evaluateIntakeReadyPrerequisites({
      description: "Smoke",
      dimensions: "",
      assignedTo: "Maria C.",
      deliveryType: "delivery_standard",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      productSpec: volumetricSpec,
      requiresInstallAudit: false,
    });
    expect(result.missing).not.toContain("Dimensiuni — lipsă");
    expect(result.canMarkReady).toBe(true);
  });

  it("flags missing structured envelope for volumetric", () => {
    const result = evaluateIntakeReadyPrerequisites({
      description: "Smoke",
      assignedTo: "Maria C.",
      deliveryType: "delivery_standard",
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      productSpec: { width_mm: 4800 },
      requiresInstallAudit: false,
    });
    expect(result.missing.some((m) => m.includes("Dimensiuni din specificație"))).toBe(
      true
    );
  });

  it("generic intake still requires free-text dimensions", () => {
    const result = evaluateIntakeReadyPrerequisites({
      description: "Banner",
      dimensions: "",
      assignedTo: "Maria C.",
      deliveryType: "delivery_standard",
      confirmedTemplateCode: "TPL-BANNER-STANDARD",
      requiresInstallAudit: false,
    });
    expect(result.missing).toContain("Dimensiuni — lipsă");
  });

  it("renders volumetric form from confirmed template code", () => {
    expect(
      shouldShowVolumetricProductForm(
        TPL_VOLUMETRIC_LETTERS,
        "other_family",
        isLitereVolumetriceFamily
      )
    ).toBe(true);
    expect(
      shouldShowVolumetricProductForm(null, "print_large_format", isLitereVolumetriceFamily)
    ).toBe(false);
  });
});
