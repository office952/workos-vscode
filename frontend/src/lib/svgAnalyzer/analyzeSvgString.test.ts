import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { analyzeSvgString } from "./index";

const fixtureDir = dirname(fileURLToPath(import.meta.url));

describe("analyzeSvgString (nest2 port)", () => {
  it("parses pbl-complex.svg with production layers", () => {
    const source = readFileSync(join(fixtureDir, "fixtures", "pbl-complex.svg"), "utf8");
    const { report } = analyzeSvgString(source, "pbl-complex.svg", source.length);
    expect(report.layers.length).toBeGreaterThanOrEqual(4);
    expect(report.layerRoleConfirmation.layers.length).toBeGreaterThanOrEqual(4);
    expect(report.document.widthMm).toBeGreaterThan(0);
    expect(report.document.heightMm).toBeGreaterThan(0);
    const layerNames = report.layers.map((layer) => layer.name);
    expect(layerNames.some((name) => /logo/i.test(name))).toBe(true);
  });
});
