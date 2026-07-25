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
  if (!pricing) return "Oferta client nu este disponibilă.";
  if (intakeV6HasOfficialCommercialTotals(pricing)) return null;
  const blockers = pricing.blockers ?? [];
  if (blockers.length > 0) return blockers[0]?.message ?? blockers[0]?.code ?? null;
  if (pricing.commercial_authority_status === "blocked") {
    return "Oferta client este blocată — 7G nu a returnat un total valid.";
  }
  return "Oferta client nu este disponibilă.";
}

/**
 * Operator-facing copy for offer rail / commercial sliders.
 * Keeps backend blocker codes/messages for diagnostics; never shows dry-run English in primary UI.
 */
export function intakeV6OperatorFacingPricingBlocker(
  message: string | null | undefined,
): string | null {
  if (!message) return null;
  const lower = message.toLowerCase();
  if (
    lower.includes("pricing input") ||
    lower.includes("not ready for dry-run") ||
    lower.includes("not ready for priced") ||
    lower.includes("dry-run") ||
    lower.includes("dry run")
  ) {
    return "Oferta client nu e gata încă — completează configurația și tarifele lipsă.";
  }
  if (
    lower.includes("compozit") ||
    lower.includes("composition") ||
    lower.includes("analyzer")
  ) {
    return "Preț disponibil după confirmarea produsului.";
  }
  if (lower.includes("7g")) {
    return "Oferta client este blocată — verifică liniile comerciale.";
  }
  if (message.length > 96) return `${message.slice(0, 93).trim()}…`;
  return message;
}

export function intakeV6OperatorFacingOfficialPricingBlocker(
  pricing: IntakeV6PricedQuoteDryRunResponse | null | undefined,
): string | null {
  return intakeV6OperatorFacingPricingBlocker(intakeV6OfficialPricingBlockerMessage(pricing));
}
