import { describe, expect, it } from "vitest";

import type { FormSystemBackboneFieldProjection } from "./formSystemBackboneFieldProjection";
import { evaluateRuntimeOverlayReadinessPolicy } from "./formSystemBackboneRuntimeReadinessPolicy";
import type { FormSystemBackboneReadiness } from "./intakeV6ModularFormContractTypes";

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
    productTruthPathCandidate: fieldKey,
    isConfirmedTruth: false,
    isDerived: false,
    isBlocking: false,
    warnings: [],
    blockers: [],
    trace: {},
    ...overrides,
  };
}

function readiness(blockers: NonNullable<FormSystemBackboneReadiness["blockers"]>): FormSystemBackboneReadiness {
  return {
    status: blockers.length > 0 ? "blocked" : "ready",
    blockers,
    operator_confirmation_required: [],
    suggestions_allowed: [],
    fallback_or_hydrated_not_confirmed: [],
    downstream_later: [],
  };
}

describe("evaluateRuntimeOverlayReadinessPolicy", () => {
  it("allows relaxing a field-level warning for svg.selected_layer_group but keeps global blocker inactive by default", () => {
    const originalProjection = [
      projection("svg.selected_layer_group", {
        sourceKind: "operator_manual",
        state: "missing",
        isConfirmedTruth: false,
      }),
    ];
    const overlaidProjection = [
      projection("svg.selected_layer_group", {
        sourceKind: "operator_manual",
        state: "confirmed",
        isConfirmedTruth: true,
      }),
    ];

    const decisions = evaluateRuntimeOverlayReadinessPolicy({
      originalProjection,
      overlaidProjection,
      backboneReadiness: readiness([]),
    });

    expect(decisions).toEqual([
      expect.objectContaining({
        fieldKey: "svg.selected_layer_group",
        canRelaxFieldWarning: true,
        canRelaxGlobalBlocker: false,
      }),
    ]);
  });

  it("does not remove broad or global blockers", () => {
    const decisions = evaluateRuntimeOverlayReadinessPolicy({
      originalProjection: [projection("svg.selected_layer_group", { state: "missing" })],
      overlaidProjection: [projection("svg.selected_layer_group", { state: "confirmed", isConfirmedTruth: true })],
      backboneReadiness: readiness([
        {
          field_key: "readiness.product_truth_blockers",
          blocker_code: "PRODUCT_TRUTH_INCOMPLETE",
          message: "Readiness summarizes missing required truth.",
        },
      ]),
    });

    expect(decisions[0]).toMatchObject({
      canRelaxFieldWarning: true,
      canRelaxGlobalBlocker: false,
    });
    expect(decisions[0].trace).toMatchObject({
      broadBlockerCodes: ["PRODUCT_TRUTH_INCOMPLETE"],
    });
  });

  it("allows relaxing a matching field-addressed blocker only for the same confirmed field key", () => {
    const decisions = evaluateRuntimeOverlayReadinessPolicy({
      originalProjection: [projection("svg.selected_layer_group", { state: "missing" })],
      overlaidProjection: [projection("svg.selected_layer_group", { state: "confirmed", isConfirmedTruth: true })],
      backboneReadiness: readiness([
        {
          field_key: "svg.selected_layer_group",
          blocker_code: "SELECTED_FACE_LAYER_MISSING",
          message: "Select confirmed face layer refs.",
        },
      ]),
    });

    expect(decisions[0]).toMatchObject({
      canRelaxFieldWarning: true,
      canRelaxGlobalBlocker: true,
    });
    expect(decisions[0].trace).toMatchObject({
      matchingBlockerCodes: ["SELECTED_FACE_LAYER_MISSING"],
    });
  });

  it("keeps suggested-only overlay unrelaxed", () => {
    const decisions = evaluateRuntimeOverlayReadinessPolicy({
      originalProjection: [projection("svg.layer_group_role", { state: "suggested" })],
      overlaidProjection: [projection("svg.layer_group_role", { state: "suggested", isConfirmedTruth: false })],
      backboneReadiness: readiness([
        {
          field_key: "svg.layer_group_role",
          blocker_code: "LAYER_ROLES_INCOMPLETE",
          message: "Confirm layer roles.",
        },
      ]),
    });

    expect(decisions[0]).toMatchObject({
      fieldStateChanged: false,
      canRelaxFieldWarning: false,
      canRelaxGlobalBlocker: false,
    });
  });

  it("keeps hydrated fields unconfirmed and not relaxed", () => {
    const decisions = evaluateRuntimeOverlayReadinessPolicy({
      originalProjection: [
        projection("return.depth_mm", {
          ownerKind: "component",
          ownerId: "return_cant",
          sourceKind: "hydrated_runtime",
          state: "hydrated",
        }),
      ],
      overlaidProjection: [
        projection("return.depth_mm", {
          ownerKind: "component",
          ownerId: "return_cant",
          sourceKind: "hydrated_runtime",
          state: "hydrated",
        }),
      ],
      backboneReadiness: readiness([
        {
          field_key: "return.depth_mm",
          blocker_code: "RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED",
          message: "Hydrated return depth still needs operator acceptance.",
        },
      ]),
    });

    expect(decisions[0]).toMatchObject({
      canRelaxFieldWarning: false,
      canRelaxGlobalBlocker: false,
    });
  });

  it("ignores PSU and material exclusions", () => {
    const decisions = evaluateRuntimeOverlayReadinessPolicy({
      originalProjection: [
        projection("lighting.psu_configuration"),
        projection("material.led_psu"),
        projection("materials.led_psu"),
      ],
      overlaidProjection: [
        projection("lighting.psu_configuration"),
        projection("material.led_psu"),
        projection("materials.led_psu"),
      ],
      backboneReadiness: readiness([]),
    });

    expect(decisions).toEqual([]);
  });

  it("does not mutate input projections", () => {
    const originalProjection = [projection("svg.selected_layer_group", { state: "missing" })];
    const overlaidProjection = [projection("svg.selected_layer_group", { state: "confirmed", isConfirmedTruth: true })];
    const originalBefore = JSON.stringify(originalProjection);
    const overlaidBefore = JSON.stringify(overlaidProjection);

    evaluateRuntimeOverlayReadinessPolicy({
      originalProjection,
      overlaidProjection,
      backboneReadiness: readiness([]),
    });

    expect(JSON.stringify(originalProjection)).toBe(originalBefore);
    expect(JSON.stringify(overlaidProjection)).toBe(overlaidBefore);
  });
});