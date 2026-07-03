import { describe, expect, it } from "vitest";
import {
  intakeTerrainGatesActive,
  isIntakeGateStage0,
  resolveIntakeGateStage,
} from "./intakeGateStages";

describe("intakeGateStages", () => {
  it("treats empty product_family as stage 0", () => {
    expect(isIntakeGateStage0("")).toBe(true);
    expect(isIntakeGateStage0("   ")).toBe(true);
    expect(resolveIntakeGateStage({
      productFamily: "",
      status: "new",
      showVolumetricForm: false,
      readinessInput: {
        description: "x",
        dimensions: "—",
        assignedTo: "—",
        deliveryType: "delivery_install",
        confirmedTemplateCode: null,
        productSpec: null,
        siteAudit: null,
        requiresInstallAudit: true,
      },
    })).toBe(0);
  });

  it("disables terrain gates in stage 0 even with install delivery", () => {
    expect(intakeTerrainGatesActive("", "delivery_install")).toBe(false);
    expect(intakeTerrainGatesActive("litere_volumetrice", "delivery_install")).toBe(
      true
    );
    expect(intakeTerrainGatesActive("litere_volumetrice", "courier")).toBe(false);
  });
});
