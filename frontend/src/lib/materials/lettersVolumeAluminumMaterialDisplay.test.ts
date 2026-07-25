import { describe, expect, it } from "vitest";
import {
  getLettersVolumeAluminumByCode,
  getLettersVolumeAluminumByDepthMm,
  LETTERS_VOLUME_ALUMINUM_MATERIAL_CODES,
  LETTERS_VOLUME_ALUMINUM_WIDTHS,
  lettersVolumeAluminumPricingLabel,
} from "./lettersVolumeAluminumMaterialDisplay";
import { isLettersVolumeAluminumStructureComponent } from "@/features/product-system/lettersVolumeAluminumProcessDisplay";

describe("lettersVolumeAluminumMaterialDisplay", () => {
  it("locks four aluminum volume widths with owner prices", () => {
    expect(LETTERS_VOLUME_ALUMINUM_WIDTHS.map((entry) => entry.depthMm)).toEqual([
      30, 60, 80, 100,
    ]);
    expect(LETTERS_VOLUME_ALUMINUM_MATERIAL_CODES).toEqual([
      "MAT-PROFIL-LATERAL-LITERE-30MM",
      "MAT-PROFIL-LATERAL-LITERE-60MM",
      "MAT-PROFIL-LATERAL-LITERE-80MM",
      "MAT-PROFIL-LATERAL-LITERE-100MM",
    ]);
    expect(LETTERS_VOLUME_ALUMINUM_WIDTHS.map((entry) => entry.unitCostEurMl)).toEqual([
      2.0, 3.0, 4.0, 5.0,
    ]);
  });

  it("resolves by code and depth", () => {
    expect(getLettersVolumeAluminumByCode("MAT-PROFIL-LATERAL-LITERE-80MM")?.labelRo).toBe("80 mm");
    expect(getLettersVolumeAluminumByDepthMm(60)?.materialCode).toBe(
      "MAT-PROFIL-LATERAL-LITERE-60MM",
    );
    expect(lettersVolumeAluminumPricingLabel(100)).toBe("Volum aluminiu 100 mm");
  });

  it("detects Volum aluminiu structure component, not face", () => {
    expect(
      isLettersVolumeAluminumStructureComponent({
        type: "LITERE_3D",
        component_id: "comp_lateral_litere",
        name: "Volum aluminiu",
      }),
    ).toBe(true);
    expect(
      isLettersVolumeAluminumStructureComponent({
        type: "LITERE_3D",
        component_id: "comp_face_litere",
        name: "Vizual față",
      }),
    ).toBe(false);
  });
});
