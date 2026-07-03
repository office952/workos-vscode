import { describe, expect, it } from "vitest";
import {
  buildPreviewLayerStack,
  computeExpandedViewBox,
  getIsometricDepthVector,
  resolveGeometrySource,
  usesEstimatedLedPlacement,
} from "./volumetricLetterPreviewGeometry";
import {
  MOCK_COMPLETE_CONFIG,
  MOCK_TEXT_FALLBACK,
} from "./volumetricLetterPreviewMocks";

describe("volumetricLetterPreviewGeometry", () => {
  it("resolves real geometry when svgPath is present", () => {
    expect(resolveGeometrySource(MOCK_COMPLETE_CONFIG)).toBe("real");
  });

  it("resolves estimated geometry for text-only artwork", () => {
    expect(resolveGeometrySource(MOCK_TEXT_FALLBACK)).toBe("estimated");
  });

  it("builds layer stack only from configured product fields", () => {
    const layers = buildPreviewLayerStack(MOCK_COMPLETE_CONFIG);
    const ids = layers.map((l) => l.id);
    expect(ids).toEqual(["face", "vinyl", "return", "backing", "led", "wiring", "mounting"]);
  });

  it("omits vinyl layer when face vinyl is disabled", () => {
    const layers = buildPreviewLayerStack({
      ...MOCK_COMPLETE_CONFIG,
      face: { material: "plexiglas", hasVinyl: false },
    });
    expect(layers.some((l) => l.id === "vinyl")).toBe(false);
  });

  it("computes expanded viewBox from layer count", () => {
    const layers = buildPreviewLayerStack(MOCK_COMPLETE_CONFIG);
    const box = computeExpandedViewBox(layers.length);
    expect(box.width).toBeGreaterThan(200);
    expect(box.height).toBeGreaterThan(140);
  });

  it("flags estimated LED placement for non-SVG geometry", () => {
    expect(usesEstimatedLedPlacement(MOCK_COMPLETE_CONFIG)).toBe(false);
    expect(usesEstimatedLedPlacement(MOCK_TEXT_FALLBACK)).toBe(true);
  });

  it("scales isometric depth vector from return depth mm", () => {
    const shallow = getIsometricDepthVector(30);
    const deep = getIsometricDepthVector(100);
    expect(deep.depth).toBeGreaterThan(shallow.depth);
    expect(deep.dx).toBeGreaterThan(shallow.dx);
  });
});
