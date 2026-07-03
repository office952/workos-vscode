import { describe, expect, it } from "vitest";
import {
  getIntakeV6ComponentQuestionDisplay,
  INTAKE_V6_COMPONENT_QUESTION_DISPLAY,
  INTAKE_V6_COMPONENT_QUESTION_DISPLAY_ONLY_NOTE,
} from "./intakeV6ComponentQuestionDisplay";

describe("intakeV6ComponentQuestionDisplay", () => {
  it("marks component question metadata as display-only", () => {
    const face = getIntakeV6ComponentQuestionDisplay("facePlexiglas");

    expect(face.componentOwner).toBe("Face");
    expect(face.sourceStatus).toContain("OWNER_APPROVED_RULE_APPLIED");
    expect(face.blockerLevel).toContain("REQUIRED_FOR_QUOTE");
    expect(face.productTruthStatus).toContain("PRODUCT_TRUTH_CANDIDATE");
    expect(face.productTruthStatus).toContain("OWNER_APPROVED_DEFAULT");
    expect(face.productTruthStatus).toContain("OPERATOR_CONFIRMABLE");
    expect(face.productTruthStatus).toContain("MISSING_UI_GAP");
    expect(face.displayOnly).toBe(true);
    expect(INTAKE_V6_COMPONENT_QUESTION_DISPLAY_ONLY_NOTE).toMatch(/do not decide readiness/i);
  });

  it("does not mark fallback or owner-default metadata as confirmed truth", () => {
    const statuses = Object.values(INTAKE_V6_COMPONENT_QUESTION_DISPLAY).flatMap(
      (item) => item.productTruthStatus,
    );

    expect(statuses).toContain("FALLBACK_OR_HYDRATED");
    expect(statuses).toContain("OWNER_APPROVED_DEFAULT");
    expect(statuses).toContain("MISSING_UI_GAP");
    expect(statuses).not.toContain("CONFIRMED_TRUTH");
  });

  it("classifies missing UI gaps and conditional blockers without treating them as readiness logic", () => {
    const face = getIntakeV6ComponentQuestionDisplay("facePlexiglas");
    const electrical = getIntakeV6ComponentQuestionDisplay("electricalLedCables");
    const support = getIntakeV6ComponentQuestionDisplay("supportBars");

    expect(face.sourceStatus).toContain("MISSING_UI_GAP");
    expect(face.chips.map((chip) => chip.text)).toContain(
      "Missing UI gap: explicit face material/thickness control",
    );
    expect(electrical.blockerLevel).toContain("QUOTE_BLOCKER_CONDITIONAL");
    expect(electrical.blockerLevel).toContain("ORDER_EXECUTION_ONLY");
    expect(support.blockerLevel).toContain("QUOTE_BLOCKER_CONDITIONAL");
  });

  it("keeps Pricing Registry and Product Truth boundary as display text", () => {
    const pricing = getIntakeV6ComponentQuestionDisplay("pricingBoundary");

    expect(pricing.componentOwner).toBe("Pricing boundary");
    expect(pricing.ownerApprovedRule).toBe("Pricing Registry does not decide Product Truth");
    expect(pricing.blockerLevel).toContain("INTERNAL_ONLY");
    expect(pricing.productTruthStatus).toEqual(["NOT_PRODUCT_TRUTH"]);
    expect(pricing.chips.map((chip) => chip.text)).toContain("CostEngine internal-only");
  });

  it("does not introduce commercial hour or minute pricing labels", () => {
    const allText = Object.values(INTAKE_V6_COMPONENT_QUESTION_DISPLAY)
      .flatMap((item) => [item.ownerApprovedRule, ...item.chips.map((chip) => chip.text)])
      .join(" ");

    expect(allText).not.toMatch(/\b(hour|minute|ora|oră|minut)\b/i);
  });
});