import { describe, expect, it } from "vitest";
import { suggestLayerRole } from "@/lib/svgLayerRoleSuggestion";

describe("suggestLayerRole", () => {
  it("detects Litere from layer name", () => {
    expect(suggestLayerRole("LITERE volumetrice")).toBe("volumetric_letters");
    expect(suggestLayerRole("volumetric_letters")).toBe("volumetric_letters");
  });

  it("detects Dibond/ACM from layer name", () => {
    expect(suggestLayerRole("DIBOND backing")).toBe("support_panel");
    expect(suggestLayerRole("ACM panel")).toBe("support_panel");
  });

  it("detects Cadru metalic from layer name", () => {
    expect(suggestLayerRole("CADRU metalic")).toBe("metal_frame");
    expect(suggestLayerRole("BARE_MONTAJ")).toBe("metal_frame");
    expect(suggestLayerRole("STRUCTURA_SUPORT")).toBe("metal_frame");
    expect(suggestLayerRole("frame_steel")).toBe("metal_frame");
  });

  it("detects guide/reference layers", () => {
    expect(suggestLayerRole("ghidaj cote")).toBe("guide_reference");
  });

  it("unknown layer remains unknown", () => {
    expect(suggestLayerRole("Layer_x0020_1")).toBe("unknown");
    expect(suggestLayerRole("")).toBe("unknown");
  });
});
