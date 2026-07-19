import { describe, expect, it } from "vitest";
import { buildFinalConfirmationBlockers } from "./intakeV6FinalConfirmationBlockers";

describe("buildFinalConfirmationBlockers", () => {
  it("lists composition when not confirmed", () => {
    const blockers = buildFinalConfirmationBlockers({
      payload: {},
      finish: {},
    });
    expect(blockers.some((b) => b.id === "composition" && b.severity === "blocker")).toBe(true);
  });

  it("warns on proposed segmented without blocking as composition replacement", () => {
    const blockers = buildFinalConfirmationBlockers({
      payload: {
        product_composition_confirmed: { confirmed: true },
      },
      finish: {
        segmented_background: {
          schema: "acm_segmented_background_v1",
          status: "PROPOSED",
          panels: [{ panel_id: "a" }, { panel_id: "b" }],
        },
      },
    });
    expect(blockers.find((b) => b.id === "composition")).toBeUndefined();
    expect(blockers.find((b) => b.id === "segmented-proposed")?.severity).toBe("warning");
  });
});
