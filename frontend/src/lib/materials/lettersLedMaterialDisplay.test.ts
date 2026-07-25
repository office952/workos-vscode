import { describe, expect, it } from "vitest";
import {
  getLettersLedPsuByCode,
  LETTERS_LED_MODULE_CODE,
  LETTERS_LED_MODULE_DISPLAY_NAME,
  LETTERS_LED_MODULE_UNIT_COST_EUR_BUC,
  LETTERS_LED_PROCESS_STEPS,
  LETTERS_LED_PSU_VARIANTS,
  LETTERS_LED_STRUCTURE_DISPLAY_NAME,
  lettersLedPsuPricingLabel,
} from "./lettersLedMaterialDisplay";
import { isLettersLedStructureComponent } from "@/features/product-system/lettersLedProcessDisplay";

describe("lettersLedMaterialDisplay", () => {
  it("locks Modul LED 12V as standard with owner price", () => {
    expect(LETTERS_LED_MODULE_CODE).toBe("MAT-LED-MODULE");
    expect(LETTERS_LED_MODULE_DISPLAY_NAME).toBe("Modul LED 12V");
    expect(LETTERS_LED_MODULE_UNIT_COST_EUR_BUC).toBe(0.5);
    expect(LETTERS_LED_STRUCTURE_DISPLAY_NAME).toBe("Sistem LED — montaj pe spate Forex");
  });

  it("locks four PSU wattage variants with owner prices", () => {
    expect(LETTERS_LED_PSU_VARIANTS.map((entry) => entry.watts)).toEqual([60, 100, 160, 200]);
    expect(LETTERS_LED_PSU_VARIANTS.map((entry) => entry.unitCostEurBuc)).toEqual([
      12, 16, 20, 40,
    ]);
    expect(getLettersLedPsuByCode("MAT-LED-PSU-12V-100W")?.labelRo).toBe("100 W");
    expect(lettersLedPsuPricingLabel(160)).toBe("Sursă LED 12V 160W");
  });

  it("documents mount / PSU / colet process steps", () => {
    expect(LETTERS_LED_PROCESS_STEPS.map((step) => step.id)).toEqual([
      "led_mount_modules",
      "led_select_psu",
      "led_cables_colet",
    ]);
  });

  it("detects Sistem LED structure component, not Capac spate / Finisaj", () => {
    expect(
      isLettersLedStructureComponent({
        type: "ELECTRIC_LED",
        component_id: "comp_led_litere",
        name: "Sistem LED",
      }),
    ).toBe(true);
    expect(
      isLettersLedStructureComponent({
        type: "STRUCTURA",
        component_id: "comp_spate_litere",
        name: "Capac spate — Forex 10 mm",
      }),
    ).toBe(false);
    expect(
      isLettersLedStructureComponent({
        type: "FINISAJ",
        component_id: "comp_finisaj_litere",
        name: "Finisaj",
      }),
    ).toBe(false);
  });
});
