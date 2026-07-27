import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { analyzeSvgString } from "./index";
import { isDegenerateBbox, measurePathShape } from "./part-extractor/shapeBounds";
import { classifyLetterPartsFromAnalysis } from "../intakeV6/intakeV4LetterPartClassification";

const fixtureDir = dirname(fileURLToPath(import.meta.url));

describe("pbl-layere child parts regression", () => {
  it("measures CorelDRAW relative paths with non-degenerate bounds when DOM getBBox is zero", () => {
    const source = readFileSync(join(fixtureDir, "fixtures", "pbl-layere.svg"), "utf8");
    const { parsed, report } = analyzeSvgString(source, "pbl-layere.svg", Buffer.byteLength(source));
    const facePath = parsed.elements.find((el) => el.layerName === "Layer_x0020_2" && el.d);
    expect(facePath?.d).toBeTruthy();

    const measured = measurePathShape(facePath!.d!, report.document.mmPerViewBoxUnit);
    expect(isDegenerateBbox(measured.bboxMm)).toBe(false);
    expect(measured.bboxMm?.width).toBeGreaterThan(10);
    expect(measured.bboxMm?.height).toBeGreaterThan(10);
  });

  it("produces 11 child parts (10 face letters + 1 artwork) for pbl-layere.svg", () => {
    const source = readFileSync(join(fixtureDir, "fixtures", "pbl-layere.svg"), "utf8");
    const { report } = analyzeSvgString(source, "pbl-layere.svg", Buffer.byteLength(source));

    expect(report.parts?.count).toBe(11);
    expect(report.parts?.splitDiagnostics?.groupsCreated).toBe(10);
    expect(report.parts?.splitDiagnostics?.subPathCount).toBe(15);
    expect(report.parts?.splitDiagnostics?.fallbackUsed).toBe(false);

    const splitItems = (report.parts?.items ?? []).filter(
      (item) => item.partExtractionMethod === "subpath-shape-grouping",
    );
    expect(splitItems).toHaveLength(10);
    expect(splitItems.every((item) => item.canNest)).toBe(true);
    expect(splitItems.every((item) => (item.bounds.widthMm ?? 0) > 0)).toBe(true);

    const artwork = (report.parts?.items ?? []).find((item) => item.source.layerName === "Layer_x0020_1");
    expect(artwork?.partExtractionMethod).toBe("layer-as-part");
    expect(artwork?.canNest).toBe(true);

    const nestableSheets = report.nesting?.sheets?.filter((sheet) => (sheet.placements?.length ?? 0) > 0) ?? [];
    expect(nestableSheets.length).toBeGreaterThan(0);
  });

  it("classifies 10 real letters and 1 artwork piece after role confirmation", () => {
    const source = readFileSync(join(fixtureDir, "fixtures", "pbl-layere.svg"), "utf8");
    const { report } = analyzeSvgString(source, "pbl-layere.svg", Buffer.byteLength(source));

    const layerRoleSetup = {
      confirmationStatus: "complete" as const,
      layers: [
        {
          layerKey: "Layer_x0020_1",
          layerName: "Layer_x0020_1",
          autoRole: "printed_artwork" as const,
          autoConfidence: "high" as const,
          confirmedRole: "printed_artwork" as const,
          confirmationState: "confirmed" as const,
        },
        {
          layerKey: "Layer_x0020_2",
          layerName: "Layer_x0020_2",
          autoRole: "face" as const,
          autoConfidence: "high" as const,
          confirmedRole: "face" as const,
          confirmationState: "confirmed" as const,
        },
        {
          layerKey: "Layer_x0020_3",
          layerName: "Layer_x0020_3",
          autoRole: "face" as const,
          autoConfidence: "high" as const,
          confirmedRole: "face" as const,
          confirmationState: "confirmed" as const,
        },
      ],
      warnings: [],
    };

    const classification = classifyLetterPartsFromAnalysis(report, layerRoleSetup);

    expect(classification.real_letters_count).toBe(10);
    expect(classification.inner_holes_count).toBe(5);

    const faceParts = (report.parts?.items ?? [])
      .filter((item) => item.source.layerName === "Layer_x0020_2" || item.source.layerName === "Layer_x0020_3")
      .filter((item) => item.partExtractionMethod === "subpath-shape-grouping")
      .sort((a, b) => (a.bounds.xMm ?? 0) - (b.bounds.xMm ?? 0));

    const holesByPart = faceParts.map((part) => ({
      name: part.name,
      layer: part.source.layerName,
      innerContourCount: part.innerContourCount,
      canNest: part.canNest,
    }));

    expect(holesByPart.reduce((sum, row) => sum + row.innerContourCount, 0)).toBe(5);
    expect(holesByPart.every((row) => row.canNest)).toBe(true);
    expect(holesByPart.filter((row) => row.innerContourCount > 0)).toHaveLength(4);
    expect(holesByPart.filter((row) => row.innerContourCount === 2)).toHaveLength(1);
    expect(holesByPart.filter((row) => row.innerContourCount === 1)).toHaveLength(3);
  });
});
