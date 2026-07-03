/** Mirrors backend DEFAULT_VAT_PCT — fallback only when Settings API unavailable. */
export const DEFAULT_VAT_PCT = 21;
/** Seed/default only — runtime value comes from Settings API. */
export const DEFAULT_EUR_TO_RON_RATE = 5;

export function normalizeVatPct(value: number | null | undefined): number {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return DEFAULT_VAT_PCT;
  }
  return value;
}

export function normalizeEurToRonRate(value: number | null | undefined): number {
  if (value === null || value === undefined || Number.isNaN(value) || value <= 0) {
    return DEFAULT_EUR_TO_RON_RATE;
  }
  return value;
}
