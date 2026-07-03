import { describe, expect, it } from "vitest";

import { buildLayerRoleConfirmationDraft } from "@/lib/svgAnalyzer/analyzer/buildLayerRoleConfirmation";
import type { LayerAnalysis } from "@/lib/svgAnalyzer/analyzer/types";
import {
  confirmAllSuggestedLayerRoles,
  layerRoleConfirmationToV6Setup,
} from "./intakeV6LayerRoleBridge";

function mockLayer(name: string, autoRole: LayerAnalysis["autoRole"]): LayerAnalysis {
  return {
    id: name,
    name,
    autoRole,
    autoConfidence: "high",
    autoRoleCandidates: [],
    paintEvidence: {
      fills: ["#000000"],
      strokes: [],
      gradientRefs: [],
      hasGradient: false,
      hasPattern: false,
      hasImage: false,
      isMulticolor: false,
      fillCount: 1,
      textElementCount: 0,
      paintKind: "solid",
    },
    productionHint: null,
    roleGuess: autoRole,
    elementCount: 1,
    pathElementCount: 1,
    subPathCount: 1,
    closedSubPathCount: 1,
    openSubPathCount: 0,
    widthMm: 100,
    heightMm: 100,
    boundingAreaSqm: 0.01,
    filledAreaSqm: 0.01,
    areaConfidence: "high",
    perimeterMm: 400,
    perimeterMl: 0.4,
    colors: ["#000000"],
    warnings: [],
  };
}

describe("intakeV6LayerRoleBridge", () => {
  it("confirms all suggested roles and maps to V6 setup", () => {
    const draft = buildLayerRoleConfirmationDraft([
      mockLayer("logo", "face"),
      mockLayer("fundal-acm", "backing"),
    ]);
    expect(draft.confirmationStatus).toBe("missing");

    const confirmed = confirmAllSuggestedLayerRoles(draft);
    expect(confirmed.confirmationStatus).toBe("complete");
    expect(confirmed.layers.every((layer) => layer.confirmationState === "confirmed")).toBe(true);

    const setup = layerRoleConfirmationToV6Setup(confirmed);
    expect(setup.confirmation_status).toBe("complete");
    expect(setup.layers).toHaveLength(2);
    expect(setup.layers[0]?.confirmed_role).toBe("face");
  });
});