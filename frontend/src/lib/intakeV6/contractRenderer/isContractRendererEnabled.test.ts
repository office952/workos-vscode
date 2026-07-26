import { describe, expect, it } from "vitest";
import { isContractRendererEnabled } from "./isContractRendererEnabled";

describe("isContractRendererEnabled", () => {
  it("enables only Letters pilot templates", () => {
    expect(isContractRendererEnabled("TPL-VOLUMETRIC-LETTERS_v2")).toBe(true);
    expect(isContractRendererEnabled("TPL-VOLUMETRIC-LETTERS")).toBe(true);
    expect(isContractRendererEnabled("TPL-VOLUMETRIC-LOGO_v1")).toBe(false);
    expect(isContractRendererEnabled(null)).toBe(false);
  });
});
