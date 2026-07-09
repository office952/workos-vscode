/**
 * Canonical Finish Enum Map v1 — readonly contract only.
 * Source: docs/worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md
 * Not runtime wiring. Not Product Truth write. Not Pricing activation.
 */

export type FinishSurfaceTarget = "cant" | "face" | "artwork";

export type FinishTechnicalVariant =
  | "stock_color"
  | "vinyl_application"
  | "paint_application"
  | "print_laminate"
  | "print_only"
  | "commercial_minimum"
  | "none_or_material_default";

export type FinishOwnerComponent = "RETURN-CANT" | "FINISH" | "FACE";

export type FinishQuantityBasis =
  | "none"
  | "ml_perimeter"
  | "ml_perimeter_x_width"
  | "mp_face_area"
  | "mp_artwork_area"
  | "owner_policy";

export type FinishActivationStatus =
  | "owner_confirmed"
  | "blocked"
  | "deprecated_conceptual"
  | "audit_only";

export type CanonicalFinishCatalogSource =
  | "intake_v6_color_registry"
  | "stock_color_catalog_tbd"
  | null;

export type CanonicalFinishEnumEntry = {
  canonicalId: string;
  surfaceTarget: FinishSurfaceTarget;
  technicalVariant: FinishTechnicalVariant;
  intakeTokens: readonly string[];
  productSystemLabelRo: string | null;
  ownerComponent: FinishOwnerComponent;
  truthPathPrefix: string;
  catalogSource: CanonicalFinishCatalogSource;
  pricingSource: "/inventory/pricing" | null;
  pricingMaterialKeys: readonly string[];
  pricingLaborKeys: readonly string[];
  quantityBasis: FinishQuantityBasis;
  commercialPolicySource: "cpp_owner_policy" | null;
  forbiddenOwners: readonly FinishOwnerComponent[];
  activationStatus: FinishActivationStatus;
  notesRo: string;
};

export type CanonicalFinishRetiredPath = {
  retiredPath: string;
  reasonRo: string;
  replacementPaths: readonly string[];
  retirementStatus: "deprecated_conceptual";
};

export const CANONICAL_FINISH_PRICING_SOURCE = "/inventory/pricing" as const;

export const CANONICAL_FINISH_PROFILE_MATERIAL_KEY_PATTERN =
  "MAT-PROFIL-LATERAL-LITERE-{30|60|80|100}MM" as const;

export const CANONICAL_FINISH_ENUM_MAP: readonly CanonicalFinishEnumEntry[] = [
  {
    canonicalId: "cant_stock_color",
    surfaceTarget: "cant",
    technicalVariant: "stock_color",
    intakeTokens: [
      "white_aluminum",
      "black_aluminum",
      "gold_aluminum",
      "mirror_silver",
      "standard_aluminum",
    ],
    productSystemLabelRo: "Culoare Stock",
    ownerComponent: "RETURN-CANT",
    truthPathPrefix: "product.components.return_cant.finish",
    catalogSource: "stock_color_catalog_tbd",
    pricingSource: CANONICAL_FINISH_PRICING_SOURCE,
    pricingMaterialKeys: [
      "MAT-PROFIL-LATERAL-LITERE-30MM",
      "MAT-PROFIL-LATERAL-LITERE-60MM",
      "MAT-PROFIL-LATERAL-LITERE-80MM",
      "MAT-PROFIL-LATERAL-LITERE-100MM",
    ],
    pricingLaborKeys: [],
    quantityBasis: "ml_perimeter",
    commercialPolicySource: null,
    forbiddenOwners: ["FINISH", "FACE"],
    activationStatus: "owner_confirmed",
    notesRo:
      "Fără tarif finish suplimentar — cost din profil cant pe adâncime + operații formare/lipire.",
  },
  {
    canonicalId: "cant_oracal_wrap",
    surfaceTarget: "cant",
    technicalVariant: "vinyl_application",
    intakeTokens: ["oracal_wrapped", "oracal_651", "vinyl"],
    productSystemLabelRo: "Oracal",
    ownerComponent: "RETURN-CANT",
    truthPathPrefix: "product.components.return_cant.finish.vinyl",
    catalogSource: "intake_v6_color_registry",
    pricingSource: CANONICAL_FINISH_PRICING_SOURCE,
    pricingMaterialKeys: ["MAT-ORACAL-641", "MAT-ORACAL-651"],
    pricingLaborKeys: ["RETURN_CANT_VINYL_APPLICATION_LABOR"],
    quantityBasis: "ml_perimeter_x_width",
    commercialPolicySource: null,
    forbiddenOwners: ["FINISH", "FACE"],
    activationStatus: "owner_confirmed",
    notesRo:
      "Consum material mp din perimetru × lățime cant; catalog Oracal — cross-ref Intake V6, fără duplicare PS.",
  },
  {
    canonicalId: "cant_ral_paint",
    surfaceTarget: "cant",
    technicalVariant: "paint_application",
    intakeTokens: ["ral_paint", "painted", "paint"],
    productSystemLabelRo: "Vopsit RAL",
    ownerComponent: "RETURN-CANT",
    truthPathPrefix: "product.components.return_cant.finish.paint",
    catalogSource: "intake_v6_color_registry",
    pricingSource: CANONICAL_FINISH_PRICING_SOURCE,
    pricingMaterialKeys: [
      "MAT-VOPSEA-RAL-CANT-30MM",
      "MAT-VOPSEA-RAL-CANT-60MM",
      "MAT-VOPSEA-RAL-CANT-80MM",
      "MAT-VOPSEA-RAL-CANT-100MM",
    ],
    pricingLaborKeys: ["RETURN_CANT_RAL_PAINT_LABOR"],
    quantityBasis: "ml_perimeter",
    commercialPolicySource: null,
    forbiddenOwners: ["FINISH", "FACE"],
    activationStatus: "owner_confirmed",
    notesRo: "Chei registry readonly — fără valori EUR duplicate în Product System.",
  },
  {
    canonicalId: "cant_ral_minimum_policy",
    surfaceTarget: "cant",
    technicalVariant: "commercial_minimum",
    intakeTokens: [],
    productSystemLabelRo: "100 lei pe culoare RAL",
    ownerComponent: "RETURN-CANT",
    truthPathPrefix: "product.components.return_cant.commercial_policy.ral_minimum",
    catalogSource: null,
    pricingSource: null,
    pricingMaterialKeys: [],
    pricingLaborKeys: [],
    quantityBasis: "owner_policy",
    commercialPolicySource: "cpp_owner_policy",
    forbiddenOwners: ["FINISH"],
    activationStatus: "owner_confirmed",
    notesRo:
      "NOT Pricing Registry · owner commercial rule · fără conversie automată lei→EUR · total material RAL + manoperă.",
  },
  {
    canonicalId: "face_none_or_material_default",
    surfaceTarget: "face",
    technicalVariant: "none_or_material_default",
    intakeTokens: ["none"],
    productSystemLabelRo: null,
    ownerComponent: "FACE",
    truthPathPrefix: "product.components.finish.face",
    catalogSource: null,
    pricingSource: null,
    pricingMaterialKeys: [],
    pricingLaborKeys: [],
    quantityBasis: "none",
    commercialPolicySource: null,
    forbiddenOwners: ["RETURN-CANT"],
    activationStatus: "blocked",
    notesRo: "FACE deține substratul; FINISH nu are aplicație finish pe față brută.",
  },
  {
    canonicalId: "face_oracal_641",
    surfaceTarget: "face",
    technicalVariant: "vinyl_application",
    intakeTokens: ["oracal_641"],
    productSystemLabelRo: "Folie autocolantă — 641",
    ownerComponent: "FINISH",
    truthPathPrefix: "product.components.finish.face.vinyl",
    catalogSource: "intake_v6_color_registry",
    pricingSource: CANONICAL_FINISH_PRICING_SOURCE,
    pricingMaterialKeys: ["MAT-ORACAL-641"],
    pricingLaborKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    quantityBasis: "mp_face_area",
    commercialPolicySource: null,
    forbiddenOwners: ["RETURN-CANT"],
    activationStatus: "blocked",
    notesRo: "FINISH workshop blocked până la FACE boundary workshop.",
  },
  {
    canonicalId: "face_oracal_651",
    surfaceTarget: "face",
    technicalVariant: "vinyl_application",
    intakeTokens: ["oracal_651"],
    productSystemLabelRo: "Folie autocolantă — 651",
    ownerComponent: "FINISH",
    truthPathPrefix: "product.components.finish.face.vinyl",
    catalogSource: "intake_v6_color_registry",
    pricingSource: CANONICAL_FINISH_PRICING_SOURCE,
    pricingMaterialKeys: ["MAT-ORACAL-651"],
    pricingLaborKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    quantityBasis: "mp_face_area",
    commercialPolicySource: null,
    forbiddenOwners: ["RETURN-CANT"],
    activationStatus: "blocked",
    notesRo: "FINISH workshop blocked până la FACE boundary workshop.",
  },
  {
    canonicalId: "face_oracal_8500",
    surfaceTarget: "face",
    technicalVariant: "vinyl_application",
    intakeTokens: ["oracal_8500"],
    productSystemLabelRo: "Folie autocolantă — 8500",
    ownerComponent: "FINISH",
    truthPathPrefix: "product.components.finish.face.vinyl",
    catalogSource: "intake_v6_color_registry",
    pricingSource: CANONICAL_FINISH_PRICING_SOURCE,
    pricingMaterialKeys: ["MAT-ORACAL-8500"],
    pricingLaborKeys: ["FACE_VINYL_APPLICATION_LABOR"],
    quantityBasis: "mp_face_area",
    commercialPolicySource: null,
    forbiddenOwners: ["RETURN-CANT"],
    activationStatus: "blocked",
    notesRo: "FINISH workshop blocked până la FACE boundary workshop.",
  },
  {
    canonicalId: "face_print_laminate",
    surfaceTarget: "face",
    technicalVariant: "print_laminate",
    intakeTokens: ["print_laminate"],
    productSystemLabelRo: "Print + laminare",
    ownerComponent: "FINISH",
    truthPathPrefix: "product.components.finish.face.print_lamination",
    catalogSource: null,
    pricingSource: CANONICAL_FINISH_PRICING_SOURCE,
    pricingMaterialKeys: [],
    pricingLaborKeys: [],
    quantityBasis: "mp_face_area",
    commercialPolicySource: null,
    forbiddenOwners: ["RETURN-CANT"],
    activationStatus: "blocked",
    notesRo: "Chei exacte print/lam în registry — pending confirmare sursă; RETURN-CANT nu deține print/lam.",
  },
  {
    canonicalId: "artwork_print_laminate",
    surfaceTarget: "artwork",
    technicalVariant: "print_laminate",
    intakeTokens: ["execution_type=print_laminate", "face_personalization_method=print_laminate"],
    productSystemLabelRo: "Print + laminare (logo/artwork)",
    ownerComponent: "FINISH",
    truthPathPrefix: "product.components.finish.artwork.instances[].print_lamination",
    catalogSource: null,
    pricingSource: CANONICAL_FINISH_PRICING_SOURCE,
    pricingMaterialKeys: [],
    pricingLaborKeys: [],
    quantityBasis: "mp_artwork_area",
    commercialPolicySource: null,
    forbiddenOwners: ["RETURN-CANT"],
    activationStatus: "blocked",
    notesRo: "Vector Logo / printed_artwork — FINISH owns application; chei print/lam pending.",
  },
  {
    canonicalId: "artwork_print_only",
    surfaceTarget: "artwork",
    technicalVariant: "print_only",
    intakeTokens: ["execution_type=print_only"],
    productSystemLabelRo: "Print (logo/artwork)",
    ownerComponent: "FINISH",
    truthPathPrefix: "product.components.finish.artwork.instances[].print",
    catalogSource: null,
    pricingSource: CANONICAL_FINISH_PRICING_SOURCE,
    pricingMaterialKeys: [],
    pricingLaborKeys: [],
    quantityBasis: "mp_artwork_area",
    commercialPolicySource: null,
    forbiddenOwners: ["RETURN-CANT"],
    activationStatus: "blocked",
    notesRo: "Chei print exacte pending confirmare registry.",
  },
  {
    canonicalId: "artwork_cut_vinyl",
    surfaceTarget: "artwork",
    technicalVariant: "vinyl_application",
    intakeTokens: ["execution_type=cut_vinyl"],
    productSystemLabelRo: "Colant tăiat (logo/artwork)",
    ownerComponent: "FINISH",
    truthPathPrefix: "product.components.finish.artwork.instances[].vinyl",
    catalogSource: "intake_v6_color_registry",
    pricingSource: CANONICAL_FINISH_PRICING_SOURCE,
    pricingMaterialKeys: [],
    pricingLaborKeys: [],
    quantityBasis: "mp_artwork_area",
    commercialPolicySource: null,
    forbiddenOwners: ["RETURN-CANT"],
    activationStatus: "blocked",
    notesRo: "Familie Oracal — chei exacte artwork pending; nu cant labor keys.",
  },
  {
    canonicalId: "artwork_translucent_vinyl",
    surfaceTarget: "artwork",
    technicalVariant: "vinyl_application",
    intakeTokens: ["execution_type=translucent_vinyl"],
    productSystemLabelRo: "Colant translucid (logo/artwork)",
    ownerComponent: "FINISH",
    truthPathPrefix: "product.components.finish.artwork.instances[].vinyl",
    catalogSource: "intake_v6_color_registry",
    pricingSource: CANONICAL_FINISH_PRICING_SOURCE,
    pricingMaterialKeys: ["MAT-ORACAL-8500"],
    pricingLaborKeys: [],
    quantityBasis: "mp_artwork_area",
    commercialPolicySource: null,
    forbiddenOwners: ["RETURN-CANT"],
    activationStatus: "blocked",
    notesRo: "8500 typical pentru translucid; labor artwork pending confirmare.",
  },
  {
    canonicalId: "artwork_none_raw_plexi",
    surfaceTarget: "artwork",
    technicalVariant: "none_or_material_default",
    intakeTokens: ["execution_type=none_raw_plexi"],
    productSystemLabelRo: "Plexiglas brut (artwork)",
    ownerComponent: "FINISH",
    truthPathPrefix: "product.components.finish.artwork.instances[].variant",
    catalogSource: null,
    pricingSource: null,
    pricingMaterialKeys: [],
    pricingLaborKeys: [],
    quantityBasis: "none",
    commercialPolicySource: null,
    forbiddenOwners: ["RETURN-CANT"],
    activationStatus: "blocked",
    notesRo: "Fără aplicație finish suplimentară pe artwork; substrat/scope artwork separat.",
  },
] as const;

export const CANONICAL_FINISH_RETIRED_PATHS: readonly CanonicalFinishRetiredPath[] = [
  {
    retiredPath: "product.components.finish.oracal_code",
    reasonRo: "Generic fără surface_target — duplică Oracal cant.",
    replacementPaths: [
      "product.components.finish.face.vinyl.*",
      "product.components.finish.artwork.instances[].vinyl.*",
      "product.components.return_cant.finish.vinyl.*",
    ],
    retirementStatus: "deprecated_conceptual",
  },
  {
    retiredPath: "product.components.finish.ral_code",
    reasonRo: "Generic fără surface_target — duplică RAL cant.",
    replacementPaths: [
      "product.components.return_cant.finish.paint.ral_code",
      "product.components.finish.face.paint.*",
    ],
    retirementStatus: "deprecated_conceptual",
  },
  {
    retiredPath: "product.components.finish.stock_color",
    reasonRo: "Generic fără surface_target — duplică stock cant.",
    replacementPaths: [
      "product.components.return_cant.finish.stock_color_label",
      "product.components.finish.face.variant",
    ],
    retirementStatus: "deprecated_conceptual",
  },
  {
    retiredPath: "product.components.finish.type",
    reasonRo: "Ambiguu fără suprafață.",
    replacementPaths: [
      "product.components.return_cant.finish.variant",
      "product.components.finish.face.variant",
      "product.components.finish.artwork.instances[].variant",
    ],
    retirementStatus: "deprecated_conceptual",
  },
] as const;

export function getCanonicalFinishEntry(canonicalId: string): CanonicalFinishEnumEntry | null {
  const normalized = canonicalId.trim();
  return CANONICAL_FINISH_ENUM_MAP.find((entry) => entry.canonicalId === normalized) ?? null;
}

export function getCanonicalFinishEntriesBySurface(
  surfaceTarget: FinishSurfaceTarget,
): CanonicalFinishEnumEntry[] {
  return CANONICAL_FINISH_ENUM_MAP.filter((entry) => entry.surfaceTarget === surfaceTarget);
}

export function getCanonicalFinishEntriesByOwner(
  ownerComponent: FinishOwnerComponent,
): CanonicalFinishEnumEntry[] {
  return CANONICAL_FINISH_ENUM_MAP.filter((entry) => entry.ownerComponent === ownerComponent);
}

export function isRetiredFinishTruthPath(path: string): boolean {
  const normalized = path.trim();
  return CANONICAL_FINISH_RETIRED_PATHS.some((entry) => entry.retiredPath === normalized);
}

export function canonicalFinishEnumSummary(): {
  totalEntries: number;
  ownerConfirmedCount: number;
  blockedCount: number;
  cantCount: number;
  faceCount: number;
  artworkCount: number;
  retiredPathCount: number;
} {
  return {
    totalEntries: CANONICAL_FINISH_ENUM_MAP.length,
    ownerConfirmedCount: CANONICAL_FINISH_ENUM_MAP.filter(
      (e) => e.activationStatus === "owner_confirmed",
    ).length,
    blockedCount: CANONICAL_FINISH_ENUM_MAP.filter((e) => e.activationStatus === "blocked").length,
    cantCount: getCanonicalFinishEntriesBySurface("cant").length,
    faceCount: getCanonicalFinishEntriesBySurface("face").length,
    artworkCount: getCanonicalFinishEntriesBySurface("artwork").length,
    retiredPathCount: CANONICAL_FINISH_RETIRED_PATHS.length,
  };
}
