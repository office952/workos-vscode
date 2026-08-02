import { describe, expect, it } from "vitest";
import {
  EXECUTION_FLOW_STAGES,
  controlProductionNextStepHint,
  executionDetailNextStepHint,
  executionFlowStageIndex,
  executionListNextStepHint,
  operatorCompatibilityHint,
  shopFloorNextStepHint,
} from "./executionFlowUi";

describe("executionFlowUi", () => {
  it("keeps Comenzi → Execuție → Atelier → Control order", () => {
    expect(EXECUTION_FLOW_STAGES.map((s) => s.id)).toEqual([
      "comenzi",
      "executie",
      "atelier",
      "control",
    ]);
    expect(executionFlowStageIndex("atelier")).toBe(2);
    expect(executionFlowStageIndex("operator")).toBe(2);
  });

  it("list hint links to shop floor and control without inventing mutations", () => {
    const hint = executionListNextStepHint();
    expect(hint.primaryTo).toBe("/shop-floor");
    expect(hint.secondaryTo).toBe("/dashboard");
    expect(hint.description.toLowerCase()).not.toMatch(/claim|schedule|salari/);
  });

  it("detail hint preserves identity gate messaging and operator query", () => {
    const hint = executionDetailNextStepHint(973019);
    expect(hint.primaryTo).toBe("/shop-floor");
    expect(hint.secondaryTo).toBe("/operator?orderId=973019");
    expect(hint.description.toLowerCase()).toMatch(/identitate/);
  });

  it("shop floor and control hints stay read/triage oriented", () => {
    expect(shopFloorNextStepHint().primaryTo).toBe("/operator");
    expect(controlProductionNextStepHint().primaryTo).toBe("/execution");
    expect(operatorCompatibilityHint(21).primaryTo).toBe("/execution/21");
  });
});
