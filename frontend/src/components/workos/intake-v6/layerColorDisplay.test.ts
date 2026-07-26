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

  it("uses neutral logo numbering instead of positional labels", () => {
    expect(
      resolveLayerColorHumanLabel("#2B2A29", {
        layers: [
          {
            id: "logo-dreapta",
            name: "logo dreapta",
            colors: ["#2B2A29"],
            layerKind: "pseudo",
            autoRole: "printed_artwork",
            autoConfidence: "high",
            paintEvidence: { paintKind: "none", isMulticolor: false },
            warnings: [],
          },
        ],
      } as never),
    ).toBe("Logo 1");
  });
});
