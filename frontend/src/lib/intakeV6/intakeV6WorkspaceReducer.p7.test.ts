import { describe, expect, it } from "vitest";
import {
  initialIntakeV6WorkspaceState,
  intakeV6WorkspaceReducer,
} from "./intakeV6WorkspaceReducer";
import type { IntakeV6WorkspaceResponse } from "./intakeV6Api";

function workspaceWithCompleteRoles(): IntakeV6WorkspaceResponse {
  return {
    id: "ws-1",
    workspace_code: "IV6-TEST",
    title: "test",
    template_code: "TPL-VOLUMETRIC-LETTERS_v2",
    status: "collecting_data",
    readiness_status: "product_composition_not_confirmed",
    payload: {
      svg_source: { file_name: "x.svg", file_size_bytes: 10 },
      svg_source_text: "<svg></svg>",
      svg_analysis_json: {
        layers: [{ id: "a", name: "a" }],
        layerRoleConfirmation: {
          confirmationStatus: "complete",
          layers: [
            {
              layerKey: "a",
              layerId: "a",
              layerName: "a",
              autoRole: "face",
              autoConfidence: "high",
              confirmedRole: "face",
              confirmationState: "confirmed",
              operatorNote: null,
            },
          ],
        },
      },
      layer_role_setup: {
        confirmation_status: "complete",
        layers: [
          {
            layer_key: "a",
            layer_id: "a",
            layer_name: "a",
            auto_role: "face",
            auto_confidence: "high",
            confirmed_role: "face",
            confirmation_state: "confirmed",
            operator_note: null,
          },
        ],
        warnings: [],
      },
    },
  } as unknown as IntakeV6WorkspaceResponse;
}

describe("P7 operatorStepIntent survives LOAD_SUCCESS", () => {
  it("keeps layers after explicit SET_STEP(layers) when readiness would bounce to review", () => {
    let state = initialIntakeV6WorkspaceState;
    state = intakeV6WorkspaceReducer(state, {
      type: "LOAD_SUCCESS",
      workspace: workspaceWithCompleteRoles(),
    });
    expect(state.currentStep).toBe("review");

    state = intakeV6WorkspaceReducer(state, { type: "SET_STEP", step: "layers" });
    expect(state.currentStep).toBe("layers");
    expect(state.operatorStepIntent).toBe("layers");

    state = intakeV6WorkspaceReducer(state, {
      type: "LOAD_SUCCESS",
      workspace: workspaceWithCompleteRoles(),
    });
    expect(state.currentStep).toBe("layers");
    expect(state.analyzerReport).not.toBeNull();
    expect(state.svg?.fileName).toBe("x.svg");
  });
});
