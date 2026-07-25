import { buildProductSystemProductDetailPath } from "./productSystemRouteSync";

/** Structure sub-path — prices page for Letters↔ACM connection. */
export const LETTERS_ACM_CONNECTION_PRICES_STEP_ID = "conexiune-litere-acm-preturi" as const;

export function buildLettersAcmConnectionPricesPath(templateCode: string): string {
  return `${buildProductSystemProductDetailPath(templateCode)}/structure/${LETTERS_ACM_CONNECTION_PRICES_STEP_ID}`;
}

export function isLettersAcmConnectionPricesStepId(value: string | undefined): boolean {
  return value === LETTERS_ACM_CONNECTION_PRICES_STEP_ID;
}
