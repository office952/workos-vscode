import { describe, expect, it } from "vitest";
import { resolveLayerColorHumanLabel } from "./layerColorDisplay";

describe("resolveLayerColorHumanLabel", () => {
  it("maps known brand colors to human labels", () => {
    expect(resolveLayerColorHumanLabel("#009846")).toBe("Verde · ANA");
    expect(resolveLayerColorHumanLabel("#00A0E3")).toBe("Albastru · MARIA");
  });

  it("uses pseudo layer names from report when available", () => {
    expect(
      resolveLayerColorHumanLabel("#009846", {
        layers: [
          {
            id: "ana",
            name: "pseudo ana (green)",
            colors: ["#009846"],
            layerKind: "pseudo",
            autoRole: "letter_group",
            autoConfidence: "high",
            paintEvidence: { paintKind: "solid", isMulticolor: false },
            warnings: [],
          },
        ],
      } as never),
    ).toBe("ana");
  });
});
