import { describe, expect, it } from "vitest";
import { buildReviewDiagnosticEntryCount } from "./intakeV6ReviewDiagnosticEntryCount";

describe("buildReviewDiagnosticEntryCount", () => {
  it("counts unique blocker codes across runtime and planner models", () => {
    const count = buildReviewDiagnosticEntryCount({
      runtimeModel: {
        workspace_code: "IV6-TEST",
        read_only: true,
        fields: [
          {
            field_key: "a",
            blockers: ["SELECTED_LAYER_REFS_MISSING"],
            state: "blocked",
          } as never,
          {
            field_key: "b",
            blockers: ["SELECTED_LAYER_REFS_MISSING", "OTHER_CODE"],
            state: "blocked",
          } as never,
        ],
        blockers: [],
      },
      plannerModel: {
        blockers: [{ blockers: ["PRODUCT_TRUTH_INCOMPLETE"] } as never],
        blocked_entries: [],
      } as never,
    });

    expect(count).toBe(3);
  });

  it("falls back to field counts when no blocker codes exist", () => {
    const count = buildReviewDiagnosticEntryCount({
      runtimeModel: {
        workspace_code: "IV6-TEST",
        read_only: true,
        fields: [{ field_key: "a", blockers: [], state: "confirmed" } as never],
        blockers: [],
      },
    });

    expect(count).toBe(1);
  });
});
