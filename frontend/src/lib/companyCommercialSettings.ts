/** Mirrors backend DEFAULT_VAT_PCT — fallback only when Settings API unavailable. */
export const DEFAULT_VAT_PCT = 21;
/**
 * Non-authoritative UI placeholder / demo seed example only.
 * Never treat as live configured commercial FX.
 */
export const DEFAULT_EUR_TO_RON_RATE = 5;

export function normalizeVatPct(value: number | null | undefined): number {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return DEFAULT_VAT_PCT;
  }
  return value;
}

/** Configured FX only — null when Settings has not saved an explicit rate. */
export function parseConfiguredEurToRonRate(
  value: number | null | undefined,
): number | null {
  if (value === null || value === undefined || Number.isNaN(value) || value <= 0) {
    return null;
  }
  return value;
}

/**
 * @deprecated Do not use for money authority — invents 5.0.
 * Prefer parseConfiguredEurToRonRate.
 */
export function normalizeEurToRonRate(value: number | null | undefined): number {
  const configured = parseConfiguredEurToRonRate(value);
  return configured ?? DEFAULT_EUR_TO_RON_RATE;
}
