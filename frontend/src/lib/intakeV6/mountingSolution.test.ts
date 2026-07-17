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

  it("buildMountingSolutionPatch writes installation_template sentinel for empty selector", () => {
    const patch = buildMountingSolutionPatch("");
    expect(patch.mounting_solution).toEqual({
      kind: "installation_template",
      template_code: null,
      configuration: {},
    });
    expect(patch.mounting_system).toBeNull();
  });

  it("installation_template is not composition-active (no ACM/metal child)", () => {
    const setup = {
      mounting_scope: "preparation_only",
      mounting_template_enabled: true,
      mounting_template_area_m2: 3,
      mounting_template_material_type: "forex",
      mounting_solution: {
        kind: "installation_template",
        template_code: null,
        configuration: {},
      },
    };
    expect(isMountingSolutionCompositionActive(setup)).toBe(false);
    expect(mountingSolutionSelectorValue(setup)).toBe("");
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

  it("hydrates ACM panel dimensions from svg_support_selection instead of 1000×600 defaults", () => {
    const solution = resolveEffectiveMountingSolution({
      svg_support_selection: {
        schema: "svg_support_selection_v1",
        status: "confirmed",
        role: "ALUCOBOND_CASED_PANEL",
        contour_id: "cc_1",
        geometry_hash: "gh",
        svg_source_hash: "sh",
        unit_ambiguity: true,
        panel_geometry: {
          width_mm: 1500,
          height_mm: 900,
          area_mm2: 1_350_000,
          perimeter_mm: 4800,
          geometry_hash: "gh",
        },
        casing_profile: {
          fold_count: 2,
          l1_mm: 60,
          l2_mm: 25,
          finished_depth_mm: 60,
        },
      },
    });
    expect(solution?.template_code).toBe(ACM_BOXED_MOUNTING_TEMPLATE_CODE);
    expect(solution?.configuration.panel_width_mm).toBe(1500);
    expect(solution?.configuration.panel_height_mm).toBe(900);
    expect(solution?.configuration.dimension_source).toBe("svg_support_selection");
    expect(solution?.configuration.unit_ambiguity).toBe(true);
  });
});
