import { describe, expect, it } from "vitest";
import { shopFloorWorkcenterTitle } from "./useShopFloorData";

describe("shopFloorWorkcenterTitle", () => {
  it("maps raw workcenter codes to existing operator station names", () => {
    expect(shopFloorWorkcenterTitle("wc_cnc_routing")).toBe("CNC");
    expect(shopFloorWorkcenterTitle("WC_CNC_ROUTING")).toBe("CNC");
    expect(shopFloorWorkcenterTitle("CNC_ROUTING")).toBe("CNC");
    expect(shopFloorWorkcenterTitle("METAL_FAB")).toBe("Lăcătușerie / Sudură");
    expect(shopFloorWorkcenterTitle("LETTER_FORMING")).toBe("Modelare litere");
    expect(shopFloorWorkcenterTitle("LASER_CUTTING")).toBe("CNC");
    expect(shopFloorWorkcenterTitle("VINYL_APPLICATION")).toBe("Montaj autocolant");
  });

  it("does not use WC_* or SNAKE_CASE as the primary title when a mapping exists", () => {
    for (const code of ["CNC_ROUTING", "METAL_FAB", "LETTER_FORMING"]) {
      const title = shopFloorWorkcenterTitle(code);
      expect(title).not.toMatch(/^WC_/);
      expect(title).not.toBe(code);
    }
  });

  it("uses a generic readable fallback for unknown codes", () => {
    expect(shopFloorWorkcenterTitle("UNKNOWN_COMPILER_WC")).toBe("Post de lucru");
  });
});
