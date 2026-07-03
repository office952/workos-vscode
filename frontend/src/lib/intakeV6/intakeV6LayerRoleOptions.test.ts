import { describe, expect, it } from "vitest";
import { getIntakeV6RoleOptionsForLayer } from "./intakeV6LayerRoleOptions";

describe("getIntakeV6RoleOptionsForLayer", () => {
  it("returns letters-first recommended roles for volumetric letters layers", () => {
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
      "return",
      "backing",
      "vinyl",
      "ignore",
      "unknown",
    ]);
    expect(result.secondaryOptions.map((option) => option.value)).toContain("drill");
    expect(result.secondaryOptions.map((option) => option.value)).toContain("logo");
  });

  it("returns logo-first recommended roles for volumetric logo layers", () => {
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
      "logo",
      "printed_artwork",
      "vinyl",
      "face",
      "ignore",
      "unknown",
    ]);
    expect(result.secondaryOptions.map((option) => option.value)).toContain("return");
    expect(result.secondaryOptions.map((option) => option.value)).not.toContain("logo");
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
      "logo",
      "printed_artwork",
      "support_panel",
      "vinyl",
    ]);
    expect(result.secondaryOptions.map((option) => option.value)).toContain("backing");
    expect(result.fallbackOptions.map((option) => option.value)).toEqual(["ignore", "unknown"]);
  });

  it("keeps the currently selected role available even when it is not recommended", () => {
    const result = getIntakeV6RoleOptionsForLayer({
      layer: { name: "maria", layerKind: "pseudo", autoRole: "face" },
      layerDisplay: "Grup detectat: maria",
      confirmedRole: "bevel",
      detectedKind: "pseudo",
      targetTemplateCode: "TPL-VOLUMETRIC-LETTERS_v2",
      activeTemplateCode: "TPL-VOLUMETRIC-LETTERS_v2",
      assemblyType: "letters_only",
    });

    expect(result.secondaryOptions.map((option) => option.value)).toContain("bevel");
  });
});