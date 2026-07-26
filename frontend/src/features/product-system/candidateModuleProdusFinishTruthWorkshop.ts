/**
 * FINISH Component Truth Workshop v1 — readonly contract only.
 * FINISH = face/artwork surface application; consumes FACE outputs.
 * Not runtime wiring. Not Product Truth write. Not Pricing activation.
 * Basis: canonical_finish_enum_map + face_component_truth + finish_component_truth_owner_decision_v1.md
 */

import {
  CANONICAL_FINISH_ENUM_MAP,
  getCanonicalFinishEntriesByOwner,
  type CanonicalFinishEnumEntry,
} from "./canonicalFinishEnumMap";

export type FinishWorkshopFieldStatus =
  | "owner_confirmed"
  | "owner_decision"
  | "source_found"
  | "evidence_only"
  | "draft_only"
  | "legacy_evidence"
  | "legacy_runtime_evidence"
  | "source_inventory_audit_required"
  | "registry_authority"
  | "owner_input_required"
  | "blocked";

export type FinishWorkshopVariantEntry = {
  id: string;
  labelRo: string;
  surfaceTarget: "face" | "artwork";
  technicalVariant: string;
  canonicalId: string;
  ownerStatus: FinishWorkshopFieldStatus;
  truthPathProposal: string;
  inputSource: string;
  quantityBasis: string;
  quantityBasisStatus: FinishWorkshopFieldStatus;
  catalogPricingRefs: readonly string[];
  catalogEvidenceLevel: FinishWorkshopFieldStatus;
  blockers: readonly string[];
  forbiddenOwners: readonly string[];
  activationStatus: "blocked" | "owner_confirmed" | "audit_only";
  notesRo: string;
};

export type FinishDependencyInput = {
  inputKey: string;
  labelRo: string;
  sourceComponent: "FACE" | "artwork" | "canonical_finish_enum";
  status: FinishWorkshopFieldStatus;
  consumerUse: string;
  notesRo: string;
};

export type FinishQuantityBasisQuestion = {
  questionKey: string;
  labelRo: string;
  proposedBasis: string;
  status: FinishWorkshopFieldStatus;
  ownerQuestionRo: string;
  notesRo: string;
};

export type FinishPricingEvidenceRef = {
  evidenceKey: string;
  labelRo: string;
  registryRoute: "/inventory/pricing" | null;
  materialKeys: readonly string[];
  laborKeys: readonly string[];
  evidenceLevel: FinishWorkshopFieldStatus;
  activationStatus: "blocked";
  notesRo: string;
};

export const FINISH_COMPONENT_TEMPLATE_CODE = "TPL-COMP-LETTER-FINISH_v1" as const;
export const FINISH_COMPONENT_ROLE = "FINISH" as const;
export const FINISH_WORKSHOP_STATUS = "partial_confirmed" as const;
export const FINISH_OWNER_DECISION_SOURCE = "finish_component_truth_owner_decision_v1" as const;
export const FINISH_READY_FOR_PRICING = false as const;
export const FINISH_PRODUCT_DEFINITION_BRIDGE_BLOCKED = true as const;

export const FINISH_IDENTITY = {
  templateCode: FINISH_COMPONENT_TEMPLATE_CODE,
  componentRole: FINISH_COMPONENT_ROLE,
  workshopStatus: FINISH_WORKSHOP_STATUS,
  offerable: false as const,
  standaloneQuoteable: false as const,
  workIntakeExposed: false as const,
  pricingActive: false as const,
  productTruthLiveWrite: false as const,
  pricingRegistryWrite: false as const,
} as const;

export const FINISH_OWNS: readonly string[] = [
  "aplicare suprafață față pe substrat FACE",
  "aplicare artwork / Vector Logo surface (pentru acum)",
  "vinyl / Oracal tăiat pe față sau artwork",
  "print pe față sau artwork",
  "laminare pe față sau artwork",
  "selecție variantă tehnică finish pentru față/artwork",
  "bază cantitate finish — doar consumând output-uri geometrie FACE/artwork",
] as const;

export const FINISH_DOES_NOT_OWN: readonly string[] = [
  "material/substrat/grosime FACE (Plexiglas/acrylic)",
  "debitare CNC FACE",
  "consum material FACE / preț Plexiglas (ex. MAT-ACP-FATA-LITERE 16 EUR/mp)",
  "sursă perimetru față (face_perimeter_length_m)",
  "finisaj cant lateral: Stock Color / Oracal / RAL (RETURN-CANT)",
  "material cant / adâncime cant (RETURN-CANT)",
  "politică minim 100 lei RAL cant (RETURN-CANT)",
  "RETURN-CANT material/labor keys",
  "Pricing Registry authority",
  "ProductDefinition runtime bridge",
  "Quote / Order / Execution task materialization",
  "Work Intake exposure",
] as const;

export const FINISH_DOES_NOT_OWN_CANT = true as const;

export const FINISH_FACE_DEPENDENCY_INPUTS: readonly FinishDependencyInput[] = [
  {
    inputKey: "mp_face_area",
    labelRo: "Arie față FINISH (mp_face_area)",
    sourceComponent: "FACE",
    status: "owner_confirmed",
    consumerUse: "Bază cantitate owner-confirmed vinyl față / print+laminare față",
    notesRo: "Owner decision: mp_face_area — visible face/application basis.",
  },
  {
    inputKey: "face_material_usage_area_m2",
    labelRo: "Arie material față (face_material_usage_area_m2)",
    sourceComponent: "FACE",
    status: "evidence_only",
    consumerUse: "Referință internă / evidence only — nu bază cantitate FINISH",
    notesRo: "Bounding/out-of-box FACE — nu folosit ca quantity basis FINISH.",
  },
  {
    inputKey: "face_piece_boxes",
    labelRo: "Cutii piesă față (face_piece_boxes)",
    sourceComponent: "FACE",
    status: "owner_confirmed",
    consumerUse: "Context geometrie / nesting per piece",
    notesRo: "FINISH nu recalculează nesting FACE.",
  },
  {
    inputKey: "source_layer_role",
    labelRo: "Rol sursă layer = Vector Litere",
    sourceComponent: "FACE",
    status: "owner_confirmed",
    consumerUse: "Geometrie față — nu Vector Logo",
    notesRo: "Artwork/Logo consum separat.",
  },
  {
    inputKey: "selected_face_layer_refs",
    labelRo: "Referințe layer față selectate",
    sourceComponent: "FACE",
    status: "owner_input_required",
    consumerUse: "Legătură geometrie față pentru finish application",
    notesRo: "Handoff runtime Intake V6 → FACE pending.",
  },
] as const;

export const FINISH_ARTWORK_DEPENDENCY_INPUTS: readonly FinishDependencyInput[] = [
  {
    inputKey: "artwork_instances",
    labelRo: "Instanțe artwork / Vector Logo",
    sourceComponent: "artwork",
    status: "owner_confirmed",
    consumerUse: "FINISH owns artwork surface finish application for now",
    notesRo: "Future LOGO component may own geometry later — not this slice.",
  },
  {
    inputKey: "selected_artwork_layer_refs",
    labelRo: "Referințe layer artwork selectate",
    sourceComponent: "artwork",
    status: "owner_input_required",
    consumerUse: "Geometrie artwork pentru vinyl/print/laminate",
    notesRo: "Runtime handoff pending — blocked until artwork area source exists.",
  },
  {
    inputKey: "artwork_bounding_area",
    labelRo: "Bază mp_artwork_area / visible artwork area",
    sourceComponent: "artwork",
    status: "owner_confirmed",
    consumerUse: "Bază cantitate finish artwork când geometria există",
    notesRo: "Blocked until artwork geometry handoff — basis rule owner-confirmed.",
  },
] as const;

function variantFromCanonical(
  canonicalId: string,
  overrides: Partial<FinishWorkshopVariantEntry> & Pick<FinishWorkshopVariantEntry, "labelRo">,
): FinishWorkshopVariantEntry {
  const entry = CANONICAL_FINISH_ENUM_MAP.find((e) => e.canonicalId === canonicalId)!;
  return {
    id: canonicalId,
    labelRo: overrides.labelRo,
    surfaceTarget: entry.surfaceTarget === "face" ? "face" : "artwork",
    technicalVariant: entry.technicalVariant,
    canonicalId,
    ownerStatus: "owner_input_required",
    truthPathProposal: entry.truthPathPrefix,
    inputSource: entry.catalogSource ?? "owner_input_required",
    quantityBasis: entry.quantityBasis,
    quantityBasisStatus: "owner_input_required",
    catalogPricingRefs: [
      ...entry.pricingMaterialKeys,
      ...entry.pricingLaborKeys,
    ],
    catalogEvidenceLevel:
      entry.pricingMaterialKeys.length > 0 || entry.pricingLaborKeys.length > 0
        ? "evidence_only"
        : "owner_input_required",
    blockers: [
      "Owner confirm surface variant",
      "Owner confirm quantity basis",
      "Pricing Registry alignment pending",
      "No Product Truth live write",
    ],
    forbiddenOwners: entry.forbiddenOwners,
    activationStatus: entry.activationStatus === "owner_confirmed" ? "owner_confirmed" : "blocked",
    notesRo: overrides.notesRo ?? entry.notesRo,
    ...overrides,
  };
}

export const FINISH_VARIANT_ENTRIES: readonly FinishWorkshopVariantEntry[] = [
  variantFromCanonical("face_oracal_641", {
    labelRo: "Face Oracal 641",
    ownerStatus: "owner_confirmed",
    quantityBasis: "mp_face_area",
    quantityBasisStatus: "owner_confirmed",
    catalogEvidenceLevel: "evidence_only",
    catalogPricingRefs: ["MAT-ORACAL-641", "FACE_VINYL_APPLICATION_LABOR"],
    blockers: ["Pricing activation blocked", "No Product Truth live write"],
    notesRo: "Simple visible mp — no roll optimization in workshop. MAT-ORACAL-641 evidence only.",
  }),
  variantFromCanonical("face_oracal_651", {
    labelRo: "Face Oracal 651",
    ownerStatus: "owner_confirmed",
    quantityBasis: "mp_face_area",
    quantityBasisStatus: "owner_confirmed",
    catalogEvidenceLevel: "evidence_only",
    catalogPricingRefs: ["MAT-ORACAL-651", "FACE_VINYL_APPLICATION_LABOR"],
    blockers: ["Pricing activation blocked", "No Product Truth live write"],
    notesRo: "MAT-ORACAL-651 evidence only — simple visible mp basis.",
  }),
  variantFromCanonical("face_oracal_8500", {
    labelRo: "Face Oracal 8500",
    ownerStatus: "owner_confirmed",
    quantityBasis: "mp_face_area",
    quantityBasisStatus: "owner_confirmed",
    catalogEvidenceLevel: "evidence_only",
    catalogPricingRefs: ["MAT-ORACAL-8500", "FACE_VINYL_APPLICATION_LABOR"],
    blockers: ["Pricing activation blocked", "No Product Truth live write"],
    notesRo: "MAT-ORACAL-8500 evidence only — simple visible mp basis.",
  }),
  variantFromCanonical("face_print_laminate", {
    labelRo: "Face print + laminate",
    ownerStatus: "owner_confirmed",
    quantityBasis: "mp_face_area",
    quantityBasisStatus: "owner_confirmed",
    catalogPricingRefs: ["MAT-VINYL-PRINT-LAMINATED", "LARGE_FORMAT_PRINT", "LAMINATION"],
    catalogEvidenceLevel: "evidence_only",
    blockers: ["Pricing activation blocked", "Print/lam conceptually separable — evidence only"],
    notesRo: "Print+lam accepted variant; material/service keys evidence only.",
  }),
  variantFromCanonical("artwork_print_laminate", {
    labelRo: "Artwork print + laminate",
    ownerStatus: "owner_confirmed",
    quantityBasis: "mp_artwork_area",
    quantityBasisStatus: "owner_confirmed",
    catalogEvidenceLevel: "evidence_only",
    blockers: ["Artwork geometry handoff pending", "Pricing activation blocked"],
    notesRo: "mp_artwork_area when geometry exists — FINISH owns artwork finish now.",
  }),
  variantFromCanonical("artwork_print_only", {
    labelRo: "Artwork print only",
    ownerStatus: "owner_confirmed",
    quantityBasis: "mp_artwork_area",
    quantityBasisStatus: "owner_confirmed",
    catalogEvidenceLevel: "evidence_only",
    catalogPricingRefs: ["LARGE_FORMAT_PRINT"],
    blockers: ["Artwork geometry handoff pending", "Pricing activation blocked"],
    notesRo: "PRINT evidence only — artwork visible mp basis.",
  }),
  variantFromCanonical("artwork_cut_vinyl", {
    labelRo: "Artwork cut vinyl",
    ownerStatus: "owner_confirmed",
    quantityBasis: "mp_artwork_area",
    quantityBasisStatus: "owner_confirmed",
    catalogEvidenceLevel: "evidence_only",
    blockers: ["Artwork geometry handoff pending", "Pricing activation blocked"],
    notesRo: "Oracal artwork — evidence only; not cant labor keys.",
  }),
  variantFromCanonical("artwork_translucent_vinyl", {
    labelRo: "Artwork translucent vinyl",
    ownerStatus: "owner_confirmed",
    quantityBasis: "mp_artwork_area",
    quantityBasisStatus: "owner_confirmed",
    catalogEvidenceLevel: "evidence_only",
    catalogPricingRefs: ["MAT-ORACAL-8500"],
    blockers: ["Artwork geometry handoff pending", "Pricing activation blocked"],
    notesRo: "8500 typical pentru translucid — evidence only.",
  }),
  variantFromCanonical("artwork_none_raw_plexi", {
    labelRo: "Artwork none / raw plexi",
    ownerStatus: "owner_confirmed",
    quantityBasis: "none",
    quantityBasisStatus: "owner_confirmed",
    catalogEvidenceLevel: "owner_confirmed",
    catalogPricingRefs: [],
    blockers: ["Pricing activation blocked"],
    notesRo: "No extra finish application on artwork — variant owner-confirmed.",
    activationStatus: "blocked",
  }),
] as const;

export const FINISH_QUANTITY_BASIS_QUESTIONS: readonly FinishQuantityBasisQuestion[] = [
  {
    questionKey: "face_finish_quantity_basis",
    labelRo: "Bază cantitate finish față",
    proposedBasis: "mp_face_area",
    status: "owner_confirmed",
    ownerQuestionRo: "Finish față: mp_face_area (ACCEPTED)",
    notesRo: "face_material_usage_area_m2 = internal/evidence only — not FINISH quantity basis.",
  },
  {
    questionKey: "artwork_finish_quantity_basis",
    labelRo: "Bază cantitate finish artwork",
    proposedBasis: "mp_artwork_area / visible artwork area",
    status: "owner_confirmed",
    ownerQuestionRo: "Artwork: mp_artwork_area when geometry exists (ACCEPTED)",
    notesRo: "Blocked until artwork geometry handoff — basis rule owner-confirmed.",
  },
  {
    questionKey: "oracal_roll_usage",
    labelRo: "Consum Oracal / vinyl roll",
    proposedBasis: "simple visible mp (no roll optimization now)",
    status: "owner_confirmed",
    ownerQuestionRo: "Oracal: simple mp basis in workshop — no roll width×length now (ACCEPTED)",
    notesRo: "Roll optimization = future internal material usage topic.",
  },
  {
    questionKey: "print_laminate_roll_usage",
    labelRo: "Consum print + laminare",
    proposedBasis: "print_laminated variant accepted; print/lam separable evidence",
    status: "owner_confirmed",
    ownerQuestionRo: "Print+lam: variant accepted; material/service evidence only (ACCEPTED)",
    notesRo: "MAT-VINYL-PRINT-LAMINATED or LARGE_FORMAT_PRINT + LAMINATION — evidence only.",
  },
] as const;

export const FINISH_PRICING_EVIDENCE: readonly FinishPricingEvidenceRef[] = [
  {
    evidenceKey: "oracal_641_651_8500",
    labelRo: "Oracal 641 / 651 / 8500 material keys",
    registryRoute: "/inventory/pricing",
    materialKeys: ["MAT-ORACAL-641", "MAT-ORACAL-651", "MAT-ORACAL-8500"],
    laborKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    evidenceLevel: "evidence_only",
    activationStatus: "blocked",
    notesRo:
      "Owner decision: all Oracal keys + FACE_VINYL_APPLICATION_LABOR = evidence_only — not active authority.",
  },
  {
    evidenceKey: "print_laminate_combined_material",
    labelRo: "Print + laminare față — material combinat",
    registryRoute: "/inventory/pricing",
    materialKeys: ["MAT-VINYL-PRINT-LAMINATED"],
    laborKeys: [],
    evidenceLevel: "evidence_only",
    activationStatus: "blocked",
    notesRo: "Owner decision: evidence_only — print+lam conceptually separable from services.",
  },
  {
    evidenceKey: "print_laminate_services",
    labelRo: "Print / laminare — servicii workcenter (PRINT / LAMINATION)",
    registryRoute: "/inventory/pricing",
    materialKeys: [],
    laborKeys: ["LARGE_FORMAT_PRINT", "LAMINATION"],
    evidenceLevel: "evidence_only",
    activationStatus: "blocked",
    notesRo: "Owner decision: PRINT + LAMINATION = evidence_only — not FINISH registry authority.",
  },
  {
    evidenceKey: "artwork_print_lam_evidence",
    labelRo: "Artwork print/lam — same keys as face (owner decision)",
    registryRoute: "/inventory/pricing",
    materialKeys: ["MAT-VINYL-PRINT", "MAT-VINYL-PRINT-LAMINATED"],
    laborKeys: ["FACE_VINYL_APPLICATION_LABOR", "LARGE_FORMAT_PRINT", "LAMINATION"],
    evidenceLevel: "evidence_only",
    activationStatus: "blocked",
    notesRo:
      "Owner price values decision: same evidence keys as face. mp_artwork_area handoff still blocked.",
  },
  {
    evidenceKey: "legacy_wc_vinyl_application",
    labelRo: "WC_VINYL_APPLICATION — legacy Intake V4 only",
    registryRoute: "/inventory/pricing",
    materialKeys: [],
    laborKeys: ["WC_VINYL_APPLICATION"],
    evidenceLevel: "legacy_runtime_evidence",
    activationStatus: "blocked",
    notesRo: "Not FINISH draft labor authority — Intake V4 artwork application path only.",
  },
  {
    evidenceKey: "artwork_print_only_blocked",
    labelRo: "Artwork print only — visible blocked",
    registryRoute: "/inventory/pricing",
    materialKeys: ["MAT-VINYL-PRINT"],
    laborKeys: ["LARGE_FORMAT_PRINT"],
    evidenceLevel: "source_inventory_audit_required",
    activationStatus: "blocked",
    notesRo: "No Intake V4 print_only runtime — canonical variant retained; future implementation.",
  },
  {
    evidenceKey: "return_cant_boundary",
    labelRo: "RETURN-CANT keys — NOT FINISH",
    registryRoute: "/inventory/pricing",
    materialKeys: ["MAT-PROFIL-LATERAL-LITERE-30MM", "RETURN_CANT_VINYL_APPLICATION_LABOR"],
    laborKeys: ["RETURN_CANT_RAL_PAINT_LABOR"],
    evidenceLevel: "registry_authority",
    activationStatus: "blocked",
    notesRo: "FINISH nu folosește cant labor keys; RAL 100 lei minimum = RETURN-CANT policy.",
  },
] as const;

export type FinishOwnerQuestion = {
  questionId: "A" | "B" | "C" | "D" | "E";
  topicRo: string;
  promptRo: string;
  currentEvidenceRo: string;
  ownerMustAnswerRo: string;
  status: FinishWorkshopFieldStatus;
};

export const FINISH_OWNER_QUESTIONS_PENDING: readonly FinishOwnerQuestion[] = [
  {
    questionId: "A",
    topicRo: "Variante suprafață FINISH",
    promptRo: "Confirmă cele 9 variante face/artwork din workshop.",
    currentEvidenceRo:
      "Canonical enum map: 9 surface-application variants owner-ACCEPTED.",
    ownerMustAnswerRo: "ACCEPT all 9 — recorded in finish_component_truth_owner_decision_v1.md",
    status: "owner_confirmed",
  },
  {
    questionId: "B",
    topicRo: "Bază cantitate",
    promptRo: "Confirmă regulile de cantitate pentru față, artwork, Oracal, print/lam.",
    currentEvidenceRo: "mp_face_area (face); mp_artwork_area (artwork); simple mp Oracal; print/lam separable.",
    ownerMustAnswerRo: "ACCEPTED — see owner decision doc §3",
    status: "owner_confirmed",
  },
  {
    questionId: "C",
    topicRo: "Catalog / pricing refs",
    promptRo: "Confirmă surse evidence pentru Oracal, print, laminare, labor.",
    currentEvidenceRo:
      "MAT-ORACAL-*, MAT-VINYL-PRINT-LAMINATED, FACE_VINYL_APPLICATION_LABOR, PRINT, LAMINATION — all evidence_only.",
    ownerMustAnswerRo: "ACCEPTED — RETURN_CANT_VINYL_APPLICATION_LABOR excluded from FINISH",
    status: "owner_confirmed",
  },
  {
    questionId: "D",
    topicRo: "Boundary FINISH vs FACE / RETURN-CANT",
    promptRo: "Reconfirmă ce NU deține FINISH.",
    currentEvidenceRo:
      "FACE owner decision + RETURN-CANT owner inputs + canonical forbiddenOwners.",
    ownerMustAnswerRo: "ACCEPTED — no cant, no FACE Plexiglas, no RAL 100 lei, no registry authority",
    status: "owner_confirmed",
  },
  {
    questionId: "E",
    topicRo: "Split LOGO / artwork",
    promptRo: "Artwork / Vector Logo rămâne sub FINISH acum?",
    currentEvidenceRo: "Intake V6 artwork_instances — FINISH owns surface finish application now.",
    ownerMustAnswerRo: "ACCEPTED — artwork under FINISH now; future LOGO component for geometry later",
    status: "owner_confirmed",
  },
] as const;

export const FINISH_BOUNDARY_REAFFIRMATION: readonly string[] = [
  "FINISH does not own RETURN-CANT cant finish (Stock / Oracal wrap / RAL paint)",
  "FINISH does not own FACE base material / Plexiglas pricing (MAT-ACP-FATA-LITERE)",
  "FINISH does not own RAL cant minimum 100 lei (RETURN-CANT commercial policy)",
  "FINISH does not own Pricing Registry authority — evidence cross-ref only",
  "RETURN_CANT_VINYL_APPLICATION_LABOR is RETURN-CANT only — not FINISH face vinyl labor",
] as const;

export const FINISH_AWAITING_OWNER_CHAT = false as const;

export const FINISH_READINESS_BLOCKERS: readonly string[] = [
  "Pricing activation blocked — no readyForPricing",
  "Product Truth live write blocked",
  "ProductDefinition bridge blocked",
  "Runtime Intake V6 → FACE/FINISH handoff blocked",
  "Artwork geometry handoff pending — mp_artwork_area rule confirmed but runtime source missing",
  "Pricing Registry alignment / draft slice needed later — no write now",
  "FACE pricing remains inactive — FINISH does not inherit active pricing",
  "Quote/Order active pricing use blocked",
] as const;

export const FINISH_DANGEROUS_ACTIONS: readonly string[] = [
  "Save",
  "Apply",
  "Activate",
  "Write Product Truth",
  "Create Pricing Key",
  "Generate Quote",
  "Sync",
  "Promote",
  "Expose to Work Intake",
] as const;

export type FinishReadinessSummary = {
  workshopStatus: typeof FINISH_WORKSHOP_STATUS;
  readyForPricing: false;
  offerable: false;
  standaloneQuoteable: false;
  workIntakeExposed: false;
  pricingActive: false;
  productTruthLiveWrite: false;
  pricingRegistryWrite: false;
  productDefinitionBridgeBlocked: true;
  doesNotOwnCant: true;
  ownerConfirmedVariantCount: number;
  variantCount: number;
  faceDependencyCount: number;
  artworkDependencyCount: number;
  quantityBasisQuestionCount: number;
  pricingEvidenceCount: number;
  readinessBlockerCount: number;
  canonicalFinishOwnedCount: number;
  blockedVariantCount: number;
};

export function buildFinishReadinessSummary(): FinishReadinessSummary {
  const canonicalFinishOwnedCount = getCanonicalFinishEntriesByOwner("FINISH").length;
  const blockedVariantCount = FINISH_VARIANT_ENTRIES.filter((v) => v.activationStatus === "blocked").length;
  const ownerConfirmedVariantCount = FINISH_VARIANT_ENTRIES.filter(
    (v) => v.ownerStatus === "owner_confirmed",
  ).length;

  return {
    workshopStatus: FINISH_WORKSHOP_STATUS,
    readyForPricing: false,
    offerable: false,
    standaloneQuoteable: false,
    workIntakeExposed: false,
    pricingActive: false,
    productTruthLiveWrite: false,
    pricingRegistryWrite: false,
    productDefinitionBridgeBlocked: FINISH_PRODUCT_DEFINITION_BRIDGE_BLOCKED,
    doesNotOwnCant: FINISH_DOES_NOT_OWN_CANT,
    ownerConfirmedVariantCount,
    variantCount: FINISH_VARIANT_ENTRIES.length,
    faceDependencyCount: FINISH_FACE_DEPENDENCY_INPUTS.length,
    artworkDependencyCount: FINISH_ARTWORK_DEPENDENCY_INPUTS.length,
    quantityBasisQuestionCount: FINISH_QUANTITY_BASIS_QUESTIONS.length,
    pricingEvidenceCount: FINISH_PRICING_EVIDENCE.length,
    readinessBlockerCount: FINISH_READINESS_BLOCKERS.length,
    canonicalFinishOwnedCount,
    blockedVariantCount,
  };
}

export function getFinishVariantById(id: string): FinishWorkshopVariantEntry | null {
  return FINISH_VARIANT_ENTRIES.find((v) => v.id === id) ?? null;
}

export function getCanonicalFinishEntryForFinish(id: string): CanonicalFinishEnumEntry | null {
  return CANONICAL_FINISH_ENUM_MAP.find((e) => e.canonicalId === id) ?? null;
}

export const FINISH_READINESS_SUMMARY = buildFinishReadinessSummary();
