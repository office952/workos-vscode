/**
 * Canonical operator display for letter back (Capac spate).
 * Owner lock: Forex 10 mm. Stable code MAT-SPATE-PVC-LITERE (legacy PVC in code).
 */

export const LETTERS_BACK_FOREX_10MM_DISPLAY_NAME = "Forex 10 mm";
export const LETTERS_BACK_FOREX_10MM_REGISTRY_CODE = "MAT-SPATE-PVC-LITERE";
/** Owner-confirmed purchase evidence (EUR/mp, excl. TVA) — display only. */
export const LETTERS_BACK_FOREX_10MM_UNIT_COST_EUR_MP = 16.0;

export const LETTERS_BACK_STRUCTURE_DISPLAY_NAME = `Capac spate — ${LETTERS_BACK_FOREX_10MM_DISPLAY_NAME}`;

export const LETTERS_BACK_FOREX_MEANING_RO =
  "Spate litere volumetrice — Forex 10 mm (cod operațional MAT-SPATE-PVC-LITERE). Nu panou ACM, nu șablon montaj 3 mm.";

/**
 * CNC processes for back Forex (shared_cnc VOLUMETRIC_BACKING_*).
 * Debitare required; șanfren optional. Does NOT expand BADGE-CNC-PROCESSABLE onto Forex
 * (that badge remains face plexi + CNC 4020 only).
 */
export const LETTERS_BACK_FOREX_PROCESS_STEPS = [
  {
    id: "back_cnc_cut",
    labelRo: "Debitare CNC",
    required: true,
    meaningRo: "Debitare CNC spate Forex 10 mm — obligatoriu (back_cut).",
  },
  {
    id: "back_cnc_bevel",
    labelRo: "Șanfren spate",
    required: false,
    meaningRo: "Șanfren CNC spate Forex 10 mm — opțional (owner default: fără).",
  },
] as const;
