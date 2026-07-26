import { describe, expect, it } from "vitest";
import { TPL_VOLUMETRIC_LETTERS_V2 } from "@/lib/volumetricQuoteInput";
import {
  buildLettersVolumAluminiuPath,
  resolveLettersStructureDetailPath,
} from "./lettersStructureDetailRoutes";

describe("lettersStructureDetailRoutes", () => {
  it("resolves volume chip/row to volum-aluminiu detail path", () => {
    const path = resolveLettersStructureDetailPath(TPL_VOLUMETRIC_LETTERS_V2, {
      type: "STRUCTURA",
      component_id: "comp_volum_aluminiu",
      name: "Volum aluminiu — profil Al 0.6 mm",
    });
    expect(path).toBe(buildLettersVolumAluminiuPath(TPL_VOLUMETRIC_LETTERS_V2));
  });

  it("resolves face and back detail paths", () => {
    expect(
      resolveLettersStructureDetailPath(TPL_VOLUMETRIC_LETTERS_V2, {
        type: "STRUCTURA",
        component_id: "comp_fata",
        name: "Vizual față — plexiglas",
      }),
    ).toMatch(/structure\/vizual-fata$/);

    expect(
      resolveLettersStructureDetailPath(TPL_VOLUMETRIC_LETTERS_V2, {
        type: "STRUCTURA",
        component_id: "comp_spate",
        name: "Capac spate — Forex 10 mm",
      }),
    ).toMatch(/structure\/capac-spate$/);
  });

  it("resolves LED detail path and null for non-letters / finisaj", () => {
    expect(
      resolveLettersStructureDetailPath(TPL_VOLUMETRIC_LETTERS_V2, {
        type: "ELECTRIC_LED",
        component_id: "comp_led",
        name: "Sistem LED — montaj pe spate Forex",
      }),
    ).toMatch(/structure\/sistem-led$/);
    expect(
      resolveLettersStructureDetailPath(TPL_VOLUMETRIC_LETTERS_V2, {
        type: "FINISAJ",
        component_id: "comp_finisaj",
        name: "Finisaj",
      }),
    ).toBeNull();
    expect(
      resolveLettersStructureDetailPath("TPL-OTHER", {
        type: "STRUCTURA",
        component_id: "comp_volum",
        name: "Volum aluminiu",
      }),
    ).toBeNull();
  });
});
