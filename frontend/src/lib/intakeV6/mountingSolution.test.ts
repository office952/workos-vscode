import { describe, expect, it } from "vitest";

import {
  buildMountingSolutionPatch,
  hydrateMountingSolutionFromLegacy,
  isMountingSolutionCompositionActive,
  METAL_PREMOUNT_TEMPLATE_CODE,
  mountingSolutionSelectorValue,
  prepareMountingSolutionForSave,
  resolveEffectiveMountingSolution,
} from "@/lib/intakeV6/mountingSolution";

describe("mountingSolution", () => {
  it("hydrates legacy steel bars into canonical metal solution", () => {
    const solution = hydrateMountingSolutionFromLegacy({
      mounting_system: "steel_bars",
      mounting_bar_profile: "30x30x1.5",
    });
    expect(solution?.template_code).toBe(METAL_PREMOUNT_TEMPLATE_CODE);
    expect(solution?.configuration.bar_material).toBe("steel");
  });

  it("selector reflects canonical solution", () => {
    expect(
      mountingSolutionSelectorValue({
        mounting_scope: "preparation_only",
        mounting_solution: {
          template_code: METAL_PREMOUNT_TEMPLATE_CODE,
          configuration: { bar_material: "steel" },
        },
      }),
    ).toBe(METAL_PREMOUNT_TEMPLATE_CODE);
  });

  it("scope none disables active composition while preserving selection", () => {
    const setup = {
      mounting_scope: "none",
      mounting_solution: {
        template_code: METAL_PREMOUNT_TEMPLATE_CODE,
        configuration: { bar_material: "steel" },
      },
    };
    expect(isMountingSolutionCompositionActive(setup)).toBe(false);
    expect(resolveEffectiveMountingSolution(setup)?.template_code).toBe(
      METAL_PREMOUNT_TEMPLATE_CODE,
    );
  });

  it("prepareMountingSolutionForSave removes legacy dual-write fields", () => {
    const prepared = prepareMountingSolutionForSave({
      mounting_solution: {
        template_code: METAL_PREMOUNT_TEMPLATE_CODE,
        configuration: { bar_material: "steel" },
      },
      mounting_system: "steel_bars",
      mounting_bar_profile: "30x30x1.5",
    });
    expect(prepared.mounting_solution).toBeTruthy();
    expect(prepared.mounting_system).toBeUndefined();
    expect(prepared.mounting_bar_profile).toBeUndefined();
  });

  it("buildMountingSolutionPatch clears canonical reference for none", () => {
    const patch = buildMountingSolutionPatch("");
    expect(patch.mounting_solution).toBeNull();
    expect(patch.mounting_system).toBeNull();
  });
});
