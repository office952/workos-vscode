/**
 * FINISH estimated price draft — readonly workshop only.
 * Authority: EVIDENCE_DRAFT_READONLY — not Pricing Registry, not active pricing.
 * Source: finish_component_truth_owner_decision_v1.md + seed evidence cross-ref only.
 * Values from seeds are evidence_only — not owner-confirmed FINISH pricing authority.
 */

export const FINISH_ESTIMATE_DRAFT_AUTHORITY = {
  label: "EVIDENCE_DRAFT_READONLY",
  notPricingRegistryAuthority: true,
  notActivePricing: true,
  estimatedPriceDraftOnly: true,
  pricingRegistryWrite: false as const,
  pricingActive: false as const,
  productTruthLiveWrite: false as const,
  productDefinitionBridge: false as const,
  readyForPricing: false as const,
} as const;

export type FinishDraftValueStatus =
  | "evidence_only"
  | "draft_only"
  | "owner_confirmed_quantity_basis"
  | "owner_price_required"
  | "source_inventory_audit_required"
  | "not_applicable"
  | "not_finish_scope"
  | "blocked_from_activation";

export type FinishEstimateDraftCategory =
  | "oracal_vinyl"
  | "print_laminate"
  | "application_labor"
  | "none"
  | "excluded_boundary";

export type FinishEstimateDraftEntry = {
  key: string;
  labelRo: string;
  variantId: string;
  surfaceTarget: "face" | "artwork";
  category: FinishEstimateDraftCategory;
  quantityBasis: string;
  quantityBasisStatus: "owner_confirmed_quantity_basis";
  materialEvidenceKeys: readonly string[];
  laborEvidenceKeys: readonly string[];
  serviceEvidenceKeys: readonly string[];
  evidenceMaterialEurMp: number | null;
  evidenceLaborEurMp: number | null;
  evidenceCombinedEurMp: number | null;
  draftValueStatus: FinishDraftValueStatus;
  displayValueRo: string;
  pricingActive: false;
  mustNotWritePricingRegistry: true;
  activationStatus: "blocked_from_activation";
  notesRo: string;
};

export type FinishDraftExcludedKey = {
  key: string;
  pricingKey: string;
  ownerComponent: "RETURN-CANT" | "FACE";
  status: "not_finish_scope";
  notesRo: string;
};

export const FINISH_ESTIMATE_CALCULATION_RULES: readonly string[] = [
  "Finish față Oracal/print = mp_face_area × evidence material/service/labor (readonly — nu activare)",
  "Finish artwork = mp_artwork_area când geometria există (handoff runtime pending)",
  "face_material_usage_area_m2 = referință internă FACE — nu bază FINISH",
  "Material Plexiglas / MAT-ACP-FATA-LITERE = FACE — nu FINISH",
  "RETURN-CANT labor keys = exclus din FINISH",
  "Evidence EUR/mp din seeds — nu Pricing Registry authority în Product System",
] as const;

/** Seed evidence EUR/mp — evidence_only, not active pricing. */
export const FINISH_EVIDENCE_REFERENCE_RATES = {
  MAT_ORACAL_641: 6.5,
  MAT_ORACAL_651: 9.0,
  MAT_ORACAL_8500: 20.0,
  MAT_VINYL_PRINT_LAMINATED: 10.0,
  MAT_VINYL_PRINT: 1.5,
  FACE_VINYL_APPLICATION_LABOR: 5.0,
  LARGE_FORMAT_PRINT: 8.5,
  LAMINATION: 5.0,
} as const;

export const FINISH_ESTIMATED_PRICE_DRAFT_ENTRIES: readonly FinishEstimateDraftEntry[] = [
  {
    key: "face_oracal_641_draft",
    labelRo: "Face Oracal 641 — material + labor evidence",
    variantId: "face_oracal_641",
    surfaceTarget: "face",
    category: "oracal_vinyl",
    quantityBasis: "mp_face_area",
    quantityBasisStatus: "owner_confirmed_quantity_basis",
    materialEvidenceKeys: ["MAT-ORACAL-641"],
    laborEvidenceKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    serviceEvidenceKeys: [],
    evidenceMaterialEurMp: FINISH_EVIDENCE_REFERENCE_RATES.MAT_ORACAL_641,
    evidenceLaborEurMp: FINISH_EVIDENCE_REFERENCE_RATES.FACE_VINYL_APPLICATION_LABOR,
    evidenceCombinedEurMp: null,
    draftValueStatus: "evidence_only",
    displayValueRo: "material 6.50 EUR/mp + labor 5.00 EUR/mp (evidence only)",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
    activationStatus: "blocked_from_activation",
    notesRo: "Seed volumetric_owner_confirmed_prices — nu activare pricing.",
  },
  {
    key: "face_oracal_651_draft",
    labelRo: "Face Oracal 651 — material + labor evidence",
    variantId: "face_oracal_651",
    surfaceTarget: "face",
    category: "oracal_vinyl",
    quantityBasis: "mp_face_area",
    quantityBasisStatus: "owner_confirmed_quantity_basis",
    materialEvidenceKeys: ["MAT-ORACAL-651"],
    laborEvidenceKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    serviceEvidenceKeys: [],
    evidenceMaterialEurMp: FINISH_EVIDENCE_REFERENCE_RATES.MAT_ORACAL_651,
    evidenceLaborEurMp: FINISH_EVIDENCE_REFERENCE_RATES.FACE_VINYL_APPLICATION_LABOR,
    evidenceCombinedEurMp: null,
    draftValueStatus: "evidence_only",
    displayValueRo: "material 9.00 EUR/mp + labor 5.00 EUR/mp (evidence only)",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
    activationStatus: "blocked_from_activation",
    notesRo: "Simple visible mp basis — no roll optimization in workshop.",
  },
  {
    key: "face_oracal_8500_draft",
    labelRo: "Face Oracal 8500 — material + labor evidence",
    variantId: "face_oracal_8500",
    surfaceTarget: "face",
    category: "oracal_vinyl",
    quantityBasis: "mp_face_area",
    quantityBasisStatus: "owner_confirmed_quantity_basis",
    materialEvidenceKeys: ["MAT-ORACAL-8500"],
    laborEvidenceKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    serviceEvidenceKeys: [],
    evidenceMaterialEurMp: FINISH_EVIDENCE_REFERENCE_RATES.MAT_ORACAL_8500,
    evidenceLaborEurMp: FINISH_EVIDENCE_REFERENCE_RATES.FACE_VINYL_APPLICATION_LABOR,
    evidenceCombinedEurMp: null,
    draftValueStatus: "evidence_only",
    displayValueRo: "material 20.00 EUR/mp + labor 5.00 EUR/mp (evidence only)",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
    activationStatus: "blocked_from_activation",
    notesRo: "Translucent / backlit face — evidence only.",
  },
  {
    key: "face_print_laminate_combined_draft",
    labelRo: "Face print + laminate — combined material evidence",
    variantId: "face_print_laminate",
    surfaceTarget: "face",
    category: "print_laminate",
    quantityBasis: "mp_face_area",
    quantityBasisStatus: "owner_confirmed_quantity_basis",
    materialEvidenceKeys: ["MAT-VINYL-PRINT-LAMINATED"],
    laborEvidenceKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    serviceEvidenceKeys: [],
    evidenceMaterialEurMp: null,
    evidenceLaborEurMp: FINISH_EVIDENCE_REFERENCE_RATES.FACE_VINYL_APPLICATION_LABOR,
    evidenceCombinedEurMp: FINISH_EVIDENCE_REFERENCE_RATES.MAT_VINYL_PRINT_LAMINATED,
    draftValueStatus: "evidence_only",
    displayValueRo: "combined 10.00 EUR/mp + labor 5.00 EUR/mp (evidence only)",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
    activationStatus: "blocked_from_activation",
    notesRo: "Variant acceptat — model combinat seed. Split: MAT-VINYL-PRINT 1.5 + PRINT 8.5 + LAMINATION 5.",
  },
  {
    key: "face_print_laminate_split_draft",
    labelRo: "Face print + laminate — split evidence (readonly)",
    variantId: "face_print_laminate",
    surfaceTarget: "face",
    category: "print_laminate",
    quantityBasis: "mp_face_area",
    quantityBasisStatus: "owner_confirmed_quantity_basis",
    materialEvidenceKeys: ["MAT-VINYL-PRINT"],
    laborEvidenceKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    serviceEvidenceKeys: ["LARGE_FORMAT_PRINT", "LAMINATION"],
    evidenceMaterialEurMp: FINISH_EVIDENCE_REFERENCE_RATES.MAT_VINYL_PRINT,
    evidenceLaborEurMp: FINISH_EVIDENCE_REFERENCE_RATES.FACE_VINYL_APPLICATION_LABOR,
    evidenceCombinedEurMp: null,
    draftValueStatus: "evidence_only",
    displayValueRo: "material 1.50 + print 8.50 + lam 5.00 + labor 5.00 EUR/mp (evidence only)",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
    activationStatus: "blocked_from_activation",
    notesRo: "Conceptual separable model — owner decision; not activated.",
  },
  {
    key: "artwork_oracal_641_draft",
    labelRo: "Artwork Oracal 641 — material + labor evidence",
    variantId: "artwork_cut_vinyl",
    surfaceTarget: "artwork",
    category: "oracal_vinyl",
    quantityBasis: "mp_artwork_area",
    quantityBasisStatus: "owner_confirmed_quantity_basis",
    materialEvidenceKeys: ["MAT-ORACAL-641"],
    laborEvidenceKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    serviceEvidenceKeys: [],
    evidenceMaterialEurMp: FINISH_EVIDENCE_REFERENCE_RATES.MAT_ORACAL_641,
    evidenceLaborEurMp: FINISH_EVIDENCE_REFERENCE_RATES.FACE_VINYL_APPLICATION_LABOR,
    evidenceCombinedEurMp: null,
    draftValueStatus: "evidence_only",
    displayValueRo: "material 6.50 EUR/mp + labor 5.00 EUR/mp (evidence only)",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
    activationStatus: "blocked_from_activation",
    notesRo: "Artwork geometry handoff pending — basis rule owner-confirmed.",
  },
  {
    key: "artwork_print_laminate_draft",
    labelRo: "Artwork print + laminate — evidence",
    variantId: "artwork_print_laminate",
    surfaceTarget: "artwork",
    category: "print_laminate",
    quantityBasis: "mp_artwork_area",
    quantityBasisStatus: "owner_confirmed_quantity_basis",
    materialEvidenceKeys: ["MAT-VINYL-PRINT-LAMINATED"],
    laborEvidenceKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    serviceEvidenceKeys: ["LARGE_FORMAT_PRINT", "LAMINATION"],
    evidenceMaterialEurMp: null,
    evidenceLaborEurMp: FINISH_EVIDENCE_REFERENCE_RATES.FACE_VINYL_APPLICATION_LABOR,
    evidenceCombinedEurMp: FINISH_EVIDENCE_REFERENCE_RATES.MAT_VINYL_PRINT_LAMINATED,
    draftValueStatus: "source_inventory_audit_required",
    displayValueRo: "combined 10.00 EUR/mp or split — artwork keys audit required",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
    activationStatus: "blocked_from_activation",
    notesRo: "Artwork-specific print/lam keys pending inventory cross-ref audit.",
  },
  {
    key: "artwork_print_only_draft",
    labelRo: "Artwork print only — evidence",
    variantId: "artwork_print_only",
    surfaceTarget: "artwork",
    category: "print_laminate",
    quantityBasis: "mp_artwork_area",
    quantityBasisStatus: "owner_confirmed_quantity_basis",
    materialEvidenceKeys: ["MAT-VINYL-PRINT"],
    laborEvidenceKeys: [],
    serviceEvidenceKeys: ["LARGE_FORMAT_PRINT"],
    evidenceMaterialEurMp: FINISH_EVIDENCE_REFERENCE_RATES.MAT_VINYL_PRINT,
    evidenceLaborEurMp: null,
    evidenceCombinedEurMp: null,
    draftValueStatus: "source_inventory_audit_required",
    displayValueRo: "material 1.50 + print 8.50 EUR/mp (evidence only)",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
    activationStatus: "blocked_from_activation",
    notesRo: "Artwork print keys — audit required before owner price draft.",
  },
  {
    key: "artwork_translucent_8500_draft",
    labelRo: "Artwork translucent vinyl — Oracal 8500 evidence",
    variantId: "artwork_translucent_vinyl",
    surfaceTarget: "artwork",
    category: "oracal_vinyl",
    quantityBasis: "mp_artwork_area",
    quantityBasisStatus: "owner_confirmed_quantity_basis",
    materialEvidenceKeys: ["MAT-ORACAL-8500"],
    laborEvidenceKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    serviceEvidenceKeys: [],
    evidenceMaterialEurMp: FINISH_EVIDENCE_REFERENCE_RATES.MAT_ORACAL_8500,
    evidenceLaborEurMp: FINISH_EVIDENCE_REFERENCE_RATES.FACE_VINYL_APPLICATION_LABOR,
    evidenceCombinedEurMp: null,
    draftValueStatus: "evidence_only",
    displayValueRo: "material 20.00 EUR/mp + labor 5.00 EUR/mp (evidence only)",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
    activationStatus: "blocked_from_activation",
    notesRo: "8500 typical pentru translucid artwork.",
  },
  {
    key: "artwork_none_raw_plexi_draft",
    labelRo: "Artwork none / raw plexi — no FINISH charge",
    variantId: "artwork_none_raw_plexi",
    surfaceTarget: "artwork",
    category: "none",
    quantityBasis: "none",
    quantityBasisStatus: "owner_confirmed_quantity_basis",
    materialEvidenceKeys: [],
    laborEvidenceKeys: [],
    serviceEvidenceKeys: [],
    evidenceMaterialEurMp: null,
    evidenceLaborEurMp: null,
    evidenceCombinedEurMp: null,
    draftValueStatus: "not_applicable",
    displayValueRo: "N/A — 0 EUR (no FINISH finish application)",
    pricingActive: false,
    mustNotWritePricingRegistry: true,
    activationStatus: "blocked_from_activation",
    notesRo: "Nu confunda cu material Plexiglas FACE — substrat FACE, nu FINISH.",
  },
] as const;

export const FINISH_DRAFT_EXCLUDED_KEYS: readonly FinishDraftExcludedKey[] = [
  {
    key: "return_cant_vinyl_labor_excluded",
    pricingKey: "RETURN_CANT_VINYL_APPLICATION_LABOR",
    ownerComponent: "RETURN-CANT",
    status: "not_finish_scope",
    notesRo: "RETURN-CANT only — not FINISH face/artwork labor.",
  },
  {
    key: "face_plexiglas_material_excluded",
    pricingKey: "MAT-ACP-FATA-LITERE",
    ownerComponent: "FACE",
    status: "not_finish_scope",
    notesRo: "FACE base material — not FINISH finish application.",
  },
] as const;

export type FinishEstimateDraftSummary = {
  authority: typeof FINISH_ESTIMATE_DRAFT_AUTHORITY;
  readyForPricing: false;
  pricingActiveCount: 0;
  draftEntryCount: number;
  evidenceOnlyCount: number;
  auditRequiredCount: number;
  excludedKeyCount: number;
};

export function buildFinishEstimateDraftSummary(): FinishEstimateDraftSummary {
  return {
    authority: FINISH_ESTIMATE_DRAFT_AUTHORITY,
    readyForPricing: false,
    pricingActiveCount: 0,
    draftEntryCount: FINISH_ESTIMATED_PRICE_DRAFT_ENTRIES.length,
    evidenceOnlyCount: FINISH_ESTIMATED_PRICE_DRAFT_ENTRIES.filter(
      (e) => e.draftValueStatus === "evidence_only",
    ).length,
    auditRequiredCount: FINISH_ESTIMATED_PRICE_DRAFT_ENTRIES.filter(
      (e) => e.draftValueStatus === "source_inventory_audit_required",
    ).length,
    excludedKeyCount: FINISH_DRAFT_EXCLUDED_KEYS.length,
  };
}

export function getFinishEstimateDraftByKey(key: string): FinishEstimateDraftEntry | null {
  return FINISH_ESTIMATED_PRICE_DRAFT_ENTRIES.find((e) => e.key === key) ?? null;
}

export const FINISH_ESTIMATE_DRAFT_SUMMARY = buildFinishEstimateDraftSummary();
