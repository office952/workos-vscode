import { describe, expect, it } from "vitest";

import {
  ACM_BOXED_MOUNTING_TEMPLATE_CODE,
  buildMountingSolutionPatch,
  hydrateMountingSolutionFromLegacy,
  isMountingSolutionCompositionActive,
  METAL_PREMOUNT_TEMPLATE_CODE,
  mountingSolutionSelectorValue,
  normalizeAcmMountingConfiguration,
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

  it("hydrates legacy acm_panel into canonical boxed mounting solution", () => {
    const solution = hydrateMountingSolutionFromLegacy({
      mounting_system: "acm_panel",
    });
    expect(solution?.template_code).toBe(ACM_BOXED_MOUNTING_TEMPLATE_CODE);
    expect(solution?.configuration.acm_thickness_mm).toBe(3);
  });

  it("selector reflects canonical metal solution", () => {
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

  it("selector reflects canonical ACM boxed mounting solution", () => {
    expect(
      mountingSolutionSelectorValue({
        mounting_scope: "preparation_only",
        mounting_solution: {
          template_code: ACM_BOXED_MOUNTING_TEMPLATE_CODE,
          configuration: { panel_width_mm: 1000, panel_height_mm: 600 },
        },
      }),
    ).toBe(ACM_BOXED_MOUNTING_TEMPLATE_CODE);
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

  it("ACM composition active under preparation_only scope", () => {
    const setup = {
      mounting_scope: "preparation_only",
      mounting_solution: {
        template_code: ACM_BOXED_MOUNTING_TEMPLATE_CODE,
        configuration: normalizeAcmMountingConfiguration({
          panel_width_mm: 1000,
          panel_height_mm: 600,
        }),
      },
    };
    expect(isMountingSolutionCompositionActive(setup)).toBe(true);
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

  it("buildMountingSolutionPatch normalizes ACM configuration", () => {
    const patch = buildMountingSolutionPatch(ACM_BOXED_MOUNTING_TEMPLATE_CODE, {
      panel_width_mm: 2000,
      panel_height_mm: 1000,
      return_depth_mm: 60,
      fold_sides: "all",
    });
    const config = (patch.mounting_solution as { configuration: Record<string, unknown> }).configuration;
    expect(config.panel_area_m2).toBe(2);
    expect(config.fold_length_m).toBe(6);
  });

  it("preserves 4 mm thickness for explicit resolver block (no silent coerce to 3)", () => {
    const config = normalizeAcmMountingConfiguration({ acm_thickness_mm: 4 });
    expect(config.acm_thickness_mm).toBe(4);
  });
});
