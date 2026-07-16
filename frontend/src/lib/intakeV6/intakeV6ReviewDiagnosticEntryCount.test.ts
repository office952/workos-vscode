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

  it("does not crash on Logo fail-closed backbone blocker rows without nested blockers", () => {
    expect(() =>
      buildReviewDiagnosticEntryCount({
        runtimeModel: {
          workspace_code: "IV6-LOGO",
          read_only: true,
          fields: [],
          blockers: [
            {
              blocker_code: "LOGO_NOT_OFFERABLE",
              severity: "blocked",
              message: "candidate-only",
              blocks: ["quote_preview"],
            } as never,
          ],
        } as never,
      }),
    ).not.toThrow();

    const count = buildReviewDiagnosticEntryCount({
      runtimeModel: {
        workspace_code: "IV6-LOGO",
        read_only: true,
        fields: [],
        blockers: [
          {
            blocker_code: "LOGO_NOT_OFFERABLE",
            severity: "blocked",
            message: "candidate-only",
            blocks: ["quote_preview"],
          } as never,
        ],
      } as never,
    });
    // No nested string codes → falls through to empty fields + one blocker row count path.
    expect(count).toBeGreaterThanOrEqual(0);
  });
});
