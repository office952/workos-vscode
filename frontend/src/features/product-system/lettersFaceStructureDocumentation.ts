/**
 * Vizual față — explanatory + directional documentation (operator-facing).
 * Sourced from owner locks / decisions — display only; no Product Truth write.
 *
 * Canonical markdown mirror:
 * docs/worklog/realignment/2026-07-23_letters_vizual_fata_structure_documentation.md
 */

import {
  CNC_PROCESSABLE_BADGE_CODE,
  CNC_PROCESSABLE_BADGE_LABEL,
  CNC_PROCESSABLE_LETTER_FACE_SERVICES,
  CNC_PROCESSABLE_MACHINE_CODES,
} from "@/lib/cnc/cncProcessableBadge";
import {
  LETTERS_FACE_FINISH_MATERIALS,
} from "@/lib/materials/lettersFaceFinishMaterialDisplay";
import {
  LETTERS_FACE_FINISH_LABOR_STEPS,
  LETTERS_FACE_FINISH_SECTION_LABEL_RO,
} from "@/lib/materials/lettersAutocolantDisplay";
import {
  LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME,
  LETTERS_FACE_PLEXI_3MM_OPAL_REGISTRY_CODE,
} from "@/lib/materials/lettersFacePlexiMaterialDisplay";

export type LettersFaceDocSection = {
  id: string;
  titleRo: string;
  bodyRo: string;
  bulletsRo?: readonly string[];
};

export type LettersFaceDocSource = {
  labelRo: string;
  path: string;
};

export type LettersFaceCalcCard = {
  id: "material_consumption" | "cnc_cutting";
  /** Visual weight hint for UI (1 = primary band). */
  importance: 1 | 2;
  titleRo: string;
  subtitleRo: string;
  formulaRo: string;
  stepsRo: readonly string[];
  outputsRo: readonly string[];
  notThisRo: readonly string[];
  priceNoteRo: string;
  verifyMaterialCode?: string;
};

/** One-line role in the Letters nucleus. */
export const LETTERS_FACE_DOC_ROLE_RO =
  "Pasul 1 din Structură produs (Litere volumetrice): substratul vizibil al literei — material + prelucrare CNC + finisaj față după asamblare.";

export const LETTERS_FACE_DOC_DIRECTION_RO =
  "În sistem: Structură produs = hartă scurtă; această pagină = documentul componentei. Același pattern urmează pentru Volum aluminiu, Capac spate, Sistem LED, Finisaj. Litere se închid UI înainte de contract ACM / Composer.";

export const LETTERS_FACE_DOC_SECTIONS: readonly LettersFaceDocSection[] = [
  {
    id: "role",
    titleRo: "Ce este Vizual față",
    bodyRo:
      "Este fața literei volumetrice — placa din care se citește forma. Conturul ei autorizează lungimea de cant (Volum aluminiu). Nu este panou ACM, nu este spate Forex, nu este finisajul de asamblare al produsului.",
    bulletsRo: [
      "Loc în nucleu: după alegerea Product Template Litere, înainte de Volum aluminiu",
      "Consumator downstream: Volum aluminiu (perimetru), Finisaj față (suprafață mp)",
      "Finish line laborator: cost de producție / EIC — nu ofertă, nu Execution",
    ],
  },
  {
    id: "material",
    titleRo: "Material standard",
    bodyRo: `Stocul operatorului pentru față este «${LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME}». Codul de registry rămâne ${LETTERS_FACE_PLEXI_3MM_OPAL_REGISTRY_CODE} (legacy „ACP” în cod — nu panou ACM/Bond).`,
    bulletsRo: [
      "Familie permisă FACE standard: plexiglas / acrylic",
      "Grosime standard: 3 mm opal; 5 mm / 10 mm = opțiuni speciale (confirmare owner înainte de pricing)",
      "Nu FACE standard: Forex, ACM / Bond / Dibond",
      "Nesting material: bounding / out-of-box pe piesă — nu aria vectorială brută",
    ],
  },
  {
    id: "cnc",
    titleRo: "Prelucrare CNC",
    bodyRo: `Badge-ul «${CNC_PROCESSABLE_BADGE_LABEL}» (${CNC_PROCESSABLE_BADGE_CODE}) marchează capacitatea: același identificator pe materialul de față și pe utilajul CNC 4020 (${CNC_PROCESSABLE_MACHINE_CODES[0]}). Nu se lipește pe Forex, pe panou ACM sau pe orice alt CNC generic.`,
    bulletsRo: [
      "Cum obții fața (taskuri, nu card): prep vector → fișier CNC (ArtCAM/DWG) → Decupare CNC față — vezi panoul «Cum obții · ordine taskuri»",
      `1. ${CNC_PROCESSABLE_LETTER_FACE_SERVICES[0]} — contur față pe CNC router (obligatoriu pe calea standard)`,
      `2. ${CNC_PROCESSABLE_LETTER_FACE_SERVICES[1]} — pe margine/suprafață pentru lipirea volumului (≠ V-groove Dibond)`,
      "Finisajele Oracal / print nu sunt procese CNC pe plexi — task târziu după asamblare",
      "Sursa ordine: lettersStructurePrincipalTaskOrder.ts (card ≠ task)",
    ],
  },
  {
    id: "finish",
    titleRo: LETTERS_FACE_FINISH_SECTION_LABEL_RO,
    bodyRo:
      "Opțiunile de finisaj pe față sunt FINISH după asamblare — nu badge de capacitate CNC și nu pas separat în structură. Identitatea = etichetă + cod MAT-*.",
    bulletsRo: [
      ...LETTERS_FACE_FINISH_MATERIALS.map(
        (entry) => `${entry.labelRo} · ${entry.materialCode}`,
      ),
      `Manoperă comună: ${LETTERS_FACE_FINISH_LABOR_STEPS.map((step) => step.labelRo).join(" · ")}`,
      "Prețurile materialelor se verifică în Pricing Registry — nu se dublează aici",
      "Vizual față nu „deține” vopsirea cantului, RAL sau prețurile comerciale",
    ],
  },
  {
    id: "boundary",
    titleRo: "Ce nu este aici",
    bodyRo:
      "Pagină de documentare / afișare a adevărului deja blocat. Nu scrie Product Truth, nu calculează ofertă, nu activează Composer.",
    bulletsRo: [
      "Nu = panou ACM / Dibond (alt Product Template + contract ulterior)",
      "Nu = Capac spate Forex 10 mm",
      "Nu = Finisaj produs (asamblare / QC) — pasul 5 din structură",
      "Nu = redenumire coduri CostEngine / mutare prețuri",
    ],
  },
  {
    id: "direction",
    titleRo: "Direcție în sistem",
    bodyRo: LETTERS_FACE_DOC_DIRECTION_RO,
    bulletsRo: [
      "Structură produs rămâne harta 1→5; detaliul trăiește pe /structure/<pas>",
      "După Litere UI: ACM separat, apoi contract de compatibilitate + Composer",
      "Sursele desktop (SVG/DXF) observă; operatorul confirmă — fără confirmare silențioasă",
    ],
  },
] as const;

/**
 * Calculation cards — owner-locked method (display documentation).
 * Sources: face_component_truth_owner_decision_v1 §C–F,
 * face_estimated_price_draft_v1, face_price_registry_alignment_owner_decision_v1 §4.
 */
export const LETTERS_FACE_CALC_CARDS: readonly LettersFaceCalcCard[] = [
  {
    id: "material_consumption",
    importance: 1,
    titleRo: "Consum material",
    subtitleRo: "Cât plexi se consumă pe lucrare",
    formulaRo: "consum mp = sumă (bounding / out-of-box pe piesă)",
    stepsRo: [
      "Fiecare literă / piesă → cutie de încadrare (bounding box)",
      "Suprafața de material = aria cutiei, nu aria vectorială exactă",
      "Găurile interioare = negative holes — nu piese separate de nesting",
      "Total = face_material_usage_area_m2 (din piece boxes)",
    ],
    outputsRo: [
      "face_piece_boxes — nesting / material",
      "face_material_usage_area_m2 — consum mp",
      "mp_face_area — bază cantitate pentru Finisaj față (vinyl / print)",
    ],
    notThisRo: [
      "Nu arie vectorială brută a path-ului",
      "Nu confunda cu aria de finisaj Oracal fără waste separat",
    ],
    priceNoteRo: "Cost material = consum mp × preț registry (€/mp).",
    verifyMaterialCode: LETTERS_FACE_PLEXI_3MM_OPAL_REGISTRY_CODE,
  },
  {
    id: "cnc_cutting",
    importance: 1,
    titleRo: "Decupare CNC",
    subtitleRo: "Perimetru × 2 treceri (plexi 3 mm) = Decupare + Canal/Șanfren",
    formulaRo:
      "cost CNC față = face_perimeter_length_m × 2 treceri × tarif CNC (€/ml/trecere)",
    stepsRo: [
      "Baza = perimetrul / conturul real al feței (ml)",
      "Treceri CNC plexi 3 mm (default): 2 = 1 Decupare contur + 1 Canal/Șanfren",
      "Canal/Șanfren pe același traseu — pentru lipirea volumului (≠ V-groove Dibond)",
      "Cheie operațională: face_cnc_cutting_perimeter / cnc_face_cutting_plexiglas_3mm",
    ],
    outputsRo: [
      "face_perimeter_length_m — autoritar și pentru Volum aluminiu (cant)",
      "pass_count față = 2 (Decupare 1 + Canal/Șanfren 1)",
      "Decupare pe ml contur × treceri — nu pe mp material",
    ],
    notThisRo: [
      "Nu se facturează decuparea pe aria bounding box",
      "Nu confunda cele 2 treceri CNC cu consumul mp de plexi",
      "Nu = V-groove (îndoire Dibond/ACM)",
    ],
    priceNoteRo:
      "Tariful €/ml/trecere se citește din Pricing / politică owner — nu se dublează aici.",
  },
] as const;

export const LETTERS_FACE_DOC_SOURCES: readonly LettersFaceDocSource[] = [
  {
    labelRo: "Taxonomie CNC RO + schițe Canal/Șanfren (secțiune litere)",
    path: "docs/architecture/CNC_PROCESS_TAXONOMY_RO.md",
  },
  {
    labelRo: "Schiță Canal/Șanfren — suprafață vs margine",
    path: "docs/worklog/realignment/audit_assets/25_letters_canal_sanfren_section.png",
  },
  {
    labelRo: "Schiță literă pe layere — secțiune confecționare",
    path: "docs/worklog/realignment/audit_assets/26_letters_volumetric_section_confectionare.png",
  },
  {
    labelRo: "Ordine taskuri principale (display SoT pe carduri)",
    path: "frontend/src/features/product-system/lettersStructurePrincipalTaskOrder.ts",
  },
  {
    labelRo: "FACE Component Truth — Owner Decision v1",
    path: "docs/worklog/owner-input/face_component_truth_owner_decision_v1.md",
  },
  {
    labelRo: "FACE estimated price draft — reguli calcul",
    path: "docs/worklog/owner-input/face_estimated_price_draft_v1.md",
  },
  {
    labelRo: "FACE price registry alignment — model comercial vs intern",
    path: "docs/worklog/owner-input/face_price_registry_alignment_owner_decision_v1.md",
  },
  {
    labelRo: "Display lock plexiglas 3mm PMMA - opal",
    path: "docs/worklog/realignment/2026-07-23_letters_face_plexi_display_name_lock.md",
  },
  {
    labelRo: "CNC processable badge",
    path: "docs/worklog/realignment/2026-07-23_cnc_processable_badge_identifier.md",
  },
  {
    labelRo: "CNC pass policy — față 2 treceri",
    path: "backend/services/intake_v4_cnc_router_pass_policy_service.py",
  },
  {
    labelRo: "Finisaj față — meaning",
    path: "docs/worklog/realignment/2026-07-23_letters_face_finish_meaning.md",
  },
  {
    labelRo: "Litere × ACM — direcție (blocat până UI Litere)",
    path: "docs/worklog/realignment/decision__letters_acm_compatibility_composer_direction_v1.md",
  },
] as const;
