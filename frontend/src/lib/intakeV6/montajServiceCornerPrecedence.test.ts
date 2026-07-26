import { describe, expect, it } from "vitest";
import {
  resolveServiceCornerUiMode,
  shouldShowLegacyServiceCornerInput,
} from "./montajServiceCornerPrecedence";

describe("montajServiceCornerPrecedence", () => {
  it("keeps legacy corner authoritative for single-panel / no segmented", () => {
    expect(resolveServiceCornerUiMode({})).toBe("legacy_authoritative");
    expect(shouldShowLegacyServiceCornerInput({})).toBe(true);
  });

  it("hides legacy input when segmented multi-panel is CONFIRMED", () => {
    const finish = {
      segmented_background: {
        schema: "acm_segmented_background_v1",
        status: "CONFIRMED",
        panels: [{ panel_id: "p1" }, { panel_id: "p2" }],
      },
    };
    expect(resolveServiceCornerUiMode(finish)).toBe("legacy_hidden_segmented_confirmed");
    expect(shouldShowLegacyServiceCornerInput(finish)).toBe(false);
  });

  it("demotes but does not hide legacy while segmented is PROPOSED", () => {
    const finish = {
      segmented_background: {
        schema: "acm_segmented_background_v1",
        status: "PROPOSED",
        panels: [{ panel_id: "p1" }, { panel_id: "p2" }],
      },
    };
    expect(resolveServiceCornerUiMode(finish)).toBe("legacy_demoted_segmented_pending");
    expect(shouldShowLegacyServiceCornerInput(finish)).toBe(true);
  });

  it("does not destroy single-panel truth path when REJECTED", () => {
    const finish = {
      segmented_background: {
        schema: "acm_segmented_background_v1",
        status: "REJECTED",
        panels: [{ panel_id: "p1" }, { panel_id: "p2" }],
      },
      power_supply_service_corner: "TOP_LEFT",
    };
    expect(resolveServiceCornerUiMode(finish)).toBe("legacy_demoted_segmented_pending");
    expect(shouldShowLegacyServiceCornerInput(finish)).toBe(true);
  });
});
