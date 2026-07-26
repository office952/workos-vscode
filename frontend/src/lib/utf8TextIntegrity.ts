/**
 * UTF-8 text integrity helpers for tests and development diagnostics.
 * Frontend renders backend Unicode as-is — this is not a runtime repair layer.
 */

const SUSPICIOUS_MOJIBAKE =
  /(?:Ä[ƒ„‚]|Ã[¢®îÎ‚]|È[™›˜š]|â€[”–’“„]|â€”|â€“|â€™|â€œ|�)/;

export function hasSuspiciousMojibake(value: string): boolean {
  if (!value) return false;
  return SUSPICIOUS_MOJIBAKE.test(value);
}

export function assertNoMojibake(value: string, context = ""): void {
  if (hasSuspiciousMojibake(value)) {
    const loc = context ? ` (${context})` : "";
    throw new Error(`Suspicious mojibake detected${loc}: ${JSON.stringify(value)}`);
  }
}

/** Development-only console diagnostic — never throws in production builds. */
export function warnMojibakeInDev(value: string, context = ""): void {
  if (import.meta.env.PROD) return;
  if (hasSuspiciousMojibake(value)) {
    // eslint-disable-next-line no-console
    console.warn(`[utf8] suspicious mojibake${context ? ` @ ${context}` : ""}:`, value);
  }
}
