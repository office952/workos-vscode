/**
 * Dedicated structure-step detail routes for Alucobond casetat (display documentation).
 * Owner nucleus: Corp casetat + Structură metalică (not BOM slice cards).
 */
import {
  ACM_BOXED_MOUNTING_TEMPLATE_CODE,
  isAcmBoxedAssemblyStructureComponent,
  isAcmBoxedCasetareStructureComponent,
  isAcmBoxedFaceStructureComponent,
  isAcmBoxedMountingTemplate,
  type AcmBoxedStructureComponentRef,
} from "./acmBoxedTemplateIdentity";
import { buildProductSystemProductDetailPath } from "./productSystemRouteSync";

export const ACM_STRUCTURE_STEP_CORP_CASETAT = "corp-casetat" as const;
export const ACM_STRUCTURE_STEP_STRUCTURA_METALICA = "structura-metalica" as const;

/** Legacy 3-step UI — redirect into Corp casetat. */
export const ACM_STRUCTURE_STEP_LEGACY_FATA_PANOU = "fata-panou" as const;
export const ACM_STRUCTURE_STEP_LEGACY_CASETARE = "casetare" as const;
export const ACM_STRUCTURE_STEP_LEGACY_PRINDERI = "prinderi-asamblare" as const;

export type AcmBoxedStructureStepId =
  | typeof ACM_STRUCTURE_STEP_CORP_CASETAT
  | typeof ACM_STRUCTURE_STEP_STRUCTURA_METALICA;

export const ACM_BOXED_STRUCTURE_STEP_IDS: readonly AcmBoxedStructureStepId[] = [
  ACM_STRUCTURE_STEP_CORP_CASETAT,
  ACM_STRUCTURE_STEP_STRUCTURA_METALICA,
] as const;

const LEGACY_TO_CANONICAL: Record<string, AcmBoxedStructureStepId> = {
  [ACM_STRUCTURE_STEP_LEGACY_FATA_PANOU]: ACM_STRUCTURE_STEP_CORP_CASETAT,
  [ACM_STRUCTURE_STEP_LEGACY_CASETARE]: ACM_STRUCTURE_STEP_CORP_CASETAT,
  [ACM_STRUCTURE_STEP_LEGACY_PRINDERI]: ACM_STRUCTURE_STEP_CORP_CASETAT,
};

export function canonicalizeAcmBoxedStructureStepId(
  value: string | undefined,
): AcmBoxedStructureStepId | null {
  if (!value) return null;
  if (value === ACM_STRUCTURE_STEP_CORP_CASETAT || value === ACM_STRUCTURE_STEP_STRUCTURA_METALICA) {
    return value;
  }
  return LEGACY_TO_CANONICAL[value] ?? null;
}

export function isAcmBoxedStructureStepId(value: string | undefined): value is AcmBoxedStructureStepId {
  return canonicalizeAcmBoxedStructureStepId(value) != null;
}

export function buildAcmBoxedStructureStepPath(
  templateCode: string,
  stepId: AcmBoxedStructureStepId,
): string {
  return `${buildProductSystemProductDetailPath(templateCode)}/structure/${stepId}`;
}

export function buildAcmBoxedCorpCasetatPath(templateCode: string): string {
  return buildAcmBoxedStructureStepPath(templateCode, ACM_STRUCTURE_STEP_CORP_CASETAT);
}

export function buildAcmBoxedStructuraMetalicaPath(templateCode: string): string {
  return buildAcmBoxedStructureStepPath(templateCode, ACM_STRUCTURE_STEP_STRUCTURA_METALICA);
}

/**
 * Seed BOM comps (face / returns / fasteners) are decomposition of Corp casetat —
 * not separate Product Structure cards. All resolve to Corp detail.
 */
export function resolveAcmBoxedStructureDetailPath(
  templateCode: string,
  component: AcmBoxedStructureComponentRef,
): string | null {
  if (!isAcmBoxedMountingTemplate(templateCode)) return null;
  if (
    isAcmBoxedFaceStructureComponent(component) ||
    isAcmBoxedCasetareStructureComponent(component) ||
    isAcmBoxedAssemblyStructureComponent(component)
  ) {
    return buildAcmBoxedCorpCasetatPath(templateCode);
  }
  return null;
}

export { ACM_BOXED_MOUNTING_TEMPLATE_CODE };
