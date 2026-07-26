/**
 * FACE Component Truth Workshop v1 — readonly contract only.
 * Owner decisions: docs/worklog/owner-input/face_component_truth_owner_decision_v1.md
 * Not runtime wiring. Not Product Truth write. Not Pricing activation.
 */

import {
  CANONICAL_FINISH_RETIRED_PATHS,
  getCanonicalFinishEntriesByOwner,
} from "./canonicalFinishEnumMap";

export type FaceWorkshopFieldStatus =
  | "owner_confirmed"
  | "partial_confirmed"
  | "owner_input_required"
  | "blocked_until_owner_decision"
  | "evidence_only"
  | "special_case_only";

export type FaceWorkshopEvidenceLevel =
  | "owner_decision_accepted"
  | "intake_v6_source"
  | "legacy_template_evidence"
  | "workshop_skeleton"
  | "none";

export type FaceMaterialFamilyDecision = {
  materialFamily: string;
  allowedForFaceStandard: boolean;
  specialCaseOnly: boolean;
  status: "owner_confirmed" | "owner_input_required";
  notesRo: string;
};

export type FaceThicknessDecision = {
  materialFamily: string;
  allowedThicknessesMm: readonly number[];
  defaultThicknessMm: number | null;
  optionalThicknessesMm: readonly number[];
  status: "owner_confirmed" | "special_case_only" | "not_applicable";
  notesRo: string;
};

export type FaceCutProcessDecision = {
  materialFamily: string;
  thicknessMm: number;
  process: "CNC router" | "laser" | "other";
  faceStandard: boolean;
  status: "owner_confirmed" | "special_case_only" | "not_face_standard";
  notesRo: string;
};

export type FaceTruthField = {
  fieldKey: string;
  labelRo: string;
  status: FaceWorkshopFieldStatus;
  value: string | null;
  truthPathPrefix: string | null;
  evidenceLevel: FaceWorkshopEvidenceLevel;
  evidenceSource: string | null;
  usedBy: readonly string[];
  notesRo: string;
  mustNotInvent: boolean;
};

export type FaceDownstreamOutput = {
  outputKey: string;
  labelRo: string;
  quantityBasis: string;
  consumerComponent: "RETURN-CANT" | "FINISH" | "BACK" | "LED" | "FACE";
  status: FaceWorkshopFieldStatus;
  notesRo: string;
};

export const FACE_COMPONENT_TEMPLATE_CODE = "TPL-COMP-LETTER-FACE_v1" as const;
export const FACE_LEGACY_TEMPLATE_CODE = "TPL-VOLUMETRIC-FACE_v1" as const;
export const FACE_WORKSHOP_STATUS = "partial_confirmed" as const;

export const FACE_NESTING_BASIS_RULE =
  "bounding/out-of-box per piece; not exact vector area; interior holes = negative holes, not separate nesting pieces" as const;

export const FACE_OWNER_TRUTH_FIELDS: readonly string[] = [
  "substrat față / material family",
  "grosime material față",
  "referință geometrie tăiere (cut path / contour)",
  "face_piece_boxes / face_material_usage_area_m2",
  "mp_face_area (FINISH quantity basis)",
  "face_perimeter_length_m (RETURN-CANT source)",
  "rol sursă layer: Vector Litere",
  "referințe layer selectate (selected_layer_refs)",
] as const;

export const FACE_DOES_NOT_OWN: readonly string[] = [
  "aplicare folie vinyl pe față (FINISH)",
  "print + laminare pe față (FINISH)",
  "finisaj artwork / Vector Logo (FINISH)",
  "finisaj cant: Stock / Oracal / RAL (RETURN-CANT)",
  "material cant / adâncime cant (RETURN-CANT)",
  "politică minim 100 lei RAL (RETURN-CANT)",
  "rate preț / EUR literals (Pricing Registry)",
  "minime comerciale (CPP owner policy — nu FACE)",
  "task-uri runtime execuție",
  "Product Truth live write",
  "ProductDefinition bridge",
  "Work Intake exposure",
] as const;

export const FACE_DOES_NOT_OWN_CONFIRMED = true as const;

export const FACE_FORBIDDEN_OWNERSHIP: readonly string[] = [
  "no face vinyl pricing",
  "no print/laminate pricing",
  "no cant finish",
  "no RAL minimum",
  "no pricing rates",
  "no Product Truth live write",
] as const;

export const FACE_MATERIAL_FAMILY_DECISIONS: readonly FaceMaterialFamilyDecision[] = [
  {
    materialFamily: "Plexiglas / acrilic",
    allowedForFaceStandard: true,
    specialCaseOnly: false,
    status: "owner_confirmed",
    notesRo: "Material față standard litere volumetrice.",
  },
  {
    materialFamily: "Forex",
    allowedForFaceStandard: false,
    specialCaseOnly: true,
    status: "owner_confirmed",
    notesRo: "Nu FACE standard momentan; doar caz special owner sau BACK/suport.",
  },
  {
    materialFamily: "ACM / Bond / Dibond",
    allowedForFaceStandard: false,
    specialCaseOnly: true,
    status: "owner_confirmed",
    notesRo: "Backing / suport / panouri — nu FACE standard.",
  },
  {
    materialFamily: "Other",
    allowedForFaceStandard: false,
    specialCaseOnly: false,
    status: "owner_input_required",
    notesRo: "Alte materiale — owner input required.",
  },
] as const;

export const FACE_THICKNESS_DECISIONS: readonly FaceThicknessDecision[] = [
  {
    materialFamily: "Plexiglas / acrilic",
    allowedThicknessesMm: [3, 5, 10],
    defaultThicknessMm: 3,
    optionalThicknessesMm: [5, 10],
    status: "owner_confirmed",
    notesRo: "3 mm default; 5 / 10 mm opționale — confirmare owner înainte de pricing.",
  },
  {
    materialFamily: "Forex",
    allowedThicknessesMm: [],
    defaultThicknessMm: null,
    optionalThicknessesMm: [],
    status: "not_applicable",
    notesRo: "Nu pentru FACE standard.",
  },
  {
    materialFamily: "ACM / Bond / Dibond",
    allowedThicknessesMm: [],
    defaultThicknessMm: null,
    optionalThicknessesMm: [],
    status: "not_applicable",
    notesRo: "Nu pentru FACE standard.",
  },
] as const;

export const FACE_CUT_PROCESS_DECISIONS: readonly FaceCutProcessDecision[] = [
  {
    materialFamily: "Plexiglas / acrilic",
    thicknessMm: 3,
    process: "CNC router",
    faceStandard: true,
    status: "owner_confirmed",
    notesRo: "Standard FACE debitare.",
  },
  {
    materialFamily: "Plexiglas / acrilic",
    thicknessMm: 5,
    process: "CNC router",
    faceStandard: false,
    status: "special_case_only",
    notesRo: "Opțional — confirmare owner înainte de pricing.",
  },
  {
    materialFamily: "Plexiglas / acrilic",
    thicknessMm: 10,
    process: "CNC router",
    faceStandard: false,
    status: "special_case_only",
    notesRo: "Caz special.",
  },
  {
    materialFamily: "Forex",
    thicknessMm: 10,
    process: "CNC router",
    faceStandard: false,
    status: "not_face_standard",
    notesRo: "Nu FACE standard; BACK/suport — confirmare separată.",
  },
  {
    materialFamily: "ACM / Bond / Dibond",
    thicknessMm: 3,
    process: "CNC router",
    faceStandard: false,
    status: "not_face_standard",
    notesRo: "Panou/backing/suport — nu FACE standard.",
  },
] as const;

export const FACE_DOWNSTREAM_OUTPUTS: readonly FaceDownstreamOutput[] = [
  {
    outputKey: "face_piece_boxes",
    labelRo: "Cutii piesă față (face_piece_boxes)",
    quantityBasis: "bounding_box_per_piece",
    consumerComponent: "FACE",
    status: "owner_confirmed",
    notesRo: "Bounding/out-of-box per piece; interior holes negative, not separate pieces.",
  },
  {
    outputKey: "face_material_usage_area_m2",
    labelRo: "Arie material față (face_material_usage_area_m2)",
    quantityBasis: "sum_of_piece_boxes",
    consumerComponent: "FACE",
    status: "owner_confirmed",
    notesRo: "Din cutii piesă — nu arie vectorială exactă.",
  },
  {
    outputKey: "face_perimeter_length_m",
    labelRo: "Perimetru față (face_perimeter_length_m)",
    quantityBasis: "ml_perimeter",
    consumerComponent: "RETURN-CANT",
    status: "owner_confirmed",
    notesRo: "Sursă autoritară cant length; RETURN-CANT nu inventează perimetru.",
  },
  {
    outputKey: "mp_face_area",
    labelRo: "Arie față FINISH (mp_face_area)",
    quantityBasis: "mp_face_area",
    consumerComponent: "FINISH",
    status: "owner_confirmed",
    notesRo: "FINISH consumă pentru vinyl față și print/laminare. Handoff path runtime pending.",
  },
  {
    outputKey: "source_layer_role",
    labelRo: "Rol sursă layer (Vector Litere)",
    quantityBasis: "layer_role",
    consumerComponent: "FACE",
    status: "owner_confirmed",
    notesRo: "Vector Litere — nu Vector Logo.",
  },
  {
    outputKey: "face_geometry_ref",
    labelRo: "Referință geometrie față (contur SVG / layer refs)",
    quantityBasis: "geometry_ref",
    consumerComponent: "BACK",
    status: "partial_confirmed",
    notesRo: "BACK / LED — contract separat; handoff runtime pending.",
  },
] as const;

export const FACE_TRUTH_WORKSHOP_FIELDS: readonly FaceTruthField[] = [
  {
    fieldKey: "component_identity",
    labelRo: "Identitate componentă",
    status: "owner_confirmed",
    value: FACE_COMPONENT_TEMPLATE_CODE,
    truthPathPrefix: "product.components.face",
    evidenceLevel: "owner_decision_accepted",
    evidenceSource: "face_component_truth_owner_decision_v1",
    usedBy: ["Product System", "ProductDefinition (future)"],
    notesRo: "Față literă vizibilă — substrat și geometrie.",
    mustNotInvent: false,
  },
  {
    fieldKey: "source_layer_role",
    labelRo: "Rol sursă layer",
    status: "owner_confirmed",
    value: "Vector Litere",
    truthPathPrefix: "product.components.face.selected_layer_refs",
    evidenceLevel: "owner_decision_accepted",
    evidenceSource: "face_component_truth_owner_decision_v1 §F",
    usedBy: ["Intake V6", "FACE geometry source"],
    notesRo: "Geometria faței vine din layer Vector Litere, nu Vector Logo.",
    mustNotInvent: false,
  },
  {
    fieldKey: "geometry_source",
    labelRo: "Sursă geometrie",
    status: "partial_confirmed",
    value: "SVG layer / vector contour din Intake V6 / Vector Litere",
    truthPathPrefix: "product.components.face.geometry",
    evidenceLevel: "intake_v6_source",
    evidenceSource: "intakeV6 layer_role_setup",
    usedBy: ["RETURN-CANT", "FINISH", "BACK"],
    notesRo: "Handoff path exact runtime — încă neconectat.",
    mustNotInvent: true,
  },
  {
    fieldKey: "material_nesting_basis",
    labelRo: "Bază material / nesting",
    status: "owner_confirmed",
    value: FACE_NESTING_BASIS_RULE,
    truthPathPrefix: "product.components.face.piece_boxes",
    evidenceLevel: "owner_decision_accepted",
    evidenceSource: "face_component_truth_owner_decision_v1 §C",
    usedBy: ["FACE material usage", "face_material_usage_area_m2"],
    notesRo: "Excepții doar cu confirmare owner explicită.",
    mustNotInvent: false,
  },
  {
    fieldKey: "face_area_output",
    labelRo: "Output arie față FINISH",
    status: "owner_confirmed",
    value: "mp_face_area",
    truthPathPrefix: "product.components.face.area_m2",
    evidenceLevel: "owner_decision_accepted",
    evidenceSource: "face_component_truth_owner_decision_v1 §F",
    usedBy: ["FINISH face vinyl", "FINISH face print/laminate"],
    notesRo: "Quantity basis FINISH — separat de face_material_usage_area_m2 dacă reguli diferă.",
    mustNotInvent: false,
  },
  {
    fieldKey: "face_perimeter_output",
    labelRo: "Output perimetru față",
    status: "owner_confirmed",
    value: "face_perimeter_length_m",
    truthPathPrefix: "product.components.face.confirmed_perimeter",
    evidenceLevel: "owner_decision_accepted",
    evidenceSource: "face_component_truth_owner_decision_v1 §D",
    usedBy: ["RETURN-CANT cant length"],
    notesRo: "RETURN-CANT consumă; nu inventează perimetru.",
    mustNotInvent: false,
  },
  {
    fieldKey: "material_family_options",
    labelRo: "Familii material față",
    status: "owner_confirmed",
    value: "Plexiglas/acrylic YES; Forex/ACM/Bond NO (standard)",
    truthPathPrefix: "product.components.face.material",
    evidenceLevel: "owner_decision_accepted",
    evidenceSource: "face_component_truth_owner_decision_v1 §A",
    usedBy: ["Pricing (future)", "ProductDefinition (future)"],
    notesRo: "Forex/ACM doar caz special owner sau backing.",
    mustNotInvent: false,
  },
  {
    fieldKey: "material_thickness_options",
    labelRo: "Grosimi material față",
    status: "owner_confirmed",
    value: "Plexiglas: 3 mm default; 5/10 mm opțional cu confirmare pre-pricing",
    truthPathPrefix: "product.components.face.thickness",
    evidenceLevel: "owner_decision_accepted",
    evidenceSource: "face_component_truth_owner_decision_v1 §B",
    usedBy: ["Pricing (future)", "cut process selection"],
    notesRo: "5 / 10 mm = special_case_only până la confirmare explicită per job.",
    mustNotInvent: false,
  },
  {
    fieldKey: "cut_process",
    labelRo: "Proces tăiere",
    status: "owner_confirmed",
    value: "Plexiglas 3/5/10 mm → CNC router (5/10 special)",
    truthPathPrefix: "product.components.face.cutting_method",
    evidenceLevel: "owner_decision_accepted",
    evidenceSource: "face_component_truth_owner_decision_v1 §E",
    usedBy: ["Execution (future)"],
    notesRo: "Forex/ACM rows = not_face_standard.",
    mustNotInvent: false,
  },
] as const;

export const FACE_READINESS_BLOCKERS: readonly string[] = [
  "Handoff path exact geometrie Intake V6 → FACE truth — neconectat (runtime)",
  "Contract outputs — nu live în Product Truth",
  "Plexiglas 5 / 10 mm — confirmare owner per job înainte de pricing",
  "Owner estimate drafts (material/CNC) — NOT Pricing Registry authority; not active",
  "Product Truth live write — blocked",
  "ProductDefinition bridge — blocked",
  "FINISH workshop — slice separat (FACE core boundary owner-confirmed)",
  "Work Intake exposure — blocked",
  "Generic FINISH paths — retired conceptual only",
] as const;

export type FaceReadinessSummary = {
  workshopStatus: typeof FACE_WORKSHOP_STATUS;
  readyForPricing: false;
  productTruthLiveWriteBlocked: true;
  productDefinitionBridgeBlocked: true;
  finishWorkshopBlocked: true;
  workIntakeExposureBlocked: true;
  doesNotOwnConfirmed: true;
  ownerConfirmedFieldCount: number;
  ownerInputRequiredFieldCount: number;
  partialConfirmedFieldCount: number;
  downstreamOutputCount: number;
  readinessBlockerCount: number;
  retiredGenericFinishPathCount: number;
  blockedFinishEntryCount: number;
};

export function buildFaceReadinessSummary(): FaceReadinessSummary {
  const ownerConfirmedFieldCount = FACE_TRUTH_WORKSHOP_FIELDS.filter(
    (f) => f.status === "owner_confirmed",
  ).length;
  const ownerInputRequiredFieldCount = FACE_MATERIAL_FAMILY_DECISIONS.filter(
    (d) => d.status === "owner_input_required",
  ).length;
  const partialConfirmedFieldCount = FACE_TRUTH_WORKSHOP_FIELDS.filter(
    (f) => f.status === "partial_confirmed",
  ).length;
  const blockedFinishEntryCount = getCanonicalFinishEntriesByOwner("FINISH").filter(
    (e) => e.surfaceTarget === "face" || e.surfaceTarget === "artwork",
  ).length;

  return {
    workshopStatus: FACE_WORKSHOP_STATUS,
    readyForPricing: false,
    productTruthLiveWriteBlocked: true,
    productDefinitionBridgeBlocked: true,
    finishWorkshopBlocked: true,
    workIntakeExposureBlocked: true,
    doesNotOwnConfirmed: FACE_DOES_NOT_OWN_CONFIRMED,
    ownerConfirmedFieldCount,
    ownerInputRequiredFieldCount,
    partialConfirmedFieldCount,
    downstreamOutputCount: FACE_DOWNSTREAM_OUTPUTS.length,
    readinessBlockerCount: FACE_READINESS_BLOCKERS.length,
    retiredGenericFinishPathCount: CANONICAL_FINISH_RETIRED_PATHS.length,
    blockedFinishEntryCount,
  };
}

export function getFaceTruthField(fieldKey: string): FaceTruthField | null {
  return FACE_TRUTH_WORKSHOP_FIELDS.find((f) => f.fieldKey === fieldKey) ?? null;
}

export function getFaceDownstreamOutput(outputKey: string): FaceDownstreamOutput | null {
  return FACE_DOWNSTREAM_OUTPUTS.find((o) => o.outputKey === outputKey) ?? null;
}

export const FACE_READINESS_SUMMARY = buildFaceReadinessSummary();
