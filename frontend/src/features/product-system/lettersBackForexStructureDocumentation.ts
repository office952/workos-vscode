/**
 * Capac spate — explanatory + directional documentation (operator-facing).
 * Sourced from owner locks / FACE-BACK prep contract — display only; no Product Truth write.
 *
 * Canonical markdown mirror:
 * docs/worklog/realignment/2026-07-23_letters_capac_spate_structure_documentation.md
 */

import {
  LETTERS_BACK_FOREX_10MM_DISPLAY_NAME,
  LETTERS_BACK_FOREX_10MM_REGISTRY_CODE,
  LETTERS_BACK_FOREX_MEANING_RO,
  LETTERS_BACK_FOREX_PROCESS_STEPS,
} from "@/lib/materials/lettersBackForexMaterialDisplay";

export type LettersBackDocSection = {
  id: string;
  titleRo: string;
  bodyRo: string;
  bulletsRo?: readonly string[];
};

export type LettersBackDocSource = {
  labelRo: string;
  path: string;
};

export type LettersBackCalcCard = {
  id: "material_consumption" | "cnc_cutting";
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

/** One-line role in the Letters nucleus. */
export const LETTERS_BACK_DOC_ROLE_RO =
  "Pasul 3 din Structură produs (Litere volumetrice): capacul spate din Forex 10 mm — material + debitare CNC; șanfren opțional (default owner: fără).";

export const LETTERS_BACK_DOC_DIRECTION_RO =
  "În sistem: Structură produs = hartă scurtă; această pagină = documentul componentei. Pattern-ul urmează modelul Vizual față / Volum aluminiu. Urmează Sistem LED, Finisaj. Litere se închid UI înainte de contract ACM / Composer.";

export const LETTERS_BACK_DOC_SECTIONS: readonly LettersBackDocSection[] = [
  {
    id: "role",
    titleRo: "Ce este Capac spate",
    bodyRo: LETTERS_BACK_FOREX_MEANING_RO,
    bulletsRo: [
      "Loc în nucleu: după Volum aluminiu, înainte de Sistem LED",
      "Suport pentru montaj LED pe spate Forex",
      "Finish line laborator: cost de producție / EIC — nu ofertă, nu Execution",
    ],
  },
  {
    id: "material",
    titleRo: "Material standard",
    bodyRo: `Stocul operatorului pentru spate este «${LETTERS_BACK_FOREX_10MM_DISPLAY_NAME}». Codul de registry rămâne ${LETTERS_BACK_FOREX_10MM_REGISTRY_CODE} (legacy „PVC” în cod — material = Forex / PVC expandat 10 mm).`,
    bulletsRo: [
      "Grosime standard: 10 mm",
      "Unitate material: mp",
      "Nu Capac spate: panou ACM / Bond / Dibond",
      "Nu Capac spate: șablon montaj 3 mm (alt rol)",
      "Prețul €/mp se verifică în Pricing Registry — nu se dublează aici",
    ],
  },
  {
    id: "process",
    titleRo: "Prelucrare CNC pe Forex",
    bodyRo:
      "Cardul Spate ≠ task. Cum obții Forex: aceeași prep vector + fișier CNC ca fața, apoi debitare Forex. Badge-ul BADGE-CNC-PROCESSABLE rămâne pe față plexi + CNC 4020 — nu se extinde pe Forex.",
    bulletsRo: [
      "Vezi panoul «Cum obții · ordine taskuri» / lettersStructurePrincipalTaskOrder.ts",
      ...LETTERS_BACK_FOREX_PROCESS_STEPS.map(
        (step, index) =>
          `${index + 1}. ${step.labelRo}${step.required ? " — obligatoriu" : " — opțional (owner default: fără)"} · ${step.meaningRo}`,
      ),
    ],
  },
  {
    id: "geometry",
    titleRo: "Geometrie: arie vs perimetru",
    bodyRo:
      "Materialul (mp) și debitarea CNC (ml) au surse diferite. Nu se înlocuiește perimetrul vectorial CNC cu bbox sau nesting.",
    bulletsRo: [
      "Material: backing_area_m2 / back_area_m2 — fallback față→spate permis doar pentru mp",
      "CNC: backing_cnc_cutting_perimeter_ml / back_cutting_perimeter_ml — perimetru vectorial",
      "Șanfren (dacă e activ): folosește același perimetru vectorial; default owner = fără",
      "Fără perimetru vectorial → status manual_required — nu inventa cost din bbox",
    ],
  },
  {
    id: "boundary",
    titleRo: "Ce nu este aici",
    bodyRo:
      "Pagină de documentare / afișare a adevărului deja blocat. Nu scrie Product Truth, nu calculează ofertă, nu activează Composer.",
    bulletsRo: [
      "Nu = panou ACM / Dibond",
      "Nu = șablon montaj 3 mm",
      "Nu = Vizual față plexi · Volum aluminiu · Sistem LED · Finisaj produs",
      "Nu = badge CNC processable pe Forex",
      "Nu = redenumire coduri CostEngine / mutare prețuri",
    ],
  },
  {
    id: "direction",
    titleRo: "Direcție în sistem",
    bodyRo: LETTERS_BACK_DOC_DIRECTION_RO,
    bulletsRo: [
      "Structură produs rămâne harta 1→5; detaliul trăiește pe /structure/<pas>",
      "LED urmează pe acest suport Forex — fără a confunda pasul LED cu materialul spate",
      "După Litere UI: ACM separat, apoi contract de compatibilitate + Composer",
    ],
  },
] as const;

/**
 * Calculation cards — owner/prep-contract method (display documentation).
 * Sources: TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CONTRACT §8–9,
 * lettersBackForexMaterialDisplay, intake backing modes.
 */
export const LETTERS_BACK_CALC_CARDS: readonly LettersBackCalcCard[] = [
  {
    id: "material_consumption",
    importance: 1,
    titleRo: "Consum material",
    subtitleRo: "Cât Forex (mp) pe lucrare",
    formulaRo: "consum mp = backing_area_m2 (sau fallback față→spate pentru mp)",
    stepsRo: [
      "Suprafața de material spate = aria pieselor / nesting pe Forex",
      "Fallback față→spate e permis doar pentru mp material — nu pentru CNC",
      "SKU = MAT-SPATE-PVC-LITERE (Forex 10 mm)",
      "Cost material = consum mp × preț registry (€/mp)",
    ],
    outputsRo: [
      "backing_area_m2 / back_area_m2 — consum mp",
      "material_code — MAT-SPATE-PVC-LITERE",
    ],
    notThisRo: [
      "Nu confunda aria material cu perimetrul CNC",
      "Nu panou ACM ca spate litere",
      "Nu șablon montaj 3 mm",
    ],
    priceNoteRo:
      "Prețul €/mp se citește din Pricing Registry pe MAT-SPATE-PVC-LITERE — nu se dublează aici.",
    verifyHref: "/inventory/pricing?code=MAT-SPATE-PVC-LITERE",
    verifyLabelRo: "Verifică preț material",
  },
  {
    id: "cnc_cutting",
    importance: 1,
    titleRo: "Debitare CNC spate",
    subtitleRo: "Perimetru × 3 sau 5 treceri (Forex 10 mm)",
    formulaRo:
      "cost CNC spate = back_cutting_perimeter_ml × (3 sau 5) treceri × tarif CNC (€/ml/trecere)",
    stepsRo: [
      "Baza = perimetrul vectorial al traseului CNC spate (ml) — nu bbox",
      "Fără șanfren (default owner): 3 treceri = ceil(10 mm / 3.5 mm) debitare",
      "Cu șanfren: 5 treceri = 3 debitare + 2 șanfren (adâncime ~7 mm)",
      "Debitare CNC Forex — obligatoriu (back_cut); șanfren — opțional",
      "Chei: backing_cnc_cutting_perimeter_ml / back_cutting_perimeter_ml",
    ],
    outputsRo: [
      "back_cut — operație debitare spate",
      "back_bevel_enabled — gate șanfren (default false → 3 treceri; true → 5)",
      "Debitare pe ml contur × treceri — nu pe mp material",
    ],
    notThisRo: [
      "Nu bbox / nesting perimeter pentru CNC",
      "Nu inventa cost dacă lipsește perimetrul vectorial",
      "Nu aplica BADGE-CNC-PROCESSABLE pe Forex",
      "Nu confunda 3/5 treceri CNC cu consumul mp de Forex",
    ],
    priceNoteRo:
      "Tariful €/ml/trecere se citește din Pricing / politică owner — nu se dublează aici.",
    verifyHref: "/inventory/pricing",
    verifyLabelRo: "Verifică tarif CNC",
  },
] as const;

export const LETTERS_BACK_DOC_SOURCES: readonly LettersBackDocSource[] = [
  {
    labelRo: "Schiță literă pe layere — secțiune confecționare",
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
    labelRo: "FACE-BACK prep — Forex 3/5 treceri CNC",
    path: "docs/architecture/TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CONTRACT.md",
  },
  {
    labelRo: "CNC pass policy — Forex 3 sau 5",
    path: "backend/services/intake_v4_cnc_router_pass_policy_service.py",
  },
  {
    labelRo: "FACE Component Truth — Forex nu e FACE",
    path: "docs/worklog/owner-input/face_component_truth_owner_decision_v1.md",
  },
  {
    labelRo: "Canonical naming Forex 10 mm",
    path: "backend/seeds/material_canonical_naming.py",
  },
  {
    labelRo: "Display lock Capac spate (material + procese)",
    path: "frontend/src/lib/materials/lettersBackForexMaterialDisplay.ts",
  },
  {
    labelRo: "Model pagină (Vizual față / Volum)",
    path: "docs/worklog/realignment/2026-07-23_letters_vizual_fata_structure_detail_page_v1.md",
  },
] as const;
