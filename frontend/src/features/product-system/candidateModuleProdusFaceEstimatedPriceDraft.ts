/**
 * FACE estimated material / CNC price draft — readonly workshop only.
 * Authority: OWNER_ESTIMATE_DRAFT — not Pricing Registry, not active pricing.
 * Source: owner conversation 2026-07-09 + face_component_truth_owner_decision_v1.md
 * 3 mm material aligned to face_price_registry_alignment_owner_decision_v1.md (MAT-ACP-FATA-LITERE = 16 EUR/mp) — still readonly draft, not active pricing.
 */

export const FACE_ESTIMATE_DRAFT_AUTHORITY = {
  label: "OWNER_ESTIMATE_DRAFT",
  notPricingRegistryAuthority: true,
  notActivePricing: true,
  editableByOwner: true,
  pricingRegistryWrite: false as const,
  pricingActive: false as const,
} as const;

export type FaceEstimateDraftStatus = "owner_estimate_draft";

export type FaceEstimateDraftCategory =
  | "face_material"
  | "face_cnc_cutting"
  | "face_cnc_minimum_policy"
  | "inventory_cross_reference";

export type FaceEstimateDraftEntry = {
  key: string;
  labelRo: string;
  category: FaceEstimateDraftCategory;
  status: FaceEstimateDraftStatus;
  materialFamily: string;
  thicknessMm: number | null;
  process: string | null;
  estimateValue: number;
  unit: "mp" | "ml" | "lei" | "none";
  faceStandard: boolean;
  notesRo: string;
  pricingActive: false;
  mustNotWritePricingRegistry: true;
};

export type FaceInventoryCrossReference = {
  key: string;
  pricingKey: string | null;
  materialFamily: string;
  thicknessMm: number | null;
  registryRoute: "/inventory/pricing";
  registryAuthority: false;
  draftAuthority: typeof FACE_ESTIMATE_DRAFT_AUTHORITY.label;
  notesRo: string;
};

export const FACE_ESTIMATE_CALCULATION_RULES: readonly string[] = [
  "Material FACE = bounding/out-of-box per piece × pret material EUR/mp",
  "Debitare CNC FACE = face_perimeter_length_m × pret CNC EUR/ml contur",
  "Minim CNC = daca debitarea calculata < 50 lei, se aplica minim 50 lei / lucrare",
  "Nu arie vectoriala exacta pentru material FACE",
  "Gaurile = negative holes, nu piese separate nesting",
] as const;

export const FACE_MATERIAL_ESTIMATE_DRAFTS: readonly FaceEstimateDraftEntry[] = [
  {
    key: "plexiglas_3mm_material",
    labelRo: "plexiglas 3mm PMMA - opal",
    category: "face_material",
    status: "owner_estimate_draft",
    materialFamily: "Plexiglas / acrylic",
    thicknessMm: 3,
    process: null,
    estimateValue: 16,
    unit: "mp",
    faceStandard: true,
    notesRo:
      "Linie standard FACE (display lock). Aliniat la MAT-ACP-FATA-LITERE (16 EUR/mp) — owner draft readonly, nu Pricing Registry authority.",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
  },
  {
    key: "plexiglas_5mm_material",
    labelRo: "Plexiglas / acrylic 5 mm — material față",
    category: "face_material",
    status: "owner_estimate_draft",
    materialFamily: "Plexiglas / acrylic",
    thicknessMm: 5,
    process: null,
    estimateValue: 25,
    unit: "mp",
    faceStandard: false,
    notesRo: "Opțional — confirmare owner per job înainte de pricing.",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
  },
  {
    key: "plexiglas_10mm_material",
    labelRo: "Plexiglas / acrylic 10 mm — material față",
    category: "face_material",
    status: "owner_estimate_draft",
    materialFamily: "Plexiglas / acrylic",
    thicknessMm: 10,
    process: null,
    estimateValue: 50,
    unit: "mp",
    faceStandard: false,
    notesRo: "Opțional / caz special — confirmare owner per job.",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
  },
] as const;

export const FACE_CNC_CUTTING_ESTIMATE_DRAFTS: readonly FaceEstimateDraftEntry[] = [
  {
    key: "plexiglas_3mm_cnc",
    labelRo: "Debitare CNC FACE — plexiglas 3mm PMMA - opal",
    category: "face_cnc_cutting",
    status: "owner_estimate_draft",
    materialFamily: "Plexiglas / acrylic",
    thicknessMm: 3,
    process: "CNC router",
    estimateValue: 1.0,
    unit: "ml",
    faceStandard: true,
    notesRo: "Pret pe ml contur — standard.",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
  },
  {
    key: "plexiglas_5mm_cnc",
    labelRo: "Debitare CNC FACE — Plexiglas 5 mm",
    category: "face_cnc_cutting",
    status: "owner_estimate_draft",
    materialFamily: "Plexiglas / acrylic",
    thicknessMm: 5,
    process: "CNC router",
    estimateValue: 1.5,
    unit: "ml",
    faceStandard: false,
    notesRo: "Opțional — ml contur.",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
  },
  {
    key: "plexiglas_10mm_cnc",
    labelRo: "Debitare CNC FACE — Plexiglas 10 mm",
    category: "face_cnc_cutting",
    status: "owner_estimate_draft",
    materialFamily: "Plexiglas / acrylic",
    thicknessMm: 10,
    process: "CNC router",
    estimateValue: 2.5,
    unit: "ml",
    faceStandard: false,
    notesRo: "Opțional / mai lent — ml contur.",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
  },
] as const;

export const FACE_CNC_MINIMUM_POLICY_DRAFT = {
  key: "face_cnc_minimum_per_job",
  labelRo: "Minim debitare CNC FACE / lucrare",
  status: "owner_estimate_draft" as const,
  estimateValueLei: 50,
  setupIncludedInMinimum: true,
  policySource: "owner_commercial_policy" as const,
  notPricingRegistry: true,
  pricingActive: false as const,
  notesRo:
    "Regulă comercială atelier în lei — similar RAL minimum. Dacă debitarea calculată depășește minimul, se aplică ml contur.",
} as const;

/** Readonly cross-reference — registry may differ; draft is not authority. */
export const FACE_INVENTORY_PRICING_CROSS_REFERENCES: readonly FaceInventoryCrossReference[] = [
  {
    key: "plexiglas_3mm_registry_key",
    pricingKey: "MAT-ACP-FATA-LITERE",
    materialFamily: "Plexiglas / acrylic",
    thicknessMm: 3,
    registryRoute: "/inventory/pricing",
    registryAuthority: false,
    draftAuthority: FACE_ESTIMATE_DRAFT_AUTHORITY.label,
    notesRo:
      "Intake V4 map plexiglas_face → MAT-ACP-FATA-LITERE. Aliniat la registry authority 16 EUR/mp — draft readonly, fără write, fără activare.",
  },
  {
    key: "plexiglas_5mm_registry_key",
    pricingKey: null,
    materialFamily: "Plexiglas / acrylic",
    thicknessMm: 5,
    registryRoute: "/inventory/pricing",
    registryAuthority: false,
    draftAuthority: FACE_ESTIMATE_DRAFT_AUTHORITY.label,
    notesRo: "Cheie registry neconfirmată — doar draft owner.",
  },
  {
    key: "plexiglas_10mm_registry_key",
    pricingKey: null,
    materialFamily: "Plexiglas / acrylic",
    thicknessMm: 10,
    registryRoute: "/inventory/pricing",
    registryAuthority: false,
    draftAuthority: FACE_ESTIMATE_DRAFT_AUTHORITY.label,
    notesRo: "Cheie registry neconfirmată — doar draft owner.",
  },
] as const;

export type FaceEstimateDraftSummary = {
  authority: typeof FACE_ESTIMATE_DRAFT_AUTHORITY;
  readyForPricing: false;
  pricingActiveCount: 0;
  materialDraftCount: number;
  cncDraftCount: number;
  minimumPolicyLei: number;
  crossReferenceCount: number;
};

export function buildFaceEstimateDraftSummary(): FaceEstimateDraftSummary {
  return {
    authority: FACE_ESTIMATE_DRAFT_AUTHORITY,
    readyForPricing: false,
    pricingActiveCount: 0,
    materialDraftCount: FACE_MATERIAL_ESTIMATE_DRAFTS.length,
    cncDraftCount: FACE_CNC_CUTTING_ESTIMATE_DRAFTS.length,
    minimumPolicyLei: FACE_CNC_MINIMUM_POLICY_DRAFT.estimateValueLei,
    crossReferenceCount: FACE_INVENTORY_PRICING_CROSS_REFERENCES.length,
  };
}

export function formatFaceEstimateDraftValue(entry: FaceEstimateDraftEntry): string {
  if (entry.unit === "mp") return `${entry.estimateValue.toFixed(2)} EUR/mp`;
  if (entry.unit === "ml") return `${entry.estimateValue.toFixed(2)} EUR/ml contur`;
  if (entry.unit === "lei") return `${entry.estimateValue.toFixed(0)} lei`;
  return String(entry.estimateValue);
}

export function getFaceEstimateDraftByKey(key: string): FaceEstimateDraftEntry | null {
  return (
    [...FACE_MATERIAL_ESTIMATE_DRAFTS, ...FACE_CNC_CUTTING_ESTIMATE_DRAFTS].find(
      (entry) => entry.key === key,
    ) ?? null
  );
}

export const FACE_ESTIMATE_DRAFT_SUMMARY = buildFaceEstimateDraftSummary();
