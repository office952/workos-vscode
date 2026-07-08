import { describe, expect, it } from "vitest";

import {
  buildFormSystemBackboneFieldProjection,
  DEFAULT_FORM_SYSTEM_BACKBONE_FIELD_KEYS,
  type FormSystemBackboneFieldProjection,
} from "./formSystemBackboneFieldProjection";
import type { IntakeV6ModularFormContractResponse } from "./intakeV6ModularFormContractTypes";

function buildContract(): IntakeV6ModularFormContractResponse {
  return {
    summary: {
      template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    },
    modules: [],
    field_bindings: [],
    trigger_alignments: [],
    form_system_backbone: {
      read_only: true,
      root: {
        canonical_code: "TPL-VOLUMETRIC-LETTERS_v2",
      },
      fields: [
        {
          field_key: "svg.layer_group_role",
          operator_label: "Rol strat/grup SVG",
          owning_component: "svg_layer_roles",
          source_type: "svg_suggested",
          state: "suggested",
          product_truth_path: "svg.layer_roles[].suggested_role",
          blocker_code: "LAYER_ROLES_INCOMPLETE",
          notes: "Suggestion only. Operator confirmation must create the confirmed role map.",
        },
        {
          field_key: "svg.selected_layer_group",
          operator_label: "Layer/grup selectat",
          owning_component: "svg_layer_roles",
          source_type: "operator_confirmed",
          state: "missing",
          product_truth_path: "svg.selected_layer_refs[]",
          blocker_code: "SELECTED_FACE_LAYER_MISSING",
          notes: "Explicit selected/confirmed layer refs are required before quote-safe truth.",
        },
        {
          field_key: "return.depth_mm",
          operator_label: "Adancime cant",
          owning_component: "return_cant",
          component_template_code: "TPL-VOLUM-ALUMINIU_v1",
          source_type: "hydrated",
          state: "hydrated",
          product_truth_path: "components.return.depth_mm",
          blocker_code: "RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED",
          notes: "A hydrated/default depth such as 60 mm does not count as confirmed until operator acceptance.",
        },
        {
          field_key: "lighting.type",
          operator_label: "Tip iluminare",
          owning_component: "lighting_led",
          source_type: "fallback",
          state: "fallback",
          product_truth_path: "components.lighting.illumination_type",
          blocker_code: "LIGHTING_MODE_CONFIRMATION_REQUIRED",
        },
        {
          field_key: "lighting.psu_configuration",
          operator_label: "PSU config",
          owning_component: "lighting_led",
          source_type: "hydrated",
          state: "hydrated",
          product_truth_path: "components.lighting.psu_configuration",
        },
        {
          field_key: "materials.led_psu",
          operator_label: "LED PSU material",
          owning_component: "lighting_led",
          source_type: "blocked",
          state: "blocked",
          product_truth_path: "materials.led_psu",
        },
        {
          field_key: "material.led_psu",
          operator_label: "LED PSU material row",
          owning_component: "lighting_led",
          source_type: "blocked",
          state: "blocked",
          product_truth_path: "material.led_psu",
        },
      ],
      blockers: [
        {
          field_key: "svg.layer_group_role",
          owning_component: "svg_layer_roles",
          blocker_code: "LAYER_ROLES_INCOMPLETE",
          state: "suggested",
          message: "Confirm layer roles before quote-safe truth.",
        },
        {
          field_key: "svg.selected_layer_group",
          owning_component: "svg_layer_roles",
          blocker_code: "SELECTED_FACE_LAYER_MISSING",
          state: "missing",
          message: "Select confirmed face layer refs.",
        },
        {
          field_key: "return.depth_mm",
          owning_component: "return_cant",
          blocker_code: "RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED",
          state: "hydrated",
          message: "Hydrated return depth still needs operator acceptance.",
        },
      ],
    },
  };
}

function byField(projections: FormSystemBackboneFieldProjection[], fieldKey: string) {
  const projection = projections.find((entry) => entry.fieldKey === fieldKey);
  expect(projection).toBeDefined();
  return projection!;
}

describe("buildFormSystemBackboneFieldProjection", () => {
  it("maps svg.layer_group_role as svg analyzer suggestion and not confirmed truth", () => {
    const projections = buildFormSystemBackboneFieldProjection(buildContract());

    const projection = byField(projections, "svg.layer_group_role");
    expect(projection.sourceKind).toBe("svg_analyzer");
    expect(projection.state).toBe("suggested");
    expect(projection.isConfirmedTruth).toBe(false);
    expect(projection.ownerKind).toBe("svg");
    expect(projection.productTruthPathCandidate).toBe("svg.layer_roles[].suggested_role");
  });

  it("maps svg.selected_layer_group from the existing backbone state without inventing confirmation", () => {
    const projections = buildFormSystemBackboneFieldProjection(buildContract());

    const projection = byField(projections, "svg.selected_layer_group");
    expect(projection.ownerKind).toBe("svg");
    expect(projection.ownerId).toBe("svg_layer_roles");
    expect(projection.sourceKind).toBe("operator_manual");
    expect(projection.state).toBe("missing");
    expect(projection.isConfirmedTruth).toBe(false);
  });

  it("maps return.depth_mm as hydrated runtime and not confirmed truth", () => {
    const projections = buildFormSystemBackboneFieldProjection(buildContract());

    const projection = byField(projections, "return.depth_mm");
    expect(projection.sourceKind).toBe("hydrated_runtime");
    expect(projection.state).toBe("hydrated");
    expect(projection.isConfirmedTruth).toBe(false);
    expect(projection.ownerId).toBe("return_cant");
    expect(projection.productTruthPathCandidate).toBe("components.return.depth_mm");
  });

  it("does not include PSU or material rows by default", () => {
    const projections = buildFormSystemBackboneFieldProjection(buildContract());
    const keys = projections.map((entry) => entry.fieldKey);

    expect(keys).toEqual([...DEFAULT_FORM_SYSTEM_BACKBONE_FIELD_KEYS]);
    expect(keys).not.toContain("lighting.psu_configuration");
    expect(keys).not.toContain("materials.led_psu");
    expect(keys).not.toContain("material.led_psu");
  });

  it("does not mutate the input contract", () => {
    const contract = buildContract();
    const before = JSON.stringify(contract);

    buildFormSystemBackboneFieldProjection(contract);

    expect(JSON.stringify(contract)).toBe(before);
  });

  it("returns no projection for an unknown requested field key", () => {
    const projections = buildFormSystemBackboneFieldProjection(buildContract(), {
      fieldKeys: ["unknown.field"],
    });

    expect(projections).toEqual([]);
  });
});