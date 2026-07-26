import { describe, expect, it } from "vitest";

import type { FormSystemBackboneFieldProjection } from "./formSystemBackboneFieldProjection";
import { applyFormSystemRuntimeStateOverlay } from "./formSystemBackboneRuntimeStateOverlay";
import type { IntakeV6LayerRoleSetup } from "./intakeV6LayerRoleBridge";

function projection(
  fieldKey: string,
  overrides: Partial<FormSystemBackboneFieldProjection> = {},
): FormSystemBackboneFieldProjection {
  return {
    fieldKey,
    label: fieldKey,
    ownerKind: "svg",
    ownerId: "svg_layer_roles",
    sourceKind: "svg_analyzer",
    state: "suggested",
    valuePath: null,
    productTruthPathCandidate: fieldKey === "svg.selected_layer_group" ? "svg.selected_layer_refs[]" : fieldKey,
    isConfirmedTruth: false,
    isDerived: false,
    isBlocking: false,
    warnings: ["Suggested value only; operator confirmation is still required."],
    blockers: ["LAYER_ROLES_INCOMPLETE"],
    trace: { sourceType: "svg_suggested", rawState: "suggested" },
    ...overrides,
  };
}

function runtimeState(overrides: Partial<IntakeV6LayerRoleSetup> = {}): IntakeV6LayerRoleSetup {
  return {
    confirmation_status: "complete",
    layers: [
      {
        layer_key: "face-1",
        layer_id: "face-1",
        layer_name: "Face 1",
        auto_role: "face",
        auto_confidence: "high",
        confirmed_role: "face",
        confirmation_state: "confirmed",
      },
    ],
    warnings: [],
    ...overrides,
  };
}

describe("applyFormSystemRuntimeStateOverlay", () => {
  it("does not mutate projection input", () => {
    const input = [
      projection("svg.layer_group_role"),
      projection("svg.selected_layer_group", {
        sourceKind: "operator_manual",
        state: "missing",
        warnings: ["Field is missing and does not represent confirmed truth."],
        blockers: ["SELECTED_FACE_LAYER_MISSING"],
        trace: { sourceType: "operator_confirmed", rawState: "missing" },
      }),
    ];
    const before = JSON.stringify(input);

    applyFormSystemRuntimeStateOverlay(input, { layerRoleSetup: runtimeState() });

    expect(JSON.stringify(input)).toBe(before);
  });

  it("does not add unknown fields", () => {
    const input = [projection("svg.layer_group_role")];

    const result = applyFormSystemRuntimeStateOverlay(input, { layerRoleSetup: runtimeState() });

    expect(result).toHaveLength(1);
    expect(result.map((entry) => entry.fieldKey)).toEqual(["svg.layer_group_role"]);
    expect(result.find((entry) => entry.fieldKey === "svg.selected_layer_group")).toBeUndefined();
  });

  it("keeps suggested-only layer role unconfirmed", () => {
    const input = [projection("svg.layer_group_role")];

    const result = applyFormSystemRuntimeStateOverlay(input, {
      layerRoleSetup: runtimeState({
        confirmation_status: "partial",
        layers: [
          {
            layer_key: "face-1",
            layer_id: "face-1",
            layer_name: "Face 1",
            auto_role: "face",
            auto_confidence: "high",
            confirmed_role: null,
            confirmation_state: "pending",
          },
        ],
      }),
    });

    expect(result[0]).toMatchObject({
      fieldKey: "svg.layer_group_role",
      state: "suggested",
      isConfirmedTruth: false,
      sourceKind: "svg_analyzer",
    });
  });

  it("marks confirmed layer role as confirmed and preserves original trace in overlay metadata", () => {
    const input = [projection("svg.layer_group_role")];

    const result = applyFormSystemRuntimeStateOverlay(input, { layerRoleSetup: runtimeState() });

    expect(result[0]).toMatchObject({
      fieldKey: "svg.layer_group_role",
      state: "confirmed",
      sourceKind: "operator_manual",
      isConfirmedTruth: true,
      isBlocking: false,
      blockers: [],
    });
    expect(result[0].trace).toMatchObject({
      sourceType: "operator_confirmed",
      rawState: "confirmed",
      overlayOriginalState: "suggested",
      overlayOriginalSourceKind: "svg_analyzer",
      overlayRuntimeConfirmedLayerCount: 1,
    });
  });

  it("updates selected layer group from missing to confirmed when runtime has confirmed layer refs", () => {
    const input = [
      projection("svg.selected_layer_group", {
        sourceKind: "operator_manual",
        state: "missing",
        warnings: ["Field is missing and does not represent confirmed truth."],
        blockers: ["SELECTED_FACE_LAYER_MISSING"],
        trace: { sourceType: "operator_confirmed", rawState: "missing" },
      }),
    ];

    const result = applyFormSystemRuntimeStateOverlay(input, { layerRoleSetup: runtimeState() });

    expect(result[0]).toMatchObject({
      fieldKey: "svg.selected_layer_group",
      state: "confirmed",
      isConfirmedTruth: true,
      productTruthPathCandidate: "svg.selected_layer_refs[]",
    });
    expect(result[0].trace).toMatchObject({
      overlaySelectedLayerIds: ["face-1"],
      overlaySelectedLayerNames: ["Face 1"],
    });
  });

  it("leaves hydrated fields unconfirmed", () => {
    const input = [
      projection("return.depth_mm", {
        ownerKind: "component",
        ownerId: "return_cant",
        sourceKind: "hydrated_runtime",
        state: "hydrated",
        isConfirmedTruth: false,
        warnings: ["Hydrated or fallback value is not confirmed truth."],
        blockers: ["RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED"],
        trace: { sourceType: "hydrated", rawState: "hydrated" },
      }),
    ];

    const result = applyFormSystemRuntimeStateOverlay(input, { layerRoleSetup: runtimeState() });

    expect(result[0]).toMatchObject({
      fieldKey: "return.depth_mm",
      state: "hydrated",
      sourceKind: "hydrated_runtime",
      isConfirmedTruth: false,
    });
  });

  it("ignores PSU and material rows completely", () => {
    const input = [
      projection("lighting.psu_configuration", { ownerKind: "component", ownerId: "lighting_led" }),
      projection("material.led_psu", { ownerKind: "component", ownerId: "lighting_led" }),
      projection("materials.led_psu", { ownerKind: "component", ownerId: "lighting_led" }),
    ];

    const result = applyFormSystemRuntimeStateOverlay(input, { layerRoleSetup: runtimeState() });

    expect(result.map((entry) => entry.fieldKey)).toEqual([
      "lighting.psu_configuration",
      "material.led_psu",
      "materials.led_psu",
    ]);
    expect(result).toEqual(input);
  });
});