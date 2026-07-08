import { describe, expect, it } from "vitest";
import {
  buildFormSystemBackboneAwarenessFromProjection,
  buildFormSystemBackboneAwarenessModel,
} from "./formSystemBackboneAwareness";
import { buildFormSystemBackboneFieldProjection } from "./formSystemBackboneFieldProjection";
import type { FormSystemBackboneContract } from "./intakeV6ModularFormContractTypes";

function sampleBackbone(overrides: Partial<FormSystemBackboneContract> = {}): FormSystemBackboneContract {
  return {
    read_only: true,
    root: {
      canonical_code: "TPL-VOLUMETRIC-LETTERS_v2",
      root_type: "product_template",
      quote_mode: "product_total",
      allowed: true,
      blocked: false,
      canonical_alias_resolution: true,
    },
    components: [
      { component_key: "face", label: "Face", coverage: "covered" },
      { component_key: "back", label: "Back", coverage: "partial" },
      { component_key: "electrical", label: "Electrical", coverage: "future" },
    ],
    fields: [
      {
        field_key: "svg.layer_group_role",
        owning_component: "svg_layer_roles",
        source_type: "svg_suggested",
        state: "suggested",
        product_truth_path: "svg.layer_roles[].suggested_role",
        required_for: ["quote_preview"],
        blocker_code: "LAYER_ROLES_INCOMPLETE",
      },
      {
        field_key: "return.depth_mm",
        owning_component: "return_cant",
        source_type: "hydrated",
        state: "hydrated",
        product_truth_path: "components.return.depth_mm",
        required_for: ["quote_preview"],
        blocker_code: "RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED",
      },
      {
        field_key: "lighting.type",
        owning_component: "lighting_led",
        source_type: "fallback",
        state: "fallback",
        product_truth_path: "components.lighting.illumination_type",
        required_for: ["quote_preview"],
        blocker_code: "LIGHTING_MODE_CONFIRMATION_REQUIRED",
      },
      {
        field_key: "svg.selected_layer_group",
        owning_component: "svg_layer_roles",
        source_type: "operator_confirmed",
        state: "missing",
        product_truth_path: "svg.selected_layer_refs[]",
        required_for: ["quote_preview"],
        blocker_code: "SELECTED_FACE_LAYER_MISSING",
      },
      {
        field_key: "lighting.psu_configuration",
        owning_component: "lighting_led",
        source_type: "hydrated",
        state: "hydrated",
        product_truth_path: "components.lighting.psu_configuration",
      },
      {
        field_key: "materials.led_psu",
        owning_component: "lighting_led",
        source_type: "blocked",
        state: "blocked",
        product_truth_path: "materials.led_psu",
      },
      {
        field_key: "material.led_psu",
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
        message: "Layer role suggestions need confirmation.",
      },
    ],
    downstream_write_intent: {
      pricing_write: false,
      quote_write: false,
      order_write: false,
      execution_runtime_write: false,
      db_write: false,
    },
    ...overrides,
  };
}

describe("buildFormSystemBackboneAwarenessModel", () => {
  it("returns unavailable model for missing backbone", () => {
    const model = buildFormSystemBackboneAwarenessModel(null);

    expect(model.available).toBe(false);
    expect(model.downstreamWriteSafe).toBe(true);
    expect(model.stateWarnings).toContain("Form System Backbone diagnostic unavailable.");
  });

  it("summarizes root, coverage, fields, blockers and state warnings", () => {
    const model = buildFormSystemBackboneAwarenessModel(sampleBackbone());

    expect(model.available).toBe(true);
    expect(model.root.canonicalCode).toBe("TPL-VOLUMETRIC-LETTERS_v2");
    expect(model.root.aliasNormalized).toBe(true);
    expect(model.coverage.covered).toBe(1);
    expect(model.coverage.partial).toBe(1);
    expect(model.coverage.future).toBe(1);
    expect(model.fields.find((field) => field.fieldKey === "svg.layer_group_role")).toMatchObject({
      fieldKey: "svg.layer_group_role",
      owningComponent: "svg_layer_roles",
      sourceType: "svg_suggested",
      state: "suggested",
      targetPath: "svg.layer_roles[].suggested_role",
    });
    expect(model.fields.find((field) => field.fieldKey === "return.depth_mm")).toMatchObject({
      fieldKey: "return.depth_mm",
      state: "hydrated",
      targetPath: "components.return.depth_mm",
    });
    expect(model.fields.find((field) => field.fieldKey === "svg.selected_layer_group")).toMatchObject({
      fieldKey: "svg.selected_layer_group",
      state: "missing",
      targetPath: "svg.selected_layer_refs[]",
    });
    expect(model.blockers[0].code).toBe("LAYER_ROLES_INCOMPLETE");
    expect(model.stateWarnings).toContain("Suggested values are not confirmed.");
    expect(model.stateWarnings).toContain("Fallback/hydrated values are not confirmed.");
  });

  it("builds awareness categories from backbone projection without promoting unconfirmed fields", () => {
    const projection = buildFormSystemBackboneFieldProjection(sampleBackbone(), {
      fieldKeys: ["svg.layer_group_role", "svg.selected_layer_group", "return.depth_mm", "lighting.type"],
    });

    const awareness = buildFormSystemBackboneAwarenessFromProjection(projection);

    expect(awareness.fields.find((field) => field.fieldKey === "svg.layer_group_role")).toMatchObject({
      sourceType: "svg_suggested",
      state: "suggested",
    });
    expect(awareness.fields.find((field) => field.fieldKey === "return.depth_mm")).toMatchObject({
      state: "hydrated",
    });
    expect(awareness.fields.find((field) => field.fieldKey === "svg.selected_layer_group")).toMatchObject({
      state: "missing",
    });
    expect(awareness.stateWarnings).toContain("Suggested values are not confirmed.");
    expect(awareness.stateWarnings).toContain("Fallback/hydrated values are not confirmed.");
  });

  it("excludes PSU and material rows from awareness projection wiring", () => {
    const model = buildFormSystemBackboneAwarenessModel(sampleBackbone());
    const keys = model.fields.map((field) => field.fieldKey);

    expect(keys).not.toContain("lighting.psu_configuration");
    expect(keys).not.toContain("material.led_psu");
    expect(keys).not.toContain("materials.led_psu");
  });

  it("does not mutate the input backbone", () => {
    const backbone = sampleBackbone();
    const before = JSON.stringify(backbone);

    buildFormSystemBackboneAwarenessModel(backbone);

    expect(JSON.stringify(backbone)).toBe(before);
  });

  it("marks write-intent warnings without executing anything", () => {
    const model = buildFormSystemBackboneAwarenessModel(
      sampleBackbone({ downstream_write_intent: { quote_write: true, order_write: false } }),
    );

    expect(model.downstreamWriteSafe).toBe(false);
    expect(model.unsafeWriteIntents).toEqual(["quote_write"]);
  });
});