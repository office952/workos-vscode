import { describe, expect, it } from "vitest";
import {
  acmInclusionStateLabelRo,
  acmInclusionStateTone,
  isAcmPricedIntoOffer,
  resolveAcmInclusionState,
} from "./inclusionState";

const ACM_TEMPLATE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";

function acmPayload(overrides: {
  mountingTemplateCode?: string | null;
  appliedContent?: unknown;
  appliedContentOn?: "top" | "finish_setup" | "product_composition_confirmed";
} = {}): Record<string, unknown> {
  const mountingTemplateCode =
    overrides.mountingTemplateCode === undefined ? ACM_TEMPLATE : overrides.mountingTemplateCode;
  const appliedContentOn = overrides.appliedContentOn ?? "finish_setup";
  const appliedContent = overrides.appliedContent === undefined ? "letters" : overrides.appliedContent;

  const finishSetup: Record<string, unknown> = {
    mounting_solution: mountingTemplateCode != null ? { template_code: mountingTemplateCode } : null,
  };
  const payload: Record<string, unknown> = { finish_setup: finishSetup };

  if (appliedContentOn === "top") payload.applied_content = appliedContent;
  if (appliedContentOn === "finish_setup") finishSetup.applied_content = appliedContent;
  if (appliedContentOn === "product_composition_confirmed") {
    payload.product_composition_confirmed = { confirmed: true, applied_content: appliedContent };
  }
  return payload;
}

describe("isAcmPricedIntoOffer", () => {
  it("is true when ACM boxed mounting carries applied_content=letters (mirrors CPP gate)", () => {
    expect(isAcmPricedIntoOffer(acmPayload())).toBe(true);
  });

  it("is false when mounting_solution is not the ACM boxed template", () => {
    expect(isAcmPricedIntoOffer(acmPayload({ mountingTemplateCode: "TPL-METAL-PREMOUNT-STRUCTURE_v1" }))).toBe(false);
  });

  it("is false when mounting_solution is missing entirely", () => {
    expect(isAcmPricedIntoOffer(acmPayload({ mountingTemplateCode: null }))).toBe(false);
  });

  it("is false when applied_content is none / panel-only", () => {
    expect(isAcmPricedIntoOffer(acmPayload({ appliedContent: "none" }))).toBe(false);
    expect(isAcmPricedIntoOffer(acmPayload({ appliedContent: "panel_only" }))).toBe(false);
  });

  it("is false when applied_content is logo, not letters", () => {
    expect(isAcmPricedIntoOffer(acmPayload({ appliedContent: "logo" }))).toBe(false);
  });

  it("falls back to product_composition_confirmed.applied_content when finish_setup bag is empty", () => {
    const payload = acmPayload({ appliedContentOn: "product_composition_confirmed" });
    expect(isAcmPricedIntoOffer(payload)).toBe(true);
  });

  it("is false for null/undefined payload", () => {
    expect(isAcmPricedIntoOffer(null)).toBe(false);
    expect(isAcmPricedIntoOffer(undefined)).toBe(false);
  });
});

describe("resolveAcmInclusionState", () => {
  it("is inactive when there is no ACM/support component at all", () => {
    const result = resolveAcmInclusionState({ payload: {}, hasComponent: false, blocked: false });
    expect(result.state).toBe("inactive");
    expect(result.pricedIntoOffer).toBe(false);
  });

  it("is selected_incomplete when the component exists but CPP does not price it yet", () => {
    const result = resolveAcmInclusionState({
      payload: acmPayload({ appliedContent: "none" }),
      hasComponent: true,
      blocked: false,
    });
    expect(result.state).toBe("selected_incomplete");
  });

  it("is active_priced when CPP prices the component and nothing is blocked", () => {
    const result = resolveAcmInclusionState({ payload: acmPayload(), hasComponent: true, blocked: false });
    expect(result.state).toBe("active_priced");
    expect(result.pricedIntoOffer).toBe(true);
  });

  it("is active_blocked when CPP would price it but an honesty/critical-field blocker exists", () => {
    const result = resolveAcmInclusionState({ payload: acmPayload(), hasComponent: true, blocked: true });
    expect(result.state).toBe("active_blocked");
    expect(result.pricedIntoOffer).toBe(true);
  });
});

describe("acm inclusion labels/tones", () => {
  it("never labels a non-priced state as cleanly included", () => {
    expect(acmInclusionStateLabelRo("selected_incomplete")).toMatch(/nu este încă inclus/i);
    expect(acmInclusionStateTone("selected_incomplete")).toBe("pending");
  });

  it("labels active_priced as included with an ok tone", () => {
    expect(acmInclusionStateLabelRo("active_priced")).toMatch(/inclus/i);
    expect(acmInclusionStateTone("active_priced")).toBe("ok");
  });

  it("labels active_blocked as a blocker, not a clean inclusion", () => {
    expect(acmInclusionStateTone("active_blocked")).toBe("blocker");
  });
});
