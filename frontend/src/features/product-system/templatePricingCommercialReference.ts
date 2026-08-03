/**
 * F7I — Product Template shows commercial reference readiness; catalog owns numeric rates.
 * Never display 0 as a stand-in for a missing Owner sell rate.
 */

import type { CommercialReferenceStatus } from "@/api/templatePricingRecipe";

export function commercialReferenceLabel(
  status: CommercialReferenceStatus | null | undefined,
): string | null {
  if (!status) return null;
  switch (status) {
    case "ACTIVE_PUBLISHED":
      return "Publicat (catalog)";
    case "ACTIVE_PROVISIONAL":
      return "Tarif provizoriu";
    case "ACTIVE_MISSING_RATE":
      return "Lipsă tarif Owner";
    case "BLOCKED_BY_POLICY":
      return "Blocat de politică";
    case "LEGACY_NOT_USED":
      return "Legacy (nefolosit)";
    case "NOT_APPLICABLE":
      return "N/A";
    case "INVALID_REFERENCE":
      return "Referință invalidă";
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

/** Whether the numeric rate may be shown (never invent / never show 0 for missing). */
export function shouldDisplayCommercialRateValue(args: {
  currentValue: number | null | undefined;
  commercialReferenceStatus?: CommercialReferenceStatus | null;
  status?: "active" | "missing" | "blocked" | "warning" | "inactive";
}): boolean {
  if (args.currentValue == null) return false;
  if (args.commercialReferenceStatus === "ACTIVE_MISSING_RATE") return false;
  if (args.status === "missing") return false;
  return true;
}
