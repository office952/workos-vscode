import { describe, expect, it } from "vitest";
import {
  getIntakeV6RoleOptionsForLayer,
  INTAKE_V6_OWNER_LAYER_ROLE_OPTIONS,
  normalizeIntakeV6OwnerSelectableRole,
} from "./intakeV6LayerRoleOptions";

describe("getIntakeV6RoleOptionsForLayer", () => {
  it("returns the two owner-approved roles for volumetric letters layers", () => {
    const result = getIntakeV6RoleOptionsForLayer({
      layer: { name: "maria", layerKind: "pseudo", autoRole: "face" },
      layerDisplay: "Grup detectat: maria",
      confirmedRole: "face",
      detectedKind: "pseudo",
      targetTemplateCode: "TPL-VOLUMETRIC-LETTERS_v2",
      activeTemplateCode: "TPL-VOLUMETRIC-LETTERS_v2",
      assemblyType: "letters_logo",
    });

    expect(result.recommendedOptions.map((option) => option.value)).toEqual([
      "face",
      "printed_artwork",
    ]);
    expect(result.secondaryOptions).toEqual([]);
    expect(result.fallbackOptions).toEqual([]);
  });

  it("returns the same two owner-approved roles for volumetric logo layers", () => {
    const result = getIntakeV6RoleOptionsForLayer({
      layer: { name: "logo stanga", layerKind: "pseudo", autoRole: "printed_artwork" },
      layerDisplay: "Grup detectat: logo stanga",
      confirmedRole: "printed_artwork",
      detectedKind: "pseudo",
      targetTemplateCode: "TPL-VOLUMETRIC-LOGO_v1",
      activeTemplateCode: "TPL-VOLUMETRIC-LETTERS_v2",
      assemblyType: "letters_logo",
    });

    expect(result.recommendedOptions.map((option) => option.value)).toEqual([
      "face",
      "printed_artwork",
    ]);
    expect(result.secondaryOptions).toEqual([]);
    expect(result.fallbackOptions).toEqual([]);
  });

  it("exposes Contur suport in owner layer dropdown options", () => {
    expect(INTAKE_V6_OWNER_LAYER_ROLE_OPTIONS.map((o) => o.value)).toEqual([
      "face",
      "printed_artwork",
      "support_panel",
    ]);
    expect(
      normalizeIntakeV6OwnerSelectableRole({
        layer: { autoRole: "support_panel" },
        confirmedRole: "support_panel",
      }),
    ).toBe("support_panel");
  });

  it("keeps a safe grouped fallback for unknown layers", () => {
    const result = getIntakeV6RoleOptionsForLayer({
      layer: { name: "mystery", layerKind: "pseudo", autoRole: "unknown" },
      layerDisplay: "Grup detectat: mystery",
      confirmedRole: "unknown",
      detectedKind: "pseudo",
      targetTemplateCode: null,
      activeTemplateCode: null,
      assemblyType: null,
    });

    expect(result.recommendedOptions.map((option) => option.value)).toEqual([
      "face",
      "return",
      "backing",
      "vinyl",
      "ignore",
      "unknown",
    ]);
    expect(result.secondaryOptions.map((option) => option.value)).toContain("support_panel");
    expect(result.fallbackOptions).toEqual([]);
  });

  it("keeps grouped fallback behavior for non-volumetric contexts", () => {
    const result = getIntakeV6RoleOptionsForLayer({
      layer: { name: "maria", layerKind: "pseudo", autoRole: "face" },
      layerDisplay: "Grup detectat: maria",
      confirmedRole: "bevel",
      detectedKind: "pseudo",
      targetTemplateCode: null,
      activeTemplateCode: null,
      assemblyType: null,
    });

    expect(result.secondaryOptions.map((option) => option.value)).toContain("drill");
  });

  it("normalizes legacy logo-ish roles to Vector Logo for owner dropdowns", () => {
    expect(
      normalizeIntakeV6OwnerSelectableRole({
        layer: { name: "Logo 1", layerKind: "pseudo", autoRole: "printed_artwork" },
        confirmedRole: "vinyl",
        targetTemplateCode: "TPL-VOLUMETRIC-LOGO_v1",
      }),
    ).toBe("printed_artwork");
  });

  it("normalizes unknown letter-ish roles to Vector Litere for owner dropdowns", () => {
    expect(
      normalizeIntakeV6OwnerSelectableRole({
        layer: { name: "maria", layerKind: "pseudo", autoRole: "face" },
        confirmedRole: "unknown",
        targetTemplateCode: "TPL-VOLUMETRIC-LETTERS_v2",
      }),
    ).toBe("face");
  });
});