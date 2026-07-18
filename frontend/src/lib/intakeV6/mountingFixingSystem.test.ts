import { describe, expect, it } from "vitest";

import {
  PROFILE_SHS_20X20X1_5,
  readMountingFixingSystem,
  selectVerticalSteelBracket,
  VERTICAL_STEEL_BRACKET,
} from "@/lib/intakeV6/mountingFixingSystem";

describe("mountingFixingSystem", () => {
  it("selects vertical steel bracket without fixed cornier/bottom lengths", () => {
    const fixing = selectVerticalSteelBracket();
    expect(fixing.type_code).toBe(VERTICAL_STEEL_BRACKET);
    expect(fixing.main_profile_code).toBe(PROFILE_SHS_20X20X1_5);
    expect(fixing.top_angle?.length_mm).toBeNull();
    expect(fixing.bottom_horizontal_bar?.length_mm).toBeNull();
    expect(fixing.lower_fastener?.diameter_mm).toBe(4.5);
    expect(fixing.lower_fastener?.length_mm).toBe(60);
    expect(JSON.stringify(fixing)).not.toContain("150");
  });

  it("reads persisted fixing from finish setup", () => {
    const fixing = readMountingFixingSystem({
      mounting_fixing_system: selectVerticalSteelBracket(),
    });
    expect(fixing.type_code).toBe(VERTICAL_STEEL_BRACKET);
  });
});
