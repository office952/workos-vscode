/**
 * FINISH Component Truth Workshop v1 — readonly contract only.
 * FINISH = face/artwork surface application; consumes FACE outputs.
 * Not runtime wiring. Not Product Truth write. Not Pricing activation.
 * Basis: canonical_finish_enum_map + face_component_truth + face_price_registry_alignment owner decisions.
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
export const FINISH_WORKSHOP_STATUS = "owner_input_required" as const;

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
    consumerUse: "Bază cantitate propusă vinyl față / print+laminare față",
    notesRo: "Output FACE — owner confirmă dacă mp_face_area sau face_material_usage_area_m2.",
  },
  {
    inputKey: "face_material_usage_area_m2",
    labelRo: "Arie material față (face_material_usage_area_m2)",
    sourceComponent: "FACE",
    status: "owner_confirmed",
    consumerUse: "Alternativă comparativă pentru bază cantitate material finish față",
    notesRo: "Bounding/out-of-box FACE — nu arie vectorială exactă.",
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
    status: "owner_input_required",
    consumerUse: "Scope finish artwork per instanță",
    notesRo: "Componentă LOGO viitoare poate prelua geometria — owner confirmă split.",
  },
  {
    inputKey: "selected_artwork_layer_refs",
    labelRo: "Referințe layer artwork selectate",
    sourceComponent: "artwork",
    status: "owner_input_required",
    consumerUse: "Geometrie artwork pentru vinyl/print/laminate",
    notesRo: "Nu componentizat complet în Product System.",
  },
  {
    inputKey: "artwork_bounding_area",
    labelRo: "Bază bounding/out-of-box artwork",
    sourceComponent: "artwork",
    status: "owner_input_required",
    consumerUse: "Bază cantitate propusă mp_artwork_area",
    notesRo: "Regulă exactă — owner input required.",
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
    notesRo: "Folie autocolantă 641 pe față Plexiglas — consumă mp_face_area (basis TBD).",
    catalogEvidenceLevel: "evidence_only",
  }),
  variantFromCanonical("face_oracal_651", {
    labelRo: "Face Oracal 651",
    notesRo: "Folie autocolantă 651 pe față — MAT-ORACAL-651 evidence only.",
  }),
  variantFromCanonical("face_oracal_8500", {
    labelRo: "Face Oracal 8500",
    notesRo: "Folie autocolantă 8500 pe față — MAT-ORACAL-8500 evidence only.",
  }),
  variantFromCanonical("face_print_laminate", {
    labelRo: "Face print + laminate",
    catalogPricingRefs: [],
    catalogEvidenceLevel: "owner_input_required",
    notesRo: "Chei print/lam față în registry — pending confirmare sursă owner.",
  }),
  variantFromCanonical("artwork_print_laminate", {
    labelRo: "Artwork print + laminate",
    catalogEvidenceLevel: "owner_input_required",
    notesRo: "Vector Logo / printed_artwork — chei print/lam pending.",
  }),
  variantFromCanonical("artwork_print_only", {
    labelRo: "Artwork print only",
    catalogEvidenceLevel: "owner_input_required",
    notesRo: "Chei print artwork pending confirmare registry.",
  }),
  variantFromCanonical("artwork_cut_vinyl", {
    labelRo: "Artwork cut vinyl",
    catalogEvidenceLevel: "owner_input_required",
    notesRo: "Familie Oracal artwork — chei exacte pending; nu cant labor keys.",
  }),
  variantFromCanonical("artwork_translucent_vinyl", {
    labelRo: "Artwork translucent vinyl",
    catalogEvidenceLevel: "evidence_only",
    notesRo: "8500 typical pentru translucid; labor artwork pending.",
  }),
  variantFromCanonical("artwork_none_raw_plexi", {
    labelRo: "Artwork none / raw plexi",
    quantityBasis: "none",
    quantityBasisStatus: "owner_confirmed",
    catalogEvidenceLevel: "owner_confirmed",
    ownerStatus: "owner_confirmed",
    notesRo: "Fără aplicație finish suplimentară pe artwork; substrat/scope artwork separat.",
    activationStatus: "blocked",
  }),
] as const;

export const FINISH_QUANTITY_BASIS_QUESTIONS: readonly FinishQuantityBasisQuestion[] = [
  {
    questionKey: "face_finish_quantity_basis",
    labelRo: "Bază cantitate finish față",
    proposedBasis: "mp_face_area SAU face_material_usage_area_m2",
    status: "owner_input_required",
    ownerQuestionRo: "Finish față: mp_face_area sau face_material_usage_area_m2?",
    notesRo: "Nu inventa formulă finală — owner confirmă.",
  },
  {
    questionKey: "artwork_finish_quantity_basis",
    labelRo: "Bază cantitate finish artwork",
    proposedBasis: "mp_artwork_area / bounding artwork",
    status: "owner_input_required",
    ownerQuestionRo: "Finish artwork: sursă geometrie Vector Logo și bază mp?",
    notesRo: "Componentă LOGO viitoare poate prelua — owner confirmă.",
  },
  {
    questionKey: "oracal_roll_usage",
    labelRo: "Consum Oracal / vinyl roll",
    proposedBasis: "roll width × used length SAU mp simplu",
    status: "owner_input_required",
    ownerQuestionRo: "FINISH face/artwork: roll width × used length sau mp simplu per variantă?",
    notesRo: "RETURN-CANT Oracal folosește ml_perimeter_x_width — FINISH poate avea regulă separată.",
  },
  {
    questionKey: "print_laminate_roll_usage",
    labelRo: "Consum print + laminare",
    proposedBasis: "probabil urmează aria print/roll usage",
    status: "owner_input_required",
    ownerQuestionRo: "Print/laminate: aceeași bază ca print area sau roll width × used length?",
    notesRo: "Nu activa — evidence only până la owner GO.",
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
    notesRo: "Cross-ref canonical enum + Intake V6 color registry — nu Pricing Registry write.",
  },
  {
    evidenceKey: "print_laminate_materials",
    labelRo: "Print material / laminate material / services",
    registryRoute: "/inventory/pricing",
    materialKeys: [],
    laborKeys: [],
    evidenceLevel: "owner_input_required",
    activationStatus: "blocked",
    notesRo: "Chei exacte print/lam în registry — pending owner confirmare sursă.",
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

export const FINISH_READINESS_BLOCKERS: readonly string[] = [
  "Owner must confirm FINISH surface variants",
  "Owner must confirm face quantity basis (mp_face_area vs face_material_usage_area_m2)",
  "Owner must confirm artwork quantity basis",
  "Owner must confirm Oracal/print/laminate catalog sources",
  "Owner must confirm artwork under FINISH vs future LOGO component",
  "Pricing Registry alignment needed later — no write now",
  "Product Truth live write blocked",
  "ProductDefinition bridge blocked",
  "Runtime Intake V6 → FACE/FINISH handoff blocked",
  "FACE pricing remains inactive — FINISH does not inherit active pricing",
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
  offerable: false;
  standaloneQuoteable: false;
  workIntakeExposed: false;
  pricingActive: false;
  productTruthLiveWrite: false;
  pricingRegistryWrite: false;
  doesNotOwnCant: true;
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

  return {
    workshopStatus: FINISH_WORKSHOP_STATUS,
    offerable: false,
    standaloneQuoteable: false,
    workIntakeExposed: false,
    pricingActive: false,
    productTruthLiveWrite: false,
    pricingRegistryWrite: false,
    doesNotOwnCant: FINISH_DOES_NOT_OWN_CANT,
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
