import { describe, expect, it } from "vitest";
import {
  buildReturnCantOwnerApplyPlan,
  RETURN_CANT_APPLY_PLAN_SAFETY,
  RETURN_CANT_OWNER_ANSWER_TOPICS,
  contractStatusForTopic,
} from "./componentFirstReturnCantOwnerApplyPlan";
import { RETURN_CANT_OWNER_INPUTS } from "./componentFirstReturnCantOwnerInputs";

describe("componentFirstReturnCantOwnerApplyPlan", () => {
  it("reports owner answers found after apply v2", () => {
    const plan = buildReturnCantOwnerApplyPlan();
    expect(plan.answersFound).toBe(true);
    expect(plan.answersSource).toBe("owner_prompt");
    expect(plan.topicsAnswered).toBeGreaterThan(0);
    expect(plan.topicsPartial).toBe(2);
    expect(plan.topicsPending).toBe(1);
    expect(plan.globalWorkshopStatus).toBe("OWNER_INPUT_REQUIRED");
  });

  it("lists applied contract keys from answered topics", () => {
    const plan = buildReturnCantOwnerApplyPlan();
    expect(plan.contractKeysReadyToApply).toContain("oracal_selector_mode");
    expect(plan.contractKeysReadyToApply).toContain("oracal_pricing_mode");
    expect(plan.contractKeysReadyToApply).toContain("ral_input_mode");
    expect(plan.contractKeysReadyToApply).toContain("return_depths_standard");
    expect(plan.contractKeysReadyToApply).toContain("return_material");
    expect(plan.contractKeysReadyToApply).toContain("stock_color_affects_price");
    expect(plan.contractKeysReadyToApply).toContain("perimeter_geometry_source");
  });

  it("lists catalog and pricing keys still pending or partial", () => {
    const plan = buildReturnCantOwnerApplyPlan();
    expect(plan.contractKeysStillPending).not.toContain("ral_selector_source");
    expect(plan.contractKeysStillPending).not.toContain("material_depth_compatibility");
    expect(plan.contractKeysStillPending).not.toContain("ral_material_price_rule");
    expect(plan.contractKeysStillPending).not.toContain("ral_labor_price_rule");
  });

  it("reflects confirmed and partial contract statuses", () => {
    expect(contractStatusForTopic("oracal_selector_mode")).toBe("owner_confirmed");
    expect(contractStatusForTopic("ral_selector_source")).toBe("owner_confirmed");
    expect(contractStatusForTopic("ral_material_price_rule")).toBe("owner_confirmed");
    expect(contractStatusForTopic("minimum_price_rule")).toBe("partial_confirmed");
    expect(contractStatusForTopic("material_depth_compatibility")).toBe("owner_confirmed");
  });

  it("documents apply safety guards", () => {
    expect(RETURN_CANT_APPLY_PLAN_SAFETY.join(" ")).toMatch(/no Product Truth live write/i);
    expect(RETURN_CANT_APPLY_PLAN_SAFETY.join(" ")).toMatch(/No Pricing activation/i);
  });

  it("would apply only explicitly answered topics in isolation", () => {
    const withOneAnswer = RETURN_CANT_OWNER_ANSWER_TOPICS.map((t) =>
      t.contractKeys.includes("oracal_selector_mode") ? { ...t, docStatus: "answered" as const } : t,
    );
    const plan = buildReturnCantOwnerApplyPlan(withOneAnswer);
    expect(plan.contractKeysReadyToApply).toContain("oracal_selector_mode");
  });
});
