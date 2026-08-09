/**
 * Quote commercial currency helpers.
 * Never invent FX. Never guess EUR on historical records.
 * Missing snapshot currency → null; operator UI uses neutral "—" (no technical jargon).
 */

/** Neutral operator presentation when amount/currency provenance is unavailable. */
export const NEUTRAL_MONEY_UNAVAILABLE = "—";

/** @deprecated Prefer null / unavailable when snapshot has no currency. Kept for legacy callers. */
export const DEFAULT_QUOTE_CURRENCY = "RON";

function normalizeCurrencyCode(raw: unknown): string | null {
  if (typeof raw !== "string" || !raw.trim()) return null;
  const upper = raw.trim().toUpperCase();
  if (upper === "LEI") return "RON";
  return upper;
}

function isCanonicalSnapshot(obj: unknown): obj is Record<string, unknown> {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return false;
  return (
    "product_definition" in obj &&
    ("cost_result" in obj || "pricing" in obj || "price" in obj || "commercial_totals" in obj)
  );
}

function extractSnapshotCurrency(snapshot: Record<string, unknown> | null): string | null {
  if (!snapshot) return null;

  const commercialTotals = snapshot.commercial_totals;
  if (commercialTotals && typeof commercialTotals === "object" && !Array.isArray(commercialTotals)) {
    const fromTotals = normalizeCurrencyCode((commercialTotals as Record<string, unknown>).currency);
    if (fromTotals) return fromTotals;
  }

  const topCurrency = normalizeCurrencyCode(snapshot.currency);
  if (topCurrency) return topCurrency;

  const costResult = snapshot.cost_result;
  if (costResult && typeof costResult === "object" && !Array.isArray(costResult)) {
    const fromCost = normalizeCurrencyCode((costResult as Record<string, unknown>).currency);
    if (fromCost) return fromCost;
  }

  const pricing = snapshot.pricing;
  if (pricing && typeof pricing === "object" && !Array.isArray(pricing)) {
    const fromPricing = normalizeCurrencyCode((pricing as Record<string, unknown>).currency);
    if (fromPricing) return fromPricing;
  }

  const productDefinition = snapshot.product_definition;
  if (productDefinition && typeof productDefinition === "object" && !Array.isArray(productDefinition)) {
    const pricingContext = (productDefinition as Record<string, unknown>).pricing_context;
    if (pricingContext && typeof pricingContext === "object" && !Array.isArray(pricingContext)) {
      const fromContext = normalizeCurrencyCode((pricingContext as Record<string, unknown>).currency);
      if (fromContext) return fromContext;
    }
  }
  return null;
}

/**
 * Read priced currency from quote.line_items JSON.
 * Returns null when unavailable — callers must not invent RON/EUR.
 */
export function extractQuoteCurrencyFromLineItems(raw?: string | null): string | null {
  if (!raw) return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }

  if (isCanonicalSnapshot(parsed)) {
    return extractSnapshotCurrency(parsed);
  }

  if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
    const wrapper = parsed as Record<string, unknown>;
    const fromWrapperCommercial = extractSnapshotCurrency(wrapper);
    if (fromWrapperCommercial) return fromWrapperCommercial;

    const inner = wrapper.line_items;
    if (inner && typeof inner === "object" && !Array.isArray(inner)) {
      const fromInner = extractSnapshotCurrency(inner as Record<string, unknown>);
      if (fromInner) return fromInner;
      if (isCanonicalSnapshot(inner)) {
        return extractSnapshotCurrency(inner as Record<string, unknown>);
      }
    }
    if (isCanonicalSnapshot(wrapper)) {
      return extractSnapshotCurrency(wrapper);
    }
  }

  return null;
}

/**
 * Read V6 commercial currency from quote.notes provenance.
 * Prefers commercial_adjustment_trace.currency, then write-trace currency.
 * Never invents EUR/RON when provenance is absent.
 */
export function extractQuoteCurrencyFromNotes(raw?: string | null): string | null {
  if (!raw) return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
  const notes = parsed as Record<string, unknown>;
  const adj = notes.commercial_adjustment_trace;
  if (adj && typeof adj === "object" && !Array.isArray(adj)) {
    const fromAdj = normalizeCurrencyCode((adj as Record<string, unknown>).currency);
    if (fromAdj) return fromAdj;
  }
  const linkage = notes.intake_v6_linkage_v1;
  if (linkage && typeof linkage === "object" && !Array.isArray(linkage)) {
    const write = (linkage as Record<string, unknown>).intake_v6_priced_quote_write_v1;
    if (write && typeof write === "object" && !Array.isArray(write)) {
      const writeObj = write as Record<string, unknown>;
      const writeAdj = writeObj.commercial_adjustment_trace;
      if (writeAdj && typeof writeAdj === "object" && !Array.isArray(writeAdj)) {
        const fromWriteAdj = normalizeCurrencyCode((writeAdj as Record<string, unknown>).currency);
        if (fromWriteAdj) return fromWriteAdj;
      }
      const fromWrite = normalizeCurrencyCode(writeObj.currency);
      if (fromWrite) return fromWrite;
    }
  }
  return null;
}

/** Prefer line_items snapshot currency; fall back to V6 notes provenance. */
export function extractQuoteCurrency(lineItemsRaw?: string | null, notesRaw?: string | null): string | null {
  return extractQuoteCurrencyFromLineItems(lineItemsRaw) ?? extractQuoteCurrencyFromNotes(notesRaw);
}

export function formatQuoteMoney(amount: number, currency: string): string {
  return `${amount.toLocaleString("ro-RO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${currency}`;
}

/**
 * Official commercial amount + currency from backend; no currency invent.
 * Missing currency → neutral em dash (do not pair a raw amount with technical jargon).
 */
export function formatCommercialAmount(
  amount: number | null | undefined,
  currency: string | null | undefined,
): string {
  if (amount == null || !Number.isFinite(amount)) return NEUTRAL_MONEY_UNAVAILABLE;
  const code = normalizeCurrencyCode(currency);
  if (!code) return NEUTRAL_MONEY_UNAVAILABLE;
  return formatQuoteMoney(amount, code);
}

export function quoteCurrencyLabel(
  quotes: Array<{ currency?: string | null }>,
): { label: string; mixed: boolean } {
  const currencies = quotes
    .map((q) => normalizeCurrencyCode(q.currency))
    .filter((c): c is string => Boolean(c));
  if (currencies.length === 0) {
    return { label: NEUTRAL_MONEY_UNAVAILABLE, mixed: false };
  }
  const unique = [...new Set(currencies)];
  if (unique.length === 1) {
    return { label: `${unique[0]} (cu TVA)`, mixed: false };
  }
  return { label: "valori în monede diferite — total agregat indisponibil", mixed: true };
}

/** Never show a cross-currency sum as a single money figure. */
export function formatQuoteListKpiAmount(
  amount: number,
  currencyMeta: { mixed: boolean; label: string },
  formatAmount: (n: number) => string,
): string {
  if (currencyMeta.mixed) return NEUTRAL_MONEY_UNAVAILABLE;
  if (currencyMeta.label === NEUTRAL_MONEY_UNAVAILABLE) return NEUTRAL_MONEY_UNAVAILABLE;
  return formatAmount(amount);
}
