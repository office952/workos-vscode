import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { analyzeSvgString } from "../index";
import { extractSubPaths } from "./subPathExtractor";
import { isDegenerateBbox, isInnerContourHoleOfOuter, isPointInsidePathFill, measurePathShape } from "./shapeBounds";

const fixtureDir = dirname(fileURLToPath(import.meta.url));

describe("isInnerContourHoleOfOuter", () => {
  it("detects pbl-layere hole subpaths against parent letter outers", () => {
    const source = readFileSync(join(fixtureDir, "../fixtures/pbl-layere.svg"), "utf8");
    const { parsed, report } = analyzeSvgString(source, "pbl-layere.svg", Buffer.byteLength(source));
    const mm = report.document.mmPerViewBoxUnit;
    const extracted = extractSubPaths(parsed, mm);

    const pairs: Array<[number, number]> = [
      [3, 9],
      [6, 14],
    ];
    for (const [holeIdx, outerIdx] of pairs) {
      const hole = extracted.subPaths.find((row) => row.subPathIndex === holeIdx)!;
      const outer = extracted.subPaths.find((row) => row.subPathIndex === outerIdx)!;
      expect(isInnerContourHoleOfOuter(outer.d, hole.d, hole.bboxMm!, mm)).toBe(true);
    }
  });
});

describe("isPointInsidePathFill", () => {
  it("detects a point inside a simple rectangle path", () => {
    const path = "M0 0 L100 0 L100 50 L0 50 Z";
    expect(isPointInsidePathFill(path, 500, 250, 10)).toBe(true);
    expect(isPointInsidePathFill(path, 5000, 5000, 10)).toBe(false);
  });
});

describe("measurePathShape", () => {
  it("treats zero-sized DOM bbox as degenerate", () => {
    expect(isDegenerateBbox({ x: 0, y: 0, width: 0, height: 0 })).toBe(true);
    expect(isDegenerateBbox({ x: 1, y: 2, width: 10, height: 20 })).toBe(false);
  });

  it("estimates bounds for CorelDRAW-style relative path segments", () => {
    const segment =
      "M160.96101 0.00002l0 34.23166 -8.86554 0 0 -34.23166 8.86554 0z";
    const measured = measurePathShape(segment, 10);
    expect(isDegenerateBbox(measured.bboxMm)).toBe(false);
    expect(measured.bboxMm?.width).toBeGreaterThan(50);
    expect(measured.bboxMm?.height).toBeGreaterThan(50);
  });
});
