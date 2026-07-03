import { describe, expect, it } from "vitest";
import {
  buildQuoteWizardNavStateFromIntake,
  isTerminalClosedQuoteStatus,
  quoteDetailPath,
  resolveCreatedQuoteRouteId,
  terminalClosedQuoteMessage,
} from "@/lib/commercialSpineNavigation";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";

describe("commercialSpineNavigation", () => {
  it("builds wizard nav state from intake with volumetric template default", () => {
    const state = buildQuoteWizardNavStateFromIntake({
      id: "WI-SMOKE-P001",
      client: "TEST",
      status: "ready_for_quote",
      deliveryType: "courier",
      productSpec: { width_mm: 1000 },
      confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
      siteAudit: null,
    });
    expect(state.openWizard).toBe(true);
    expect(state.templateCode).toBe(TPL_VOLUMETRIC_LETTERS);
    expect(state.intakeRequestId).toBe("WI-SMOKE-P001");
    expect(state.fromIntake).toBe(true);
    expect(state.productSpec).toEqual({ width_mm: 1000 });
  });

  it("encodes quote detail path", () => {
    expect(quoteDetailPath("QT-2245")).toBe("/quotes/QT-2245");
  });

  it("prefers quote_code for created quote navigation", () => {
    expect(
      resolveCreatedQuoteRouteId({
        quoteId: 501,
        quoteCode: "Q-1781117536",
      })
    ).toBe("Q-1781117536");
    expect(
      resolveCreatedQuoteRouteId({
        quoteId: 501,
      })
    ).toBe("501");
  });

  it("identifies terminal closed quote statuses", () => {
    expect(isTerminalClosedQuoteStatus("rejected")).toBe(true);
    expect(isTerminalClosedQuoteStatus("expired")).toBe(true);
    expect(isTerminalClosedQuoteStatus("accepted")).toBe(false);
    expect(isTerminalClosedQuoteStatus("priced")).toBe(false);
  });

  it("returns Romanian terminal messages", () => {
    expect(terminalClosedQuoteMessage("rejected")).toContain("respinsă");
    expect(terminalClosedQuoteMessage("expired")).toContain("expirată");
  });
});
