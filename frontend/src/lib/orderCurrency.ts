/** Order commercial currency handoff parsed from order snapshot_line_items. */
export interface OrderCommercialCurrencyHandoff {
  commercial_currency: string;
  base_currency: string;
  commercial_total_eur?: number | null;
  commercial_total_eur_raw?: number;
  exchange_rate_eur_ron?: number | null;
  base_total_ron: number;
  base_total_net?: number | null;
}

export function roundCommercialTotalEur(amount: number): number {
  return Math.round(amount);
}

export function estimateOrderRonFromEurQuote(
  grandTotalEur: number,
  eurToRonRate: number
): number {
  const roundedEur = roundCommercialTotalEur(grandTotalEur);
  return Math.round(roundedEur * eurToRonRate * 100) / 100;
}

export function extractOrderCommercialHandoff(
  snapshotLineItems?: string | null
): OrderCommercialCurrencyHandoff | null {
  if (!snapshotLineItems) return null;
  try {
    const parsed = JSON.parse(snapshotLineItems) as {
      commercial_currency_handoff?: OrderCommercialCurrencyHandoff;
    };
    const handoff = parsed.commercial_currency_handoff;
    if (!handoff || typeof handoff.base_total_ron !== "number") return null;
    return handoff;
  } catch {
    return null;
  }
}

export function formatOrderMoney(amount: number, currency = "RON"): string {
  return `${amount.toLocaleString("ro-RO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${currency}`;
}

export function formatExchangeRate(rate: number): string {
  return rate.toLocaleString("ro-RO", {
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  });
}
