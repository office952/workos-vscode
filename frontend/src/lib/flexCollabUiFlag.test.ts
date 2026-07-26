import { describe, expect, it } from "vitest";
import { FLEX_COLLAB_UI_FLAG, isFlexCollabUiEnabled } from "./flexCollabUiFlag";

describe("isFlexCollabUiEnabled", () => {
  it("defaults to false", () => {
    expect(isFlexCollabUiEnabled({})).toBe(false);
  });

  it("accepts true/1/yes", () => {
    expect(isFlexCollabUiEnabled({ [FLEX_COLLAB_UI_FLAG]: "true" })).toBe(true);
    expect(isFlexCollabUiEnabled({ [FLEX_COLLAB_UI_FLAG]: "1" })).toBe(true);
    expect(isFlexCollabUiEnabled({ [FLEX_COLLAB_UI_FLAG]: "yes" })).toBe(true);
  });

  it("rejects other values", () => {
    expect(isFlexCollabUiEnabled({ [FLEX_COLLAB_UI_FLAG]: "false" })).toBe(false);
    expect(isFlexCollabUiEnabled({ [FLEX_COLLAB_UI_FLAG]: "on" })).toBe(false);
  });
});
