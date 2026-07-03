/** Default when snapshot has no priced currency (legacy flat quotes). */
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
    ("cost_result" in obj || "pricing" in obj || "price" in obj)
  );
}

function extractSnapshotCurrency(snapshot: Record<string, unknown> | null): string | null {
  if (!snapshot) return null;
  const costResult = snapshot.cost_result;
  if (costResult && typeof costResult === "object" && !Array.isArray(costResult)) {
    const fromCost = normalizeCurrencyCode((costResult as Record<string, unknown>).currency);
    if (fromCost) return fromCost;
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
 * Read priced currency from quote.line_items JSON (cost_result.currency).
 * Does not convert — mirrors backend QuoteDocumentService snapshot read.
 */
export function extractQuoteCurrencyFromLineItems(raw?: string | null): string {
  if (!raw) return DEFAULT_QUOTE_CURRENCY;
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return DEFAULT_QUOTE_CURRENCY;
  }

  if (isCanonicalSnapshot(parsed)) {
    return extractSnapshotCurrency(parsed) ?? DEFAULT_QUOTE_CURRENCY;
  }

  if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
    const wrapper = parsed as Record<string, unknown>;
    const inner = wrapper.line_items;
    if (inner && typeof inner === "object" && !Array.isArray(inner) && isCanonicalSnapshot(inner)) {
      return extractSnapshotCurrency(inner as Record<string, unknown>) ?? DEFAULT_QUOTE_CURRENCY;
    }
    if (isCanonicalSnapshot(wrapper)) {
      return extractSnapshotCurrency(wrapper) ?? DEFAULT_QUOTE_CURRENCY;
    }
  }

  return DEFAULT_QUOTE_CURRENCY;
}

export function formatQuoteMoney(amount: number, currency: string): string {
  return `${amount.toLocaleString("ro-RO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${currency}`;
}

export function quoteCurrencyLabel(
  quotes: Array<{ currency?: string }>,
): { label: string; mixed: boolean } {
  const currencies = quotes.map((q) => q.currency ?? DEFAULT_QUOTE_CURRENCY);
  const unique = [...new Set(currencies)];
  if (unique.length === 1) {
    return { label: `${unique[0]} (cu TVA)`, mixed: false };
  }
  return { label: "valori în monede diferite", mixed: true };
}
