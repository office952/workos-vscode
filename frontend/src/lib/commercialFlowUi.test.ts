import { describe, expect, it } from "vitest";
import {
  COMMERCIAL_FLOW_STAGES,
  commercialFlowStageIndex,
  intakeListNextStepHint,
  productsNextStepHint,
  quoteStatusLabelRo,
} from "./commercialFlowUi";

describe("commercialFlowUi", () => {
  it("keeps Cereri → Produse → Oferte → Comenzi order", () => {
    expect(COMMERCIAL_FLOW_STAGES.map((s) => s.id)).toEqual([
      "cereri",
      "produse",
      "oferte",
      "comenzi",
    ]);
    expect(commercialFlowStageIndex("oferte")).toBe(2);
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
    expect(hint.title.toLowerCase()).toMatch(/ofert/);
  });

  it("keeps products next step pointing at quotes/intake only", () => {
    const hint = productsNextStepHint();
    expect(hint.primaryTo).toBe("/quotes");
    expect(hint.secondaryTo).toBe("/intake");
  });
});
