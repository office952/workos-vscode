import { describe, expect, it } from "vitest";
import {
  LETTERS_BACK_FOREX_10MM_DISPLAY_NAME,
  LETTERS_BACK_FOREX_10MM_REGISTRY_CODE,
  LETTERS_BACK_FOREX_10MM_UNIT_COST_EUR_MP,
  LETTERS_BACK_FOREX_PROCESS_STEPS,
  LETTERS_BACK_STRUCTURE_DISPLAY_NAME,
} from "./lettersBackForexMaterialDisplay";
import { isLettersBackForexStructureComponent } from "@/features/product-system/lettersBackForexProcessDisplay";

describe("lettersBackForexMaterialDisplay", () => {
  it("locks Capac spate Forex 10 mm identity", () => {
    expect(LETTERS_BACK_FOREX_10MM_DISPLAY_NAME).toBe("Forex 10 mm");
    expect(LETTERS_BACK_FOREX_10MM_REGISTRY_CODE).toBe("MAT-SPATE-PVC-LITERE");
    expect(LETTERS_BACK_FOREX_10MM_UNIT_COST_EUR_MP).toBe(16);
    expect(LETTERS_BACK_STRUCTURE_DISPLAY_NAME).toBe("Capac spate — Forex 10 mm");
  });

  it("documents debitare required and șanfren optional", () => {
    expect(LETTERS_BACK_FOREX_PROCESS_STEPS.map((step) => step.id)).toEqual([
      "back_cnc_cut",
      "back_cnc_bevel",
    ]);
    expect(LETTERS_BACK_FOREX_PROCESS_STEPS[0]?.required).toBe(true);
    expect(LETTERS_BACK_FOREX_PROCESS_STEPS[1]?.required).toBe(false);
  });

  it("detects Capac spate structure component, not LED / șablon / față", () => {
    expect(
      isLettersBackForexStructureComponent({
        type: "LITERE_3D",
        component_id: "comp_spate_litere",
        name: "Capac spate — Forex 10 mm",
      }),
    ).toBe(true);
    expect(
      isLettersBackForexStructureComponent({
        type: "LITERE_3D",
        component_id: "comp_led_litere",
        name: "Iluminare LED — montaj pe spate Forex",
      }),
    ).toBe(false);
    expect(
      isLettersBackForexStructureComponent({
        type: "LITERE_3D",
        component_id: "comp_sablon",
        name: "Șablon montaj Forex 3 mm",
      }),
    ).toBe(false);
    expect(
      isLettersBackForexStructureComponent({
        type: "LITERE_3D",
        component_id: "comp_face_litere",
        name: "Vizual față",
      }),
    ).toBe(false);
  });
});
