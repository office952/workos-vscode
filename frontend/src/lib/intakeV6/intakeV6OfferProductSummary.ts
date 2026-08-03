import type {
  IntakeV6CommercialProductBreakdown,
  IntakeV6CommercialProductSubtotal,
} from "@/lib/intakeV6/intakeV6PricedQuoteTypes";

export const OFFER_TOTAL_AVAILABLE_LABEL = "Total ofertă";
export const OFFER_TOTAL_UNAVAILABLE_LABEL = "Total ofertă indisponibil";
export const OFFER_CURRENCY_MIX_MESSAGE =
  "Tarife comerciale în monede diferite (EUR și RON). Nu convertim automat — cere Owner-ului tarifele comerciale în EUR sau un curs cu proveniență.";
export const OFFER_PRODUCT_BLOCKED_MESSAGE =
  "Un produs din ofertă este blocat comercial. Rezolvă blockerul înainte de total.";
export const OFFER_PRESENTATION_CURRENCY_UNAVAILABLE_MESSAGE =
  "Totalul ofertei nu poate fi afișat: o linie comercială nu respectă moneda de prezentare (EUR). Nu redenumim și nu convertim automat.";
export const OFFER_TOTAL_GENERIC_UNAVAILABLE_MESSAGE =
  "Totalul complet al ofertei nu poate fi exprimat onest. Verifică blockerii comerciali.";
export const OFFER_TAX_EXCLUSIVE_NOTE = "Prețuri fără TVA";

export const OFFER_TOTAL_PARTIAL_LABEL = "Total ofertă (parțial)";
export const OFFER_TOTAL_PARTIAL_MESSAGE =
  "Totalul nu include pozițiile fără tarif comercial confirmat de Owner.";

export type OfferTotalState =
  | {
      kind: "available";
      amount: number;
      currency: string;
      partial: boolean;
      pendingLineCodes: string[];
    }
  | { kind: "unavailable"; reasonCode: string | null; message: string };

export interface OfferProductRow {
  productKey: string;
  label: string;
  amounts: { currency: string; subtotal: number }[];
  blocked: boolean;
  blockerCodes: string[];
}

export interface OfferProductSummaryViewModel {
  products: OfferProductRow[];
  total: OfferTotalState;
  currencyMixDetected: boolean;
  taxNote: string;
  vatRatePercent: number | null;
}

const PRODUCT_SUBTOTAL_SHORT_LABELS: Record<string, string> = {
  letters: "Litere",
  acm_panel: "Panou ACM",
};

function normalizeCurrency(raw: string | null | undefined): string | null {
  if (typeof raw !== "string") return null;
  const value = raw.trim().toUpperCase();
  return value.length > 0 ? value : null;
}

function normalizeCodes(raw: unknown): string[] {
  if (!Array.isArray(raw)) return [];
  return raw.filter((code): code is string => typeof code === "string" && code.trim().length > 0);
}

function buildProductRow(product: IntakeV6CommercialProductSubtotal): OfferProductRow {
  const amounts = (Array.isArray(product.subtotals_by_currency) ? product.subtotals_by_currency : [])
    .flatMap((bucket) => {
      const currency = normalizeCurrency(bucket?.currency);
      const subtotal = bucket?.subtotal;
      if (currency == null || typeof subtotal !== "number" || !Number.isFinite(subtotal)) return [];
      return [{ currency, subtotal }];
    });
  return {
    productKey: product.product_key,
    label: product.label,
    amounts,
    blocked: product.blocked === true,
    blockerCodes: normalizeCodes(product.blocker_codes),
  };
}

function unavailableMessage(reasonCode: string | null, currencyMixDetected: boolean): string {
  if (reasonCode === "COMMERCIAL_CURRENCY_MIX_UNRESOLVED") return OFFER_CURRENCY_MIX_MESSAGE;
  if (reasonCode === "COMMERCIAL_PRESENTATION_CURRENCY_UNAVAILABLE") {
    return OFFER_PRESENTATION_CURRENCY_UNAVAILABLE_MESSAGE;
  }
  if (reasonCode === "COMMERCIAL_PRODUCT_BLOCKED") return OFFER_PRODUCT_BLOCKED_MESSAGE;
  if (currencyMixDetected) return OFFER_CURRENCY_MIX_MESSAGE;
  return OFFER_TOTAL_GENERIC_UNAVAILABLE_MESSAGE;
}

function buildTotalState(
  breakdown: IntakeV6CommercialProductBreakdown,
  products: OfferProductRow[],
): OfferTotalState {
  const reasonCode =
    typeof breakdown.complete_offer_total_unavailable_reason === "string" &&
    breakdown.complete_offer_total_unavailable_reason.trim().length > 0
      ? breakdown.complete_offer_total_unavailable_reason
      : null;
  const currency = normalizeCurrency(breakdown.complete_offer_total_currency);
  const amount = breakdown.complete_offer_total;
  const anyBlocked = products.some((product) => product.blocked);
  const honestTotal =
    reasonCode == null &&
    !anyBlocked &&
    breakdown.currency_mix_detected !== true &&
    currency != null &&
    typeof amount === "number" &&
    Number.isFinite(amount);

  if (honestTotal) {
    const pendingLineCodes = normalizeCodes(breakdown.pending_line_codes);
    return {
      kind: "available",
      amount: amount as number,
      currency: currency as string,
      // A total that silently omits unpriced lines would understate the offer.
      partial: breakdown.complete_offer_total_is_partial === true || pendingLineCodes.length > 0,
      pendingLineCodes,
    };
  }
  const effectiveReason =
    reasonCode ?? (anyBlocked ? "COMMERCIAL_PRODUCT_BLOCKED" : null);
  return {
    kind: "unavailable",
    reasonCode: effectiveReason,
    message: unavailableMessage(effectiveReason, breakdown.currency_mix_detected === true),
  };
}

/** Tax-exclusive note — never invents a VAT rate when the fiscal policy did not supply one. */
export function offerTaxNote(vatRatePercent: number | null): string {
  if (vatRatePercent == null || !Number.isFinite(vatRatePercent)) return OFFER_TAX_EXCLUSIVE_NOTE;
  const rate = vatRatePercent.toLocaleString("ro-RO", { maximumFractionDigits: 2 });
  return `${OFFER_TAX_EXCLUSIVE_NOTE} (TVA ${rate}% conform politicii fiscale)`;
}

/** ro-RO amount + explicit currency suffix. Currency is required — there is no default. */
export function formatOfferMoney(amount: number, currency: string): string {
  const normalizedCurrency = normalizeCurrency(currency);
  const value = Number.isFinite(amount)
    ? amount.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : "—";
  return normalizedCurrency ? `${value} ${normalizedCurrency}` : value;
}

/** "Subtotal Litere" / "Subtotal Panou ACM" — never "Total ofertă". */
export function offerSubtotalLabel(productKey: string, label: string): string {
  const short = PRODUCT_SUBTOTAL_SHORT_LABELS[productKey] ?? (label.trim() || productKey);
  return `Subtotal ${short}`;
}

/**
 * Presentation view model over the canonical backend breakdown.
 * Pure: selects and formats only — it never sums lines into a commercial total
 * and never converts currency.
 */
export function buildOfferProductSummary(
  breakdown: IntakeV6CommercialProductBreakdown | null | undefined,
): OfferProductSummaryViewModel | null {
  if (breakdown == null) return null;
  const products = (Array.isArray(breakdown.products) ? breakdown.products : []).map(buildProductRow);
  const vatRatePercent =
    typeof breakdown.vat_rate_percent === "number" && Number.isFinite(breakdown.vat_rate_percent)
      ? breakdown.vat_rate_percent
      : null;
  return {
    products,
    total: buildTotalState(breakdown, products),
    currencyMixDetected: breakdown.currency_mix_detected === true,
    taxNote: offerTaxNote(vatRatePercent),
    vatRatePercent,
  };
}
