import { describe, expect, it } from "vitest";

import { deriveLetterGroupsFromAnalyzer } from "./intakeV6LetterGroups";
import { INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE } from "./intakeV6ReturnFinishOptions";

describe("deriveLetterGroupsFromAnalyzer return default", () => {
  it("uses white_aluminum for new letter groups", () => {
    const groups = deriveLetterGroupsFromAnalyzer(
      {
        schemaVersion: "1.11.0",
        layers: [
          {
            id: "layer-a",
            name: "layer-a",
            perimeterMl: 5,
            filledAreaSqm: 1,
            elementCount: 1,
            colors: [],
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
              paintKind: "none",
            },
          },
        ],
      },
      {
        confirmation_status: "complete",
        layers: [
          {
            layerKey: "layer-a",
            layerName: "layer-a",
            autoRole: "face",
            confirmedRole: "face",
            confirmationState: "confirmed",
          },
        ],
        warnings: [],
      },
    );
    expect(groups[0]?.return_finish_type).toBe(INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE);
  });
});