import { describe, expect, it } from "vitest";
import type { OwnerDecisionSummaryItem } from "@/api/operatorTaskTruth";
import {
  OWNER_DECISION_DISPLAY_FALLBACK,
  decisionDisplayLabel,
  parseStructuredActionError,
  productionReleaseStatusLabel,
  splitOwnerDecisions,
  structuredErrorHeadline,
  unresolvedBlockingCount,
} from "./operatorProductionBlockerPresentation";

function decision(overrides: Partial<OwnerDecisionSummaryItem>): OwnerDecisionSummaryItem {
  return {
    code: "INTERNAL_SABLON_FOREX_COST",
    label: "Cost șablon Forex — decizie owner necesară înainte de producție",
    category: "production_blocking",
    blocking: true,
    frozen_status: "present",
    operational_status: "unresolved",
    scope: "order",
    acknowledgement_sufficient: false,
    requires_resolution: true,
    can_resolve: false,
    has_resolution_note: false,
    ...overrides,
  };
}

describe("operatorProductionBlockerPresentation", () => {
  it("maps blocking decision display label from backend first", () => {
    expect(decisionDisplayLabel(decision({}))).toContain("Forex");
  });

  it("uses fallback label when backend label is raw code", () => {
    expect(
      decisionDisplayLabel(
        decision({
          code: "INTERNAL_MONTAJ_RULE",
          label: "INTERNAL_MONTAJ_RULE",
        }),
      ),
    ).toBe(OWNER_DECISION_DISPLAY_FALLBACK.INTERNAL_MONTAJ_RULE.label);
  });

  it("splits blocking and nonblocking without client policy", () => {
    const items = [
      decision({ code: "INTERNAL_SABLON_FOREX_COST", blocking: true }),
      decision({
        code: "INTERNAL_AMBALARE_RULE",
        label: "Regulă ambalare",
        category: "nonblocking_internal_analysis",
        blocking: false,
      }),
    ];
    const { blocking, nonblocking } = splitOwnerDecisions(items);
    expect(blocking).toHaveLength(1);
    expect(nonblocking).toHaveLength(1);
    expect(blocking[0].blocking).toBe(true);
  });

  it("counts unresolved blocking decisions from backend flags", () => {
    expect(
      unresolvedBlockingCount([
        decision({ operational_status: "unresolved" }),
        decision({ code: "INTERNAL_MONTAJ_RULE", operational_status: "resolved" }),
      ]),
    ).toBe(1);
  });

  it("parses production_release_blocked structured 409", () => {
    const parsed = parseStructuredActionError(409, {
      detail: {
        code: "production_release_blocked",
        message: "Producția este blocată",
        blockers: [{ code: "INTERNAL_SABLON_FOREX_COST", label: "Forex" }],
      },
    });
    expect(parsed.code).toBe("production_release_blocked");
    expect(parsed.blockers).toHaveLength(1);
    expect(structuredErrorHeadline(parsed)).toContain("decizii owner");
  });

  it("parses task_not_ready without inventing blockers", () => {
    const parsed = parseStructuredActionError(409, {
      detail: {
        code: "task_not_ready",
        message: "Așteaptă finalizarea predecesorului",
        readiness_label: "blocked_by_predecessor",
      },
    });
    expect(parsed.code).toBe("task_not_ready");
    expect(parsed.readinessLabel).toBe("blocked_by_predecessor");
  });

  it("labels release allowed vs blocked from backend status", () => {
    expect(productionReleaseStatusLabel("RELEASE_ALLOWED", false)).toBe("Productie permisa");
    expect(productionReleaseStatusLabel("RELEASE_BLOCKED_OWNER_DECISIONS", true)).toBe(
      "Productie blocata",
    );
  });
});
