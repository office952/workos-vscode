/**
 * Resolve /quotes/:quoteId against commercial code (QT-*) or numeric DB id.
 * Deep-links like /quotes/5 must match Quote.dbId when present.
 */

export type QuoteRouteMatchable = {
  id: string;
  dbId?: number | null;
};

export function matchQuoteByRouteParam<T extends QuoteRouteMatchable>(
  quotes: T[],
  param: string | undefined | null,
): T | undefined {
  if (!param) return undefined;
  const trimmed = param.trim();
  if (!trimmed) return undefined;

  const byCode = quotes.find((q) => q.id.toLowerCase() === trimmed.toLowerCase());
  if (byCode) return byCode;

  if (/^\d+$/.test(trimmed)) {
    const numericId = Number(trimmed);
    return quotes.find((q) => q.dbId != null && q.dbId === numericId);
  }

  return undefined;
}
