/**
 * Volum aluminiu — explanatory + directional documentation (operator-facing).
 * Sourced from owner locks / RETURN-CANT decisions — display only; no Product Truth write.
 *
 * Canonical markdown mirror:
 * docs/worklog/realignment/2026-07-23_letters_volum_aluminiu_structure_documentation.md
 */

import {
  LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO,
  LETTERS_VOLUME_ALUMINUM_NOT_THESE_CODES,
  LETTERS_VOLUME_ALUMINUM_PROCESS_STEPS,
  LETTERS_VOLUME_ALUMINUM_SELECTOR_CODE,
  LETTERS_VOLUME_ALUMINUM_SELECTOR_DISPLAY_NAME,
  LETTERS_VOLUME_ALUMINUM_THICKNESS_NOTE_RO,
  LETTERS_VOLUME_ALUMINUM_WIDTHS,
} from "@/lib/materials/lettersVolumeAluminumMaterialDisplay";

export type LettersVolumeDocSection = {
  id: string;
  titleRo: string;
  bodyRo: string;
  bulletsRo?: readonly string[];
};

export type LettersVolumeDocSource = {
  labelRo: string;
  path: string;
};

export type LettersVolumeCalcCard = {
  id: "profile_consumption" | "cant_finish";
  importance: 1 | 2;
  titleRo: string;
  subtitleRo: string;
  formulaRo: string;
  stepsRo: readonly string[];
  outputsRo: readonly string[];
  notThisRo: readonly string[];
  priceNoteRo: string;
  /** Pricing Registry deep-link (no hardcoded EUR). */
  verifyHref: string;
  verifyLabelRo: string;
};

/** One-line role in the Letters nucleus. */
export const LETTERS_VOLUME_DOC_ROLE_RO =
  "Pasul 2 din Structură produs (Litere volumetrice): cantul / lateralul din profil aluminiu — lățime 30/60/80/100 mm pe perimetrul autoritar al feței.";

export const LETTERS_VOLUME_DOC_DIRECTION_RO =
  "În sistem: Structură produs = hartă scurtă; această pagină = documentul componentei. Pattern-ul urmează modelul Vizual față. Urmează Capac spate, Sistem LED, Finisaj. Litere se închid UI înainte de contract ACM / Composer.";

export const LETTERS_VOLUME_DOC_SECTIONS: readonly LettersVolumeDocSection[] = [
  {
    id: "role",
    titleRo: `Ce este ${LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO}`,
    bodyRo:
      "Este volumul literei — profilul aluminiu care urmează conturul feței. Consumă perimetrul din Vizual față; nu inventează geometrie. Nu este panou ACM, nu este țeavă de premontaj, nu este profil de casetă.",
    bulletsRo: [
      "Loc în nucleu: după Vizual față, înainte de Capac spate",
      "Dependență upstream: face_perimeter_length_m (autoritar pentru lungimea de cant)",
      "Finish line laborator: cost de producție / EIC — nu ofertă, nu Execution",
    ],
  },
  {
    id: "material",
    titleRo: "Material standard",
    bodyRo: `Familia operatorului este «${LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO}» (${LETTERS_VOLUME_ALUMINUM_THICKNESS_NOTE_RO}). Selectorul de template «${LETTERS_VOLUME_ALUMINUM_SELECTOR_DISPLAY_NAME}» (${LETTERS_VOLUME_ALUMINUM_SELECTOR_CODE}) se rezolvă pe lățime după return_depth_mm.`,
    bulletsRo: [
      ...LETTERS_VOLUME_ALUMINUM_WIDTHS.map(
        (entry) =>
          `${LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO} ${entry.labelRo} · ${entry.materialCode}`,
      ),
      `Nu Volum aluminiu: ${LETTERS_VOLUME_ALUMINUM_NOT_THESE_CODES.join(" · ")}`,
      "Unitate material: ml (perimetru / contur real)",
      "Prețurile pe lățime se verifică în Pricing Registry — nu se dublează aici",
    ],
  },
  {
    id: "process",
    titleRo: "Procese pe volum",
    bodyRo:
      "Cardul Volum ≠ task. Cum obții volumul: prep traseu → (Oracal înainte) → formare → lipire pe față → (RAL după). Detaliu: panoul «Cum obții · ordine taskuri» + lettersStructurePrincipalTaskOrder.ts.",
    bulletsRo: [
      ...LETTERS_VOLUME_ALUMINUM_PROCESS_STEPS.map(
        (step, index) => `${index + 1}. ${step.labelRo} — ${step.meaningRo}`,
      ),
      "Nu sunt badge CNC pe plexi — calea operațională RETURN-CANT",
    ],
  },
  {
    id: "finish",
    titleRo: "Finisaj cant (pe volum)",
    bodyRo:
      "Finisajul cantului aparține RETURN-CANT — nu pasului Finisaj produs și nu Finisaj față. Variante: culoare stock (fără extra pricing), Oracal 651, vopsit RAL.",
    bulletsRo: [
      "Stock (alb / negru / auriu / argintiu) — informație atelier, fără cheie pricing extra",
      "Oracal pe cant — consum pe mp (lățime rolă × lungime folosită); preț serie în registry",
      "RAL pe cant — material €/ml pe lățime + manoperă €/ml (aceleași adâncimi 30/60/80/100)",
      "Nu confunda cu Oracal / print pe Vizual față",
    ],
  },
  {
    id: "boundary",
    titleRo: "Ce nu este aici",
    bodyRo:
      "Pagină de documentare / afișare a adevărului deja blocat. Nu scrie Product Truth, nu calculează ofertă, nu activează Composer.",
    bulletsRo: [
      "Nu = panou ACM / Dibond / Bond",
      "Nu = MAT-PREMOUNT-BAR-ALUMINUM (țeavă premontaj)",
      "Nu = MAT-PROFIL-ALU-BOX (profil casetă)",
      "Nu = Capac spate Forex · Sistem LED · Finisaj produs (pașii 3–5)",
      "Nu = redenumire coduri CostEngine / mutare prețuri",
    ],
  },
  {
    id: "direction",
    titleRo: "Direcție în sistem",
    bodyRo: LETTERS_VOLUME_DOC_DIRECTION_RO,
    bulletsRo: [
      "Structură produs rămâne harta 1→5; detaliul trăiește pe /structure/<pas>",
      "Perimetrul rămâne ownership FACE; Volum consumă, nu redefinește",
      "După Litere UI: ACM separat, apoi contract de compatibilitate + Composer",
    ],
  },
] as const;

/**
 * Calculation cards — owner-locked method (display documentation).
 * Sources: face_component_truth_owner_decision_v1 §D (perimeter),
 * return_cant_owner_answers_pending (#7–8, #12, #15–17),
 * RETURN_CANT_PRICING_KEYS_ALIGNMENT_PLAN §5,
 * RETURN_CANT_INTAKE audit (quantity_ml = face perimeter).
 */
export const LETTERS_VOLUME_CALC_CARDS: readonly LettersVolumeCalcCard[] = [
  {
    id: "profile_consumption",
    importance: 1,
    titleRo: "Consum profil",
    subtitleRo: "Cât aluminiu (ml) pe lucrare",
    formulaRo: "quantity_ml = face_perimeter_length_m",
    stepsRo: [
      "Baza = perimetrul / conturul real al feței (din Vizual față)",
      "Volum aluminiu consumă acest ml — nu inventează perimetru",
      "SKU material = MAT-PROFIL-LATERAL-LITERE-{30|60|80|100}MM după return_depth_mm",
      "Același profil Al 0.6 mm pe toate lățimile standard",
    ],
    outputsRo: [
      "return_cant.quantity_ml — lungime cant",
      "material_code — SKU pe lățime",
      "Cost profil = quantity_ml × preț registry (€/ml)",
    ],
    notThisRo: [
      "Nu se măsoară pe mp bounding box",
      "Nu se folosește perimetru inventat local pe cant",
      "Nu confunda cu ACM / premontaj / casetă",
    ],
    priceNoteRo:
      "Prețul €/ml diferă pe lățime — se citește din Pricing Registry pe codul SKU, nu din această pagină.",
    verifyHref: "/inventory/pricing?q=MAT-PROFIL-LATERAL-LITERE",
    verifyLabelRo: "Verifică prețuri profil",
  },
  {
    id: "cant_finish",
    importance: 1,
    titleRo: "Finisaj cant",
    subtitleRo: "Extra cost doar dacă Oracal sau RAL",
    formulaRo: "Oracal: mp = lățime_rolă × lungime · RAL: ml × tarif pe lățime",
    stepsRo: [
      "Stock color — fără cheie pricing extra (doar info atelier)",
      "Oracal pe cant — consum pe mp (lățime rolă 100/126 cm × lungime folosită), nu simplu pe ml",
      "Aplicare Oracal — manoperă pe ml (registry labor), înainte de formare",
      "RAL — material pe ml (SKU pe lățime) + manoperă pe ml, după lipirea pe față",
    ],
    outputsRo: [
      "finish.variant — stock | vinyl | paint",
      "Chei material Oracal / RAL în Pricing Registry",
      "Labor: RETURN_CANT_VINYL_APPLICATION_LABOR · RETURN_CANT_RAL_PAINT_LABOR",
    ],
    notThisRo: [
      "Nu factura Oracal cant ca €/ml material",
      "Nu muta RAL cant în Finisaj față sau Finisaj produs",
      "Nu inventa prețuri în Product System Lab UI",
    ],
    priceNoteRo:
      "Valorile €/mp și €/ml se citesc din Pricing — aici rămâne doar metoda.",
    verifyHref: "/inventory/pricing?q=ORACAL",
    verifyLabelRo: "Verifică finisaj cant",
  },
] as const;

export const LETTERS_VOLUME_DOC_SOURCES: readonly LettersVolumeDocSource[] = [
  {
    labelRo: "Schiță literă pe layere — secțiune confecționare",
    path: "docs/worklog/realignment/audit_assets/26_letters_volumetric_section_confectionare.png",
  },
  {
    labelRo: "Taxonomie CNC RO + schițe (Canal/Șanfren ≠ V-groove)",
    path: "docs/architecture/CNC_PROCESS_TAXONOMY_RO.md",
  },
  {
    labelRo: "Ordine taskuri principale (display SoT pe carduri)",
    path: "frontend/src/features/product-system/lettersStructurePrincipalTaskOrder.ts",
  },
  {
    labelRo: "FACE perimeter → RETURN-CANT",
    path: "docs/worklog/owner-input/face_component_truth_owner_decision_v1.md",
  },
  {
    labelRo: "RETURN-CANT owner answers (ml, depths, Oracal/RAL)",
    path: "docs/worklog/owner-input/return_cant_owner_answers_pending.md",
  },
  {
    labelRo: "RETURN-CANT pricing keys alignment",
    path: "docs/architecture/product-system/RETURN_CANT_PRICING_KEYS_ALIGNMENT_PLAN.md",
  },
  {
    labelRo: "Display lock Volum aluminiu",
    path: "docs/worklog/realignment/2026-07-23_letters_volume_aluminum_display_lock.md",
  },
  {
    labelRo: "Variation semantics / pricing boundary",
    path: "docs/architecture/product-system/RETURN_CANT_VARIATION_SEMANTICS_AND_PRICING_BOUNDARY.md",
  },
  {
    labelRo: "Model pagină (Vizual față)",
    path: "docs/worklog/realignment/2026-07-23_letters_vizual_fata_structure_detail_page_v1.md",
  },
] as const;
