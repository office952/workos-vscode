/**
 * Derived Ofertă lifecycle for Intake V6 Step 2 — no parallel money truth.
 * Status is presentation-only; amounts remain backend dry-run authority.
 */

export type IntakeV6OfferLifecyclePhase =
  | "idle"
  | "pending_save"
  | "saving"
  | "recalculating"
  | "updated"
  | "save_failed"
  | "reprice_failed";

export type IntakeV6OfferLifecycleView = {
  phase: IntakeV6OfferLifecyclePhase;
  /** Operator-facing Romanian label; null when idle (no chrome). */
  label: string | null;
  /** True when displayed offer money must not look current. */
  offerStale: boolean;
};

export function deriveIntakeV6OfferLifecycleStatus(args: {
  selectorPendingSave: boolean;
  commercialInputsPendingSave: boolean;
  saving: boolean;
  loadingPricedQuote: boolean;
  saveError: string | null | undefined;
  pricedQuoteError: string | null | undefined;
  recentlyUpdated: boolean;
}): IntakeV6OfferLifecycleView {
  const {
    selectorPendingSave,
    commercialInputsPendingSave,
    saving,
    loadingPricedQuote,
    saveError,
    pricedQuoteError,
    recentlyUpdated,
  } = args;

  const dirty = selectorPendingSave || commercialInputsPendingSave;

  if (saveError && !saving) {
    return { phase: "save_failed", label: "Salvare eșuată", offerStale: true };
  }
  if (pricedQuoteError && !dirty && !saving && !loadingPricedQuote) {
    return {
      phase: "reprice_failed",
      label: "Actualizare ofertă eșuată",
      offerStale: true,
    };
  }
  if (saving) {
    return { phase: "saving", label: "Se salvează…", offerStale: true };
  }
  if (dirty) {
    return { phase: "pending_save", label: "Se salvează…", offerStale: true };
  }
  if (loadingPricedQuote) {
    return { phase: "recalculating", label: "Recalculez oferta…", offerStale: true };
  }
  if (recentlyUpdated) {
    return { phase: "updated", label: "Ofertă actualizată", offerStale: false };
  }
  return { phase: "idle", label: null, offerStale: false };
}
