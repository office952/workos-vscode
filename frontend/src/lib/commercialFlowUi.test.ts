import { describe, expect, it } from "vitest";
import {
  COMMERCIAL_FLOW_STAGES,
  commercialFlowStageIndex,
  intakeListNextStepHint,
  productsNextStepHint,
  quoteStatusLabelRo,
} from "./commercialFlowUi";

describe("commercialFlowUi", () => {
  it("keeps Cereri → Oferte → Comenzi order without Product System", () => {
    expect(COMMERCIAL_FLOW_STAGES.map((s) => s.id)).toEqual([
      "cereri",
      "oferte",
      "comenzi",
    ]);
    expect(COMMERCIAL_FLOW_STAGES.map((s) => s.label)).toEqual([
      "Cereri",
      "Oferte",
      "Comenzi",
    ]);
    expect(COMMERCIAL_FLOW_STAGES.some((s) => s.path.includes("product-system"))).toBe(
      false,
    );
    expect(commercialFlowStageIndex("oferte")).toBe(1);
    expect(commercialFlowStageIndex("cereri")).toBe(0);
  });

  it("maps quote status to Romanian operator labels", () => {
    expect(quoteStatusLabelRo("draft")).toBe("Ciornă");
    expect(quoteStatusLabelRo("priced")).toBe("Tarifat");
    expect(quoteStatusLabelRo("accepted")).toBe("Acceptat");
    expect(quoteStatusLabelRo("unknown_x")).toBe("unknown_x");
  });

  it("gives ready_for_quote a clear offer next step without inventing mutation", () => {
    const hint = intakeListNextStepHint("ready_for_quote");
    expect(hint.primaryTo).toBe("/quotes");
    expect(hint.secondaryTo).toBe("/intake");
    expect(hint.title.toLowerCase()).toMatch(/ofert/);
    expect(JSON.stringify(hint)).not.toMatch(/product-system/);
  });

  it("does not send intake next-step through Product System", () => {
    for (const status of ["new", "in_review", "needs_info", "blocked", "unknown"]) {
      const hint = intakeListNextStepHint(status);
      expect(JSON.stringify(hint)).not.toMatch(/product-system/);
    }
  });

  it("keeps products next step pointing at quotes/intake only", () => {
    const hint = productsNextStepHint();
    expect(hint.primaryTo).toBe("/quotes");
    expect(hint.secondaryTo).toBe("/intake");
  });
});
