/**
 * FACE Component Truth Workshop v1 — readonly contract only.
 * Source: docs/worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md
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
  | "evidence_only";

export type FaceWorkshopEvidenceLevel =
  | "owner_decision_accepted"
  | "intake_v6_source"
  | "legacy_template_evidence"
  | "workshop_skeleton"
  | "none";

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
  consumerComponent: "RETURN-CANT" | "FINISH" | "BACK" | "LED";
  status: FaceWorkshopFieldStatus;
  notesRo: string;
};

export type FaceMaterialOptionEvidence = {
  materialFamily: string;
  status: "evidence_only" | "owner_input_required";
  evidenceSource: string;
  thicknessHints: readonly string[];
  notesRo: string;
};

export const FACE_COMPONENT_TEMPLATE_CODE = "TPL-COMP-LETTER-FACE_v1" as const;
export const FACE_LEGACY_TEMPLATE_CODE = "TPL-VOLUMETRIC-FACE_v1" as const;
export const FACE_WORKSHOP_STATUS = "owner_input_required" as const;

export const FACE_OWNER_TRUTH_FIELDS: readonly string[] = [
  "substrat față / material family",
  "grosime material față",
  "referință geometrie tăiere (cut path / contour)",
  "arie vizibilă față (mp_face_area)",
  "perimetru / lungime contur față",
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

export const FACE_FORBIDDEN_OWNERSHIP: readonly string[] = [
  "no face vinyl pricing",
  "no print/laminate pricing",
  "no cant finish",
  "no RAL minimum",
  "no pricing rates",
  "no Product Truth live write",
] as const;

export const FACE_DOWNSTREAM_OUTPUTS: readonly FaceDownstreamOutput[] = [
  {
    outputKey: "mp_face_area",
    labelRo: "Arie față (mp_face_area)",
    quantityBasis: "mp_face_area",
    consumerComponent: "FINISH",
    status: "owner_input_required",
    notesRo:
      "FINISH consumă mp_face_area pentru vinyl față și print/laminare. Exact handoff path pending.",
  },
  {
    outputKey: "face_perimeter",
    labelRo: "Perimetru / lungime contur față",
    quantityBasis: "ml_perimeter",
    consumerComponent: "RETURN-CANT",
    status: "partial_confirmed",
    notesRo:
      "RETURN-CANT consumă perimetrul faței pentru lungime cant — nu inventează propriul perimeter source.",
  },
  {
    outputKey: "face_geometry_ref",
    labelRo: "Referință geometrie față (contur SVG / layer refs)",
    quantityBasis: "geometry_ref",
    consumerComponent: "BACK",
    status: "partial_confirmed",
    notesRo: "BACK / LED pot depinde de geometrie față — contract separat, blocked.",
  },
] as const;

export const FACE_MATERIAL_FAMILY_EVIDENCE: readonly FaceMaterialOptionEvidence[] = [
  {
    materialFamily: "Plexiglas / acrilic",
    status: "evidence_only",
    evidenceSource:
      "componentFirstLettersProductTruthWorkshop skeleton question; intakeV6 plexiglas_face material key; VolumetricProductionGuidance",
    thicknessHints: ["3 mm", "5 mm", "10 mm"],
    notesRo: "Grosimi menționate în skeleton workshop — owner confirmation required.",
  },
  {
    materialFamily: "Forex",
    status: "evidence_only",
    evidenceSource: "componentFirstLettersProductTruthWorkshop BACK skeleton; intakeV6Review backing modes",
    thicknessHints: [],
    notesRo: "Forex apare la BACK/spate în surse — validitate pentru FACE neconfirmată.",
  },
  {
    materialFamily: "ACM / Bond",
    status: "evidence_only",
    evidenceSource: "ProductSystem ownership audit TPL-VOLUMETRIC-FACE_v1; mockData CL-ALU-PLEXI",
    thicknessHints: [],
    notesRo: "Evidență legacy/module — nu acceptat ca listă finală FACE.",
  },
] as const;

export const FACE_CUT_PROCESS_EVIDENCE: readonly {
  process: string;
  status: FaceWorkshopFieldStatus;
  evidenceSource: string;
  notesRo: string;
}[] = [
  {
    process: "CNC router (debitare_fata / face_cnc_cut)",
    status: "evidence_only",
    evidenceSource:
      "ProductSystem ownership audit operationSource debitare_fata; mockData face_cnc_cut; backend order_execution_snapshot_mapper",
    notesRo: "Proces documentat legacy — mapare per material/grosime pending owner.",
  },
  {
    process: "Laser",
    status: "owner_input_required",
    evidenceSource: null,
    notesRo: "Fără confirmare owner per material/grosime.",
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
    evidenceSource: "canonical_finish_enum_map_owner_decision_v1 + component-first set",
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
    evidenceLevel: "intake_v6_source",
    evidenceSource: "frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts — INTAKE_V6_OWNER_ROLE_LABEL_LETTERS",
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
    evidenceSource: "intakeV6 layer_role_setup; productTruth returnCantTruthFieldCaptureReadonlyAdapter vector_type",
    usedBy: ["RETURN-CANT", "FINISH", "BACK"],
    notesRo: "Handoff path exact pending — fără runtime bridge în acest task.",
    mustNotInvent: true,
  },
  {
    fieldKey: "face_area_output",
    labelRo: "Output arie față",
    status: "owner_input_required",
    value: "mp_face_area",
    truthPathPrefix: "product.components.face.area_m2",
    evidenceLevel: "owner_decision_accepted",
    evidenceSource: "canonicalFinishEnumMap quantityBasis mp_face_area",
    usedBy: ["FINISH face vinyl", "FINISH face print/laminate"],
    notesRo:
      "Regula globală nesting: de obicei bounding/out-of-box pe piese, nu raw area — exceptii LED de clarificat owner.",
    mustNotInvent: true,
  },
  {
    fieldKey: "face_perimeter_output",
    labelRo: "Output perimetru față",
    status: "partial_confirmed",
    value: "perimeter / contour length",
    truthPathPrefix: "product.components.face.confirmed_perimeter",
    evidenceLevel: "owner_decision_accepted",
    evidenceSource: "ProductSystem RETURN-CANT face dependency; returnCant owner inputs perimeter_geometry_source",
    usedBy: ["RETURN-CANT cant length"],
    notesRo: "Perimetrul faței este sursa upstream pentru cant — RETURN-CANT nu inventează.",
    mustNotInvent: true,
  },
  {
    fieldKey: "material_family_options",
    labelRo: "Familii material față",
    status: "owner_input_required",
    value: null,
    truthPathPrefix: "product.components.face.material",
    evidenceLevel: "workshop_skeleton",
    evidenceSource: "componentFirstLettersProductTruthWorkshop FACE skeleton question",
    usedBy: ["Pricing (future)", "ProductDefinition (future)"],
    notesRo: "Plexiglas 3/5/10 mm menționat în skeleton — evidence_only până la confirmare owner.",
    mustNotInvent: true,
  },
  {
    fieldKey: "material_thickness_options",
    labelRo: "Grosimi material față",
    status: "owner_input_required",
    value: null,
    truthPathPrefix: "product.components.face.thickness",
    evidenceLevel: "workshop_skeleton",
    evidenceSource: "componentFirstReadonlyProductTruthMapping face_thickness path",
    usedBy: ["Pricing (future)", "cut process selection"],
    notesRo: "Grosimi per material family — owner input required.",
    mustNotInvent: true,
  },
  {
    fieldKey: "cut_process",
    labelRo: "Proces tăiere",
    status: "owner_input_required",
    value: null,
    truthPathPrefix: "product.components.face.cutting_method",
    evidenceLevel: "legacy_template_evidence",
    evidenceSource: "ProductSystem ownership audit debitare_fata / face_cnc_cut",
    usedBy: ["Execution (future)"],
    notesRo: "CNC router documentat legacy — laser/other per material pending.",
    mustNotInvent: true,
  },
] as const;

export const FACE_READINESS_BLOCKERS: readonly string[] = [
  "Familii material față — confirmare owner sau cross-reference sursă",
  "Grosimi per material — confirmare owner sau cross-reference sursă",
  "Handoff path exact geometrie Intake V6 → FACE truth — neconectat",
  "Contract output mp_face_area / perimeter — nu live",
  "Chei pricing FACE — neactivate (fără inventare rate)",
  "Product Truth live write — blocked",
  "ProductDefinition bridge — blocked",
  "FINISH workshop — blocked până la stabilire boundary FACE",
  "Generic FINISH paths — retired conceptual (oracal_code, ral_code, stock_color, type)",
] as const;

export type FaceReadinessSummary = {
  workshopStatus: typeof FACE_WORKSHOP_STATUS;
  readyForPricing: false;
  productTruthLiveWriteBlocked: true;
  productDefinitionBridgeBlocked: true;
  finishWorkshopBlocked: true;
  workIntakeExposureBlocked: true;
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
  const ownerInputRequiredFieldCount = FACE_TRUTH_WORKSHOP_FIELDS.filter(
    (f) => f.status === "owner_input_required",
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
