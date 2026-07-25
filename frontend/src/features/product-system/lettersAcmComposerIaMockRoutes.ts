import { buildProductSystemProductDetailPath } from "./productSystemRouteSync";

export const LETTERS_ACM_COMPOSER_STEP_ID = "composer-litere-acm" as const;

export function buildLettersAcmComposerPath(templateCode: string): string {
  return `${buildProductSystemProductDetailPath(templateCode)}/structure/${LETTERS_ACM_COMPOSER_STEP_ID}`;
}

export function isLettersAcmComposerStepId(value: string | undefined): boolean {
  return value === LETTERS_ACM_COMPOSER_STEP_ID;
}
