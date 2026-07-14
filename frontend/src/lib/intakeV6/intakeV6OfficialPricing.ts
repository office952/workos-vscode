import type { IntakeV6PricedQuoteDryRunResponse } from "@/lib/intakeV6/intakeV6PricedQuoteTypes";

export const V6_OFFICIAL_COMMERCIAL_AUTHORITY = "commercial_price_proposal_7g";

export function intakeV6HasOfficialCommercialTotals(
  pricing: IntakeV6PricedQuoteDryRunResponse | null | undefined,
): boolean {
  if (!pricing || pricing.pricing_status !== "V6_PRICED_DRY_RUN_READY") {
    return false;
  }
  if (pricing.pricing_authority !== V6_OFFICIAL_COMMERCIAL_AUTHORITY) {
    return false;
  }
  const totals = pricing.commercial_totals;
  return totals?.subtotal_net != null && totals?.total_gross != null;
}

export function intakeV6OfficialPricingBlockerMessage(
  pricing: IntakeV6PricedQuoteDryRunResponse | null | undefined,
): string | null {
  if (!pricing) return "Prețul comercial oficial nu este disponibil.";
  if (intakeV6HasOfficialCommercialTotals(pricing)) return null;
  const blockers = pricing.blockers ?? [];
  if (blockers.length > 0) return blockers[0]?.message ?? blockers[0]?.code ?? null;
  if (pricing.commercial_authority_status === "blocked") {
    return "Prețul comercial oficial este blocat — 7G nu a returnat un total valid.";
  }
  return "Prețul comercial oficial nu este disponibil.";
}
