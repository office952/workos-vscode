/**
 * Sistem LED — explanatory + directional documentation (operator-facing).
 * Sourced from owner display locks + LED pitch/PSU rules — display only; no Product Truth write.
 *
 * Canonical markdown mirror:
 * docs/worklog/realignment/2026-07-23_letters_sistem_led_structure_documentation.md
 */

import {
  LETTERS_LED_FAMILY_LABEL_RO,
  LETTERS_LED_MODULE_CODE,
  LETTERS_LED_MODULE_DISPLAY_NAME,
  LETTERS_LED_MOUNT_NOTE_RO,
  LETTERS_LED_PROCESS_STEPS,
  LETTERS_LED_PSU_SELECTOR_CODE,
  LETTERS_LED_PSU_VARIANTS,
  LETTERS_LED_STRIP_CODE,
  LETTERS_LED_STRIP_DISPLAY_NAME,
  LETTERS_LED_STRUCTURE_DISPLAY_NAME,
} from "@/lib/materials/lettersLedMaterialDisplay";

export type LettersLedDocSection = {
  id: string;
  titleRo: string;
  bodyRo: string;
  bulletsRo?: readonly string[];
};

export type LettersLedDocSource = {
  labelRo: string;
  path: string;
};

export type LettersLedCalcCard = {
  id: "module_count" | "psu_selection";
  importance: 1 | 2;
  titleRo: string;
  subtitleRo: string;
  formulaRo: string;
  stepsRo: readonly string[];
  outputsRo: readonly string[];
  notThisRo: readonly string[];
  priceNoteRo: string;
  verifyHref: string;
  verifyLabelRo: string;
};

/** Intake V4/V6 letter module pitch — matches INTAKE_V4_LED_PITCH_MM. */
export const LETTERS_LED_PITCH_MM = 250;

/** Matches INTAKE_V4_LED_MODULE_WATTAGE_OPTIONS + dossier led_module_power_w. */
export const LETTERS_LED_MODULE_WATTAGE_OPTIONS_W = [0.75, 1.0, 1.44] as const;
export const LETTERS_LED_MODULE_WATTAGE_DEFAULT_W = 0.75;

/** Matches dossier light_color allowed_values / default. */
export const LETTERS_LED_LIGHT_COLOR_OPTIONS = ["warm", "neutral", "cool"] as const;
export const LETTERS_LED_LIGHT_COLOR_DEFAULT = "warm";

/** PSU reserve — matches INTAKE_V4_PSU_RESERVE_RATIO / backend DEFAULT_RESERVE_PERCENT. */
export const LETTERS_LED_PSU_RESERVE_PERCENT = 30;

export const LETTERS_LED_DOC_ROLE_RO =
  "Pasul 4 din Structură produs (Litere volumetrice): iluminarea pe spatele Forex — doar litere (module LED 12V standard + sursă 12V); bandă LED ca alternativă. Emblema nu e pe această pagină.";

export const LETTERS_LED_DOC_DIRECTION_RO =
  "În sistem: Structură produs = hartă scurtă; această pagină = documentul LED litere. Pattern-ul urmează modelul Vizual față. Emblema / caseta pe densitate mp = tratament separat. Urmează Finisaj. Litere se închid UI înainte de contract ACM / Composer.";

export const LETTERS_LED_DOC_SECTIONS: readonly LettersLedDocSection[] = [
  {
    id: "role",
    titleRo: `Ce este ${LETTERS_LED_FAMILY_LABEL_RO}`,
    bodyRo: `${LETTERS_LED_STRUCTURE_DISPLAY_NAME}. Nu este alimentarea 220V a carcasei / panoului ACM — e iluminarea literei (PSU litere).`,
    bulletsRo: [
      "Loc în nucleu: după Capac spate Forex, înainte de Finisaj",
      `Montaj: ${LETTERS_LED_MOUNT_NOTE_RO}`,
      "Scope: doar litere — emblema se tratează separat",
      "Finish line laborator: cost de producție / EIC — nu ofertă, nu Execution",
    ],
  },
  {
    id: "material",
    titleRo: "Materiale iluminare (litere)",
    bodyRo: `Standard litere: «${LETTERS_LED_MODULE_DISPLAY_NAME}» (${LETTERS_LED_MODULE_CODE}). Alternativă: «${LETTERS_LED_STRIP_DISPLAY_NAME}» (${LETTERS_LED_STRIP_CODE}) când lighting_system_type=led_strip.`,
    bulletsRo: [
      `${LETTERS_LED_MODULE_DISPLAY_NAME} · ${LETTERS_LED_MODULE_CODE} · unitate buc`,
      `Putere modul (operator): ${LETTERS_LED_MODULE_WATTAGE_OPTIONS_W.join(" / ")} W — default ${LETTERS_LED_MODULE_WATTAGE_DEFAULT_W} W (led_module_power_w)`,
      `Culoare lumină (operator): ${LETTERS_LED_LIGHT_COLOR_OPTIONS.join(" / ")} — default ${LETTERS_LED_LIGHT_COLOR_DEFAULT} (light_color)`,
      `${LETTERS_LED_STRIP_DISPLAY_NAME} · ${LETTERS_LED_STRIP_CODE} · unitate ml (alt.)`,
      "Emblemă / casetă pe densitate mp — în afara acestei pagini (tratament separat)",
      "Prețurile se verifică în Pricing Registry — nu se dublează aici",
    ],
  },
  {
    id: "psu",
    titleRo: "Surse 12V",
    bodyRo: `Selector template «${LETTERS_LED_PSU_SELECTOR_CODE}» → alocare automată pe required_psu_watts → psu_configuration (una sau mai multe unități). Prețul registry e pe bucată SKU — nu se înmulțește cu valoarea W.`,
    bulletsRo: [
      ...LETTERS_LED_PSU_VARIANTS.map(
        (entry) => `Sursă LED 12V ${entry.labelRo} · ${entry.materialCode}`,
      ),
      `Rezervă automată ${LETTERS_LED_PSU_RESERVE_PERCENT}% pe estimated_led_watts`,
      "Dacă required > 200 W: combinație din trepte (ex. [200, 100]) — nu inventăm consum pe job aici",
      "Fără suport comun: sursele se pregătesc în colet (fără task montaj sursă pe suport)",
    ],
  },
  {
    id: "process",
    titleRo: "Procese pe LED",
    bodyRo:
      "Cardul LED ≠ task. Cum obții iluminarea litere: Forex gata → montaj module → cablare/test/PSU → colet. Emblemă exclusă. Detaliu: panoul «Cum obții · ordine taskuri» + lettersStructurePrincipalTaskOrder.ts.",
    bulletsRo: LETTERS_LED_PROCESS_STEPS.map(
      (step, index) => `${index + 1}. ${step.labelRo} — ${step.meaningRo}`,
    ),
  },
  {
    id: "boundary",
    titleRo: "Ce nu este aici",
    bodyRo:
      "Pagină de documentare / afișare a adevărului deja blocat. Nu scrie Product Truth, nu calculează ofertă, nu activează Composer.",
    bulletsRo: [
      "Nu = iluminare emblemă / casetă (densitate pe mp) — tratament separat",
      "Nu = Electrică 220V panou / carcasă ACM",
      "Nu = Capac spate Forex (materialul pe care se montează)",
      "Nu = Finisaj produs (pasul 5)",
      "Nu = redenumire coduri CostEngine / mutare prețuri",
    ],
  },
  {
    id: "direction",
    titleRo: "Direcție în sistem",
    bodyRo: LETTERS_LED_DOC_DIRECTION_RO,
    bulletsRo: [
      "Structură produs rămâne harta 1→5; detaliul LED litere trăiește pe /structure/sistem-led",
      "Pitch litere = 250 mm (Intake V4/V6) — doar perimetru litere",
      "Emblemă: documentare / UI separat (nu pe această pagină)",
      "După Litere UI: ACM separat, apoi contract de compatibilitate + Composer",
    ],
  },
] as const;

/**
 * Calculation cards — letter LED formula + automatic PSU allocation (display documentation).
 * Sources: intake_v4_led_lighting_service (pitch 250), intakeV4LedLighting / psuAllocation,
 * dossier led_module_power_w + light_color, lettersLedMaterialDisplay PSU variants.
 */
export const LETTERS_LED_CALC_CARDS: readonly LettersLedCalcCard[] = [
  {
    id: "module_count",
    importance: 1,
    titleRo: "Formula LED litere",
    subtitleRo: "Doar litere — din perimetru, nu inventată",
    formulaRo: `letter_led_module_count = ceil(perimeter_m × 1000 / ${LETTERS_LED_PITCH_MM})  ·  estimated_led_watts = count × led_module_power_w`,
    stepsRo: [
      "Baza = perimetrul exterior al literelor (ml / m) din job — nu se inventează aici",
      `Pitch module litere = ${LETTERS_LED_PITCH_MM} mm (Intake V4/V6)`,
      `led_module_power_w = ${LETTERS_LED_MODULE_WATTAGE_OPTIONS_W.join(" / ")} W (default ${LETTERS_LED_MODULE_WATTAGE_DEFAULT_W}) — alegere operator`,
      `light_color = ${LETTERS_LED_LIGHT_COLOR_OPTIONS.join(" / ")} (default ${LETTERS_LED_LIGHT_COLOR_DEFAULT}) — nu schimbă formula de count/W`,
      "Standard lighting_system_type = led_modules; led_strip = consum pe ml (altă formulă)",
      "Emblemă: în afara acestei formule — tratament separat",
    ],
    outputsRo: [
      "letter_led_module_count",
      "estimated_led_watts litere (intrare pentru alegerea PSU pe această pagină)",
      "MAT-LED-MODULE — cantitate buc litere",
      "Cost module litere = count × preț registry (€/buc)",
    ],
    notThisRo: [
      "Nu include emblemă / casetă pe densitate mp — separat",
      "Nu inventa pitch 100 mm pe litere — engine = 250 mm",
      "Nu inventa un consum W pe job pe această pagină — doar formula",
      "Nu factura module pe mp față",
    ],
    priceNoteRo:
      "Prețul €/buc pentru MAT-LED-MODULE se citește din Pricing Registry — nu se dublează aici.",
    verifyHref: "/inventory/pricing?code=MAT-LED-MODULE",
    verifyLabelRo: "Verifică preț module",
  },
  {
    id: "psu_selection",
    importance: 1,
    titleRo: "Alegere automată sursă (W)",
    subtitleRo: "Din puterea LED litere → psu_configuration",
    formulaRo: `required_psu_watts = estimated_led_watts_litere × (1 + ${LETTERS_LED_PSU_RESERVE_PERCENT}/100)  →  allocate {60,100,160,200} → psu_configuration[]`,
    stepsRo: [
      "Intrare = estimated_led_watts din formula litere (module sau bandă) — fără emblemă pe această pagină",
      `Rezervă ${LETTERS_LED_PSU_RESERVE_PERCENT}% → required_psu_watts`,
      "Alocare automată pe treptele 60 / 100 / 160 / 200 W (psuAllocation)",
      "Prioritate: mai puține unități → spare mai mic → PSU max mai mare la egalitate",
      "Dacă required > 200 W: mai multe unități în psu_configuration (ex. [200, 100])",
      "SKU pe fiecare unitate: MAT-LED-PSU-12V-{watts}W",
    ],
    outputsRo: [
      "required_psu_watts (din litere)",
      "psu_configuration (array — una sau mai multe surse)",
      "selected_psu_watts (când e o singură treaptă / compat template)",
      "Cost surse = sumă prețuri registry pe fiecare SKU (€/buc) — nu × W",
    ],
    notThisRo: [
      "Nu include consum emblemă în formula acestei pagini — separat",
      "Nu multiplica prețul registry cu valoarea W",
      "Nu confunda cu alimentare 220V carcasă",
      "Nu inventa trepte în afara 60/100/160/200",
      "Nu inventa un consum W pe job pe această pagină — doar regula de alocare",
    ],
    priceNoteRo:
      "Prețurile pe treaptă se citesc din Pricing pe codul SKU — nu din această pagină.",
    verifyHref: "/inventory/pricing?q=MAT-LED-PSU-12V",
    verifyLabelRo: "Verifică prețuri PSU",
  },
] as const;

export const LETTERS_LED_DOC_SOURCES: readonly LettersLedDocSource[] = [
  {
    labelRo: "Schiță literă pe layere — secțiune confecționare (LED în cavitate)",
    path: "docs/worklog/realignment/audit_assets/26_letters_volumetric_section_confectionare.png",
  },
  {
    labelRo: "Taxonomie CNC RO + schițe",
    path: "docs/architecture/CNC_PROCESS_TAXONOMY_RO.md",
  },
  {
    labelRo: "Ordine taskuri principale (display SoT pe carduri)",
    path: "frontend/src/features/product-system/lettersStructurePrincipalTaskOrder.ts",
  },
  {
    labelRo: "LED pitch litere 250 mm + count",
    path: "backend/services/intake_v4_led_lighting_service.py",
  },
  {
    labelRo: "Alocare automată PSU (multi-unit)",
    path: "frontend/src/lib/psuAllocation.ts",
  },
  {
    labelRo: "Intake V4/V6 LED wattage + PSU propose",
    path: "frontend/src/lib/intakeV6/intakeV4LedLighting.ts",
  },
  {
    labelRo: "Dossier — led_module_power_w + light_color",
    path: "backend/seeds/seed_tpl_volumetric_letters_dossier.py",
  },
  {
    labelRo: "Display lock Sistem LED (litere)",
    path: "frontend/src/lib/materials/lettersLedMaterialDisplay.ts",
  },
  {
    labelRo: "Densitate emblemă (referință — nu pe această pagină)",
    path: "docs/architecture/LED_LIGHTING_DENSITY_RULES.md",
  },
  {
    labelRo: "Model pagină (Vizual față)",
    path: "docs/worklog/realignment/2026-07-23_letters_vizual_fata_structure_detail_page_v1.md",
  },
] as const;
