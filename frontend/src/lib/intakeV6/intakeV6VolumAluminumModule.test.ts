import { describe, expect, it } from "vitest";

import { isVolumAluminumModuleApplicable } from "./intakeV6VolumAluminumModule";

describe("isVolumAluminumModuleApplicable", () => {
  it("returns false when cant finish is inactive", () => {
    expect(
      isVolumAluminumModuleApplicable("TPL-VOLUMETRIC-LETTERS_v2", {
        return_finish_type: "none",
        return_depth_mm: 60,
      }),
    ).toBe(false);
  });

  it("returns true for volumetric letters with cant depth and finish", () => {
    expect(
      isVolumAluminumModuleApplicable("TPL-VOLUMETRIC-LETTERS_v2", {
        return_finish_type: "white_aluminum",
        return_depth_mm: 60,
      }),
    ).toBe(true);
  });
});
