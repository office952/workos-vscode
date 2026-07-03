import { describe, expect, it } from "vitest";

import {
  hydrateAnalyzerStateFromPayload,
  mergeServerLayerRolesIntoConfirmation,
  resolveIntakeV6StepFromReadiness,
} from "./intakeV6PayloadHydrate";

const baseConfirmation = {
  schemaVersion: "layer_role_confirmation_v1" as const,
  confirmationStatus: "partial" as const,
  layers: [
    {
      layerKey: "logo",
      layerId: "logo",
      layerName: "logo",
      autoRole: "face" as const,
      autoConfidence: "high" as const,
      autoRoleCandidates: [],
      confirmedRole: null,
      confirmationState: "pending" as const,
      operatorNote: null,
      paintEvidence: {
        fills: [],
        strokes: [],
        gradientRefs: [],
        hasGradient: false,
        hasPattern: false,
        hasImage: false,
        isMulticolor: false,
        fillCount: 0,
        textElementCount: 0,
        paintKind: "none" as const,
      },
      productionHint: "none" as const,
    },
  ],
};

describe("intakeV6PayloadHydrate", () => {
  it("merges server layer role confirmations over analyzer draft", () => {
    const merged = mergeServerLayerRolesIntoConfirmation(baseConfirmation, {
      confirmation_status: "complete",
      layers: [
        {
          layer_key: "logo",
          confirmed_role: "face",
          confirmation_state: "confirmed",
          auto_role: "face",
          auto_confidence: "high",
        },
      ],
      warnings: [],
    });
    expect(merged.confirmationStatus).toBe("complete");
    expect(merged.layers[0]?.confirmationState).toBe("confirmed");
    expect(merged.layers[0]?.confirmedRole).toBe("face");
  });

  it("hydrates analyzer state including preview text", () => {
    const hydrated = hydrateAnalyzerStateFromPayload({
      svg_source: { file_name: "pbl.svg", file_size_bytes: 1000, upload_status: "analyzed" },
      svg_source_text: "<svg/>",
      svg_analysis_json: {
        schemaName: "svg-analyzer-analysis",
        schemaVersion: "1.10.0",
        layerRoleConfirmation: baseConfirmation,
        layers: [],
      },
      layer_role_setup: {
        confirmation_status: "complete",
        layers: [
          {
            layer_key: "logo",
            confirmed_role: "face",
            confirmation_state: "confirmed",
            auto_role: "face",
            auto_confidence: "high",
          },
        ],
        warnings: [],
      },
    });
    expect(hydrated?.svg.fileName).toBe("pbl.svg");
    expect(hydrated?.svg.previewSource).toBe("<svg/>");
    expect(hydrated?.svgSource).toBe("<svg/>");
    expect(hydrated?.layerRoleConfirmation.confirmationStatus).toBe("complete");
    expect(hydrated?.layerChips[0]?.status).toBe("confirmed");
  });

  it("resolves step from readiness_status", () => {
    expect(resolveIntakeV6StepFromReadiness("finish_setup_incomplete", {})).toBe("review");
    expect(resolveIntakeV6StepFromReadiness("ready_for_quote_preview", {})).toBe("confirm");
    expect(resolveIntakeV6StepFromReadiness("missing_svg", {})).toBe("layers");
  });
});