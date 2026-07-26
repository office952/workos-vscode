import { describe, expect, it } from "vitest";
import {
  describeOfferScopeSummary,
  resolveActiveOfferScopePreset,
} from "./intakeV6OfferScopePresets";

describe("intakeV6OfferScopePresets", () => {
  it("resolves Build 3 presets", () => {
    expect(resolveActiveOfferScopePreset("full_product", [])).toBe("full_product");
    expect(resolveActiveOfferScopePreset("component_subset", ["FACE"])).toBe("face_only");
    expect(resolveActiveOfferScopePreset("component_subset", ["RETURN-CANT"])).toBe("cant_only");
    expect(resolveActiveOfferScopePreset("component_subset", ["FACE", "RETURN-CANT"])).toBe(
      "face_cant",
    );
  });

  it("describes cant-only active/excluded labels with diacritics", () => {
    const summary = describeOfferScopeSummary("component_subset", ["RETURN-CANT"]);
    expect(summary.requestModeLabelRo).toBe("Subset componente");
    expect(summary.activeLabelsRo).toEqual(["Cant"]);
    expect(summary.excludedLabelsRo).toContain("Față");
    expect(summary.excludedLabelsRo).toContain("Spate");
    expect(summary.excludedLabelsRo).toContain("Iluminare");
  });
});
