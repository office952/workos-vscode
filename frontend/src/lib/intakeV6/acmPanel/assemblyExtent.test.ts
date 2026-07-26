import { describe, expect, it } from "vitest";
import {
  ASSEMBLY_DIMENSION_TOLERANCE_MM,
  computeAcmAssemblyExtent,
} from "./assemblyExtent";

describe("computeAcmAssemblyExtent", () => {
  it("uses 1 mm tolerance", () => {
    expect(ASSEMBLY_DIMENSION_TOLERANCE_MM).toBe(1);
  });

  it("matches fixture: assembly 2000×350, envelope 1000×350", () => {
    const result = computeAcmAssemblyExtent({
      panels: [
        { width_mm: 1000, height_mm: 350, position: { x_mm: 0, y_mm: 0 } },
        { width_mm: 1000, height_mm: 350, position: { x_mm: 1000, y_mm: 0 } },
      ],
      assembly_dimensions: { width_mm: 2000, height_mm: 350 },
      envelope_width_mm: 1000,
      envelope_height_mm: 350,
    });
    expect(result.assembly_width_mm).toBe(2000);
    expect(result.assembly_height_mm).toBe(350);
    expect(result.source).toBe("assembly_dimensions");
    expect(result.envelope_ignored_for_multi_panel).toBe(true);
  });

  it("does not use envelope as overall for multi-panel", () => {
    const result = computeAcmAssemblyExtent({
      panels: [
        { width_mm: 1000, height_mm: 350, x_mm: 0, y_mm: 0 },
        { width_mm: 1000, height_mm: 350, x_mm: 1000, y_mm: 0 },
      ],
      envelope_width_mm: 1000,
      envelope_height_mm: 350,
    });
    expect(result.assembly_width_mm).toBe(2000);
    expect(result.assembly_height_mm).toBe(350);
    expect(result.source).toBe("panel_extent");
  });

  it("empty panels falls back to envelope for panel-alone", () => {
    const result = computeAcmAssemblyExtent({
      panels: [],
      envelope_width_mm: 2000,
      envelope_height_mm: 500,
    });
    expect(result.assembly_width_mm).toBe(2000);
    expect(result.assembly_height_mm).toBe(500);
    expect(result.source).toBe("envelope");
  });
});
