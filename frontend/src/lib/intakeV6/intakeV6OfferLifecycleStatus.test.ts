import { describe, expect, it } from "vitest";
import { deriveIntakeV6OfferLifecycleStatus } from "./intakeV6OfferLifecycleStatus";

const base = {
  selectorPendingSave: false,
  commercialInputsPendingSave: false,
  saving: false,
  loadingPricedQuote: false,
  saveError: null as string | null,
  pricedQuoteError: null as string | null,
  recentlyUpdated: false,
};

describe("deriveIntakeV6OfferLifecycleStatus", () => {
  it("marks pending selector edits as saving/stale immediately", () => {
    const view = deriveIntakeV6OfferLifecycleStatus({
      ...base,
      selectorPendingSave: true,
    });
    expect(view.phase).toBe("pending_save");
    expect(view.label).toBe("Se salvează…");
    expect(view.offerStale).toBe(true);
  });

  it("shows saving while PUT is in flight", () => {
    const view = deriveIntakeV6OfferLifecycleStatus({
      ...base,
      saving: true,
    });
    expect(view.phase).toBe("saving");
    expect(view.offerStale).toBe(true);
  });

  it("shows recalculating while pricedQuote loads after save", () => {
    const view = deriveIntakeV6OfferLifecycleStatus({
      ...base,
      loadingPricedQuote: true,
    });
    expect(view.phase).toBe("recalculating");
    expect(view.label).toBe("Recalculez oferta…");
    expect(view.offerStale).toBe(true);
  });

  it("shows brief updated only when not stale and recentlyUpdated", () => {
    const view = deriveIntakeV6OfferLifecycleStatus({
      ...base,
      recentlyUpdated: true,
    });
    expect(view.phase).toBe("updated");
    expect(view.label).toBe("Ofertă actualizată");
    expect(view.offerStale).toBe(false);
  });

  it("does not show updated when save failed", () => {
    const view = deriveIntakeV6OfferLifecycleStatus({
      ...base,
      saveError: "boom",
      recentlyUpdated: true,
    });
    expect(view.phase).toBe("save_failed");
    expect(view.label).not.toBe("Ofertă actualizată");
    expect(view.offerStale).toBe(true);
  });

  it("does not show updated when pricedQuote failed", () => {
    const view = deriveIntakeV6OfferLifecycleStatus({
      ...base,
      pricedQuoteError: "dry-run failed",
      recentlyUpdated: true,
    });
    expect(view.phase).toBe("reprice_failed");
    expect(view.label).not.toBe("Ofertă actualizată");
    expect(view.offerStale).toBe(true);
  });

  it("prefers saving over recalculating while both true", () => {
    const view = deriveIntakeV6OfferLifecycleStatus({
      ...base,
      saving: true,
      loadingPricedQuote: true,
    });
    expect(view.phase).toBe("saving");
  });
});
