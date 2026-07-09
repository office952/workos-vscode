import { describe, expect, it } from "vitest";
import {
  buildReturnCantOwnerApplyPlan,
  RETURN_CANT_APPLY_PLAN_SAFETY,
  RETURN_CANT_OWNER_ANSWER_TOPICS,
  contractStatusForTopic,
} from "./componentFirstReturnCantOwnerApplyPlan";
import { RETURN_CANT_OWNER_INPUTS } from "./componentFirstReturnCantOwnerInputs";

describe("componentFirstReturnCantOwnerApplyPlan", () => {
  it("reports no owner answers found when all doc topics are pending", () => {
    const plan = buildReturnCantOwnerApplyPlan();
    expect(plan.answersFound).toBe(false);
    expect(plan.answersSource).toBe("none");
    expect(plan.contractKeysReadyToApply).toEqual([]);
    expect(plan.topicsPending).toBe(RETURN_CANT_OWNER_ANSWER_TOPICS.length);
    expect(plan.topicsAnswered).toBe(0);
    expect(plan.globalWorkshopStatus).toBe("OWNER_INPUT_REQUIRED");
  });

  it("lists pending contract keys without inventing values", () => {
    const plan = buildReturnCantOwnerApplyPlan();
    expect(plan.contractKeysStillPending).toContain("oracal_code_list");
    expect(plan.contractKeysStillPending).toContain("return_depths_standard");
    expect(plan.contractKeysStillPending).toContain("ral_material_price_rule");
    for (const key of plan.contractKeysStillPending) {
      const input = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === key);
      expect(input?.value).toBeNull();
    }
  });

  it("would apply only explicitly answered topics in a future slice", () => {
    const withOneAnswer = RETURN_CANT_OWNER_ANSWER_TOPICS.map((t) =>
      t.contractKeys.includes("oracal_code_list") ? { ...t, docStatus: "answered" as const } : t,
    );
    const plan = buildReturnCantOwnerApplyPlan(withOneAnswer);
    expect(plan.answersFound).toBe(true);
    expect(plan.contractKeysReadyToApply).toEqual(["oracal_code_list"]);
    expect(plan.contractKeysStillPending).not.toContain("oracal_code_list");
  });

  it("keeps confirmed workshop fields unchanged in current audit", () => {
    expect(contractStatusForTopic("finish_type_variants")).toBe("owner_confirmed");
    expect(contractStatusForTopic("ral_material_labor_separation")).toBe("owner_confirmed");
    expect(contractStatusForTopic("oracal_code_list")).toBe("owner_input_required");
  });

  it("documents apply safety guards", () => {
    expect(RETURN_CANT_APPLY_PLAN_SAFETY.join(" ")).toMatch(/no Product Truth live write/i);
    expect(RETURN_CANT_APPLY_PLAN_SAFETY.join(" ")).toMatch(/No Pricing activation/i);
  });
});
