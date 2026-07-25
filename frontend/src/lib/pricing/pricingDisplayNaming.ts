/**
 * Display-only naming normalization for Pricing / Inventory labels.
 * Stable codes are never renamed here.
 */
import {
  LETTERS_BACK_FOREX_10MM_DISPLAY_NAME,
  LETTERS_BACK_FOREX_10MM_REGISTRY_CODE,
} from "@/lib/materials/lettersBackForexMaterialDisplay";
import {
  LETTERS_LED_MODULE_CODE,
  LETTERS_LED_MODULE_DISPLAY_NAME,
  LETTERS_LED_PSU_SELECTOR_CODE,
  LETTERS_LED_PSU_SELECTOR_DISPLAY_NAME,
  LETTERS_LED_PSU_VARIANTS,
  LETTERS_LED_STRIP_CODE,
  LETTERS_LED_STRIP_DISPLAY_NAME,
  lettersLedPsuPricingLabel,
} from "@/lib/materials/lettersLedMaterialDisplay";
import {
  LETTERS_VOLUME_ALUMINUM_SELECTOR_CODE,
  LETTERS_VOLUME_ALUMINUM_SELECTOR_DISPLAY_NAME,
  LETTERS_VOLUME_ALUMINUM_WIDTHS,
  lettersVolumeAluminumPricingLabel,
} from "@/lib/materials/lettersVolumeAluminumMaterialDisplay";

const VOLUME_ALU_OVERRIDES: Record<string, string> = {
  [LETTERS_VOLUME_ALUMINUM_SELECTOR_CODE]: LETTERS_VOLUME_ALUMINUM_SELECTOR_DISPLAY_NAME,
  ...Object.fromEntries(
    LETTERS_VOLUME_ALUMINUM_WIDTHS.map((entry) => [
      entry.materialCode,
      lettersVolumeAluminumPricingLabel(entry.depthMm),
    ]),
  ),
};

const LED_OVERRIDES: Record<string, string> = {
  [LETTERS_LED_MODULE_CODE]: LETTERS_LED_MODULE_DISPLAY_NAME,
  [LETTERS_LED_STRIP_CODE]: LETTERS_LED_STRIP_DISPLAY_NAME,
  [LETTERS_LED_PSU_SELECTOR_CODE]: LETTERS_LED_PSU_SELECTOR_DISPLAY_NAME,
  ...Object.fromEntries(
    LETTERS_LED_PSU_VARIANTS.map((entry) => [
      entry.materialCode,
      lettersLedPsuPricingLabel(entry.watts),
    ]),
  ),
};

const CODE_DISPLAY_OVERRIDES: Record<string, string> = {
  "MAT-ACP-FATA-LITERE": "plexiglas 3mm PMMA - opal",
  [LETTERS_BACK_FOREX_10MM_REGISTRY_CODE]: LETTERS_BACK_FOREX_10MM_DISPLAY_NAME,
  "MAT-ORACAL-8500": "Oracal 8500",
  "MAT-ORACAL-641": "Oracal 641",
  "MAT-ORACAL-651": "Oracal 651",
  "MAT-VINYL-PRINT-LAMINATED": "Printat / Laminat",
  ...VOLUME_ALU_OVERRIDES,
  ...LED_OVERRIDES,
  "MAT-ACM-BOND-3MM": "Panou compozit aluminiu (ACM/ACP) 3 mm",
  "MAT-ACM-BOND-4MM": "Panou compozit aluminiu (ACM/ACP) 4 mm",
  "MAT-ACM-BOND-PANEL": "Panou compozit aluminiu (ACM/ACP) — rezolvare grosime",
  "MAT-ACP-3MM": "Panou compozit aluminiu (ACM/ACP) 3 mm — alias legacy",
  CNC_ROUTER: "CNC router — debitare / tăiere",
  ACM_PANEL_CUTTING: "Debitare panou ACM",
  ACM_V_GROOVE: "Canelare V-groove ACM",
  LASER_CUTTING: "CNC laser — tăiere",
  FACE_VINYL_APPLICATION_LABOR: "Manoperă aplicare folie fețe",
  RETURN_CANT_VINYL_APPLICATION_LABOR: "Manoperă aplicare folie pe cant",
  RETURN_CANT_RAL_PAINT_LABOR: "Manoperă vopsire RAL pe cant",
  SITE_INSTALLATION_STANDARD: "Montaj la locație (standard)",
  LAMINATION: "Serviciu laminare",
  LARGE_FORMAT_PRINT: "Serviciu print format mare",
};

export function normalizePricingDisplayName(code: string, fallbackName: string): string {
  const c = String(code || "").trim().toUpperCase();
  if (CODE_DISPLAY_OVERRIDES[c]) return CODE_DISPLAY_OVERRIDES[c];
  return fallbackName || code;
}

export function misleadingCodeNoteRo(code: string): string | null {
  const c = String(code || "").trim().toUpperCase();
  if (c === "MAT-ACP-FATA-LITERE") {
    return "Cod istoric conține ACP; stoc = plexiglas 3mm PMMA - opal (procesabil CNC — BADGE-CNC-PROCESSABLE). Nu panou ACM.";
  }
  if (c === "MAT-ACP-3MM") {
    return "Alias legacy pentru MAT-ACM-BOND-3MM — nu a doua opțiune de preț.";
  }
  if (c === LETTERS_VOLUME_ALUMINUM_SELECTOR_CODE) {
    return "Selector template — fără preț unic. Alege Volum aluminiu 30/60/80/100 mm (return_depth_mm). Nu ACM, nu premontaj, nu casetă.";
  }
  if (c.startsWith("MAT-PROFIL-LATERAL-LITERE-") && c.endsWith("MM")) {
    return "Pas structură Volum aluminiu (profil Al 0.6 mm). Nu panou ACM, nu țeavă premontaj, nu profil casetă.";
  }
  if (c === LETTERS_BACK_FOREX_10MM_REGISTRY_CODE) {
    return "Capac spate litere = Forex 10 mm. Cod istoric PVC; nu panou ACM, nu șablon montaj 3 mm.";
  }
  if (c === LETTERS_LED_MODULE_CODE) {
    return "Pas Sistem LED — standard litere (led_modules). Montaj pe spate Forex. Nu bandă LED.";
  }
  if (c === LETTERS_LED_STRIP_CODE) {
    return "Alternativă Sistem LED (led_strip). Nu înlocuiește Modul LED 12V ca standard.";
  }
  if (c === LETTERS_LED_PSU_SELECTOR_CODE) {
    return "Selector template — fără preț unic. Alege Sursă LED 12V 60/100/160/200 W (selected_psu_watts). Nu multiplica prețul cu W.";
  }
  if (c.startsWith("MAT-LED-PSU-12V-") && c.endsWith("W")) {
    return "Sursă LED 12V pe clasă de putere (EUR/buc). Nu multiplica prețul cu valoarea W.";
  }
  return null;
}
