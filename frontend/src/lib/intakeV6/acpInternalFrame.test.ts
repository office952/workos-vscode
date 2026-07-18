import { describe, expect, it } from "vitest";
import {
  CROSSBAR_SPACING_ALUMINIUM_MM,
  CROSSBAR_SPACING_STEEL_MM,
  MAT_STRUCT_ALUMINIUM,
  MAT_STRUCT_STEEL,
  computeFrameOuterDimensions,
  proposeInternalFrame,
  suggestCrossbarCount,
} from "./acpInternalFrame";

describe("acpInternalFrame domain (client mirror)", () => {
  it("computes 2000x700x3 → 1992x692", () => {
    const dims = computeFrameOuterDimensions({
      panelOuterWidthMm: 2000,
      panelOuterHeightMm: 700,
      panelMaterialThicknessMm: 3,
    });
    expect(dims.frameOuterWidthMm).toBe(1992);
    expect(dims.frameOuterHeightMm).toBe(692);
    expect(dims.valid).toBe(true);
  });

  it("steel vs aluminium spacing and suggestion", () => {
    expect(CROSSBAR_SPACING_STEEL_MM).toBe(1000);
    expect(CROSSBAR_SPACING_ALUMINIUM_MM).toBe(750);
    expect(suggestCrossbarCount(1992, 1000)).toBe(1);
    expect(suggestCrossbarCount(1992, 750)).toBe(2);
  });

  it("keeps profile catalog gate in proposeInternalFrame", () => {
    const frame = proposeInternalFrame({
      enabled: true,
      materialCode: MAT_STRUCT_STEEL,
      panelWidthMm: 2000,
      panelHeightMm: 700,
      panelThicknessMm: 3,
      orientation: "VERTICAL",
      confirmedCrossbarCount: 1,
    });
    expect(frame.frame_outer_width_mm).toBe(1992);
    expect(frame.confirmation_status).toBe("INCOMPLETE");
    expect(frame.blockers).toContain("internal_frame_profile_catalog_empty");
    expect(frame.material_code).toBe(MAT_STRUCT_STEEL);
    expect(MAT_STRUCT_ALUMINIUM).toBe("MAT-STRUCT-ALUMINIUM");
  });
});
