/**
 * Canonical operator display for letter Sistem LED.
 * Standard: module LED 12V on Forex back; alternative: bandă LED.
 * PSU: selector + wattage variants (owner-confirmed purchase evidence).
 * Stable registry codes are never renamed.
 */

export const LETTERS_LED_FAMILY_LABEL_RO = "Sistem LED";
export const LETTERS_LED_MOUNT_NOTE_RO = "montaj pe spate Forex";

export const LETTERS_LED_MODULE_CODE = "MAT-LED-MODULE";
export const LETTERS_LED_MODULE_DISPLAY_NAME = "Modul LED 12V";
/** Owner-confirmed purchase evidence (EUR/buc, excl. TVA) — display only. */
export const LETTERS_LED_MODULE_UNIT_COST_EUR_BUC = 0.5;

export const LETTERS_LED_STRIP_CODE = "MAT-LED-STRIP";
export const LETTERS_LED_STRIP_DISPLAY_NAME = "Bandă LED 12V";
/** Owner-confirmed purchase evidence (EUR/ml, excl. TVA) — display only. */
export const LETTERS_LED_STRIP_UNIT_COST_EUR_ML = 2.0;

export const LETTERS_LED_PSU_SELECTOR_CODE = "MAT-LED-PSU-12V";
export const LETTERS_LED_PSU_SELECTOR_DISPLAY_NAME =
  "Sursă LED 12V — alege puterea (60/100/160/200 W)";

/** Structure row subtitle under SISTEM LED. */
export const LETTERS_LED_STRUCTURE_DISPLAY_NAME = `${LETTERS_LED_FAMILY_LABEL_RO} — ${LETTERS_LED_MOUNT_NOTE_RO}`;

export type LettersLedPsuEntry = {
  id: "psu_60" | "psu_100" | "psu_160" | "psu_200";
  watts: 60 | 100 | 160 | 200;
  labelRo: string;
  materialCode: string;
  /** Owner-confirmed purchase evidence (EUR/buc, excl. TVA) — display only. */
  unitCostEurBuc: number;
  meaningRo: string;
};

/** Owner-confirmed PSU wattage tiers. */
export const LETTERS_LED_PSU_VARIANTS: readonly LettersLedPsuEntry[] = [
  {
    id: "psu_60",
    watts: 60,
    labelRo: "60 W",
    materialCode: "MAT-LED-PSU-12V-60W",
    unitCostEurBuc: 12.0,
    meaningRo: "Sursă LED 12V 60W — varianta după selected_psu_watts. Nu multiplica prețul cu valoarea W.",
  },
  {
    id: "psu_100",
    watts: 100,
    labelRo: "100 W",
    materialCode: "MAT-LED-PSU-12V-100W",
    unitCostEurBuc: 16.0,
    meaningRo: "Sursă LED 12V 100W — varianta după selected_psu_watts. Nu multiplica prețul cu valoarea W.",
  },
  {
    id: "psu_160",
    watts: 160,
    labelRo: "160 W",
    materialCode: "MAT-LED-PSU-12V-160W",
    unitCostEurBuc: 20.0,
    meaningRo: "Sursă LED 12V 160W — varianta după selected_psu_watts. Nu multiplica prețul cu valoarea W.",
  },
  {
    id: "psu_200",
    watts: 200,
    labelRo: "200 W",
    materialCode: "MAT-LED-PSU-12V-200W",
    unitCostEurBuc: 40.0,
    meaningRo: "Sursă LED 12V 200W — varianta după selected_psu_watts. Nu multiplica prețul cu valoarea W.",
  },
] as const;

export function lettersLedPsuPricingLabel(watts: number): string {
  return `Sursă LED 12V ${watts}W`;
}

export function getLettersLedPsuByCode(
  materialCode: string | null | undefined,
): LettersLedPsuEntry | null {
  const code = String(materialCode ?? "")
    .trim()
    .toUpperCase();
  return LETTERS_LED_PSU_VARIANTS.find((entry) => entry.materialCode === code) ?? null;
}

/**
 * Documented production paths for Sistem LED (display only).
 * Standard lighting_system_type = led_modules; led_strip is alternative.
 */
export const LETTERS_LED_PROCESS_STEPS = [
  {
    id: "led_mount_modules",
    labelRo: "Montaj module pe spate",
    meaningRo:
      "Module LED 12V pe spatele Forex — cantitate din perimetru (pitch 250 mm, Intake V4/V6). Standard: led_modules.",
  },
  {
    id: "led_select_psu",
    labelRo: "Alegere sursă (W)",
    meaningRo:
      "Sursă 12V după puterea necesară (60/100/160/200 W). Selector template MAT-LED-PSU-12V.",
  },
  {
    id: "led_cables_colet",
    labelRo: "Cabluri / colet",
    meaningRo:
      "Fără suport comun: sursele se pregătesc în colet, fără task separat de montaj sursă pe suport.",
  },
] as const;
