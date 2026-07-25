/**
 * Dedicated structure-step detail pages for Letters (display documentation).
 * Structure list stays thin; detail lives on these routes.
 */
import { isVolumetricLettersTemplate } from "@/features/product-system/componentTypeDisplay";
import { isLettersBackForexStructureComponent } from "./lettersBackForexProcessDisplay";
import { isLettersFaceStructureComponent } from "./lettersFaceProcessDisplay";
import { isLettersLedStructureComponent } from "./lettersLedProcessDisplay";
import { isLettersVolumeAluminumStructureComponent } from "./lettersVolumeAluminumProcessDisplay";
import { buildProductSystemProductDetailPath } from "./productSystemRouteSync";

export const LETTERS_STRUCTURE_STEP_VIZUAL_FATA = "vizual-fata" as const;
export const LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU = "volum-aluminiu" as const;
export const LETTERS_STRUCTURE_STEP_CAPAC_SPATE = "capac-spate" as const;
export const LETTERS_STRUCTURE_STEP_SISTEM_LED = "sistem-led" as const;

export type LettersStructureStepId =
  | typeof LETTERS_STRUCTURE_STEP_VIZUAL_FATA
  | typeof LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU
  | typeof LETTERS_STRUCTURE_STEP_CAPAC_SPATE
  | typeof LETTERS_STRUCTURE_STEP_SISTEM_LED;

export function buildLettersStructureStepPath(
  templateCode: string,
  stepId: LettersStructureStepId,
): string {
  return `${buildProductSystemProductDetailPath(templateCode)}/structure/${stepId}`;
}

export function buildLettersVizualFataPath(templateCode: string): string {
  return buildLettersStructureStepPath(templateCode, LETTERS_STRUCTURE_STEP_VIZUAL_FATA);
}

export function buildLettersVolumAluminiuPath(templateCode: string): string {
  return buildLettersStructureStepPath(templateCode, LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU);
}

export function buildLettersCapacSpatePath(templateCode: string): string {
  return buildLettersStructureStepPath(templateCode, LETTERS_STRUCTURE_STEP_CAPAC_SPATE);
}

export function buildLettersSistemLedPath(templateCode: string): string {
  return buildLettersStructureStepPath(templateCode, LETTERS_STRUCTURE_STEP_SISTEM_LED);
}

type LettersStructureComponentRef = {
  type: string;
  component_id: string;
  name: string;
};

/**
 * Resolve dedicated detail path for a Letters structure component.
 * Used by list rows and construction-stage chips so both open the same page.
 */
export function resolveLettersStructureDetailPath(
  templateCode: string,
  component: LettersStructureComponentRef,
): string | null {
  if (!isVolumetricLettersTemplate(templateCode)) return null;
  if (isLettersFaceStructureComponent(component)) {
    return buildLettersVizualFataPath(templateCode);
  }
  if (isLettersVolumeAluminumStructureComponent(component)) {
    return buildLettersVolumAluminiuPath(templateCode);
  }
  if (isLettersBackForexStructureComponent(component)) {
    return buildLettersCapacSpatePath(templateCode);
  }
  if (isLettersLedStructureComponent(component)) {
    return buildLettersSistemLedPath(templateCode);
  }
  return null;
}
