/**
 * Local commercial preview for volumetric quote sidebar.
 * Mirrors QuoteOrchestrator._apply_commercial — UI-only; does not replace backend pricing.
 */

export interface CommercialPreviewBreakdown {
  productionCost: number;
  markupValue: number;
  priceBeforeVat: number;
  discountValue: number;
  subtotalBeforeVat: number;
  vatValue: number;
  totalWithVat: number;
}

function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}

export function computeCommercialPreviewBreakdown(params: {
  productionCost: number;
  marginPct: number;
  discountPct: number;
  vatPct: number;
}): CommercialPreviewBreakdown | null {
  const cost = params.productionCost;
  if (!Number.isFinite(cost) || cost <= 0) {
    return null;
  }

  const margin = Math.max(params.marginPct, 0) / 100;
  const discount = Math.max(params.discountPct, 0) / 100;
  const vat = Math.max(params.vatPct, 0) / 100;

  const markupValue = roundMoney(cost * margin);
  const priceBeforeVat = roundMoney(cost + markupValue);
  const discountValue = roundMoney(priceBeforeVat * discount);
  const subtotalBeforeVat = roundMoney(priceBeforeVat - discountValue);
  const vatValue = roundMoney(subtotalBeforeVat * vat);
  const totalWithVat = roundMoney(subtotalBeforeVat + vatValue);

  return {
    productionCost: roundMoney(cost),
    markupValue,
    priceBeforeVat,
    discountValue,
    subtotalBeforeVat,
    vatValue,
    totalWithVat,
  };
}
